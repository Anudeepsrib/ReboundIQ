"""
Resume service: upload + faithful parse (pdfplumber/docx/txt) + structured via gateway (no hallucination),
original immutable storage (never delete), versioning with grounded rewrite,
RAG chunk+embed via gateway + store in document_chunks (pgvector) for recall.

Follows: AGENTS.md (gateway only, user_id isolation, audit via gateway, faithful, originals preserved),
design for PR-7: smallest extension of stubs.

Memory recall integration: used to ground version tailoring (text-match fallback; vector search in later).
"""

import uuid
from io import BytesIO
from typing import Optional

import pdfplumber
from docx import Document as DocxDocument  # python-docx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gateway import gateway
from app.core.logging import logger
from app.models.resume import Resume, ResumeVersion, DocumentChunk
from app.services.storage import get_storage


storage = get_storage()


def extract_text(file_bytes: bytes, ext: str) -> str:
    """Faithful text extraction. No LLM here; raw from file."""
    ext = ext.lower()
    if ext == "pdf":
        try:
            with pdfplumber.open(BytesIO(file_bytes)) as pdf:
                pages = [p.extract_text() or "" for p in pdf.pages]
                return "\n".join(pages).strip()
        except Exception:
            return file_bytes.decode("utf-8", errors="ignore")
    elif ext == "docx":
        try:
            doc = DocxDocument(BytesIO(file_bytes))
            paras = [p.text for p in doc.paragraphs if getattr(p, "text", "").strip()]
            return "\n".join(paras).strip()
        except Exception:
            return file_bytes.decode("utf-8", errors="ignore")
    elif ext == "txt":
        return file_bytes.decode("utf-8", errors="ignore")
    return file_bytes.decode("utf-8", errors="ignore")


def _chunk_text(text: str, max_len: int = 600, overlap: int = 80) -> list[str]:
    """Simple deterministic chunker (no external splitter for minimal deps)."""
    if not text or len(text) < 30:
        return []
    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + max_len, n)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        start = end - overlap
    return chunks


async def _index_resume_chunks(
    db: AsyncSession,
    resume_id: str,
    user_id: str,
    text: str,
    request_id: Optional[str],
) -> int:
    """Chunk, embed via gateway (audit+redact), persist to document_chunks. User isolated."""
    chunks = _chunk_text(text)
    count = 0
    for idx, ch in enumerate(chunks):
        if len(ch) < 30:
            continue
        emb: Optional[list[float]] = None
        try:
            emb = await gateway.embed(ch, user_id=user_id, request_id=request_id)
        except Exception as e:
            logger.warning(
                "resume.chunk_embed_fail",
                extra={
                    "user_id": user_id,
                    "request_id": request_id,
                    "err": str(e)[:100],
                },
            )
            emb = None
        chunk = DocumentChunk(
            user_id=user_id,
            resume_id=resume_id,
            chunk_index=idx,
            text=ch,
            embedding=emb,
            meta={"source": "resume_original"},
        )
        db.add(chunk)
        count += 1
    if count:
        await db.commit()
    return count


async def recall_similar_chunks(
    db: AsyncSession, user_id: str, query: str, k: int = 3
) -> list[str]:
    """Minimal memory recall integration for grounding (PR-7).
    Uses recent user chunks (text match on keywords). Real impl: embed query + pgvector <=> / <#> .
    Never overrides explicit user data; used as evidence only.
    """
    if not query:
        return []
    res = await db.execute(
        select(DocumentChunk.text)
        .where(DocumentChunk.user_id == user_id)
        .order_by(DocumentChunk.created_at.desc())
        .limit(8)
    )
    candidates = [row[0] for row in res.all() if row[0]]
    if not candidates:
        return []
    q_tokens = [t.lower() for t in query.split() if len(t) > 3][:6]
    if not q_tokens:
        return candidates[:k]
    matched = [c for c in candidates if any(tok in c.lower() for tok in q_tokens)]
    return (matched or candidates)[:k]


