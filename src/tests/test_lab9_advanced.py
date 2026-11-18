"""M5-M7 self-check (Advanced/Expert). Run: python -m pytest -q -m student -o addopts= -k advanced
Public vectors only; the instructor grades with hidden ones."""
import copy
import math

import pytest

pytestmark = pytest.mark.student


@pytest.fixture(scope="module")
def stats():
    from lab9 import stats

    return stats


@pytest.mark.parametrize("n,c,k,want", [(5, 5, 5, 1.0), (5, 0, 1, 0.0), (5, 2, 1, 0.4), (10, 3, 3, 1 - 35 / 120)])
def test_pass_at_k(stats, n, c, k, want):
    assert math.isclose(stats.pass_at_k(n, c, k), want, abs_tol=1e-9)


@pytest.mark.parametrize("n,c,k,want", [(5, 5, 5, 1.0), (5, 4, 5, 0.0), (5, 4, 3, 0.4), (10, 8, 2, 28 / 45)])
def test_pass_hat_k(stats, n, c, k, want):
    assert math.isclose(stats.pass_hat_k(n, c, k), want, abs_tol=1e-9)


def test_pass_k_rejects_bad_args(stats):
    for args in [(5, 6, 1), (5, 2, 0), (3, 1, 4)]:
        with pytest.raises(ValueError):
            stats.pass_at_k(*args)


def _report(rows, metrics, items=4, seeds=(1, 2)):
    return {"manifest": {"eval_set_sha": "x", "items": items, "seeds": list(seeds)},
            "rows": rows, "metrics": metrics, "evaluator_failures": []}


ROWS = [{"item_id": f"E-{i:03d}", "seed": s, "pass_rate": True, "slices": ["denial"] if i < 2 else []}
        for i in range(4) for s in (1, 2)]
SPEC = {"eval_set_version": "v2", "metrics": [{"id": "pass_rate", "kind": "capability", "blocking": True,
                                               "threshold": {"min": 0.8}}]}


def test_integrity_flags_nan_and_dropped_rows():
    from lab9 import gate

    base = _report(copy.deepcopy(ROWS), {"pass_rate": 1.0})
    assert gate.integrity_check(base, base, SPEC) == []
    nan = _report(copy.deepcopy(ROWS), {"pass_rate": float("nan")})
    assert gate.integrity_check(nan, base, SPEC)
    dropped = _report(copy.deepcopy(ROWS[:-1]), {"pass_rate": 1.0})
    assert gate.integrity_check(dropped, base, SPEC)


def test_integrity_flags_loosened_spec():
    from lab9 import gate

    base = _report(copy.deepcopy(ROWS), {"pass_rate": 1.0})
    loose = copy.deepcopy(SPEC)
    loose["metrics"][0]["threshold"]["min"] = 0.5
    assert gate.integrity_check(base, base, loose, SPEC)
    assert gate.integrity_check(base, base, SPEC, SPEC) == []


def test_integrity_flags_duplicates_failures_missing_values_and_slice_relabel():
    from lab9 import gate

    base = _report(copy.deepcopy(ROWS), {"pass_rate": 1.0})
    duplicate = _report(copy.deepcopy(ROWS), {"pass_rate": 1.0})
    duplicate["rows"][-1] = copy.deepcopy(duplicate["rows"][0])
    assert any("duplicate" in p for p in gate.integrity_check(duplicate, base, SPEC))

    failed_eval = _report(copy.deepcopy(ROWS), {"pass_rate": 1.0})
    failed_eval["evaluator_failures"] = ["grader crashed"]
    assert any("evaluator_failures" in p for p in gate.integrity_check(failed_eval, base, SPEC))

    missing = _report(copy.deepcopy(ROWS), {"pass_rate": 1.0})
    missing["rows"][0]["pass_rate"] = None
    code_spec = {**SPEC, "metrics": [{**SPEC["metrics"][0], "grader": "code"}]}
    assert any("missing/None" in p for p in gate.integrity_check(missing, base, code_spec))

    relabeled = _report(copy.deepcopy(ROWS), {"pass_rate": 1.0})
    relabeled["rows"][0]["slices"] = []
    assert any("slice tags changed" in p for p in gate.integrity_check(relabeled, base, SPEC))


def test_slice_check_blocks_a_slice_below_floor():
    from lab9 import gate

    base = _report(copy.deepcopy(ROWS), {"pass_rate": 1.0})
    rows = copy.deepcopy(ROWS)
    for r in rows:
        if "denial" in r["slices"] and r["seed"] == 1:
            r["pass_rate"] = False
    spec = dict(SPEC, slices=[{"name": "denial", "metric": "pass_rate", "min": 0.9, "blocking": True}])
    blocked, _ = gate.slice_check(_report(rows, {"pass_rate": 0.75}), base, spec)
    assert blocked == ["slice:denial/pass_rate"]


def test_ratchet_rejects_removed_slice_and_looser_cost_cap():
    from lab9 import gate

    old = {"eval_set_version": "v2", "metrics": [{"id": "cost", "threshold": {"max_increase": 0.1}}],
           "slices": [{"name": "money", "metric": "pass_rate", "min": 0.9,
                       "no_significant_drop": True, "blocking": True}]}
    new = copy.deepcopy(old)
    new["metrics"][0]["threshold"]["max_increase"] = 0.2
    new["slices"] = []
    problems = gate._ratchet_problems(new, old)
    assert any("max_increase" in p for p in problems)
    assert any("removed slice" in p for p in problems)
