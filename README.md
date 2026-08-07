# 🦉 Owl Stealth Workspace

**Owl** is a premium, next-generation stealth browser designed for maximum privacy, modern aesthetics, and seamless AI integration. Built using PyQt6 and QtWebEngine, it acts as a fully isolated, zero-trace workspace that remains completely invisible to screen capture software and intrusive applications.

## ✨ Key Features

### 🛡️ Ultimate Stealth & Privacy
- **Screen-Capture Invisibility**: Leverages the Windows API `SetWindowDisplayAffinity(WDA_EXCLUDEFROMCAPTURE)` to render the browser completely invisible to screen recording software (OBS Studio, Zoom, Teams) and screenshot utilities.
- **Taskbar & Alt-Tab Suppression**: Uses `WS_EX_TOOLWINDOW` and `WS_EX_NOACTIVATE` to run as a floating widget, preventing the application from appearing in the Windows Taskbar or the Alt-Tab switcher.
- **Always-On-Top Layering**: Forces the Windows Desktop Window Manager (DWM) to render the browser above all other applications, ensuring it never gets buried behind other windows.
- **Direct Launch**: Simply double-click the executable to launch the browser — no hotkeys required.
- **Zero-Trace Ephemeral Profiles**: All browsing data (cookies, history, cache) is kept strictly off-the-record in memory. Once the browser is closed, all session data is permanently destroyed.

### 🎨 Premium Glassmorphic UI
- **Custom Frameless Design**: Stripped of the standard Windows borders and title bars for a pure, clean, modern dark card aesthetic.
- **Window Opacity Slider**: A built-in slider in the custom title bar allows users to dynamically adjust the transparency of the entire application window on the fly.
- **Chrome-Style Tab System**: Beautifully curved tabs with dynamic '+' button placement that perfectly mimics the premium feel of Google Chrome.
- **Guest Mode Default**: The profile selector defaults to a clean, isolated Guest Mode profile upon startup.
- **Clean Google Navigation**: The homepage and URL bar are designed to be completely distraction-free, defaulting to a pristine Google Search page without cluttered shortcuts.

### 🤖 Integrated AI Co-Pilot
- **Floating AI Sparkle**: A discreet, pulsing floating sparkle button (`✦`) sits at the bottom center of the workspace.
- **Sliding ChatGPT Panel**: Clicking the floating button slides out a sleek 400px side panel running a fully integrated ChatGPT webview, allowing you to ask questions and brainstorm without ever leaving your workspace.

## 🚀 Installation & Usage

### Running from Source
Ensure you have Python 3.12+ installed along with the required dependencies (`PyQt6`, `pytest`).
```powershell
# Clone the repository
git clone https://github.com/Raghuvaranlokati/private-brower.git
cd private-brower

# Run the application
python main.py
```

### Running the Standalone Executable
If you prefer not to use Python, you can run the compiled standalone application directly:
1. Navigate to the `dist` folder.
2. Double-click `Owl.exe`.

*(Note: If you run `Owl.exe` from your desktop, make sure to keep the application closed when attempting to update or replace the executable).*

## 🧪 Testing & Verification
This project maintains a rigorous **100% test coverage** standard.
Run the automated test suite to verify the integrity of all features, including the stealth protections and UI components:
```powershell
pytest tests/ -v
```
*(Currently passing 163 / 163 tests)*

---
*Built with precision and stealth.* 🦉✨
