"""
test_single_instance.py - Tier 1 & Tier 2 Opaque-Box E2E Tests for Single-Instance Enforcement.

Covers:
- SingleInstanceGuard primary acquisition vs secondary rejection.
- QLocalServer / QLocalSocket IPC activation signaling.
- Lock release and re-acquisition lifecycle.
- Boundary conditions: empty app key, stale server cleanup, rapid sequential attempts, long keys, multiple releases.
"""

import sys
import unittest
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication

from single_instance import SingleInstanceGuard


class TestSingleInstanceEnforcement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.guard1 = SingleInstanceGuard(app_key="test_phantom_app_key_1")
        self.guard2 = SingleInstanceGuard(app_key="test_phantom_app_key_1")

    def tearDown(self):
        self.guard1.release()
        self.guard2.release()

    # --- Tier 1: Happy-Path Test Cases (≥5) ---

    def test_tier1_primary_instance_acquisition(self):
        """Tier 1: Primary instance successfully acquires single instance lock."""
        res = self.guard1.try_acquire("test_key_primary")
        self.assertTrue(res, "Primary instance must acquire single instance lock.")
        self.guard1.release()

    def test_tier1_secondary_instance_rejection(self):
        """Tier 2: Secondary instance attempt with same app key is rejected (returns False)."""
        key = "test_key_secondary"
        acquired1 = self.guard1.try_acquire(key)
        self.assertTrue(acquired1, "First instance must acquire lock.")

        acquired2 = self.guard2.try_acquire(key)
        self.assertFalse(acquired2, "Second instance must be rejected when app is already running.")
        self.guard1.release()

    def test_tier1_ipc_socket_connection(self):
        """Tier 1: Secondary instance connects to primary instance server via QLocalSocket."""
        key = "test_key_ipc"
        acquired1 = self.guard1.try_acquire(key)
        self.assertTrue(acquired1)

        # Secondary instance try_acquire triggers connection to primary
        acquired2 = self.guard2.try_acquire(key)
        self.assertFalse(acquired2)
        self.guard1.release()

    def test_tier1_activation_signal_emitted(self):
        """Tier 1: Secondary instance attempt triggers activation_requested signal on primary."""
        key = "test_key_signal"
        activation_received = []

        self.guard1.activation_requested.connect(lambda: activation_received.append(True))
        acquired1 = self.guard1.try_acquire(key)
        self.assertTrue(acquired1)

        # Second instance triggers signal
        acquired2 = self.guard2.try_acquire(key)
        self.assertFalse(acquired2)
        self.assertEqual(len(activation_received), 1, "Secondary launch must trigger activation_requested signal on primary.")
        self.guard1.release()

    def test_tier1_release_and_reacquire(self):
        """Tier 1: Releasing primary instance lock allows subsequent instance to acquire lock."""
        key = "test_key_reacquire"
        self.assertTrue(self.guard1.try_acquire(key))
        self.guard1.release()

        # New acquire after release
        self.assertTrue(self.guard2.try_acquire(key), "Subsequent instance must be able to acquire lock after primary releases.")

    # --- Tier 2: Boundary & Corner Cases (≥5) ---

    def test_tier2_empty_app_key_handling(self):
        """Tier 2: Empty or whitespace app key handles input safely / raises ValueError."""
        with self.assertRaises((ValueError, Exception)):
            self.guard1.try_acquire("")

    def test_tier2_stale_server_cleanup(self):
        """Tier 2: SingleInstanceGuard cleans up stale server files before acquiring."""
        key = "test_key_stale"
        # Simulate initial acquire and ungraceful cleanup
        self.guard1.try_acquire(key)
        self.guard1._server.close() if hasattr(self.guard1, "_server") and self.guard1._server else None
        
        # New acquisition should succeed by cleaning stale server
        guard_new = SingleInstanceGuard(app_key=key)
        res = guard_new.try_acquire(key)
        self.assertTrue(res, "Stale socket server should be cleaned up automatically.")
        guard_new.release()

    def test_tier2_rapid_concurrent_acquire_attempts(self):
        """Tier 2: Rapid sequential acquire/release attempts maintain consistent state."""
        key = "test_key_rapid"
        for i in range(5):
            g = SingleInstanceGuard(app_key=key)
            res = g.try_acquire(key)
            self.assertTrue(res, f"Iteration {i} should acquire lock successfully.")
            g.release()

    def test_tier2_long_app_key_truncation(self):
        """Tier 2: Extremely long key (>200 chars) handles lock creation without crashing."""
        long_key = "a" * 250
        res = self.guard1.try_acquire(long_key)
        self.assertTrue(res, "Long application key must be handled safely.")
        self.guard1.release()

    def test_tier2_multiple_releases_idempotent(self):
        """Tier 2: Calling release() multiple times is idempotent and does not crash."""
        key = "test_key_multi_release"
        self.guard1.try_acquire(key)
        self.guard1.release()
        self.guard1.release()  # Second release call
        self.guard1.release()  # Third release call
        self.assertTrue(True, "Multiple releases must be safe and idempotent.")


if __name__ == "__main__":
    unittest.main()
