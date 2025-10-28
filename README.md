# x402 Python Solana Implementation

A standalone Python implementation of the [x402 payment protocol](https://github.com/coinbase/x402) for Solana (SVM) networks.

## Overview

This package provides the core functionality for implementing x402 payments on Solana, enabling:

- **Client-side**: Creating partially-signed token transfer transactions
- **Facilitator-side**: Verifying and settling transactions
- **Gasless payments**: Clients don't need SOL for fees (facilitator covers fees)

## What is x402?

x402 is an internet-native payment protocol that enables micropayments for digital resources using blockchain technology. It uses the standard HTTP 402 "Payment Required" status code to indicate that payment is needed.

For more information about the x402 protocol, see the [official documentation](https://github.com/coinbase/x402).

## Installation

```bash
# Using pip
pip install -e .

# Or using uv (recommended for faster installs)
uv pip install -e .
```

## Quick Start

### Client Side - Creating Payments

```python
from x402_solana.schemes.exact_svm.client import create_payment_header
from x402_solana.shared.svm.wallet import create_signer_from_bytes
from x402_solana.types import PaymentRequirements

# Create a signer from private key
private_key_bytes = bytes.fromhex("your_private_key_hex")
signer = create_signer_from_bytes(private_key_bytes)

# Define payment requirements (typically received from server via 402 response)
requirements = PaymentRequirements(
    scheme="exact",
    network="solana-devnet",
    max_amount_required="1000000",  # 1 USDC (6 decimals)
    asset="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC mint
    pay_to="RecipientPublicKey...",
    resource="https://api.example.com/protected-endpoint",
    description="Access to premium API",
    mime_type="application/json",
    max_timeout_seconds=60,
    extra={"feePayer": "FacilitatorPublicKey..."}
)

# Create payment header
payment_header = await create_payment_header(
    signer=signer,
    x402_version=1,
    payment_requirements=requirements
)

# Use payment_header in X-PAYMENT HTTP header
```

### Facilitator Side - Verifying Payments

```python
from x402_solana.schemes.exact_svm.facilitator import verify_payment, settle_payment
from x402_solana.types import PaymentPayload, PaymentRequirements

# Verify the payment
verify_response = await verify_payment(
    signer=facilitator_signer,
    payload=payment_payload,
    payment_requirements=requirements
)

if verify_response.is_valid:
    # Settle the payment
    settle_response = await settle_payment(
        signer=facilitator_signer,
        payload=payment_payload,
        payment_requirements=requirements
    )
```

## Architecture

```
x402_solana/
├── schemes/              # Payment scheme implementations
│   └── exact_svm/
│       ├── client.py     # Client-side payment creation
│       └── facilitator.py # Facilitator verification/settlement
├── shared/
│   └── svm/             # Shared Solana utilities
│       ├── wallet.py    # Solana wallet/signer utilities
│       ├── rpc.py       # RPC client wrappers
│       └── transaction.py # Transaction encoding/decoding
├── types/               # Type definitions and schemas
│   ├── __init__.py
│   ├── payment.py      # Payment payload types
│   └── requirements.py # Payment requirements types
└── clients/             # Client-side HTTP integration
    └── httpx.py        # httpx-based client with x402 support
```

## Supported Networks

- `solana` - Solana Mainnet
- `solana-devnet` - Solana Devnet

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=x402_solana --cov-report=html

# Type checking
mypy x402_solana

# Linting
ruff check x402_solana
```

## Examples

See the `examples/` directory for complete working examples:

- `client_example.py` - Client-side payment creation
- `facilitator_example.py` - Facilitator verification and settlement
- `fullstack_example.py` - Complete flow

## Differences from EVM x402

This implementation is specifically for Solana (SVM), which differs from the EVM implementation in:

1. **Transaction Format**: Uses Solana transaction format with SPL token transfers
2. **Signature Model**: Partial signatures (client signs first, facilitator adds signature)
3. **Gas/Fees**: Uses compute units instead of gas, facilitator pays fees
4. **Token Accounts**: Uses Associated Token Accounts (ATAs) instead of ERC-20 direct transfers
5. **Payment Payload**: Base64-encoded Solana transaction vs EIP-712 signature

## Components

### Type Definitions (`types/`)
- `PaymentRequirements`: Payment details from server's 402 response
- `PaymentPayload`: Client payment payload with signed transaction
- `ExactSvmPayload`: Solana-specific payload format
- `VerifyResponse`/`SettleResponse`: Facilitator operation results

### Client Implementation (`schemes/exact_svm/client.py`)
- Creates partially-signed Solana token transfer transactions
- Handles SPL token instructions with fallback support
- Implements proper ATA (Associated Token Account) derivation
- JSON and base64 encoding for payment headers

### Facilitator Implementation (`schemes/exact_svm/facilitator.py`)
- Validates transaction structure and simulates execution
- Verifies compute budget and transfer instructions
- Adds facilitator signature for fee payment
- Submits and confirms transactions on Solana networks

### Shared Utilities (`shared/svm/`)
- **wallet.py**: Keypair creation, signing, error definitions
- **rpc.py**: JSON-RPC client for Solana networks (mainnet/devnet)
- **transaction.py**: Transaction encoding/decoding and payer extraction

## Key Features

- **Multi-signature Support**: Client signs first, facilitator adds signature as fee payer
- **Gasless for Client**: Facilitator pays all transaction fees
- **Type Safety**: Full Pydantic validation throughout
- **Network Support**: Mainnet and devnet configurations
- **Error Handling**: Comprehensive error codes matching TypeScript implementation
- **Library Integration**: Uses spl-token library with manual fallback

## Development

This implementation follows the same architecture as the TypeScript x402 library and adapts it for Python and Solana-specific libraries.

## Contributing

Contributions are welcome. Please follow the coding standards and include tests for new features.

## License

Apache-2.0
