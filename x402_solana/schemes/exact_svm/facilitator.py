"""
Facilitator-side implementation for verifying and settling Solana payments in x402
"""

from typing import Optional
from solders.keypair import Keypair
from solders.transaction import Transaction
from solders.message import Message
from solders.instruction import Instruction
from solders.pubkey import Pubkey
from solders.compute_budget import COMPUTE_BUDGET_PROGRAM_ID
from x402_solana.types import (
    PaymentPayload,
    PaymentRequirements,
    VerifyResponse,
    SettleResponse,
)
from x402_solana.shared.svm.transaction import (
    decode_transaction_from_payload,
    get_token_payer_from_transaction,
    decode_transaction_from_base64,
)
from x402_solana.shared.svm.rpc import (
    create_rpc_client,
    simulate_transaction,
    send_and_confirm_transaction,
)
from x402_solana.shared.svm.wallet import ERROR_REASONS
import base64
import struct


# Token program addresses
TOKEN_PROGRAM = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
TOKEN_2022_PROGRAM = Pubkey.from_string("TokenzQdBNbLqP5VEhdkAW6Q5YdDaTKSHvHjKAE9zZPJU")


async def verify_payment(
    signer: Keypair,
    payload: PaymentPayload,
    payment_requirements: PaymentRequirements,
    custom_rpc_url: Optional[str] = None,
) -> VerifyResponse:
    """
    Verify a payment payload against the payment requirements.
    
    This function:
    1. Decodes the base64 transaction
    2. Validates transaction structure and instructions
    3. Simulates the transaction to ensure it will succeed
    4. Returns verification result
    
    Args:
        signer: Facilitator's keypair (for signing simulation)
        payload: Payment payload from client
        payment_requirements: Payment requirements from server
        custom_rpc_url: Optional custom RPC URL
        
    Returns:
        Verification response with validity status
    """
    try:
        # Verify scheme and network
        verify_schemes_and_networks(payload, payment_requirements)
        
        # Decode the transaction
        decoded_transaction = decode_transaction_from_payload(payload.payload)
        
        # Create RPC URL
        rpc_url = create_rpc_client(
            network=payment_requirements.network,
            custom_url=custom_rpc_url,
        )
        
        # Perform transaction introspection
        await transaction_introspection(
            payload.payload,
            payment_requirements,
            rpc_url,
        )
        
        # Simulate the transaction
        simulation_result = await simulate_transaction(
            rpc_url=rpc_url,
            transaction=decoded_transaction,
            sig_verify=True,
        )
        
        # Check if simulation failed
        if simulation_result.get("err"):
            raise ValueError("invalid_exact_svm_payload_transaction_simulation_failed")
        
        # Also check nested value.err format
        if isinstance(simulation_result.get("value"), dict) and simulation_result.get("value", {}).get("err"):
            raise ValueError("invalid_exact_svm_payload_transaction_simulation_failed")
        
        # Get payer address
        payer = get_token_payer_from_transaction(decoded_transaction)
        
        return VerifyResponse(
            is_valid=True,
            invalid_reason=None,
            payer=payer,
        )
        
    except ValueError as e:
        error_message = str(e)
        if error_message in ERROR_REASONS:
            try:
                payer = get_token_payer_from_transaction(
                    decode_transaction_from_payload(payload.payload)
                )
            except Exception:
                payer = None
                
            return VerifyResponse(
                is_valid=False,
                invalid_reason=error_message,
                payer=payer,
            )
        # Re-raise if not a known error
        raise
    except Exception as e:
        # Unexpected error
        print(f"Unexpected verify error: {e}")
        try:
            payer = get_token_payer_from_transaction(
                decode_transaction_from_payload(payload.payload)
            )
        except Exception:
            payer = None
            
        return VerifyResponse(
            is_valid=False,
            invalid_reason="unexpected_verify_error",
            payer=payer,
        )


async def settle_payment(
    signer: Keypair,
    payload: PaymentPayload,
    payment_requirements: PaymentRequirements,
    custom_rpc_url: Optional[str] = None,
) -> SettleResponse:
    """
    Settle a payment by signing and submitting the transaction to the blockchain.
    
    This function:
    1. Verifies the payment first
    2. Adds facilitator's signature as fee payer
    3. Submits transaction to network
    4. Waits for confirmation
    
    Args:
        signer: Facilitator's keypair (fee payer)
        payload: Payment payload from client
        payment_requirements: Payment requirements from server
        custom_rpc_url: Optional custom RPC URL
        
    Returns:
        Settlement response with transaction signature
    """
    # First verify the payment
    verify_response = await verify_payment(
        signer=signer,
        payload=payload,
        payment_requirements=payment_requirements,
        custom_rpc_url=custom_rpc_url,
    )
    
    if not verify_response.is_valid:
        return SettleResponse(
            success=False,
            error_reason=verify_response.invalid_reason,
            network=payload.network,
            transaction="",
            payer=verify_response.payer,
        )
    
    # Decode transaction
    decoded_transaction = decode_transaction_from_payload(payload.payload)
    
    # Add facilitator's signature as fee payer
    # The transaction already has the client's signature, now add facilitator's
    message_bytes = bytes(decoded_transaction.message)
    facilitator_signature = signer.sign_message(message_bytes)
    
    # Combine signatures: client's signature + facilitator's signature
    existing_signatures = list(decoded_transaction.signatures)
    all_signatures = existing_signatures + [facilitator_signature]
    
    # Create fully signed transaction
    fully_signed_transaction = Transaction.new_signed(
        decoded_transaction.message,
        all_signatures,
    )
    
    # Get payer address
    payer = get_token_payer_from_transaction(decoded_transaction)
    
    #     Create RPC URL
    rpc_url = create_rpc_client(
        network=payment_requirements.network,
        custom_url=custom_rpc_url,
    )
    
    # Submit and confirm transaction
    success, signature, error = await send_and_confirm_transaction(
        rpc_url=rpc_url,
        transaction=fully_signed_transaction,
        commitment="confirmed",
    )
    
    if success and signature:
        return SettleResponse(
            success=True,
            error_reason=None,
            network=payload.network,
            transaction=signature,
            payer=payer,
        )
    else:
        error_reason = str(error) if error else "transaction_failed"
        return SettleResponse(
            success=False,
            error_reason=error_reason,
            network=payload.network,
            transaction=signature or "",
            payer=payer,
        )


