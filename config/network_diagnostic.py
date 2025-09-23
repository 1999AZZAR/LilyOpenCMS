#!/usr/bin/env python3
"""
Network Diagnostic Tool for SMTP Connectivity
Helps diagnose SMTP connection issues on shared hosting providers
"""

import socket
import sys
import time
from urllib.parse import urlparse

def test_connection(host, port, timeout=10):
    """Test TCP connection to a host:port"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        return False, str(e)

def test_dns_resolution(hostname):
    """Test DNS resolution for a hostname"""
    try:
        ip = socket.gethostbyname(hostname)
        return True, ip
    except Exception as e:
        return False, str(e)

def main():
    print("🔍 SMTP Network Diagnostic Tool")
    print("=" * 50)
    
    # Test DNS resolution first
    print("\n📡 Testing DNS Resolution:")
    print("-" * 30)
    
    dns_tests = [
        "smtp.gmail.com",
        "smtp.outlook.com", 
        "smtp.yahoo.com",
        "mail.hostinger.com",
        "smtp.cpanel.net"
    ]
    
    for hostname in dns_tests:
        success, result = test_dns_resolution(hostname)
        if success:
            print(f"✅ {hostname} → {result}")
        else:
            print(f"❌ {hostname} → {result}")
    
    # Test SMTP port connectivity
    print("\n🔌 Testing SMTP Port Connectivity:")
    print("-" * 40)
    
    smtp_tests = [
        ("smtp.gmail.com", 587, "Gmail SMTP (TLS)"),
        ("smtp.gmail.com", 465, "Gmail SMTP (SSL)"),
        ("smtp.outlook.com", 587, "Outlook SMTP (TLS)"),
        ("smtp.outlook.com", 465, "Outlook SMTP (SSL)"),
        ("smtp.yahoo.com", 587, "Yahoo SMTP (TLS)"),
        ("smtp.yahoo.com", 465, "Yahoo SMTP (SSL)"),
        ("mail.hostinger.com", 587, "Hostinger SMTP (TLS)"),
        ("mail.hostinger.com", 465, "Hostinger SMTP (SSL)"),
        ("smtp.cpanel.net", 587, "cPanel SMTP (TLS)"),
        ("smtp.cpanel.net", 465, "cPanel SMTP (SSL)"),
    ]
    
    working_connections = []
    
    for host, port, description in smtp_tests:
        print(f"Testing {description} ({host}:{port})...", end=" ")
        success = test_connection(host, port, timeout=5)
        if success:
            print("✅ CONNECTED")
            working_connections.append((host, port, description))
        else:
            print("❌ BLOCKED")
    
    # Test basic internet connectivity
    print("\n🌐 Testing Basic Internet Connectivity:")
    print("-" * 40)
    
    internet_tests = [
        ("google.com", 80, "Google HTTP"),
        ("google.com", 443, "Google HTTPS"),
        ("cloudflare.com", 80, "Cloudflare HTTP"),
        ("cloudflare.com", 443, "Cloudflare HTTPS"),
    ]
    
    for host, port, description in internet_tests:
        print(f"Testing {description} ({host}:{port})...", end=" ")
        success = test_connection(host, port, timeout=5)
        if success:
            print("✅ CONNECTED")
        else:
            print("❌ BLOCKED")
    
    # Summary and recommendations
    print("\n📋 DIAGNOSTIC SUMMARY:")
    print("=" * 50)
    
    if working_connections:
        print("✅ WORKING SMTP CONNECTIONS:")
        for host, port, description in working_connections:
            print(f"   • {description} ({host}:{port})")
        
        print("\n💡 RECOMMENDATIONS:")
        print("   1. Use one of the working SMTP servers above")
        print("   2. Update your smtp_config.txt with working settings")
        print("   3. Test email sending with the working configuration")
        
        # Generate configuration suggestions
        print("\n🔧 SUGGESTED CONFIGURATIONS:")
        print("-" * 30)
        
        for host, port, description in working_connections[:3]:  # Show top 3
            if "gmail" in host.lower():
                print(f"\n📧 {description}:")
                print(f"   smtp_server={host}")
                print(f"   smtp_port={port}")
                print(f"   smtp_use_tls={'true' if port == 587 else 'false'}")
                print(f"   smtp_use_ssl={'true' if port == 465 else 'false'}")
                print(f"   # Use your Gmail App Password")
            elif "outlook" in host.lower():
                print(f"\n📧 {description}:")
                print(f"   smtp_server={host}")
                print(f"   smtp_port={port}")
                print(f"   smtp_use_tls={'true' if port == 587 else 'false'}")
                print(f"   smtp_use_ssl={'true' if port == 465 else 'false'}")
                print(f"   # Use your Outlook/Hotmail credentials")
            elif "hostinger" in host.lower():
                print(f"\n📧 {description}:")
                print(f"   smtp_server={host}")
                print(f"   smtp_port={port}")
                print(f"   smtp_use_tls={'true' if port == 587 else 'false'}")
                print(f"   smtp_use_ssl={'true' if port == 465 else 'false'}")
                print(f"   # Use your hosting provider's email credentials")
    else:
        print("❌ NO WORKING SMTP CONNECTIONS FOUND")
        print("\n🚨 POSSIBLE ISSUES:")
        print("   1. Hosting provider blocks all outbound SMTP connections")
        print("   2. Firewall rules preventing SMTP access")
        print("   3. Network configuration issues")
        
        print("\n💡 ALTERNATIVE SOLUTIONS:")
        print("   1. Contact your hosting provider for SMTP settings")
        print("   2. Use hosting provider's built-in email system")
        print("   3. Consider using a third-party email service (SendGrid, Mailgun)")
        print("   4. Use webhook-based email services")
        print("   5. Enable 'smtp_suppress_send=true' for development mode")
    
    print("\n" + "=" * 50)
    print("Diagnostic complete! Use the recommendations above to fix SMTP issues.")

if __name__ == "__main__":
    main()
