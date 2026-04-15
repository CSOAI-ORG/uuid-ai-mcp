# Uuid Ai

> By [MEOK AI Labs](https://meok.ai) — UUID, ULID, and NanoID generation by MEOK AI Labs.

UUID, ULID, and NanoID generation and parsing — MEOK AI Labs.

## Installation

```bash
pip install uuid-ai-mcp
```

## Usage

```bash
# Run standalone
python server.py

# Or via MCP
mcp install uuid-ai-mcp
```

## Tools

### `generate_uuid`
Generate one or more UUIDs. Supports versions 1, 3, 4, and 5.

**Parameters:**
- `version` (int)
- `namespace` (str)
- `name` (str)
- `count` (int)

### `parse_uuid`
Parse and validate a UUID string, extracting all components.

**Parameters:**
- `uuid_string` (str)

### `generate_ulid`
Generate ULID(s) - Universally Unique Lexicographically Sortable Identifiers.

**Parameters:**
- `count` (int)

### `generate_nanoid`
Generate NanoID(s) - compact URL-friendly unique identifiers.

**Parameters:**
- `size` (int)
- `alphabet` (str)
- `count` (int)

### `batch_generate`
Batch generate identifiers of a specified type. Efficient for bulk operations.

**Parameters:**
- `id_type` (str)
- `count` (int)


## Authentication

Free tier: 15 calls/day. Upgrade at [meok.ai/pricing](https://meok.ai/pricing) for unlimited access.

## Links

- **Website**: [meok.ai](https://meok.ai)
- **GitHub**: [CSOAI-ORG/uuid-ai-mcp](https://github.com/CSOAI-ORG/uuid-ai-mcp)
- **PyPI**: [pypi.org/project/uuid-ai-mcp](https://pypi.org/project/uuid-ai-mcp/)

## License

MIT — MEOK AI Labs