async def upload_and_parse_resume(
    db: AsyncSession,
    file_bytes: bytes,
    filename: str,
    user_id: str,
    request_id: Optional[str] = None,
    content_type: Optional[str] = None,
) -> dict:
    """Store original (immutable key), extract text faithfully, structured parse via gateway only,
    persist Resume row (user_id filtered), RAG index chunks+embeds.
    """
    if not filename:
        raise ValueError("filename required")
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ("pdf", "docx", "txt"):
        raise ValueError(f"Unsupported file type: {ext}")

    text = extract_text(file_bytes, ext)

    # Structured via SINGLE gateway (redact/audit/consent/local-first enforced)
    system = (
        "Extract structured resume info as JSON ONLY. Be 100% faithful to the text. "
        "NEVER invent companies, titles, dates, metrics, skills or names. "
        "If missing use null. Keys: name (str|null), contact (dict|null), summary (str|null), "
        "skills (string[]), experience (array of {company,title,start,end,bullets:string[]}), "
        "education, certifications, metrics (dict). Output pure JSON object."
    )
    parsed = await gateway.structured(
        system,
        text[:10000],
        schema={"type": "object"},
        user_id=user_id,
        request_id=request_id,
    )
    if parsed.get("_parse_error"):
        logger.warning("resume.structured_fallback", extra={"request_id": request_id})

    # Immutable original storage. Key encodes user for isolation.
    key = f"users/{user_id}/resumes/originals/{uuid.uuid4()}.{ext}"
    saved_ref = await storage.save(
        key, file_bytes, content_type or "application/octet-stream"
    )

    resume = Resume(
        user_id=user_id,
        original_filename=filename,
        storage_key=key,
        mime_type=content_type or ("application/" + ext),
        parsed_text=text,
        parsed_json=parsed
        if isinstance(parsed, dict) and not parsed.get("_parse_error")
        else None,
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    num_chunks = await _index_resume_chunks(db, resume.id, user_id, text, request_id)

    logger.info(
        "resume.upload",
        extra={
            "user_id": user_id,
            "request_id": request_id,
            "resume_id": resume.id,
            "filename": filename,
            "storage_key": key,
            "saved_ref": saved_ref,
            "text_len": len(text),
            "num_chunks": num_chunks,
            "has_parsed": bool(resume.parsed_json),
        },
    )

    return {
        "id": resume.id,
        "original_filename": resume.original_filename,
        "created_at": resume.created_at,
        "has_parsed": bool(resume.parsed_json),
        "num_chunks": num_chunks,
        "storage_key": key,
    }


async def create_resume_version(
    db: AsyncSession,
    resume_id: str,
    target_role: str,
    user_id: str,
    request_id: Optional[str] = None,
) -> dict:
    """Create role-targeted version. Grounded via base resume + memory recall (never fabricate).
    Uses gateway.structured. Inserts ResumeVersion with source_inputs for citations/audit.
    """
    if not target_role or len(target_role) < 2:
        raise ValueError("target_role required")

    res = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
    )
    resume = res.scalar_one_or_none()
    if not resume:
        raise ValueError("Resume not found or access denied (user isolation)")

    base_text = resume.parsed_text or ""
    base_parsed = resume.parsed_json or {}

    # Memory recall integration for grounding (evidence only)
    recalled = await recall_similar_chunks(
        db, user_id, f"{target_role} {base_text[:200]}", k=2
    )
    recall_snippet = (
        "\n- ".join(recalled)
        if recalled
        else "(no additional memory grounding snippets)"
    )

    system = (
        "Tailor the resume for the target role. Use *ONLY* facts present in the base parsed resume "
        "and the recalled grounding snippets. Do not invent, exaggerate, or add unmentioned metrics/companies/titles. "
        "Keep language professional and concise. Output STRICT JSON: "
        '{"summary": string, "bullets": string[], "skills": string[], "notes": string }.'
    )
    user_msg = (
        f"TARGET ROLE: {target_role}\n\n"
        f"BASE RESUME (parsed, authoritative): {base_parsed}\n\n"
        f"BASE TEXT EXCERPT (for fidelity): {base_text[:2500]}\n\n"
        f"RECALLED MEMORY/GROUNDING (use only if matches base): \n- {recall_snippet}\n\n"
        "Produce the role-specific rewrite JSON now."
    )

    tailored = await gateway.structured(
        system,
        user_msg,
        schema={"type": "object"},
        user_id=user_id,
        request_id=request_id,
    )

    # Simple deterministic ATS heuristic (no claims)
    ats = 60.0
    bullets = tailored.get("bullets") or []
    if isinstance(bullets, list):
        ats += min(18.0, len(bullets) * 2.5)
    skills = tailored.get("skills") or base_parsed.get("skills") or []
    if isinstance(skills, list) and len(skills) > 4:
        ats += 8.0
    if base_parsed.get("metrics"):
        ats += 7.0
    ats = min(95.0, round(ats, 1))

    version_name = f"{target_role} Tailored"
    content_json = {
        "summary": tailored.get("summary") or base_parsed.get("summary") or "",
        "bullets": [b for b in bullets if isinstance(b, str)][:8],
        "skills": [s for s in skills if isinstance(s, str)][:12],
    }

    version = ResumeVersion(
        resume_id=resume.id,
        user_id=user_id,
        version_name=version_name,
        target_role=target_role,
        content_json=content_json,
        ats_score=ats,
        source_inputs={
            "base_resume_id": resume_id,
            "recalled_snippets_count": len(recalled),
            "grounded": True,
            "notes": tailored.get("notes", ""),
        },
    )
    db.add(version)
    await db.commit()
    await db.refresh(version)

    logger.info(
        "resume.version_created",
        extra={
            "user_id": user_id,
            "request_id": request_id,
            "resume_id": resume_id,
            "version_id": version.id,
            "target_role": target_role,
            "ats_score": ats,
            "recalled_used": len(recalled),
        },
    )

    return {
        "id": version.id,
        "version_name": version.version_name,
        "target_role": version.target_role,
        "content_json": version.content_json,
        "ats_score": version.ats_score,
        "created_at": version.created_at,
    }


async def list_user_resumes(db: AsyncSession, user_id: str) -> list[dict]:
    """List resumes for user (row level isolation)."""
    res = await db.execute(
        select(Resume)
        .where(Resume.user_id == user_id)
        .order_by(Resume.created_at.desc())
    )
    items = res.scalars().all()
    return [
        {
            "id": r.id,
            "original_filename": r.original_filename,
            "created_at": r.created_at,
            "has_parsed": bool(r.parsed_json),
        }
        for r in items
    ]
