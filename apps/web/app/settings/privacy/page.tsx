'use client';
export default function Privacy() {
  return (
    <div className="prose prose-invert max-w-none">
      <h1>Privacy &amp; Data Controls</h1>
      <p>ReboundIQ is built privacy-first. Local AI default. Your documents, resumes, applications, and memories stay in your DB + object storage under your user_id.</p>
      <ul>
        <li>Export all data (GDPR-style)</li>
        <li>Delete account + all artifacts + vectors + memories (irreversible option)</li>
        <li>Consent gates for external AI and sensitive memory categories (visa, finances, etc.)</li>
        <li>Encryption at rest for sensitive profile fields</li>
        <li>Full audit log of AI calls and agent actions</li>
        <li>Redaction before any external provider</li>
      </ul>
      <div className="text-xs text-zinc-500 mt-6">See PRIVACY.md and SECURITY.md in repo. This is a demo slice; full flows in the complete build.</div>
    </div>
  );
}
