#!/usr/bin/env python3
"""
Email Templates Preview Tool
Generates and previews email templates for LilyOpenCMS
"""

import os
import sys
import argparse
import webbrowser
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class EmailTemplatePreview:
    """Email template preview generator"""
    
    def __init__(self):
        self.templates_dir = "templates/email"
        self.preview_dir = "config/email_previews"
        
        # Create preview directory if it doesn't exist
        os.makedirs(self.preview_dir, exist_ok=True)
    
    def generate_verification_template(self, user_data: Dict[str, Any] = None) -> str:
        """Generate email verification template"""
        if not user_data:
            user_data = {
                'username': 'testuser',
                'first_name': 'Test',
                'last_name': 'User',
                'email': 'test@example.com'
            }
        
        token = "sample_verification_token_12345"
        verify_url = f"http://localhost:5000/verify-email?token={token}"
        
        subject = "Verify Your Email - LilyOpenCMS"
        body = f"""
Hello {user_data['first_name'] or user_data['username']},

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
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 5px; }}
        .content {{ padding: 20px; }}
        .button {{ display: inline-block; background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 5px; font-size: 12px; color: #666; }}
        .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 5px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>LilyOpenCMS</h1>
        </div>
        <div class="content">
            <h2>Verify Your Email Address</h2>
            <p>Hello {user_data['first_name'] or user_data['username']},</p>
            <p>Thank you for registering with LilyOpenCMS!</p>
            <p>Please click the button below to verify your email address:</p>
            <a href="{verify_url}" class="button">Verify Email Address</a>
            <p>Or copy and paste this link into your browser:</p>
            <p><a href="{verify_url}">{verify_url}</a></p>
            <div class="warning">
                <strong>This link will expire in 3 days.</strong>
            </div>
            <p>If you didn't create an account, please ignore this email.</p>
        </div>
        <div class="footer">
            <p>Best regards,<br>LilyOpenCMS Team</p>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return {
            'subject': subject,
            'body': body,
            'html_body': html_body,
            'type': 'verification'
        }
    
    def generate_password_reset_template(self, user_data: Dict[str, Any] = None) -> str:
        """Generate password reset template"""
        if not user_data:
            user_data = {
                'username': 'testuser',
                'first_name': 'Test',
                'last_name': 'User',
                'email': 'test@example.com'
            }
        
        token = "sample_reset_token_12345"
        reset_url = f"http://localhost:5000/reset-password?token={token}"
        
        subject = "Reset Your Password - LilyOpenCMS"
        body = f"""
