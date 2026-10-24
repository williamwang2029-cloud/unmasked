"""Plain-assert tests for reid.release_warnings (no pytest, no third-party packages).

Run:  python scripts/checks/test_release_warnings.py
Exits 0 and prints OK if all cases pass; raises AssertionError otherwise.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from reid.release_warnings import release_warnings


def test_default_ok():
    # considered 16 fields, active 9, 2 of 4 analyses lost, within removal limit -> clean
    considered = [f"f{i}" for i in range(16)]
    active = [f"f{i}" for i in range(9)]
    status = {"Class": "lost", "MAJfirstcol": "lost", "affiliation": "available", "Year": "available"}
    out = release_warnings(considered, active, status, 0.025, 0.05)
    assert out["warnings"] == [], out["warnings"]
    assert out["errors"] == [], out["errors"]
    assert out["fields_kept"] == ", ".join(active)
    print("a) default-like case: no warnings, no errors -> PASS")


def test_strict_warns():
    # considered 16, only 2 survive, 3 of 4 analyses lost, removal within limit -> one warning
    considered = [f"f{i}" for i in range(16)]
    active = ["affiliation", "attend_other"]
    status = {"Class": "lost", "MAJfirstcol": "lost", "Year": "lost", "affiliation": "available"}
    out = release_warnings(considered, active, status, 0.0, 0.0)
    assert len(out["warnings"]) == 1, out["warnings"]
    assert out["errors"] == [], out["errors"]
    w = out["warnings"][0]
    assert "only 2 of 16 fields survived" in w, w
    assert "3 of 4 analyses are lost" in w, w
    # lost analyses are listed, sorted
    assert "Class, MAJfirstcol, Year" in w, w
    assert out["fields_kept"] == "affiliation, attend_other"
    print("b) strict case: one warning listing lost analyses -> PASS")


def test_over_limit_errors():
    # removed more than the limit -> one error
    considered = [f"f{i}" for i in range(16)]
    active = [f"f{i}" for i in range(9)]
    status = {"Class": "available", "Year": "available"}
    out = release_warnings(considered, active, status, 0.08, 0.05)
    assert len(out["errors"]) == 1, out["errors"]
    assert out["warnings"] == [], out["warnings"]
    assert "8.0%" in out["errors"][0], out["errors"][0]
    assert "5%" in out["errors"][0], out["errors"][0]
    print("c) over-limit case: one error -> PASS")


def test_empty_no_crash():
    # everything empty -> no crash, no warnings, no errors, fields_kept == "none"
    out = release_warnings([], [], {}, 0.0, 0.0)
    assert out["warnings"] == [], out["warnings"]
    assert out["errors"] == [], out["errors"]
    assert out["fields_kept"] == "none", out["fields_kept"]
    print("d) empty inputs: no crash, no warnings -> PASS")


if __name__ == "__main__":
    test_default_ok()
    test_strict_warns()
    test_over_limit_errors()
    test_empty_no_crash()
    print("OK: all release_warnings tests passed")
