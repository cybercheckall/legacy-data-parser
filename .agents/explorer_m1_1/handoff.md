# Handoff Report: Milestone 1 — Profile System Specifications & Implementation Plan

## 1. Observation
- **Qt Binding**: PyQt6 (`PyQt6.QtCore`, `PyQt6.QtWidgets`, `PyQt6.QtWebEngineCore`, `PyQt6.QtWebEngineWidgets`).
  - Citing `main.py` lines 32-33: `from PyQt6.QtWidgets import QApplication`
  - Citing `browser.py` lines 18-19: `from PyQt6.QtWebEngineWidgets import QWebEngineView`, `from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile`
  - Confirmed via runtime execution: `PyQt6 version 6.11.0` with `Qt runtime 6.11.1`.
- **Directory Layout & Existing Code**:
  - `main.py`: Main application launcher using `QApplication` and `GlobalHotkey`.
  - `browser.py`: `PhantomBrowser(QMainWindow)` and `WebTab(QWebEngineView)`. Currently uses `QWebEngineProfile.defaultProfile()` with `ForcePersistentCookies` enabled and hardcoded `HOME_URL = "https://www.google.com"`.
  - `display_affinity.py`: Win32 `SetWindowDisplayAffinity(WDA_EXCLUDEFROMCAPTURE)` implementation.
  - `hotkey.py`: `pynput` global `Ctrl+Shift+B` hotkey listener.
  - `tests/`: Contains test suites (`conftest.py`, `test_browser_features.py`, `test_e2e.py`, etc.).
  - Currently **no** `profile_manager.py` or `profiles.json` exists in the repository.
- **QtWebEngine Off-The-Record (OTR) Verification**:
  - Executed runtime test command:
    `python -c "import sys; from PyQt6.QtWidgets import QApplication; app = QApplication(sys.argv); from PyQt6.QtWebEngineCore import QWebEngineProfile; p = QWebEngineProfile(); p.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies); p.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache); print('isOTR:', p.isOffTheRecord(), 'cookiesPolicy:', p.persistentCookiesPolicy(), 'cacheType:', p.httpCacheType())"`
  - Output: `isOTR: True cookiesPolicy: PersistentCookiesPolicy.NoPersistentCookies cacheType: HttpCacheType.MemoryHttpCache`

---

## 2. Logic Chain
1. **Existing Gap**: `browser.py` lines 72-76 currently initialize a shared persistent profile (`QWebEngineProfile.defaultProfile()` with `ForcePersistentCookies`). To satisfy R2 & M1 requirements, the browser requires a standalone `profile_manager.py` module that models profiles, persists user preferences in `profiles.json`, and yields ephemeral zero-disk-storage `QWebEngineProfile` instances.
2. **Profile Data Model**:
   - Fields required by R2/PROJECT.md:
     - `id`: `str` (UUID v4 string for unique identification).
     - `name`: `str` (User display name, e.g., "Default", "Work", "Private").
     - `avatar`: `str` (Icon/Avatar identifier string, e.g., "ghost", "user", "shield", "rocket", "briefcase").
     - `homepage`: `str` (Default homepage URL, e.g., "https://www.google.com").
     - `search_engine`: `str` ("Google" | "DuckDuckGo").
     - `theme_color`: `str` (Hex accent color code, e.g., "#533483").
   - Convenience helpers: `to_dict()`, `from_dict()`, and `get_search_url(query: str) -> str`.
3. **Storage & Schema (`profiles.json`)**:
   - Location: Configurable storage path, defaulting to `profiles.json` in the root application directory (`os.path.join(os.path.dirname(__file__), "profiles.json")`).
   - JSON Schema:
     ```json
     {
       "active_profile_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
       "profiles": [
         {
           "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
           "name": "Default Profile",
           "avatar": "ghost",
           "homepage": "https://www.google.com",
           "search_engine": "Google",
           "theme_color": "#533483"
         }
       ]
     }
     ```
   - Default Auto-Creation: If `profiles.json` does not exist or contains invalid JSON, `ProfileManager` automatically creates a default profile and writes the initial `profiles.json`.
