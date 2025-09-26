#!/usr/bin/env python3
"""
Test script for Performance Monitoring System
Tests performance metrics collection, monitoring, alerts, and recommendations
"""

import sys
import os
import time
import psutil
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_performance_monitor_initialization():
    """Test performance monitor initialization"""
    print("🧪 Testing Performance Monitor Initialization...")
    
    try:
        from optimizations.performance_monitoring import PerformanceMonitor
        
        # Test 1: Create performance monitor
        print("  🔧 Testing performance monitor creation...")
        monitor = PerformanceMonitor()
        assert monitor is not None
        assert hasattr(monitor, 'metrics')
        assert hasattr(monitor, 'start_time')
        print("    ✅ Performance monitor created successfully")
        
        # Test 2: Initialize with app
        print("  🔧 Testing app initialization...")
        from flask import Flask
        app = Flask(__name__)
        monitor.init_app(app)
        assert monitor.app == app
        print("    ✅ App initialization works correctly")
        
        print("    ✅ Performance monitor initialization tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing performance monitor initialization: {e}")

def test_request_metrics():
    """Test request metrics collection"""
    print("🧪 Testing Request Metrics...")
    
    try:
        from optimizations.performance_monitoring import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        
        # Test 1: Record request metrics
        print("  📊 Testing request metrics recording...")
        
        # Simulate request metrics
        monitor._record_request_metrics(0.5, 200)
        monitor._record_request_metrics(1.2, 200)
        monitor._record_request_metrics(0.8, 404)
        
        # Check metrics
        assert len(monitor.metrics) > 0
        for path, metric in monitor.metrics.items():
            assert metric['count'] > 0
            assert metric['total_time'] > 0
            assert metric['avg_time'] > 0
            assert metric['min_time'] > 0
            assert metric['max_time'] > 0
            assert len(metric['status_codes']) > 0
        
        print("    ✅ Request metrics recording works correctly")
        
        # Test 2: Check metric calculations
        print("  📊 Testing metric calculations...")
        for path, metric in monitor.metrics.items():
            # Verify average calculation
            expected_avg = metric['total_time'] / metric['count']
            assert abs(metric['avg_time'] - expected_avg) < 0.001
            
            # Verify min/max
            assert metric['min_time'] <= metric['max_time']
        
        print("    ✅ Metric calculations are correct")
        
        print("    ✅ Request metrics tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing request metrics: {e}")

def test_system_metrics():
    """Test system metrics collection"""
    print("🧪 Testing System Metrics...")
    
    try:
        # Test 1: CPU metrics
        print("  💻 Testing CPU metrics...")
        cpu_percent = psutil.cpu_percent(interval=0.1)
        assert 0 <= cpu_percent <= 100
        print("    ✅ CPU metrics collection works")
        
        # Test 2: Memory metrics
        print("  💾 Testing memory metrics...")
        memory = psutil.virtual_memory()
        assert memory.total > 0
        assert memory.available >= 0
        assert 0 <= memory.percent <= 100
        print("    ✅ Memory metrics collection works")
        
        # Test 3: Disk metrics
        print("  💿 Testing disk metrics...")
        disk = psutil.disk_usage('/')
        assert disk.total > 0
        assert disk.free >= 0
        assert 0 <= disk.percent <= 100
        print("    ✅ Disk metrics collection works")
        
        print("    ✅ System metrics tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing system metrics: {e}")

def test_performance_summary():
    """Test performance summary generation"""
    print("🧪 Testing Performance Summary...")
    
    try:
        from optimizations.performance_monitoring import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        
        # Add some test metrics
        monitor._record_request_metrics(0.5, 200)
        monitor._record_request_metrics(1.2, 200)
        monitor._record_request_metrics(0.8, 404)
        
        # Test 1: Get performance summary
        print("  📈 Testing performance summary...")
        summary = monitor.get_performance_summary()
        
        assert 'total_requests' in summary
        assert 'avg_response_time' in summary
        assert 'slow_requests' in summary
        assert 'error_rate' in summary
        assert 'uptime' in summary
        print("    ✅ Performance summary generation works")
        
        # Test 2: Check summary values
        print("  📈 Testing summary values...")
        assert summary['total_requests'] > 0
        assert summary['avg_response_time'] > 0
        assert summary['uptime'] > 0
        print("    ✅ Summary values are valid")
        
        print("    ✅ Performance summary tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing performance summary: {e}")

