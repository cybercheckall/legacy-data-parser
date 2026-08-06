"""
ast_check.py - Forensic AST and Static Integrity Analyzer for Milestone 3.
"""

import ast
import os
import sys

def check_file(file_path):
    print(f"=== AST Analysis: {os.path.basename(file_path)} ===")
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source, filename=file_path)
    
    # 1. Imports check
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            imports.append(f"{node.module}")
            
    print(f"Imports ({len(imports)}): {', '.join(sorted(set(imports)))}")
    mock_imports = [imp for imp in imports if "mock" in imp.lower()]
    if mock_imports:
        print(f"  [WARNING] Suspicious mock import found: {mock_imports}")
    else:
        print("  [OK] No mock imports found.")

    # 2. Class definitions check
    classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    print(f"Classes defined ({len(classes)}): {[c.name for c in classes]}")

    # 3. Method analysis
    empty_methods = []
    hardcoded_returns = []
    
    for cls in classes:
        for node in cls.body:
            if isinstance(node, ast.FunctionDef):
                fn_name = f"{cls.name}.{node.name}"
                # Check for empty body
                non_doc_body = [n for n in node.body if not isinstance(n, ast.Expr) or not isinstance(n.value, ast.Constant)]
                if not non_doc_body or (len(non_doc_body) == 1 and isinstance(non_doc_body[0], ast.Pass)):
                    empty_methods.append(fn_name)
                
                # Check if body is just return constant
                if len(node.body) == 1 and isinstance(node.body[0], ast.Return) and isinstance(node.body[0].value, ast.Constant):
                    hardcoded_returns.append((fn_name, node.body[0].value.value))

    if empty_methods:
        print(f"  [WARNING] Empty stub methods: {empty_methods}")
    else:
        print("  [OK] No empty stub methods found.")

    if hardcoded_returns:
        print(f"  [WARNING] Constant return methods: {hardcoded_returns}")
    else:
        print("  [OK] No constant-return facade methods found.")

    # 4. Check for test environment bypass checks (e.g. if 'pytest' in sys.modules)
    bypass_keywords = ["pytest", "unittest", "PYTEST_CURRENT_TEST", "MOCK_MODE"]
    bypasses = []
    for kw in bypass_keywords:
        if kw in source and "test" not in os.path.basename(file_path):
            bypasses.append(kw)
    if bypasses:
        print(f"  [WARNING] Potential test environment bypass keywords found: {bypasses}")
    else:
        print("  [OK] No environment bypass flags detected in source code.")

    print()

if __name__ == "__main__":
    base_dir = r"C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser"
    files = [
        os.path.join(base_dir, "ai_panel.py"),
        os.path.join(base_dir, "settings_view.py"),
        os.path.join(base_dir, "browser.py"),
        os.path.join(base_dir, "profile_manager.py"),
    ]
    for f in files:
        check_file(f)
