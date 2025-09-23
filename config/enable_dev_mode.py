#!/usr/bin/env python3
"""
Quick Fix: Enable Development Mode for SMTP
This enables email logging instead of sending when SMTP is blocked
"""

import os
from pathlib import Path

def enable_dev_mode():
    """Enable development mode for SMTP"""
    config_path = Path(__file__).parent / "smtp_config.txt"
    
    if not config_path.exists():
        print("❌ smtp_config.txt not found!")
        return False
    
    # Read current config
    lines = []
    with open(config_path, 'r') as f:
        lines = f.readlines()
    
    # Update suppress_send and debug settings
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('smtp_suppress_send='):
            lines[i] = 'smtp_suppress_send=true\n'
            updated = True
        elif line.startswith('smtp_debug='):
            lines[i] = 'smtp_debug=true\n'
            updated = True
    
    # Write back to file
    with open(config_path, 'w') as f:
        f.writelines(lines)
    
    print("✅ Development mode enabled!")
    print("📝 Emails will now be logged instead of sent.")
    print("🔍 Check your application logs to see email content.")
    print()
    print("💡 To disable development mode later:")
    print("   python config/disable_dev_mode.py")
    
    return True

if __name__ == "__main__":
    enable_dev_mode()
