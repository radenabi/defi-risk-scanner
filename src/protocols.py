"""Known DeFi protocols database."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class Protocol:
    name: str
    slug: str
    chain: str
    category: str  # lending, dex, yield, bridge, etc
    main_contract: str
    tvl_url: str = ""
    website: str = ""
    audits: List[str] = field(default_factory=list)
    deployed_date: str = ""  # YYYY-MM-DD
    exploits: List[str] = field(default_factory=list)
    has_timelock: bool = False
    has_multisig: bool = False
    is_upgradeable: bool = True


PROTOCOLS = {
    "uniswap": Protocol(
        name="Uniswap",
        slug="uniswap",
        chain="ethereum",
        category="dex",
        main_contract="0x1F98431c8aD98523631AE4a59f267346ea31F984",
        website="https://uniswap.org",
        audits=["Trail of Bits", "ABDK"],
        deployed_date="2020-05-05",
        has_timelock=True,
        has_multisig=True,
        is_upgradeable=False,
    ),
    "aave": Protocol(
        name="Aave",
        slug="aave",
        chain="ethereum",
        category="lending",
        main_contract="0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
        website="https://aave.com",
        audits=["Trail of Bits", "OpenZeppelin", "Peckshield"],
        deployed_date="2020-10-01",
        has_timelock=True,
        has_multisig=True,
        is_upgradeable=True,
    ),
    "compound": Protocol(
        name="Compound",
        slug="compound-finance",
        chain="ethereum",
        category="lending",
        main_contract="0xc3d688B66703497DAA19211EEdff47f25384cdc3",
        website="https://compound.finance",
        audits=["Trail of Bits", "OpenZeppelin"],
        deployed_date="2018-09-01",
        has_timelock=True,
        has_multisig=True,
        is_upgradeable=True,
    ),
    "makerdao": Protocol(
        name="MakerDAO",
        slug="makerdao",
        chain="ethereum",
        category="lending",
        main_contract="0x35D1b3F3D7966A1DFe207aa4514C12a259A0492B",
        website="https://makerdao.com",
        audits=["Trail of Bits", "Runtime Verification"],
        deployed_date="2017-12-01",
        has_timelock=True,
        has_multisig=True,
        is_upgradeable=True,
    ),
    "lido": Protocol(
        name="Lido",
        slug="lido",
        chain="ethereum",
        category="staking",
        main_contract="0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84",
        website="https://lido.fi",
        audits=["Quantstamp", "MixBytes", "Statemind"],
        deployed_date="2020-12-01",
        has_timelock=True,
        has_multisig=True,
        is_upgradeable=True,
    ),
    "curve": Protocol(
        name="Curve Finance",
        slug="curve-dex",
        chain="ethereum",
        category="dex",
        main_contract="0x99a58482BD75cbab83b27EC03CA68fF489b5788f",
        website="https://curve.fi",
        audits=["Trail of Bits", "MixBytes"],
        deployed_date="2020-01-01",
        has_timelock=False,
        has_multisig=True,
        is_upgradeable=True,
        exploits=["2023-07 — Vyper reentrancy exploit (~$70M)"],
    ),
    "pancakeswap": Protocol(
        name="PancakeSwap",
        slug="pancakeswap",
        chain="bsc",
        category="dex",
        main_contract="0x10ED43C718714eb63d5aA57B78B54704E256024E",
        website="https://pancakeswap.finance",
        audits=["SlowMist", "Peckshield"],
        deployed_date="2020-09-01",
        has_timelock=True,
        has_multisig=True,
        is_upgradeable=True,
    ),
    "gmx": Protocol(
        name="GMX",
        slug="gmx",
        chain="arbitrum",
        category="derivatives",
        main_contract="0x489ee077994B6658eAfA855C308275EAd8097C4A",
        website="https://gmx.io",
        audits=["ABDK", "Quantstamp"],
        deployed_date="2021-09-01",
        has_timelock=True,
        has_multisig=True,
        is_upgradeable=True,
    ),
}


def lookup_protocol(query: str) -> Protocol | None:
    """Lookup protocol by name or contract address."""
    q = query.lower().strip()
    # Try by slug/name
    for slug, proto in PROTOCOLS.items():
        if q in (slug, proto.name.lower()):
            return proto
    # Try by address
    for proto in PROTOCOLS.values():
        if q == proto.main_contract.lower():
            return proto
    return None


def list_protocols() -> list[Protocol]:
    return list(PROTOCOLS.values())
