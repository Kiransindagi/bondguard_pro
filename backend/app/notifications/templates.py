class NotificationTemplateRenderer:
    """
    Renders notification titles and messages based on event type.
    """
    TEMPLATES = {
        "LIMIT_BREACH": {
            "title": "Risk Limit Breach Detected",
            "message": "A {severity} breach occurred for limit {limit_id} on portfolio {portfolio_id}."
        },
        "SEVERE_BREACH": {
            "title": "Severe Risk Breach",
            "message": "CRITICAL: A severe breach requires immediate attention for limit {limit_id}."
        },
        "BREACH_ACKNOWLEDGED": {
            "title": "Breach Acknowledged",
            "message": "Breach for limit {limit_id} was acknowledged. Note: {note}"
        },
        "BREACH_RESOLVED": {
            "title": "Breach Resolved",
            "message": "Breach for limit {limit_id} has been resolved. Note: {note}"
        },
        "PIPELINE_FAILURE": {
            "title": "Pipeline Run Failed",
            "message": "The pipeline {pipeline_id} failed during execution."
        },
        "RATE_MODEL_UNAVAILABLE": {
            "title": "Rate Model Unavailable",
            "message": "The rate model is currently unavailable."
        },
        "MODEL_DEGRADATION": {
            "title": "Model Degradation",
            "message": "The risk model has degraded to {fallback_model}."
        }
    }

    @classmethod
    def render(cls, event_type: str, context: dict) -> tuple[str, str]:
        """
        Returns (title, message)
        """
        # Fallback template if specific one is not found
        template = cls.TEMPLATES.get(
            event_type, 
            {"title": context.get("title", "System Alert"), "message": context.get("message", "An event occurred.")}
        )
        
        title = template["title"].format(**context) if "{" in template["title"] else template["title"]
        # Allow pre-rendered messages via context
        if "message" in context and event_type not in cls.TEMPLATES:
            message = context["message"]
        else:
            message = template["message"].format(**context)
            
        return title, message
