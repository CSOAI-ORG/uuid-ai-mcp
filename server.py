#!/usr/bin/env python3
"""UUID, ULID, and NanoID generation and parsing — MEOK AI Labs."""
import sys, os
sys.path.insert(0, os.path.expanduser('~/clawd/meok-labs-engine/shared'))
from auth_middleware import check_access

import json
import uuid
import time
import random
import string
from datetime import datetime, timezone
from collections import defaultdict
from mcp.server.fastmcp import FastMCP

FREE_DAILY_LIMIT = 15
_usage = defaultdict(list)


def _rl(c="anon"):
    now = datetime.now(timezone.utc)
    _usage[c] = [t for t in _usage[c] if (now - t).total_seconds() < 86400]
    if len(_usage[c]) >= FREE_DAILY_LIMIT:
        return json.dumps({"error": f"Limit {FREE_DAILY_LIMIT}/day"})
    _usage[c].append(now)
    return None


# Crockford's Base32 for ULID encoding
_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _encode_crockford(value: int, length: int) -> str:
    """Encode an integer to Crockford's Base32."""
    result = []
    for _ in range(length):
        result.append(_CROCKFORD[value & 0x1F])
        value >>= 5
    return "".join(reversed(result))


def _generate_ulid_str() -> str:
    """Generate a ULID (Universally Unique Lexicographically Sortable Identifier)."""
    now_ms = int(time.time() * 1000)
    # Timestamp: 48 bits -> 10 chars in Crockford Base32
    ts_part = _encode_crockford(now_ms, 10)
    # Randomness: 80 bits -> 16 chars
    rand_val = random.getrandbits(80)
    rand_part = _encode_crockford(rand_val, 16)
    return ts_part + rand_part


def _parse_ulid(ulid_str: str) -> dict:
    """Parse a ULID string into its timestamp and randomness components."""
    if len(ulid_str) != 26:
        return {"error": "ULID must be exactly 26 characters."}
    ulid_upper = ulid_str.upper()
    for ch in ulid_upper:
        if ch not in _CROCKFORD:
            return {"error": f"Invalid Crockford Base32 character: {ch}"}

    # Decode timestamp (first 10 chars)
    ts_val = 0
    for ch in ulid_upper[:10]:
        ts_val = (ts_val << 5) | _CROCKFORD.index(ch)

    try:
        ts_dt = datetime.fromtimestamp(ts_val / 1000, tz=timezone.utc)
        ts_iso = ts_dt.isoformat()
    except (OSError, OverflowError, ValueError):
        ts_iso = "invalid"

    return {
        "ulid": ulid_str,
        "timestamp_ms": ts_val,
        "timestamp_iso": ts_iso,
        "randomness": ulid_upper[10:],
    }


# NanoID alphabet
_NANOID_ALPHABET = "_-0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _generate_nanoid(size: int = 21, alphabet: str = None) -> str:
    """Generate a NanoID-style compact unique identifier."""
    alpha = alphabet or _NANOID_ALPHABET
    return "".join(random.choice(alpha) for _ in range(size))


mcp = FastMCP("uuid-ai-mcp", instructions="UUID, ULID, and NanoID generation by MEOK AI Labs.")


@mcp.tool(name="generate_uuid")
async def generate_uuid(version: int = 4, namespace: str = "", name: str = "", count: int = 1, api_key: str = "") -> dict:
    """Generate one or more UUIDs. Supports versions 1, 3, 4, and 5."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(api_key or "anon"):
        return err

    if version not in (1, 3, 4, 5):
        return {"error": "Supported UUID versions: 1, 3, 4, 5."}

    count = max(1, min(count, 100))

    namespace_map = {
        "dns": uuid.NAMESPACE_DNS,
        "url": uuid.NAMESPACE_URL,
        "oid": uuid.NAMESPACE_OID,
        "x500": uuid.NAMESPACE_X500,
    }

    results = []
    for _ in range(count):
        if version == 1:
            u = uuid.uuid1()
        elif version == 3:
            ns = namespace_map.get(namespace.lower(), uuid.NAMESPACE_DNS)
            n = name or "default"
            u = uuid.uuid3(ns, n)
        elif version == 5:
            ns = namespace_map.get(namespace.lower(), uuid.NAMESPACE_DNS)
            n = name or "default"
            u = uuid.uuid5(ns, n)
        else:
            u = uuid.uuid4()

        results.append({
            "uuid": str(u),
            "hex": u.hex,
            "urn": u.urn,
            "version": u.version,
            "variant": str(u.variant),
        })

    return {
        "uuids": results if count > 1 else results[0],
        "count": count,
        "version": version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@mcp.tool(name="parse_uuid")
async def parse_uuid(uuid_string: str, api_key: str = "") -> dict:
    """Parse and validate a UUID string, extracting all components."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(api_key or "anon"):
        return err

    uuid_string = uuid_string.strip()

    try:
        u = uuid.UUID(uuid_string)
    except ValueError as e:
        return {"valid": False, "error": str(e), "input": uuid_string}

    # Extract timestamp for v1 UUIDs
    timestamp_info = None
    if u.version == 1:
        # UUID v1 timestamp is 100-nanosecond intervals since Oct 15, 1582
        uuid_time = (u.time - 0x01B21DD213814000) / 1e7
        try:
            ts_dt = datetime.fromtimestamp(uuid_time, tz=timezone.utc)
            timestamp_info = {
                "timestamp_unix": round(uuid_time, 3),
                "timestamp_iso": ts_dt.isoformat(),
            }
        except (OSError, OverflowError, ValueError):
            timestamp_info = {"timestamp_unix": round(uuid_time, 3), "timestamp_iso": "out_of_range"}

    # Node info for v1
    node_info = None
    if u.version == 1:
        node_hex = format(u.node, '012x')
        node_info = {
            "node": node_hex,
            "node_formatted": ":".join(node_hex[i:i+2] for i in range(0, 12, 2)),
            "clock_seq": u.clock_seq,
        }

    # Format variants
    canonical = str(u)
    formats = {
        "canonical": canonical,
        "hex": u.hex,
        "urn": u.urn,
        "braced": "{" + canonical + "}",
        "uppercase": canonical.upper(),
        "no_hyphens": u.hex,
        "bytes_le": u.bytes_le.hex(),
    }

    return {
        "valid": True,
        "uuid": canonical,
        "version": u.version,
        "variant": str(u.variant),
        "formats": formats,
        "timestamp": timestamp_info,
        "node": node_info,
        "int_value": u.int,
        "bit_length": 128,
        "is_nil": u.int == 0,
    }


