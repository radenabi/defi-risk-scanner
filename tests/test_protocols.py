"""Tests for protocols database."""
from src.protocols import lookup_protocol, list_protocols, PROTOCOLS


def test_lookup_by_slug():
    proto = lookup_protocol("uniswap")
    assert proto is not None
    assert proto.name == "Uniswap"


def test_lookup_by_name():
    proto = lookup_protocol("Aave")
    assert proto is not None
    assert proto.slug == "aave"


def test_lookup_by_address():
    addr = "0x1F98431c8aD98523631AE4a59f267346ea31F984"
    proto = lookup_protocol(addr)
    assert proto is not None
    assert proto.name == "Uniswap"


def test_lookup_case_insensitive():
    proto = lookup_protocol("UNISWAP")
    assert proto is not None


def test_lookup_unknown():
    proto = lookup_protocol("nonexistent_protocol_xyz")
    assert proto is None


def test_list_protocols():
    protocols = list_protocols()
    assert len(protocols) >= 8
    assert all(p.name for p in protocols)


def test_protocols_have_required_fields():
    for slug, proto in PROTOCOLS.items():
        assert proto.name, f"{slug} missing name"
        assert proto.chain, f"{slug} missing chain"
        assert proto.category, f"{slug} missing category"
        assert proto.main_contract, f"{slug} missing main_contract"
