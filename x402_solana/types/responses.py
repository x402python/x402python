"""
Response types for verification and settlement
"""

from pydantic import BaseModel, Field
from typing import Optional
from typing_extensions import Literal


class VerifyResponse(BaseModel):
    """Response from facilitator verification endpoint"""
    
    is_valid: bool = Field(..., alias="isValid")
    """Whether the payment is valid"""
    
    invalid_reason: Optional[str] = Field(None, alias="invalidReason")
    """Reason why payment is invalid (if not valid)"""
    
    payer: Optional[str] = None
    """Address of the payer (owner of source token account)"""
    
    class Config:
        populate_by_name = True


class SettleResponse(BaseModel):
    """Response from facilitator settlement endpoint"""
    
    success: bool
    """Whether settlement was successful"""
    
    error_reason: Optional[str] = Field(None, alias="errorReason")
    """Error reason if settlement failed"""
    
    transaction: str
    """Transaction signature (base58 encoded)"""
    
    network: Literal["solana", "solana-devnet"]
    """Network where transaction was settled"""
    
    payer: Optional[str] = None
    """Address of the payer"""
    
    class Config:
        populate_by_name = True
