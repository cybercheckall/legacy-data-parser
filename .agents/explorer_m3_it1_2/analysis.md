# Feature 7 Technical Strategy: Modern Settings Page & Search Engine Switcher

**Module**: `settings_view.py`  
**Milestone**: Milestone 3 (AI Side Panel & Settings System), Iteration 1  
**Author**: Explorer 2  
**Target Project Directory**: `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser`

---

## 1. Executive Summary & Problem Scope

Feature 7 requires implementing a **Modern Settings Page** (`SettingsView`) with a 2026 dark glassmorphic sidebar layout for Phantom Workspace. The settings page allows users to:
1. **Switch default search engine**: Toggle/select between **Google** (`https://www.google.com/search?q=`) and **DuckDuckGo** (`https://duckduckgo.com/?q=`), emitting `search_engine_changed(str)` signals and dynamically updating URL bar query formulation.
2. **Profile Management**: View active profile details, edit profile parameters (name, avatar, homepage, search engine), create new profiles, and delete existing profiles cleanly via integration with `ProfileManager`. Emits `profile_updated()`.
3. **Appearance**: Dark mode default toggle, theme color highlights/accents preview.
4. **About Section**: Display browser version info ("Phantom Workspace v2.0 Stealth Edition") and stealth capabilities summary (`SetWindowDisplayAffinity`, zero-cookie OTR storage, single-instance IPC, global `Ctrl+Shift+B` hotkey).
5. **General Section**: Homepage URL preference input, scheme auto-prefixing (`https://`), startup behavior options. Emits `homepage_changed(str)`.
6. **In-Browser Routing**: Triggered via toolbar gear icon (`nav_bar.py` -> `settings_requested`) or URL navigation to `phantom://settings` / `chrome://settings`, rendering as an internal tab in `PhantomBrowser`.

---

## 2. Component Architecture & Detailed Design

### 2.1 `SettingsView` (`settings_view.py`)
`SettingsView` will inherit from `QWidget` and use a two-column responsive glassmorphic layout:
- **Left Column**: Sidebar navigation widget with vertical layout containing navigation buttons (`btn_general`, `btn_profiles`, `btn_search`, `btn_appearance`, `btn_about`) matching `test_settings.py` requirements.
- **Right Column**: A `QStackedWidget` (`self.stack`) hosting 5 section pages.

```
+-----------------------------------------------------------------------------------+
|  SettingsView (QWidget)                                                           |
| +-------------------------+ +---------------------------------------------------+ |
| | Sidebar (QVBoxLayout)   | | QStackedWidget (self.stack)                         | |
| |                         | |                                                   | |
| | [⚙ General]            | | [Page 0: General Settings]                          | |
| |   (self.btn_general)    | |  - Homepage URL QLineEdit                           | |
| |                         | |  - Startup behavior radios                      | |
| | [👤 Profiles]           | |                                                   | |
| |   (self.btn_profiles)   | | [Page 1: Profile Management]                        | |
| |                         | |  - Active Profile Card & Edit Form                | |
| | [🔍 Search Engine]      | |  - Profile List / Switcher / Create / Delete      | |
| |   (self.btn_search)     | |                                                   | |
| |                         | | [Page 2: Search Engine]                           | |
| | [🎨 Appearance]         | |  - Radio / Combo: Google vs DuckDuckGo            | |
| |   (self.btn_appearance) | |  - Search URL template preview                     | |
| |                         | |                                                   | |
| | [ℹ About]               | | [Page 3: Appearance]                              | |
| |   (self.btn_about)      | |  - Dark mode default toggle                       | |
| |                         | |  - Theme accent highlights                        | |
| |                         | |                                                   | |
| |                         | | [Page 4: About]                                   | |
| |                         | |  - App Version & Stealth Features Summary         | |
| +-------------------------+ +---------------------------------------------------+ |
+-----------------------------------------------------------------------------------+
```

### 2.2 Class Interface Specification (`settings_view.py`)

