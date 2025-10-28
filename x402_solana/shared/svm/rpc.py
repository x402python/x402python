"""
RPC client utilities for connecting to Solana networks
"""

from solders.keypair import Keypair
from solders.transaction import Transaction
from typing import Optional, Literal
import httpx
import asyncio
import base58


# Solana RPC endpoints
MAINNET_ENDPOINTS = [
    "https://api.mainnet-beta.solana.com",
]

DEVNET_ENDPOINTS = [
    "https://api.devnet.solana.com",
]


def create_rpc_client(
    network: Literal["solana", "solana-devnet"],
    custom_url: Optional[str] = None
) -> str:
    """
    Create an RPC URL for the specified Solana network.
    
    Args:
        network: Network identifier ("solana" or "solana-devnet")
        custom_url: Optional custom RPC URL
        
    Returns:
        RPC URL as string
    """
    if custom_url:
        return custom_url
    
    if network == "solana":
        return MAINNET_ENDPOINTS[0]
    elif network == "solana-devnet":
        return DEVNET_ENDPOINTS[0]
    else:
        raise ValueError(f"Unsupported network: {network}")


async def get_latest_blockhash(rpc_url: str) -> tuple[bytes, int]:
    """
    Get the latest blockhash from the network.
    
    Args:
        rpc_url: RPC URL
        
    Returns:
        Tuple of (blockhash_bytes, last_valid_block_height)
    """
    import httpx
    import json
    
    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getLatestBlockhash",
            "params": [{"commitment": "confirmed"}]
        }
        
        response = await client.post(rpc_url, json=payload, timeout=30.0)
        response.raise_for_status()
        
        result = response.json()
        
        if "error" in result:
            raise ValueError(f"RPC error: {result['error']}")
        
        blockhash_str = result["result"]["value"]["blockhash"]
        last_valid_slot = result["result"]["value"]["lastValidBlockHeight"]
        
        # Decode base58 blockhash
        blockhash_bytes = base58.b58decode(blockhash_str)
        
        return blockhash_bytes, last_valid_slot


async def simulate_transaction(
    rpc_url: str,
    transaction: Transaction,
    sig_verify: bool = True
) -> dict:
    """
    Simulate a transaction without sending it.
    
    Args:
        rpc_url: RPC URL
        transaction: Transaction to simulate
        sig_verify: Whether to verify signatures
        
    Returns:
        Simulation result
    """
    # Serialize transaction to wire format
    tx_bytes = bytes(transaction)
    tx_base64 = base64.b64encode(tx_bytes).decode('utf-8')
    
    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "simulateTransaction",
            "params": [
                tx_base64,
                {
                    "sigVerify": sig_verify,
                    "encoding": "base64",
                }
            ]
        }
        
        response = await client.post(rpc_url, json=payload, timeout=30.0)
        response.raise_for_status()
        
        result = response.json()
        
        if "error" in result:
            raise ValueError(f"Simulation error: {result['error']}")
        
        return result["result"]


async def send_and_confirm_transaction(
    rpc_url: str,
    transaction: Transaction,
    commitment: str = "confirmed"
) -> tuple[bool, Optional[str], Optional[Exception]]:
    """
    Send a transaction and wait for confirmation.
    
    Args:
        rpc_url: RPC URL
        transaction: Signed transaction to send
        commitment: Commitment level ("processed", "confirmed", or "finalized")
        
    Returns:
        Tuple of (success, signature, error)
    """
    import httpx
    import base64
    import time
    
    try:
        # Serialize transaction
        tx_bytes = bytes(transaction)
        tx_base64 = base64.b64encode(tx_bytes).decode('utf-8')
        
        # Send transaction
        async with httpx.AsyncClient() as client:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "sendTransaction",
                "params": [
                    tx_base64,
                    {
                        "encoding": "base64",
                        "skipPreflight": False,
                    }
                ]
            }
            
            response = await client.post(rpc_url, json=payload, timeout=60.0)
            response.raise_for_status()
            
            result = response.json()
            
            if "error" in result:
                return False, None, ValueError(f"RPC error: {result['error']}")
            
            signature = result["result"]
            
            # Wait for confirmation
            max_attempts = 40
            for attempt in range(max_attempts):
                status_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getSignatureStatuses",
                    "params": [[signature], {"searchTransactionHistory": True}]
                }
                
                status_response = await client.post(rpc_url, json=status_payload)
                status_result = status_response.json()
                
                if status_result.get("result", {}).get("value", [{}])[0]:
                    return True, signature, None
                
                await asyncio.sleep(0.5)
            
            # Didn't confirm in time, but sent successfully
            return True, signature, None
            
    except Exception as e:
        return False, None, e