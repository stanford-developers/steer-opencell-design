from flask_caching import Cache
import hashlib
import json


class MyCache:

    def __init__(self):

        self.cache = Cache()
        self._hit_count = 0
        self._miss_count = 0
    
    def init_app(self, app):

        config = {
            'CACHE_TYPE': 'SimpleCache',  # Start with SimpleCache for development
            'CACHE_DEFAULT_TIMEOUT': 30000,  # 500 minutes
            'CACHE_KEY_PREFIX': 'opencell_'
        }
        
        # For production, you can switch to Redis:
        # config = {
        #     'CACHE_TYPE': 'RedisCache',
        #     'CACHE_REDIS_URL': 'redis://localhost:6379/0',
        #     'CACHE_DEFAULT_TIMEOUT': 30000,
        #     'CACHE_KEY_PREFIX': 'opencell_'
        # }
        
        self.cache.init_app(app, config)
    
    def memoize_with_hash(self, timeout=300):
        """Custom memoization with object hashing."""
        def decorator(f):
            def wrapper(*args, **kwargs):
                # Create hash of function arguments
                key_data = {
                    'func': f.__name__,
                    'args': str(args),
                    'kwargs': str(sorted(kwargs.items()))
                }
                cache_key = hashlib.md5(
                    json.dumps(key_data, sort_keys=True).encode()
                ).hexdigest()
                
                # Try to get from cache
                result = self.cache.get(cache_key)
                if result is not None:
                    self._hit_count += 1
                    return result
                
                # Execute function and cache result
                self._miss_count += 1
                result = f(*args, **kwargs)
                self.cache.set(cache_key, result, timeout=timeout)
                return result
            return wrapper
        return decorator
    
    def get_stats(self):
        total = self._hit_count + self._miss_count
        hit_rate = self._hit_count / total if total > 0 else 0
        return {
            'hits': self._hit_count,
            'misses': self._miss_count,
            'hit_rate': hit_rate
        }
    
    def __getattr__(self, name):
        """Proxy all unknown methods to the underlying cache object."""
        return getattr(self.cache, name)

    
    
cache = MyCache()  # New advanced cache