```python
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QStackedWidget, QLineEdit, QComboBox, QRadioButton,
    QButtonGroup, QScrollArea, QFrame, QMessageBox, QCheckBox
)
from profile_manager import ProfileManager, Profile, VALID_SEARCH_ENGINES

class SettingsView(QWidget):
    """
    Modern Sidebar Settings Page matching Phantom Workspace dark glassmorphism styling.
    
    Signals:
        search_engine_changed(str): Emitted when active search engine selection changes ("Google" | "DuckDuckGo").
        profile_updated(): Emitted when profile CRUD operations modify profile state.
        homepage_changed(str): Emitted when active profile homepage URL changes.
    """
    search_engine_changed = pyqtSignal(str)
    profile_updated = pyqtSignal()
    homepage_changed = pyqtSignal(str)

    def __init__(self, profile_manager: ProfileManager, parent=None):
        super().__init__(parent)
        self.profile_manager = profile_manager
        self.setObjectName("SettingsView")
        self._init_ui()
        self._load_current_settings()

    def set_search_engine(self, engine: str):
        """
        Programmatically set active search engine.
        Validates engine against ('Google', 'DuckDuckGo'), defaulting to 'Google'.
        Updates ProfileManager, UI controls, and emits search_engine_changed signal.
        """
        valid = engine if engine in VALID_SEARCH_ENGINES else "Google"
        active_prof = self.profile_manager.get_active_profile()
        if active_prof:
            self.profile_manager.update_profile(active_prof.id, search_engine=valid)
        self._update_search_ui_state(valid)
        self.search_engine_changed.emit(valid)

    def set_homepage(self, url: str):
        """
        Programmatically set active homepage.
        Auto-prepends https:// scheme if missing.
        Updates ProfileManager, UI controls, and emits homepage_changed signal.
        """
        cleaned = url.strip()
        if cleaned and not cleaned.startswith(("http://", "https://", "file://", "about:", "phantom://")):
            cleaned = "https://" + cleaned
        active_prof = self.profile_manager.get_active_profile()
        if active_prof:
            self.profile_manager.update_profile(active_prof.id, homepage=cleaned)
        if hasattr(self, "homepage_input"):
            self.homepage_input.setText(cleaned)
        self.homepage_changed.emit(cleaned)
```

---

## 3. Section Specifications & Integration Strategy

### 3.1 Search Engine Section (`btn_search`)
- **Controls**: Radio buttons / Combo box allowing selection between `"Google"` and `"DuckDuckGo"`.
- **Formatting Logic**:
  - Google URL: `https://www.google.com/search?q={query}`
  - DuckDuckGo URL: `https://duckduckgo.com/?q={query}`
- **Integration**:
  - Selection change invokes `self.set_search_engine(selected_engine)`.
  - In `PhantomBrowser`, catching `search_engine_changed(engine)` updates `_active_profile` and sets URL bar placeholder text to `f"Search with {engine} or enter URL..."`.

### 3.2 Profile Management Section (`btn_profiles`)
- **Active Profile Editing**:
  - Name (`QLineEdit`), Avatar (`QLineEdit` / preset picker), Homepage (`QLineEdit`), Search Engine (`QComboBox`).
  - "Save Profile" updates `ProfileManager` and emits `profile_updated`.
- **Profile List & Switcher**:
  - Cards / items for all profiles in `self.profile_manager.get_all_profiles()`.
  - "Switch Profile" activates target profile ID via `self.profile_manager.set_active_profile(pid)` and emits `profile_updated`.
- **New Profile Creation**:
  - Form fields for creating a new profile (`name`, `avatar`, `homepage`, `search_engine`, `theme_color`).
  - Calls `self.profile_manager.create_profile(...)` and emits `profile_updated`.
- **Profile Deletion**:
  - "Delete Profile" button calling `self.profile_manager.delete_profile(pid)`.
  - Prevents deletion if `len(profiles) <= 1` (returns `False` with log/warning). Emits `profile_updated`.

### 3.3 General Section (`btn_general`)
- **Homepage Field**: `self.homepage_input` (`QLineEdit`). Clicking Save or pressing Return triggers `set_homepage(input_text)`.
- **Startup Options**: Radio buttons ("Show Profile Selector on Launch" vs "Open Homepage").

### 3.4 Appearance Section (`btn_appearance`)
- **Dark Theme Option**: `QCheckBox` ("Enable Glassmorphic Dark Theme", checked by default).
- **Theme Color Highlight**: Preset selection chips (`#6366f1` Indigo, `#533483` Purple, `#0d9488` Teal, `#1e293b` Dark Slate).

### 3.5 About Section (`btn_about`)
- **Application Info**: `Phantom Workspace v2.0 (Stealth Edition)`.
- **Stealth Capabilities Grid**:
  1. 🛡️ **Screen Capture Protection**: `SetWindowDisplayAffinity` (`WDA_EXCLUDEFROMCAPTURE`).
  2. 🍪 **Zero Storage Footprint**: Ephemeral off-the-record `QWebEngineProfile` with memory-only cache and zero persistent cookies.
  3. 🔒 **Single-Instance Enforcement**: `QLocalServer` / `QLocalSocket` IPC.
  4. 📌 **Always-on-Top & Tool Window**: Frameless design with stealth tool flags.
  5. ⌨ **Global Hotkey**: `Ctrl+Shift+B` toggle.

---

