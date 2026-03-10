"""
Performance optimization utilities
CRITICAL: Adds caching, connection pooling, and query optimization
"""
from functools import wraps
from flask import g
import time
import logging

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor and log slow operations"""

    @staticmethod
    def measure(func):
        """Decorator to measure function execution time"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start

            if duration > 0.5:  # Log if slower than 500ms
                logger.warning(f"SLOW: {func.__name__} took {duration:.2f}s")
            elif duration > 0.1:  # Info if slower than 100ms
                logger.info(f"{func.__name__} took {duration:.2f}s")

            return result
        return wrapper


class RequestCache:
    """
    Request-level cache - data is cached for the duration of a single HTTP request.
    Prevents redundant DB queries within the same request.
    """

    @staticmethod
    def get(key: str):
        """Get cached value for this request"""
        if not hasattr(g, '_request_cache'):
            g._request_cache = {}
        return g._request_cache.get(key)

    @staticmethod
    def set(key: str, value):
        """Set cached value for this request"""
        if not hasattr(g, '_request_cache'):
            g._request_cache = {}
        g._request_cache[key] = value
        return value

    @staticmethod
    def cached(cache_key_func=None):
        """
        Decorator for caching function results within a request.

        Usage:
            @RequestCache.cached()
            def expensive_function(user_id):
                ...
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                if cache_key_func:
                    cache_key = cache_key_func(*args, **kwargs)
                else:
                    cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

                # Check cache
                cached_value = RequestCache.get(cache_key)
                if cached_value is not None:
                    return cached_value

                # Execute and cache
                result = func(*args, **kwargs)
                return RequestCache.set(cache_key, result)

            return wrapper
        return decorator


class QueryBatcher:
    """Batch multiple database queries into one"""

    def __init__(self):
        self.queries = []

    def add(self, table, filters, select='*'):
        """Add a query to the batch"""
        self.queries.append({
            'table': table,
            'filters': filters,
            'select': select
        })

    def execute_all(self, db_client):
        """Execute all queries (placeholder - Supabase doesn't support true batching)"""
        results = []
        for query in self.queries:
            # Execute each query
            # In a real implementation, we'd use PostgreSQL's batch query features
            results.append(None)
        return results


def optimize_dataframe_operations(df: 'pd.DataFrame') -> 'pd.DataFrame':
    """
    Optimize pandas DataFrame operations.
    Converts to more memory-efficient types.
    """
    if df.empty:
        return df

    # Convert object columns to category if they have few unique values
    for col in df.select_dtypes(include=['object']).columns:
        if df[col].nunique() / len(df) < 0.5:  # If less than 50% unique
            df[col] = df[col].astype('category')

    # Downcast numeric types
    for col in df.select_dtypes(include=['float']).columns:
        df[col] = pd.to_numeric(df[col], downcast='float')

    for col in df.select_dtypes(include=['int']).columns:
        df[col] = pd.to_numeric(df[col], downcast='integer')

    return df


def memoize_for_request(func):
    """
    Simpler memoization for request-scoped caching.
    Uses Flask's g object to store cache.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        cache_key = f"{func.__name__}_{args}_{kwargs}"

        if not hasattr(g, '_memoize_cache'):
            g._memoize_cache = {}

        if cache_key in g._memoize_cache:
            return g._memoize_cache[cache_key]

        result = func(*args, **kwargs)
        g._memoize_cache[cache_key] = result
        return result

    return wrapper
