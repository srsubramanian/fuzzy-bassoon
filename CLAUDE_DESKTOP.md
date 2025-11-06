# Claude Desktop Integration

To use this PostgreSQL MCP server with Claude Desktop, add the following configuration to your Claude Desktop config file.

## Configuration File Location

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

## Configuration

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "postgres-readonly": {
      "command": "/Users/subramaniansubbiahramasamy/GitHubWorkspae/fuzzy-bassoon/.venv/bin/python",
      "args": [
        "-m",
        "fuzzy_bassoon.server"
      ],
      "env": {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_DATABASE": "your_database",
        "POSTGRES_USER": "your_user",
        "POSTGRES_PASSWORD": "your_password",
        "POSTGRES_SSL": "prefer",
        "MAX_ROWS_LIMIT": "1000",
        "QUERY_TIMEOUT_SECONDS": "30",
        "ALLOWED_TABLES": "",
        "BLOCKED_SCHEMAS": "pg_catalog,information_schema",
        "ENABLE_AUDIT_LOG": "true"
      }
    }
  }
}
```

## Quick Configuration Steps

1. **Locate your Claude Desktop config file** (see locations above)

2. **Edit the configuration**:
   - Update the `command` path to point to your virtual environment's Python
   - Update the `env` variables with your PostgreSQL credentials
   - Customize security settings as needed

3. **Restart Claude Desktop**

4. **Verify connection**: In Claude Desktop, you should see the MCP server tools available

## Environment Variables

Customize these in the `env` section:

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_HOST` | PostgreSQL server host | `localhost` |
| `POSTGRES_PORT` | PostgreSQL server port | `5432` |
| `POSTGRES_DATABASE` | Database name | `postgres` |
| `POSTGRES_USER` | Database username | `postgres` |
| `POSTGRES_PASSWORD` | Database password | (required) |
| `POSTGRES_SSL` | SSL mode | `prefer` |
| `MAX_ROWS_LIMIT` | Maximum rows per query | `1000` |
| `QUERY_TIMEOUT_SECONDS` | Query timeout in seconds | `30` |
| `ALLOWED_TABLES` | Comma-separated table whitelist | (empty = all) |
| `BLOCKED_SCHEMAS` | Comma-separated schema blocklist | `pg_catalog,information_schema` |
| `ENABLE_AUDIT_LOG` | Enable audit logging | `true` |

## Testing the Connection

After configuration, test in Claude Desktop by asking:

```
Can you list the available tables in my database?
```

or

```
Can you show me the schema for the users table?
```

## Security Best Practices

1. **Use a dedicated read-only database user**:
   ```sql
   CREATE ROLE claude_readonly WITH LOGIN PASSWORD 'secure_password';
   GRANT CONNECT ON DATABASE mydb TO claude_readonly;
   GRANT USAGE ON SCHEMA public TO claude_readonly;
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO claude_readonly;
   ```

2. **Configure table whitelist** for sensitive databases:
   ```json
   "ALLOWED_TABLES": "public.users,public.orders,public.products"
   ```

3. **Use SSL in production**:
   ```json
   "POSTGRES_SSL": "require"
   ```

4. **Monitor audit logs**:
   ```bash
   tail -f /Users/subramaniansubbiahramasamy/GitHubWorkspae/fuzzy-bassoon/postgres_mcp_audit.log
   ```

## Troubleshooting

### Server not appearing in Claude Desktop

1. Check Claude Desktop logs for errors
2. Verify the Python path is correct
3. Ensure all dependencies are installed
4. Restart Claude Desktop

### Connection failures

1. Verify PostgreSQL is running
2. Check credentials in the config
3. Test connection manually:
   ```bash
   psql -h localhost -U your_user -d your_database
   ```
4. Check audit logs for error details

### Permission denied

1. Verify the database user has SELECT permissions
2. Check `ALLOWED_TABLES` and `BLOCKED_SCHEMAS` settings
3. Review audit logs for blocked queries

## Example Queries with Claude

Once configured, you can ask Claude to:

- "Show me all tables in the database"
- "What's the schema of the customers table?"
- "Query the orders table and show me orders from the last 30 days"
- "Count the number of active users"
- "Show me the top 10 products by revenue"

The server will automatically enforce read-only access and apply security restrictions.
