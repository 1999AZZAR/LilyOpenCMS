#!/usr/bin/env python3
"""
Redis Configuration Deployment Script
Helps configure Redis settings for different server environments
"""

import os
import sys
import shutil
from pathlib import Path

def create_config_for_server(server_type, username=None, custom_socket=None):
    """Create Redis configuration for a specific server type"""
    
    config_template = """# Redis Configuration File
# This file contains Redis connection settings for different server environments
# Modify these values according to your server's Redis setup

# Connection Type: 'socket' or 'tcp'
CONNECTION_TYPE=socket

# Unix Socket Path (for DirectAdmin and similar hosting)
# Common paths:
# - DirectAdmin: /home/username/.redis/redis.sock
# - cPanel: /home/username/.redis/redis.sock
# - Custom: /var/run/redis/redis.sock
REDIS_SOCKET={socket_path}

# TCP Connection Settings (fallback or primary)
REDIS_HOST=localhost
REDIS_PORT=6379

# Authentication (if required)
REDIS_PASSWORD=

# Connection Timeouts (in seconds)
SOCKET_CONNECT_TIMEOUT=1
SOCKET_TIMEOUT=1
TCP_CONNECT_TIMEOUT=2
TCP_TIMEOUT=2

# Cache Settings
CACHE_DEFAULT_TIMEOUT=300
CACHE_KEY_PREFIX=lilycms_
"""
    
    # Determine socket path based on server type
    if server_type == "directadmin":
        if not username:
            username = input("Enter your DirectAdmin username: ")
        socket_path = f"/home/{username}/.redis/redis.sock"
    elif server_type == "cpanel":
        if not username:
            username = input("Enter your cPanel username: ")
        socket_path = f"/home/{username}/.redis/redis.sock"
    elif server_type == "vps":
        socket_path = "/var/run/redis/redis.sock"
    elif server_type == "custom":
        if custom_socket:
            socket_path = custom_socket
        else:
            socket_path = input("Enter the Redis socket path: ")
    else:
        print(f"❌ Unknown server type: {server_type}")
        return False
    
    # Create config content
    config_content = config_template.format(socket_path=socket_path)
    
    # Write to file in config directory
    config_file = "config/redis_config.txt"
    os.makedirs("config", exist_ok=True)
    
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    print(f"✅ Created Redis configuration for {server_type}")
    print(f"📁 Config file: {config_file}")
    print(f"🔗 Socket path: {socket_path}")
    
    return True

def create_tcp_config(host="localhost", port=6379, password=None):
    """Create TCP-based Redis configuration"""
    
    config_content = f"""# Redis Configuration File
# This file contains Redis connection settings for different server environments
# Modify these values according to your server's Redis setup

# Connection Type: 'socket' or 'tcp'
CONNECTION_TYPE=tcp

# Unix Socket Path (for DirectAdmin and similar hosting)
# Common paths:
# - DirectAdmin: /home/username/.redis/redis.sock
# - cPanel: /home/username/.redis/redis.sock
# - Custom: /var/run/redis/redis.sock
REDIS_SOCKET=/home/username/.redis/redis.sock

# TCP Connection Settings (fallback or primary)
REDIS_HOST={host}
REDIS_PORT={port}

# Authentication (if required)
REDIS_PASSWORD={password or ''}

# Connection Timeouts (in seconds)
SOCKET_CONNECT_TIMEOUT=1
SOCKET_TIMEOUT=1
TCP_CONNECT_TIMEOUT=2
TCP_TIMEOUT=2

# Cache Settings
CACHE_DEFAULT_TIMEOUT=300
CACHE_KEY_PREFIX=lilycms_
"""
    
    config_file = "config/redis_config.txt"
    os.makedirs("config", exist_ok=True)
    
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    print(f"✅ Created TCP Redis configuration")
    print(f"📁 Config file: {config_file}")
    print(f"🌐 Host: {host}:{port}")
    
    return True

def backup_existing_config():
    """Backup existing configuration if it exists"""
    config_file = "config/redis_config.txt"
    if os.path.exists(config_file):
        backup_file = f"{config_file}.backup"
        shutil.copy2(config_file, backup_file)
        print(f"📦 Backed up existing config to: {backup_file}")
        return backup_file
    return None

def main():
    """Main deployment script"""
    print("🚀 Redis Configuration Deployment Script")
    print("=" * 50)
    
    print("\nAvailable server types:")
    print("1. DirectAdmin hosting")
    print("2. cPanel hosting")
    print("3. VPS/Dedicated server")
    print("4. Custom socket path")
    print("5. TCP connection")
    print("6. Test current configuration")
    
    choice = input("\nSelect server type (1-6): ").strip()
    
    if choice == "1":
        username = input("Enter your DirectAdmin username: ")
        create_config_for_server("directadmin", username)
    elif choice == "2":
        username = input("Enter your cPanel username: ")
        create_config_for_server("cpanel", username)
    elif choice == "3":
        create_config_for_server("vps")
    elif choice == "4":
        socket_path = input("Enter the Redis socket path: ")
        create_config_for_server("custom", custom_socket=socket_path)
    elif choice == "5":
        host = input("Enter Redis host (default: localhost): ").strip() or "localhost"
        port = input("Enter Redis port (default: 6379): ").strip() or "6379"
        password = input("Enter Redis password (optional): ").strip() or None
        create_tcp_config(host, int(port), password)
    elif choice == "6":
        print("\n🧪 Testing current configuration...")
        os.system("python test/test_redis_connection.py")
    else:
        print("❌ Invalid choice")
        return
    
    print("\n✅ Configuration deployed successfully!")
    print("\nNext steps:")
    print("1. Test the configuration: python test/test_redis_connection.py")
    print("2. Restart your application")
    print("3. Check the logs for Redis connection status")

if __name__ == "__main__":
    main() 