from trisigma import command
from trisigma import secondary

@command.expose()
def cache(key: str):
    """Cache a value in the current context"""
    try:
        cache = secondary.CacheMemcached()
        print(cache[key])
    except ConnectionRefusedError:
        print("No connection to cache daemon")
