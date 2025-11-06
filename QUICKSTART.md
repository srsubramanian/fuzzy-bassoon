# Quick Start Guide

## Setup (5 minutes)

### 1. Install Dependencies
```bash
cd /Users/subramaniansubbiahramasamy/GitHubWorkspae/fuzzy-bassoon
source .venv/bin/activate
uv pip install -e .
```

### 2. Configure Database Connection
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your database credentials
nano .env
```

Required settings in `.env`:
```bash
POSTGRES_HOST=localhost
POSTGRES_DATABASE=your_database
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
```

### 3. Test Connection
```bash
python test_connection.py
```

### 4. Run Server
```bash
fuzzy-bassoon
```

## Quick Test Commands

After starting the server, test with these MCP tool calls:

### List all tables
```json
{
  "tool": "list_tables",
  "arguments": {}
}
```

### Query a table
```json
{
  "tool": "query_database",
  "arguments": {
    "query": "SELECT * FROM your_table LIMIT 5"
  }
}
```

### Get table schema
```json
{
  "tool": "get_table_schema",
  "arguments": {
    "table_name": "your_table"
  }
}
```

### Check security config
```json
{
  "tool": "get_security_config",
  "arguments": {}
}
```

## Common Issues

### "Connection refused"
- PostgreSQL not running: `brew services start postgresql` (macOS)
- Wrong host/port: check `POSTGRES_HOST` and `POSTGRES_PORT`

### "Permission denied"
- User lacks SELECT permission
- Grant access: `GRANT SELECT ON ALL TABLES IN SCHEMA public TO your_user;`

### "Table not allowed"
- Check `ALLOWED_TABLES` in `.env`
- Leave empty to allow all tables

## Security Presets

### Development (permissive)
```bash
MAX_ROWS_LIMIT=1000
QUERY_TIMEOUT_SECONDS=30
ALLOWED_TABLES=
BLOCKED_SCHEMAS=pg_catalog,information_schema
```

### Production (strict)
```bash
MAX_ROWS_LIMIT=100
QUERY_TIMEOUT_SECONDS=10
ALLOWED_TABLES=public.users,public.orders,public.products
BLOCKED_SCHEMAS=pg_catalog,information_schema,private,internal
```

### Testing (very permissive)
```bash
MAX_ROWS_LIMIT=10000
QUERY_TIMEOUT_SECONDS=60
ALLOWED_TABLES=
BLOCKED_SCHEMAS=pg_catalog
```

## Next Steps

1. ✅ Test connection works
2. 📝 Configure security settings for your use case
3. 🔧 Integrate with Claude Desktop (see CLAUDE_DESKTOP.md)
4. 📊 Monitor audit logs: `tail -f postgres_mcp_audit.log`
5. 🚀 Start querying your database!

## Useful Commands

```bash
# Check if server is installed
which fuzzy-bassoon

# View installed package info
pip show fuzzy-bassoon

# View audit logs
tail -f postgres_mcp_audit.log

# Test PostgreSQL connection directly
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DATABASE

# Check server is running (if using stdio)
ps aux | grep fuzzy-bassoon
```

## Getting Help

- 📖 Full documentation: [README.md](README.md)
- 🖥️ Claude Desktop setup: [CLAUDE_DESKTOP.md](CLAUDE_DESKTOP.md)
- 🐛 Issues: Create a GitHub issue
- 📧 Contact: subramanian_psg@yahoo.com
