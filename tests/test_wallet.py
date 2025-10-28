"""
Tests for wallet utilities
"""

import pytest
from solders.keypair import Keypair
from x402_solana.shared.svm.wallet import (
    create_signer_from_bytes,
    create_signer_from_base58,
    is_valid_pubkey,
)


def test_create_signer_from_bytes():
    """Test creating signer from 32-byte private key"""
    # Generate a random keypair
    keypair = Keypair()
    private_bytes = bytes(keypair)
    
    # Create signer from bytes
    signer = create_signer_from_bytes(private_bytes)
    
    assert signer is not None
    assert isinstance(signer, Keypair)


def test_create_signer_from_bytes_invalid():
    """Test that invalid byte length raises error"""
    with pytest.raises(ValueError, match="Private key must be 32 bytes"):
        create_signer_from_bytes(b"invalid")


def test_is_valid_pubkey():
    """Test public key validation"""
    keypair = Keypair()
    valid_pubkey = str(keypair.pubkey())
    
    assert is_valid_pubkey(valid_pubkey) is True
    assert is_valid_pubkey("invalid") is False
    assert is_valid_pubkey("") is False
