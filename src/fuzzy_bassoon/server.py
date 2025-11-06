"""
PostgreSQL MCP Server - Strict Read-Only Version (FastMCP)
Enhanced with row limits, timeouts, table/schema restrictions, and audit logging
"""

import asyncio
import json
import os
import logging
from datetime import datetime
from typing import Optional, Set
from contextlib import asynccontextmanager
import asyncpg
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('postgres_mcp_audit.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database connection pool
db_pool: Optional[asyncpg.Pool] = None

# ============================================================================
# CONFIGURATION - Adjust these settings for your security requirements
# ============================================================================

class SecurityConfig:
    """Security configuration for read-only access"""
    
    # 1. ROW LIMIT - Maximum rows any query can return
    MAX_ROWS_LIMIT = int(os.getenv("MAX_ROWS_LIMIT", "1000"))
    
    # 2. QUERY TIMEOUT - Maximum query execution time in seconds
    QUERY_TIMEOUT_SECONDS = int(os.getenv("QUERY_TIMEOUT_SECONDS", "30"))
    
    # 3. ALLOWED TABLES - Whitelist of tables (empty = all tables allowed)
    # Format: "schema.table,schema.table" or "table1,table2" (assumes public schema)
    ALLOWED_TABLES: Set[str] = set(
        filter(None, os.getenv("ALLOWED_TABLES", "").split(","))
    )
    
    # 4. BLOCKED SCHEMAS - Schemas that cannot be accessed
    BLOCKED_SCHEMAS: Set[str] = set(
        filter(None, os.getenv("BLOCKED_SCHEMAS", "pg_catalog,information_schema").split(","))
    )
    
    # 5. AUDIT LOGGING - Enable detailed query logging
    ENABLE_AUDIT_LOG = os.getenv("ENABLE_AUDIT_LOG", "true").lower() == "true"
    
    @classmethod
    def log_config(cls):
        """Log current configuration"""
        logger.info("=== Security Configuration ===")
        logger.info(f"Max Rows Limit: {cls.MAX_ROWS_LIMIT}")
        logger.info(f"Query Timeout: {cls.QUERY_TIMEOUT_SECONDS}s")
        logger.info(f"Allowed Tables: {cls.ALLOWED_TABLES if cls.ALLOWED_TABLES else 'ALL'}")
        logger.info(f"Blocked Schemas: {cls.BLOCKED_SCHEMAS}")
        logger.info(f"Audit Logging: {cls.ENABLE_AUDIT_LOG}")
        logger.info("==============================")


# ============================================================================
# AUDIT LOGGING
# ============================================================================

def audit_log(event_type: str, query: str = "", success: bool = True, 
              error: str = "", rows_returned: int = 0, execution_time: float = 0.0):
    """Log security and access events"""
    if not SecurityConfig.ENABLE_AUDIT_LOG:
        return
    
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "query": query[:500] if query else "",  # Truncate long queries
        "success": success,
        "error": error,
        "rows_returned": rows_returned,
        "execution_time_ms": round(execution_time * 1000, 2),
        "user": os.getenv("POSTGRES_USER", "unknown"),
        "host": os.getenv("POSTGRES_HOST", "unknown")
    }
    
    if success:
        logger.info(f"AUDIT: {json.dumps(log_entry)}")
    else:
        logger.warning(f"AUDIT: {json.dumps(log_entry)}")


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_read_only_query(query: str) -> tuple[bool, str]:
    """Validate that query is strictly read-only"""
    upper_query = query.upper().strip()
    
    # Only allow SELECT, SHOW, EXPLAIN, DESCRIBE, and WITH queries
    allowed_prefixes = ['SELECT', 'SHOW', 'EXPLAIN', 'DESCRIBE', 'WITH']
    
    if not any(upper_query.startswith(prefix) for prefix in allowed_prefixes):
        return False, "Only SELECT, SHOW, EXPLAIN, DESCRIBE, and WITH queries are allowed"
    
    # Block any write operations even within allowed queries
    write_keywords = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'TRUNCATE', 
        'ALTER', 'CREATE', 'GRANT', 'REVOKE', 'REPLACE', 'MERGE'
    ]
    
    for keyword in write_keywords:
        if keyword in upper_query:
            return False, f"Write operation '{keyword}' is not allowed in read-only mode"
    
    return True, "Query validated"


