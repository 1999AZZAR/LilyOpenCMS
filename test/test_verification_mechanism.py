#!/usr/bin/env python3
"""
Test the verification mechanism directly
"""

import os
import sys
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

def test_verification_email_generation():
    """Test verification email generation"""
    print("🔍 Testing Verification Email Generation...")

    try:
        # Mock user object
        class MockUser:
            def __init__(self):
                self.id = 123
                self.username = "testuser"
                self.email = "test@example.com"
                self.first_name = "Test"
                self.last_name = "User"

        # Mock Flask app
        class MockApp:
            def __init__(self):
                self.config = {
                    'SECRET_KEY': 'test-secret-key',
                    'BASE_URL': 'http://localhost:5000'
                }
                self.logger = MockLogger()

        class MockLogger:
            def info(self, msg): print(f"INFO: {msg}")
            def warning(self, msg): print(f"WARNING: {msg}")
            def error(self, msg): print(f"ERROR: {msg}")

        # Mock current_app
        import routes.utils.email_service
        routes.utils.email_service.current_app = MockApp()

        # Create mock user
        user = MockUser()

        # Test email service
        from routes.utils.email_service import EmailService

        app = MockApp()
        email_service = EmailService()
        email_service.init_app(app)

        print(f"✅ Email service initialized")
        print(f"📋 SMTP Server: {email_service.config.get('smtp_server')}")
        print(f"📋 Suppress Send: {email_service.config.get('smtp_suppress_send')}")

        # Test verification email
        print(f"\n🔍 Testing verification email for user: {user.username}")
        success = email_service.send_verification_email(user, "test-token-123")

        if success:
            print("✅ Verification email sent successfully!")
        else:
            print("❌ Verification email failed to send")

        return success

    except Exception as e:
        print(f"❌ Verification email test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_smtp_config_loading():
    """Test SMTP configuration loading"""
    print("\n🔍 Testing SMTP Configuration Loading...")

    try:
        from routes.utils.email_service import EmailService
        from flask import Flask

        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-key'
        app.config['BASE_URL'] = 'http://localhost:5000'

        email_service = EmailService()
        config = email_service._load_smtp_config()

        print("✅ SMTP configuration loaded successfully")
        print(f"📋 Configuration keys: {list(config.keys())}")
        print(f"📋 SMTP Server: {config.get('smtp_server')}")
        print(f"📋 SMTP Port: {config.get('smtp_port')}")
        print(f"📋 Username: {config.get('smtp_username')}")
        print(f"📋 Suppress Send: {config.get('smtp_suppress_send')}")

        return True

    except Exception as e:
        print(f"❌ SMTP config loading failed: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Verification Mechanism Test")
    print("=" * 50)

    tests = [
        ("SMTP Configuration", test_smtp_config_loading),
        ("Verification Email", test_verification_email_generation)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name"25"}: {status}")
        if result:
            passed += 1

    print("=" * 50)
    print(f"Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Verification mechanism is working.")
    else:
        print("⚠️  Some tests failed. Check the configuration and logs.")
