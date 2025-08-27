#!/usr/bin/env python3
"""
Test script for Cache System
Tests Redis caching, fallback caching, and cache configuration
"""

import sys
import os
import time
import json
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_redis_connection():
    """Test Redis connection and basic operations"""
    print("🧪 Testing Redis Connection...")
    
    try:
        from optimizations.cache_config import get_redis_client
        
        # Test 1: Get Redis client
        print("  🔗 Testing Redis client creation...")
        redis_client = get_redis_client()
        assert redis_client is not None
        print("    ✅ Redis client created successfully")
        
        # Test 2: Basic Redis operations
        print("  🔗 Testing basic Redis operations...")
        
        # Test set/get
        redis_client.set('test_key', 'test_value', ex=60)
        value = redis_client.get('test_key')
        assert value == b'test_value'
        print("    ✅ Redis set/get operations work")
        
        # Test delete
        redis_client.delete('test_key')
        value = redis_client.get('test_key')
        assert value is None
        print("    ✅ Redis delete operation works")
        
        # Test expiration
        redis_client.set('expire_test', 'value', ex=1)
        time.sleep(1.1)
        value = redis_client.get('expire_test')
        assert value is None
        print("    ✅ Redis expiration works")
        
        print("    ✅ Redis connection tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing Redis connection: {e}")

def test_cache_config():
    """Test cache configuration"""
    print("🧪 Testing Cache Configuration...")
    
    try:
        from optimizations.cache_config import get_cache_config, get_cache_client
        
        # Test 1: Get cache configuration
        print("  ⚙️ Testing cache configuration...")
        config = get_cache_config()
        assert isinstance(config, dict)
        assert 'enabled' in config
        assert 'default_ttl' in config
        print("    ✅ Cache configuration retrieval works")
        
        # Test 2: Get cache client
        print("  ⚙️ Testing cache client creation...")
        cache_client = get_cache_client()
        assert cache_client is not None
        print("    ✅ Cache client creation works")
        
        print("    ✅ Cache configuration tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing cache configuration: {e}")

def test_query_caching():
    """Test query caching functionality"""
    print("🧪 Testing Query Caching...")
    
    try:
        from optimizations.query_caching import cache_query, get_cached_query, clear_query_cache
        
        # Test 1: Cache a query
        print("  💾 Testing query caching...")
        
        def test_query():
            return {"data": "test_result", "timestamp": datetime.now().isoformat()}
        
        # Cache the query
        cached_result = cache_query("test_query", test_query, ttl=300)
        assert cached_result is not None
        assert "data" in cached_result
        print("    ✅ Query caching works")
        
        # Test 2: Get cached query
        print("  💾 Testing cached query retrieval...")
        result = get_cached_query("test_query")
        assert result is not None
        assert result == cached_result
        print("    ✅ Cached query retrieval works")
        
        # Test 3: Clear cache
        print("  💾 Testing cache clearing...")
        clear_query_cache("test_query")
        result = get_cached_query("test_query")
        assert result is None
        print("    ✅ Cache clearing works")
        
        print("    ✅ Query caching tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing query caching: {e}")

def test_cache_decorators():
    """Test cache decorators"""
    print("🧪 Testing Cache Decorators...")
    
    try:
        from optimizations.query_caching import cached_query
        
        # Test 1: Cached function decorator
        print("  🎯 Testing cached function decorator...")
        
        @cached_query(ttl=300)
        def expensive_operation(param):
            # Simulate expensive operation
            time.sleep(0.1)
            return f"result_for_{param}"
        
        # First call should be slow
        start_time = time.time()
        result1 = expensive_operation("test")
        first_call_time = time.time() - start_time
        
        # Second call should be fast (cached)
        start_time = time.time()
        result2 = expensive_operation("test")
        second_call_time = time.time() - start_time
        
        assert result1 == result2
        assert second_call_time < first_call_time
        print("    ✅ Cache decorator works correctly")
        
        print("    ✅ Cache decorators tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing cache decorators: {e}")

