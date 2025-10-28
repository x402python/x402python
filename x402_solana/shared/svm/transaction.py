"""
Transaction encoding/decoding and introspection utilities
"""

import base64
from solders.transaction import Transaction
from solders.instruction import Instruction
from solders.keypair import Keypair
from solders.signature import Signature
from solders.hash import Hash
from typing import Optional
from x402_solana.types import ExactSvmPayload


def encode_transaction_to_base64(transaction: Transaction) -> str:
    """
    Encode a Solana transaction to base64 string.
    
    Args:
        transaction: Solana transaction
        
    Returns:
        Base64-encoded transaction
    """
    tx_bytes = bytes(transaction)
    return base64.b64encode(tx_bytes).decode('utf-8')


def decode_transaction_from_base64(encoded: str) -> Transaction:
    """
    Decode a base64-encoded Solana transaction.
    
    Args:
        encoded: Base64-encoded transaction
        
    Returns:
        Decoded transaction
    """
    try:
        tx_bytes = base64.b64decode(encoded)
        return Transaction.from_bytes(tx_bytes)
    except Exception as e:
        raise ValueError("invalid_exact_svm_payload_transaction") from e


def decode_transaction_from_payload(payload: ExactSvmPayload) -> Transaction:
    """
    Decode a transaction from an ExactSvmPayload.
    
    Args:
        payload: SVM payment payload
        
    Returns:
        Decoded transaction
    """
    return decode_transaction_from_base64(payload.transaction)


def get_token_payer_from_transaction(transaction: Transaction) -> Optional[str]:
    """
    Extract the token payer (owner of source token account) from a transaction.
    
    Looks for TransferChecked instructions and extracts the owner account.
    
    Args:
        transaction: Transaction to analyze
        
    Returns:
        Public key of token payer as string, or None if not found
    """
    from solders.message import Message
    
    # SPL Token program addresses
    TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
    TOKEN_2022_PROGRAM = "TokenzQdBNbLqP5VEhdkAW6Q5YdDaTKSHvHjKAE9zZPJU"
    
    message = transaction.message
    if not message:
        return None
    
    # Get static accounts
    static_accounts = message.static_account_keys
    
    # Iterate through instructions
    for instruction in message.instructions:
        program_index = instruction.program_id_index
        program_key = static_accounts[program_index]
        
        # Check if this is a token program instruction
        program_str = str(program_key)
        if program_str == TOKEN_PROGRAM or program_str == TOKEN_2022_PROGRAM:
            account_indices = instruction.account_indexes
            
            # TransferChecked account order: [source, mint, destination, owner, ...]
            if len(account_indices) >= 4:
                owner_index = account_indices[3]
                if owner_index < len(static_accounts):
                    owner_address = str(static_accounts[owner_index])
                    return owner_address
    
    return None


def sign_transaction(transaction: Transaction, signers: list[Keypair]) -> Transaction:
    """
    Sign a transaction with one or more signers.
    
    Args:
        transaction: Transaction to sign
        signers: List of keypair signers
        
    Returns:
        Signed transaction
    """
    # Note: solders Transaction is immutable, so we need to create a new one
    # This is a simplified version - in practice you'd use the proper signing APIs
    
    # Get the latest blockhash from the message
    message = transaction.message
    
    # Collect signatures
    signatures = []
    for signer in signers:
        # Create signature
        signature = signer.sign_message(bytes(message))
        signatures.append(signature)
    
    # Create new transaction with signatures
    return Transaction.new_signed(
        message,
        [k.pubkey() for k in signers],
        signatures
    )


def partially_sign_transaction(
    transaction: Transaction,
    client_keypair: Keypair
) -> Transaction:
    """
    Partially sign a transaction with the client's keypair.
    
    The facilitator will add their signature later to complete the transaction.
    
    Args:
        transaction: Transaction to sign
        client_keypair: Client's keypair
        
    Returns:
        Partially-signed transaction
    """
    return sign_transaction(transaction, [client_keypair])
