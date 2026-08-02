# Phantom Browser

A stealth Chromium browser built with PyQt6, global hotkey support, and desktop window affinity protection.

## What this repo contains

- `main.py` — application entrypoint
- `browser.py` — main browser UI and tab management
- `hotkey.py` — global hotkey support for toggling the browser
- `display_affinity.py` — display affinity helper for Windows
- `phantom_browser.spec` — PyInstaller spec for building `phantom_browser.exe`
- `test_sample.spec` — PyInstaller spec for a sample test executable
- `tests/` — test files for project validation

## Requirements

- Windows 10/11
- Python 3.11+ (or compatible Python 3.x)
- `PyQt6`
- `PyInstaller`
- `pynput`

## Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install PyQt6 pyinstaller pynput
```

## Run from source

```powershell
python main.py
```

## Build the executable

This project uses PyInstaller and the provided spec file.

```powershell
pyinstaller phantom_browser.spec
```

After the build completes, the executable will be in the `dist\phantom_browser\` directory.

## Ignore generated files

This repo ignores build and distribution artifacts using `.gitignore`.

## Notes

- Do not commit `build/` or `dist/` directories.
- `dist/phantom_browser.exe` and related generated files are large and should remain local.
- Use `git rm --cached -r build dist` if generated files were accidentally tracked.

## Troubleshooting

- If `pyinstaller` fails because of missing Qt resources, verify `PyQt6` is installed and that the correct `QtWebEngineProcess.exe` path exists.
- If the app does not start, make sure `PyQt6.QtWebEngineWidgets` is available.
