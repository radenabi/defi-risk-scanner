"""Risk analysis engine — scores protocols across 8 risk factors."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List

from .protocols import Protocol
from .onchain import fetch_contract_info, fetch_tvl, fetch_admin_info


@dataclass
class RiskFactor:
    name: str
    weight: float  # 0.0 - 1.0
    score: float   # 0 (safe) - 100 (critical)
    grade: str     # A-F
    details: str
    recommendation: str


@dataclass
class RiskReport:
    protocol: Protocol
    factors: List[RiskFactor] = field(default_factory=list)
    overall_score: float = 0.0
    overall_grade: str = ""
    tvl_data: dict = field(default_factory=dict)
    contract_info: dict = field(default_factory=dict)
    admin_info: dict = field(default_factory=dict)

    def compute_overall(self):
        if not self.factors:
            return
        total_weight = sum(f.weight for f in self.factors)
        if total_weight == 0:
            return
        self.overall_score = sum(f.score * f.weight for f in self.factors) / total_weight
        self.overall_grade = score_to_grade(self.overall_score)


def score_to_grade(score: float) -> str:
    if score <= 15:
        return "A"
    elif score <= 30:
        return "B"
    elif score <= 50:
        return "C"
    elif score <= 70:
        return "D"
    elif score <= 85:
        return "E"
    else:
        return "F"


def grade_color(grade: str) -> str:
    return {
        "A": "green", "B": "green", "C": "yellow",
        "D": "red", "E": "red", "F": "red",
    }.get(grade, "white")


def analyze_tvl_concentration(protocol: Protocol) -> RiskFactor:
    """Check if TVL is concentrated in few wallets."""
    tvl_data = fetch_tvl(protocol.slug)
    tvl = tvl_data.get("current_tvl", 0)
    chains = tvl_data.get("chains", [])

    if tvl == 0:
        return RiskFactor(
            name="TVL Concentration",
            weight=0.15,
            score=80,
            grade="E",
            details="Could not fetch TVL data or TVL is zero.",
            recommendation="Verify protocol is active and has liquidity.",
        )

    # Multi-chain is generally safer (less concentration)
    chain_count = len(chains)
    if chain_count >= 5:
        score = 10
        grade = "A"
        detail = f"TVL ${tvl:,.0f} across {chain_count} chains — well diversified."
    elif chain_count >= 3:
        score = 25
        grade = "B"
        detail = f"TVL ${tvl:,.0f} across {chain_count} chains — moderate diversification."
    elif chain_count >= 2:
        score = 45
        grade = "C"
        detail = f"TVL ${tvl:,.0f} across {chain_count} chains — some concentration risk."
    else:
        score = 60
        grade = "D"
        detail = f"TVL ${tvl:,.0f} on single chain — higher concentration risk."

    return RiskFactor(
        name="TVL Concentration",
        weight=0.15,
        score=score,
        grade=grade,
        details=detail,
        recommendation="Prefer protocols with multi-chain presence for diversification." if chain_count < 3 else "Good diversification.",
    )


def analyze_admin_keys(protocol: Protocol) -> RiskFactor:
    """Evaluate admin key setup — multisig, timelock, EOA."""
    score = 50  # default medium risk
    details = []
    recs = []

    if protocol.has_multisig:
        score -= 20
        details.append("Uses multisig for governance.")
    else:
        score += 15
        details.append("No known multisig — higher centralization risk.")
        recs.append("Implement multisig (e.g., Gnosis Safe) for admin functions.")

    if protocol.has_timelock:
        score -= 15
        details.append("Has timelock on governance actions.")
    else:
        score += 10
        details.append("No timelock — admin changes take effect immediately.")
        recs.append("Add timelock (24-48h) for governance actions.")

    if protocol.is_upgradeable:
        score += 10
        details.append("Contracts are upgradeable — admin can change logic.")
        recs.append("Consider renouncing upgradeability or adding strict governance.")
    else:
        score -= 10
        details.append("Contracts are immutable — no upgrade risk.")

    score = max(0, min(100, score))
    grade = score_to_grade(score)

    return RiskFactor(
        name="Admin Keys",
        weight=0.20,
        score=score,
        grade=grade,
        details=" ".join(details),
        recommendation=" ".join(recs) if recs else "Admin key setup looks reasonable.",
    )


def analyze_contract_verification(protocol: Protocol) -> RiskFactor:
    """Check if source code is verified on block explorer."""
    info = fetch_contract_info(protocol.main_contract, protocol.chain)
    verified = info.get("verified", False)
    contract_name = info.get("contract_name", "Unknown")

    if verified:
        return RiskFactor(
            name="Contract Verification",
            weight=0.10,
            score=5,
            grade="A",
            details=f"Source code verified on explorer. Contract: {contract_name}.",
            recommendation="Good — source code is publicly auditable.",
        )
    else:
        return RiskFactor(
            name="Contract Verification",
            weight=0.10,
            score=80,
            grade="E",
            details="Source code NOT verified on block explorer.",
            recommendation="Unverified contracts are a major red flag — avoid.",
        )


def analyze_protocol_age(protocol: Protocol) -> RiskFactor:
    """Older protocols are battle-tested."""
    if not protocol.deployed_date:
        return RiskFactor(
            name="Protocol Age",
            weight=0.05,
            score=50,
            grade="C",
            details="Deployment date unknown.",
            recommendation="Verify protocol deployment date before depositing funds.",
        )

    deployed = datetime.strptime(protocol.deployed_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    days = (now - deployed).days

    if days >= 1095:  # 3+ years
        score, grade = 5, "A"
        detail = f"Deployed {days} days ago ({protocol.deployed_date}) — battle-tested."
    elif days >= 730:  # 2+ years
        score, grade = 15, "B"
        detail = f"Deployed {days} days ago ({protocol.deployed_date}) — mature protocol."
    elif days >= 365:  # 1+ year
        score, grade = 30, "B"
        detail = f"Deployed {days} days ago ({protocol.deployed_date}) — moderate track record."
    elif days >= 180:
        score, grade = 55, "C"
        detail = f"Deployed {days} days ago ({protocol.deployed_date}) — relatively new."
    else:
        score, grade = 75, "D"
        detail = f"Deployed {days} days ago ({protocol.deployed_date}) — new protocol, higher risk."

    return RiskFactor(
        name="Protocol Age",
        weight=0.05,
        score=score,
        grade=grade,
        details=detail,
        recommendation="Newer protocols carry more risk — start with small amounts." if days < 365 else "Good track record.",
    )


def analyze_audit_status(protocol: Protocol) -> RiskFactor:
    """Check audit history."""
    audit_count = len(protocol.audits)

    if audit_count == 0:
        return RiskFactor(
            name="Audit Status",
            weight=0.15,
            score=85,
            grade="F",
            details="No known audits.",
            recommendation="Unaudited protocols carry extreme risk. Avoid depositing significant funds.",
        )
    elif audit_count == 1:
        return RiskFactor(
            name="Audit Status",
            weight=0.15,
            score=40,
            grade="C",
            details=f"Audited by: {', '.join(protocol.audits)}. Single audit is basic coverage.",
            recommendation="Consider protocols with multiple independent audits.",
        )
    elif audit_count == 2:
        return RiskFactor(
            name="Audit Status",
            weight=0.15,
            score=20,
            grade="B",
            details=f"Audited by: {', '.join(protocol.audits)}. Good coverage.",
            recommendation="Solid audit coverage.",
        )
    else:
        return RiskFactor(
            name="Audit Status",
            weight=0.15,
            score=8,
            grade="A",
            details=f"Audited by: {', '.join(protocol.audits)}. Extensive audit coverage.",
            recommendation="Excellent audit coverage.",
        )


def analyze_centralization(protocol: Protocol) -> RiskFactor:
    """Evaluate centralization risks."""
    score = 40
    details = []
    recs = []

    if protocol.is_upgradeable:
        score += 15
        details.append("Upgradeable contracts — admin can change logic.")
        recs.append("Monitor governance proposals for upgrade changes.")

    if not protocol.has_timelock:
        score += 10
        details.append("No timelock — instant changes possible.")

    if protocol.has_multisig:
        score -= 10
        details.append("Multisig governance — distributed control.")

    score = max(0, min(100, score))
    grade = score_to_grade(score)

    return RiskFactor(
        name="Centralization",
        weight=0.15,
        score=score,
        grade=grade,
        details=" ".join(details) if details else "Centralization assessment based on known data.",
        recommendation=" ".join(recs) if recs else "Monitor governance activity.",
    )


def analyze_oracle_dependency(protocol: Protocol) -> RiskFactor:
    """Evaluate oracle risk — lending/derivatives are most affected."""
    high_oracle_risk = protocol.category in ("lending", "derivatives", "yield")

    if high_oracle_risk:
        return RiskFactor(
            name="Oracle Dependency",
            weight=0.10,
            score=45,
            grade="C",
            details=f"Category '{protocol.category}' relies heavily on price oracles. "
                    "Oracle manipulation is a common attack vector.",
            recommendation="Verify oracle setup (Chainlink, TWAP, etc.) and check for fallback mechanisms.",
        )
    else:
        return RiskFactor(
            name="Oracle Dependency",
            weight=0.10,
            score=15,
            grade="B",
            details=f"Category '{protocol.category}' has lower oracle dependency.",
            recommendation="Oracle risk is manageable for this protocol type.",
        )


def analyze_exploit_history(protocol: Protocol) -> RiskFactor:
    """Check for past exploits."""
    if not protocol.exploits:
        return RiskFactor(
            name="Exploit History",
            weight=0.10,
            score=10,
            grade="A",
            details="No known exploits or security incidents.",
            recommendation="Clean track record, but always stay vigilant.",
        )

    return RiskFactor(
        name="Exploit History",
        weight=0.10,
        score=70,
        grade="D",
        details=f"Known incidents: {'; '.join(protocol.exploits)}",
        recommendation="Past exploits indicate real-world attack surface. Verify fixes were implemented.",
    )


def analyze_protocol(protocol: Protocol) -> RiskReport:
    """Run all risk analyses on a protocol."""
    report = RiskReport(protocol=protocol)

    report.factors = [
        analyze_tvl_concentration(protocol),
        analyze_admin_keys(protocol),
        analyze_contract_verification(protocol),
        analyze_protocol_age(protocol),
        analyze_audit_status(protocol),
        analyze_centralization(protocol),
        analyze_oracle_dependency(protocol),
        analyze_exploit_history(protocol),
    ]

    report.tvl_data = fetch_tvl(protocol.slug)
    report.contract_info = fetch_contract_info(protocol.main_contract, protocol.chain)
    report.admin_info = fetch_admin_info(protocol.main_contract, protocol.chain)
    report.compute_overall()

    return report