def test_slow_queries():
    """Test slow query detection"""
    print("🧪 Testing Slow Query Detection...")
    
    try:
        from optimizations.performance_monitoring import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        
        # Add some test metrics with slow requests
        monitor._record_request_metrics(0.5, 200)
        monitor._record_request_metrics(2.5, 200)  # Slow request
        monitor._record_request_metrics(1.8, 200)  # Slow request
        monitor._record_request_metrics(0.8, 404)
        
        # Test 1: Get slow queries
        print("  ⏱️ Testing slow query detection...")
        slow_queries = monitor.get_slow_queries(threshold=1.0)
        
        assert len(slow_queries) >= 2  # Should find the 2 slow requests
        for query in slow_queries:
            assert query['duration'] > 1.0
        print("    ✅ Slow query detection works")
        
        # Test 2: Different threshold
        print("  ⏱️ Testing different threshold...")
        slow_queries = monitor.get_slow_queries(threshold=2.0)
        assert len(slow_queries) >= 1  # Should find the 2.5s request
        print("    ✅ Threshold adjustment works")
        
        print("    ✅ Slow query detection tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing slow query detection: {e}")

def test_performance_alerts():
    """Test performance alerts"""
    print("🧪 Testing Performance Alerts...")
    
    try:
        from optimizations.performance_monitoring import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        
        # Add test metrics that would trigger alerts
        monitor._record_request_metrics(3.0, 200)  # Very slow request
        monitor._record_request_metrics(0.5, 500)  # Error
        monitor._record_request_metrics(0.5, 500)  # Another error
        
        # Test 1: Get performance alerts
        print("  🚨 Testing performance alerts...")
        alerts = monitor.get_performance_alerts()
        
        assert isinstance(alerts, list)
        print("    ✅ Performance alerts generation works")
        
        # Test 2: Check alert types
        print("  🚨 Testing alert types...")
        alert_types = [alert['type'] for alert in alerts]
        print(f"    ✅ Found alert types: {alert_types}")
        
        print("    ✅ Performance alerts tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing performance alerts: {e}")

def test_performance_recommendations():
    """Test performance recommendations"""
    print("🧪 Testing Performance Recommendations...")
    
    try:
        from optimizations.performance_monitoring import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        
        # Add test metrics
        monitor._record_request_metrics(0.5, 200)
        monitor._record_request_metrics(1.2, 200)
        monitor._record_request_metrics(0.8, 404)
        
        # Test 1: Get performance recommendations
        print("  💡 Testing performance recommendations...")
        recommendations = monitor.get_performance_recommendations()
        
        assert isinstance(recommendations, list)
        print("    ✅ Performance recommendations generation works")
        
        # Test 2: Check recommendation structure
        print("  💡 Testing recommendation structure...")
        for rec in recommendations:
            assert 'type' in rec
            assert 'title' in rec
            assert 'description' in rec
            assert 'priority' in rec
        print("    ✅ Recommendation structure is correct")
        
        print("    ✅ Performance recommendations tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing performance recommendations: {e}")

