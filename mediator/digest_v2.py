"""
digest_v2.py — Keystone Gate v1.1.0: the primitive-usage digest, standing on its own.

Function:
    Same behaviour as the v1 digest (archive/1.0.0/mediator/digest.py):
    read capsule_primitives.json read-only, wrap each field's
    {type, first_seen, count} as a primitive_digest .sc.json envelope,
    export it. Three differences, all from James's word of 2026-11-18
    that the-full-stack was for reference only and never a layer of the
    Legacy:
      - no forge_core: the two rules it lent (strict UTC seconds and the
        scp_id shape) are written here on the standard library, the same
        rules as P16 Time (forge-time);
      - "inherits" is None: no forge-stack governance stands over it;
      - scp_id ends -v2, so an export never overwrites the signed
        sc/primitive-digest-v1.sc.json.

Public API:
    1. format_iso_utc(when) -> str
    2. is_ratified_scp_id(value) -> bool
    3. PrimitiveUsage
    4. compute_primitive_usage(primitive_file) -> list[PrimitiveUsage]
    5. build_digest_envelope(consumer, usages) -> dict
    6. export_digest(primitive_file, sc_export_dir, consumer) -> Path

Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List

SCP_ID = "keystone-gate/mediator/primitive-digest-v2"
SCP_ID_RE = re.compile(r"[a-z0-9-]+(?:/[a-z0-9-]+)*-v[0-9]+")
_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


# 1. format_iso_utc
def format_iso_utc(when):
    """A datetime as YYYY-MM-DDTHH:MM:SSZ in UTC, fractions dropped."""
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return when.astimezone(timezone.utc).strftime(_FORMAT)


# 2. is_ratified_scp_id
def is_ratified_scp_id(value):
    """Whole-string match: lowercase a-z0-9- segments, ending -vN."""
    return isinstance(value, str) and SCP_ID_RE.fullmatch(value) is not None


# 3. PrimitiveUsage
@dataclass(frozen=True)
class PrimitiveUsage:
    field_path: str
    field_type: str
    first_seen: str
    observation_count: int


def _now():
    return format_iso_utc(datetime.now(timezone.utc))


def _reformat_first_seen(raw):
    """primitives.py writes microseconds; the digest carries whole seconds."""
    if not raw:
        return _now()
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return _now()
    return format_iso_utc(parsed)


# 4. compute_primitive_usage
def compute_primitive_usage(primitive_file: Path) -> List[PrimitiveUsage]:
    primitive_file = Path(primitive_file)
    if not primitive_file.exists():
        return []
    try:
        data = json.loads(primitive_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return [
        PrimitiveUsage(
            field_path=field_path,
            field_type=meta.get("type", "unknown"),
            first_seen=_reformat_first_seen(meta.get("first_seen", "")),
            observation_count=meta.get("count", 0),
        )
        for field_path, meta in data.items()
    ]


# 5. build_digest_envelope
def build_digest_envelope(consumer: str, usages: List[PrimitiveUsage]) -> dict:
    assert is_ratified_scp_id(SCP_ID), f"scp_id fails the ratified format: {SCP_ID!r}"
    now = _now()
    return {
        "scp_id": SCP_ID,
        "scp_version": "1.2.0",
        "created": now,
        "inherits": None,
        "declaration": {
            "type": "primitive_digest",
            "consumer": consumer,
            "generated_at": now,
            "fields": [
                {
                    "field_path": u.field_path,
                    "field_type": u.field_type,
                    "first_seen": u.first_seen,
                    "observation_count": u.observation_count,
                }
                for u in usages
            ],
        },
        "licence": "MSL-1.0",
        "signature": None,
    }


# 6. export_digest
def export_digest(primitive_file: Path, sc_export_dir: Path, consumer: str = "keystone_gate") -> Path:
    envelope = build_digest_envelope(consumer, compute_primitive_usage(primitive_file))
    sc_export_dir = Path(sc_export_dir)
    sc_export_dir.mkdir(parents=True, exist_ok=True)
    path = sc_export_dir / (envelope["scp_id"].rsplit("/", 1)[-1] + ".sc.json")
    path.write_text(json.dumps(envelope, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