def extract_tables_from_query(query: str) -> Set[str]:
    """Extract table names from query (simple pattern matching)"""
    import re
    upper_query = query.upper()
    
    # Simple pattern to find table references after FROM and JOIN
    patterns = [
        r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*\.)?([a-zA-Z_][a-zA-Z0-9_]*)',
        r'JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*\.)?([a-zA-Z_][a-zA-Z0-9_]*)',
    ]
    
    tables = set()
    for pattern in patterns:
        matches = re.finditer(pattern, upper_query)
        for match in matches:
            schema = match.group(1).rstrip('.') if match.group(1) else 'public'
            table = match.group(2)
            tables.add(f"{schema}.{table}".lower())
    
    return tables


def validate_table_access(query: str) -> tuple[bool, str]:
    """Validate that query only accesses allowed tables and schemas"""
    
    # Extract tables from query
    referenced_tables = extract_tables_from_query(query)
    
    # Check blocked schemas
    for table in referenced_tables:
        schema = table.split('.')[0]
        if schema in SecurityConfig.BLOCKED_SCHEMAS:
            return False, f"Access to schema '{schema}' is not allowed"
    
    # Check allowed tables whitelist (if configured)
    if SecurityConfig.ALLOWED_TABLES:
        for table in referenced_tables:
            # Check both "schema.table" and just "table" format
            table_only = table.split('.')[-1]
            if table not in SecurityConfig.ALLOWED_TABLES and table_only not in SecurityConfig.ALLOWED_TABLES:
                return False, f"Access to table '{table}' is not allowed. Allowed tables: {SecurityConfig.ALLOWED_TABLES}"
    
    return True, "Table access validated"


# ============================================================================
# DATABASE CONNECTION
# ============================================================================

async def get_db_pool() -> asyncpg.Pool:
    """Get or create database connection pool"""
    global db_pool
    if db_pool is None:
        # Support both SSL and non-SSL connections
        ssl_mode = os.getenv("POSTGRES_SSL", "prefer")
        ssl_context = None
        
        if ssl_mode in ["require", "verify-ca", "verify-full"]:
            import ssl
            ssl_context = ssl.create_default_context()
            if ssl_mode == "require":
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
        
        db_pool = await asyncpg.create_pool(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DATABASE", "postgres"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", ""),
            ssl=ssl_context,
            min_size=2,
            max_size=10,
            max_queries=50000,
            max_inactive_connection_lifetime=300,
            command_timeout=SecurityConfig.QUERY_TIMEOUT_SECONDS
        )
        
        logger.info("Database connection pool created")
        SecurityConfig.log_config()
    
    return db_pool


# ============================================================================
# LIFESPAN MANAGEMENT
# ============================================================================

@asynccontextmanager
async def lifespan(server: FastMCP):
    """Lifespan context manager for connection pool"""
    # Startup: Initialize connection pool
    await get_db_pool()
    logger.info("FastMCP server initialized with database connection pool")
    
    yield
    
    # Shutdown: Close connection pool
    global db_pool
    if db_pool:
        await db_pool.close()
        logger.info("Database connection pool closed")


# ============================================================================
# PYDANTIC MODELS FOR STRUCTURED OUTPUT
# ============================================================================

class QueryResult(BaseModel):
    """Structured query result"""
    rowCount: int = Field(description="Number of rows returned")
    executionTimeMs: float = Field(description="Query execution time in milliseconds")
    data: list[dict] = Field(description="Query results")
    restrictions: dict = Field(description="Applied security restrictions")


