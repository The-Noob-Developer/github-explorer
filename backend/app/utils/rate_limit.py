"""Shared `slowapi` rate limiter instance.

Limits are applied per-client-IP (`get_remote_address`) and only ever
attached to `/api/search` (Section 10) -- `/api/facts` and `/api/health` are
left unlimited since they are cheap, local, and useful for uptime probes.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
