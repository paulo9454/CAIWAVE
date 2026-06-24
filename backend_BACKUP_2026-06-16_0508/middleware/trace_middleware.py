import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from backend.utils.audit import audit_log


class TraceMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):
        trace_id = str(uuid.uuid4())
        start_time = time.time()

        request.state.trace_id = trace_id

        try:
            response = await call_next(request)

            duration = int((time.time() - start_time) * 1000)

            response.headers["X-Trace-ID"] = trace_id

            audit_log(
                event_type="api",
                message=f"{request.method} {request.url.path}",
                meta={
                    "trace_id": trace_id,
                    "path": str(request.url.path),
                    "method": request.method,
                    "status_code": response.status_code,
                    "duration_ms": duration
                },
                level="INFO"
            )

            return response

        except Exception as e:
            duration = int((time.time() - start_time) * 1000)

            audit_log(
                event_type="api",
                message=f"FAILED {request.method} {request.url.path}",
                meta={
                    "trace_id": trace_id,
                    "error": str(e),
                    "duration_ms": duration
                },
                level="ERROR"
            )

            raise
