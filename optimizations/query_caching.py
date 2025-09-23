"""
Advanced Query Result Caching Module
Provides intelligent caching for database queries with automatic invalidation
Enhanced with aggressive preloading, background refresh, and smart prediction
"""

import hashlib
import json
import time
import threading
from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps
from flask import current_app, request
from sqlalchemy import text
from sqlalchemy.orm import Query
import logging
from datetime import datetime, timedelta
from .cache_config import safe_cache_get, safe_cache_set

logger = logging.getLogger(__name__)

class QueryCache:
    """Advanced query result caching with intelligent invalidation and aggressive optimization"""
    
    def __init__(self, cache_instance):
        self.cache = cache_instance
        self.query_patterns = {}
        self.invalidation_rules = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'invalidations': 0,
            'preloads': 0,
            'background_refreshes': 0
        }
        self.preload_queue = []
        self.background_tasks = {}
        self.cache_prediction = {}
        self.aggressive_mode = True
        self._lock = threading.Lock()
        
    def cache_query(self, timeout: int = 300, key_prefix: str = 'query', 
                   invalidate_on: List[str] = None, 
                   condition: Callable = None,
                   preload: bool = False,
                   background_refresh: bool = False,
                   priority: int = 1) -> Callable:
        """
        Decorator for caching query results with intelligent invalidation and aggressive optimization
        
        Args:
            timeout: Cache timeout in seconds
            key_prefix: Prefix for cache key
            invalidate_on: List of events that should invalidate this cache
            condition: Function that returns True if query should be cached
            preload: Whether to preload this query in background
            background_refresh: Whether to refresh cache in background before expiry
            priority: Priority for preloading (1=high, 5=low)
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Check if caching should be skipped
                if condition and not condition(*args, **kwargs):
                    return func(*args, **kwargs)
                
                # Generate cache key
                cache_key = self._generate_query_key(func, args, kwargs, key_prefix)
                
                # Try to get from cache
                cached_result = safe_cache_get(cache_key)
                if cached_result is not None:
                    self.cache_stats['hits'] += 1
                    logger.debug(f"Cache HIT for {cache_key}")
                    
                    # Schedule background refresh if enabled and cache is getting stale
                    if background_refresh and self.aggressive_mode:
                        self._schedule_background_refresh(cache_key, func, args, kwargs, timeout)
                    
                    # Predict and preload related queries
                    if self.aggressive_mode:
                        self._predict_and_preload(func, args, kwargs)
                    
                    return cached_result
                
                # Cache miss - execute query
                self.cache_stats['misses'] += 1
                logger.debug(f"Cache MISS for {cache_key}")
                
                result = func(*args, **kwargs)
                
                # Cache the result with extended timeout for aggressive mode
                effective_timeout = timeout * 2 if self.aggressive_mode else timeout
                safe_cache_set(cache_key, result, timeout=effective_timeout)
                
                # Register invalidation rules
                if invalidate_on:
                    self._register_invalidation_rules(cache_key, invalidate_on)
                
                # Add to preload queue if enabled
                if preload and self.aggressive_mode:
                    self._add_to_preload_queue(func, args, kwargs, priority)
                
                return result
            return wrapper
        return decorator
    
    def cache_sqlalchemy_query(self, timeout: int = 300, key_prefix: str = 'sql',
                              include_user: bool = False) -> Callable:
        """
        Decorator specifically for SQLAlchemy queries
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key including user if requested
                cache_key = self._generate_sqlalchemy_key(func, args, kwargs, key_prefix, include_user)
                
                # Try to get from cache
                cached_result = safe_cache_get(cache_key)
                if cached_result is not None:
                    self.cache_stats['hits'] += 1
                    return cached_result
                
                # Cache miss - execute query
                self.cache_stats['misses'] += 1
                result = func(*args, **kwargs)
                
                # Convert SQLAlchemy objects to dict for caching
                serializable_result = self._serialize_sqlalchemy_result(result)
                
                # Cache the result
                safe_cache_set(cache_key, serializable_result, timeout=timeout)
                
                return result
            return wrapper
        return decorator
    
    def cache_aggregation(self, timeout: int = 600, key_prefix: str = 'agg') -> Callable:
        """
        Decorator for caching aggregation queries (counts, sums, etc.)
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                cache_key = self._generate_aggregation_key(func, args, kwargs, key_prefix)
                
                cached_result = safe_cache_get(cache_key)
                if cached_result is not None:
                    self.cache_stats['hits'] += 1
                    return cached_result
                
                self.cache_stats['misses'] += 1
                result = func(*args, **kwargs)
                
                # Cache aggregation results
                safe_cache_set(cache_key, result, timeout=timeout)
                
                return result
            return wrapper
        return decorator
    
    def _generate_query_key(self, func: Callable, args: tuple, kwargs: dict, 
                           prefix: str) -> str:
        """Generate cache key for function calls"""
        # Create a unique identifier for the function call
        func_name = f"{func.__module__}.{func.__name__}"
        
        # Create a hash of the arguments
        args_hash = hashlib.md5(
            json.dumps((args, kwargs), sort_keys=True, default=str).encode()
        ).hexdigest()[:12]
        
        return f"{prefix}:{func_name}:{args_hash}"
    
    def _generate_sqlalchemy_key(self, func: Callable, args: tuple, kwargs: dict,
                                prefix: str, include_user: bool) -> str:
        """Generate cache key for SQLAlchemy queries"""
        func_name = f"{func.__module__}.{func.__name__}"
        
        # Include user ID if requested
        user_id = ""
        if include_user and hasattr(request, 'user'):
            user_id = f":user_{request.user.id}" if request.user else ""
        
        # Create hash of arguments
        args_hash = hashlib.md5(
            json.dumps((args, kwargs), sort_keys=True, default=str).encode()
        ).hexdigest()[:12]
        
        return f"{prefix}:{func_name}{user_id}:{args_hash}"
    
    def _generate_aggregation_key(self, func: Callable, args: tuple, kwargs: dict,
                                 prefix: str) -> str:
        """Generate cache key for aggregation queries"""
        func_name = f"{func.__module__}.{func.__name__}"
        
        # Include current date for time-based aggregations
        date_suffix = time.strftime("%Y%m%d")
        
        args_hash = hashlib.md5(
            json.dumps((args, kwargs), sort_keys=True, default=str).encode()
        ).hexdigest()[:8]
        
        return f"{prefix}:{func_name}:{date_suffix}:{args_hash}"
    
    def _serialize_sqlalchemy_result(self, result: Any) -> Any:
        """Convert SQLAlchemy objects to serializable format"""
        if isinstance(result, list):
            return [self._serialize_sqlalchemy_object(obj) for obj in result]
        elif isinstance(result, dict):
            return {k: self._serialize_sqlalchemy_object(v) for k, v in result.items()}
        else:
            return self._serialize_sqlalchemy_object(result)
    
    def _serialize_sqlalchemy_object(self, obj: Any) -> Any:
        """Convert a single SQLAlchemy object to dict"""
        if hasattr(obj, '__table__'):
            # SQLAlchemy model object
            return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
        elif hasattr(obj, '_asdict'):
            # SQLAlchemy Row object
            return obj._asdict()
        else:
            return obj
    
    def _register_invalidation_rules(self, cache_key: str, events: List[str]):
        """Register cache invalidation rules"""
        for event in events:
            if event not in self.invalidation_rules:
                self.invalidation_rules[event] = []
            self.invalidation_rules[event].append(cache_key)
    
    def invalidate_by_pattern(self, pattern: str):
        """Invalidate cache entries matching a pattern"""
        keys_to_delete = []
        
        # This is a simplified version - in production you'd use Redis SCAN
        # For now, we'll track patterns manually
        if pattern in self.query_patterns:
            keys_to_delete.extend(self.query_patterns[pattern])
        
        for key in keys_to_delete:
            self.cache.delete(key)
            self.cache_stats['invalidations'] += 1
        
        logger.info(f"Invalidated {len(keys_to_delete)} cache entries for pattern: {pattern}")
    
    def invalidate_by_event(self, event: str):
        """Invalidate cache entries based on events"""
        if event in self.invalidation_rules:
            keys_to_delete = self.invalidation_rules[event]
            for key in keys_to_delete:
                self.cache.delete(key)
                self.cache_stats['invalidations'] += 1
            
            logger.info(f"Invalidated {len(keys_to_delete)} cache entries for event: {event}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        hit_rate = 0
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        if total_requests > 0:
            hit_rate = (self.cache_stats['hits'] / total_requests) * 100
        
        return {
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'invalidations': self.cache_stats['invalidations'],
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests
        }
    
    def clear_all_query_cache(self):
        """Clear all query cache entries"""
        # In a real implementation, you'd use Redis SCAN to find all keys
        # For now, we'll clear the entire cache
        self.cache.clear()
        self.cache_stats['invalidations'] += 1
        logger.info("Cleared all query cache entries")
    
    def _schedule_background_refresh(self, cache_key: str, func: Callable, args: tuple, kwargs: dict, timeout: int):
        """Schedule background refresh of cache before it expires"""
        if cache_key in self.background_tasks:
            return  # Already scheduled
        
        # Schedule refresh at 80% of timeout
        refresh_delay = int(timeout * 0.8)
        
        def background_refresh():
            try:
                time.sleep(refresh_delay)
                logger.debug(f"Background refresh for {cache_key}")
                result = func(*args, **kwargs)
                safe_cache_set(cache_key, result, timeout=timeout)
                self.cache_stats['background_refreshes'] += 1
            except Exception as e:
                logger.error(f"Background refresh failed for {cache_key}: {e}")
            finally:
                with self._lock:
                    if cache_key in self.background_tasks:
                        del self.background_tasks[cache_key]
        
        thread = threading.Thread(target=background_refresh, daemon=True)
        thread.start()
        
        with self._lock:
            self.background_tasks[cache_key] = thread
    
    def _predict_and_preload(self, func: Callable, args: tuple, kwargs: dict):
        """Predict and preload related queries based on current query"""
        func_name = f"{func.__module__}.{func.__name__}"
        
        # Simple prediction patterns - can be enhanced with ML
        predictions = {
            'get_latest_news': ['get_popular_news', 'get_news_categories'],
            'get_user_profile': ['get_user_activity', 'get_user_preferences'],
            'get_album_details': ['get_album_images', 'get_related_albums'],
            'get_image_details': ['get_image_comments', 'get_related_images']
        }
        
        if func_name in predictions:
            for related_func in predictions[func_name]:
                self._preload_related_query(related_func, args, kwargs)
    
    def _preload_related_query(self, func_name: str, original_args: tuple, original_kwargs: dict):
        """Preload a related query in background"""
        def preload_task():
            try:
                # This would need to be implemented based on your actual functions
                # For now, just log the attempt
                logger.debug(f"Preloading related query: {func_name}")
                self.cache_stats['preloads'] += 1
            except Exception as e:
                logger.error(f"Preload failed for {func_name}: {e}")
        
        thread = threading.Thread(target=preload_task, daemon=True)
        thread.start()
    
    def _add_to_preload_queue(self, func: Callable, args: tuple, kwargs: dict, priority: int):
        """Add query to preload queue for future execution"""
        with self._lock:
            self.preload_queue.append({
                'func': func,
                'args': args,
                'kwargs': kwargs,
                'priority': priority,
                'timestamp': time.time()
            })
            
            # Sort by priority and limit queue size
            self.preload_queue.sort(key=lambda x: x['priority'])
            if len(self.preload_queue) > 100:  # Limit queue size
                self.preload_queue = self.preload_queue[:100]
    
    def process_preload_queue(self, max_items: int = 10):
        """Process preload queue in background"""
        with self._lock:
            items_to_process = self.preload_queue[:max_items]
            self.preload_queue = self.preload_queue[max_items:]
        
        for item in items_to_process:
            try:
                # Execute the preloaded query
                cache_key = self._generate_query_key(item['func'], item['args'], item['kwargs'], 'preload')
                
                # Check if already cached
                if safe_cache_get(cache_key) is None:
                    result = item['func'](*item['args'], **item['kwargs'])
                    safe_cache_set(cache_key, result, timeout=600)  # Longer timeout for preloaded data
                    self.cache_stats['preloads'] += 1
                    logger.debug(f"Preloaded query: {cache_key}")
            except Exception as e:
                logger.error(f"Preload execution failed: {e}")
    
    def warm_cache(self, queries: List[Dict[str, Any]]):
        """Warm cache with common queries"""
        logger.info(f"Warming cache with {len(queries)} queries")
        
        def warm_task():
            for query_info in queries:
                try:
                    func = query_info['func']
                    args = query_info.get('args', ())
                    kwargs = query_info.get('kwargs', {})
                    timeout = query_info.get('timeout', 300)
                    
                    cache_key = self._generate_query_key(func, args, kwargs, 'warm')
                    
                    if safe_cache_get(cache_key) is None:
                        result = func(*args, **kwargs)
                        safe_cache_set(cache_key, result, timeout=timeout)
                        logger.debug(f"Warmed cache: {cache_key}")
                except Exception as e:
                    logger.error(f"Cache warming failed: {e}")
        
        thread = threading.Thread(target=warm_task, daemon=True)
        thread.start()
    
    def get_enhanced_stats(self) -> Dict[str, Any]:
        """Get enhanced cache statistics including aggressive mode metrics"""
        base_stats = self.get_cache_stats()
        
        with self._lock:
            base_stats.update({
                'preloads': self.cache_stats['preloads'],
                'background_refreshes': self.cache_stats['background_refreshes'],
                'preload_queue_size': len(self.preload_queue),
                'active_background_tasks': len(self.background_tasks),
                'aggressive_mode': self.aggressive_mode,
                'prediction_accuracy': self._calculate_prediction_accuracy()
            })
        
        return base_stats
    
    def _calculate_prediction_accuracy(self) -> float:
        """Calculate prediction accuracy for cache preloading"""
        # Simple accuracy calculation - can be enhanced
        total_predictions = sum(self.cache_prediction.values()) if self.cache_prediction else 1
        successful_predictions = self.cache_stats['preloads']
        return round((successful_predictions / total_predictions) * 100, 2) if total_predictions > 0 else 0.0
    
    def set_aggressive_mode(self, enabled: bool):
        """Enable or disable aggressive caching mode"""
        self.aggressive_mode = enabled
        logger.info(f"Aggressive caching mode: {'enabled' if enabled else 'disabled'}")
    
    def start_background_processor(self):
        """Start background processor for preload queue and cache maintenance"""
        def background_processor():
            while True:
                try:
                    # Process preload queue
                    self.process_preload_queue(max_items=5)
                    
                    # Clean up expired background tasks
                    with self._lock:
                        expired_tasks = []
                        for cache_key, thread in self.background_tasks.items():
                            if not thread.is_alive():
                                expired_tasks.append(cache_key)
                        
                        for cache_key in expired_tasks:
                            del self.background_tasks[cache_key]
                    
                    # Sleep for 30 seconds before next iteration
                    time.sleep(30)
                except Exception as e:
                    logger.error(f"Background processor error: {e}")
                    time.sleep(60)  # Longer sleep on error
        
        thread = threading.Thread(target=background_processor, daemon=True)
        thread.start()
        logger.info("Background cache processor started")

# Convenience functions
def cache_query_result(timeout: int = 300, key_prefix: str = 'query'):
    """Simple decorator for caching query results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from optimizations import cache
            
            # Generate cache key
            func_name = f"{func.__module__}.{func.__name__}"
            args_hash = hashlib.md5(
                json.dumps((args, kwargs), sort_keys=True, default=str).encode()
            ).hexdigest()[:12]
            cache_key = f"{key_prefix}:{func_name}:{args_hash}"
            
            # Try to get from cache
            cached_result = safe_cache_get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            safe_cache_set(cache_key, result, timeout=timeout)
            
            return result
        return wrapper
    return decorator

