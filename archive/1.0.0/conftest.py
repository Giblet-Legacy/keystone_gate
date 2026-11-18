"""
conftest.py — Keystone Gate v0.6.5: put the-full-stack on the path for the suite.

Function:
    Keystone Gate's mediator/digest.py imports the-full-stack's forge_core.
    Until v0.6.5 nothing said where that is, so the suite passed only as
    the-full-stack's submodule with the-full-stack on PYTHONPATH; cloned on
    its own (Giblet-Legacy/keystone_gate, 2026-11-17) one test module could
    not even be collected. pytest loads this file first, from the
    repository root, and it puts the first stack root it finds on sys.path:
      1. $FORGE_STACK_ROOT, if set;
      2. two levels up (the-full-stack/consumer/keystone_gate, the submodule);
      3. a sibling folder named the-full-stack (the workspace layout).
    A stack root is a folder holding forge_core/. If none is found the
    suite runs as before and the modules that need forge_core fail loudly.

Public API:
    1. stack_root(here) -> Path | None

Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


# 1. stack_root
def stack_root(here):
    here = Path(here)
    candidates = []
    if os.environ.get("FORGE_STACK_ROOT"):
        candidates.append(Path(os.environ["FORGE_STACK_ROOT"]))
    candidates += [here.parent.parent, here.parent / "the-full-stack"]
    for c in candidates:
        if (c / "forge_core").is_dir():
            return c
    return None


_root = stack_root(HERE)
if _root is not None and str(_root) not in sys.path:
    sys.path.append(str(_root))  # appended: keystone's own mediator package stays first
