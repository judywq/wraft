class QuotaExceededError(Exception):
    """Exception raised when a user's quota is exceeded."""

    def __init__(self, message="Daily quota exceeded"):
        self.message = message
        super().__init__(self.message)