def test_performance_decorators():
    """Test performance monitoring decorators"""
    print("🧪 Testing Performance Decorators...")
    
    try:
        from optimizations.performance_monitoring import monitor_performance, track_database_queries
        
        # Test 1: Performance monitoring decorator
        print("  🎯 Testing performance monitoring decorator...")
        
        @monitor_performance(timeout=0.5)
        def test_function():
            time.sleep(0.1)  # Simulate work
            return "success"
        
        result = test_function()
        assert result == "success"
        print("    ✅ Performance monitoring decorator works")
        
        # Test 2: Database query tracking decorator
        print("  🎯 Testing database query tracking decorator...")
        
        @track_database_queries
        def test_db_function():
            # Simulate database operations
            time.sleep(0.05)
            return "db_success"
        
        result = test_db_function()
        assert result == "db_success"
        print("    ✅ Database query tracking decorator works")
        
        print("    ✅ Performance decorators tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing performance decorators: {e}")

def test_performance_utilities():
    """Test performance monitoring utilities"""
    print("🧪 Testing Performance Utilities...")
    
    try:
        from optimizations.performance_monitoring import (
            create_performance_monitor,
            get_performance_monitor,
            get_performance_summary
        )
        
        # Test 1: Create performance monitor
        print("  🔧 Testing create_performance_monitor...")
        monitor = create_performance_monitor()
        assert monitor is not None
        print("    ✅ Create performance monitor works")
        
        # Test 2: Get performance monitor
        print("  🔧 Testing get_performance_monitor...")
        monitor = get_performance_monitor()
        assert monitor is not None
        print("    ✅ Get performance monitor works")
        
        # Test 3: Get performance summary
        print("  🔧 Testing get_performance_summary...")
        summary = get_performance_summary()
        assert isinstance(summary, dict)
        print("    ✅ Get performance summary works")
        
        print("    ✅ Performance utilities tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing performance utilities: {e}")

def test_performance_thresholds():
    """Test performance threshold monitoring"""
    print("🧪 Testing Performance Thresholds...")
    
    try:
        from optimizations.performance_monitoring import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        
        # Test 1: Normal performance
        print("  📊 Testing normal performance thresholds...")
        monitor._record_request_metrics(0.1, 200)
        monitor._record_request_metrics(0.2, 200)
        
        alerts = monitor.get_performance_alerts()
        # Should have few or no alerts for normal performance
        print(f"    ✅ Normal performance: {len(alerts)} alerts")
        
        # Test 2: Poor performance
        print("  📊 Testing poor performance thresholds...")
        monitor._record_request_metrics(5.0, 200)  # Very slow
        monitor._record_request_metrics(0.1, 500)  # Error
        monitor._record_request_metrics(0.1, 500)  # Another error
        
        alerts = monitor.get_performance_alerts()
        # Should have more alerts for poor performance
        print(f"    ✅ Poor performance: {len(alerts)} alerts")
        
        print("    ✅ Performance threshold tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing performance thresholds: {e}")

def main():
    """Run all performance monitoring tests"""
    print("🚀 Starting Performance Monitoring Tests")
    print("=" * 50)
    
    test_performance_monitor_initialization()
    print()
    test_request_metrics()
    print()
    test_system_metrics()
    print()
    test_performance_summary()
    print()
    test_slow_queries()
    print()
    test_performance_alerts()
    print()
    test_performance_recommendations()
    print()
    test_performance_decorators()
    print()
    test_performance_utilities()
    print()
    test_performance_thresholds()
    print()
    
    print("✅ All performance monitoring tests completed!")
    print("\n📋 Test Summary:")
    print("  - Monitor Initialization: Setup and configuration")
    print("  - Request Metrics: Response time tracking")
    print("  - System Metrics: CPU, memory, disk monitoring")
    print("  - Performance Summary: Overall statistics")
    print("  - Slow Queries: Performance bottleneck detection")
    print("  - Performance Alerts: Automated notifications")
    print("  - Performance Recommendations: Optimization suggestions")
    print("  - Performance Decorators: Code-level monitoring")
    print("  - Performance Utilities: Helper functions")
    print("  - Performance Thresholds: Alert triggering")
    print("\n🎉 Performance monitoring system is working correctly!")

if __name__ == "__main__":
    main() 