@mcp.tool(name="generate_ulid")
async def generate_ulid(count: int = 1, api_key: str = "") -> dict:
    """Generate ULID(s) - Universally Unique Lexicographically Sortable Identifiers."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(api_key or "anon"):
        return err

    count = max(1, min(count, 100))
    results = []

    for _ in range(count):
        ulid_str = _generate_ulid_str()
        parsed = _parse_ulid(ulid_str)
        results.append({
            "ulid": ulid_str,
            "timestamp_ms": parsed.get("timestamp_ms"),
            "timestamp_iso": parsed.get("timestamp_iso"),
            "lowercase": ulid_str.lower(),
        })

    return {
        "ulids": results if count > 1 else results[0],
        "count": count,
        "properties": {
            "length": 26,
            "encoding": "Crockford's Base32",
            "sortable": True,
            "timestamp_bits": 48,
            "randomness_bits": 80,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@mcp.tool(name="generate_nanoid")
async def generate_nanoid(size: int = 21, alphabet: str = "", count: int = 1, api_key: str = "") -> dict:
    """Generate NanoID(s) - compact URL-friendly unique identifiers."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(api_key or "anon"):
        return err

    if size < 2 or size > 256:
        return {"error": "Size must be between 2 and 256."}

    count = max(1, min(count, 100))
    alpha = alphabet if alphabet else None

    # Presets
    presets = {
        "default": _NANOID_ALPHABET,
        "alphanumeric": string.ascii_letters + string.digits,
        "lowercase": string.ascii_lowercase + string.digits,
        "numbers": string.digits,
        "hex": string.hexdigits[:16],
        "url_safe": _NANOID_ALPHABET,
    }

    if alpha and alpha in presets:
        alpha = presets[alpha]

    effective_alpha = alpha or _NANOID_ALPHABET

    results = []
    for _ in range(count):
        nid = _generate_nanoid(size, effective_alpha)
        results.append(nid)

    # Collision probability estimate
    alphabet_size = len(effective_alpha)
    total_combinations = alphabet_size ** size
    # Birthday paradox approximation: ~50% collision after sqrt(pi/2 * N)
    import math
    p50_ids = int(math.sqrt(math.pi / 2 * total_combinations)) if total_combinations < 10**50 else None

    return {
        "nanoids": results if count > 1 else results[0],
        "count": count,
        "properties": {
            "size": size,
            "alphabet_size": alphabet_size,
            "total_possible": str(total_combinations) if total_combinations < 10**50 else "extremely_large",
            "ids_for_50pct_collision": str(p50_ids) if p50_ids else "astronomically_large",
            "url_safe": all(c in _NANOID_ALPHABET + string.ascii_letters + string.digits for c in effective_alpha),
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@mcp.tool(name="batch_generate")
async def batch_generate(id_type: str = "uuid4", count: int = 10, api_key: str = "") -> dict:
    """Batch generate identifiers of a specified type. Efficient for bulk operations."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(api_key or "anon"):
        return err

    count = max(1, min(count, 1000))
    id_type = id_type.lower().strip()

    generators = {
        "uuid1": lambda: str(uuid.uuid1()),
        "uuid4": lambda: str(uuid.uuid4()),
        "ulid": _generate_ulid_str,
        "nanoid": lambda: _generate_nanoid(21),
        "nanoid_short": lambda: _generate_nanoid(10),
        "hex16": lambda: uuid.uuid4().hex[:16],
        "hex32": lambda: uuid.uuid4().hex,
        "short8": lambda: _generate_nanoid(8, string.ascii_lowercase + string.digits),
    }

    if id_type not in generators:
        return {
            "error": f"Unknown type: {id_type}",
            "available_types": list(generators.keys()),
        }

    start_time = time.monotonic()
    ids = [generators[id_type]() for _ in range(count)]
    elapsed_ms = round((time.monotonic() - start_time) * 1000, 2)

    # Verify uniqueness
    unique_count = len(set(ids))

    return {
        "ids": ids,
        "type": id_type,
        "count": count,
        "unique": unique_count,
        "all_unique": unique_count == count,
        "generation_time_ms": elapsed_ms,
        "available_types": list(generators.keys()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    mcp.run()
