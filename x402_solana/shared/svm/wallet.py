"""
Solana wallet and signer utilities for x402
"""

from solders.keypair import Keypair
from solders.pubkey import Pubkey
from typing import Optional
from solders.instruction import AccountMeta
from solders.rpc.config import RpcSendTransactionConfig


# Error reasons for payment validation
ERROR_REASONS = [
    "unsupported_scheme",
    "invalid_network",
    "invalid_exact_svm_payload_transaction",
    "invalid_exact_svm_payload_transaction_instructions_length",
    "invalid_exact_svm_payload_transaction_instructions",
    "invalid_exact_svm_payload_transaction_instructions_compute_limit_instruction",
    "invalid_exact_svm_payload_transaction_instructions_compute_price_instruction",
    "invalid_exact_svm_payload_transaction_instructions_compute_price_instruction_too_high",
    "invalid_exact_svm_payload_transaction_create_ata_instruction",
    "invalid_exact_svm_payload_transaction_create_ata_instruction_incorrect_payee",
    "invalid_exact_svm_payload_transaction_create_ata_instruction_incorrect_asset",
    "invalid_exact_svm_payload_transaction_transfer_to_incorrect_ata",
    "invalid_exact_svm_payload_transaction_sender_ata_not_found",
    "invalid_exact_svm_payload_transaction_receiver_ata_not_found",
    "invalid_exact_svm_payload_transaction_amount_mismatch",
    "invalid_exact_svm_payload_transaction_instruction_not_spl_token_transfer_checked",
    "invalid_exact_svm_payload_transaction_instruction_not_token_2022_transfer_checked",
    "invalid_exact_svm_payload_transaction_not_a_transfer_instruction",
    "invalid_exact_svm_payload_transaction_simulation_failed",
    "unexpected_verify_error",
    "unexpected_settle_error",
]


def create_signer_from_bytes(private_key_bytes: bytes) -> Keypair:
    """
    Create a Solana keypair signer from private key bytes.
    
    Args:
        private_key_bytes: Raw private key bytes (32 bytes)
        
    Returns:
        Keypair for signing transactions
    """
    if len(private_key_bytes) != 32:
        raise ValueError("Private key must be 32 bytes")
    return Keypair.from_bytes(private_key_bytes)


def create_signer_from_base58(private_key_base58: str) -> Keypair:
    """
    Create a Solana keypair signer from base58-encoded private key.
    
    Args:
        private_key_base58: Base58-encoded private key
        
    Returns:
        Keypair for signing transactions
    """
    try:
        key_bytes = bytes.fromhex(private_key_base58)
        if len(key_bytes) == 32:
            return Keypair.from_bytes(key_bytes)
        elif len(key_bytes) == 64:
            # 64 bytes means concatenated private + public key
            return Keypair.from_bytes(key_bytes[:32])
    except ValueError:
        pass
    
    # Try direct base58 decoding
    try:
        return Keypair.from_seed(bytes.fromhex(private_key_base58))
    except Exception:
        raise ValueError("Invalid private key format. Expected 32-byte hex or base58")


def is_valid_pubkey(address: str) -> bool:
    """
    Check if a string is a valid Solana public key.
    
    Args:
        address: String to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        Pubkey.from_string(address)
        return True
    except Exception:
        return False


def to_account_meta(pubkey: Pubkey, is_signer: bool, is_writable: bool) -> AccountMeta:
    """
    Create an AccountMeta object.
    
    Args:
        pubkey: Public key
        is_signer: Whether account is a signer
        is_writable: Whether account is writable
        
    Returns:
        AccountMeta object
    """
    return AccountMeta(pubkey=pubkey, is_signer=is_signer, is_writable=is_writable)
