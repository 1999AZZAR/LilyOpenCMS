#!/usr/bin/env python3

import smtplib
import os

# Test SMTP connection manually
def test_connection():
    print("Testing SMTP connection...")

    # Configuration from smtp_config.txt
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'hystory.id@gmail.com'
    smtp_password = 'bcijwaskrbtdvsdc'

    try:
        # Connect to SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.set_debuglevel(1)  # Enable debug output

        print(f"Connected to {smtp_server}:{smtp_port}")

        # Start TLS
        server.starttls()
        print("TLS started")

        # Login
        server.login(smtp_username, smtp_password)
        print("Login successful")

        # Test sending a simple email
        from email.mime.text import MIMEText
        msg = MIMEText("This is a test email from LilyOpenCMS SMTP test.")
        msg['Subject'] = 'LilyOpenCMS SMTP Test'
        msg['From'] = smtp_username
        msg['To'] = smtp_username

        server.sendmail(smtp_username, [smtp_username], msg.as_string())
        print("Test email sent successfully!")

        server.quit()
        print("Connection closed successfully")
        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_connection()
    print(f"Test result: {'SUCCESS' if success else 'FAILED'}")
