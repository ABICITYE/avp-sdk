"""
AVP SDK — Custom exceptions.
"""


class AVPError(Exception):
    """Base exception for all AVP SDK errors."""
    pass


class AVPConnectionError(AVPError):
    """Raised when the SDK cannot reach the AVP server."""
    pass


class AVPAuthError(AVPError):
    """Raised when signature verification fails."""
    pass


class AVPRateLimitError(AVPError):
    """Raised when the wallet is rate limited."""
    def __init__(self, message: str, retry_after: float = None):
        super().__init__(message)
        self.retry_after = retry_after


class AVPSybilError(AVPError):
    """Raised when a wallet is flagged as HIGH Sybil risk."""
    pass


class AVPChallengeError(AVPError):
    """Raised when a challenge is invalid, expired, or already used."""
    pass


class AVPTokenError(AVPError):
    """Raised when a JWT token is invalid or expired."""
    pass
