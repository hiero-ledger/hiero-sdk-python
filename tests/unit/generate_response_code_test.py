"""Tests for the ResponseCode member generation in generate_proto.py."""

from __future__ import annotations

from pathlib import Path

import pytest

import generate_proto as gp


pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTO_ROOT = REPO_ROOT / gp.CACHE_DIR
RESPONSE_CODE_FILE = REPO_ROOT / gp.RESPONSE_CODE_PATH

SAMPLE_PROTO = """
syntax = "proto3";
/** FAKE = 99; in a block comment must be ignored */
enum ResponseCodeEnum {
    // GHOST = 98; in a line comment must be ignored
    OK = 0;
    /**
     * INVALID_FOO = 97;
     */
    OLD_THING = 86 [deprecated = true];
    INVALID_GOSSIP_CA_CERTIFICATE = 344;
    PENDING_AIRDROP_ID_LIST_TOO_LONG = 363;
    INVALID_TOKEN_IN_PENDING_AIRDROP = 369;
}
"""


def test_parse_ignores_comments_and_flags_deprecated() -> None:
    members = gp.parse_response_code_proto(SAMPLE_PROTO)

    assert members == [
        ("OK", 0, False),
        ("OLD_THING", 86, True),
        ("INVALID_GOSSIP_CA_CERTIFICATE", 344, False),
        ("PENDING_AIRDROP_ID_LIST_TOO_LONG", 363, False),
        ("INVALID_TOKEN_IN_PENDING_AIRDROP", 369, False),
    ]


def test_parse_raises_without_enum() -> None:
    with pytest.raises(RuntimeError, match="not found"):
        gp.parse_response_code_proto("enum Other { A = 0; }")


def test_render_emits_deprecations_and_aliases_after_canonical_member() -> None:
    rendered = gp.render_response_code_members(gp.parse_response_code_proto(SAMPLE_PROTO))
    lines = rendered.splitlines()

    assert lines[0] == gp.RESPONSE_CODE_BEGIN
    assert lines[-1] == gp.RESPONSE_CODE_END
    assert "    # Deprecated in the protobuf definition." in lines
    assert lines.index("    OLD_THING = 86") == lines.index("    # Deprecated in the protobuf definition.") + 1
    canonical = lines.index("    INVALID_GOSSIP_CA_CERTIFICATE = 344")
    assert lines[canonical + 1] == "    # Deprecated alias, misspelled: use INVALID_GOSSIP_CA_CERTIFICATE instead."
    assert lines[canonical + 2] == "    INVALID_GOSSIP_CAE_CERTIFICATE = 344"


def test_render_fails_when_alias_target_disappears() -> None:
    with pytest.raises(RuntimeError, match="not in response_code.proto"):
        gp.render_response_code_members([("OK", 0, False)])


def test_render_fails_when_alias_becomes_real_member() -> None:
    members = gp.parse_response_code_proto(SAMPLE_PROTO) + [("INVALID_GOSSIP_CAE_CERTIFICATE", 400, False)]

    with pytest.raises(RuntimeError, match="real member"):
        gp.render_response_code_members(members)


def test_replace_region_preserves_shell() -> None:
    source = (
        "class ResponseCode(IntEnum):\n"
        f"{gp.RESPONSE_CODE_BEGIN}\n    STALE = 1\n{gp.RESPONSE_CODE_END}\n"
        "\n    def shell(self): ...\n"
    )

    updated = gp.replace_response_code_region(source, "    # NEW\n    OK = 0")

    assert updated == "class ResponseCode(IntEnum):\n    # NEW\n    OK = 0\n\n    def shell(self): ...\n"


def test_replace_region_requires_markers() -> None:
    with pytest.raises(RuntimeError, match="markers not found"):
        gp.replace_response_code_region("class ResponseCode(IntEnum):\n    OK = 0\n", "x")


def test_generate_is_idempotent(tmp_path: Path) -> None:
    proto_root = tmp_path / "protos"
    (proto_root / "services").mkdir(parents=True)
    (proto_root / gp.RESPONSE_CODE_PROTO).write_text(SAMPLE_PROTO, encoding="utf-8")
    target = tmp_path / "response_code.py"
    target.write_text(f"{gp.RESPONSE_CODE_BEGIN}\n{gp.RESPONSE_CODE_END}\n", encoding="utf-8")

    assert gp.generate_response_code(proto_root, target) is True
    first = target.read_bytes()
    assert gp.generate_response_code(proto_root, target) is False
    assert target.read_bytes() == first
    assert b"\r" not in first


@pytest.mark.skipif(not (PROTO_ROOT / gp.RESPONSE_CODE_PROTO).exists(), reason="protos not downloaded")
def test_checked_in_response_code_is_up_to_date(tmp_path: Path) -> None:
    """The committed response_code.py must equal what the generator produces from the vendored proto."""
    copy = tmp_path / "response_code.py"
    copy.write_bytes(RESPONSE_CODE_FILE.read_bytes())

    changed = gp.generate_response_code(PROTO_ROOT, copy)

    assert not changed, "response_code.py is stale; run `uv run python generate_proto.py` and commit the result"
