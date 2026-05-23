"""Tests for the risk analyzer."""
from src.protocols import lookup_protocol
from src.analyzer import (
    analyze_protocol,
    analyze_admin_keys,
    analyze_audit_status,
    analyze_protocol_age,
    analyze_centralization,
    analyze_oracle_dependency,
    analyze_exploit_history,
    score_to_grade,
    RiskReport,
)


def test_score_to_grade():
    assert score_to_grade(5) == "A"
    assert score_to_grade(20) == "B"
    assert score_to_grade(40) == "C"
    assert score_to_grade(60) == "D"
    assert score_to_grade(75) == "E"
    assert score_to_grade(90) == "F"


def test_analyze_admin_keys_multisig_timelock():
    proto = lookup_protocol("uniswap")
    factor = analyze_admin_keys(proto)
    assert factor.grade in ("A", "B")  # has both multisig and timelock
    assert factor.score < 40


def test_analyze_admin_keys_no_multisig():
    proto = lookup_protocol("curve")
    factor = analyze_admin_keys(proto)
    assert factor.score > 0  # no timelock, no multisig = higher risk


def test_analyze_audit_status_good():
    proto = lookup_protocol("aave")  # 3 audits
    factor = analyze_audit_status(proto)
    assert factor.grade in ("A", "B")
    assert factor.score < 25


def test_analyze_audit_status_none():
    from src.protocols import Protocol
    proto = Protocol(name="Test", slug="test", chain="ethereum", category="dex",
                     main_contract="0x0", audits=[], deployed_date="2024-01-01")
    factor = analyze_audit_status(proto)
    assert factor.grade == "F"
    assert factor.score >= 80


def test_analyze_protocol_age_old():
    proto = lookup_protocol("makerdao")  # 2017
    factor = analyze_protocol_age(proto)
    assert factor.grade == "A"
    assert factor.score <= 10


def test_analyze_protocol_age_new():
    from src.protocols import Protocol
    from datetime import datetime, timedelta
    recent = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    proto = Protocol(name="New", slug="new", chain="ethereum", category="dex",
                     main_contract="0x0", deployed_date=recent)
    factor = analyze_protocol_age(proto)
    assert factor.score >= 50


def test_analyze_oracle_dependency_lending():
    proto = lookup_protocol("aave")
    factor = analyze_oracle_dependency(proto)
    assert factor.score >= 30  # lending has high oracle dependency


def test_analyze_oracle_dependency_dex():
    proto = lookup_protocol("uniswap")
    factor = analyze_oracle_dependency(proto)
    assert factor.score < 30  # dex has lower oracle dependency


def test_analyze_exploit_history_clean():
    proto = lookup_protocol("uniswap")
    factor = analyze_exploit_history(proto)
    assert factor.grade == "A"


def test_analyze_exploit_history_exploited():
    proto = lookup_protocol("curve")
    factor = analyze_exploit_history(proto)
    assert factor.grade == "D"
    assert factor.score >= 50


def test_analyze_protocol_full():
    proto = lookup_protocol("aave")
    report = analyze_protocol(proto)
    assert isinstance(report, RiskReport)
    assert len(report.factors) == 8
    assert report.overall_grade in ("A", "B", "C", "D", "E", "F")
    assert 0 <= report.overall_score <= 100


def test_report_factors_have_weights():
    proto = lookup_protocol("uniswap")
    report = analyze_protocol(proto)
    total_weight = sum(f.weight for f in report.factors)
    assert abs(total_weight - 1.0) < 0.01  # weights should sum to 1.0
