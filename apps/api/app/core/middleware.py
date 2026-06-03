"""
Core HTTP middleware.

request_id propagation for audit correlation across logs, gateway calls, ai_requests.
Set from header if present (for tracing), else generate.
"""

import uuid
from fastapi import Request


async def add_request_id(request: Request, call_next):
    """Middleware func registered via @app.middleware or app.middleware('http')(fn)"""
    rid = request.headers.get("x-request-id") or f"req-{uuid.uuid4().hex[:12]}"
    request.state.request_id = rid
    response = await call_next(request)
    response.headers["x-request-id"] = rid
    return response
