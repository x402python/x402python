# Project Structure

This document outlines the structure of the x402 Python Solana implementation.

## Directory Structure

```
x402-python-solana/
├── x402_solana/              # Main package
│   ├── __init__.py           # Package exports
│   ├── types/                # Type definitions
│   │   ├── __init__.py
│   │   ├── payment.py        # PaymentPayload, PaymentRequirements
│   │   └── responses.py      # VerifyResponse, SettleResponse
│   ├── shared/
│   │   └── svm/              # Shared Solana utilities
│   │       ├── __init__.py
│   │       ├── wallet.py    # Keypair creation, signing
│   │       ├── rpc.py       # RPC client wrapper
│   │       └── transaction.py # Transaction encoding/decoding
│   └── schemes/
│       └── exact_svm/        # Exact payment scheme for Solana
│           ├── __init__.py
│           ├── client.py    # Client-side payment creation
│           └── facilitator.py # Facilitator verification/settlement
├── examples/                 # Usage examples
│   ├── client_example.py     # Client payment creation
│   ├── facilitator_example.py # Facilitator verification/settlement
│   └── fullstack_example.py # Complete flow
├── tests/                    # Test suite
│   ├── __init__.py
│   ├── test_wallet.py       # Wallet utility tests
│   └── test_types.py        # Type validation tests
├── README.md                 # Main documentation
├── LICENSE                   # Apache 2.0 license
├── pyproject.toml           # Project configuration
└── .gitignore               # Git ignore rules
```

## Package Organization

### Core Modules

**`x402_solana.types`**

- Type definitions using Pydantic
- Payment requirements and payloads
- Facilitator response types

**`x402_solana.schemes.exact_svm`**

- Client: Creates partially-signed transactions
- Facilitator: Verifies and settles transactions

**`x402_solana.shared.svm`**

- Wallet utilities for keypair management
- RPC client for Solana networks
- Transaction encoding/decoding

## API Overview

### Client Side

```python
from x402_solana import create_payment_header

# Create payment header from requirements
payment_header = await create_payment_header(
    signer=signer,
    x402_version=1,
    payment_requirements=requirements
)
```

### Facilitator Side

```python
from x402_solana import verify_payment, settle_payment

# Verify payment
verify_response = await verify_payment(
    signer=facilitator_signer,
    payload=payment_payload,
    payment_requirements=requirements
)

# Settle payment if valid
if verify_response.is_valid:
    settle_response = await settle_payment(
        signer=facilitator_signer,
        payload=payment_payload,
        payment_requirements=requirements
    )
```

## Testing

The test suite includes:

- Wallet utility tests
- Type validation tests
- Pydantic model tests

Run tests with:

```bash
pytest
```

## Configuration

Project configuration is in `pyproject.toml`:

- Python >= 3.10
- Dependencies: solana, solders, spl-token, pydantic, httpx
- Dev dependencies: pytest, ruff, mypy

## License

Apache-2.0
