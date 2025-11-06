# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a **PostgreSQL MCP (Model Context Protocol) server** with strict read-only access controls, built with **FastMCP**, Python 3.13+, and managed with uv. The server provides secure database access through the MCP protocol with comprehensive security features including query validation, audit logging, row limits, and timeout protection.

**Key Technologies:**
- **FastMCP** - Simplified MCP server framework with automatic schema generation from type hints
- **asyncpg** - High-performance async PostgreSQL driver
- **Pydantic** - Data validation using Python type annotations

## Project Structure

```
fuzzy-bassoon/
├── src/fuzzy_bassoon/
│   ├── __init__.py          # Package exports
│   ├── py.typed             # Type hints marker
│   └── server.py            # Main PostgreSQL MCP server implementation
├── pyproject.toml           # Project configuration and dependencies
├── .env.example             # Example environment configuration
├── .gitignore              # Git ignore patterns
├── test_connection.py       # Database connection test script
├── setup_readonly_user.sql  # SQL script for creating read-only user
├── README.md                # Comprehensive documentation
├── QUICKSTART.md            # Quick start guide
└── CLAUDE_DESKTOP.md        # Claude Desktop integration guide
```

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux

# Install dependencies
uv pip install -e .

# Configure database connection
cp .env.example .env
# Edit .env with your PostgreSQL credentials
```

### Running the Server
```bash
# Test database connection first
python test_connection.py

# Run the MCP server
fuzzy-bassoon

# Or run directly
python -m fuzzy_bassoon.server
```

### Testing
```bash
# Test connection
./test_connection.py

# View audit logs
tail -f postgres_mcp_audit.log
```

## Architecture

The server is built using:
- **MCP Python SDK** (`mcp>=1.20.0`) - MCP protocol implementation
- **asyncpg** (`asyncpg>=0.29.0`) - High-performance PostgreSQL driver
- **STDIO Transport** - Server communicates via standard input/output

### Security Architecture

**Multi-Layer Security**:
1. **Query Validation** - Only SELECT, SHOW, EXPLAIN, DESCRIBE, WITH allowed
2. **Keyword Scanning** - Blocks INSERT, UPDATE, DELETE, DROP, etc.
3. **Schema Access Control** - Blocks pg_catalog, information_schema by default
4. **Table Whitelist** - Optional table-level access restrictions
5. **Automatic Row Limits** - Enforces MAX_ROWS_LIMIT (default: 1000)
6. **Query Timeouts** - Cancels long-running queries (default: 30s)
7. **Audit Logging** - Comprehensive query and access logging

### Current Features

**MCP Tools**:
1. `query_database` - Execute read-only SELECT queries with validation
2. `get_table_schema` - Get detailed schema information for tables
3. `list_tables` - List accessible tables (respects restrictions)
4. `get_security_config` - View current security settings

**Security Features**:
- Connection pooling with asyncpg
- SSL/TLS support for database connections
- Parameterized query support ($1, $2, etc.)
- Audit logging to `postgres_mcp_audit.log`
- Environment-based configuration

## Configuration

Configure via environment variables in `.env`:

```bash
# Database Connection (Required)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=your_database
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_SSL=prefer

# Security Settings (Optional)
MAX_ROWS_LIMIT=1000
QUERY_TIMEOUT_SECONDS=30
ALLOWED_TABLES=                # Empty = all allowed
BLOCKED_SCHEMAS=pg_catalog,information_schema
ENABLE_AUDIT_LOG=true
```

## Adding New Features

When extending this MCP server:

### Adding New Tools
Add to `@app.list_tools()` and `@app.call_tool()` in `server.py`:
```python
Tool(
    name="your_tool_name",
    description="Clear description of what it does",
    inputSchema={
        "type": "object",
        "properties": {
            "param_name": {
                "type": "string",
                "description": "Parameter description"
            }
        },
        "required": ["param_name"]
    }
)
```

### Security Considerations
- Always validate inputs before database queries
- Use parameterized queries to prevent SQL injection
- Add audit logging for new operations
- Test with table whitelist restrictions
- Verify queries are read-only

### Database Operations
```python
# Use connection pool
pool = await get_db_pool()

# Execute queries safely
async with pool.acquire() as conn:
    rows = await conn.fetch("SELECT * FROM table WHERE id = $1", param)
    results = [dict(row) for row in rows]
```

## Best Practices

1. **Database User**: Create dedicated read-only user (see `setup_readonly_user.sql`)
2. **SSL Connections**: Use `POSTGRES_SSL=require` in production
3. **Table Whitelist**: Configure `ALLOWED_TABLES` for sensitive databases
4. **Audit Monitoring**: Regularly review `postgres_mcp_audit.log`
5. **Error Handling**: Always log errors and return user-friendly messages
6. **Connection Pooling**: Leverage asyncpg's built-in pooling
7. **Timeout Protection**: Keep `QUERY_TIMEOUT_SECONDS` reasonable

## Testing Strategy

1. **Unit Tests**: Test validation functions independently
2. **Integration Tests**: Test database operations with test database
3. **Security Tests**: Verify blocked operations are rejected
4. **Performance Tests**: Test timeout and row limit enforcement

## Common Issues

- **Connection refused**: PostgreSQL not running or wrong host/port
- **Permission denied**: User lacks SELECT permission or table not in whitelist
- **Query timeout**: Complex query exceeds QUERY_TIMEOUT_SECONDS
- **Row limit**: Results truncated by MAX_ROWS_LIMIT

See README.md for detailed troubleshooting.