## 4. Settings Triggering & In-Browser Routing (`browser.py` & `nav_bar.py`)

1. **Toolbar Gear Icon**:
   - `NavBar.settings_btn` ("⚙") is connected to `settings_requested`.
   - `PhantomBrowser` connects `self.nav_bar.settings_requested.connect(self._open_settings)`.

2. **`phantom://settings` Internal URL Interception**:
   - In `PhantomBrowser._navigate_from_input(text)`:
     - Check if `text.strip().lower() in ("phantom://settings", "chrome://settings", "about:settings", "settings")`.
     - If matched, execute `self._open_settings()` and set URL bar text to `phantom://settings`.

3. **Tab Manager Integration (`PhantomBrowser._open_settings`)**:
   - Iterates through existing tabs in `self.tab_widget`. If a tab with `SettingsView` already exists, switches active tab to that index (`self.tab_widget.setCurrentIndex(idx)`).
   - Otherwise, instantiates `SettingsView(self._profile_manager, parent=self)`, connects its signals (`search_engine_changed`, `profile_updated`, `homepage_changed`), and adds it to `self.tab_widget.addTab(settings_view, "⚙ Settings")`. Sets URL bar text to `phantom://settings`.

---

## 5. Search Engine Formulation Logic (`browser.py`)

When the user enters a search query in `nav_bar.py`'s `url_bar`:
```python
def _navigate_from_input(self, text: str):
    cleaned = text.strip()
    if not cleaned:
        return
    cleaned_lower = cleaned.lower()
    explicit_schemes = ("http://", "https://", "file://", "about:", "chrome://", "phantom://", "ftp://", "data:")

    if cleaned_lower in ("phantom://settings", "chrome://settings", "about:settings", "settings"):
        self._open_settings()
        return

    if cleaned_lower.startswith(explicit_schemes):
        url_str = cleaned
    elif (cleaned_lower.startswith("localhost") or cleaned_lower.startswith("127.0.0.1")) and " " not in cleaned:
        url_str = "http://" + cleaned
    elif "." in cleaned and " " not in cleaned:
        url_str = "https://" + cleaned
    else:
        # Use active profile's configured search engine
        if hasattr(self, "_active_profile") and hasattr(self._active_profile, "get_search_url"):
            url_str = self._active_profile.get_search_url(cleaned)
        else:
            import urllib.parse
            url_str = f"https://www.google.com/search?q={urllib.parse.quote_plus(cleaned)}"

    self._navigate(url_str)
```

---

## 6. Stylesheet Additions (`styles.py`)

```css
/* Settings Page Styling */
#SettingsView {
    background-color: #0a0a1a;
}

#SettingsSidebar {
    background-color: rgba(15, 23, 42, 0.90);
    border-right: 1px solid rgba(255, 255, 255, 0.08);
    min-width: 200px;
    max-width: 220px;
}

.SettingsNavBtn {
    background-color: transparent;
    color: #94a3b8;
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 13px;
    font-weight: 500;
    text-align: left;
}

.SettingsNavBtn:hover {
    background-color: rgba(99, 102, 241, 0.15);
    color: #f8fafc;
}

.SettingsNavBtn:checked {
    background-color: #6366f1;
    color: #ffffff;
    font-weight: 600;
}

.SettingsCard {
    background-color: rgba(30, 41, 59, 0.70);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 12px;
    padding: 18px;
    margin-bottom: 14px;
}

.SettingsSectionHeader {
    font-size: 18px;
    font-weight: 700;
    color: #f8fafc;
    margin-bottom: 12px;
}
```

---

## 7. Strategy Verification & Test Alignment

The proposed design directly satisfies all 10 test cases in `tests/test_settings.py`:
- `test_tier1_settings_sidebar_navigation`: Attributes `btn_general`, `btn_profiles`, `btn_search`, `btn_appearance`, `btn_about` present.
- `test_tier1_search_engine_switcher`: `set_search_engine` updates profile & emits signal for Google/DuckDuckGo.
- `test_tier1_profile_management_view`: `profile_manager` reference accessible.
- `test_tier1_homepage_setting_change`: `set_homepage` updates homepage & emits signal.
- `test_tier1_about_section_info`: `stack` container present.
- `test_tier2_search_engine_url_formatting`: Google and DuckDuckGo URL formatting verified.
- `test_tier2_invalid_homepage_url_correction`: Scheme auto-prepended to `https://`.
- `test_tier2_settings_page_open_in_tab_or_view`: Standalone or embedded in `PhantomBrowser` tab.
- `test_tier2_search_engine_validation_on_set`: Fallback to "Google" on invalid input.
- `test_tier2_multiple_signal_emissions`: Sequential emissions handled cleanly.
