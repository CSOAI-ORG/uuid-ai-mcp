#!/usr/bin/env python3
"""Generate and validate UUIDs. — MEOK AI Labs."""
import json, os, re, hashlib, uuid as _uuid, random
from datetime import datetime, timezone
from collections import defaultdict
from mcp.server.fastmcp import FastMCP

FREE_DAILY_LIMIT = 30
_usage = defaultdict(list)
def _rl(c="anon"):
    now = datetime.now(timezone.utc)
    _usage[c] = [t for t in _usage[c] if (now-t).total_seconds() < 86400]
    if len(_usage[c]) >= FREE_DAILY_LIMIT: return json.dumps({"error": "Limit/day"})
    _usage[c].append(now); return None

mcp = FastMCP("uuid", instructions="MEOK AI Labs — Generate and validate UUIDs.")


@mcp.tool()
def generate_uuid(version: int = 4) -> str:
    """Generate a UUID."""
    if err := _rl(): return err
    u = str(_uuid.uuid4()) if version == 4 else str(_uuid.uuid1())
    return json.dumps({"uuid": u, "version": version, "hex": u.replace("-", ""), "urn": f"urn:uuid:{u}"}, indent=2)

@mcp.tool()
def validate_uuid(uuid_string: str) -> str:
    """Validate a UUID string."""
    if err := _rl(): return err
    try:
        val = _uuid.UUID(uuid_string)
        return json.dumps({"valid": True, "uuid": str(val), "version": val.version, "variant": str(val.variant)}, indent=2)
    except:
        return json.dumps({"valid": False, "error": "Invalid UUID format"}, indent=2)

if __name__ == "__main__":
    mcp.run()
