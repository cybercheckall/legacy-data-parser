"""
verify_signal.py - Empirical verification script for signal emission count.
"""

import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication
from single_instance import SingleInstanceGuard

def verify_signal_count():
    app = QApplication.instance() or QApplication(sys.argv)
    key = "empirical_verification_key_m1_2"
    
    primary = SingleInstanceGuard(app_key=key)
    assert primary.try_acquire(key) == True, "Primary acquire failed"
    
    signal_emissions = []
    primary.activation_requested.connect(lambda: signal_emissions.append(1))
    
    # Perform 5 secondary instance connection attempts
    for i in range(5):
        initial_count = len(signal_emissions)
        secondary = SingleInstanceGuard(app_key=key)
        res = secondary.try_acquire(key)
        assert res == False, f"Secondary attempt {i+1} should return False"
        QCoreApplication.processEvents()
        new_count = len(signal_emissions)
        delta = new_count - initial_count
        print(f"Secondary attempt {i+1}: signal count delta = {delta} (total: {new_count})")
        assert delta == 1, f"Expected exactly 1 signal emission, got {delta}"
        secondary.release()
        QCoreApplication.processEvents()
        
    primary.release()
    print("ALL 5 SECONDARY LAUNCHES EMITTED EXACTLY 1 SIGNAL EACH. VERIFICATION PASSED.")

if __name__ == "__main__":
    verify_signal_count()
