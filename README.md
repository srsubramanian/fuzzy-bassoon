# Fuzzy-Bassoon PostgreSQL MCP Server

A strict read-only PostgreSQL MCP (Model Context Protocol) server with comprehensive security controls, audit logging, and configurable access restrictions.

## Features

- 🔒 **Strict Read-Only Access**: Only SELECT, SHOW, EXPLAIN, DESCRIBE, and WITH queries allowed
- 🛡️ **Security Controls**:
  - Row limit enforcement (default: 1000 rows)
  - Query timeout protection (default: 30 seconds)
  - Table/schema whitelist support
  - Schema blocking (pg_catalog, information_schema blocked by default)
- 📊 **Audit Logging**: Comprehensive query logging with execution metrics
- ⚡ **Connection Pooling**: Efficient asyncpg connection management
- 🔍 **Query Validation**: Multi-layer validation to prevent unauthorized operations

## Installation

### Prerequisites

- Python 3.13+
- PostgreSQL database
- uv (recommended) or pip

### Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd fuzzy-bassoon
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
# Using uv (recommended)
uv pip install -e .

# Or using pip
pip install -e .
```

## Configuration

Configure the server using environment variables. Create a `.env` file in the project root:

```bash
# Database Connection (Required)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=your_database
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_SSL=prefer  # Options: disable, prefer, require, verify-ca, verify-full

# Security Configuration (Optional)
MAX_ROWS_LIMIT=1000                    # Maximum rows any query can return
QUERY_TIMEOUT_SECONDS=30               # Maximum query execution time
ALLOWED_TABLES=                        # Comma-separated list (empty = all allowed)
                                       # Examples: "users,orders" or "public.users,sales.orders"
BLOCKED_SCHEMAS=pg_catalog,information_schema  # Comma-separated schemas to block
ENABLE_AUDIT_LOG=true                  # Enable audit logging
```

### Environment Variable Details

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `POSTGRES_HOST` | PostgreSQL host | `localhost` | `mydb.example.com` |
| `POSTGRES_PORT` | PostgreSQL port | `5432` | `5432` |
| `POSTGRES_DATABASE` | Database name | `postgres` | `myapp_db` |
| `POSTGRES_USER` | Database user | `postgres` | `readonly_user` |
| `POSTGRES_PASSWORD` | Database password | (empty) | `secure_password` |
| `POSTGRES_SSL` | SSL mode | `prefer` | `require` |
| `MAX_ROWS_LIMIT` | Max rows per query | `1000` | `500` |
| `QUERY_TIMEOUT_SECONDS` | Query timeout | `30` | `60` |
| `ALLOWED_TABLES` | Table whitelist | (empty) | `users,orders` |
| `BLOCKED_SCHEMAS` | Schema blocklist | `pg_catalog,information_schema` | `pg_catalog,sys` |
| `ENABLE_AUDIT_LOG` | Enable audit logs | `true` | `false` |

## Usage

### Running the Server

```bash
# Using the installed script
fuzzy-bassoon

# Or directly with Python
python -m fuzzy_bassoon.server

