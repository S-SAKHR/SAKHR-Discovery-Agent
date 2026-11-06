import time
import random
import logging
import requests
from typing import Optional, Dict, Any

# In-memory search cache with TTL
_SEARCH_CACHE = {}
_CACHE_TTL = 3600  # 1 hour


def get_cached_search(cache_key: str):
    if cache_key in _SEARCH_CACHE:
        entry = _SEARCH_CACHE[cache_key]
        if time.time() - entry["time"] < _CACHE_TTL:
            return entry["data"]
        else:
            del _SEARCH_CACHE[cache_key]
    return None


def set_cached_search(cache_key: str, data: Any):
    _SEARCH_CACHE[cache_key] = {
        "time": time.time(),
        "data": data
    }


def robust_request(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Any] = None,
    timeout: int = 30,
    max_retries: int = 3,
    source_name: str = "api"
) -> Optional[requests.Response]:
    """
    Executes an HTTP request with exponential backoff, random jitter,
    Retry-After header handling for HTTP 429 and 503, timeouts,
    and secure logging without exposing credentials.
    """
    base_delay = 1.0
    for attempt in range(max_retries + 1):
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data,
                timeout=timeout
            )
            
            # Respect Retry-After and backoff for 429 / 503
            if response.status_code in [429, 503]:
                retry_after = response.headers.get("Retry-After")
                delay = base_delay * (2 ** attempt) + random.uniform(0.1, 0.5)
                if retry_after:
                    try:
                        delay = max(float(retry_after), delay)
                    except ValueError:
                        pass
                
                print(f"[{source_name}] HTTP {response.status_code} received. Retrying in {delay:.2f}s (attempt {attempt+1}/{max_retries})...")
                if attempt < max_retries:
                    time.sleep(delay)
                    continue

            # Server errors
            if response.status_code >= 500:
                delay = base_delay * (2 ** attempt) + random.uniform(0.1, 0.5)
                print(f"[{source_name}] Server error HTTP {response.status_code}. Retrying in {delay:.2f}s (attempt {attempt+1}/{max_retries})...")
                if attempt < max_retries:
                    time.sleep(delay)
                    continue

            return response
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            delay = base_delay * (2 ** attempt) + random.uniform(0.1, 0.5)
            print(f"[{source_name}] Network/Timeout error: {type(e).__name__}. Retrying in {delay:.2f}s (attempt {attempt+1}/{max_retries})...")
            if attempt < max_retries:
                time.sleep(delay)
                continue
            raise
        except Exception as e:
            print(f"[{source_name}] Request failed: {type(e).__name__} (credentials masked)")
            raise
    return None
