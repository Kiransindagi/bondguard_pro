from sqlalchemy.orm import Session
from app.db.models import AuditEvent
import json
from decimal import Decimal
from datetime import date, datetime

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
        previous_state: dict = None,
        new_state: dict = None,
        metadata: dict = None
    ):
        # Serialize to ensure proper type conversion for JSON column
        prev_json = json.loads(json.dumps(previous_state, cls=AuditJSONEncoder)) if previous_state else None
        new_json = json.loads(json.dumps(new_state, cls=AuditJSONEncoder)) if new_state else None
        meta_json = json.loads(json.dumps(metadata, cls=AuditJSONEncoder)) if metadata else None
        
        audit = AuditEvent(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor=actor,
            previous_state=prev_json,
            new_state=new_json,
            metadata_json=meta_json
        )
        db.add(audit)
        # Flush to persist ordering if needed within transaction
        db.flush()
