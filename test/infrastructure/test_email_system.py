#!/usr/bin/env python3
"""
Simple Email System Test
Tests the email system functionality
"""

import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

def test_email_service():
    """Test the email service"""
    print("🔍 Testing Email Service...")
    
    try:
        from routes.utils.email_service import EmailService
        from flask import Flask
        
        # Create test app
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-key'
        app.config['BASE_URL'] = 'http://localhost:5000'
        
        # Initialize email service
        email_service = EmailService()
        email_service.init_app(app)
        
        print("✅ Email service initialized successfully")
        
        # Test configuration
        print(f"📋 SMTP Server: {email_service.config.get('smtp_server')}")
        print(f"📋 Suppress Send: {email_service.config.get('smtp_suppress_send')}")
        
        # Test connection
        result = email_service.test_smtp_connection()
        print(f"📧 Connection Test: {'✅ Success' if result['success'] else '❌ Failed'}")
        print(f"📧 Message: {result['message']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Email service test failed: {e}")
        return False

def test_email_templates():
    """Test email template generation"""
    print("\n🔍 Testing Email Templates...")
    
    try:
        from config.email_templates_preview import EmailTemplatePreview
        
        preview = EmailTemplatePreview()
        
        # Test verification template
        verification_template = preview.generate_verification_template()
        print("✅ Verification template generated")
        print(f"   Subject: {verification_template['subject']}")
        
        # Test password reset template
        reset_template = preview.generate_password_reset_template()
        print("✅ Password reset template generated")
        print(f"   Subject: {reset_template['subject']}")
        
        # Test welcome template
        welcome_template = preview.generate_welcome_template()
        print("✅ Welcome template generated")
        print(f"   Subject: {welcome_template['subject']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Email template test failed: {e}")
        return False

def test_auth_integration():
    """Test authentication integration"""
    print("\n🔍 Testing Authentication Integration...")

    try:
        from routes.routes_auth import _send_verification_email
        print("✅ Authentication routes can import email service")
        return True

    except Exception as e:
        print(f"❌ Authentication integration test failed: {e}")
        return False

def test_smtp_directly():
    """Test SMTP connection directly"""
    print("\n🔍 Testing SMTP Connection Directly...")

    try:
        import smtplib
        from routes.utils.email_service import EmailService
        from flask import Flask

        # Create test app
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-key'
        app.config['BASE_URL'] = 'http://localhost:5000'

        # Initialize email service
        email_service = EmailService()
        email_service.init_app(app)

        print(f"📋 SMTP Server: {email_service.config.get('smtp_server')}")
        print(f"📋 SMTP Port: {email_service.config.get('smtp_port')}")
        print(f"📋 Use TLS: {email_service.config.get('smtp_use_tls')}")
        print(f"📋 Username: {email_service.config.get('smtp_username')}")
        print(f"📋 Suppress Send: {email_service.config.get('smtp_suppress_send')}")

        # Test connection
        result = email_service.test_smtp_connection()
        print(f"📧 Connection Test: {'✅ Success' if result['success'] else '❌ Failed'}")
        print(f"📧 Message: {result['message']}")

        if result['success']:
            print("✅ SMTP connection is working properly!")
        else:
            print("❌ SMTP connection failed - check configuration")

        return result['success']

    except Exception as e:
        print(f"❌ SMTP test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🚀 Email System Test")
    print("=" * 50)
    
    tests = [
        ("Email Service", test_email_service),
        ("Email Templates", test_email_templates),
        ("Authentication Integration", test_auth_integration),
        ("SMTP Connection", test_smtp_directly)
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
        print(f"{test_name:25}: {status}")
        if result:
            passed += 1
    
    print("=" * 50)
    print(f"Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Email system is ready.")
        print("\n📋 Next Steps:")
        print("1. The system is configured for development mode (emails will be logged)")
        print("2. To test with real emails, configure a real SMTP provider")
        print("3. Run the Flask app to test user registration emails")
    else:
        print("⚠️  Some tests failed. Check the configuration.")
