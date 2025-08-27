"""
Cache Configuration and Utilities
Handles Redis caching setup and provides cache decorators for performance optimization
"""

import os
from functools import wraps
from flask import request, current_app
from flask_caching import Cache
import hashlib
import json
from datetime import timedelta
import logging

# Initialize cache
cache = Cache()

def init_cache(app):
    """Initialize cache with Redis configuration from text file"""
    # Import config reader
    try:
        from routes.utils.config_reader import get_redis_config
        redis_config = get_redis_config()
    except ImportError:
        app.logger.warning("Config reader not available, using environment variables")
        redis_config = {
            'connection_type': 'socket',
            'socket_path': os.getenv('REDIS_SOCKET', '/home/newenerg/.redis/redis.sock'),
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', 6379)),
            'password': os.getenv('REDIS_PASSWORD', None),
            'socket_connect_timeout': 1,
            'socket_timeout': 1,
            'tcp_connect_timeout': 2,
            'tcp_timeout': 2,
            'cache_default_timeout': 300,
            'cache_key_prefix': 'lilycms_'
        }
    
    # Check if Redis is available
    redis_available = True
    try:
        import redis
        
        # Test connection based on configuration
        test_client = None
        connection_type = redis_config.get('connection_type', 'socket')
        
        if connection_type == 'socket':
            socket_path = redis_config.get('socket_path')
            if socket_path and os.path.exists(socket_path):
                try:
                    # Test Unix socket connection
                    test_client = redis.Redis(
                        unix_socket_path=socket_path,
                        password=redis_config.get('password'),
                        socket_connect_timeout=redis_config.get('socket_connect_timeout', 1),
                        socket_timeout=redis_config.get('socket_timeout', 1)
                    )
                    test_client.ping()
                    app.logger.info(f"✅ Redis connected via Unix socket: {socket_path}")
                except Exception as socket_error:
                    app.logger.warning(f"Unix socket connection failed: {socket_error}")
                    # Fallback to TCP connection
                    try:
                        test_client = redis.Redis(
                            host=redis_config.get('host', 'localhost'),
                            port=redis_config.get('port', 6379),
                            password=redis_config.get('password'),
                            socket_connect_timeout=redis_config.get('tcp_connect_timeout', 2),
                            socket_timeout=redis_config.get('tcp_timeout', 2)
                        )
                        test_client.ping()
                        app.logger.info(f"✅ Redis connected via TCP: {redis_config.get('host')}:{redis_config.get('port')}")
                    except Exception as tcp_error:
                        redis_available = False
                        app.logger.warning(f"Redis not available (TCP also failed): {tcp_error}")
            else:
                app.logger.warning(f"Redis socket file not found: {socket_path}")
                redis_available = False
        else:
            # TCP connection
            try:
                test_client = redis.Redis(
                    host=redis_config.get('host', 'localhost'),
                    port=redis_config.get('port', 6379),
                    password=redis_config.get('password'),
                    socket_connect_timeout=redis_config.get('tcp_connect_timeout', 2),
                    socket_timeout=redis_config.get('tcp_timeout', 2)
                )
                test_client.ping()
                app.logger.info(f"✅ Redis connected via TCP: {redis_config.get('host')}:{redis_config.get('port')}")
            except Exception as tcp_error:
                redis_available = False
                app.logger.warning(f"Redis not available: {tcp_error}")
        
        if test_client:
            test_client.close()
            
    except Exception as e:
        redis_available = False
        app.logger.warning(f"Redis not available, falling back to simple cache: {e}")
    
    if redis_available:
        # Use configuration from text file
        if connection_type == 'socket' and redis_config.get('socket_path') and os.path.exists(redis_config.get('socket_path')):
            cache_config = {
                'CACHE_TYPE': 'redis',
                'CACHE_REDIS_URL': f'unix://{redis_config.get("socket_path")}',
                'CACHE_DEFAULT_TIMEOUT': redis_config.get('cache_default_timeout', 300),
                'CACHE_KEY_PREFIX': redis_config.get('cache_key_prefix', 'lilycms_'),
                'CACHE_REDIS_PASSWORD': redis_config.get('password'),
                'CACHE_REDIS_UNIX_SOCKET_PATH': redis_config.get('socket_path'),
            }
        else:
            cache_config = {
                'CACHE_TYPE': 'redis',
                'CACHE_REDIS_URL': f'redis://{redis_config.get("host", "localhost")}:{redis_config.get("port", 6379)}/0',
                'CACHE_DEFAULT_TIMEOUT': redis_config.get('cache_default_timeout', 300),
                'CACHE_KEY_PREFIX': redis_config.get('cache_key_prefix', 'lilycms_'),
                'CACHE_REDIS_DB': 0,
                'CACHE_REDIS_PASSWORD': redis_config.get('password'),
                'CACHE_REDIS_HOST': redis_config.get('host', 'localhost'),
                'CACHE_REDIS_PORT': redis_config.get('port', 6379),
            }
    else:
        # Fallback to simple cache when Redis is not available
        cache_config = {
            'CACHE_TYPE': 'simple',
            'CACHE_DEFAULT_TIMEOUT': redis_config.get('cache_default_timeout', 300),
            'CACHE_KEY_PREFIX': redis_config.get('cache_key_prefix', 'lilycms_'),
        }
    
    app.config.update(cache_config)
    cache.init_app(app)

