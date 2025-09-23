# SMTP Setup Guide for LilyOpenCMS

This guide covers the complete SMTP setup for LilyOpenCMS, including configuration, testing, and email template management.

## Overview

The SMTP system provides:
- Email verification for user registration
- Password reset functionality
- Rate limiting to prevent abuse
- HTML and plain text email templates
- Configuration management tools
- Testing and preview utilities

## Files Structure

```
config/
├── smtp_config.txt              # SMTP configuration file
├── smtp_config_helper.py        # Configuration and testing tool
├── email_templates_preview.py   # Email template preview tool
├── test_smtp_setup.py          # Complete setup test suite
└── SMTP_SETUP_README.md        # This guide

routes/utils/
└── email_service.py            # Core email service implementation
```

## Quick Start

### 1. Install Dependencies

```bash
# Install Flask-Mail (already added to requirements.txt)
pip install Flask-Mail
```

### 2. Configure SMTP Settings

Edit `config/smtp_config.txt` with your SMTP provider details:

```ini
# SMTP Server Configuration
smtp_server=smtp.gmail.com
smtp_port=587
smtp_use_tls=true
smtp_use_ssl=false

# Authentication
smtp_username=your-email@gmail.com
smtp_password=your-app-password

# Email Settings
mail_default_sender=noreply@yourdomain.com
mail_sender_name=Your Site Name
mail_reply_to=noreply@yourdomain.com

# Rate Limiting
email_rate_limit_per_hour=10
email_rate_limit_per_day=50

# Security
smtp_verify_ssl=true
smtp_timeout=30

# Development/Testing
smtp_debug=false
smtp_suppress_send=false
```

### 3. Test the Setup

```bash
# Run the complete test suite
python config/test_smtp_setup.py

# Test SMTP connection
python config/smtp_config_helper.py test

# Send a test email
python config/smtp_config_helper.py send-test your@email.com
```

## Configuration Options

### SMTP Server Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `smtp_server` | SMTP server hostname | localhost |
| `smtp_port` | SMTP server port | 587 |
| `smtp_use_tls` | Enable TLS encryption | true |
| `smtp_use_ssl` | Use SSL instead of TLS | false |
| `smtp_username` | SMTP username | (empty) |
| `smtp_password` | SMTP password | (empty) |
| `smtp_timeout` | Connection timeout (seconds) | 30 |
| `smtp_verify_ssl` | Verify SSL certificates | true |

### Email Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `mail_default_sender` | Default sender email | noreply@lilyopencms.com |
| `mail_sender_name` | Sender display name | LilyOpenCMS |
| `mail_reply_to` | Reply-to email address | noreply@lilyopencms.com |

### Rate Limiting

| Setting | Description | Default |
|---------|-------------|---------|
| `email_rate_limit_per_hour` | Max emails per hour per recipient | 10 |
| `email_rate_limit_per_day` | Max emails per day per recipient | 50 |

### Development Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `smtp_debug` | Enable SMTP debug output | false |
| `smtp_suppress_send` | Log emails instead of sending | false |

## Popular SMTP Providers

### Gmail

```ini
smtp_server=smtp.gmail.com
smtp_port=587
smtp_use_tls=true
smtp_username=your-email@gmail.com
smtp_password=your-app-password
```

**Note**: Use App Passwords, not your regular Gmail password.

### Outlook/Hotmail

```ini
smtp_server=smtp-mail.outlook.com
smtp_port=587
smtp_use_tls=true
smtp_username=your-email@outlook.com
smtp_password=your-password
```

### SendGrid

```ini
smtp_server=smtp.sendgrid.net
smtp_port=587
smtp_use_tls=true
smtp_username=apikey
smtp_password=your-sendgrid-api-key
```

### Mailgun

```ini
smtp_server=smtp.mailgun.org
smtp_port=587
smtp_use_tls=true
smtp_username=your-mailgun-smtp-username
smtp_password=your-mailgun-smtp-password
```

## Tools and Utilities

### SMTP Configuration Helper

