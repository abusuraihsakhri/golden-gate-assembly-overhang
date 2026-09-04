"""
Enterprise Security, PHI Outbound Guard, and HMAC-SHA256 Audit Trail.

"""
import os
import re
import json
import time
import hmac
import hashlib
import secrets
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

PHI_PATTERNS = [
    re.compile(r"\b(?:MRN|mrn)[:#\s-]*\d{4,10}\b", re.IGNORECASE),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    re.compile(r"\b(?:DOB|Date of Birth)[:\s]*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", re.IGNORECASE),
    re.compile(r"\b(?:Patient\s+Name|Patient)[:\s]+[A-Z][a-z]+\s+[A-Z][a-z]+\b", re.IGNORECASE),
    re.compile(r"\b(?:John\s+Doe|Jane\s+Smith|Alice\s+Johnson)\b", re.IGNORECASE),
]


class SecurityException(Exception):
    """Raised when outbound data violates HIPAA Safe Harbor or contains raw PHI."""
    pass


class ResourceLimitExceededException(Exception):
    """Raised when computational parameters exceed safety bounds."""
    pass


class PathTraversalException(SecurityException):
    """Raised when a file path attempts to escape the allowed directory."""
    pass


class InputValidationException(SecurityException):
    """Raised when input values fail validation checks."""
    pass


def assert_no_phi(text: str) -> None:
    if not text:
        return
    for pattern in PHI_PATTERNS:
        if pattern.search(str(text)):
            raise SecurityException(f"PHI Outbound Guard Violation: Sensitive identifier detected with pattern {pattern.pattern}")


def assert_safe_path(filepath: str, allowed_base: Optional[str] = None) -> str:
    """Validate that a file path does not escape the allowed directory (path traversal protection)."""
    import pathlib
    base = pathlib.Path(allowed_base or os.getcwd()).resolve()
    target = pathlib.Path(filepath).resolve()
    # Ensure the resolved path is within the allowed base directory
    try:
        target.relative_to(base)
    except ValueError:
        raise PathTraversalException(
            f"Path traversal blocked: '{filepath}' resolves outside allowed directory '{base}'"
        )
    return str(target)


def assert_valid_metric(value: float, field_name: str = "metric") -> float:
    """Validate that a metric value is finite and within acceptable bounds."""
    import math
    if not isinstance(value, (int, float)):
        raise InputValidationException(f"{field_name} must be a number, got {type(value).__name__}")
    if math.isnan(value) or math.isinf(value):
        raise InputValidationException(f"{field_name} must be finite, got {value}")
    # Reasonable bounds for biological measurements (adjust per domain)
    ABSOLUTE_MAX = 1e9
    if abs(value) > ABSOLUTE_MAX:
        raise InputValidationException(f"{field_name} absolute value exceeds maximum ({ABSOLUTE_MAX})")
    return float(value)


class PHIGuard:
    @staticmethod
    def assert_no_phi(text: str) -> None:
        assert_no_phi(text)

    @staticmethod
    def redact_phi(text: str) -> str:
        res = str(text)
        for pattern in PHI_PATTERNS:
            res = pattern.sub("[REDACTED_IDENTIFIER]", res)
        return res


class AuditTrail:
    """Cryptographic Tamper-Evident HMAC-SHA256 Audit Trail."""
    def __init__(self, secret_key: Optional[str] = None):
        resolved_key = secret_key or os.getenv("AUDIT_SECRET_KEY")
        if not resolved_key:
            # Generate a cryptographically secure random key at runtime.
            # This ensures a default is always available for development/testing,
            # but production deployments MUST set AUDIT_SECRET_KEY for persistence.
            resolved_key = secrets.token_hex(32)
        self.secret_key = resolved_key.encode("utf-8") if isinstance(resolved_key, str) else resolved_key
        self.logs: List[Dict[str, Any]] = []

    def log(self, actor: str, actor_tier: str, event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        payload_str = json.dumps(details, sort_keys=True)
        assert_no_phi(payload_str)
        payload_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
        audit_id = f"AUDIT-{int(time.time()*1000)}-{len(self.logs)+1}"
        ts = datetime.now(timezone.utc).isoformat()
        prev_hash = self.logs[-1]["current_hash"] if self.logs else "GENESIS_BLOCK_0000000000000000"
        sign_string = f"{audit_id}|{ts}|{actor}|{actor_tier}|{event_type}|{payload_hash}|{prev_hash}"
        signature = hmac.new(self.secret_key, sign_string.encode("utf-8"), hashlib.sha256).hexdigest()
        entry = {
            "audit_id": audit_id,
            "timestamp": ts,
            "actor": actor,
            "actor_tier": actor_tier,
            "event_type": event_type,
            "payload_hash": payload_hash,
            "prev_hash": prev_hash,
            "current_hash": signature,
        }
        self.logs.append(entry)
        return entry

    def _compute_signature(self, entry: Dict[str, Any]) -> str:
        """Recompute the HMAC signature for a given entry to verify it."""
        sign_string = f"{entry['audit_id']}|{entry['timestamp']}|{entry['actor']}|{entry['actor_tier']}|{entry['event_type']}|{entry['payload_hash']}|{entry['prev_hash']}"
        return hmac.new(self.secret_key, sign_string.encode("utf-8"), hashlib.sha256).hexdigest()

    def verify_integrity(self) -> bool:
        """Verify both chain linkage and HMAC signatures for all entries."""
        for i, entry in enumerate(self.logs):
            # Verify chain linkage
            prev = self.logs[i-1]["current_hash"] if i > 0 else "GENESIS_BLOCK_0000000000000000"
            if entry["prev_hash"] != prev:
                return False
            # Verify HMAC signature authenticity
            expected_sig = self._compute_signature(entry)
            if not hmac.compare_digest(entry["current_hash"], expected_sig):
                return False
        return True

    def get_trail(self) -> List[Dict[str, Any]]:
        return self.logs


GLOBAL_AUDIT = AuditTrail()


class AuditLogger:
    @staticmethod
    def log(actor: str, actor_tier: str, event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        return GLOBAL_AUDIT.log(actor, actor_tier, event_type, details)

    @staticmethod
    def get_trail() -> List[Dict[str, Any]]:
        return GLOBAL_AUDIT.get_trail()

    @staticmethod
    def verify_integrity() -> bool:
        return GLOBAL_AUDIT.verify_integrity()


class ActionExecutor:
    @staticmethod
    def execute_with_audit(actor: str, actor_tier: str, action_type: str, fn, *args, **kwargs):
        res = fn(*args, **kwargs)
        AuditLogger.log(actor, actor_tier, action_type, {"status": "SUCCESS"})
        return res
