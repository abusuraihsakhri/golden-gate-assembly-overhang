import csv
from pathlib import Path

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from agents.api import api_audit_logs
from agents.base import AuditTrail, SecurityException
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from cli import main as operations_main
from golden_gate_agent.cli import main as legacy_main


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_model_rejects_nonfinite_metrics(value):
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="TEST", target_identifier="X", primary_metric=value)
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="TEST", target_identifier="X", primary_metric=1, secondary_metric=value)


def test_nested_attributes_screened_for_identifiers():
    task = SystemTaskPayload(
        task_id="TEST", target_identifier="X", primary_metric=1,
        attributes={"notes": {"email": "private@example.com"}},
    )
    with pytest.raises(SecurityException):
        SystemSupervisor().process_task(task)


def test_audit_trail_accessor_is_read_only_copy():
    trail = AuditTrail(secret_key="test-key")
    trail.log("tester", "test", "test-event", {"safe": True})
    exported = trail.get_trail()
    exported[0]["current_hash"] = "tampered"
    assert trail.verify_integrity()


def test_log_endpoint_defaults_closed(monkeypatch):
    monkeypatch.delenv("AUDIT_READ_TOKEN", raising=False)
    with pytest.raises(HTTPException) as error:
        api_audit_logs(x_audit_token=None)
    assert error.value.status_code == 403


def test_log_endpoint_requires_correct_token(monkeypatch):
    monkeypatch.setenv("AUDIT_READ_TOKEN", "private-demo-token")
    with pytest.raises(HTTPException):
        api_audit_logs(x_audit_token="wrong")
    assert api_audit_logs(x_audit_token="private-demo-token")["verified"] is True


@pytest.mark.parametrize("flag,critical", [("False", False), ("true", True), ("0", False), ("1", True)])
@pytest.mark.parametrize("cli_name,runner,status_name,critical_text", [
    ("operations", operations_main, "overall_urgency", "CRITICAL_STAT_PANIC"),
    ("legacy", legacy_main, "overall_status", "CRITICAL_INTERVENTION_REQUIRED"),
])
def test_batch_booleans(tmp_path, monkeypatch, flag, critical, cli_name, runner, status_name, critical_text):
    monkeypatch.chdir(tmp_path)
    Path("input.csv").write_text(
        "task_id,target_identifier,primary_metric,secondary_metric,is_critical_flag,status_descriptor\n"
        f"T,X,1,1,{flag},NOMINAL\n", encoding="utf-8",
    )
    assert runner(["batch", "-i", "input.csv", "-o", "output.csv"]) == 0
    with Path("output.csv").open(encoding="utf-8", newline="") as stream:
        row = next(csv.DictReader(stream))
    assert (row[status_name] == critical_text) is critical


def test_invalid_boolean_flag_is_rejected(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("input.csv").write_text(
        "task_id,target_identifier,primary_metric,secondary_metric,is_critical_flag,status_descriptor\n"
        "T,X,1,1,sometimes,NOMINAL\n", encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Invalid is_critical_flag"):
        operations_main(["batch", "-i", "input.csv", "-o", "output.csv"])