```bash
# Interactive setup
python config/smtp_config_helper.py setup

# Test connection
python config/smtp_config_helper.py test

# Send test email
python config/smtp_config_helper.py send-test recipient@example.com

# Show current configuration
python config/smtp_config_helper.py show

# Update a setting
python config/smtp_config_helper.py update smtp_server smtp.gmail.com
```

### Email Template Preview

```bash
# Generate all template previews
python config/email_templates_preview.py generate

# Generate specific template
python config/email_templates_preview.py generate-template verification

# Open preview in browser
python config/email_templates_preview.py open verification

# List available templates
python config/email_templates_preview.py list
```

### Complete Setup Test

```bash
# Run all tests
python config/test_smtp_setup.py
```

## Email Templates

The system includes three built-in email templates:

### 1. Email Verification
- Sent when users register
- Contains verification link
- Expires in 3 days

### 2. Password Reset
- Sent when users request password reset
- Contains reset link
- Expires in 1 hour

### 3. Welcome Email
- Sent after successful verification
- Welcomes users to the platform
- Lists available features

## Integration with Authentication

The email service is automatically integrated with the authentication system:

- **Registration**: Sends verification email automatically
- **Email Verification**: Handles verification link processing
- **Password Reset**: Ready for password reset functionality
- **Rate Limiting**: Prevents email abuse

## Rate Limiting

The system includes built-in rate limiting using Redis:

- **Per Hour**: Configurable limit per recipient per hour
- **Per Day**: Configurable limit per recipient per day
- **Automatic**: Counters reset automatically
- **Fallback**: Works without Redis (no rate limiting)

## Error Handling

The email service includes comprehensive error handling:

- **Connection Failures**: Graceful fallback to logging
- **Authentication Errors**: Clear error messages
- **Rate Limit Exceeded**: Prevents sending
- **Invalid Recipients**: Validates email addresses
- **Template Errors**: Fallback to plain text

## Development Mode

For development, you can:

1. **Suppress Sending**: Set `smtp_suppress_send=true` to log emails instead of sending
2. **Enable Debug**: Set `smtp_debug=true` to see SMTP debug output
3. **Use Local SMTP**: Configure a local SMTP server for testing

## Production Considerations

For production deployment:

1. **Use App Passwords**: Don't use regular email passwords
2. **Enable SSL/TLS**: Always use encrypted connections
3. **Set Rate Limits**: Configure appropriate rate limits
4. **Monitor Logs**: Watch for email delivery issues
5. **Backup Configuration**: Keep SMTP settings secure

## Troubleshooting

### Common Issues

**Connection Refused**
- Check SMTP server and port
- Verify firewall settings
- Test with telnet: `telnet smtp.gmail.com 587`

**Authentication Failed**
- Verify username and password
- Use App Passwords for Gmail
- Check if 2FA is enabled

**Emails Not Delivered**
- Check spam folders
- Verify sender reputation
- Test with different recipients

**Rate Limiting Issues**
- Check Redis connection
- Verify rate limit settings
- Monitor email logs

### Debug Mode

Enable debug mode to see detailed SMTP communication:

```ini
smtp_debug=true
```

### Testing Without Sending

Use suppress mode to test without actually sending emails:

```ini
smtp_suppress_send=true
```

## Security Best Practices

1. **Use Environment Variables**: Store sensitive data in environment variables
2. **App Passwords**: Use application-specific passwords
3. **Rate Limiting**: Implement appropriate rate limits
4. **SSL/TLS**: Always use encrypted connections
5. **Input Validation**: Validate all email addresses
6. **Logging**: Log email activities for monitoring

## Support

If you encounter issues:

1. Run the test suite: `python config/test_smtp_setup.py`
2. Check the logs for error messages
3. Verify SMTP configuration with the helper tool
4. Test with a simple email client first

## Roadmap Integration

This SMTP setup addresses the following items from the roadmap:

- ✅ **Email delivery for verification (SMTP)** - Implemented
- ✅ **Verification email templates** - Implemented  
- ✅ **Resend verification with rate limits** - Implemented
- ✅ **SMTP config helper + delivery tester** - Implemented
- ✅ **Email templates preview tool** - Implemented

The system is now ready for the pending email-related features in Phase 2 of the roadmap.
