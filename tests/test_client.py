"""
AVP SDK Test Suite.
Tests against the live Render API using TEST_ signatures.
Run: python -m pytest tests/ -v
"""
import pytest
from avp_wallet_sdk import AVPClient, AVPAuthError, AVPChallengeError, AVPTokenError

BASE_URL = "https://avp-protocol.onrender.com"
WALLET = "0xSDKTestWallet001"
CHAIN = "ethereum"

@pytest.fixture
def client():
    return AVPClient(BASE_URL)


class TestHealth:
    def test_health_returns_ok(self, client):
        result = client.health()
        assert result["status"] == "ok"
        assert result["protocol"] == "AVP"


class TestChallenge:
    def test_challenge_returns_challenge_object(self, client):
        ch = client.challenge(WALLET, CHAIN)
        assert ch.challenge_id
        assert ch.message
        assert WALLET in ch.message
        assert ch.chain == CHAIN
        assert ch.wallet_address == WALLET

    def test_challenge_message_contains_chain(self, client):
        ch = client.challenge(WALLET, "polygon")
        assert "polygon" in ch.message.lower()

    def test_challenge_repr(self, client):
        ch = client.challenge(WALLET, CHAIN)
        assert "Challenge(" in repr(ch)

    def test_solana_challenge(self, client):
        ch = client.challenge("DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG3LZSQ", "solana")
        assert ch.chain == "solana"


class TestVerify:
    def test_successful_verify(self, client):
        ch = client.challenge(WALLET, CHAIN)
        result = client.verify(ch, signature="TEST_sdk_test")
        assert result.success
        assert result.trust_score >= 40
        assert result.trust_tier in ("sovereign", "verified", "basic", "untrusted")
        assert len(result.permissions) > 0
        assert result.jwt_token is not None

    def test_verify_with_device_fingerprint(self, client):
        ch = client.challenge(WALLET, CHAIN)
        result = client.verify(ch, signature="TEST_sdk_fp", device_fingerprint="sdk-test-fp-001")
        assert result.success
        assert result.trust_score >= 50

    def test_bad_signature_raises_auth_error(self, client):
        ch = client.challenge(WALLET, CHAIN)
        with pytest.raises(AVPAuthError):
            client.verify(ch, signature="BAD_SIGNATURE")

    def test_stale_challenge_raises_challenge_error(self, client):
        ch = client.challenge(WALLET, CHAIN)
        client.verify(ch, signature="TEST_first_use")
        with pytest.raises(AVPChallengeError):
            client.verify(ch, signature="TEST_replay")

    def test_result_properties(self, client):
        ch = client.challenge(WALLET, CHAIN)
        result = client.verify(ch, signature="TEST_props")
        assert isinstance(result.is_sovereign, bool)
        assert isinstance(result.is_verified, bool)
        assert isinstance(result.can, set)
        assert "read" in result.can

    def test_result_repr(self, client):
        ch = client.challenge(WALLET, CHAIN)
        result = client.verify(ch, signature="TEST_repr")
        assert "VerifyResult(" in repr(result)


class TestValidate:
    def test_validate_valid_token(self, client):
        ch = client.challenge(WALLET, CHAIN)
        result = client.verify(ch, signature="TEST_validate")
        token_info = client.validate(result.jwt_token)
        assert token_info.valid
        assert token_info.wallet_address == WALLET
        assert token_info.trust_tier is not None
        assert len(token_info.permissions) > 0

    def test_validate_invalid_token_raises(self, client):
        with pytest.raises(AVPTokenError):
            client.validate("invalid.token.here")

    def test_token_info_repr(self, client):
        ch = client.challenge(WALLET, CHAIN)
        result = client.verify(ch, signature="TEST_repr2")
        info = client.validate(result.jwt_token)
        assert "TokenInfo(" in repr(info)


class TestQuickVerify:
    def test_quick_verify(self, client):
        result = client.quick_verify(WALLET, CHAIN, "TEST_quick")
        assert result.success
        assert result.jwt_token


class TestOperators:
    def test_register_and_get_operator(self, client):
        op = client.register_operator("sdk-test-op-001", 1.0)
        assert op.operator_id == "sdk-test-op-001"
        assert op.stake_amount >= 1.0
        assert op.is_active

    def test_operator_slash_rate(self, client):
        op = client.register_operator("sdk-test-op-002", 2.0)
        assert op.slash_rate == 0.0
