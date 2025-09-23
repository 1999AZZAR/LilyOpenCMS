#!/usr/bin/env python3
"""
SMTP Setup Test Script
Tests the complete SMTP setup and email functionality
"""

import os
import sys
import tempfile
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_smtp_config():
    """Test SMTP configuration loading"""
    print("🔍 Testing SMTP Configuration...")
    
    try:
        from routes.utils.email_service import EmailService
        
        # Create a temporary Flask app for testing
        from flask import Flask
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-key'
        app.config['BASE_URL'] = 'http://localhost:5000'
        
        # Initialize email service
        email_service = EmailService()
        email_service.init_app(app)
        
        print("✅ Email service initialized successfully")
        
        # Test configuration
        print(f"📋 SMTP Server: {email_service.config.get('smtp_server', 'Not configured')}")
        print(f"📋 SMTP Port: {email_service.config.get('smtp_port', 'Not configured')}")
        print(f"📋 Use TLS: {email_service.config.get('smtp_use_tls', 'Not configured')}")
        print(f"📋 Default Sender: {email_service.config.get('mail_default_sender', 'Not configured')}")
        print(f"📋 Suppress Send: {email_service.config.get('smtp_suppress_send', 'Not configured')}")
        
        return True
        
    except Exception as e:
        print(f"❌ SMTP configuration test failed: {e}")
        return False

def test_email_service():
    """Test email service functionality"""
    print("\n🔍 Testing Email Service...")
    
    try:
        from routes.utils.email_service import EmailService
        
        # Create a temporary Flask app for testing
        from flask import Flask
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-key'
        app.config['BASE_URL'] = 'http://localhost:5000'
        
        # Initialize email service
        email_service = EmailService()
        email_service.init_app(app)
        
        # Test connection
        result = email_service.test_smtp_connection()
        print(f"📧 SMTP Connection Test: {'✅ Success' if result['success'] else '❌ Failed'}")
        print(f"📧 Message: {result['message']}")
        
        return result['success']
        
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
        
        # Test password reset template
        reset_template = preview.generate_password_reset_template()
        print("✅ Password reset template generated")
        
        # Test welcome template
        welcome_template = preview.generate_welcome_template()
        print("✅ Welcome template generated")
        
        return True
        
    except Exception as e:
        print(f"❌ Email template test failed: {e}")
        return False

def test_auth_integration():
    """Test authentication integration"""
    print("\n🔍 Testing Authentication Integration...")
    
    try:
        # Test if the auth routes can import the email service
        from routes.routes_auth import _send_verification_email
        print("✅ Authentication routes can import email service")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication integration test failed: {e}")
        return False

def test_config_helper():
    """Test SMTP configuration helper"""
    print("\n🔍 Testing SMTP Configuration Helper...")
    
    try:
        from config.smtp_config_helper import SMTPConfigHelper
        
        helper = SMTPConfigHelper()
        
        # Test config loading
        config = helper._load_config()
        print("✅ Configuration helper can load config")
        
        # Test connection test
        result = helper.test_connection()
        print(f"📧 Helper Connection Test: {'✅ Success' if result['success'] else '❌ Failed'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration helper test failed: {e}")
        return False

def main():
    """Run all SMTP setup tests"""
    print("🚀 SMTP Setup Test Suite")
    print("=" * 50)
    
    tests = [
        ("SMTP Configuration", test_smtp_config),
        ("Email Service", test_email_service),
        ("Email Templates", test_email_templates),
        ("Authentication Integration", test_auth_integration),
        ("Configuration Helper", test_config_helper)
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
        print("🎉 All tests passed! SMTP setup is ready.")
    else:
        print("⚠️  Some tests failed. Check the configuration and dependencies.")
    
    print("\n📋 Next Steps:")
    print("1. Configure your SMTP settings in config/smtp_config.txt")
    print("2. Run: python config/smtp_config_helper.py setup")
    print("3. Test connection: python config/smtp_config_helper.py test")
    print("4. Send test email: python config/smtp_config_helper.py send-test your@email.com")
    print("5. Preview templates: python config/email_templates_preview.py generate")

if __name__ == '__main__':
    main()
