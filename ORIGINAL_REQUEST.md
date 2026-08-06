# Original User Request

## 2026-08-05T01:03:05Z

Overhaul the existing Phantom Browser (a stealth PyQt6 Chromium browser with display affinity protection) into **Phantom Workspace** — a modern, next-generation private workspace browser that is visually stunning, unique, and attractive enough to compete with mainstream browsers. Think iPhone-level design polish: every pixel matters, every interaction should feel premium.

Working directory: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser
Integrity mode: development

## Requirements

### R1. Modern Chrome-like UI Overhaul

The browser UI must be completely redesigned with a premium, modern dark aesthetic. Key UI changes:

- **Navigation bar**: Remove back/forward arrow buttons entirely. Keep only the reload button. The URL/search bar should be prominent and centered.
- **Tab bar**: Chrome-style tabs at the top with smooth tab animations. New tab button ("+") on the right side of the tab bar, just like Chrome.
- **Title bar**: Custom frameless title bar with minimize, maximize, close buttons. Modern window controls.
- **Overall aesthetic**: Dark glassmorphism theme with subtle gradients, micro-animations on hover/click, smooth transitions, modern typography (use system fonts like Segoe UI or similar). The UI should look next-generation — not like a 2015 browser, but like a 2026 premium workspace tool. Use rounded corners, subtle shadows, blur effects where appropriate.
- **Icons**: Use modern, clean SVG/Unicode icons throughout. No ugly text-based buttons.

### R2. Browser Profiles System

Implement a profile system similar to Chrome/Firefox but tailored for a **private browser** (no cookies or browsing history are stored):

- Users can create, select, edit, and delete profiles.
- Each profile stores: name, avatar/icon, preferred homepage URL, and preferred search engine (Google or DuckDuckGo).
- On app launch, show a profile selector screen (modern card-based UI) to choose which profile to use.
- Profiles are saved to a local JSON file so they persist between sessions.
- Since this is a private/stealth browser, profiles do NOT store cookies, browsing history, or cache — they are purely preference-based.

### R3. Single-Instance Application Enforcement

The application must enforce single-instance behavior:

- If the user launches the app and it's already running, the existing window should be brought to the foreground and activated — do NOT open a second instance.
- Use a named mutex (Windows) or lock file mechanism to detect existing instances.
- The second launch attempt should signal the first instance to show/activate itself, then exit.

### R4. AI Side Panel (ChatGPT Integration)

Add an AI assistant side panel, inspired by how Google integrates Gemini into Chrome:

