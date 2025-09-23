#!/usr/bin/env python3
"""
Gmail SMTP Quick Setup
Interactive script to configure Gmail SMTP settings
"""

import os
import sys
import getpass

def setup_gmail_config():
    """Interactive Gmail SMTP setup"""
    print("🔧 Gmail SMTP Quick Setup")
    print("=" * 50)
    print("This script will help you configure Gmail SMTP for LilyOpenCMS.")
    print("You'll need:")
    print("1. A Gmail account with 2-Factor Authentication enabled")
    print("2. An App Password generated for this application")
    print()
    
    # Get Gmail credentials
    email = input("Enter your Gmail address: ").strip()
    if not email or '@gmail.com' not in email:
        print("❌ Please enter a valid Gmail address")
        return False
    
    print("\n🔑 App Password Setup:")
    print("1. Go to: https://myaccount.google.com/security")
    print("2. Enable 2-Factor Authentication if not already enabled")
    print("3. Go to 'App passwords' and generate one for 'Mail'")
    print("4. Copy the 16-character password (format: abcd efgh ijkl mnop)")
    print()
    
    app_password = getpass.getpass("Enter your Gmail App Password: ").strip()
    if not app_password or len(app_password.replace(' ', '')) != 16:
        print("❌ App Password should be 16 characters (with or without spaces)")
        return False
    
    # Update configuration
    config_file = "config/smtp_config.txt"
    
    try:
        # Read current config
        with open(config_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Update the configuration
        updated_lines = []
        for line in lines:
            if line.startswith('smtp_username='):
                updated_lines.append(f'smtp_username={email}\n')
            elif line.startswith('smtp_password='):
                updated_lines.append(f'smtp_password={app_password}\n')
            elif line.startswith('mail_default_sender='):
                updated_lines.append(f'mail_default_sender={email}\n')
            elif line.startswith('mail_reply_to='):
                updated_lines.append(f'mail_reply_to={email}\n')
            else:
                updated_lines.append(line)
        
        # Write back to file
        with open(config_file, 'w', encoding='utf-8') as f:
            f.writelines(updated_lines)
        
        print("✅ Configuration updated successfully!")
        print(f"📧 Gmail: {email}")
        print("🔑 App Password: [HIDDEN]")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to update configuration: {e}")
        return False

def test_gmail_connection():
    """Test Gmail SMTP connection"""
    print("\n🧪 Testing Gmail Connection...")
    
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
        
        # Test connection
        result = email_service.test_smtp_connection()
        
        if result['success']:
            print("✅ Gmail SMTP connection successful!")
            return True
        else:
            print(f"❌ Connection failed: {result['message']}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def send_test_email():
    """Send a test email"""
    print("\n📨 Send Test Email")
    
    test_email = input("Enter email address to send test to: ").strip()
    if not test_email:
        print("❌ No email address provided")
        return False
    
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
        
        # Send test email
        success = email_service.send_email(
            to=test_email,
            subject="LilyOpenCMS SMTP Test",
            body="This is a test email from LilyOpenCMS. If you received this, your SMTP configuration is working correctly!",
            html_body="""
            <html>
            <body>
                <h2>🎉 SMTP Test Successful!</h2>
                <p>This is a test email from <strong>LilyOpenCMS</strong>.</p>
                <p>If you received this email, your SMTP configuration is working correctly!</p>
                <hr>
                <p><em>Best regards,<br>LilyOpenCMS Team</em></p>
            </body>
            </html>
            """
        )
        
        if success:
            print(f"✅ Test email sent successfully to {test_email}")
            return True
        else:
            print("❌ Failed to send test email")
            return False
            
    except Exception as e:
        print(f"❌ Send test failed: {e}")
        return False

def main():
    """Main setup process"""
    print("🚀 Gmail SMTP Setup for LilyOpenCMS")
    print("=" * 50)
    
    # Step 1: Setup configuration
    if not setup_gmail_config():
        print("❌ Setup failed. Please check your Gmail settings.")
        return
    
    # Step 2: Test connection
    if not test_gmail_connection():
        print("❌ Connection test failed. Please check your credentials.")
        return
    
    # Step 3: Send test email
    send_test = input("\nSend test email? (y/n): ").strip().lower()
    if send_test in ['y', 'yes']:
        send_test_email()
    
    print("\n🎉 Gmail SMTP setup complete!")
    print("\n📋 What's Next:")
    print("1. Your LilyOpenCMS will now send real emails")
    print("2. User registration will send verification emails")
    print("3. Password reset functionality is ready")
    print("4. Check your Flask app logs to see email activity")
    
    print("\n📚 Documentation:")
    print("- Gmail Setup Guide: config/GMAIL_SETUP_GUIDE.md")
    print("- SMTP Setup Guide: config/SMTP_SETUP_README.md")

if __name__ == '__main__':
    main()