# Or from the src directory
cd src
python -m fuzzy_bassoon.server
```

### Available Tools

The MCP server provides the following tools:

#### 1. query_database

Execute read-only SQL queries with automatic validation and limits.

```json
{
  "name": "query_database",
  "arguments": {
    "query": "SELECT * FROM users WHERE active = true",
    "params": []
  }
}
```

**Response Format:**
```json
{
  "rowCount": 42,
  "executionTimeMs": 15.23,
  "data": [
    {"id": 1, "name": "John", "active": true},
    ...
  ],
  "restrictions": {
    "maxRowsLimit": 1000,
    "timeoutSeconds": 30
  }
}
```

#### 2. get_table_schema

Get detailed schema information for a specific table.

```json
{
  "name": "get_table_schema",
  "arguments": {
    "table_name": "users",
    "schema_name": "public"
  }
}
```

#### 3. list_tables

List all accessible tables (respects schema restrictions).

```json
{
  "name": "list_tables",
  "arguments": {
    "schema_name": "public"  // Optional
  }
}
```

#### 4. get_security_config

View current security configuration and restrictions.

```json
{
  "name": "get_security_config",
  "arguments": {}
}
```

## Security Features

### Read-Only Enforcement

The server validates all queries and blocks:
- INSERT, UPDATE, DELETE operations
- DROP, TRUNCATE, ALTER statements
- CREATE, GRANT, REVOKE commands
- Any other write operations

### Query Validation Layers

1. **Prefix Validation**: Only SELECT, SHOW, EXPLAIN, DESCRIBE, WITH allowed
2. **Keyword Scanning**: Blocks write operation keywords anywhere in query
3. **Schema Access Control**: Enforces schema blocklist
4. **Table Whitelist**: Optional table-level access control
5. **Automatic LIMIT**: Adds LIMIT clause if missing
6. **Timeout Protection**: Cancels queries exceeding time limit

### Audit Logging

All queries are logged with:
- Timestamp
- Query text (truncated to 500 chars)
- Success/failure status
- Error messages
- Rows returned
- Execution time
- User and host information

Audit logs are written to `postgres_mcp_audit.log`.

## Example Use Cases

### Basic Query

```sql
SELECT id, name, email FROM users WHERE created_at > '2024-01-01' LIMIT 10
```

### Parameterized Query

```json
{
  "query": "SELECT * FROM orders WHERE user_id = $1 AND status = $2",
  "params": [123, "completed"]
}
```

### Complex Analytics

```sql
WITH monthly_sales AS (
  SELECT 
    DATE_TRUNC('month', order_date) as month,
    SUM(total_amount) as revenue
  FROM orders
  WHERE order_date >= NOW() - INTERVAL '12 months'
  GROUP BY 1
)
SELECT * FROM monthly_sales ORDER BY month
```

## Development

### Project Structure

```
fuzzy-bassoon/
├── src/
│   └── fuzzy_bassoon/
│       ├── __init__.py
│       ├── py.typed
│       └── server.py          # Main server implementation
├── pyproject.toml             # Project configuration
├── README.md                  # This file
└── .env                       # Environment variables (create this)
```

### Running Tests

```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Run tests (when implemented)
pytest
```

### Debugging

Enable debug logging by setting:
```bash
export LOG_LEVEL=DEBUG
```

View audit logs:
```bash
tail -f postgres_mcp_audit.log
```

## Troubleshooting

### Connection Issues

- Verify PostgreSQL is running: `psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DATABASE`
- Check SSL configuration matches server requirements
- Ensure user has SELECT permissions on target tables

### Permission Denied Errors

- Check `ALLOWED_TABLES` configuration
- Verify schema is not in `BLOCKED_SCHEMAS`
- Ensure database user has SELECT grants

### Query Timeout

- Increase `QUERY_TIMEOUT_SECONDS` for complex queries
- Optimize query with indexes
- Add WHERE clauses to reduce result set

### Row Limit Issues

- Increase `MAX_ROWS_LIMIT` if needed
- Add explicit LIMIT clause to queries
- Use pagination for large datasets

## Best Practices

1. **Use a dedicated read-only database user**
   ```sql
   CREATE ROLE readonly_user WITH LOGIN PASSWORD 'secure_password';
   GRANT CONNECT ON DATABASE mydb TO readonly_user;
   GRANT USAGE ON SCHEMA public TO readonly_user;
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly_user;
   ```

2. **Configure table whitelist for sensitive databases**
   ```bash
   ALLOWED_TABLES=public.users,public.orders,public.products
   ```

3. **Monitor audit logs regularly**
   ```bash
   # View failed access attempts
   grep '"success": false' postgres_mcp_audit.log
   
   # View slow queries
   grep '"execution_time_ms"' postgres_mcp_audit.log | awk -F'"execution_time_ms": ' '{print $2}' | sort -n
   ```

4. **Use SSL in production**
   ```bash
   POSTGRES_SSL=require
   ```

## License

[Your License Here]

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues and questions:
- GitHub Issues: [your-repo-url]/issues
- Email: subramanian_psg@yahoo.com
