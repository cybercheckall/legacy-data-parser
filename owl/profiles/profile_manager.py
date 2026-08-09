"""
profile_manager.py - Data model, JSON persistence, and off-the-record profile creation for Phantom Workspace.

Manages browser profiles:
- Data model Profile (id, name, avatar, homepage, search_engine, theme_color)
- ProfileManager (JSON loading/saving with atomic replace, default profile auto-creation,
  validation of search_engine, CRUD operations)
- create_otr_web_profile (creates QWebEngineProfile with off-the-record settings)
"""

import json
import logging
import os
import threading
import time
import urllib.parse
import uuid
from dataclasses import asdict, dataclass
from typing import List, Optional

from PyQt6.QtCore import QObject
from PyQt6.QtWebEngineCore import QWebEngineProfile

logger = logging.getLogger(__name__)

VALID_SEARCH_ENGINES = ("Google", "DuckDuckGo")
SEARCH_ENGINE_URLS = {
    "Google": "https://www.google.com/search?q={}",
    "DuckDuckGo": "https://duckduckgo.com/?q={}",
}


def sanitize_search_engine(engine: Optional[str]) -> str:
    """Ensure search engine is valid ('Google' or 'DuckDuckGo'), defaulting to 'Google'."""
    if engine in VALID_SEARCH_ENGINES:
        return engine
    return "Google"


@dataclass
class Profile:
    id: str
    name: str
    avatar: str = "ghost"
    homepage: str = "https://www.google.com"
    search_engine: str = "Google"
    theme_color: str = "#533483"

    def __post_init__(self):
        self.search_engine = sanitize_search_engine(self.search_engine)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "Guest mode"),
            avatar=data.get("avatar", "👤"),
            homepage=data.get("homepage", "https://www.google.com"),
            search_engine=sanitize_search_engine(data.get("search_engine", "Google")),
            theme_color=data.get("theme_color", "#533483"),
        )

    def get_search_url(self, query: str) -> str:
        engine = sanitize_search_engine(self.search_engine)
        template = SEARCH_ENGINE_URLS.get(engine, SEARCH_ENGINE_URLS["Google"])
        return template.format(urllib.parse.quote_plus(query))


