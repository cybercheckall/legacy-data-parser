"""Platform stealth: capture exclusion, single-instance, window policy."""

from owl.stealth.display_affinity import (
    apply_display_affinity,
    apply_app_stealth_policy,
    WDA_EXCLUDEFROMCAPTURE,
)
from owl.stealth.single_instance import SingleInstanceGuard, DEFAULT_APP_KEY

__all__ = [
    "apply_display_affinity",
    "apply_app_stealth_policy",
    "WDA_EXCLUDEFROMCAPTURE",
    "SingleInstanceGuard",
    "DEFAULT_APP_KEY",
]
