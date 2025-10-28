"""
Tests for type definitions
"""

import pytest
from pydantic import ValidationError
from x402_solana.types import (
    PaymentRequirements,
    PaymentRequirementsExtra,
    PaymentPayload,
    ExactSvmPayload,
    VerifyResponse,
    SettleResponse,
)


def test_payment_requirements_valid():
    """Test creating valid payment requirements"""
    requirements = PaymentRequirements(
        scheme="exact",
        network="solana-devnet",
        max_amount_required="1000000",
        asset="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        pay_to="2wKupLR9q6wXYppw8Gr2NvWxKBUqm4PPJKkQfoxHDBg4",
        resource="https://api.example.com/data",
        description="Test payment",
        mime_type="application/json",
        max_timeout_seconds=60,
        extra=PaymentRequirementsExtra(
            fee_payer="EwWqGE4ZFKLofuestmU4LDdK7XM1N4ALgdZccwYugwGd"
        )
    )
    
    assert requirements.scheme == "exact"
    assert requirements.network == "solana-devnet"
    assert requirements.max_amount_required == "1000000"


def test_payment_requirements_invalid_amount():
    """Test that invalid amount raises error"""
    with pytest.raises(ValidationError):
        PaymentRequirements(
            scheme="exact",
            network="solana-devnet",
            max_amount_required="invalid",
            asset="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            pay_to="2wKupLR9q6wXYppw8Gr2NvWxKBUqm4PPJKkQfoxHDBg4",
            resource="https://api.example.com/data",
            description="Test payment",
            mime_type="application/json",
            max_timeout_seconds=60,
            extra=PaymentRequirementsExtra(
                fee_payer="EwWqGE4ZFKLofuestmU4LDdK7XM1N4ALgdZccwYugwGd"
            )
        )


def test_payment_payload_valid():
    """Test creating valid payment payload"""
    payload = PaymentPayload(
        x402_version=1,
        scheme="exact",
        network="solana-devnet",
        payload=ExactSvmPayload(transaction="base64_encoded_transaction")
    )
    
    assert payload.x402_version == 1
    assert payload.scheme == "exact"
    assert payload.network == "solana-devnet"


def test_payment_payload_invalid_version():
    """Test that invalid x402 version raises error"""
    with pytest.raises(ValidationError, match="Only x402 version 1 is supported"):
        PaymentPayload(
            x402_version=2,
            scheme="exact",
            network="solana-devnet",
            payload=ExactSvmPayload(transaction="base64_encoded_transaction")
        )


def test_verify_response():
    """Test verify response creation"""
    response = VerifyResponse(
        is_valid=True,
        invalid_reason=None,
        payer="ClientPublicKey"
    )
    
    assert response.is_valid is True
    assert response.invalid_reason is None
    assert response.payer == "ClientPublicKey"


def test_settle_response():
    """Test settle response creation"""
    response = SettleResponse(
        success=True,
        error_reason=None,
        transaction="TransactionSignature",
        network="solana-devnet",
        payer="ClientPublicKey"
    )
    
    assert response.success is True
    assert response.transaction == "TransactionSignature"
    assert response.network == "solana-devnet"