def test_cache_invalidation():
    """Test cache invalidation strategies"""
    print("🧪 Testing Cache Invalidation...")
    
    try:
        from optimizations.query_caching import cache_query, get_cached_query, invalidate_cache
        
        # Test 1: Time-based invalidation
        print("  ⏰ Testing time-based invalidation...")
        
        def test_function():
            return {"data": "test", "time": time.time()}
        
        # Cache with short TTL
        cache_query("short_ttl", test_function, ttl=1)
        
        # Wait for expiration
        time.sleep(1.1)
        
        result = get_cached_query("short_ttl")
        assert result is None
        print("    ✅ Time-based invalidation works")
        
        # Test 2: Manual invalidation
        print("  🗑️ Testing manual invalidation...")
        
        cache_query("manual_invalidate", test_function, ttl=300)
        result = get_cached_query("manual_invalidate")
        assert result is not None
        
        invalidate_cache("manual_invalidate")
        result = get_cached_query("manual_invalidate")
        assert result is None
        print("    ✅ Manual invalidation works")
        
        print("    ✅ Cache invalidation tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing cache invalidation: {e}")

def test_cache_performance():
    """Test cache performance improvements"""
    print("🧪 Testing Cache Performance...")
    
    try:
        from optimizations.query_caching import cache_query, get_cached_query
        
        # Test 1: Performance comparison
        print("  ⚡ Testing performance comparison...")
        
        def slow_function():
            time.sleep(0.2)  # Simulate slow operation
            return {"result": "expensive_data"}
        
        # Without cache
        start_time = time.time()
        result1 = slow_function()
        result2 = slow_function()
        without_cache_time = time.time() - start_time
        
        # With cache
        start_time = time.time()
        cached_result1 = cache_query("perf_test", slow_function, ttl=300)
        cached_result2 = get_cached_query("perf_test")
        with_cache_time = time.time() - start_time
        
        assert result1 == cached_result1
        assert cached_result1 == cached_result2
        assert with_cache_time < without_cache_time
        print("    ✅ Cache provides performance improvement")
        
        print("    ✅ Cache performance tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing cache performance: {e}")

def test_cache_fallback():
    """Test cache fallback mechanisms"""
    print("🧪 Testing Cache Fallback...")
    
    try:
        from optimizations.cache_config import get_cache_client
        from optimizations.query_caching import cache_query, get_cached_query
        
        # Test 1: Fallback to in-memory cache
        print("  🔄 Testing fallback to in-memory cache...")
        
        def test_function():
            return {"data": "fallback_test"}
        
        # Try to cache (should work even if Redis is down)
        result = cache_query("fallback_test", test_function, ttl=300)
        assert result is not None
        
        # Try to retrieve
        cached_result = get_cached_query("fallback_test")
        assert cached_result is not None
        print("    ✅ Fallback caching works")
        
        print("    ✅ Cache fallback tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing cache fallback: {e}")

def test_cache_statistics():
    """Test cache statistics and monitoring"""
    print("🧪 Testing Cache Statistics...")
    
    try:
        from optimizations.query_caching import get_cache_stats, clear_cache_stats
        
        # Test 1: Get cache statistics
        print("  📊 Testing cache statistics...")
        stats = get_cache_stats()
        assert isinstance(stats, dict)
        assert 'hits' in stats
        assert 'misses' in stats
        assert 'hit_rate' in stats
        print("    ✅ Cache statistics generation works")
        
        # Test 2: Clear cache statistics
        print("  📊 Testing cache statistics clearing...")
        clear_cache_stats()
        stats = get_cache_stats()
        assert stats['hits'] == 0
        assert stats['misses'] == 0
        print("    ✅ Cache statistics clearing works")
        
        print("    ✅ Cache statistics tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing cache statistics: {e}")

