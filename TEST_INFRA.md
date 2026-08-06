# E2E Test Infra: Phantom Workspace

## Test Philosophy
- Opaque-box, requirement-driven. No dependency on implementation design.
- Methodology: Category-Partition + BVA + Pairwise + Workload Testing.

## Feature Inventory
| # | Feature | Source (requirement) | Tier 1 | Tier 2 | Tier 3 | Tier 4 |
|---|---------|---------------------|:------:|:------:|:------:|:------:|
| 1 | Single-Instance Enforcement | ORIGINAL_REQUEST § R3 | 5 | 5 | ✓ | ✓ |
| 2 | Profiles Manager & Schema | ORIGINAL_REQUEST § R2 | 5 | 5 | ✓ | ✓ |
| 3 | Modern Frameless UI & TitleBar | ORIGINAL_REQUEST § R1 | 5 | 5 | ✓ | ✓ |
| 4 | Tab Bar & Nav Bar Controls | ORIGINAL_REQUEST § R1, R7 | 5 | 5 | ✓ | ✓ |
| 5 | AI Side Panel (ChatGPT) | ORIGINAL_REQUEST § R4 | 5 | 5 | ✓ | ✓ |
| 6 | Settings Page & Search Engine | ORIGINAL_REQUEST § R5 | 5 | 5 | ✓ | ✓ |
| 7 | Stealth Features Preservation | ORIGINAL_REQUEST § R6 | 5 | 5 | ✓ | ✓ |

## Test Architecture
- Test runner: pytest with PyQt6 `QApplication` / `QT_QPA_PLATFORM=offscreen`
- Test case format: Automated unit and integration pytest test cases in `tests/`
- Directory layout: `tests/`

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Profile Launch -> Search -> Settings Switch -> New Tab | Profiles, Settings, TabBar, Nav | Medium |
| 2 | Multiple Launches -> Single Instance Activation | Single Instance, Window Activation | Medium |
| 3 | AI Panel Toggle -> ChatGPT Load -> Close Panel | AI Side Panel, Floating Button | Medium |
| 4 | Stealth Protection Verification under Offscreen | Display Affinity, Hotkey | Medium |
| 5 | Full Workflow: Profile creation -> Tab navigation -> Search engine switch -> Stealth toggle | All Features | High |

## Coverage Thresholds
- Tier 1: ≥5 per feature (Total: 35+)
- Tier 2: ≥5 per feature (Total: 35+)
- Tier 3: Pairwise feature combinations
- Tier 4: ≥5 realistic application scenarios
