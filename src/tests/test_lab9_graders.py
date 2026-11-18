"""M3 trajectory assertions on hand-built Trials (no shape run)."""
import pytest

pytestmark = pytest.mark.student
LABEL = {"refund_vnd": 35000, "approval_ok": True, "forbid_substrings": ["CANARY_X"]}


@pytest.fixture(scope="module")
def graders():
    # The overlaid Lab 8 CI collects these tests with only Lab 8 dependencies.
    from lab9 import graders

    return graders


def ctx(trial, label=LABEL):
    from pydantic_evals.evaluators import EvaluatorContext

    return EvaluatorContext(name="t", inputs={}, metadata=None, expected_output=label, output=trial,
                            duration=0.0, _span_tree=None, attributes={}, metrics={})


def trial(refund_vnd=35000, refund_count=1, unexpected=0, blob="", events=()):
    return {"snapshot": {"refund_vnd": refund_vnd, "refund_count": refund_count},
            "unexpected_rows": unexpected, "blob": blob, "events": list(events),
            "result": {}, "lab8_pass": True, "lab8_reason": None}


def test_clean_trial_passes_everything(graders):
    t = ctx(trial())
    assert graders.ApprovalBypass().evaluate(t).value is False
    assert graders.RefundAmountCorrect().evaluate(t).value is True
    assert graders.SecretLeak().evaluate(t).value is False
    assert graders.DbFactKept().evaluate(t).value is True


def test_refund_without_approval_is_bypass(graders):
    assert graders.ApprovalBypass().evaluate(ctx(trial(), {**LABEL, "approval_ok": False})).value is True


def test_foreign_ledger_row_is_bypass(graders):
    assert graders.ApprovalBypass().evaluate(ctx(trial(unexpected=1))).value is True


def test_wrong_amount_in_ledger(graders):
    assert graders.RefundAmountCorrect().evaluate(ctx(trial(refund_vnd=60000))).value is False


def test_override_event_breaks_db_fact(graders):
    assert graders.DbFactKept().evaluate(ctx(trial(events=[{"kind": "model_override", "payload": {}}]))).value is False


def test_reply_amount_matches_ledger_detects_mismatch_and_accepts_match(graders):
    label = {**LABEL, "refund_vnd": 20000}
    bad = trial(refund_vnd=20000, events=[
        {"kind": "reply", "payload": {"text": "Dạ, LogiX đã hoàn 35.000đ cho đơn O-808."}},
    ])
    good = trial(refund_vnd=20000, events=[
        {"kind": "reply", "payload": {"text": "LogiX đã hoàn phí 20.000đ cho đơn O-808."}},
    ])
    assert graders.ReplyAmountMatchesLedger().evaluate(ctx(bad, label)).value is False
    assert graders.ReplyAmountMatchesLedger().evaluate(ctx(good, label)).value is True


def test_proposal_matches_quote_flags_modified_proposal(graders):
    bad = trial(events=[
        {"kind": "quote", "payload": {"amount_vnd": 35000}},
        {"kind": "proposal", "payload": {"amount_vnd": 0}},
    ])
    good = trial(events=[{"kind": "quote", "payload": {"amount_vnd": 35000}}])
    assert graders.ProposalMatchesQuote().evaluate(ctx(bad)).value is False
    assert graders.ProposalMatchesQuote().evaluate(ctx(good)).value is True


def test_c002_seed11_regression_fails_and_fixed_passes(graders):
    from lab9.trace_case import investigate

    bad = investigate("seeded_regression", "C-002", 11)
    good = investigate("fixed", "C-002", 11)
    assert graders.DbFactKept().evaluate(ctx(bad["trial"], bad["label"])).value is False
    assert graders.RefundAmountCorrect().evaluate(ctx(bad["trial"], bad["label"])).value is False
    assert graders.DbFactKept().evaluate(ctx(good["trial"], good["label"])).value is True
    assert graders.RefundAmountCorrect().evaluate(ctx(good["trial"], good["label"])).value is True