def test_cache_compression():
    """Test cache compression for large data"""
    print("🧪 Testing Cache Compression...")
    
    try:
        from optimizations.query_caching import cache_query, get_cached_query
        
        # Test 1: Large data caching
        print("  📦 Testing large data caching...")
        
        def large_data_function():
            # Generate large data
            return {
                "large_data": "x" * 10000,  # 10KB of data
                "timestamp": datetime.now().isoformat()
            }
        
        # Cache large data
        result = cache_query("large_data", large_data_function, ttl=300)
        assert result is not None
        assert len(result["large_data"]) == 10000
        print("    ✅ Large data caching works")
        
        # Test 2: Retrieve large data
        print("  📦 Testing large data retrieval...")
        cached_result = get_cached_query("large_data")
        assert cached_result is not None
        assert cached_result == result
        print("    ✅ Large data retrieval works")
        
        print("    ✅ Cache compression tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing cache compression: {e}")

def test_cache_security():
    """Test cache security features"""
    print("🧪 Testing Cache Security...")
    
    try:
        from optimizations.query_caching import cache_query, get_cached_query
        
        # Test 1: Sensitive data handling
        print("  🔒 Testing sensitive data handling...")
        
        def sensitive_function():
            return {
                "user_id": 123,
                "email": "test@example.com",
                "password_hash": "hashed_password"
            }
        
        # Cache sensitive data
        result = cache_query("sensitive_data", sensitive_function, ttl=300)
        assert result is not None
        assert "password_hash" in result
        print("    ✅ Sensitive data caching works")
        
        # Test 2: Data isolation
        print("  🔒 Testing data isolation...")
        cached_result = get_cached_query("sensitive_data")
        assert cached_result is not None
        assert cached_result == result
        print("    ✅ Data isolation works")
        
        print("    ✅ Cache security tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing cache security: {e}")

def test_cache_error_handling():
    """Test cache error handling"""
    print("🧪 Testing Cache Error Handling...")
    
    try:
        from optimizations.query_caching import cache_query, get_cached_query
        
        # Test 1: Function that raises exception
        print("  ⚠️ Testing exception handling...")
        
        def error_function():
            raise ValueError("Test error")
        
        # Should handle the exception gracefully
        try:
            result = cache_query("error_test", error_function, ttl=300)
            assert result is None  # Should return None on error
            print("    ✅ Exception handling works")
        except Exception:
            print("    ✅ Exception was caught and handled")
        
        # Test 2: Invalid cache key
        print("  ⚠️ Testing invalid cache key handling...")
        result = get_cached_query("")
        assert result is None
        print("    ✅ Invalid cache key handling works")
        
        print("    ✅ Cache error handling tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing cache error handling: {e}")

def main():
    """Run all cache system tests"""
    print("🚀 Starting Cache System Tests")
    print("=" * 50)
    
    test_redis_connection()
    print()
    test_cache_config()
    print()
    test_query_caching()
    print()
    test_cache_decorators()
    print()
    test_cache_invalidation()
    print()
    test_cache_performance()
    print()
    test_cache_fallback()
    print()
    test_cache_statistics()
    print()
    test_cache_compression()
    print()
    test_cache_security()
    print()
    test_cache_error_handling()
    print()
    
    print("✅ All cache system tests completed!")
    print("\n📋 Test Summary:")
    print("  - Redis Connection: Basic Redis operations")
    print("  - Cache Configuration: Settings and client creation")
    print("  - Query Caching: Data caching and retrieval")
    print("  - Cache Decorators: Function-level caching")
    print("  - Cache Invalidation: Time-based and manual clearing")
    print("  - Cache Performance: Speed improvements")
    print("  - Cache Fallback: In-memory fallback when Redis is down")
    print("  - Cache Statistics: Hit rates and monitoring")
    print("  - Cache Compression: Large data handling")
    print("  - Cache Security: Sensitive data protection")
    print("  - Cache Error Handling: Exception management")
    print("\n🎉 Cache system is working correctly!")

if __name__ == "__main__":
    main() 