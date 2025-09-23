#!/usr/bin/env python3
"""
Simple test to verify imports work correctly from test directory
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all necessary modules can be imported"""
    print("🧪 Testing Module Imports")
    print("="*30)

    try:
        # Test basic imports
        from models import db, User, AdCampaign, Ad, AdPlacement
        print("✅ Models import successful")

        from flask import Flask
        print("✅ Flask import successful")

        from routes.utils.email_service import EmailService
        print("✅ Email service import successful")

        print("\n🎉 All imports successful!")
        return True

    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
