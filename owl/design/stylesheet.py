"""
Owl stealth workspace theme.

Handler (owl logo + tabs) over slim place row, pill omnibox,
Ask Owl AI control at the bottom. Icon-first, no wordmark in the shell.
"""

import sys

# Color Tokens (light workspace model)
BG_DARK = "#ffffff"
BG_CONTENT = "#ffffff"
SHELL_BG = "#dee1e6"
TAB_STRIP_BG = "#dee1e6"
SURFACE = "#ffffff"
SURFACE_RAISED = "#f1f3f4"
ACCENT_BLUE = "#1a73e8"
ACCENT_ORANGE = "#f97316"
TEXT_PRIMARY = "#202124"
TEXT_MUTED = "#5f6368"
BORDER_SUBTLE = "#dadce0"
CLOSE_HOVER = "#ea4335"

# Legacy aliases
GLASS_SURFACE = "#ffffff"
CARD_SURFACE = "#ffffff"
CARD_HOVER = "#f1f3f4"
ACCENT_INDIGO = ACCENT_BLUE
ACCENT_PURPLE = "#a142f4"
BORDER_GLASS = "#dadce0"
BORDER_FOCUS = ACCENT_BLUE
HOVER_BG = "rgba(60, 64, 67, 0.08)"

_UI_FONT = (
    "'Helvetica Neue', 'SF Pro Text', Arial, sans-serif"
    if sys.platform == "darwin"
    else "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
)

