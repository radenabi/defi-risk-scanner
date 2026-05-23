"""On-chain data fetchers — Etherscan, DeFiLlama."""
from __future__ import annotations
import os
import httpx
from dataclasses import dataclass, field
from typing import List


def _etherscan_key() -> str:
    return os.environ.get("ETHERSCAN_API_KEY", "")


def fetch_contract_info(address: str, chain: str = "ethereum") -> dict:
    """Fetch contract verification status and source code from Etherscan."""
    base_urls = {
        "ethereum": "https://api.etherscan.io/api",
        "bsc": "https://api.bscscan.com/api",
        "arbitrum": "https://api.arbiscan.io/api",
        "polygon": "https://api.polygonscan.com/api",
        "optimism": "https://api-optimistic.etherscan.io/api",
        "base": "https://api.basescan.org/api",
    }
    base = base_urls.get(chain, base_urls["ethereum"])
    params = {
        "module": "contract",
        "action": "getsourcecode",
        "address": address,
    }
    key = _etherscan_key()
    if key:
        params["apikey"] = key

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(base, params=params)
            data = resp.json()
            if data.get("status") == "1" and data.get("result"):
                result = data["result"][0]
                return {
                    "verified": result.get("SourceCode", "") != "",
                    "contract_name": result.get("ContractName", ""),
                    "compiler": result.get("CompilerVersion", ""),
                    "proxy": result.get("Proxy", "0") == "1",
                    "implementation": result.get("Implementation", ""),
                    "optimization": result.get("OptimizationUsed", "0") == "1",
                }
    except Exception:
        pass
    return {"verified": False, "error": "Failed to fetch"}


def fetch_tvl(slug: str) -> dict:
    """Fetch TVL data from DeFiLlama."""
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(f"https://api.llama.fi/protocol/{slug}")
            if resp.status_code == 200:
                data = resp.json()
                tvl = data.get("tvl", [])
                current_tvl = tvl[-1].get("totalLiquidityUSD", 0) if tvl else 0
                chains = data.get("chains", [])
                chain_tvls = {}
                for chain_data in data.get("currentChainTvls", {}).items():
                    chain_tvls[chain_data[0]] = chain_data[1]
                return {
                    "current_tvl": current_tvl,
                    "chains": chains,
                    "chain_tvls": chain_tvls,
                    "category": data.get("category", ""),
                    "name": data.get("name", slug),
                }
    except Exception:
        pass
    return {"current_tvl": 0, "error": "Failed to fetch"}


def fetch_deployed_block(address: str, chain: str = "ethereum") -> dict:
    """Fetch the first transaction to estimate deployment date."""
    base_urls = {
        "ethereum": "https://api.etherscan.io/api",
        "bsc": "https://api.bscscan.com/api",
        "arbitrum": "https://api.arbiscan.io/api",
    }
    base = base_urls.get(chain, base_urls["ethereum"])
    params = {
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": 1,
        "sort": "asc",
    }
    key = _etherscan_key()
    if key:
        params["apikey"] = key

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(base, params=params)
            data = resp.json()
            if data.get("status") == "1" and data.get("result"):
                tx = data["result"][0]
                return {
                    "first_tx_hash": tx.get("hash", ""),
                    "timestamp": int(tx.get("timeStamp", 0)),
                    "block": int(tx.get("blockNumber", 0)),
                }
    except Exception:
        pass
    return {}


def fetch_admin_info(address: str, chain: str = "ethereum") -> dict:
    """Basic admin/ownership check via contract calls."""
    # This is a simplified check — in production you'd call owner(), admin(), etc.
    base_urls = {
        "ethereum": "https://api.etherscan.io/api",
        "bsc": "https://api.bscscan.com/api",
        "arbitrum": "https://api.arbiscan.io/api",
    }
    base = base_urls.get(chain, base_urls["ethereum"])

    # Check if contract has known ownership patterns
    result = {
        "has_owner_function": False,
        "has_admin_function": False,
        "is_multisig": False,
    }

    # Try to detect Gnosis Safe multisig pattern
    params = {
        "module": "contract",
        "action": "getabi",
        "address": address,
    }
    key = _etherscan_key()
    if key:
        params["apikey"] = key

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(base, params=params)
            data = resp.json()
            if data.get("status") == "1":
                abi = data.get("result", "")
                if "owner" in abi.lower():
                    result["has_owner_function"] = True
                if "admin" in abi.lower():
                    result["has_admin_function"] = True
                if "getowners" in abi.lower() or "threshold" in abi.lower():
                    result["is_multisig"] = True
    except Exception:
        pass

    return result