Hello {user_data['first_name'] or user_data['username']},

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
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 5px; }}
        .content {{ padding: 20px; }}
        .button {{ display: inline-block; background-color: #dc3545; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 5px; font-size: 12px; color: #666; }}
        .warning {{ background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 10px; border-radius: 5px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>LilyOpenCMS</h1>
        </div>
        <div class="content">
            <h2>Reset Your Password</h2>
            <p>Hello {user_data['first_name'] or user_data['username']},</p>
            <p>You requested a password reset for your LilyOpenCMS account.</p>
            <p>Please click the button below to reset your password:</p>
            <a href="{reset_url}" class="button">Reset Password</a>
            <p>Or copy and paste this link into your browser:</p>
            <p><a href="{reset_url}">{reset_url}</a></p>
            <div class="warning">
                <strong>This link will expire in 1 hour.</strong>
            </div>
            <p>If you didn't request this password reset, please ignore this email.</p>
        </div>
        <div class="footer">
            <p>Best regards,<br>LilyOpenCMS Team</p>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return {
            'subject': subject,
            'body': body,
            'html_body': html_body,
            'type': 'password_reset'
        }
    
    def generate_welcome_template(self, user_data: Dict[str, Any] = None) -> str:
        """Generate welcome email template"""
        if not user_data:
            user_data = {
                'username': 'testuser',
                'first_name': 'Test',
                'last_name': 'User',
                'email': 'test@example.com'
            }
        
        subject = "Welcome to LilyOpenCMS!"
        body = f"""
Hello {user_data['first_name'] or user_data['username']},

Welcome to LilyOpenCMS! Your account has been successfully verified and activated.

You can now:
- Browse and read articles
- Create and manage your own albums
- Comment on articles and interact with the community
- Build your reading history and library

If you have any questions, feel free to contact our support team.

Best regards,
LilyOpenCMS Team
        """.strip()
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Welcome to LilyOpenCMS</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; border-radius: 5px; }}
        .content {{ padding: 20px; }}
        .feature-list {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        .feature-list ul {{ margin: 0; padding-left: 20px; }}
        .button {{ display: inline-block; background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 5px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Welcome to LilyOpenCMS!</h1>
        </div>
        <div class="content">
            <h2>Hello {user_data['first_name'] or user_data['username']}!</h2>
            <p>Your account has been successfully verified and activated.</p>
            
            <div class="feature-list">
                <h3>You can now:</h3>
                <ul>
                    <li>Browse and read articles</li>
                    <li>Create and manage your own albums</li>
                    <li>Comment on articles and interact with the community</li>
                    <li>Build your reading history and library</li>
                </ul>
            </div>
            
            <a href="http://localhost:5000/dashboard" class="button">Go to Dashboard</a>
            
            <p>If you have any questions, feel free to contact our support team.</p>
        </div>
        <div class="footer">
            <p>Best regards,<br>LilyOpenCMS Team</p>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return {
            'subject': subject,
            'body': body,
            'html_body': html_body,
            'type': 'welcome'
        }
    
    def save_preview(self, template_data: Dict[str, Any], filename: str = None):
        """Save template preview to HTML file"""
        if not filename:
            filename = f"{template_data['type']}_preview.html"
        
        filepath = os.path.join(self.preview_dir, filename)
        
        # Create full HTML document
        full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Email Template Preview - {template_data['type'].title()}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .preview-container {{ max-width: 800px; margin: 0 auto; }}
        .preview-header {{ background-color: #333; color: white; padding: 15px; border-radius: 5px 5px 0 0; }}
        .preview-content {{ background-color: white; padding: 20px; border-radius: 0 0 5px 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .template-info {{ background-color: #e9ecef; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .template-info h3 {{ margin-top: 0; }}
        .template-info p {{ margin: 5px 0; }}
        .email-content {{ border: 1px solid #ddd; border-radius: 5px; overflow: hidden; }}
    </style>
</head>
<body>
    <div class="preview-container">
        <div class="preview-header">
            <h1>📧 Email Template Preview</h1>
        </div>
        <div class="preview-content">
            <div class="template-info">
                <h3>Template Information</h3>
                <p><strong>Type:</strong> {template_data['type'].replace('_', ' ').title()}</p>
                <p><strong>Subject:</strong> {template_data['subject']}</p>
                <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="email-content">
                {template_data['html_body']}
            </div>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_html)
        
        return filepath
    
    def generate_all_previews(self):
        """Generate previews for all email templates"""
        templates = [
            self.generate_verification_template(),
            self.generate_password_reset_template(),
            self.generate_welcome_template()
        ]
        
        generated_files = []
        
        for template in templates:
            filename = f"{template['type']}_preview.html"
            filepath = self.save_preview(template, filename)
            generated_files.append(filepath)
            print(f"✅ Generated preview: {filepath}")
        
        return generated_files
    
    def open_preview(self, template_type: str):
        """Open template preview in browser"""
        filename = f"{template_type}_preview.html"
        filepath = os.path.join(self.preview_dir, filename)
        
        if os.path.exists(filepath):
            webbrowser.open(f"file://{os.path.abspath(filepath)}")
            print(f"🌐 Opened preview: {filepath}")
        else:
            print(f"❌ Preview file not found: {filepath}")
            print("Run 'generate' command first to create previews")

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='Email Templates Preview Tool')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate all previews
    subparsers.add_parser('generate', help='Generate all email template previews')
    
    # Generate specific template
    generate_parser = subparsers.add_parser('generate-template', help='Generate specific template preview')
    generate_parser.add_argument('type', choices=['verification', 'password_reset', 'welcome'], help='Template type')
    
    # Open preview
    open_parser = subparsers.add_parser('open', help='Open template preview in browser')
    open_parser.add_argument('type', choices=['verification', 'password_reset', 'welcome'], help='Template type')
    
    # List previews
    subparsers.add_parser('list', help='List available previews')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    preview = EmailTemplatePreview()
    
    if args.command == 'generate':
        preview.generate_all_previews()
    elif args.command == 'generate-template':
        if args.type == 'verification':
            template = preview.generate_verification_template()
        elif args.type == 'password_reset':
            template = preview.generate_password_reset_template()
        elif args.type == 'welcome':
            template = preview.generate_welcome_template()
        
        filepath = preview.save_preview(template)
        print(f"✅ Generated preview: {filepath}")
    elif args.command == 'open':
        preview.open_preview(args.type)
    elif args.command == 'list':
        print("📋 Available email templates:")
        print("- verification: Email verification template")
        print("- password_reset: Password reset template")
        print("- welcome: Welcome email template")

if __name__ == '__main__':
    main()
