# Gmail SMTP Setup Guide

This guide will help you set up Gmail SMTP for your LilyOpenCMS application.

## 🔧 Step 1: Enable 2-Factor Authentication

Gmail requires 2-Factor Authentication (2FA) to use App Passwords:

1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Click on **Security** in the left sidebar
3. Under "Signing in to Google", click **2-Step Verification**
4. Follow the prompts to enable 2FA (you'll need your phone)

## 🔑 Step 2: Generate App Password

1. Go back to [Google Account Settings](https://myaccount.google.com/)
2. Click on **Security** → **2-Step Verification**
3. Scroll down to **App passwords**
4. Click **App passwords**
5. Select **Mail** as the app
6. Select **Other (custom name)** as the device
7. Enter "LilyOpenCMS" as the name
8. Click **Generate**
9. **Copy the 16-character password** (it looks like: `abcd efgh ijkl mnop`)

## 📧 Step 3: Update Configuration

Edit `config/smtp_config.txt` and replace:

```ini
# Replace these with your actual Gmail details
smtp_username=your-email@gmail.com
smtp_password=your-app-password
mail_default_sender=your-email@gmail.com
mail_reply_to=your-email@gmail.com
```

**Example:**
```ini
smtp_username=john.doe@gmail.com
smtp_password=abcd efgh ijkl mnop
mail_default_sender=john.doe@gmail.com
mail_reply_to=john.doe@gmail.com
```

## 🧪 Step 4: Test the Configuration

Run the test command:

```bash
python config/smtp_config_helper.py test
```

If successful, you should see:
```
✅ SMTP connection test successful
```

## 📨 Step 5: Send Test Email

Send a test email to yourself:

```bash
python config/smtp_config_helper.py send-test your-email@gmail.com
```

## ⚠️ Important Notes

1. **Use App Password**: Never use your regular Gmail password
2. **Keep it Secret**: Don't share your App Password
3. **Rate Limits**: Gmail has daily sending limits (500 emails/day for free accounts)
4. **Security**: The App Password is specific to this application

## 🔒 Security Best Practices

1. **Environment Variables**: For production, store credentials in environment variables
2. **Restrict Access**: Only use this Gmail account for your application
3. **Monitor Usage**: Check Gmail's security settings regularly
4. **Backup**: Keep a backup of your App Password in a secure location

## 🚨 Troubleshooting

### "Authentication Failed"
- Make sure you're using the App Password, not your regular password
- Verify 2FA is enabled on your Gmail account
- Check that the App Password was copied correctly

### "Connection Refused"
- Check your internet connection
- Verify Gmail SMTP settings are correct
- Try port 465 with SSL instead of 587 with TLS

### "Too Many Requests"
- Gmail has rate limits, wait a few minutes and try again
- Consider using a different email service for high volume

## 📊 Gmail Limits

- **Free Gmail**: 500 emails/day, 100 emails/hour
- **Google Workspace**: 2000 emails/day, 100 emails/hour
- **Recipients**: 500 recipients per email

## 🎯 Ready to Use!

Once configured, your LilyOpenCMS will automatically:
- Send verification emails during user registration
- Handle password reset emails
- Apply rate limiting to prevent abuse
- Log all email activity

Your email system is now ready for production use! 🎉
