#!/usr/bin/env python3
"""
Redis Connection Test Script
Tests Redis availability and provides fallback options
"""

import os
import sys

def get_redis_config():
    """Get Redis configuration from text file or environment variables"""
    try:
        from routes.utils.config_reader import get_redis_config
        return get_redis_config()
    except ImportError:
        # Fallback to environment variables
        return {
            'connection_type': os.getenv('REDIS_CONNECTION_TYPE', 'socket'),
            'socket_path': os.getenv('REDIS_SOCKET', '/home/username/.redis/redis.sock'),
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', 6379)),
            'password': os.getenv('REDIS_PASSWORD', None),
            'socket_connect_timeout': 2,
            'socket_timeout': 2,
            'tcp_connect_timeout': 2,
            'tcp_timeout': 2
        }

def test_redis_connection():
    """Test if Redis is available"""
    try:
        import redis
        print("✅ Redis module is available")
        
        # Get configuration
        redis_config = get_redis_config()
        connection_type = redis_config.get('connection_type', 'socket')
        
        print(f"🔍 Connection type: {connection_type}")
        
        if connection_type == 'socket':
            socket_path = redis_config.get('socket_path')
            print(f"🔍 Testing Unix socket: {socket_path}")
            
            if not socket_path:
                print("❌ No socket path configured")
                return False
                
            if not os.path.exists(socket_path):
                print(f"❌ Socket file not found: {socket_path}")
                return False
                
            try:
                # Test Unix socket connection
                client = redis.Redis(
                    unix_socket_path=socket_path,
                    password=redis_config.get('password'),
                    socket_connect_timeout=redis_config.get('socket_connect_timeout', 2),
                    socket_timeout=redis_config.get('socket_timeout', 2)
                )
                
                # Test ping
                response = client.ping()
                client.close()
                
                if response:
                    print("✅ Redis connection successful via Unix socket")
                    return True
                else:
                    print("❌ Redis ping failed via Unix socket")
                    return False
            except Exception as socket_error:
                print(f"❌ Unix socket connection failed: {socket_error}")
        
        # Fallback to TCP connection
        host = redis_config.get('host', 'localhost')
        port = redis_config.get('port', 6379)
        print(f"🔍 Testing TCP connection: {host}:{port}")
        
        try:
            client = redis.Redis(
                host=host,
                port=port,
                password=redis_config.get('password'),
                socket_connect_timeout=redis_config.get('tcp_connect_timeout', 2),
                socket_timeout=redis_config.get('tcp_timeout', 2)
            )
            
            # Test ping
            response = client.ping()
            client.close()
            
            if response:
                print("✅ Redis connection successful via TCP")
                return True
            else:
                print("❌ Redis ping failed via TCP")
                return False
        except Exception as tcp_error:
            print(f"❌ TCP connection failed: {tcp_error}")
            return False
            
    except ImportError:
        print("❌ Redis module not installed")
        return False
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

def check_configuration():
    """Check Redis configuration"""
    print("\n🔍 Checking Redis configuration:")
    
    try:
        from routes.utils.config_reader import ConfigReader
        reader = ConfigReader()
        reader.print_config()
        
        # Validate configuration
        if reader.validate_config():
            print("✅ Configuration is valid")
        else:
            print("❌ Configuration has issues")
            
    except ImportError:
        print("⚠️  Config reader not available, using environment variables")
        redis_config = get_redis_config()
        print("📋 Current Redis Configuration:")
        print("=" * 40)
        for key, value in redis_config.items():
            print(f"{key}: {value}")
        print("=" * 40)

def provide_solutions():
    """Provide solutions for Redis issues"""
    print("\n💡 Solutions:")
    print("1. Edit the configuration file:")
    print("   - Open config/redis_config.txt")
    print("   - Modify REDIS_SOCKET path for your server")
    print("   - Change CONNECTION_TYPE if needed")
    
    print("\n2. Common socket paths:")
    print("   - DirectAdmin: /home/username/.redis/redis.sock")
    print("   - cPanel: /home/username/.redis/redis.sock")
    print("   - VPS: /var/run/redis/redis.sock")
    
    print("\n3. For TCP connection:")
    print("   - Set CONNECTION_TYPE=tcp")
    print("   - Configure REDIS_HOST and REDIS_PORT")
    
    print("\n4. The application will automatically fall back to simple caching")
    print("   when Redis is not available (no action needed)")
    
    print("\n5. For DirectAdmin hosting:")
    print("   - Contact your hosting provider to enable Redis")
    print("   - Or use a managed Redis service (Redis Cloud, AWS ElastiCache, etc.)")

if __name__ == "__main__":
    print("🔧 Redis Connection Test")
    print("=" * 40)
    
    check_configuration()
    
    print("\n🧪 Testing Redis connection...")
    redis_available = test_redis_connection()
    
    if redis_available:
        print("\n✅ Redis is working correctly!")
        print("Your application should work with full caching capabilities.")
    else:
        print("\n⚠️  Redis is not available")
        print("The application will use simple in-memory caching as fallback.")
        provide_solutions() 