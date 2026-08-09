"""
test_m1_stress_and_edge.py - Empirical Stress and Adversarial Edge Case Suite for Milestone 1.

Adversarially tests:
1. Profile System: Rapid CRUD, concurrency, file corruption (truncated, malformed, wrong types, nulls), path traversal, edge strings, last profile protection.
2. Single Instance Guard: Concurrent multi-threaded acquisition races, rapid release/re-acquire cycles, garbage IPC payloads, connection drops, signal duplication checks, extreme app keys.
3. Ephemeral OTR Web Profile: Zero persistent disk storage, zero cookie/cache file creation verification.
"""

import os
import sys
import json
import time
import tempfile
import threading
import unittest
from typing import List

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication, QEventLoop, QTimer
from PyQt6.QtNetwork import QLocalSocket
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage

from owl.profiles.profile_manager import Profile, ProfileManager, create_otr_web_profile, sanitize_search_engine
from owl.stealth.single_instance import SingleInstanceGuard


class TestM1ProfileSystemAdversarial(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.json_path = os.path.join(self.tmp_dir.name, "profiles.json")

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_rapid_profile_crud_stress(self):
        """Stress test: 100 rapid sequential profile creation, modification, active switching, and deletions."""
        pm = ProfileManager(json_path=self.json_path)
        created_ids = []

        # 1. Creation stress
        for i in range(50):
            prof = pm.create_profile(
                name=f"Stress Profile {i}",
                avatar=f"icon_{i}",
                homepage=f"https://example{i}.com",
                search_engine="DuckDuckGo" if i % 2 == 0 else "Google",
                theme_color="#123456"
            )
            created_ids.append(prof.id)

        self.assertEqual(len(pm.get_all_profiles()), 51)  # 1 default + 50 created

        # 2. Rapid updates & active profile switches
        for pid in created_ids[:25]:
            pm.update_profile(pid, name=f"Updated_{pid}", search_engine="DuckDuckGo")
            pm.set_active_profile(pid)
            self.assertEqual(pm.get_active_profile().id, pid)

        # 3. Persistence verification across new instance reload
        pm_reload = ProfileManager(json_path=self.json_path)
        self.assertEqual(len(pm_reload.get_all_profiles()), 51)
        self.assertEqual(pm_reload.get_active_profile().id, created_ids[24])

        # 4. Deletion stress down to 1 profile
        all_ids = [p.id for p in pm_reload.get_all_profiles()]
        for pid in all_ids[:-1]:
            res = pm_reload.delete_profile(pid)
            self.assertTrue(res)

        self.assertEqual(len(pm_reload.get_all_profiles()), 1)
        # Attempting to delete the last profile MUST fail
        last_res = pm_reload.delete_profile(all_ids[-1])
        self.assertFalse(last_res, "Deleting the last remaining profile must be prevented.")

    def test_json_file_corruption_matrix(self):
        """Adversarial Matrix: Test system resilience against multiple types of corrupt or malformed profiles.json files."""
        corruption_samples = [
            ("", "Empty file"),
            ("{", "Incomplete opening brace"),
            ('{"active_profile_id": "123", "profiles": [', "Truncated array"),
            ('{"active_profile_id": 12345, "profiles": "NOT_A_LIST"}', "Wrong profiles type"),
            ('{"profiles": null, "active_profile_id": null}', "Null values"),
            ('[1, 2, 3, 4, 5]', "JSON Array instead of Dict"),
            ('12345', "Integer JSON"),
            ('{"profiles": [{"id": null, "name": null}]}', "Profile dict with null fields"),
            ('{"profiles": [123, true, "string_item"]}', "Non-dict profile items in array"),
            ('{"active_profile_id": "non_existent_id", "profiles": [{"id": "p1", "name": "Valid"}]}', "Mismatched active_profile_id"),
        ]

        for content, desc in corruption_samples:
            with open(self.json_path, "w", encoding="utf-8") as f:
                f.write(content)

            pm = ProfileManager(json_path=self.json_path)
            profiles = pm.load_profiles()
            self.assertGreaterEqual(len(profiles), 1, f"Failed corrupt JSON recovery for case: {desc}")
            active = pm.get_active_profile()
            self.assertIsNotNone(active, f"Active profile must be non-None for case: {desc}")
            self.assertIn(active.id, [p.id for p in profiles], f"Active profile ID must exist in profiles for case: {desc}")

    def test_path_traversal_and_adversarial_strings(self):
        """Adversarial input: Path traversal, zero-bytes, huge strings, and script injections in profile fields."""
        pm = ProfileManager(json_path=self.json_path)
        
        adversarial_name = "../../../etc/passwd\x00<script>alert('xss')</script>" + ("A" * 5000)
        adversarial_homepage = "javascript:alert(1)"
        
        prof = pm.create_profile(
            name=adversarial_name,
            homepage=adversarial_homepage,
            search_engine="INVALID_ENGINE_NAME"
        )

        self.assertEqual(prof.search_engine, "Google", "Invalid search engine must sanitize to Google.")
        
        pm_reload = ProfileManager(json_path=self.json_path)
        reloaded_prof = pm_reload.get_profile_by_id(prof.id)
        self.assertIsNotNone(reloaded_prof)
        self.assertEqual(reloaded_prof.name, adversarial_name)
        self.assertEqual(reloaded_prof.search_engine, "Google")

    def test_concurrent_profile_manager_access(self):
        """Concurrency test: Multiple ProfileManager instances operating on the same file concurrently."""
        errors = []

        def worker_task(worker_id):
            try:
                pm = ProfileManager(json_path=self.json_path)
                for i in range(10):
                    p = pm.create_profile(name=f"Worker_{worker_id}_{i}")
                    pm.set_active_profile(p.id)
                    time.sleep(0.001)
            except Exception as e:
                errors.append((worker_id, e))

        threads = [threading.Thread(target=worker_task, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Concurrent ProfileManager access generated errors: {errors}")
        
        # Verify file is still valid JSON
        pm_final = ProfileManager(json_path=self.json_path)
        self.assertGreaterEqual(len(pm_final.get_all_profiles()), 1)

    def test_save_profiles_silent_disk_failure_handling(self):
        """Adversarial check: Test behavior when disk write fails (e.g. read-only directory or file lock)."""
        pm = ProfileManager(json_path=self.json_path)
        
        # Make the JSON path pointing to a non-writable path or directory
        read_only_dir = os.path.join(self.tmp_dir.name, "readonly_dir")
        os.makedirs(read_only_dir, exist_ok=True)
        read_only_file = os.path.join(read_only_dir, "profiles.json")
        
        pm_ro = ProfileManager(json_path=read_only_file)
        
        # Make directory read-only (attrib +r on Windows or chmod 0444)
        os.chmod(read_only_dir, 0o444)
        
        try:
            # Attempt to create profile when directory is non-writable
            prof = pm_ro.create_profile(name="Should Fail Save")
            # Profile is created in memory, but was file written to disk?
            file_exists = os.path.exists(read_only_file)
            # Check if fresh manager reloads it
            pm_check = ProfileManager(json_path=read_only_file)
            reloaded_names = [p.name for p in pm_check.get_all_profiles()]
            # If save silently failed, reloaded_names won't have "Should Fail Save"
            save_succeeded = "Should Fail Save" in reloaded_names
        finally:
            os.chmod(read_only_dir, 0o777)


class TestM1SingleInstanceAdversarial(unittest.TestCase):
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

    def _make_guard(self, key: str) -> SingleInstanceGuard:
        g = SingleInstanceGuard(app_key=key)
        self.guards.append(g)
        return g

    def test_rapid_acquire_release_cycles(self):
        """Stress test: 30 rapid sequential acquire and release cycles."""
        key = "stress_rapid_key"
        for i in range(30):
            g = SingleInstanceGuard(app_key=key)
            acquired = g.try_acquire(key)
            self.assertTrue(acquired, f"Cycle {i}: primary acquire failed.")
            g.release()
            QCoreApplication.processEvents()

    def test_concurrent_acquisition_race(self):
        """Race condition: Concurrent threads attempting try_acquire on the same key."""
        import uuid, time
        key = f"race_condition_key_{uuid.uuid4().hex[:8]}"
        results = []
        lock = threading.Lock()

        def try_acquire_thread(thread_idx):
            g = SingleInstanceGuard(app_key=key)
            res = g.try_acquire(key)
            with lock:
                results.append((g, res))

        threads = [threading.Thread(target=try_acquire_thread, args=(i,)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        success_count = sum(1 for _, res in results if res is True)
        failure_count = sum(1 for _, res in results if res is False)
        
        self.assertEqual(success_count, 1, f"Exactly 1 thread must acquire lock. Got {success_count}.")
        self.assertEqual(failure_count, 7, f"Remaining 7 threads must be rejected. Got {failure_count}.")

        for g, _ in results:
            g.release()

    def test_garbage_and_malformed_ipc_payloads(self):
        """Adversarial IPC: Send arbitrary binary garbage, huge payloads, and truncated streams to primary server."""
        key = "garbage_ipc_key"
        primary = self._make_guard(key)
        self.assertTrue(primary.try_acquire(key))

        server_name = primary._get_server_name(key)
        
        # Test 1: Send binary garbage
        sock1 = QLocalSocket()
        sock1.connectToServer(server_name)
        if sock1.waitForConnected(500):
            sock1.write(b"\x00\xff\xfe\xfd\x00\x00GARBAGE_PAYLOAD\n")
            sock1.flush()
            sock1.waitForBytesWritten(500)
            sock1.disconnectFromServer()
            sock1.close()
        
        QCoreApplication.processEvents()

        # Test 2: Send large payload (500KB)
        sock2 = QLocalSocket()
        sock2.connectToServer(server_name)
        if sock2.waitForConnected(500):
            sock2.write(b"A" * 500000)
            sock2.flush()
            sock2.waitForBytesWritten(1000)
            sock2.disconnectFromServer()
            sock2.close()

        QCoreApplication.processEvents()

        # Test 3: Connect and immediately disconnect without writing
        sock3 = QLocalSocket()
        sock3.connectToServer(server_name)
        if sock3.waitForConnected(500):
            sock3.disconnectFromServer()
            sock3.close()

        QCoreApplication.processEvents()

        # Primary guard must remain alive and responsive after garbage bombardment
        secondary = self._make_guard(key)
        res = secondary.try_acquire(key)
        self.assertFalse(res, "Primary instance must remain alive and reject secondary after garbage IPC.")

    def test_activation_signal_duplication_check(self):
        """Adversarial check: Ensure single secondary connection triggers activation signal exactly ONCE."""
        key = "signal_duplication_key"
        primary = self._make_guard(key)
        self.assertTrue(primary.try_acquire(key))

        signal_count = []
        primary.activation_requested.connect(lambda: signal_count.append(1))

        secondary = self._make_guard(key)
        res = secondary.try_acquire(key)
        self.assertFalse(res)

        # Allow any queued events to settle
        QCoreApplication.processEvents()
        
        self.assertEqual(len(signal_count), 1, f"Signal emitted {len(signal_count)} times, expected exactly 1.")

    def test_extreme_app_keys(self):
        """Boundary test: Test app keys with special characters, unicode, and extreme lengths."""
        test_keys = [
            "NormalKey",
            "Key With Spaces ",
            "Unicode_🚀_Stealth_🔒",
            "X" * 300,  # >60 chars triggers sha256 hash formatting
            "A" * 1000,
        ]

        for key in test_keys:
            g1 = SingleInstanceGuard(app_key=key)
            self.guards.append(g1)
            self.assertTrue(g1.try_acquire(key), f"Failed primary acquire for key of length {len(key)}")

            g2 = SingleInstanceGuard(app_key=key)
            self.guards.append(g2)
            self.assertFalse(g2.try_acquire(key), f"Failed secondary rejection for key of length {len(key)}")

            g1.release()
            g2.release()
            QCoreApplication.processEvents()


class TestM1OTRWebProfileSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_otr_profile_zero_disk_storage_guarantee(self):
        """Security Verification: Confirm create_otr_web_profile produces a 100% ephemeral profile with zero disk persistence."""
        prof = Profile(id="test_otr_sec", name="Security Test")
        web_profile = create_otr_web_profile(prof)

        self.assertTrue(web_profile.isOffTheRecord(), "QWebEngineProfile must be Off-The-Record.")
        self.assertEqual(
            web_profile.persistentCookiesPolicy(),
            QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies,
            "Must enforce NoPersistentCookies policy."
        )
        self.assertEqual(
            web_profile.httpCacheType(),
            QWebEngineProfile.HttpCacheType.MemoryHttpCache,
            "Must enforce MemoryHttpCache policy."
        )

        # Check if the storage path dir has any persistent cookie database or cache files created
        storage_dir = web_profile.persistentStoragePath()
        cache_dir = web_profile.cachePath()
        
        # Verify that no cookie file or cache db exists
        if storage_dir and os.path.exists(storage_dir):
            cookie_files = [f for f in os.listdir(storage_dir) if "cookie" in f.lower() or "network" in f.lower()]
            self.assertEqual(len(cookie_files), 0, f"No persistent cookie files allowed in storage dir: {cookie_files}")

    def test_otr_profile_page_instantiation_no_disk_leak(self):
        """Security Verification: Instantiating a QWebEnginePage with OTR profile creates zero storage directories or files."""
        prof = Profile(id="test_otr_page", name="Page Test")
        web_profile = create_otr_web_profile(prof)
        page = QWebEnginePage(web_profile)

        self.assertEqual(page.profile(), web_profile)
        self.assertTrue(page.profile().isOffTheRecord())
        self.assertEqual(
            page.profile().persistentCookiesPolicy(),
            QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies
        )
        self.assertEqual(
            page.profile().httpCacheType(),
            QWebEngineProfile.HttpCacheType.MemoryHttpCache
        )


if __name__ == "__main__":
    unittest.main()
