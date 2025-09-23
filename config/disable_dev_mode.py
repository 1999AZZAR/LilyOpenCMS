#!/usr/bin/env python3
"""
Disable Development Mode for SMTP
This disables email logging and enables actual email sending
"""

import os
from pathlib import Path

def disable_dev_mode():
    """Disable development mode for SMTP"""
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
            lines[i] = 'smtp_suppress_send=false\n'
            updated = True
        elif line.startswith('smtp_debug='):
            lines[i] = 'smtp_debug=false\n'
            updated = True
    
    # Write back to file
    with open(config_path, 'w') as f:
        f.writelines(lines)
    
    print("✅ Development mode disabled!")
    print("📧 Emails will now be sent normally.")
    print()
    print("⚠️  Make sure your SMTP configuration is working before disabling dev mode.")
    
    return True

if __name__ == "__main__":
    disable_dev_mode()
