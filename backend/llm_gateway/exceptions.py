class LimitExceededError(Exception):
    """Exception raised when a user's daily limit is exceeded."""

    def __init__(self, message="Daily limit exceeded"):
        self.message = message
        super().__init__(self.message)
