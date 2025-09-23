# DirectAdmin SMTP Setup Guide

## 🎯 DirectAdmin-Specific SMTP Configuration

DirectAdmin hosting providers typically use domain-based SMTP servers. Here's how to set up SMTP for your DirectAdmin hosting.

## 🔧 Quick Setup

Run the DirectAdmin-specific setup tool:

```bash
python config/directadmin_smtp_setup.py
```

This will:
1. Auto-detect your domain's SMTP server
2. Test connectivity to common DirectAdmin ports
3. Set up the optimal configuration

## 📧 Common DirectAdmin SMTP Settings

### Standard Configuration
```
smtp_server=mail.yourdomain.com
smtp_port=587
smtp_use_tls=true
smtp_use_ssl=false
smtp_username=your-email@yourdomain.com
smtp_password=your-email-password
```

### SSL Configuration (Alternative)
```
smtp_server=mail.yourdomain.com
smtp_port=465
smtp_use_tls=false
smtp_use_ssl=true
smtp_username=your-email@yourdomain.com
smtp_password=your-email-password
```

### Legacy Configuration (If others don't work)
```
smtp_server=mail.yourdomain.com
smtp_port=25
smtp_use_tls=false
smtp_use_ssl=false
smtp_username=your-email@yourdomain.com
smtp_password=your-email-password
```

## 🔍 Finding Your DirectAdmin SMTP Settings

### Method 1: DirectAdmin Panel
1. Log into your DirectAdmin panel
2. Go to **Email Accounts** or **Email Management**
3. Look for **SMTP Settings** or **Outgoing Mail Server**
4. Note the server name and port

### Method 2: Check Email Client Settings
1. Look at your existing email client settings
2. Check **Outgoing Mail Server (SMTP)** settings
3. Use the same server and port

### Method 3: Contact Your Hosting Provider
Ask your hosting provider for:
- SMTP server name
- SMTP port
- Authentication requirements
- Any special settings

## 🧪 Testing Your Configuration

After setting up DirectAdmin SMTP:

```bash
# Test connection
python config/smtp_config_helper.py test

# Send test email
python config/smtp_config_helper.py send-test your-email@example.com
```

## 🚨 Common DirectAdmin Issues

### Issue 1: "Authentication failed"
**Solution**: Make sure you're using your domain email credentials, not your DirectAdmin panel credentials.

### Issue 2: "Connection refused"
**Solution**: Try different ports (587, 465, 25) or contact your hosting provider.

### Issue 3: "SSL/TLS errors"
**Solution**: Try switching between TLS (port 587) and SSL (port 465).

### Issue 4: "Relay denied"
**Solution**: Make sure you're using an email address from your domain.

## 📋 DirectAdmin Email Requirements

Most DirectAdmin providers require:
- ✅ Email address from your domain (e.g., admin@yourdomain.com)
- ✅ Valid email account password
- ✅ SMTP authentication enabled
- ✅ Proper port configuration (587 or 465)

## 🔧 Alternative DirectAdmin SMTP Servers

If `mail.yourdomain.com` doesn't work, try:
- `smtp.yourdomain.com`
- `mail.yourdomain.com`
- `smtp.yourdomain.com`
- Your hosting provider's main SMTP server

## 🆘 Still Having Issues?

### Step 1: Run Network Diagnostic
```bash
python config/network_diagnostic.py
```

### Step 2: Check DirectAdmin Panel
1. Log into DirectAdmin
2. Check **Email Accounts** section
3. Look for SMTP settings or documentation

### Step 3: Contact Support
Contact your hosting provider and ask:
1. "What SMTP server should I use for my domain?"
2. "What port should I use for SMTP?"
3. "Do you require authentication for SMTP?"
4. "Are there any firewall restrictions?"

### Step 4: Use Development Mode
If nothing works, enable development mode:
```bash
python config/enable_dev_mode.py
```

This will log emails instead of sending them.

## 📞 DirectAdmin Support Resources

- **DirectAdmin Documentation**: Check your hosting provider's documentation
- **Email Settings**: Look in your DirectAdmin panel under Email Management
- **Support Ticket**: Contact your hosting provider's support team
- **Community Forums**: DirectAdmin community forums for help

## 🎯 Quick Checklist

- [ ] Domain email account created in DirectAdmin
- [ ] SMTP server set to `mail.yourdomain.com`
- [ ] Port set to 587 (TLS) or 465 (SSL)
- [ ] Authentication enabled
- [ ] Using domain email credentials
- [ ] Tested with `python config/smtp_config_helper.py test`

## 💡 Pro Tips

1. **Use domain email**: Always use an email address from your domain
2. **Try multiple ports**: Test 587, 465, and 25
3. **Check firewall**: Some providers block certain ports
4. **Verify credentials**: Make sure your email password is correct
5. **Contact support**: DirectAdmin providers usually have good support

## 🔄 Switching Back to Gmail

If you want to switch back to Gmail later:
```bash
python config/smtp_config_helper.py setup
```

Then choose Gmail configuration and use your App Password.
