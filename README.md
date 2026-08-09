# 🦉 Owl Stealth Workspace

**Owl** is a premium, next-generation stealth browser designed for maximum privacy, modern aesthetics, and seamless AI integration. Built using PyQt6 and QtWebEngine, it acts as a fully isolated, zero-trace workspace that remains difficult for screen-capture tools to record.

## Platforms

| Platform | Browser UI | Capture exclusion | Taskbar / Dock hiding |
|----------|------------|-------------------|------------------------|
| **Windows** | ✅ | `SetWindowDisplayAffinity` | Always-on-top window |
| **macOS** | ✅ | `NSWindowSharingNone` | Accessory activation policy (no Dock icon) |
| Linux | Partial | Not supported | Always-on-top (best-effort) |

Owl stays visible when you click outside the window (Esc still hides intentionally).

## ✨ Key Features

### 🛡️ Ultimate Stealth & Privacy
- **Screen-Capture Invisibility**: On Windows uses `SetWindowDisplayAffinity(WDA_EXCLUDEFROMCAPTURE)`. On macOS uses `NSWindow.setSharingType(NSWindowSharingNone)`.
- **Taskbar / Dock Suppression**: Windows Tool window flags; macOS accessory activation policy.
- **Always-On-Top Layering**: Stays above other applications.
- **Direct Launch**: Double-click / `python main.py` — no hotkeys required.
- **Zero-Trace Ephemeral Profiles**: Cookies, history, and cache stay off-the-record in memory and are destroyed on close.

### 🎨 Stealth Workspace UI
```
L1  Handler   ●●● · 🦉 logo · tabs · + · shield
L2  Place     icon nav · omnibox · utilities
L3  Content   page (+ Ask Owl pill at bottom)
```
- Icon-first branding (owl logo, no wordmark in the shell)
- Tabs live in the window handler; URL sits in a slim row beneath
- Guest Mode by default · clean Google homepage

### 🤖 Integrated AI Co-Pilot
- Bottom **Ask Owl** pill on the content layer opens a sliding AI side panel

## 📁 Project layout

```
owl/
  shell/       # Handler + Place rows (command bar, tabs, nav)
  workspace/   # Main window + content layer
  profiles/    # Identity & OTR isolation
  settings/    # Preferences UI
  ai/          # Ask Owl co-pilot
  stealth/     # Capture exclusion, single-instance
  design/      # Tokens, stylesheet, icons
assets/brand/  # Icons & brand art
packaging/     # PyInstaller specs
tests/
main.py        # Entrypoint
```

## 🚀 Installation & Usage

### Requirements
- Python **3.12+**
- macOS 12+ **or** Windows 10+

### Running from Source

```bash
# Clone
git clone https://github.com/Raghuvaranlokati/private-brower.git
cd private-brower

# Create venv (recommended)
python3.12 -m venv .venv
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Run
python main.py

# Dev mode — auto-restart when you edit .py files
python dev.py
```

### Windows Standalone Executable
1. Navigate to the `dist` folder.
2. Double-click `Owl.exe`.

Build with PyInstaller (Windows):

```powershell
pyinstaller packaging/owl.spec
```

### macOS App (`Owl.app`)

```bash
source .venv/bin/activate
pip install -r requirements.txt
pyinstaller --noconfirm --clean packaging/owl_mac.spec
open dist/Owl.app
# Optional: put on Desktop
cp -R dist/Owl.app ~/Desktop/
```

- First open: if Gatekeeper blocks it, right-click → **Open**.
- Capture exclusion reduces visibility in many screen-sharing apps; some privileged capture APIs can still see the window (OS limitation).
- Logs are written to `~/Desktop/stealth_browser.log`.
- The app may stay out of the Dock (stealth accessory policy).

## 🧪 Testing

```bash
pytest tests/ -v
```

---
*Built with precision and stealth.* 🦉✨
