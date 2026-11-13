"""Memoize With Timeout: cache a function's results per arguments for a while."""

import functools
import time


class MWT:
    """Cache the return value of a function for ``timeout`` seconds per argument set."""

    def __init__(self, timeout=2):
        self.timeout = timeout

    def __call__(self, func):
        cache = {}

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            key = (args, tuple(sorted(kwargs.items())))

            hit = cache.get(key)
            if hit is not None and now - hit[1] < self.timeout:
                return hit[0]

            value = func(*args, **kwargs)
            cache[key] = (value, now)

            # Drop expired entries so the cache cannot grow without limit
            for k in [k for k, (_, t) in cache.items() if now - t >= self.timeout]:
                del cache[k]
            return value

        return wrapper
