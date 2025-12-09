import time
from threading import Lock
from cachetools import TTLCache

# Cache for general data (with TTL)
CACHE_TTL = 600  # seconds
_cache = TTLCache(maxsize=1000, ttl=CACHE_TTL)
_cache_lock = Lock()

# State and stats are persistent for the process lifetime
_state = {}
_stats = {}
_state_lock = Lock()
_stats_lock = Lock()

def set_cache_ttl(ttl):
    global CACHE_TTL, _cache
    CACHE_TTL = ttl
    # Recreate cache with new TTL
    with _cache_lock:
        items = dict(_cache)
        _cache = TTLCache(maxsize=1000, ttl=CACHE_TTL)
        _cache.update(items)

def get_cache(key):
    with _cache_lock:
        return _cache.get(key)

def set_cache(key, data, ttl=None):
    # TTLCache does not support per-key TTL, so we use the global TTL
    with _cache_lock:
        _cache[key] = data

def clear_cache(key):
    with _cache_lock:
        if key in _cache:
            del _cache[key]

def clear_all_cache():
    with _cache_lock:
        _cache.clear()

def get_state(chat_id):
    with _state_lock:
        return _state.get(chat_id, {}).copy()

def set_state(chat_id, state):
    with _state_lock:
        _state[chat_id] = state.copy()

def update_state(chat_id, data):
    with _state_lock:
        if chat_id not in _state:
            _state[chat_id] = {}
        _state[chat_id].update(data)

def clear_state(chat_id):
    with _state_lock:
        if chat_id in _state:
            del _state[chat_id]

def get_stats(chat_id):
    with _stats_lock:
        if chat_id not in _stats:
            _stats[chat_id] = {'messages': 0, 'time': int(time.time())}
        return _stats[chat_id].copy()

def increment_message_count(chat_id):
    with _stats_lock:
        stats = get_stats(chat_id)
        stats['messages'] += 1
        _stats[chat_id] = stats
        return stats['messages']

def has_chat_messages_quota(chat_id, max_messages, time_window):
    with _stats_lock:
        stats = get_stats(chat_id)
        now = int(time.time())
        # Reset counter if time window has passed
        if now - stats['time'] > time_window:
            _stats[chat_id] = {'messages': 0, 'time': now}
            return True
        return stats['messages'] < max_messages

def clear_stats(chat_id):
    with _stats_lock:
        if chat_id in _stats:
            del _stats[chat_id]

def get_all_data():
    with _cache_lock, _state_lock, _stats_lock:
        return {
            'cache': dict(_cache),
            'state': _state.copy(),
            'stats': _stats.copy(),
        }

def clear_all():
    clear_all_cache()
    with _state_lock:
        _state.clear()
    with _stats_lock:
        _stats.clear()

# Backward compatibility functions
def get(key, default=None):
    """Backward compatibility function for get_cache"""
    result = get_cache(key)
    return result if result is not None else default

def set(key, value):
    """Backward compatibility function for set_cache"""
    set_cache(key, value)