DARK_GLASS_STYLE = """
/* Global — light workspace model */
QMainWindow {
    background-color: #ffffff;
    color: #202124;
}

QWidget {
    color: #202124;
    font-family: __UI_FONT__;
}

/* ===== Shell layers (one continuous surface) ===== */
#LayerCommand, #CommandBar, #TitleBar, #HandlerTabsHost {
    background-color: #e8eaed;
    border: none;
}
#LayerNav, #NavBar {
    background-color: #e8eaed;
    border-bottom: 1px solid #dadce0;
}
#LayerTabs, #TabStrip {
    background-color: transparent;
    border: none;
}
#LayerContent {
    background-color: #ffffff;
}

#OwlBrandBtn {
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 0;
}
#OwlBrandBtn:hover {
    background-color: rgba(60, 64, 67, 0.10);
}

#TitleLabel {
    color: #202124;
    font-size: 12px;
    font-weight: 600;
}

.TitleButton {
    background-color: transparent;
    color: #5f6368;
    border: none;
    border-radius: 6px;
    font-size: 13px;
    font-weight: bold;
    min-width: 28px;
    min-height: 24px;
}

.TitleButton:hover {
    background-color: rgba(60, 64, 67, 0.10);
    color: #202124;
}

#CloseButton:hover {
    background-color: #ea4335;
    color: #ffffff;
}

/* Tab strip in handler */
#OwlTabBar {
    background-color: transparent;
    qproperty-drawBase: 0;
}

#OwlTabBar::tab {
    background-color: transparent;
    color: #5f6368;
    border: none;
    border-radius: 8px;
    /* No top/bottom padding — horizontal only (room for close on right) */
    padding: 0 28px 0 14px;
    font-size: 13px;
    font-weight: 500;
    letter-spacing: 0.1px;
    min-width: 120px;
    max-width: 220px;
    min-height: 26px;
    max-height: 28px;
    margin-top: 0;
    margin-bottom: 0;
    margin-right: 4px;
}

#OwlTabBar::tab:selected {
    background-color: #ffffff;
    color: #202124;
    font-weight: 600;
}

#OwlTabBar::tab:hover:!selected {
    background-color: rgba(60, 64, 67, 0.10);
    color: #202124;
}

/* Custom close toolbutton — always visible on the right */
QToolButton#TabCloseBtn {
    background-color: transparent;
    border: none;
    border-radius: 9px;
    padding: 0;
    margin: 0 4px 0 0;
    min-width: 18px;
    max-width: 18px;
    min-height: 18px;
    max-height: 18px;
}

QToolButton#TabCloseBtn:hover {
    background-color: rgba(60, 64, 67, 0.14);
}

QToolButton#TabCloseBtn:pressed {
    background-color: rgba(234, 67, 53, 0.18);
}

#NewTabBtn {
    background-color: transparent;
    color: #5f6368;
    border: none;
    border-radius: 14px;
    font-size: 18px;
    font-weight: 500;
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
    padding: 0;
}

#NewTabBtn:hover {
    background-color: rgba(60, 64, 67, 0.12);
    color: #202124;
}

/* Legacy QTabWidget selectors (tests / fallbacks) */
QTabWidget::pane {
    border: none;
    background-color: #ffffff;
}

QTabBar::tab {
    background-color: transparent;
    color: #5f6368;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    padding: 8px 16px;
    font-size: 12px;
    min-width: 90px;
    max-width: 220px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #202124;
    font-weight: 600;
}

/* Omnibox inside command bar */
#NavUrlBar {
    background-color: #ffffff;
    color: #202124;
    border: 1px solid #dadce0;
    border-radius: 20px;
    padding: 6px 12px;
    font-size: 13px;
    selection-background-color: #d2e3fc;
    min-height: 28px;
    max-height: 32px;
}

#NavUrlBar:focus {
    border: 1px solid #1a73e8;
    background-color: #ffffff;
}

.NavButton {
    background-color: transparent;
    color: #3c4043;
    border: none;
    border-radius: 16px;
    font-size: 14px;
    font-weight: 500;
    min-width: 32px;
    min-height: 32px;
    padding: 0;
}

.NavButton:hover {
    background-color: rgba(60, 64, 67, 0.10);
    color: #202124;
}

.NavButton:pressed {
    background-color: rgba(60, 64, 67, 0.16);
}

.NavButton:disabled {
    color: #bdc1c6;
}

#ShieldBtn {
    color: #ea8600;
}

#ShieldBtn:hover {
    background-color: rgba(234, 134, 0, 0.12);
}

#ProfileBtn {
    font-size: 15px;
    border-radius: 16px;
}

#AISidePanel {
    background-color: #ffffff;
    border-left: 1px solid #dadce0;
}

/* Profile Selector */
#ProfileSelector {
    background-color: #f8f9fa;
}

.ProfileCard {
    background-color: #ffffff;
    border: 1px solid #dadce0;
    border-radius: 14px;
    padding: 18px;
    color: #202124;
    font-size: 14px;
    text-align: center;
}

.ProfileCard:hover {
    background-color: #f1f3f4;
    border: 1px solid #1a73e8;
}

.ProfileCard:pressed {
    background-color: #1a73e8;
    color: #ffffff;
}

/* Bookmarks Bar */
#BookmarksBar {
    background-color: #ffffff;
    border-bottom: 1px solid #dadce0;
}

.BookmarkBtn {
    background-color: transparent;
    color: #5f6368;
    border: none;
    border-radius: 4px;
    padding: 3px 10px;
    font-size: 11px;
}

.BookmarkBtn:hover {
    background-color: rgba(60, 64, 67, 0.08);
    color: #202124;
}

/* Ask Owl — Gemini-style pill at BOTTOM */
#AIFloatingButton {
    background-color: #ffffff;
    color: #202124;
    border: 1px solid #dadce0;
    border-radius: 22px;
    font-size: 13px;
    font-weight: 600;
    padding: 0 16px;
}

#AIFloatingButton:hover {
    background-color: #f8f9fa;
    border: 1px solid #bdc1c6;
}

#AIFloatingButton:pressed {
    background-color: #f1f3f4;
}

#AIHeader {
    background-color: #f8f9fa;
    border-bottom: 1px solid #dadce0;
}

#AIHeaderLabel {
    color: #202124;
    font-size: 14px;
    font-weight: bold;
}

#AICloseBtn {
    background-color: transparent;
    color: #5f6368;
    border: none;
    border-radius: 6px;
    font-size: 14px;
}

#AICloseBtn:hover {
    background-color: #ea4335;
    color: #ffffff;
}

/* Settings */
#SettingsView {
    background-color: #ffffff;
}

#SettingsSidebar {
    background-color: #f8f9fa;
    border-right: 1px solid #dadce0;
    border-radius: 10px;
}

.SettingsNavBtn {
    background-color: transparent;
    color: #5f6368;
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 13px;
    font-weight: 500;
    text-align: left;
}

.SettingsNavBtn:hover {
    background-color: rgba(60, 64, 67, 0.08);
    color: #202124;
}

.SettingsNavBtn[active="true"] {
    background-color: #e8f0fe;
    color: #1a73e8;
    font-weight: 600;
    border: 1px solid #d2e3fc;
}

.SettingsCard {
    background-color: #f8f9fa;
    border: 1px solid #dadce0;
    border-radius: 12px;
    padding: 16px;
}

QSlider#OpacitySlider {
    min-width: 64px;
    max-width: 80px;
    height: 20px;
    margin: 0 2px;
}

QSlider#OpacitySlider::groove:horizontal {
    height: 4px;
    background: #dadce0;
    border-radius: 2px;
}

QSlider#OpacitySlider::sub-page:horizontal {
    background: #1a73e8;
    border-radius: 2px;
}

QSlider#OpacitySlider::handle:horizontal {
    background: #ffffff;
    border: 1px solid #1a73e8;
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
}

QSlider#OpacitySlider::handle:horizontal:hover {
    background: #e8f0fe;
    border: 1px solid #1a73e8;
}
"""

DARK_GLASS_STYLE = DARK_GLASS_STYLE.replace("__UI_FONT__", _UI_FONT)
