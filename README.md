# avp-sdk

> Python client for the [AVP Agent Verification Protocol](https://github.com/ABICITYE/avp-protocol) — multi-chain wallet trust scoring with Sybil resistance and ZK nullifiers.

## Install

```bash
pip install avp-sdk
```

Zero dependencies. Pure Python stdlib.

## Quick Start

```python
from avp_sdk import AVPClient

client = AVPClient("https://avp-protocol.onrender.com")

# Step 1 — get a challenge message to sign
challenge = client.challenge("0xYourWallet", "ethereum")
print(challenge.message)  # sign this with your wallet

# Step 2 — submit the signature
result = client.verify(challenge, signature="0x...")
print(result.trust_score)   # 75
print(result.trust_tier)    # "verified"
print(result.permissions)   # ["read", "write", "governance_vote"]
print(result.jwt_token)     # "eyJ..."

# Step 3 — validate a token later
info = client.validate(result.jwt_token)
print(info.valid)           # True
print(info.wallet_address)  # "0xYourWallet"
```

## Development Mode

Use `TEST_` prefixed signatures to test without a real wallet:

```python
result = client.quick_verify("0xTestWallet", "ethereum", "TEST_my_signature")
print(result.trust_tier)  # "basic"
```

## Supported Chains

| Chain    | Value      |
|----------|------------|
| Ethereum | `ethereum` |
| Polygon  | `polygon`  |
| BSC      | `bsc`      |
| Solana   | `solana`   |

## Trust Tiers

| Tier      | Score  | Key Permissions                        |
|-----------|--------|----------------------------------------|
| SOVEREIGN | 80–100 | governance_vote, admin_actions         |
| VERIFIED  | 60–79  | write, transfer_standard               |
| BASIC     | 40–59  | read, transfer_limited                 |
| UNTRUSTED | 0–39   | read only                              |

## Boost Trust Score

```python
result = client.verify(
    challenge,
    signature="0x...",
    operator_id="my-operator",         # +15–25 points if operator has stake
    device_fingerprint="browser-hash", # +10 points
)
```

## Error Handling

```python
from avp_sdk import (
    AVPClient,
    AVPAuthError,
    AVPChallengeError,
    AVPRateLimitError,
    AVPSybilError,
    AVPTokenError,
    AVPConnectionError,
)

client = AVPClient("https://avp-protocol.onrender.com")

try:
    challenge = client.challenge("0xWallet", "ethereum")
    result = client.verify(challenge, signature="0x...")
except AVPAuthError:
    print("Signature verification failed")
except AVPChallengeError:
    print("Challenge expired or already used")
except AVPRateLimitError as e:
    print(f"Rate limited — retry in {e.retry_after}s")
except AVPSybilError:
    print("Wallet flagged as Sybil risk")
except AVPConnectionError:
    print("Could not reach AVP server")
```

## Operators

Operators stake ETH-equivalent value to boost trust scores for their users.

```python
# Register an operator
op = client.register_operator("my-operator", stake_amount=1.0)
print(op.is_active)      # True
print(op.trust_multiplier)  # 1.0

# Use operator in verification
result = client.verify(challenge, signature="0x...", operator_id="my-operator")
# Trust score gets +15 bonus from operator stake
```

## Configuration

```python
client = AVPClient(
    base_url="https://your-avp-instance.com",
    timeout=30,   # request timeout in seconds
    retries=3,    # retries on network errors
)
```

## Run Tests

```bash
pip install pytest
pytest tests/ -v
```

Tests run against the live Render API. Requires internet connection.

## Links

- [AVP Protocol GitHub](https://github.com/ABICITYE/avp-protocol)
- [Live API Docs](https://avp-protocol.onrender.com/docs)
- [Report Issues](https://github.com/ABICITYE/avp-protocol/issues)

## License

MIT — Oyewole Emmanuel Abiodun
