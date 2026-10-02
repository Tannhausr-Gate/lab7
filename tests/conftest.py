import os
import re

import pytest

# Required by config.py at import time. No AWS calls are made in tests.
os.environ.setdefault("AWS_REGION", "us-east-1")
os.environ.setdefault("BEDROCK_MODEL_ID", "test-model")
os.environ.setdefault("BEDROCK_MAX_TOKENS", "512")
os.environ.setdefault("GUARDRAIL_ID", "test-guardrail")

import config  # noqa: E402
import controls  # noqa: E402

PATTERNS = {
    "EMAIL": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "PHONE": re.compile(r"\b\d{3}-\d{3}-\d{4}\b"),
    "NAME": re.compile(r"Alex Testrider|Jordan Sample"),
    "ADDRESS": re.compile(r"\b\d+ (?:Example Lane|Placeholder Ave)\b"),
    "DRIVER_ID": re.compile(r"\bS\d{8}\b"),
    "CREDIT_DEBIT_NUMBER": re.compile(r"\b(?:\d{4} ){3}\d{4}\b"),
}


class FakeComprehend:
    def detect_pii_entities(self, Text, LanguageCode):
        entities = [
            {"Type": kind, "Score": 0.99, "BeginOffset": m.start(), "EndOffset": m.end()}
            for kind, pattern in PATTERNS.items()
            for m in pattern.finditer(Text)
        ]
        return {"Entities": entities}


class FakeGuardrail:
    def apply_guardrail(self, guardrailIdentifier, guardrailVersion, source, content):
        text = content[0]["text"]["text"]
        hit = any(p.search(text) for p in PATTERNS.values())
        return {"action": "GUARDRAIL_INTERVENED" if hit else "NONE", "outputs": []}


class UnavailableClient:
    def __getattr__(self, name):
        def _fail(**kwargs):
            raise ConnectionError("service unavailable")
        return _fail


@pytest.fixture(autouse=True)
def aws_fakes(monkeypatch, tmp_path):
    monkeypatch.setattr(controls, "_bedrock", FakeGuardrail())
    monkeypatch.setattr(controls, "_comprehend", FakeComprehend())
    monkeypatch.setattr(config, "AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    monkeypatch.setattr(config, "PARTNER_OUTBOX_PATH", str(tmp_path / "outbox.jsonl"))
    return tmp_path


@pytest.fixture
def comprehend_down(monkeypatch):
    monkeypatch.setattr(controls, "_comprehend", UnavailableClient())


@pytest.fixture
def guardrail_down(monkeypatch):
    monkeypatch.setattr(controls, "_bedrock", UnavailableClient())