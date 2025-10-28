"""
Example: Facilitator-side payment verification and settlement
Shows how to verify and settle payments as a facilitator
"""

import asyncio
from x402_solana import verify_payment, settle_payment, PaymentPayload
from x402_solana.shared.svm.wallet import create_signer_from_bytes
from x402_solana.types import PaymentRequirements, PaymentRequirementsExtra


async def verify_and_settle_example():
    """
    Example of verifying and settling a payment as a facilitator.
    """
    
    # 1. Load facilitator's private key
    # In production, this should be in secure storage
    facilitator_key_hex = "YOUR_FACILITATOR_PRIVATE_KEY_HEX"
    facilitator_key_bytes = bytes.fromhex(facilitator_key_hex)
    facilitator_signer = create_signer_from_bytes(facilitator_key_bytes)
    
    # 2. Receive payment payload from client
    # (In a real implementation, this comes from the resource server)
    payment_payload_dict = {
        "x402Version": 1,
        "scheme": "exact",
        "network": "solana-devnet",
        "payload": {
            "transaction": "base64_encoded_transaction_here"
        }
    }
    
    payment_payload = PaymentPayload(**payment_payload_dict)
    
    # 3. Payment requirements (from resource server)
    payment_requirements = PaymentRequirements(
        scheme="exact",
        network="solana-devnet",
        max_amount_required="1000000",
        asset="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        pay_to="2wKupLR9q6wXYppw8Gr2NvWxKBUqm4PPJKkQfoxHDBg4",
        resource="https://api.example.com/premium-data",
        description="Access to premium market data",
        mime_type="application/json",
        max_timeout_seconds=60,
        extra=PaymentRequirementsExtra(
            fee_payer=str(facilitator_signer.pubkey())  # Facilitator's public key
        )
    )
    
    # 4. Verify the payment
    verify_response = await verify_payment(
        signer=facilitator_signer,
        payload=payment_payload,
        payment_requirements=payment_requirements,
    )
    
    print(f"Verification result: {verify_response.is_valid}")
    if not verify_response.is_valid:
        print(f"Invalid reason: {verify_response.invalid_reason}")
        return
    
    print(f"Payer: {verify_response.payer}")
    
    # 5. If valid, settle the payment
    settle_response = await settle_payment(
        signer=facilitator_signer,
        payload=payment_payload,
        payment_requirements=payment_requirements,
    )
    
    print(f"Settlement result: {settle_response.success}")
    if settle_response.success:
        print(f"Transaction signature: {settle_response.transaction}")
        print(f"Network: {settle_response.network}")
    else:
        print(f"Error: {settle_response.error_reason}")
    
    return settle_response


if __name__ == "__main__":
    asyncio.run(verify_and_settle_example())