4. **CRUD Logic (`ProfileManager`)**:
   - `load_profiles()`: Loads and parses `profiles.json`.
   - `save_profiles()`: Performs atomic file write (writes to `.tmp` file then renames) to prevent file corruption.
   - `get_all_profiles() -> List[Profile]`
   - `get_profile_by_id(profile_id: str) -> Optional[Profile]`
   - `get_active_profile() -> Profile`
   - `set_active_profile(profile_id: str) -> bool`
   - `create_profile(name, avatar, homepage, search_engine, theme_color) -> Profile`
   - `update_profile(profile_id, **kwargs) -> Optional[Profile]`
   - `delete_profile(profile_id: str) -> bool` (Ensures active profile switches if deleted, and rejects deleting the last remaining profile).
5. **Ephemeral OTR Web Profile Generator**:
   - Factory function: `create_otr_web_profile(profile: Profile, parent: QObject = None) -> QWebEngineProfile`
   - Instantiates `p = QWebEngineProfile(parent)`. In PyQt6, instantiating an unnamed `QWebEngineProfile` automatically makes it an off-the-record profile (`isOffTheRecord()` evaluates to `True`).
   - Enforces zero persistent storage:
     - `p.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)`
     - `p.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)`
     - `p.setPersistentStoragePath("")`
     - `p.setCachePath("")`
   - Asserts `p.isOffTheRecord() is True` before returning.

---

## 3. Caveats
- **Qt Application Dependency**: `QWebEngineProfile` requires an active `QApplication` instance to be initialized before instantiation. In headless unit tests, `QApplication` must be created or provided via `pytest-qt` fixtures.
- **Storage Path Parameterization**: `ProfileManager` must accept an optional `storage_path` argument in `__init__` so unit tests can pass a temporary file path (`tmp_path / "profiles.json"`) to avoid polluting the workspace.
- **Avatar Identifiers**: Using string keys ("ghost", "user", "shield", etc.) for avatar representation allows loose coupling with M2 UI components (`profile_selector.py`).

---

## 4. Conclusion & Proposed Implementation Specification for `profile_manager.py`

### Proposed Code Structure (`profile_manager.py`):

