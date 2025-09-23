# SMTP Troubleshooting Guide

## 🚨 Common Issue: "Network is unreachable" Error

If you're getting `[Errno 101] Network is unreachable` when trying to connect to Gmail SMTP, this is a common issue with shared hosting providers.

### 🔍 Quick Diagnosis

Run the network diagnostic tool to identify the issue:

```bash
python config/network_diagnostic.py
```

This will test connectivity to various SMTP servers and show you which ones work.

## 🛠️ Solutions

### Solution 1: Enable Development Mode (Immediate Fix)

If you need emails to work immediately for testing:

```bash
python config/enable_dev_mode.py
```

This will log emails instead of sending them, so your application won't crash.

### Solution 2: Use Alternative SMTP Providers

Run the alternative SMTP setup:

```bash
python config/alternative_smtp_setup.py
```

Choose from:
- **Hostinger SMTP** (if you're using Hostinger hosting)
- **Outlook/Hotmail SMTP**
- **Yahoo SMTP**
- **Custom SMTP Server**

### Solution 3: Contact Your Hosting Provider

Many shared hosting providers block outbound SMTP connections. Contact your hosting provider and ask:

1. "Do you block outbound SMTP connections?"
2. "What SMTP server should I use for sending emails?"
3. "Do you provide SMTP credentials for my domain?"

## 📧 Hosting Provider SMTP Settings

### Hostinger
```
smtp_server=mail.hostinger.com
smtp_port=587
smtp_use_tls=true
smtp_use_ssl=false
smtp_username=your-email@yourdomain.com
smtp_password=your-email-password
```

### cPanel Hosting
```
smtp_server=mail.yourdomain.com
smtp_port=587
smtp_use_tls=true
smtp_use_ssl=false
smtp_username=your-email@yourdomain.com
smtp_password=your-email-password
```

### GoDaddy
```
smtp_server=smtpout.secureserver.net
smtp_port=587
smtp_use_tls=true
smtp_use_ssl=false
smtp_username=your-email@yourdomain.com
smtp_password=your-email-password
```

## 🔧 Alternative Email Services

If your hosting provider blocks all SMTP, consider these services:

### SendGrid (Free tier: 100 emails/day)
1. Sign up at sendgrid.com
2. Get API key
3. Use SendGrid API instead of SMTP

### Mailgun (Free tier: 5,000 emails/month)
1. Sign up at mailgun.com
2. Get API key
3. Use Mailgun API instead of SMTP

### Amazon SES (Pay per use)
1. Set up AWS account
2. Verify domain
3. Use SES API instead of SMTP

## 🧪 Testing Your Configuration

After setting up alternative SMTP:

```bash
# Test connection
python config/smtp_config_helper.py test

# Send test email
python config/smtp_config_helper.py send-test your-email@example.com
```

## 📋 Configuration File Location

Your SMTP configuration is stored in:
```
config/smtp_config.txt
```

## 🔍 Debugging Tips

1. **Check your hosting provider's documentation** for SMTP settings
2. **Test with different ports** (587, 465, 25)
3. **Try different protocols** (TLS vs SSL)
4. **Contact support** if nothing works
5. **Use development mode** as a temporary solution

## ⚠️ Security Notes

- Never commit SMTP passwords to version control
- Use App Passwords for Gmail/Outlook
- Consider using environment variables for sensitive data
- Enable SSL/TLS when possible

## 🆘 Still Having Issues?

1. Run the network diagnostic: `python config/network_diagnostic.py`
2. Check your hosting provider's SMTP documentation
3. Contact your hosting provider's support
4. Consider using a third-party email service
5. Use development mode as a temporary workaround

## 📞 Getting Help

If you're still stuck:
1. Check the application logs for detailed error messages
2. Run the diagnostic tools provided
3. Contact your hosting provider
4. Consider alternative email solutions
