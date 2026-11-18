"""
test_mediator_digest_v2.py — Keystone Gate v1.1.0: the digest without the-full-stack.

Function:
    Written before mediator/digest_v2.py and run red first. The v1 digest
    (archived in archive/1.0.0/) imported the-full-stack's forge_core for
    two small rules and stamped its capsule "forge-stack/governance-v7".
    James, 2026-11-18: the-full-stack was for reference only and never a
    layer of the Legacy. So v2 carries the same behaviour on the standard
    library alone, inherits nothing, and exports as primitive-digest-v2
    so it can never overwrite the signed sc/primitive-digest-v1.sc.json.
    The v1 tests are carried over unchanged in substance.

Functions in this file (pytest-collected):
    1.  test_compute_primitive_usage_reads_real_shape
    2.  test_compute_primitive_usage_reformats_microsecond_timestamps
    3.  test_compute_primitive_usage_missing_file_returns_empty
    4.  test_compute_primitive_usage_corrupt_file_returns_empty_not_crash
    5.  test_build_digest_envelope_has_ratified_scp_id_and_valid_shape
    6.  test_scp_id_uses_hyphenated_form_not_the_packages_underscored_name
    7.  test_export_digest_writes_schema_valid_file
    8.  test_export_digest_is_idempotent_filename_across_reruns
    9.  test_no_forge_core_anywhere
    10. test_inherits_nothing
    11. test_never_overwrites_the_signed_v1_digest
    12. test_rules_match_forge_time

Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import json
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from mediator import digest_v2
from mediator.digest_v2 import (
    PrimitiveUsage,
    build_digest_envelope,
    compute_primitive_usage,
    export_digest,
)

_SCP_ID_RE = re.compile(r"^[a-z0-9-]+(?:/[a-z0-9-]+)*-v[0-9]+$")
_ISO_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
REPO = Path(__file__).resolve().parent.parent


def _write_primitives(tmpdir, data):
    path = Path(tmpdir) / "capsule_primitives.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


# 1
def test_compute_primitive_usage_reads_real_shape():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = _write_primitives(tmpdir, {
            "scp_id": {"type": "str", "first_seen": "2026-01-01T00:00:00Z", "count": 5},
            "declaration.intent": {"type": "str", "first_seen": "2026-01-02T00:00:00Z", "count": 3},
        })
        usages = {u.field_path: u for u in compute_primitive_usage(path)}
        assert usages["scp_id"].observation_count == 5
        assert usages["scp_id"].field_type == "str"
        assert usages["declaration.intent"].observation_count == 3


# 2
def test_compute_primitive_usage_reformats_microsecond_timestamps():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = _write_primitives(tmpdir, {
            "scp_id": {"type": "str", "first_seen": "2026-01-01T12:30:45.383512Z", "count": 1},
        })
        usages = compute_primitive_usage(path)
        assert _ISO_UTC_RE.match(usages[0].first_seen)
        assert usages[0].first_seen == "2026-01-01T12:30:45Z"


# 3
def test_compute_primitive_usage_missing_file_returns_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        assert compute_primitive_usage(Path(tmpdir) / "nonexistent.json") == []


# 4
def test_compute_primitive_usage_corrupt_file_returns_empty_not_crash():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "capsule_primitives.json"
        path.write_text("not valid json{{{", encoding="utf-8")
        assert compute_primitive_usage(path) == []


# 5
def test_build_digest_envelope_has_ratified_scp_id_and_valid_shape():
    envelope = build_digest_envelope("keystone_gate", [
        PrimitiveUsage("scp_id", "str", "2026-01-01T00:00:00Z", 5),
    ])
    assert _SCP_ID_RE.match(envelope["scp_id"])
    assert _ISO_UTC_RE.match(envelope["created"])
    assert _ISO_UTC_RE.match(envelope["declaration"]["generated_at"])
    assert envelope["declaration"]["type"] == "primitive_digest"
    assert envelope["declaration"]["consumer"] == "keystone_gate"
    assert envelope["declaration"]["fields"][0]["field_path"] == "scp_id"
    assert envelope["signature"] is None
    assert envelope["licence"] == "MSL-1.0"


# 6
def test_scp_id_uses_hyphenated_form_not_the_packages_underscored_name():
    envelope = build_digest_envelope("keystone_gate", [])
    assert "keystone_gate" not in envelope["scp_id"]
    assert "keystone-gate" in envelope["scp_id"]


# 7
def test_export_digest_writes_schema_valid_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        primitives_path = _write_primitives(tmpdir, {
            "scp_id": {"type": "str", "first_seen": "2026-01-01T00:00:00Z", "count": 1},
        })
        path = export_digest(primitives_path, Path(tmpdir) / "sc")
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert _SCP_ID_RE.match(data["scp_id"])
        assert data["declaration"]["type"] == "primitive_digest"


# 8
def test_export_digest_is_idempotent_filename_across_reruns():
    with tempfile.TemporaryDirectory() as tmpdir:
        primitives_path = _write_primitives(tmpdir, {})
        sc_dir = Path(tmpdir) / "sc"
        path1 = export_digest(primitives_path, sc_dir)
        path2 = export_digest(primitives_path, sc_dir)
        assert path1 == path2
        assert len(list(sc_dir.glob("*.sc.json"))) == 1


# 9
def test_no_forge_core_anywhere():
    """Nothing live in this repository reaches for the-full-stack."""
    assert "forge_core" not in sys.modules
    live = [p for p in REPO.rglob("*.py")
            if "archive" not in p.relative_to(REPO).parts
            and ".git" not in p.parts
            and p.name != Path(__file__).name]
    for p in live:
        text = p.read_text(encoding="utf-8")
        assert "import forge_core" not in text, p
        assert "from forge_core" not in text, p
        assert '/ "the-full-stack"' not in text, p  # no path lookup; naming it as history is fine
    assert not (REPO / "conftest.py").exists(), "the stack-root conftest belongs in archive/1.0.0"


# 10
def test_inherits_nothing():
    assert build_digest_envelope("keystone_gate", [])["inherits"] is None


# 11
def test_never_overwrites_the_signed_v1_digest():
    assert digest_v2.SCP_ID.endswith("-v2")
    with tempfile.TemporaryDirectory() as tmpdir:
        path = export_digest(_write_primitives(tmpdir, {}), Path(tmpdir) / "sc")
        assert path.name == "primitive-digest-v2.sc.json"


# 12
def test_rules_match_forge_time():
    """Same two rules as P16 Time (forge-time): strict UTC seconds, and the scp_id shape."""
    when = datetime(2026, 1, 1, 12, 30, 45, 383512, tzinfo=timezone.utc)
    assert digest_v2.format_iso_utc(when) == "2026-01-01T12:30:45Z"
    for good in ["a-v1", "keystone-gate/mediator/primitive-digest-v2"]:
        assert digest_v2.is_ratified_scp_id(good)
    for bad in ["keystone_gate/x-v1", "a-v", "A-v1", "a-v1\n", "/a-v1"]:
        assert not digest_v2.is_ratified_scp_id(bad), bad