class TableSchema(BaseModel):
    """Table schema information"""
    column_name: str
    data_type: str
    character_maximum_length: Optional[int] = None
    is_nullable: str
    column_default: Optional[str] = None


class TableInfo(BaseModel):
    """Table information"""
    schema_name: str
    table_name: str


# ============================================================================
# FASTMCP SERVER & TOOLS
# ============================================================================

# Initialize FastMCP server with lifespan
mcp = FastMCP("fuzzy-bassoon-postgres", lifespan=lifespan)


@mcp.tool()
async def query_database(
    query: str = Field(description="SQL SELECT query to execute (read-only)"),
    params: list = Field(default=[], description="Query parameters for $1, $2, etc. placeholders")
) -> str:
    """
    Execute a read-only SELECT query with strict security validation.
    Max rows: {MAX_ROWS_LIMIT}, Timeout: {QUERY_TIMEOUT_SECONDS}s.
    Only SELECT, SHOW, EXPLAIN, DESCRIBE, and WITH queries allowed.
    """
    import time
    start_time = time.time()
    
    try:
        pool = await get_db_pool()
        # VALIDATION 1: Read-only query check
        is_valid, message = validate_read_only_query(query)
        if not is_valid:
            audit_log("QUERY_BLOCKED", query=query, success=False, error=message)
            return f"❌ Query validation failed: {message}\n\n🔒 This server enforces strict read-only access."
        
        # VALIDATION 2: Table/Schema access check
        is_valid, message = validate_table_access(query)
        if not is_valid:
            audit_log("ACCESS_DENIED", query=query, success=False, error=message)
            return f"❌ Access denied: {message}"
        
        # RESTRICTION: Add LIMIT clause if not present
        upper_query = query.upper().strip()
        if 'LIMIT' not in upper_query:
            query = f"{query.rstrip(';')} LIMIT {SecurityConfig.MAX_ROWS_LIMIT}"
            logger.info(f"Added LIMIT clause: {SecurityConfig.MAX_ROWS_LIMIT}")
        
        # Execute query with timeout
        async with pool.acquire() as conn:
            try:
                rows = await asyncio.wait_for(
                    conn.fetch(query, *params),
                    timeout=SecurityConfig.QUERY_TIMEOUT_SECONDS
                )
            except asyncio.TimeoutError:
                error_msg = f"Query exceeded timeout limit of {SecurityConfig.QUERY_TIMEOUT_SECONDS}s"
                audit_log("QUERY_TIMEOUT", query=query, success=False, error=error_msg)
                return f"❌ {error_msg}"
            
            results = [dict(row) for row in rows]
            row_count = len(results)
            execution_time = time.time() - start_time
            
            # Audit log successful query
            audit_log(
                "QUERY_SUCCESS", 
                query=query, 
                success=True, 
                rows_returned=row_count,
                execution_time=execution_time
            )
            
            response = {
                "rowCount": row_count,
                "executionTimeMs": round(execution_time * 1000, 2),
                "data": results,
                "restrictions": {
                    "maxRowsLimit": SecurityConfig.MAX_ROWS_LIMIT,
                    "timeoutSeconds": SecurityConfig.QUERY_TIMEOUT_SECONDS
                }
            }
            
            return json.dumps(response, indent=2, default=str)
    
    except Exception as e:
        error_msg = str(e)
        audit_log("ERROR", success=False, error=error_msg)
        return f"Error executing query: {error_msg}"


