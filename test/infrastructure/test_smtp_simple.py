#!/usr/bin/env python3
"""
Simple SMTP Connection Test
Tests SMTP connection directly without Flask dependencies
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def test_smtp_connection():
    """Test SMTP connection with current configuration"""
    print("🔍 Testing SMTP Connection...")

    # Load configuration
    config_file = "config/smtp_config.txt"
    config = {}

    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if value.lower() in ('true', 'false'):
                        config[key] = value.lower() == 'true'
                    elif value.isdigit():
                        config[key] = int(value)
                    elif value == '':
                        config[key] = None
                    else:
                        config[key] = value

    print(f"📋 SMTP Server: {config.get('smtp_server', 'Not configured')}")
    print(f"📋 SMTP Port: {config.get('smtp_port', 'Not configured')}")
    print(f"📋 Username: {config.get('smtp_username', 'Not configured')}")
    print(f"📋 Suppress Send: {config.get('smtp_suppress_send', False)}")

    if config.get('smtp_suppress_send', False):
        print("✅ Suppress Send is enabled - emails will be logged, not sent")
        return True

    # Test connection
    try:
        server = smtplib.SMTP(config.get('smtp_server', 'localhost'), config.get('smtp_port', 587))
        server.set_debuglevel(1)  # Enable debug output

        # Start TLS if configured
        if config.get('smtp_use_tls', True):
            server.starttls()

        # Login if credentials provided
        if config.get('smtp_username') and config.get('smtp_password'):
            server.login(config.get('smtp_username'), config.get('smtp_password'))

        print("✅ SMTP connection successful!")
        server.quit()
        return True

    except Exception as e:
        print(f"❌ SMTP connection failed: {e}")
        return False

def test_email_send():
    """Test sending an actual email"""
    print("\n🔍 Testing Email Send...")

    config_file = "config/smtp_config.txt"
    config = {}

    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if value.lower() in ('true', 'false'):
                        config[key] = value.lower() == 'true'
                    elif value.isdigit():
                        config[key] = int(value)
                    elif value == '':
                        config[key] = None
                    else:
                        config[key] = value

    if config.get('smtp_suppress_send', False):
        print("✅ Suppress Send is enabled - skipping actual email send test")
        return True

    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = config.get('mail_default_sender', 'noreply@lilyopencms.com')
        msg['To'] = config.get('smtp_username', 'test@example.com')  # Send to self for testing
        msg['Subject'] = 'LilyOpenCMS SMTP Test'

        body = 'This is a test email from LilyOpenCMS to verify SMTP functionality.'
        msg.attach(MIMEText(body, 'plain'))

        # Connect and send
        server = smtplib.SMTP(config.get('smtp_server'), config.get('smtp_port'))
        server.set_debuglevel(0)

        if config.get('smtp_use_tls', True):
            server.starttls()

        if config.get('smtp_username') and config.get('smtp_password'):
            server.login(config.get('smtp_username'), config.get('smtp_password'))

        server.sendmail(msg['From'], [msg['To']], msg.as_string())
        server.quit()

        print(f"✅ Test email sent successfully to {msg['To']}")
        print("📧 Check your email inbox to verify receipt")
        return True

    except Exception as e:
        print(f"❌ Email send failed: {e}")
        return False

if __name__ == '__main__':
    print("🚀 SMTP Connection Test")
    print("=" * 50)

    connection_ok = test_smtp_connection()
    send_ok = test_email_send()

    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print("=" * 50)
    print(f"Connection Test: {'✅ PASS' if connection_ok else '❌ FAIL'}")
    print(f"Email Send Test: {'✅ PASS' if send_ok else '❌ FAIL'}")

    if connection_ok and send_ok:
        print("\n🎉 All tests passed! SMTP is working correctly.")
        print("\n📋 Current Configuration:")
        config_file = "config/smtp_config.txt"
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                for line in f:
                    if not line.startswith('#') and '=' in line:
                        print(f"   {line.strip()}")
    else:
        print("\n⚠️  Some tests failed. Check your SMTP configuration.")
