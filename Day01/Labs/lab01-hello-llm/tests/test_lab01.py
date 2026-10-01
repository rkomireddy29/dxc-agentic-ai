"""Lab 1 auto-checks - one test per challenge. Run: pytest Day01\\Labs\\lab01-hello-llm
Tests 1, 2, 4, 5 run offline (a fake Bedrock client). Tests 3 and 6 check your saved evidence.
"""
import json
import re
import sys
from pathlib import Path

import pytest

LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB))
sys.path.insert(0, str(LAB.parents[2]))

import lab01a_first_call as a  # noqa: E402
import lab01b_extract as b  # noqa: E402


class FakeClient:
    """Pretends to be Bedrock so tests run offline, fast and free."""

    def __init__(self, content=None):
        self.calls = []
        self.content = content or [{"text": "Try restarting OrbitConnect."}]

    def converse(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "output": {"message": {"role": "assistant", "content": self.content}},
            "usage": {"inputTokens": 42, "outputTokens": 7, "totalTokens": 49},
            "stopReason": "tool_use" if any("toolUse" in c for c in self.content) else "end_turn",
            "metrics": {"latencyMs": 5},
        }


# ---------- Lab B ----------
def test_challenge_1_converse_call():
    fc = FakeClient()
    r = a.ask(fc, "model-x", "VPN error 809")
    assert fc.calls, "TODO-1: client.converse(...) was never called"
    call = fc.calls[0]
    assert call.get("modelId") == "model-x", "TODO-1: pass modelId=model_id"
    assert "VPN error 809" in json.dumps(call.get("messages")), "TODO-1: put the prompt in messages"
    assert r["text"] == "Try restarting OrbitConnect.", "TODO-1: return the reply text"


def test_challenge_2_tokens_and_latency():
    r = a.ask(FakeClient(), "model-x", "hello")
    assert r["input_tokens"] == 42, "TODO-2: read response['usage']['inputTokens']"
    assert r["output_tokens"] == 7, "TODO-2: read response['usage']['outputTokens']"
    assert isinstance(r["latency_ms"], int) and r["latency_ms"] >= 0


def test_challenge_3_model_shootout():
    tickets = [{"ticket_id": f"T{i}", "subject": "s", "description": "d"} for i in range(3)]
    rows = a.compare_models(FakeClient(), ["m1", "m2"], tickets)
    assert len(rows) == 6, "TODO-3: one row per model x ticket"
    assert {"model_id", "ticket_id", "text", "input_tokens", "output_tokens", "latency_ms"} <= set(rows[0])
    assert a.RESULTS_FILE.exists(), "Run the script for real: python Day01\\Labs\\lab01-hello-llm\\lab01a_first_call.py"
    saved = json.loads(a.RESULTS_FILE.read_text(encoding="utf-8"))
    assert len(saved["summary"]) >= 2, "Evidence file should show 2 models"
    assert all(r["text"] for r in saved["rows"]), "Evidence file has empty answers"


# ---------- Lab C ----------
GOOD = {"category": "Access", "priority": "High", "user_id": "EMP-1042",
        "summary": "Locked out after password change", "sentiment": "Urgent"}


def test_challenge_4_ticket_schema():
    t = b.Ticket(**GOOD)
    assert t.priority == "High" and t.user_id == "EMP-1042", "TODO-4: add all 5 fields"
    assert b.Ticket(**{**GOOD, "user_id": None}).user_id is None, "TODO-4: user_id must be optional"
    for bad in ({"priority": "Super"}, {"category": "Coffee"}, {"user_id": "1042"},
                {"summary": "x" * 200}, {"sentiment": "Happy"}):
        with pytest.raises(Exception):
            b.Ticket(**{**GOOD, **bad})


def test_challenge_5_structured_extraction():
    fc = FakeClient(content=[{"toolUse": {"toolUseId": "t1", "name": b.TOOL_NAME, "input": GOOD}}])
    t = b.extract_ticket(fc, "model-x", "I'm locked out")
    assert isinstance(t, b.Ticket) and t.category == "Access"
    tc = fc.calls[0].get("toolConfig", {})
    assert tc.get("toolChoice", {}).get("tool", {}).get("name") == b.TOOL_NAME, "TODO-5: force the tool with toolChoice"