@mcp.tool()
async def get_table_schema(
    table_name: str = Field(description="Name of the table"),
    schema_name: str = Field(default="public", description="Schema name (default: 'public')")
) -> str:
    """Get detailed schema information for allowed tables including columns, data types, and constraints."""
    try:
        pool = await get_db_pool()
        
        # Check schema access
        if schema_name in SecurityConfig.BLOCKED_SCHEMAS:
            audit_log("ACCESS_DENIED", success=False, error=f"Schema {schema_name} is blocked")
            return f"❌ Access to schema '{schema_name}' is not allowed"
        
        # Check table access
        full_table = f"{schema_name}.{table_name}"
        if SecurityConfig.ALLOWED_TABLES:
            if full_table not in SecurityConfig.ALLOWED_TABLES and table_name not in SecurityConfig.ALLOWED_TABLES:
                audit_log("ACCESS_DENIED", success=False, error=f"Table {full_table} not in whitelist")
                return f"❌ Access to table '{full_table}' is not allowed"
        
        schema_query = """
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = $1 AND table_name = $2
            ORDER BY ordinal_position
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(schema_query, schema_name, table_name)
            schema_info = [dict(row) for row in rows]
            
            audit_log("SCHEMA_QUERY", success=True)
            
            return json.dumps(schema_info, indent=2, default=str)
    
    except Exception as e:
        error_msg = str(e)
        audit_log("ERROR", success=False, error=error_msg)
        return f"Error getting table schema: {error_msg}"


@mcp.tool()
async def list_tables(
    schema_name: Optional[str] = Field(default=None, description="Filter by schema name (optional)")
) -> str:
    """List all accessible tables in the database, respecting schema restrictions and table whitelists."""
    try:
        pool = await get_db_pool()
        
        # Build query based on restrictions
        if schema_name:
            if schema_name in SecurityConfig.BLOCKED_SCHEMAS:
                return f"❌ Access to schema '{schema_name}' is not allowed"
            
            tables_query = """
                SELECT schemaname as schema_name, tablename as table_name
                FROM pg_tables
                WHERE schemaname = $1
                ORDER BY tablename
            """
            params = [schema_name]
        else:
            # Exclude blocked schemas
            blocked_list = ",".join([f"'{s}'" for s in SecurityConfig.BLOCKED_SCHEMAS])
            tables_query = f"""
                SELECT schemaname as schema_name, tablename as table_name
                FROM pg_tables
                WHERE schemaname NOT IN ({blocked_list})
                ORDER BY schemaname, tablename
            """
            params = []
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(tables_query, *params)
            all_tables = [dict(row) for row in rows]
            
            # Filter by allowed tables if whitelist is configured
            if SecurityConfig.ALLOWED_TABLES:
                filtered_tables = []
                for table in all_tables:
                    full_name = f"{table['schema_name']}.{table['table_name']}"
                    if full_name in SecurityConfig.ALLOWED_TABLES or table['table_name'] in SecurityConfig.ALLOWED_TABLES:
                        filtered_tables.append(table)
                all_tables = filtered_tables
            
            audit_log("LIST_TABLES", success=True, rows_returned=len(all_tables))
            
            return json.dumps(all_tables, indent=2, default=str)
    
    except Exception as e:
        error_msg = str(e)
        audit_log("ERROR", success=False, error=error_msg)
        return f"Error listing tables: {error_msg}"


@mcp.tool()
async def get_security_config() -> str:
    """View current security restrictions, limits, allowed operations, and blocked operations."""
    config = {
        "restrictions": {
            "maxRowsLimit": SecurityConfig.MAX_ROWS_LIMIT,
            "queryTimeoutSeconds": SecurityConfig.QUERY_TIMEOUT_SECONDS,
            "allowedTables": list(SecurityConfig.ALLOWED_TABLES) if SecurityConfig.ALLOWED_TABLES else "ALL (no restrictions)",
            "blockedSchemas": list(SecurityConfig.BLOCKED_SCHEMAS),
            "auditLogging": SecurityConfig.ENABLE_AUDIT_LOG
        },
        "allowedOperations": ["SELECT", "SHOW", "EXPLAIN", "DESCRIBE", "WITH"],
        "blockedOperations": ["INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE", "ALTER", "CREATE", "GRANT", "REVOKE"]
    }
    
    return json.dumps(config, indent=2)


async def main():
    """Run the FastMCP server"""
    logger.info("Starting PostgreSQL MCP Server (Strict Read-Only) - FastMCP")
    await mcp.run()


if __name__ == "__main__":
    asyncio.run(main())
