import json
import logging
import time
import uuid
from collections.abc import Callable
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Context Variable for request ID tracking
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
user_context_var: ContextVar[dict | None] = ContextVar("user_context", default=None)

class StructuredJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # Extract default fields
        log_data = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "request_id": getattr(record, "request_id", request_id_var.get())
        }

        # Collect additional context parameters, filtering out potential secrets
        for key, val in record.__dict__.items():
            if key not in [
                "args", "asctime", "created", "exc_info", "exc_text", "filename", 
                "funcName", "levelname", "levelno", "lineno", "module", "msecs", 
                "msg", "name", "pathname", "process", "processName", "relativeCreated", 
                "stack_info", "thread", "threadName", "request_id"
            ]:
                # Scrub potential sensitive values
                key_lower = key.lower()
                val_str = str(val).lower()
                if any(s in key_lower or s in val_str for s in ["password", "key", "token", "database_url", "postgres"]):
                    continue
                log_data[key] = val

        return json.dumps(log_data)

def setup_structured_logging():
    # Clear existing handlers
    root = logging.getLogger()
    for h in root.handlers[:]:
        root.removeHandler(h)

    handler = logging.StreamHandler()
    formatter = StructuredJsonFormatter()
    handler.setFormatter(formatter)
    
    root.addHandler(handler)
    root.setLevel(logging.INFO)

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[..., Any]) -> Response:
        # Get request ID from headers or generate new UUID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Store in contextvar
        token = request_id_var.set(request_id)
        
        # Attempt to decode user context from Authorization header
        user_token = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                from app.auth.tokens import decode_access_token
                token_str = auth_header.split(" ")[1]
                payload = decode_access_token(token_str)
                user_id_str = payload.get("sub")
                if user_id_str:
                    username = payload.get("username")
                    user_id = int(user_id_str)
                    user_token = user_context_var.set({
                        "id": user_id, 
                        "username": username or f"user_{user_id}"
                    })
            except Exception:
                pass
                
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_id_var.reset(token)
            if user_token is not None:
                user_context_var.reset(user_token)

@contextmanager
def log_duration(operation: str, **kwargs: Any):
    start = time.perf_counter()
    req_id = request_id_var.get()
    
    # Filter potential secrets from kwargs
    clean_kwargs = {}
    for k, v in kwargs.items():
        if not any(s in k.lower() or s in str(v).lower() for s in ["password", "key", "token", "database_url"]):
            clean_kwargs[k] = v

    logging.getLogger("observability").info(f"Starting {operation}", extra={"request_id": req_id, **clean_kwargs})
    try:
        yield
        duration_ms = (time.perf_counter() - start) * 1000.0
        logging.getLogger("observability").info(
            f"Completed {operation}", 
            extra={
                "request_id": req_id, 
                "operation": operation, 
                "duration_ms": duration_ms, 
                "status": "SUCCESS", 
                **clean_kwargs
            }
        )
    except Exception as e:
        duration_ms = (time.perf_counter() - start) * 1000.0
        logging.getLogger("observability").error(
            f"Failed {operation}: {e}", 
            extra={
                "request_id": req_id, 
                "operation": operation, 
                "duration_ms": duration_ms, 
                "status": "FAILED", 
                **clean_kwargs
            }
        )
        raise
