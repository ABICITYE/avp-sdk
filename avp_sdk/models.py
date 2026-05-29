"""
AVP SDK — Response models.
Clean Python objects returned from every client method.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class Challenge:
    """Returned by client.challenge(). Pass directly to client.verify()."""
    challenge_id: str
    message: str
    expires_at: float
    chain: str
    wallet_address: str

    def __repr__(self):
        return (
            f"Challenge(id={self.challenge_id[:8]}..., "
            f"chain={self.chain}, "
            f"wallet={self.wallet_address[:10]}...)"
        )


@dataclass
class VerifyResult:
    """Returned by client.verify() on success."""
    success: bool
    wallet_address: str
    trust_score: int
    trust_tier: str
    permissions: list[str]
    jwt_token: Optional[str] = None
    error: Optional[str] = None

    @property
    def is_sovereign(self) -> bool:
        return self.trust_tier == "sovereign"

    @property
    def is_verified(self) -> bool:
        return self.trust_tier in ("sovereign", "verified")

    @property
    def can(self) -> set[str]:
        """Quick permission check. Usage: result.can >= {'read', 'write'}"""
        return set(self.permissions)

    def __repr__(self):
        return (
            f"VerifyResult(wallet={self.wallet_address[:10]}..., "
            f"score={self.trust_score}, "
            f"tier={self.trust_tier})"
        )


@dataclass
class TokenInfo:
    """Returned by client.validate()."""
    valid: bool
    wallet_address: Optional[str] = None
    trust_tier: Optional[str] = None
    permissions: Optional[list[str]] = None
    error: Optional[str] = None

    def __repr__(self):
        if self.valid:
            return f"TokenInfo(valid=True, wallet={self.wallet_address[:10]}..., tier={self.trust_tier})"
        return f"TokenInfo(valid=False, error={self.error})"


@dataclass
class OperatorInfo:
    """Returned by client.get_operator()."""
    operator_id: str
    stake_amount: float
    slash_count: int
    verified_count: int
    trust_multiplier: float

    @property
    def is_active(self) -> bool:
        return self.stake_amount >= 0.1

    @property
    def slash_rate(self) -> float:
        total = self.verified_count + self.slash_count
        return self.slash_count / total if total > 0 else 0.0