def generate_cache_key(prefix, *args, **kwargs):
    """Generate a unique cache key based on function arguments"""
    # Convert args and kwargs to a string representation
    key_parts = [prefix]
    
    if args:
        key_parts.extend([str(arg) for arg in args])
    
    if kwargs:
        # Sort kwargs to ensure consistent key generation
        sorted_kwargs = sorted(kwargs.items())
        key_parts.extend([f"{k}:{v}" for k, v in sorted_kwargs])
    
    # Add request-specific data for dynamic content
    if request:
        key_parts.append(f"user:{request.remote_addr}")
        if hasattr(request, 'user') and request.user:
            key_parts.append(f"user_id:{request.user.id}")
    
    # Create hash of the key parts
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()

def safe_cache_get(cache_key):
    """Safely get from cache with error handling"""
    try:
        return cache.get(cache_key)
    except Exception as e:
        current_app.logger.warning(f"Cache get failed for key {cache_key}: {e}")
        return None

def safe_cache_set(cache_key, value, timeout=300):
    """Safely set cache with error handling"""
    try:
        cache.set(cache_key, value, timeout=timeout)
        return True
    except Exception as e:
        current_app.logger.warning(f"Cache set failed for key {cache_key}: {e}")
        return False

def cache_with_args(timeout=300, key_prefix='view'):
    """Decorator to cache function results with dynamic key generation"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key based on function name and arguments
            cache_key = generate_cache_key(f"{key_prefix}_{func.__name__}", *args, **kwargs)
            
            # Try to get from cache
            cached_result = safe_cache_get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # If not in cache, execute function and cache result
            result = func(*args, **kwargs)
            safe_cache_set(cache_key, result, timeout=timeout)
            return result
        return wrapper
    return decorator

def cache_query_result(timeout=300):
    """Decorator specifically for database query results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key including query parameters
            cache_key = generate_cache_key(f"query_{func.__name__}", *args, **kwargs)
            
            # Try to get from cache
            cached_result = safe_cache_get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # If not in cache, execute query and cache result
            result = func(*args, **kwargs)
            
            # Convert SQLAlchemy objects to dict for caching
            if hasattr(result, '__iter__') and not isinstance(result, (str, bytes, dict, list)):
                # Handle SQLAlchemy query results
                if hasattr(result, 'all'):
                    result = [item.to_dict() if hasattr(item, 'to_dict') else item for item in result.all()]
                else:
                    result = [item.to_dict() if hasattr(item, 'to_dict') else item for item in result]
            elif hasattr(result, 'to_dict'):
                result = result.to_dict()
            
            safe_cache_set(cache_key, result, timeout=timeout)
            return result
        return wrapper
    return decorator

def invalidate_cache_pattern(pattern):
    """Invalidate all cache keys matching a pattern"""
    try:
        # Get all keys matching the pattern
        keys = cache.cache._client.keys(f"lilycms_{pattern}*")
        if keys:
            cache.cache._client.delete(*keys)
            return True
    except Exception as e:
        current_app.logger.error(f"Error invalidating cache pattern {pattern}: {e}")
        return False

def clear_all_cache():
    """Clear all cache entries"""
    try:
        cache.clear()
        return True
    except Exception as e:
        current_app.logger.error(f"Error clearing cache: {e}")
        return False

# Cache timeouts for different types of content
CACHE_TIMEOUTS = {
    'news_list': 300,      # 5 minutes for news lists
    'news_detail': 600,    # 10 minutes for individual news
    'categories': 1800,    # 30 minutes for categories
    'images': 3600,        # 1 hour for images
    'analytics': 60,       # 1 minute for analytics
    'user_data': 300,      # 5 minutes for user data
    'static_content': 7200, # 2 hours for static content
}

# Cache key patterns for easy invalidation
CACHE_PATTERNS = {
    'news': 'news_',
    'categories': 'categories_',
    'images': 'images_',
    'users': 'users_',
    'analytics': 'analytics_',
} 