class ProfileManager:
    """
    Manages loading, saving, CRUD operations, and active profile selection for browser profiles.
    Persists data atomically to profiles.json.
    """

    _file_lock = threading.Lock()

    def __init__(self, json_path: Optional[str] = None, storage_path: Optional[str] = None):
        path = json_path or storage_path
        if path is None:
            from owl.paths import PROFILES_JSON
            path = PROFILES_JSON
        self.json_path = path
        self.storage_path = path
        self.profiles: List[Profile] = []
        self.active_profile_id: Optional[str] = None
        self.load_profiles()

    def _create_defaults(self) -> List[Profile]:
        guest_prof = Profile(
            id="guest",
            name="Guest mode",
            avatar="👤",
            homepage="https://www.google.com",
            search_engine="Google",
            theme_color="#533483",
        )
        self.profiles = [guest_prof]
        self.active_profile_id = guest_prof.id
        self.save_profiles()
        return self.profiles

    def load_profiles(self) -> List[Profile]:
        """Load profiles from JSON file. Auto-creates defaults if missing or corrupt."""
        if not os.path.exists(self.json_path):
            logger.info("profiles.json not found at %s. Initializing defaults.", self.json_path)
            return self._create_defaults()

        try:
            with ProfileManager._file_lock:
                with open(self.json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

            if not isinstance(data, dict):
                raise ValueError("JSON data must be a dictionary.")

            raw_profiles = data.get("profiles", [])
            if not isinstance(raw_profiles, list) or len(raw_profiles) == 0:
                return self._create_defaults()

            self.profiles = [Profile.from_dict(p) for p in raw_profiles]
            self.active_profile_id = data.get("active_profile_id")

            # Validate active profile ID
            if not self.active_profile_id or not any(p.id == self.active_profile_id for p in self.profiles):
                self.active_profile_id = self.profiles[0].id
                self.save_profiles()

        except Exception as e:
            logger.error("Failed to load profiles from %s: %s. Falling back to defaults.", self.json_path, e)
            return self._create_defaults()

        return self.profiles

    def save_profiles(self) -> bool:
        """Save profiles to JSON file using atomic replace via temporary file. Returns True on success, False on error."""
        data = {
            "active_profile_id": self.active_profile_id,
            "profiles": [p.to_dict() for p in self.profiles],
        }
        dir_name = os.path.dirname(self.json_path)
        if dir_name and not os.path.exists(dir_name):
            try:
                os.makedirs(dir_name, exist_ok=True)
            except Exception as e:
                logger.error("Failed to create directory %s: %s", dir_name, e)
                return False

        tmp_path = f"{self.json_path}.{uuid.uuid4().hex}.tmp"
        with ProfileManager._file_lock:
            for attempt in range(5):
                try:
                    with open(tmp_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    os.replace(tmp_path, self.json_path)
                    logger.info("Profiles saved atomically to %s", self.json_path)
                    return True
                except Exception as e:
                    if os.path.exists(tmp_path):
                        try:
                            os.remove(tmp_path)
                        except Exception:
                            pass
                    if attempt < 4:
                        time.sleep(0.01)
                    else:
                        logger.error("Failed to save profiles atomically: %s", e)
                        return False
        return False

    def get_all_profiles(self) -> List[Profile]:
        return list(self.profiles)

    def get_profile_by_id(self, profile_id: str) -> Optional[Profile]:
        for p in self.profiles:
            if p.id == profile_id:
                return p
        return None

    def get_active_profile(self) -> Profile:
        if self.active_profile_id:
            p = self.get_profile_by_id(self.active_profile_id)
            if p:
                return p
        if self.profiles:
            self.active_profile_id = self.profiles[0].id
            return self.profiles[0]
        defaults = self._create_defaults()
        return defaults[0]

    def set_active_profile(self, profile_id: str) -> bool:
        if self.get_profile_by_id(profile_id):
            old_active_id = self.active_profile_id
            self.active_profile_id = profile_id
            if not self.save_profiles():
                self.active_profile_id = old_active_id
                return False
            return True
        return False

    def create_profile(
        self,
        name: str,
        avatar: str = "ghost",
        homepage: str = "https://www.google.com",
        search_engine: str = "Google",
        theme_color: str = "#533483",
    ) -> Optional[Profile]:
        valid_engine = sanitize_search_engine(search_engine)
        prof = Profile(
            id=str(uuid.uuid4()),
            name=name,
            avatar=avatar,
            homepage=homepage,
            search_engine=valid_engine,
            theme_color=theme_color,
        )
        self.profiles.append(prof)
        if not self.save_profiles():
            self.profiles.remove(prof)
            return None
        return prof

    def update_profile(self, profile_id: str, **kwargs) -> Optional[Profile]:
        prof = self.get_profile_by_id(profile_id)
        if not prof:
            return None
        old_attrs = {key: getattr(prof, key) for key in kwargs if hasattr(prof, key)}
        if "search_engine" in kwargs:
            kwargs["search_engine"] = sanitize_search_engine(kwargs["search_engine"])
        for key, val in kwargs.items():
            if hasattr(prof, key):
                setattr(prof, key, val)
        if not self.save_profiles():
            for key, val in old_attrs.items():
                setattr(prof, key, val)
            return None
        return prof

    def delete_profile(self, profile_id: str) -> bool:
        if len(self.profiles) <= 1:
            logger.warning("Prevented deletion of the last remaining profile.")
            return False

        prof = self.get_profile_by_id(profile_id)
        if not prof:
            return False

        idx = self.profiles.index(prof)
        old_active_id = self.active_profile_id

        self.profiles.remove(prof)
        if self.active_profile_id == profile_id:
            self.active_profile_id = self.profiles[0].id

        if not self.save_profiles():
            self.profiles.insert(idx, prof)
            self.active_profile_id = old_active_id
            return False
        return True


def create_otr_web_profile(profile: Optional[Profile] = None, parent: Optional[QObject] = None) -> QWebEngineProfile:
    """
    Creates an Off-The-Record (OTR) QWebEngineProfile instance configured for zero disk storage.
    """
    web_profile = QWebEngineProfile(parent)
    web_profile.setPersistentCookiesPolicy(
        QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies
    )
    web_profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
    web_profile.setPersistentStoragePath("")
    web_profile.setCachePath("")
    return web_profile
