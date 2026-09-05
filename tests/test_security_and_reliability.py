"""
Security and reliability tests for post-cardiac-arrest-agent.
"""
import os
import sys
import tempfile
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.base import AuditTrail, PHIGuard, SecurityException


class TestAuditTrailSecurity:
    """Tests for HMAC audit trail security."""

    def test_no_hardcoded_secret_fallback(self):
        """AuditTrail should not fall back to a hardcoded default key."""
        # Clear any existing env var
        old_key = os.environ.pop("AUDIT_SECRET_KEY", None)
        try:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                trail = AuditTrail()
                # Should warn about missing secret key
                assert any("AUDIT_SECRET_KEY" in str(warning.message) for warning in w)
        finally:
            if old_key is not None:
                os.environ["AUDIT_SECRET_KEY"] = old_key

    def test_explicit_key_produces_deterministic_signatures(self):
        """Same key and same log entry should produce same signature."""
        trail = AuditTrail(secret_key="test-key-for-deterministic-signing")
        entry1 = trail.log("actor1", "tier1", "EVENT_A", {"x": 1})

        trail2 = AuditTrail(secret_key="test-key-for-deterministic-signing")
        entry2 = trail2.log("actor1", "tier1", "EVENT_A", {"x": 1})

        assert entry1["current_hash"] == entry2["current_hash"]

    def test_different_keys_produce_different_signatures(self):
        """Different keys should produce different HMAC signatures."""
        trail1 = AuditTrail(secret_key="key-one")
        trail2 = AuditTrail(secret_key="key-two")

        entry1 = trail1.log("actor", "tier", "EVENT", {"data": "value"})
        entry2 = trail2.log("actor", "tier", "EVENT", {"data": "value"})

        assert entry1["current_hash"] != entry2["current_hash"]

    def test_verify_integrity_with_tampered_chain(self):
        """Tampered audit chain should fail integrity verification."""
        trail = AuditTrail(secret_key="test-key")
        trail.log("actor", "tier", "EVENT_A", {"x": 1})
        trail.log("actor", "tier", "EVENT_B", {"x": 2})

        assert trail.verify_integrity() is True

        # Tamper with the chain
        trail.logs[0]["current_hash"] = "TAMPERED_HASH"
        assert trail.verify_integrity() is False


class TestPHIGuard:
    """Tests for PHI outbound guard."""

    def test_ssn_pattern_detected(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient SSN: 123-45-6789")

    def test_mrn_pattern_detected(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("MRN-12345678 specimen collected")

    def test_phone_pattern_detected(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Contact patient at 555-123-4567")

    def test_email_pattern_detected(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Email results to doctor@hospital.org")

    def test_clean_text_passes(self):
        """Non-PHI clinical text should pass without raising."""
        PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")
        PHIGuard.assert_no_phi("Metric value 24.5 within normal range")

    def test_empty_text_passes(self):
        PHIGuard.assert_no_phi("")
        PHIGuard.assert_no_phi(None)

    def test_redact_phi(self):
        result = PHIGuard.redact_phi("Patient MRN-994827 and SSN 123-45-6789")
        assert "MRN" not in result or "REDACTED" in result
        assert "123-45-6789" not in result


class TestBatchCLI:
    """Tests for batch CLI error handling."""

    def test_batch_missing_input_file(self, capsys):
        """Batch command with missing input file should return error code."""
        from cli import main
        result = main(["batch", "-i", "nonexistent_file_12345.csv"])
        assert result == 1

    def test_batch_invalid_output_directory(self, capsys):
        """Batch command with invalid output directory should return error code."""
        from cli import main
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("task_id,target_identifier,primary_metric,secondary_metric,status_descriptor,is_critical_flag\n")
            f.write("T1,TARGET-01,15.0,5.0,NOMINAL,false\n")
            tmp_path = f.name
        try:
            result = main(["batch", "-i", tmp_path, "-o", "/nonexistent_dir_12345/output.csv"])
            assert result == 1
        finally:
            os.unlink(tmp_path)

    def test_batch_valid_csv(self):
        """Batch command with valid CSV should process successfully."""
        from cli import main
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            f.write("task_id,target_identifier,primary_metric,secondary_metric,status_descriptor,is_critical_flag\n")
            f.write("T1,TARGET-01,15.0,5.0,NOMINAL,false\n")
            f.write("T2,TARGET-02,35.0,15.0,DISCORDANT,true\n")
            tmp_path = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as out_f:
            out_path = out_f.name

        try:
            result = main(["batch", "-i", tmp_path, "-o", out_path])
            assert result == 0

            import csv
            with open(out_path, mode='r', encoding='utf-8') as rf:
                reader = csv.DictReader(rf)
                rows = list(reader)
                assert len(rows) == 2
                assert "overall_urgency" in rows[0]
                assert "audit_hash" in rows[0]
        finally:
            os.unlink(tmp_path)
            if os.path.exists(out_path):
                os.unlink(out_path)
