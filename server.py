#!/usr/bin/env python3
import uuid, json
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("uuid-ai-mcp")
@mcp.tool(name="generate_uuid")
async def generate_uuid(version: int = 4) -> str:
    return json.dumps({"uuid": str(uuid.uuid4()) if version == 4 else str(uuid.uuid1())})
@mcp.tool(name="validate_uuid")
async def validate_uuid(u: str) -> str:
    try:
        uuid.UUID(u)
        return json.dumps({"valid": True, "version": uuid.UUID(u).version})
    except ValueError:
        return json.dumps({"valid": False})
if __name__ == "__main__":
    mcp.run()
