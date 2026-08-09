"""Resolved filesystem paths for assets and local data."""

from __future__ import annotations

import os

_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(_PACKAGE_DIR, ".."))
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
BRAND_DIR = os.path.join(ASSETS_DIR, "brand")
DEFAULTS_DIR = os.path.join(ASSETS_DIR, "defaults")
PROFILES_JSON = os.path.join(PROJECT_ROOT, "profiles.json")
PROFILES_EXAMPLE = os.path.join(DEFAULTS_DIR, "profiles.example.json")
