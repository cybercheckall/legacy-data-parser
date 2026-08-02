# TEST_INFRA.md - Test Infrastructure & Runner Architecture

## Overview
The Stealth Chromium Browser testing infrastructure provides an opaque-box E2E test harness designed to validate all functional, boundary, cross-feature, and packaging requirements headlessly across Windows platforms.

## Architecture
- **Framework**: `pytest` + `unittest` + `pytest-qt` + `PyQt6`
- **Headless Execution**: Configured via `QT_QPA_PLATFORM=offscreen` in `tests/conftest.py`.
- **Location**: `tests/`

## Test Hierarchy (Tiers 1–4)

| Tier | Focus Area | Files Covered | Key Test Cases |
|------|------------|---------------|----------------|
| **Tier 1** | Feature Coverage | `test_stealth_affinity.py`, `test_browser_features.py` | PyQt6 MainWindow creation, `QWebEngineView` initialization & settings, `SetWindowDisplayAffinity` (WDA=0x11), URL navigation, tab open/close, default bookmarks bar. |
| **Tier 2** | Boundary & Corner Cases | `test_stealth_affinity.py`, `test_browser_features.py` | Empty URL navigation, invalid URL scheme, 10-tab rapid creation/closure stress test, `Esc` key window hide behavior, `Qt.WindowType.Tool` & `Qt.WindowType.WindowStaysOnTopHint` flags. |
| **Tier 3** | Cross-Feature Combinations | `test_hotkey.py` | Global hotkey `Ctrl+Shift+B` registration, toggle visibility state transitions (visible -> hidden -> visible), key shortcuts (`Ctrl+L`, `Ctrl+T`, `Ctrl+W`, `Esc`). |
| **Tier 4** | Real-World Workloads & Packaging | `test_e2e.py` | Full browser lifecycle (launch, navigate, multi-tab, Esc hide, teardown), Desktop logger initialization & log file verification (`~/Desktop/stealth_browser.log`), PyInstaller standalone executable verification. |

## Execution Instructions

### Running the Complete Suite Headlessly
```powershell
set QT_QPA_PLATFORM=offscreen
pytest tests/ -v
```

### Running Specific Test Modules
```powershell
pytest tests/test_stealth_affinity.py -v
pytest tests/test_browser_features.py -v
pytest tests/test_hotkey.py -v
pytest tests/test_e2e.py -v
```

## Environment Requirements
- Python 3.12+
- `PyQt6` & `PyQt6-WebEngine`
- `pytest` & `pytest-qt`
