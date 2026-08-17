import json
from datetime import date, datetime
from decimal import Decimal

from app.db.models import AuditEvent
from sqlalchemy.orm import Session


class AuditJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

class AuditService:
    @staticmethod
    def append_event(
        db: Session, 
        event_type: str, 
        entity_type: str, 
        entity_id: int, 
        action: str, 
        actor: str = "SYSTEM",
        actor_user_id: int | None = None,
        request_id: str | None = None,
        previous_state: dict | None = None,
        new_state: dict | None = None,
        metadata: dict | None = None
    ):
        from app.core.observability import request_id_var, user_context_var
        
        # Auto-extract request ID if not provided
        final_request_id = request_id or request_id_var.get()
        
        # Auto-extract actor from context var if actor is default "SYSTEM"
        final_actor = actor
        final_actor_user_id = actor_user_id
        
        u_ctx = user_context_var.get()
        if u_ctx:
            if final_actor == "SYSTEM":
                final_actor = u_ctx.get("username", "SYSTEM")
            if final_actor_user_id is None:
                final_actor_user_id = u_ctx.get("id")

        # Serialize to ensure proper type conversion for JSON column
        prev_json = json.loads(json.dumps(previous_state, cls=AuditJSONEncoder)) if previous_state else None
        new_json = json.loads(json.dumps(new_state, cls=AuditJSONEncoder)) if new_state else None
        meta_json = json.loads(json.dumps(metadata, cls=AuditJSONEncoder)) if metadata else None
        
        audit = AuditEvent(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor=final_actor,
            actor_user_id=final_actor_user_id,
            request_id=final_request_id,
            previous_state=prev_json,
            new_state=new_json,
            metadata_json=meta_json
        )
        db.add(audit)
        # Flush to persist ordering if needed within transaction
        db.flush()
