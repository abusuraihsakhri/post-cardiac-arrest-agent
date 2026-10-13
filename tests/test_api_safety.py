"""Regression tests for input validation and API safety boundaries."""
import math
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from agents.api import app
from agents.models import SystemTaskPayload
from agents.llm_factory import LLMFactory

client = TestClient(app)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_invalid_numeric_payload_is_rejected(value):
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="T1", target_identifier="SYN-1", primary_metric=value)


def test_sensitive_identifier_not_reflected_in_api_error():
    response = client.post("/api/audit", json={
        "task_id": "Patient John Doe",
        "target_identifier": "SYN-1",
        "primary_metric": 1.0,
    })
    assert response.status_code == 422
    assert "John Doe" not in response.text


def test_nested_identifier_is_rejected():
    response = client.post("/api/audit", json={
        "task_id": "T1",
        "target_identifier": "SYN-1",
        "primary_metric": 1.0,
        "attributes": {"notes": "Patient MRN-994827"}
    })
    assert response.status_code == 422


def test_audit_log_endpoint_exposes_no_unauthenticated_records():
    response = client.get("/api/audit/logs")
    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"verified", "entry_count"}
    assert "audit_trail" not in payload


def test_unimplemented_inference_provider_fails_closed():
    with pytest.raises(ValueError, match="not implemented"):
        LLMFactory.create("openai")
