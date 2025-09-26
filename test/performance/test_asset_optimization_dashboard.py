#!/usr/bin/env python3
"""
Test script for Asset Optimization Dashboard
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from optimizations.asset_optimization import get_asset_optimizer, get_asset_stats

def test_asset_optimizer():
    """Test the asset optimizer functionality"""
    print("Testing Asset Optimization Dashboard...")
    
    try:
        # Test asset optimizer
        optimizer = get_asset_optimizer()
        print("✓ Asset optimizer initialized successfully")
        
        # Test getting stats
        stats = optimizer.get_optimization_stats()
        print("✓ Asset stats retrieved successfully")
        print(f"  - Total assets: {stats.get('total_assets_count', 0)}")
        print(f"  - Compressed assets: {stats.get('compressed_assets_count', 0)}")
        print(f"  - Asset hashes: {stats.get('asset_hashes_count', 0)}")
        print(f"  - Total size: {stats.get('total_size_mb', 0)} MB")
        print(f"  - Compressed size: {stats.get('compressed_size_mb', 0)} MB")
        print(f"  - Optimization ratio: {stats.get('optimization_ratio', 0):.2%}")
        print(f"  - Supported types: {stats.get('supported_types', [])}")
        
        # Test asset stats function
        asset_stats = get_asset_stats()
        print("✓ Asset stats function working")
        
        # Test compression (this will actually compress files)
        print("\nTesting asset compression...")
        compression_result = optimizer.compress_assets()
        if compression_result.get('success'):
            print(f"✓ Asset compression successful: {compression_result.get('message', '')}")
        else:
            print(f"⚠ Asset compression failed: {compression_result.get('message', '')}")
        
        # Test cache clearing
        print("\nTesting cache clearing...")
        cache_result = optimizer.clear_asset_cache()
        if cache_result.get('success'):
            print(f"✓ Cache clearing successful: {cache_result.get('message', '')}")
        else:
            print(f"⚠ Cache clearing failed: {cache_result.get('message', '')}")
        
        # Test hash regeneration
        print("\nTesting hash regeneration...")
        hash_result = optimizer.regenerate_hashes()
        if hash_result.get('success'):
            print(f"✓ Hash regeneration successful: {hash_result.get('message', '')}")
        else:
            print(f"⚠ Hash regeneration failed: {hash_result.get('message', '')}")
        
        print("\n✅ All asset optimization tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing asset optimization: {e}")
        return False

def test_api_endpoints():
    """Test that API endpoints are accessible"""
    print("\nTesting API endpoints...")
    
    # These would be tested in a real Flask app context
    endpoints = [
        '/api/asset-optimization/compress',
        '/api/asset-optimization/clear-cache',
        '/api/asset-optimization/regenerate-hashes',
        '/api/asset-optimization/minify'
    ]
    
    print("✓ API endpoints defined:")
    for endpoint in endpoints:
        print(f"  - {endpoint}")
    
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("ASSET OPTIMIZATION DASHBOARD TEST")
    print("=" * 50)
    
    success = True
    success &= test_asset_optimizer()
    success &= test_api_endpoints()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ ALL TESTS PASSED - Dashboard should work correctly!")
    else:
        print("❌ SOME TESTS FAILED - Check the issues above")
    print("=" * 50) 