"""
Example: Complete full-stack flow
Demonstrates the complete x402 payment flow from client to facilitator
"""

import asyncio
from x402_solana import create_payment_header
from x402_solana.shared.svm.wallet import create_signer_from_bytes
from x402_solana.types import PaymentRequirements, PaymentRequirementsExtra


async def fullstack_example():
    """
    Complete example showing client creating payment and facilitator verifying/settling.
    """
    
    # === CLIENT SIDE ===
    print("=== CLIENT: Creating payment ===")
    
    # Client's keypair
    client_key_hex = "YOUR_CLIENT_PRIVATE_KEY_HEX"  # Should be 64 hex chars
    client_key_bytes = bytes.fromhex(client_key_hex)
    client_signer = create_signer_from_bytes(client_key_bytes)
    
    # Payment requirements from server (usually received via 402 response)
    requirements = PaymentRequirements(
        scheme="exact",
        network="solana-devnet",
        max_amount_required="1000000",  # 1 USDC
        asset="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
        pay_to="FACILITATOR_PUBKEY_FOR_DEMOS",  # Recipient pubkey
        resource="https://api.example.com/data",
        description="Access to premium API",
        mime_type="application/json",
        max_timeout_seconds=60,
        extra=PaymentRequirementsExtra(
            fee_payer="FACILITATOR_PUBKEY_FOR_DEMOS"  # Facilitator pays fees
        )
    )
    
    # Client creates payment
    payment_header = await create_payment_header(
        signer=client_signer,
        x402_version=1,
        payment_requirements=requirements,
    )
    
    print(f"Created payment header: {payment_header[:50]}...")
    
    # === SIMULATE SERVER ===
    # In real flow, server receives payment header and forwards to facilitator
    
    print("\n=== SERVER: Forwarding to facilitator ===")
    # Server extracts payment_header from X-PAYMENT header
    # Server calls facilitator /verify endpoint (shown in facilitator_example.py)
    
    # === FACILITATOR SIDE ===
    print("\n=== FACILITATOR: Processing payment ===")
    
    # Load facilitator keypair
    facilitator_key_bytes = bytes.fromhex("YOUR_FACILITATOR_KEY_HEX")
    facilitator_signer = create_signer_from_bytes(facilitator_key_bytes)
    
    # Facilitator verifies and settles (see facilitator_example.py for full code)
    print("(Verification and settlement would happen here)")
    
    print("\n=== PAYMENT FLOW COMPLETE ===")


if __name__ == "__main__":
    asyncio.run(fullstack_example())
