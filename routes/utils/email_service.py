"""
Email Service for LilyOpenCMS
Handles SMTP configuration, email sending, and rate limiting
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from flask import current_app
from flask_mail import Mail, Message
import redis
import json

class EmailService:
    """Email service with SMTP configuration and rate limiting"""
    
    def __init__(self, app=None):
        self.mail = None
        self.redis_client = None
        self.config = {}
        self.rate_limits = {}
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize email service with Flask app"""
        try:
            # Load SMTP configuration
            self.config = self._load_smtp_config()
            
            # Initialize Flask-Mail
            app.config.update(self._get_flask_mail_config())
            self.mail = Mail(app)
            
            # Initialize Redis for rate limiting
            self._init_redis()
            
            # Initialize rate limits
            self.rate_limits = {
                'per_hour': self.config.get('email_rate_limit_per_hour', 10),
                'per_day': self.config.get('email_rate_limit_per_day', 50)
            }
            
            app.logger.info("✅ Email service initialized successfully")
            
        except Exception as e:
            app.logger.error(f"❌ Failed to initialize email service: {e}")
            # Fallback to logging mode
            self.mail = None
    
    def _load_smtp_config(self) -> Dict[str, Any]:
        """Load SMTP configuration from config file"""
        config_file = "config/smtp_config.txt"
        config = {}
        
        try:
            if not os.path.exists(config_file):
                current_app.logger.warning(f"⚠️ SMTP config file not found: {config_file}")
                return self._get_default_config()
            
            with open(config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse key=value pairs
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Convert value types
                        if value.lower() in ('true', 'false'):
                            config[key] = value.lower() == 'true'
                        elif value.isdigit():
                            config[key] = int(value)
                        elif value == '':
                            config[key] = None
                        else:
                            config[key] = value
            
            return config
            
        except Exception as e:
            current_app.logger.error(f"❌ Error reading SMTP config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default SMTP configuration"""
        return {
            'smtp_server': 'localhost',
            'smtp_port': 587,
            'smtp_use_tls': True,
            'smtp_use_ssl': False,
            'smtp_username': None,
            'smtp_password': None,
            'mail_default_sender': 'noreply@lilyopencms.com',
            'mail_sender_name': 'LilyOpenCMS',
            'mail_reply_to': 'noreply@lilyopencms.com',
            'email_rate_limit_per_hour': 10,
            'email_rate_limit_per_day': 50,
            'smtp_verify_ssl': True,
            'smtp_timeout': 30,
            'smtp_debug': False,
            'smtp_suppress_send': False
        }
    
    def _get_flask_mail_config(self) -> Dict[str, Any]:
        """Convert SMTP config to Flask-Mail format"""
        return {
            'MAIL_SERVER': self.config.get('smtp_server', 'localhost'),
            'MAIL_PORT': self.config.get('smtp_port', 587),
            'MAIL_USE_TLS': self.config.get('smtp_use_tls', True),
            'MAIL_USE_SSL': self.config.get('smtp_use_ssl', False),
            'MAIL_USERNAME': self.config.get('smtp_username'),
            'MAIL_PASSWORD': self.config.get('smtp_password'),
            'MAIL_DEFAULT_SENDER': self.config.get('mail_default_sender', 'noreply@lilyopencms.com'),
            'MAIL_SUPPRESS_SEND': self.config.get('smtp_suppress_send', False),
            'MAIL_DEBUG': self.config.get('smtp_debug', False)
        }
    
    def _init_redis(self):
        """Initialize Redis client for rate limiting"""
        try:
            # Try to get Redis config from existing config reader
            from routes.utils.config_reader import get_redis_config
            redis_config = get_redis_config()
            
            if redis_config.get('connection_type') == 'socket':
                self.redis_client = redis.Redis(
                    unix_socket_path=redis_config.get('socket_path'),
                    socket_connect_timeout=redis_config.get('socket_connect_timeout', 1),
                    socket_timeout=redis_config.get('socket_timeout', 1)
                )
            else:
                self.redis_client = redis.Redis(
                    host=redis_config.get('host', 'localhost'),
                    port=redis_config.get('port', 6379),
                    password=redis_config.get('password'),
                    socket_connect_timeout=redis_config.get('tcp_connect_timeout', 2),
                    socket_timeout=redis_config.get('tcp_timeout', 2)
                )
            
            # Test connection
            self.redis_client.ping()
            current_app.logger.info("✅ Redis connected for email rate limiting")
            
        except Exception as e:
            current_app.logger.warning(f"⚠️ Redis not available for email rate limiting: {e}")
            self.redis_client = None
    
    def _check_rate_limit(self, recipient: str) -> bool:
        """Check if recipient is within rate limits"""
        if not self.redis_client:
            return True  # No rate limiting if Redis unavailable
        
        try:
            now = datetime.now()
            hour_key = f"email_rate:{recipient}:{now.strftime('%Y%m%d%H')}"
            day_key = f"email_rate:{recipient}:{now.strftime('%Y%m%d')}"
            
            # Check hourly limit
            hour_count = self.redis_client.get(hour_key)
            if hour_count and int(hour_count) >= self.rate_limits['per_hour']:
                return False
            
            # Check daily limit
            day_count = self.redis_client.get(day_key)
            if day_count and int(day_count) >= self.rate_limits['per_day']:
                return False
            
            return True
            
        except Exception as e:
            current_app.logger.warning(f"⚠️ Rate limit check failed: {e}")
            return True  # Allow sending if rate limit check fails
    
    def _increment_rate_limit(self, recipient: str):
        """Increment rate limit counters"""
        if not self.redis_client:
            return
        
        try:
            now = datetime.now()
            hour_key = f"email_rate:{recipient}:{now.strftime('%Y%m%d%H')}"
            day_key = f"email_rate:{recipient}:{now.strftime('%Y%m%d')}"
            
            # Increment counters with expiration
            self.redis_client.incr(hour_key)
            self.redis_client.expire(hour_key, 3600)  # 1 hour
            
            self.redis_client.incr(day_key)
            self.redis_client.expire(day_key, 86400)  # 24 hours
            
        except Exception as e:
            current_app.logger.warning(f"⚠️ Rate limit increment failed: {e}")
    
    def send_email(self, 
                   to: str, 
                   subject: str, 
                   body: str, 
                   html_body: Optional[str] = None,
                   attachments: Optional[List[Dict]] = None) -> bool:
        """Send email with rate limiting and error handling"""
        
        # Check rate limits
        if not self._check_rate_limit(to):
            current_app.logger.warning(f"⚠️ Rate limit exceeded for {to}")
            return False
        
        # If email service is not available, log the email
        if not self.mail:
            current_app.logger.info(f"📧 EMAIL (SMTP disabled): To: {to}, Subject: {subject}")
            current_app.logger.info(f"📧 EMAIL DETAILS: From: {self.config.get('mail_default_sender')}, Server: {self.config.get('smtp_server')}")
            return True
        
        try:
            # Create message
            msg = Message(
                subject=subject,
                recipients=[to],
                body=body,
                html=html_body,
                sender=f"{self.config.get('mail_sender_name', 'LilyOpenCMS')} <{self.config.get('mail_default_sender', 'noreply@lilyopencms.com')}>"
            )
            
            # Add reply-to header
            if self.config.get('mail_reply_to'):
                msg.reply_to = self.config.get('mail_reply_to')
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    with open(attachment['file_path'], 'rb') as f:
                        msg.attach(
                            filename=attachment['filename'],
                            content_type=attachment.get('content_type', 'application/octet-stream'),
                            data=f.read()
                        )
            
            # Send email
            self.mail.send(msg)

            # Increment rate limit
            self._increment_rate_limit(to)

            current_app.logger.info(f"✅ Email sent successfully to {to}: {subject}")
            current_app.logger.info(f"✅ SMTP Config used: Server={self.config.get('smtp_server')}, Port={self.config.get('smtp_port')}, TLS={self.config.get('smtp_use_tls')}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"❌ Failed to send email to {to}: {e}")
            return False
    
    def send_verification_email(self, user, token: str) -> bool:
        """Send email verification email"""
        verify_url = f"{current_app.config.get('BASE_URL', 'http://localhost:5000')}/verify-email?token={token}"
        
        subject = "Verify Your Email - LilyOpenCMS"
        body = f"""
Hello {user.first_name or user.username},

Thank you for registering with LilyOpenCMS!

Please click the link below to verify your email address:
{verify_url}

This link will expire in 3 days.

If you didn't create an account, please ignore this email.

Best regards,
LilyOpenCMS Team
        """.strip()
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Verify Your Email</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 5px; }}
        .content {{ padding: 20px; }}
        .button {{ display: inline-block; background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 5px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>LilyOpenCMS</h1>
        </div>
        <div class="content">
            <h2>Verify Your Email Address</h2>
            <p>Hello {user.first_name or user.username},</p>
            <p>Thank you for registering with LilyOpenCMS!</p>
            <p>Please click the button below to verify your email address:</p>
            <a href="{verify_url}" class="button">Verify Email Address</a>
            <p>Or copy and paste this link into your browser:</p>
            <p><a href="{verify_url}">{verify_url}</a></p>
            <p><strong>This link will expire in 3 days.</strong></p>
            <p>If you didn't create an account, please ignore this email.</p>
        </div>
        <div class="footer">
            <p>Best regards,<br>LilyOpenCMS Team</p>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return self.send_email(
            to=user.email,
            subject=subject,
            body=body,
            html_body=html_body
        )
    
    def send_password_reset_email(self, user, token: str) -> bool:
        """Send password reset email"""
        reset_url = f"{current_app.config.get('BASE_URL', 'http://localhost:5000')}/reset-password?token={token}"
        
        subject = "Reset Your Password - LilyOpenCMS"
        body = f"""
Hello {user.first_name or user.username},

You requested a password reset for your LilyOpenCMS account.

Please click the link below to reset your password:
{reset_url}

This link will expire in 1 hour.

If you didn't request this password reset, please ignore this email.

Best regards,
LilyOpenCMS Team
        """.strip()
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Reset Your Password</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 5px; }}
        .content {{ padding: 20px; }}
        .button {{ display: inline-block; background-color: #dc3545; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 5px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>LilyOpenCMS</h1>
        </div>
        <div class="content">
            <h2>Reset Your Password</h2>
            <p>Hello {user.first_name or user.username},</p>
            <p>You requested a password reset for your LilyOpenCMS account.</p>
            <p>Please click the button below to reset your password:</p>
            <a href="{reset_url}" class="button">Reset Password</a>
            <p>Or copy and paste this link into your browser:</p>
            <p><a href="{reset_url}">{reset_url}</a></p>
            <p><strong>This link will expire in 1 hour.</strong></p>
            <p>If you didn't request this password reset, please ignore this email.</p>
        </div>
        <div class="footer">
            <p>Best regards,<br>LilyOpenCMS Team</p>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return self.send_email(
            to=user.email,
            subject=subject,
            body=body,
            html_body=html_body
        )
    
    def test_smtp_connection(self) -> Dict[str, Any]:
        """Test SMTP connection and return status"""
        result = {
            'success': False,
            'message': '',
            'config': self.config
        }
        
        try:
            if self.config.get('smtp_suppress_send', False):
                result['success'] = True
                result['message'] = 'SMTP is configured but suppressed (testing mode)'
                return result
            
            # Test connection
            server = smtplib.SMTP(
                self.config.get('smtp_server', 'localhost'),
                self.config.get('smtp_port', 587),
                timeout=self.config.get('smtp_timeout', 30)
            )
            
            if self.config.get('smtp_use_tls', True):
                server.starttls()
            
            if self.config.get('smtp_username') and self.config.get('smtp_password'):
                server.login(
                    self.config.get('smtp_username'),
                    self.config.get('smtp_password')
                )
            
            server.quit()
            
            result['success'] = True
            result['message'] = 'SMTP connection successful'
            
        except Exception as e:
            result['message'] = f'SMTP connection failed: {str(e)}'
        
        return result

# Global email service instance
email_service = EmailService()