```python
"""
Profile Manager module for Phantom Workspace.

Handles Profile data model, JSON persistence in profiles.json,
CRUD operations, and ephemeral Off-The-Record (OTR) QWebEngineProfile generation.
"""
import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass
from typing import List, Optional

from PyQt6.QtCore import QObject
from PyQt6.QtWebEngineCore import QWebEngineProfile

logger = logging.getLogger(__name__)

SEARCH_ENGINES = {
    "Google": "https://www.google.com/search?q={}",
    "DuckDuckGo": "https://duckduckgo.com/?q={}",
}


@dataclass
class Profile:
    id: str
    name: str
    avatar: str = "ghost"
    homepage: str = "https://www.google.com"
    search_engine: str = "Google"
    theme_color: str = "#533483"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "Default Profile"),
            avatar=data.get("avatar", "ghost"),
            homepage=data.get("homepage", "https://www.google.com"),
            search_engine=data.get("search_engine", "Google"),
            theme_color=data.get("theme_color", "#533483"),
        )

    def get_search_url(self, query: str) -> str:
        template = SEARCH_ENGINES.get(self.search_engine, SEARCH_ENGINES["Google"])
        import urllib.parse
        return template.format(urllib.parse.quote(query))


class ProfileManager:
    """Manages profile loading, saving, active profile selection, and CRUD operations."""

    def __init__(self, storage_path: Optional[str] = None):
        if storage_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            storage_path = os.path.join(base_dir, "profiles.json")
        self.storage_path = storage_path
        self.profiles: List[Profile] = []
        self.active_profile_id: Optional[str] = None
        self.load_profiles()

    def _create_default_profile(() -> Profile:
        default_p = Profile(
            id=str(uuid.uuid4()),
            name="Default Profile",
            avatar="ghost",
            homepage="https://www.google.com",
            search_engine="Google",
            theme_color="#533483",
        )
        return default_p

    def load_profiles(self) -> List[Profile]:
        if not os.path.exists(self.storage_path):
            logger.info("profiles.json not found. Initializing default profile.")
            default_p = self._create_default_profile()
            self.profiles = [default_p]
            self.active_profile_id = default_p.id
            self.save_profiles()
            return self.profiles

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            raw_profiles = data.get("profiles", [])
            self.profiles = [Profile.from_dict(p) for p in raw_profiles]
            self.active_profile_id = data.get("active_profile_id")

            if not self.profiles:
                default_p = self._create_default_profile()
                self.profiles = [default_p]
                self.active_profile_id = default_p.id
                self.save_profiles()
            elif not self.active_profile_id or not self.get_profile_by_id(self.active_profile_id):
                self.active_profile_id = self.profiles[0].id
                self.save_profiles()

        except Exception as e:
            logger.error("Failed to load profiles.json (%s). Re-initializing defaults.", e)
            default_p = self._create_default_profile()
            self.profiles = [default_p]
            self.active_profile_id = default_p.id
            self.save_profiles()

        return self.profiles

    def save_profiles((self) -> None:
        data = {
            "active_profile_id": self.active_profile_id,
            "profiles": [p.to_dict() for p in self.profiles],
        }
        temp_path = self.storage_path + ".tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(temp_path, self.storage_path)
            logger.info("Profiles saved successfully to %s", self.storage_path)
        except Exception as e:
            logger.error("Failed to save profiles: %s", e)
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def get_all_profiles(self) -> List[Profile]:
        return list(self.profiles)

    def get_profile_by_id(self, profile_id: str) -> Optional[Profile]:
        for p in self.profiles:
            if p.id == profile_id:
                return p
        return None

    def get_active_profile(self) -> Profile:
        p = self.get_profile_by_id(self.active_profile_id)
        if p:
            return p
        if self.profiles:
            self.active_profile_id = self.profiles[0].id
            return self.profiles[0]
        default_p = self._create_default_profile()
        self.profiles = [default_p]
        self.active_profile_id = default_p.id
        self.save_profiles()
        return default_p

    def set_active_profile(self, profile_id: str) -> bool:
        if self.get_profile_by_id(profile_id):
            self.active_profile_id = profile_id
            self.save_profiles()
            return True
        return False

    def create_profile(
        self,
        name: str,
        avatar: str = "ghost",
        homepage: str = "https://www.google.com",
        search_engine: str = "Google",
        theme_color: str = "#533483",
    ) -> Profile:
        new_p = Profile(
            id=str(uuid.uuid4()),
            name=name,
            avatar=avatar,
            homepage=homepage,
            search_engine=search_engine,
            theme_color=theme_color,
        )
        self.profiles.append(new_p)
        self.save_profiles()
        return new_p

    def update_profile(self, profile_id: str, **kwargs) -> Optional[Profile]:
        p = self.get_profile_by_id(profile_id)
        if not p:
            return None
        for key, val in kwargs.items():
            if hasattr(p, key):
                setattr(p, key, val)
        self.save_profiles()
        return p

    def delete_profile(self, profile_id: str) -> bool:
        if len(self.profiles) <= 1:
            logger.warning("Cannot delete the last remaining profile.")
            return False
        
        p = self.get_profile_by_id(profile_id)
        if not p:
            return False

        self.profiles.remove(p)
        if self.active_profile_id == profile_id:
            self.active_profile_id = self.profiles[0].id

        self.save_profiles()
        return True


def create_otr_web_profile(profile: Profile, parent: Optional[QObject] = None) -> QWebEngineProfile:
    """
    Generates an off-the-record (OTR) QWebEngineProfile instance configured
    to persist zero cookies, history, or disk cache.
    """
    web_profile = QWebEngineProfile(parent)
    web_profile.setPersistentCookiesPolicy(
        QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies
    )
    web_profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
    web_profile.setPersistentStoragePath("")
    web_profile.setCachePath("")
    assert web_profile.isOffTheRecord(), "QWebEngineProfile must be off-the-record!"
    return web_profile
```

---

## 5. Verification Method
- **Unit Test Suite**: Create `tests/test_profile_manager.py`.
- **Verification Commands**:
  1. `pytest tests/test_profile_manager.py`
  2. Verify:
     - Profile creation, modification, deletion, and active profile switching.
     - `profiles.json` persistence and corruption recovery.
     - `create_otr_web_profile(profile)` produces a profile where `isOffTheRecord() == True`, `persistentCookiesPolicy() == NoPersistentCookies`, and `httpCacheType() == MemoryHttpCache`.
