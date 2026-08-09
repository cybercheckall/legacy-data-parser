"""
test_challenger_m1_2.py - Comprehensive Adversarial Challenge Suite for Milestone 1.

Adversarially tests single_instance.py and profile_manager.py:
1. Long key strings (>1000 chars), empty keys, whitespace keys, unicode, control characters.
2. Socket IPC activation message handling with corrupted, unexpected, or malicious payload bytes.
3. Profile manager schema integrity, corrupt JSON handling, search engine fallback, and atomic persistence.
"""

import getpass
import hashlib
import json
import os
import sys
import tempfile
import unittest
from typing import List

from PyQt6.QtCore import QCoreApplication
from PyQt6.QtNetwork import QLocalSocket
from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtWidgets import QApplication

from owl.profiles.profile_manager import Profile, ProfileManager, create_otr_web_profile, sanitize_search_engine
from owl.stealth.single_instance import DEFAULT_APP_KEY, SingleInstanceGuard


class TestSingleInstanceAdversarialEdgeCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.guards: List[SingleInstanceGuard] = []

    def tearDown(self):
        for g in self.guards:
            try:
                g.release()
            except Exception:
                pass
        self.guards.clear()
        QCoreApplication.processEvents()

    def _create_guard(self, key: str = None) -> SingleInstanceGuard:
        g = SingleInstanceGuard(app_key=key)
        self.guards.append(g)
        return g

    # --- 1. App Key String Edge Cases ---

    def test_empty_app_key_raises_value_error(self):
        """Empty string app_key raises ValueError."""
        g = self._create_guard()
        with self.assertRaises(ValueError):
            g.try_acquire("")

    def test_whitespace_app_key_raises_value_error(self):
        """Whitespace-only app_key raises ValueError."""
        g = self._create_guard()
        whitespace_keys = [" ", "   ", "\t\t", "\n\r", " \t \n "]
        for wk in whitespace_keys:
            with self.assertRaises(ValueError):
                g.try_acquire(wk)

    def test_none_app_key_uses_default(self):
        """None app_key uses DEFAULT_APP_KEY safely."""
        g = self._create_guard(None)
        res = g.try_acquire(None)
        self.assertTrue(res, "None app_key should default to DEFAULT_APP_KEY and acquire lock.")
        self.assertEqual(g.app_key, DEFAULT_APP_KEY)
        g.release()

    def test_long_app_key_hashing(self):
        """Very long key (>60 chars, up to 5,000 chars) is safely hashed to avoid OS pipe length limits."""
        long_key = "A" * 5000
        g = self._create_guard(long_key)
        server_name = g._get_server_name(long_key)
        user = getpass.getuser()
        
        # Verify hash truncation: sha256 hex[:24]
        expected_hash = hashlib.sha256(long_key.strip().encode("utf-8")).hexdigest()[:24]
        expected_name = f"OwlWorkspace_{expected_hash}_{user}"
        self.assertEqual(server_name, expected_name)

        # Confirm try_acquire works cleanly with long key
        res = g.try_acquire(long_key)
        self.assertTrue(res, "Long key (>5000 chars) must acquire lock successfully.")
        g.release()

    def test_unicode_and_special_character_keys(self):
        """Unicode, emoji, and control characters in key strings are handled safely."""
        unicode_keys = [
            "Phantom_🚀_Stealth_🔒",
            "Key_With_Symbols_!@#$%^&*()_+{}[]|:;'<>,.?",
            "Key_With_Tabs_\t_And_Newlines_\n",
        ]
        for key in unicode_keys:
            g = SingleInstanceGuard(app_key=key)
            self.guards.append(g)
            acquired = g.try_acquire(key)
            self.assertTrue(acquired, f"Key '{key}' must acquire lock cleanly.")
            g.release()
            QCoreApplication.processEvents()

    # --- 2. IPC Activation Socket Bombardment & Payload Corruption ---

    def test_corrupted_payload_bytes_over_socket(self):
        """IPC activation handles corrupted binary bytes, NULL bytes, and random noise without crashing."""
        key = "challenger2_corrupt_ipc_test"
        primary = self._create_guard(key)
        self.assertTrue(primary.try_acquire(key))

        server_name = primary._get_server_name(key)

        activations = []
        primary.activation_requested.connect(lambda: activations.append(True))

        corrupted_payloads = [
            b"\x00\x00\x00\x00",  # NULL bytes
            b"\xff\xfe\xfd\xfc\xfb",  # High binary bytes
            b"INVALID_PROTOCOL_HEADER\r\n",  # Unexpected string header
            b"\x7f\x80\x81\x90\xaa\xbb\xcc\xdd\xee\xff",  # Non-UTF8 byte noise
            b"ACTIVATE_WITH_EXTRA_GARBAGE_\x00_DATA",  # Mixed valid/invalid
        ]

        for payload in corrupted_payloads:
            sock = QLocalSocket()
            sock.connectToServer(server_name)
            if sock.waitForConnected(1000):
                sock.write(payload)
                sock.flush()
                sock.waitForBytesWritten(500)
                sock.disconnectFromServer()
                sock.close()
            QCoreApplication.processEvents()

        # Check primary guard received activations without crashing or throwing
        self.assertGreater(len(activations), 0, "Primary instance must handle corrupted byte streams and emit activation signal.")

        # Primary guard must remain fully functional and reject a legitimate secondary instance
        secondary = self._create_guard(key)
        res = secondary.try_acquire(key)
        self.assertFalse(res, "Primary guard must stay responsive and reject secondary instance after socket bombardment.")
        primary.release()
        secondary.release()

    def test_huge_ipc_payload_handling(self):
        """IPC socket receives a 2 MB binary payload without memory allocation failure or server crash."""
        key = "challenger2_huge_payload_key"
        primary = self._create_guard(key)
        self.assertTrue(primary.try_acquire(key))

        server_name = primary._get_server_name(key)

        sock = QLocalSocket()
        sock.connectToServer(server_name)
        if sock.waitForConnected(1000):
            huge_data = b"Z" * (2 * 1024 * 1024)  # 2 MB payload
            sock.write(huge_data)
            sock.flush()
            sock.waitForBytesWritten(1000)
            sock.disconnectFromServer()
            sock.close()

        QCoreApplication.processEvents()

        # Verify server is still alive
        secondary = self._create_guard(key)
        self.assertFalse(secondary.try_acquire(key), "Server must remain responsive after receiving 2 MB payload.")
        primary.release()
        secondary.release()

    def test_socket_disconnect_without_data(self):
        """Connecting to primary server emits activation signal."""
        key = "challenger2_empty_connect_key"
        primary = self._create_guard(key)
        self.assertTrue(primary.try_acquire(key))

        server_name = primary._get_server_name(key)

        activations = []
        primary.activation_requested.connect(lambda: activations.append(True))

        sock = QLocalSocket()
        sock.connectToServer(server_name)
        if sock.waitForConnected(1000):
            sock.write(b"ACTIVATE\n")
            sock.flush()
            sock.waitForBytesWritten(500)
            QCoreApplication.processEvents()
            sock.disconnectFromServer()
            sock.close()

        QCoreApplication.processEvents()
        self.assertGreaterEqual(len(activations), 1, "Connection event must trigger activation signal.")
        primary.release()


class TestProfileManagerAdversarialEdgeCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.json_path = os.path.join(self.tmp_dir.name, "profiles.json")

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_search_engine_sanitization(self):
        """Invalid or malformed search engines sanitize to 'Google'."""
        self.assertEqual(sanitize_search_engine("Google"), "Google")
        self.assertEqual(sanitize_search_engine("DuckDuckGo"), "DuckDuckGo")
        self.assertEqual(sanitize_search_engine("Bing"), "Google")
        self.assertEqual(sanitize_search_engine(""), "Google")
        self.assertEqual(sanitize_search_engine("   "), "Google")
        self.assertEqual(sanitize_search_engine(None), "Google")
        self.assertEqual(sanitize_search_engine("GOOGLE"), "Google")

    def test_corrupt_json_structure_fallback(self):
        """Malformed or invalid JSON structures fall back gracefully to default profiles."""
        invalid_contents = [
            "{invalid_json: true",  # Syntax error
            "[]",  # Array instead of dict
            '"just a string"',  # Primitive string
            '{"profiles": "not_a_list"}',  # Non-list profiles field
            '{"profiles": []}',  # Empty profiles list
        ]

        for content in invalid_contents:
            with open(self.json_path, "w", encoding="utf-8") as f:
                f.write(content)

            pm = ProfileManager(json_path=self.json_path)
            profiles = pm.get_all_profiles()
            self.assertGreaterEqual(len(profiles), 1, f"Failed for content: {content}")
            self.assertEqual(profiles[0].name, "Guest mode")

    def test_prevent_last_profile_deletion(self):
        """ProfileManager prevents deleting the last remaining profile."""
        pm = ProfileManager(json_path=self.json_path)
        all_profs = pm.get_all_profiles()
        
        # Delete down to 1 profile
        pm.delete_profile(all_profs[0].id)
        self.assertEqual(len(pm.get_all_profiles()), 1)

        # Attempt to delete the final profile
        last_id = pm.get_all_profiles()[0].id
        res = pm.delete_profile(last_id)
        self.assertFalse(res, "Deleting last profile must return False.")
        self.assertEqual(len(pm.get_all_profiles()), 1, "Last profile must remain in manager.")

    def test_delete_active_profile_auto_switches_active(self):
        """Deleting the currently active profile automatically reassigns active_profile_id to a remaining profile."""
        pm = ProfileManager(json_path=self.json_path)
        pm.create_profile(name="Secondary Profile")
        active_id = pm.get_active_profile().id

        res = pm.delete_profile(active_id)
        self.assertTrue(res)
        new_active = pm.get_active_profile()
        self.assertIsNotNone(new_active)
        self.assertNotEqual(new_active.id, active_id)

    def test_otr_profile_security_settings(self):
        """create_otr_web_profile sets correct Off-The-Record properties."""
        p = Profile(id="p1", name="Test")
        web_prof = create_otr_web_profile(p)
        self.assertTrue(web_prof.isOffTheRecord(), "WebEngine profile must be Off-The-Record")
        self.assertEqual(
            web_prof.persistentCookiesPolicy(),
            QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies
        )
        self.assertEqual(
            web_prof.httpCacheType(),
            QWebEngineProfile.HttpCacheType.MemoryHttpCache
        )


if __name__ == "__main__":
    unittest.main()
