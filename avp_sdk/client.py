"""
AVP SDK — Main client.

Usage:
    from avp_sdk import AVPClient

    client = AVPClient("https://avp-protocol.onrender.com")

    challenge = client.challenge("0xYourWallet", "ethereum")
    result    = client.verify(challenge, signature="0x...")
    token_info = client.validate(result.jwt_token)
"""
from __future__ import annotations

import time
from typing import Optional
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode
import json

from avp_sdk.models import Challenge, VerifyResult, TokenInfo, OperatorInfo
from avp_sdk.exceptions import (
    AVPConnectionError, AVPAuthError, AVPRateLimitError,
    AVPSybilError, AVPChallengeError, AVPTokenError, AVPError,
)

_DEFAULT_TIMEOUT = 30
_DEFAULT_RETRIES = 3


class AVPClient:
    """
    AVP client. All methods are synchronous.

    Args:
        base_url:  Base URL of your AVP instance.
                   Default: https://avp-protocol.onrender.com
        timeout:   Request timeout in seconds. Default: 30
        retries:   Number of retries on network errors. Default: 3
    """

    def __init__(
        self,
        base_url: str = "https://avp-protocol.onrender.com",
        timeout: int = _DEFAULT_TIMEOUT,
        retries: int = _DEFAULT_RETRIES,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retries = retries

    # ─────────────────────────────────────────────
    # Public methods
    # ─────────────────────────────────────────────

    def health(self) -> dict:
        """Check if the AVP server is reachable and healthy."""
        return self._get("/health")

    def challenge(self, wallet_address: str, chain: str) -> Challenge:
        """
        Request a challenge message to sign with your wallet.

        Args:
            wallet_address: EVM address (0x...) or Solana public key
            chain:          One of: ethereum, polygon, bsc, solana

        Returns:
            Challenge object. Pass directly to verify().

        Raises:
            AVPConnectionError: Server unreachable
            AVPError:           Unexpected server error
        """
        data = self._post("/challenge", {
            "wallet_address": wallet_address,
            "chain": chain,
        })
        return Challenge(
            challenge_id=data["challenge_id"],
            message=data["message"],
            expires_at=data["expires_at"],
            chain=data["chain"],
            wallet_address=wallet_address,
        )

    def verify(
        self,
        challenge: Challenge,
        signature: str,
        operator_id: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
    ) -> VerifyResult:
        """
        Submit a signed challenge for verification.

        Args:
            challenge:          Challenge object from client.challenge()
            signature:          Wallet signature of challenge.message
                                Use TEST_<anything> in development
            operator_id:        Optional operator ID for trust boost
            device_fingerprint: Optional device fingerprint for trust boost

        Returns:
            VerifyResult with trust_score, trust_tier, permissions, jwt_token

        Raises:
            AVPAuthError:      Signature verification failed
            AVPChallengeError: Challenge expired or already used
            AVPRateLimitError: Wallet is rate limited
            AVPSybilError:     Wallet flagged as HIGH Sybil risk
        """
        payload = {
            "challenge_id": challenge.challenge_id,
            "wallet_address": challenge.wallet_address,
            "chain": challenge.chain,
            "signature": signature,
        }
        if operator_id:
            payload["operator_id"] = operator_id
        if device_fingerprint:
            payload["device_fingerprint"] = device_fingerprint

        data = self._post("/verify", payload)

        if not data.get("success"):
            error = data.get("error", "Verification failed")
            self._raise_verify_error(error)

        return VerifyResult(
            success=data["success"],
            wallet_address=data["wallet_address"],
            trust_score=data["trust_score"],
            trust_tier=data["trust_tier"],
            permissions=data["permissions"],
            jwt_token=data.get("jwt_token"),
            error=data.get("error"),
        )

    def validate(self, token: str) -> TokenInfo:
        """
        Validate a JWT token issued by AVP.

        Args:
            token: JWT token string from VerifyResult.jwt_token

        Returns:
            TokenInfo with valid flag, wallet_address, trust_tier, permissions

        Raises:
            AVPTokenError: Token is invalid or expired
        """
        data = self._get(f"/validate?token={token}")
        if not data.get("valid"):
            raise AVPTokenError(data.get("error", "Invalid or expired token"))
        return TokenInfo(
            valid=data["valid"],
            wallet_address=data.get("wallet_address"),
            trust_tier=data.get("trust_tier"),
            permissions=data.get("permissions"),
            error=data.get("error"),
        )

    def register_operator(self, operator_id: str, stake_amount: float) -> OperatorInfo:
        """
        Register an operator with a stake amount.

        Args:
            operator_id:   Unique identifier for your operator
            stake_amount:  ETH-equivalent stake (minimum 0.1)

        Returns:
            OperatorInfo
        """
        data = self._post(
            f"/operators/register?operator_id={operator_id}&stake_amount={stake_amount}",
            {},
        )
        return OperatorInfo(
            operator_id=data["operator_id"],
            stake_amount=data["stake_amount"],
            slash_count=0,
            verified_count=0,
            trust_multiplier=data["trust_multiplier"],
        )

    def get_operator(self, operator_id: str) -> OperatorInfo:
        """Get operator stats."""
        data = self._get(f"/operators/{operator_id}")
        return OperatorInfo(
            operator_id=data["operator_id"],
            stake_amount=data["stake_amount"],
            slash_count=data["slash_count"],
            verified_count=data["verified_count"],
            trust_multiplier=data["trust_multiplier"],
        )

    # ─────────────────────────────────────────────
    # Convenience: full flow in one call
    # ─────────────────────────────────────────────

    def quick_verify(
        self,
        wallet_address: str,
        chain: str,
        signature: str,
        operator_id: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
    ) -> VerifyResult:
        """
        Convenience method: challenge + verify in one call.

        Args:
            wallet_address: Wallet to verify
            chain:          Chain name
            signature:      Signature of the challenge message
                            Note: You must get the challenge message first
                            to produce a valid signature. Use challenge()
                            for production; this helper is for testing.

        Returns:
            VerifyResult
        """
        ch = self.challenge(wallet_address, chain)
        return self.verify(ch, signature, operator_id, device_fingerprint)

    # ─────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────

    def _post(self, path: str, payload: dict) -> dict:
        url = self.base_url + path
        body = json.dumps(payload).encode()
        req = Request(
            url,
            data=body,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        return self._request(req)

    def _get(self, path: str) -> dict:
        url = self.base_url + path
        req = Request(url, headers={"Accept": "application/json"}, method="GET")
        return self._request(req)

    def _request(self, req: Request) -> dict:
        last_error = None
        for attempt in range(self.retries):
            try:
                with urlopen(req, timeout=self.timeout) as resp:
                    return json.loads(resp.read().decode())
            except HTTPError as e:
                body = {}
                try:
                    body = json.loads(e.read().decode())
                except Exception:
                    pass
                if e.code == 429:
                    raise AVPRateLimitError(
                        body.get("detail", "Rate limited"),
                        retry_after=float(body.get("retry_after", 60)),
                    )
                if e.code >= 400:
                    raise AVPError(body.get("detail", f"HTTP {e.code}"))
            except URLError as e:
                last_error = e
                if attempt < self.retries - 1:
                    time.sleep(2 ** attempt)
        raise AVPConnectionError(
            f"Could not reach AVP server at {self.base_url}: {last_error}"
        )

    def _raise_verify_error(self, error: str) -> None:
        error_lower = error.lower()
        if "signature" in error_lower:
            raise AVPAuthError(error)
        if "challenge" in error_lower or "expired" in error_lower:
            raise AVPChallengeError(error)
        if "rate" in error_lower:
            raise AVPRateLimitError(error)
        if "sybil" in error_lower:
            raise AVPSybilError(error)
        raise AVPError(error)