- At the bottom center of the browser window, display a floating circular button/icon (like the Gemini sparkle icon shown in the reference images — use a modern AI-style icon, perhaps a sparkle ✦ or similar).
- When the user clicks this button, a side panel slides in from the right side of the screen, containing an embedded ChatGPT webview (loading https://chatgpt.com).
- The panel should be approximately 380-420px wide with a header showing "ChatGPT" title and a close (X) button.
- Clicking the floating button again (or the X button) should smoothly hide/slide the panel away.
- The floating button should have a subtle glow/pulse animation to make it noticeable.
- The side panel should have a smooth slide-in/slide-out animation.

### R5. Modern Settings Page

Implement a full settings page accessible from a gear/settings icon in the browser toolbar:

- **Search Engine**: Choose between Google and DuckDuckGo as the default search engine (applies to URL bar searches).
- **Profile Management**: View, edit, create, delete profiles from settings.
- **Appearance**: Toggle options (though dark mode is default, show the option).
- **About**: Show browser name, version info.
- **General**: Homepage setting, startup behavior.
- The settings page should be rendered as an in-browser page (like chrome://settings) with a modern sidebar navigation layout. Use smooth animations and a clean, organized layout matching the browser's premium dark theme.
- Show options similar to what modern browsers display — organized into logical sections.

### R6. Preserve Stealth & Core Features

All existing stealth/core features must be preserved:

- `SetWindowDisplayAffinity` (WDA_EXCLUDEFROMCAPTURE) — window invisible to screen capture/sharing.
- `WindowStaysOnTopHint` — always-on-top behavior.
- `Tool` window flag — no taskbar icon.
- Global hotkey (`Ctrl+Shift+B`) to toggle visibility.
- Frameless window with custom drag support.
- PyInstaller build spec should be updated to include any new files.

### R7. Tab Behavior

- When the last tab is closed, navigate to the homepage instead of closing the app (already implemented, preserve this).
- New tabs should open with the user's configured homepage (from their profile).
- Tab titles should update dynamically based on page titles.
- Tabs should be closable, movable/reorderable.

## Acceptance Criteria

### UI Quality
- [ ] The browser UI uses a cohesive dark theme with modern aesthetics (gradients, rounded corners, subtle animations)
- [ ] No text-based navigation buttons — all controls use proper icons
- [ ] Back/forward buttons are removed; only reload button remains in the navigation bar
- [ ] Tab bar is Chrome-style with a "+" new tab button on the right side
- [ ] The floating AI button is visible at the bottom center of the window
- [ ] The ChatGPT side panel slides in/out smoothly when toggled

### Profiles
- [ ] A profile selector screen appears on app launch
- [ ] Users can create a new profile with name, avatar, homepage, and search engine preference
- [ ] Profiles persist across app restarts (stored in JSON)
- [ ] Profiles do NOT store cookies, history, or cache

### Single Instance
- [ ] Launching a second instance brings the existing window to the foreground
- [ ] Only one instance of the application can run at a time

### Settings
- [ ] Settings page is accessible from the toolbar
- [ ] Users can switch between Google and DuckDuckGo as default search engine
- [ ] Settings page has modern UI matching the browser theme

### Stealth Features
- [ ] Display affinity protection still works (window invisible to screen capture)
- [ ] Global hotkey (Ctrl+Shift+B) still toggles visibility
- [ ] Window has no taskbar icon and stays on top

### Build
- [ ] The application launches without errors: `python main.py`
- [ ] PyInstaller spec is updated for any new files/modules

## Follow-up — 2026-08-05T02:57:35Z

Resume project from PAUSE_STATE.md. Proceed with Milestone 2 (Modern Glassmorphic UI & Tab Bar) and remaining milestones through completion.

## Follow-up — 2026-08-05T12:44:41Z

Resume project from PAUSE_STATE.md. Finalize M2 gate clearance and launch Milestone 3 (AI Side Panel & Settings System), followed by Milestone 4 and final Victory Audit.

## Follow-up — 2026-08-05T13:05:35Z

CRITICAL REQUIREMENT UPDATE:
1. Application Name: Change from "Phantom Workspace" to "Owl".
2. Application Icon: Use `owl_icon.jpg` located at `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\owl_icon.jpg` for PyQt6 window icon (`setWindowIcon`) and PyInstaller executable icon (convert to `.ico` or configure spec).
3. PyInstaller Executable: Build target executable as `Owl.exe` (or `owl.exe`).
4. Update all UI window titles, title bar labels, settings page about section, and PyInstaller `.spec` file accordingly.

## Follow-up — 2026-08-05T18:28:50Z

Resume the Phantom Workspace project located at `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser`.
Read `PAUSE_STATE.md` to restore your exact state and context. The project was paused exactly as Milestone 3 cleared its quality gates.

You must immediately launch and complete **Milestone 4** and the **Victory Audit**:

### Milestone 4 Requirements (Rebranding & Polish):
1. **Rebrand**: Change the application name entirely from "Phantom Workspace" to **"Owl"**. Update all window titles, UI labels, and the About settings section.
2. **Iconography**: Use `owl_icon.jpg` (located in the project root) as the PyQt6 window icon (`setWindowIcon`). Convert to `.ico` if necessary for PyInstaller.
3. **Build Spec**: Update `phantom_browser.spec` to output `Owl.exe` and use the new icon.
4. **Stealth Verification**: Ensure all original stealth features (WDA_EXCLUDEFROMCAPTURE display affinity, Tool window flag, StaysOnTop, Ctrl+Shift+B global hotkey) remain fully functional and unbroken.

### Victory Audit
- Run the full pytest suite.
- Ensure 100% pass rate.
- Finalize the codebase and prepare for user handoff.

## Follow-up — 2026-08-05T19:19:21Z

Update the UI and functionality of the existing "Owl" stealth browser to match new design specifications, including a transparency slider, Chrome-style tabs, a Guest-only startup profile, and a custom homepage.

Working directory: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser
Integrity mode: development

## Requirements

### R1. Profile Selector
On app startup, the profile selector UI must only show a "Guest mode" option initially. 

### R2. Transparency Slider
Add a slider control in the custom title bar, positioned between the "Owl" application title and the window controls (minimize/maximize/close). This slider must dynamically control the overall opacity/transparency of the entire browser window.

### R3. Chrome-Style Tabs
Redesign the tab bar to closely mimic Google Chrome. The tabs should have rounded top corners, and the "New Tab" (+) button must be positioned immediately to the right of the last active tab, rather than fixed to the far right side of the window.

### R4. Custom Homepage and Navigation Bar
Set the default homepage to a clean Google search page. The navigation/URL bar must include an "AI Mode" button inside it, matching the provided reference image. Ensure that any quick-links or shortcuts to ChatGPT, Claude, Google, StackOverflow, GitHub, and LeetCode are completely removed from the homepage.

### R5. Preserve Stealth Features
Ensure all existing stealth features remain 100% intact:
- `SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)`
- `WS_EX_TOOLWINDOW` and `WS_EX_NOACTIVATE` / `Qt.WindowType.Tool`
- `WindowStaysOnTopHint`
- `Ctrl+Shift+B` hotkey

## Acceptance Criteria

### UI Updates
- [ ] Profile selector defaults to showing only Guest mode.
- [ ] A functional transparency slider exists in the title bar.
- [ ] Tab bar styling matches Chrome, with the '+' button adjacent to tabs.
- [ ] Homepage is a clean Google page without the specified shortcuts.
- [ ] "AI Mode" button is integrated into the URL/search bar.

### Regression
- [ ] All 159 existing automated tests (including stealth verification) continue to pass.

## Follow-up — 2026-08-05T19:22:31Z

URGENT REQUIREMENT UPDATE:
Do NOT add any "Google AI" or "AI Mode" button to the URL bar or homepage.
- The default homepage should be a clean, standard Google search page without any "AI Mode" buttons and without quick-links/shortcuts (ChatGPT, Claude, Google, StackOverflow, GitHub, LeetCode).
- The navigation/URL bar must be a standard URL bar without any "AI Mode" button.
- R4 is updated to: Set the default homepage to a clean Google search page without shortcuts or AI Mode buttons. The navigation/URL bar must remain a standard URL bar without any AI Mode button.



## Follow-up — 2026-08-06T05:25:01Z

Resume the Owl UI update project located at `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser`.
Read `PAUSE_STATE_UI.md` to restore your exact state and context. The project was paused during Phase 2 Execution.

You must immediately resume and implement:
- **M1**: Guest mode profile selector default on startup.
- **M2**: Transparency slider in the custom title bar (to control overall window opacity).
- **M3**: Chrome-style tab bar with adjacent '+' new tab button.
- **M4**: Clean Google Search homepage and standard URL bar (no AI buttons, no extra shortcuts).

Then execute the verification (ensuring all 159 tests pass and stealth is preserved) and run the independent Victory Audit.

**CRITICAL**: The user is very low on usage limits (30% remaining). You must execute with maximum efficiency, speed, and zero unnecessary back-and-forth iteration. Claim victory and hand off as quickly as possible.








