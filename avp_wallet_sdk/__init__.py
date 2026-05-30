"""
avp-sdk — Python client for the AVP Agent Verification Protocol.

Quick start:
    from avp_wallet_sdk import AVPClient

    client = AVPClient("https://avp-protocol.onrender.com")
    challenge = client.challenge("0xYourWallet", "ethereum")
    result    = client.verify(challenge, signature="0x...")

    print(result.trust_score)   # 75
    print(result.trust_tier)    # "verified"
    print(result.permissions)   # ["read", "write", "governance_vote"]
"""

from avp_wallet_sdk.client import AVPClient
from avp_wallet_sdk.models import Challenge, VerifyResult, TokenInfo, OperatorInfo
from avp_wallet_sdk.exceptions import (
    AVPError,
    AVPConnectionError,
    AVPAuthError,
    AVPRateLimitError,
    AVPSybilError,
    AVPChallengeError,
    AVPTokenError,
)

__version__ = "0.1.0"
__author__ = "Oyewole Emmanuel Abiodun"
__all__ = [
    "AVPClient",
    "Challenge",
    "VerifyResult",
    "TokenInfo",
    "OperatorInfo",
    "AVPError",
    "AVPConnectionError",
    "AVPAuthError",
    "AVPRateLimitError",
    "AVPSybilError",
    "AVPChallengeError",
    "AVPTokenError",
]
