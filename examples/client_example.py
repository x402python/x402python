"""
Example: Client-side payment creation
Shows how to create a payment header for x402-protected resources
"""

import asyncio
from x402_solana import create_payment_header
from x402_solana.shared.svm.wallet import create_signer_from_bytes
from x402_solana.types import PaymentRequirements, PaymentRequirementsExtra

# Example: Create a payment for an x402-protected API


async def create_payment_example():
    """
    Example of creating a payment header for an x402-protected resource.
    """
    
    # 1. Create a signer from your private key
    # In production, load this securely from environment or wallet
    private_key_hex = "YOUR_PRIVATE_KEY_HEX_HERE"  # 64 hex chars
    private_key_bytes = bytes.fromhex(private_key_hex)
    signer = create_signer_from_bytes(private_key_bytes)
    
    # 2. Define payment requirements
    # These typically come from the server's 402 Payment Required response
    payment_requirements = PaymentRequirements(
        scheme="exact",
        network="solana-devnet",  # or "solana" for mainnet
        max_amount_required="1000000",  # 1 USDC (6 decimals)
        asset="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC mint
        pay_to="2wKupLR9q6wXYppw8Gr2NvWxKBUqm4PPJKkQfoxHDBg4",  # Recipient public key
        resource="https://api.example.com/premium-data",
        description="Access to premium market data",
        mime_type="application/json",
        max_timeout_seconds=60,
        extra=PaymentRequirementsExtra(
            fee_payer="EwWqGE4ZFKLofuestmU4LDdK7XM1N4ALgdZccwYugwGd"  # Facilitator public key
        )
    )
    
    # 3. Create the payment header
    payment_header = await create_payment_header(
        signer=signer,
        x402_version=1,
        payment_requirements=payment_requirements,
    )
    
    print(f"Payment header (use in X-PAYMENT header):")
    print(payment_header)
    
    # 4. Use this header in your HTTP request
    # headers = {
    #     "X-PAYMENT": payment_header,
    #     "Access-Control-Expose-Headers": "X-PAYMENT-RESPONSE"
    # }
    # response = requests.get("https://api.example.com/premium-data", headers=headers)
    
    return payment_header


if __name__ == "__main__":
    asyncio.run(create_payment_example())
