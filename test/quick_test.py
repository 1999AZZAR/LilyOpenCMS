#!/usr/bin/env python3
"""
Quick Test Runner
Fast test execution without full reporting
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_quick_tests():
    """Run tests quickly without detailed reporting"""
    print("🚀 Quick Test Run")
    print("=" * 40)
    
    test_dir = Path("test")
    test_files = list(test_dir.glob("test_*.py"))
    test_files = [f for f in test_files if f.name not in ["run_tests.py", "quick_test.py"]]
    
    print(f"Found {len(test_files)} test files")
    print()
    
    passed = 0
    failed = 0
    
    for test_file in test_files:
        print(f"🧪 Running {test_file.name}...", end=" ")
        
        try:
            result = subprocess.run(
                [sys.executable, str(test_file)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0 and "✅" in result.stdout:
                print("✅ PASS")
                passed += 1
            else:
                print("❌ FAIL")
                failed += 1
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 40)
    print(f"📊 Results: {passed} passed, {failed} failed")
    print(f"Success Rate: {(passed / (passed + failed)) * 100:.1f}%" if (passed + failed) > 0 else "0%")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit_code = run_quick_tests()
    sys.exit(exit_code) 