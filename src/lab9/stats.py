"""Statistics students implement (M2 judge calibration, M4 paired bootstrap).

Rules: a judge is a classifier -- measure it like one. A higher mean is not
"better" until the paired CI of the difference excludes 0.
Reference values to self-check are in tests/test_lab9_stats.py.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

POS = "FAIL"   # the judge's job is to FIND failures, so FAIL is the positive class
LABELS = {"PASS", "FAIL"}


def _pairs(human: Sequence[str], judge: Sequence[str]) -> list[tuple[str, str]]:
    if len(human) != len(judge):
        raise ValueError(f"label length mismatch: {len(human)} != {len(judge)}")
    pairs = [(str(h).strip().upper(), str(j).strip().upper()) for h, j in zip(human, judge)]
    invalid = sorted({label for pair in pairs for label in pair if label not in LABELS})
    if invalid:
        raise ValueError(f"labels must be PASS or FAIL; got {invalid}")
    return pairs


def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    """tp/fp/fn/tn with FAIL as positive."""
    pairs = _pairs(human, judge)
    tp = sum(h == POS and j == POS for h, j in pairs)
    fp = sum(h != POS and j == POS for h, j in pairs)
    fn = sum(h == POS and j != POS for h, j in pairs)
    tn = sum(h != POS and j != POS for h, j in pairs)
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def precision_recall(human: Sequence[str], judge: Sequence[str]) -> tuple[float, float]:
    """Return precision and recall with FAIL as the positive class."""
    cm = confusion(human, judge)
    predicted_fail = cm["tp"] + cm["fp"]
    actual_fail = cm["tp"] + cm["fn"]
    precision = cm["tp"] / predicted_fail if predicted_fail else 0.0
    recall = cm["tp"] / actual_fail if actual_fail else 0.0
    return precision, recall


def cohen_kappa(human: Sequence[str], judge: Sequence[str]) -> float:
    """kappa = (p_o - p_e) / (1 - p_e). Raise ValueError when undefined (p_e == 1):
    a constant judge has no signal and must FAIL calibration, not pass on a technicality."""
    cm = confusion(human, judge)
    n = sum(cm.values())
    if n == 0:
        raise ValueError("cohen_kappa undefined for empty labels")
    observed = (cm["tp"] + cm["tn"]) / n
    human_fail = cm["tp"] + cm["fn"]
    judge_fail = cm["tp"] + cm["fp"]
    human_pass = cm["tn"] + cm["fp"]
    judge_pass = cm["tn"] + cm["fn"]
    expected = (human_fail * judge_fail + human_pass * judge_pass) / (n * n)
    if math.isclose(expected, 1.0, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError("cohen_kappa undefined when expected agreement is 1")
    return (observed - expected) / (1.0 - expected)


def rogan_gladen(observed_rate: float, sensitivity: float, specificity: float) -> float:
    """Correct an observed failure rate for judge error; clip to [0, 1].

    The estimate is unidentified when sensitivity + specificity == 1, so reject
    that case rather than reporting a misleading corrected rate.
    """
    observed = float(observed_rate)
    sens = float(sensitivity)
    spec = float(specificity)
    if not all(math.isfinite(x) and 0.0 <= x <= 1.0 for x in (observed, sens, spec)):
        raise ValueError("observed rate, sensitivity, and specificity must be finite values in [0, 1]")
    denominator = sens + spec - 1.0
    if math.isclose(denominator, 0.0, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError("Rogan-Gladen rate is undefined when sensitivity + specificity = 1")
    corrected = (observed + spec - 1.0) / denominator
    return max(0.0, min(1.0, corrected))


def paired_bootstrap(a: Sequence[float], b: Sequence[float], *, n_resamples: int = 1000,
                     rng: int = 2027, confidence: float = 0.95) -> tuple[float, float, float]:
    """a[i], b[i] = per-item mean over seeds, SAME items, SAME order.
    Return (mean(a)-mean(b), lo, hi) with scipy.stats.bootstrap(paired=True, method="percentile",
    rng=numpy.random.default_rng(rng)). If a == b everywhere return (0.0, 0.0, 0.0)."""
    if len(a) != len(b):
        raise ValueError(f"paired sequences must have equal length: {len(a)} != {len(b)}")
    if n_resamples <= 0:
        raise ValueError("n_resamples must be positive")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")
    if not a:
        return (0.0, 0.0, 0.0)

    import numpy as np
    from scipy import stats as scipy_stats

    arr_a = np.asarray(a, dtype=float)
    arr_b = np.asarray(b, dtype=float)
    if not np.all(np.isfinite(arr_a)) or not np.all(np.isfinite(arr_b)):
        raise ValueError("paired samples must contain only finite values")
    differences = arr_a - arr_b
    mean_diff = float(np.mean(differences))
    if np.all(differences == 0.0):
        return (0.0, 0.0, 0.0)
    if len(differences) == 1 or np.all(differences == differences[0]):
        return (mean_diff, mean_diff, mean_diff)

    result = scipy_stats.bootstrap(
        (arr_a, arr_b),
        lambda x, y, axis=-1: np.mean(x - y, axis=axis),
        paired=True,
        n_resamples=n_resamples,
        confidence_level=confidence,
        method="percentile",
        rng=np.random.default_rng(rng),
    )
    return (mean_diff, float(result.confidence_interval.low), float(result.confidence_interval.high))


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probability that AT LEAST ONE of k trials drawn from n (c of them passing) passes.
    Unbiased estimator (Chen et al. 2021): 1 - C(n-c, k) / C(n, k). Raise ValueError if k > n."""
    # TODO M6
    raise NotImplementedError


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k (tau-bench, Yao et al. 2024): probability that ALL k trials drawn from n pass.
    Unbiased estimator: C(c, k) / C(n, k). Raise ValueError if k > n.
    pass^k <= pass@1 <= pass@k; a reliable agent keeps pass^k close to pass@1."""
    # TODO M6
    raise NotImplementedError
