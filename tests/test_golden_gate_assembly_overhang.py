"""
Automated Pytest Test Suite for Golden Gate Assembly Overhang.
Domain: AI Drug Discovery, Structural Biology & Wet-Lab Robotics
Standard: wwPDB / IUPAC / OpenSMILES / ISAC Standards
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.base import PHIGuard, AuditLogger, SecurityException, PathTraversalException, InputValidationException, assert_safe_path, assert_valid_metric, AuditTrail
from agents.models import SystemTaskPayload, UrgencyLevel, SystemIntegrityStatus
from agents.workers import InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker
from agents.supervisor import SystemSupervisor
from cli import main


def test_phi_guard_enforcement():
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient MRN-994827 blood culture positive for Staphylococcus")

    # Clean text passes
    PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")


def test_path_traversal_protection():
    """Verify that path traversal attempts are blocked."""
    # Safe path should work
    safe = assert_safe_path("sample.csv")
    assert safe.endswith("sample.csv")

    # Relative path traversal should be blocked
    with pytest.raises(PathTraversalException):
        assert_safe_path("../../../etc/passwd")

    # Absolute path outside cwd should be blocked
    with pytest.raises(PathTraversalException):
        assert_safe_path("/etc/passwd")


def test_input_validation_metrics():
    """Verify that NaN and Infinity are rejected."""
    import math

    # Valid values pass
    assert assert_valid_metric(25.0) == 25.0
    assert assert_valid_metric(0.0) == 0.0
    assert assert_valid_metric(-5.5) == -5.5

    # NaN rejected
    with pytest.raises(InputValidationException):
        assert_valid_metric(float("nan"), "primary_metric")

    # Infinity rejected
    with pytest.raises(InputValidationException):
        assert_valid_metric(float("inf"), "primary_metric")

    with pytest.raises(InputValidationException):
        assert_valid_metric(float("-inf"), "secondary_metric")


def test_audit_trail_signature_verification():
    """Verify that verify_integrity detects tampered signatures."""
    trail = AuditTrail(secret_key="test-secret-key-for-verification")
    entry = trail.log("test_actor", "test_tier", "TEST_EVENT", {"data": "test"})

    # Integrity should pass initially
    assert trail.verify_integrity() is True

    # Tamper with the signature
    trail.logs[0]["current_hash"] = "tampered_signature_12345"
    assert trail.verify_integrity() is False


def test_audit_trail_chain_verification():
    """Verify that verify_integrity detects broken chain links."""
    trail = AuditTrail(secret_key="test-secret-key-for-chain")
    trail.log("actor1", "tier1", "EVENT_1", {"step": 1})
    trail.log("actor2", "tier2", "EVENT_2", {"step": 2})

    # Integrity should pass initially
    assert trail.verify_integrity() is True

    # Tamper with chain link
    trail.logs[1]["prev_hash"] = "broken_link_hash"
    assert trail.verify_integrity() is False


def test_audit_trail_no_hardcoded_secret():
    """Verify that audit trail uses secure random key when no env var is set."""
    import os
    # Save and clear any existing env var
    saved = os.environ.pop("AUDIT_SECRET_KEY", None)
    try:
        trail = AuditTrail()
        # Key should be 64 hex chars (32 bytes)
        assert len(trail.secret_key) == 64
        # Should be valid hex
        int(trail.secret_key.decode(), 16)
    finally:
        if saved:
            os.environ["AUDIT_SECRET_KEY"] = saved


def test_specialized_workers():
    # Worker 1: QC Invariant
    p1 = SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=35.0)
    alerts1 = InvariantQCWorker.evaluate(p1)
    assert len(alerts1) == 1
    assert alerts1[0].urgency == UrgencyLevel.ELEVATED

    # Worker 2: Safety
    p2 = SystemTaskPayload(task_id="T2", target_identifier="KEY-02", primary_metric=10.0, is_critical_flag=True)
    alerts2 = SafetyEscalationWorker.evaluate(p2)
    assert len(alerts2) == 1
    assert alerts2[0].urgency == UrgencyLevel.CRITICAL_STAT

    # Worker 3: Protocol Conformance
    p3 = SystemTaskPayload(task_id="T3", target_identifier="KEY-03", primary_metric=10.0, status_descriptor="DISCORDANT_ANOMALY")
    alerts3 = ProtocolConformanceWorker.evaluate(p3)
    assert len(alerts3) == 1


def test_supervisor_consensus_and_audit():
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="TASK-PROD-01",
        target_identifier="KEY-PROD-01",
        primary_metric=12.0,
        secondary_metric=4.0,
        status_descriptor="NOMINAL"
    )
    dossier = supervisor.process_task(payload)
    assert dossier.overall_urgency == UrgencyLevel.ROUTINE
    assert dossier.integrity_status == SystemIntegrityStatus.VALIDATED
    assert dossier.audit_hash != ""

    # Verify cryptographic audit trail
    assert AuditLogger.verify_integrity() is True

    # CLI tests
    assert main(["audit", "--task-id", "CLI-TEST-01"]) == 0
    assert main(["chat", "Explain", "specifications"]) == 0
    assert main(["verify-audit"]) == 0