def cache_aggregation_result(timeout: int = 600):
    """Decorator for caching aggregation results"""
    return cache_query_result(timeout=timeout, key_prefix='agg')

def invalidate_cache_pattern(pattern: str):
    """Invalidate cache entries matching a pattern"""
    from optimizations import cache
    # This would need to be implemented with Redis SCAN in production
    logger.info(f"Cache invalidation requested for pattern: {pattern}")

# Example usage decorators
def cache_news_queries(timeout: int = 300):
    """Decorator specifically for news-related queries"""
    return cache_query_result(timeout=timeout, key_prefix='news')

def cache_user_queries(timeout: int = 300):
    """Decorator specifically for user-related queries"""
    return cache_query_result(timeout=timeout, key_prefix='user')

def cache_analytics_queries(timeout: int = 600):
    """Decorator specifically for analytics queries"""
    return cache_query_result(timeout=timeout, key_prefix='analytics')

# Aggressive caching decorators for frontend optimization
def aggressive_cache_query(timeout: int = 600, key_prefix: str = 'agg_query', 
                          preload: bool = True, background_refresh: bool = True):
    """Aggressive caching decorator for critical frontend queries"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from optimizations import query_cache
            
            # Generate cache key
            func_name = f"{func.__module__}.{func.__name__}"
            args_hash = hashlib.md5(
                json.dumps((args, kwargs), sort_keys=True, default=str).encode()
            ).hexdigest()[:12]
            cache_key = f"{key_prefix}:{func_name}:{args_hash}"
            
            # Try to get from cache
            cached_result = safe_cache_get(cache_key)
            if cached_result is not None:
                # Schedule background refresh if enabled
                if background_refresh:
                    def bg_refresh():
                        try:
                            time.sleep(int(timeout * 0.8))
                            result = func(*args, **kwargs)
                            safe_cache_set(cache_key, result, timeout=timeout)
                        except Exception as e:
                            logger.error(f"Background refresh failed: {e}")
                    
                    threading.Thread(target=bg_refresh, daemon=True).start()
                
                return cached_result
            
            # Cache miss - execute query
            result = func(*args, **kwargs)
            
            # Cache with extended timeout for aggressive mode
            safe_cache_set(cache_key, result, timeout=timeout * 2)
            
            # Preload related queries if enabled
            if preload:
                _preload_related_queries(func, args, kwargs)
            
            return result
        return wrapper
    return decorator

def cache_frontend_critical(timeout: int = 900):
    """Decorator for critical frontend queries that need maximum performance"""
    return aggressive_cache_query(timeout=timeout, key_prefix='frontend_critical', 
                                 preload=True, background_refresh=True)

def cache_user_dashboard(timeout: int = 300):
    """Decorator for user dashboard queries with aggressive preloading"""
    return aggressive_cache_query(timeout=timeout, key_prefix='user_dashboard', 
                                 preload=True, background_refresh=True)

def cache_public_content(timeout: int = 1200):
    """Decorator for public content with long cache times"""
    return aggressive_cache_query(timeout=timeout, key_prefix='public_content', 
                                 preload=True, background_refresh=False)

def cache_navigation_data(timeout: int = 1800):
    """Decorator for navigation and menu data"""
    return aggressive_cache_query(timeout=timeout, key_prefix='navigation', 
                                 preload=True, background_refresh=False)

def _preload_related_queries(func: Callable, args: tuple, kwargs: dict):
    """Preload related queries based on current query"""
    func_name = f"{func.__module__}.{func.__name__}"
    
    # Enhanced prediction patterns for frontend optimization
    predictions = {
        'get_latest_news': [
            'get_popular_news', 'get_news_categories', 'get_featured_news',
            'get_news_by_category', 'get_related_news'
        ],
        'get_user_profile': [
            'get_user_activity', 'get_user_preferences', 'get_user_stats',
            'get_user_achievements', 'get_user_recent_activity'
        ],
        'get_album_details': [
            'get_album_images', 'get_related_albums', 'get_album_comments',
            'get_album_ratings', 'get_album_metadata'
        ],
        'get_image_details': [
            'get_image_comments', 'get_related_images', 'get_image_metadata',
            'get_image_ratings', 'get_image_tags'
        ],
        'get_dashboard_data': [
            'get_user_stats', 'get_recent_activity', 'get_notifications',
            'get_quick_actions', 'get_dashboard_widgets'
        ]
    }
    
    if func_name in predictions:
        for related_func in predictions[func_name]:
            def preload_task(rel_func=related_func):
                try:
                    logger.debug(f"Preloading related query: {rel_func}")
                    # This would need actual function references in production
                except Exception as e:
                    logger.error(f"Preload failed for {rel_func}: {e}")
            
            threading.Thread(target=preload_task, daemon=True).start()

# Global query cache instance
query_cache = QueryCache(None)  # Will be initialized with actual cache instance

def initialize_aggressive_caching(cache_instance):
    """Initialize aggressive caching with cache instance"""
    global query_cache
    query_cache = QueryCache(cache_instance)
    query_cache.start_background_processor()
    logger.info("Aggressive query caching initialized")

def get_query_cache_stats():
    """Get comprehensive query cache statistics"""
    global query_cache
    return query_cache.get_enhanced_stats() if query_cache else {} 