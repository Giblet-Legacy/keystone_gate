"""
test_stack_root.py — Keystone Gate v0.6.5: find the-full-stack in either layout.

Function:
    Written before conftest.py's stack_root and run red first. Keystone
    Gate imports the-full-stack's forge_core (mediator/digest.py) but never
    said where it lives, so its suite passed only as the-full-stack's
    submodule, run with the-full-stack on the path. Since 2026-11-17 it is
    also its own repository (Giblet-Legacy/keystone_gate), cloned beside
    the others.

Functions in this file (pytest-collected):
    1. test_env_wins
    2. test_submodule_layout
    3. test_sibling_layout
    4. test_none_found
    5. test_forge_core_imports_here

Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import importlib
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("keystone_root_conftest", Path(__file__).parent.parent / "conftest.py")
conftest = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(conftest)  # the root conftest.py, not tests/conftest.py


def _stack(path: Path) -> Path:
    (path / "forge_core").mkdir(parents=True)
    (path / "forge_core" / "__init__.py").write_text("", encoding="utf-8")
    return path


# 1. test_env_wins
def test_env_wins(tmp_path, monkeypatch):
    stack = _stack(tmp_path / "elsewhere")
    here = tmp_path / "keystone_gate"
    here.mkdir()
    monkeypatch.setenv("FORGE_STACK_ROOT", str(stack))
    assert conftest.stack_root(here) == stack


# 2. test_submodule_layout
def test_submodule_layout(tmp_path, monkeypatch):
    monkeypatch.delenv("FORGE_STACK_ROOT", raising=False)
    stack = _stack(tmp_path / "the-full-stack")
    here = stack / "consumer" / "keystone_gate"
    here.mkdir(parents=True)
    assert conftest.stack_root(here) == stack


# 3. test_sibling_layout
def test_sibling_layout(tmp_path, monkeypatch):
    monkeypatch.delenv("FORGE_STACK_ROOT", raising=False)
    stack = _stack(tmp_path / "the-full-stack")
    here = tmp_path / "keystone_gate"
    here.mkdir()
    assert conftest.stack_root(here) == stack


# 4. test_none_found
def test_none_found(tmp_path, monkeypatch):
    monkeypatch.delenv("FORGE_STACK_ROOT", raising=False)
    here = tmp_path / "keystone_gate"
    here.mkdir()
    assert conftest.stack_root(here) is None


# 5. test_forge_core_imports_here
def test_forge_core_imports_here():
    assert importlib.import_module("forge_core").sha256_hex(b"") == \
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
