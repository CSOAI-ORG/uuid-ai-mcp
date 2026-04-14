#!/usr/bin/env python3

import sys, os
sys.path.insert(0, os.path.expanduser('~/clawd/meok-labs-engine/shared'))
from auth_middleware import check_access

import uuid, json
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("uuid-ai-mcp")
@mcp.tool(name="generate_uuid")
async def generate_uuid(version: int = 4, api_key: str = "") -> str:
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    return {"uuid": str(uuid.uuid4()) if version == 4 else str(uuid.uuid1())}
    return {"uuid": str(uuid.uuid4()) if version == 4 else str(uuid.uuid1())}
@mcp.tool(name="validate_uuid")
async def validate_uuid(u: str, api_key: str = "") -> str:
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    try:
        uuid.UUID(u)
        return {"valid": True, "version": uuid.UUID(u).version}
    except ValueError:
        return {"valid": False}
if __name__ == "__main__":
    mcp.run()