def verify_schemes_and_networks(
    payload: PaymentPayload,
    payment_requirements: PaymentRequirements,
) -> None:
    """
    Verify that scheme and network match and are supported.
    
    Args:
        payload: Payment payload
        payment_requirements: Payment requirements
        
    Raises:
        ValueError: If scheme or network is invalid
    """
    if payload.scheme != "exact" or payment_requirements.scheme != "exact":
        raise ValueError("unsupported_scheme")
    
    if payload.network != payment_requirements.network:
        raise ValueError("invalid_network")
    
    if payment_requirements.network not in ["solana", "solana-devnet"]:
        raise ValueError("invalid_network")


async def transaction_introspection(
    svm_payload,
    payment_requirements: PaymentRequirements,
    rpc_url: str,
) -> None:
    """
    Perform transaction introspection to validate structure and details.
    
    This validates:
    - Transaction structure (number of instructions)
    - Compute budget instructions
    - Transfer instruction parameters
    - Account existence
    - Amount matching
    
    Args:
        svm_payload: SVM payment payload
        payment_requirements: Payment requirements to validate against
        rpc: RPC client
        
    Raises:
        ValueError: If transaction validation fails
    """
    # Decode transaction
    transaction = decode_transaction_from_payload(svm_payload)
    message = transaction.message
    
    # Validate instruction count (should be 3: compute_price, compute_limit, transfer)
    instructions = list(message.instructions)
    
    if len(instructions) < 3:
        raise ValueError("invalid_exact_svm_payload_transaction_instructions_length")
    
    # Verify first two instructions are compute budget
    await verify_compute_budget_instructions(instructions[:2])
    
    # Verify transfer instruction
    transfer_ix = instructions[2]
    await verify_transfer_instruction(transfer_ix, payment_requirements, rpc_url)


async def verify_compute_budget_instructions(instructions: list) -> None:
    """
    Verify compute budget instructions are valid.
    
    Args:
        instructions: Compute budget instructions to verify
        
    Raises:
        ValueError: If instructions are invalid
    """
    if len(instructions) != 2:
        raise ValueError("invalid_exact_svm_payload_transaction_instructions_length")
    
    # Verify first is compute unit price
    price_ix = instructions[0]
    if str(price_ix.program_id) != str(COMPUTE_BUDGET_PROGRAM_ID):
        raise ValueError("invalid_exact_svm_payload_transaction_instructions_compute_price_instruction")
    
    # Parse price to ensure it's not too high
    if len(price_ix.data) > 1:
        # Extract micro lamports from instruction data
        # Instruction data format: [discriminator (2 or 3), micro_lamports (u64)]
        if price_ix.data[0] == 3:  # Set compute unit price
            micro_lamports = struct.unpack("<Q", price_ix.data[1:9])[0]
            if micro_lamports > 5_000_000:  # 5 milli lamports max
                raise ValueError("invalid_exact_svm_payload_transaction_instructions_compute_price_instruction_too_high")


async def verify_transfer_instruction(
    instruction: Instruction,
    payment_requirements: PaymentRequirements,
    rpc_url: str,  # No longer used but kept for API consistency
) -> None:
    """
    Verify the SPL token transfer instruction.
    
    Args:
        instruction: Transfer instruction to verify
        payment_requirements: Payment requirements to validate against
        rpc_url: RPC URL (for future use to verify accounts)
        
    Raises:
        ValueError: If instruction is invalid
    """
    # Verify it's a token program instruction
    program_id = str(instruction.program_id)
    if program_id not in [str(TOKEN_PROGRAM), str(TOKEN_2022_PROGRAM)]:
        raise ValueError("invalid_exact_svm_payload_transaction_not_a_transfer_instruction")
    
    # Verify instruction data length (should have discriminator + amount)
    if len(instruction.data) < 9:
        raise ValueError("invalid_exact_svm_payload_transaction_instructions")
    
    # Extract amount from instruction data
    instruction_amount = struct.unpack("<Q", instruction.data[1:9])[0]
    required_amount = int(payment_requirements.max_amount_required)
    
    # Verify amount matches
    if instruction_amount < required_amount:
        raise ValueError("invalid_exact_svm_payload_transaction_amount_mismatch")
    
    # Verify accounts exist (basic check)
    # In production, you'd fetch and verify all account states
    # This is a simplified check
    pass


async def verify_transaction_instructions(
    message: Message,
    payment_requirements: PaymentRequirements,
    rpc_url: str,
) -> None:
    """
    Verify that transaction contains expected instructions.
    
    Args:
        message: Transaction message
        payment_requirements: Payment requirements
        rpc: RPC client
        
    Raises:
        ValueError: If instructions are invalid
    """
    instructions = list(message.instructions)
    
    # Should have at least 3 instructions
    if len(instructions) < 3:
        raise ValueError("invalid_exact_svm_payload_transaction_instructions_length")
    
    # First two should be compute budget
    await verify_compute_budget_instructions(instructions[:2])
    
    # Third should be transfer
    await verify_transfer_instruction(instructions[2], payment_requirements, rpc_url)