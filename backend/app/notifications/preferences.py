

class NotificationPreferences:
    """
    Manages user preferences for notification delivery channels.
    """
    
    @staticmethod
    def get_user_channels(user_id: int, event_type: str, severity: str) -> list[str]:
        """
        Returns a list of channel names (e.g., ['in_app', 'email']) for a given user and event.
        Currently stubbed to always return ['in_app'].
        """
        # In a real implementation, this would query a user_preferences table
        # based on event_type or severity (e.g., SEVERE might trigger 'email' as well).
        return ["in_app"]
