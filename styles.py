"""
styles.py - Modern Dark Glassmorphic QSS Stylesheet & Visual Theme Tokens.

Provides cohesive dark glassmorphism styling, color tokens, and smooth
micro-interaction definitions for Phantom Workspace.
"""

# Color Tokens
BG_DARK = "#0a0a1a"
GLASS_SURFACE = "rgba(15, 23, 42, 0.90)"
CARD_SURFACE = "rgba(30, 41, 59, 0.75)"
CARD_HOVER = "rgba(51, 65, 85, 0.90)"
ACCENT_INDIGO = "#6366f1"
ACCENT_PURPLE = "#533483"
TEXT_PRIMARY = "#f8fafc"
TEXT_MUTED = "#94a3b8"
BORDER_GLASS = "rgba(255, 255, 255, 0.10)"
BORDER_FOCUS = "#818cf8"
HOVER_BG = "rgba(255, 255, 255, 0.08)"
CLOSE_HOVER = "#ef4444"

DARK_GLASS_STYLE = """
/* Global Window & Widget Dark Theme */
QMainWindow {
    background-color: #0a0a1a;
    color: #f8fafc;
}

QWidget {
    color: #f8fafc;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
}

/* Frameless TitleBar Styling */
#TitleBar {
    background-color: rgba(15, 23, 42, 0.95);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

#TitleLabel {
    color: #f8fafc;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.5px;
}

.TitleButton {
    background-color: transparent;
    color: #94a3b8;
    border: none;
    border-radius: 6px;
    font-size: 13px;
    font-weight: bold;
    min-width: 28px;
    min-height: 24px;
}

.TitleButton:hover {
    background-color: rgba(255, 255, 255, 0.12);
    color: #ffffff;
}

.TitleButton:pressed {
    background-color: rgba(255, 255, 255, 0.20);
}

#CloseButton:hover {
    background-color: #ef4444;
    color: #ffffff;
}

#CloseButton:pressed {
    background-color: #dc2626;
}

/* Navigation Bar */
#NavBar {
    background-color: rgba(15, 23, 42, 0.85);
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    padding: 4px 8px;
}

#NavUrlBar {
    background-color: rgba(30, 41, 59, 0.70);
    color: #f8fafc;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 14px;
    padding: 5px 14px;
    font-size: 13px;
    selection-background-color: #6366f1;
}

#NavUrlBar:focus {
    border: 1px solid #6366f1;
    background-color: rgba(30, 41, 59, 0.95);
}

.NavButton {
    background-color: rgba(30, 41, 59, 0.60);
    color: #94a3b8;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    font-size: 14px;
    font-weight: bold;
    min-width: 32px;
    min-height: 28px;
}

.NavButton:hover {
    background-color: rgba(99, 102, 241, 0.25);
    color: #f8fafc;
    border: 1px solid rgba(99, 102, 241, 0.50);
}

.NavButton:pressed {
    background-color: #6366f1;
    color: #ffffff;
}

/* Tab Bar & Corner Widget */
QTabWidget::pane {
    border: none;
    background-color: #0a0a1a;
}

QTabBar::tab {
    background-color: rgba(15, 23, 42, 0.70);
    color: #94a3b8;
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    padding: 7px 16px;
    font-size: 12px;
    font-weight: 500;
    min-width: 90px;
    max-width: 220px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: rgba(30, 41, 59, 0.95);
    color: #f8fafc;
    border-bottom: 2px solid #6366f1;
    font-weight: 600;
}

QTabBar::tab:hover:!selected {
    background-color: rgba(51, 65, 85, 0.60);
    color: #cbd5e1;
}

#NewTabBtn {
    background-color: rgba(30, 41, 59, 0.80);
    color: #94a3b8;
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 14px;
    font-size: 16px;
    font-weight: bold;
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
}

#NewTabBtn:hover {
    background-color: #6366f1;
    color: #ffffff;
    border: 1px solid #818cf8;
}

/* Profile Selector View */
#ProfileSelector {
    background-color: #0a0a1a;
}

.ProfileCard {
    background-color: rgba(30, 41, 59, 0.70);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 14px;
    padding: 18px;
    color: #f8fafc;
    font-size: 14px;
    text-align: center;
}

.ProfileCard:hover {
    background-color: rgba(51, 65, 85, 0.90);
    border: 1px solid #6366f1;
}

.ProfileCard:pressed {
    background-color: #6366f1;
    color: #ffffff;
}

/* Bookmarks Bar */
#BookmarksBar {
    background-color: rgba(15, 23, 42, 0.50);
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.BookmarkBtn {
    background-color: transparent;
    color: #94a3b8;
    border: none;
    border-radius: 4px;
    padding: 3px 10px;
    font-size: 11px;
}

.BookmarkBtn:hover {
    background-color: rgba(255, 255, 255, 0.10);
    color: #f8fafc;
}

/* AI Floating Sparkle Button & Side Panel */
#AIFloatingButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366f1, stop:1 #4f46e5);
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.20);
    border-radius: 26px;
    font-size: 22px;
    font-weight: bold;
}

#AIFloatingButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #818cf8, stop:1 #6366f1);
    border: 1px solid rgba(255, 255, 255, 0.40);
}

#AIFloatingButton:pressed {
    background: #4338ca;
}

#AISidePanel {
    background-color: rgba(15, 23, 42, 0.95);
    border-left: 1px solid rgba(255, 255, 255, 0.10);
}

#AIHeader {
    background-color: rgba(30, 41, 59, 0.90);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

#AIHeaderLabel {
    color: #f8fafc;
    font-size: 14px;
    font-weight: bold;
    letter-spacing: 0.5px;
}

#AICloseBtn {
    background-color: transparent;
    color: #94a3b8;
    border: none;
    border-radius: 6px;
    font-size: 14px;
}

#AICloseBtn:hover {
    background-color: #ef4444;
    color: #ffffff;
}

/* Settings View Styling */
#SettingsView {
    background-color: #0a0a1a;
}

#SettingsSidebar {
    background-color: rgba(15, 23, 42, 0.85);
    border-right: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
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
    background-color: rgba(255, 255, 255, 0.08);
    color: #f8fafc;
}

.SettingsNavBtn[active="true"] {
    background-color: rgba(99, 102, 241, 0.20);
    color: #818cf8;
    font-weight: 600;
    border: 1px solid rgba(99, 102, 241, 0.40);
}

.SettingsCard {
    background-color: rgba(30, 41, 59, 0.60);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 16px;
}

/* Opacity Slider Styling */
QSlider#OpacitySlider {
    min-width: 90px;
    max-width: 120px;
    height: 20px;
}

QSlider#OpacitySlider::groove:horizontal {
    height: 4px;
    background: rgba(255, 255, 255, 0.15);
    border-radius: 2px;
}

QSlider#OpacitySlider::sub-page:horizontal {
    background: #6366f1;
    border-radius: 2px;
}

QSlider#OpacitySlider::handle:horizontal {
    background: #f8fafc;
    border: 1px solid #6366f1;
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
}

QSlider#OpacitySlider::handle:horizontal:hover {
    background: #ffffff;
    border: 1px solid #818cf8;
}
"""


