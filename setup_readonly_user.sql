-- ============================================================================
-- PostgreSQL Read-Only User Setup Script
-- ============================================================================
-- This script creates a secure read-only user for the MCP server
-- Run this as a PostgreSQL superuser or database owner

-- ============================================================================
-- STEP 1: Create the read-only user
-- ============================================================================
-- Replace 'mcp_readonly' and 'secure_password_here' with your values

-- Drop user if exists (for testing/recreation)
-- DROP ROLE IF EXISTS mcp_readonly;

-- Create the read-only user
CREATE ROLE mcp_readonly WITH LOGIN PASSWORD 'secure_password_here';

-- Add description
COMMENT ON ROLE mcp_readonly IS 'Read-only user for MCP Server access';

-- ============================================================================
-- STEP 2: Grant database connection
-- ============================================================================
-- Replace 'your_database' with your actual database name

GRANT CONNECT ON DATABASE your_database TO mcp_readonly;

-- ============================================================================
-- STEP 3: Grant schema usage
-- ============================================================================
-- Grant usage on the public schema (adjust if using different schemas)

GRANT USAGE ON SCHEMA public TO mcp_readonly;

-- If you have other schemas, grant usage on them too:
-- GRANT USAGE ON SCHEMA your_schema TO mcp_readonly;

-- ============================================================================
-- STEP 4: Grant SELECT on existing tables
-- ============================================================================
-- Grant SELECT permission on all existing tables in public schema

GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcp_readonly;

-- For other schemas:
-- GRANT SELECT ON ALL TABLES IN SCHEMA your_schema TO mcp_readonly;

-- ============================================================================
-- STEP 5: Grant SELECT on future tables (automatic)
-- ============================================================================
-- This ensures any new tables created will automatically be accessible

ALTER DEFAULT PRIVILEGES IN SCHEMA public 
    GRANT SELECT ON TABLES TO mcp_readonly;

-- For other schemas:
-- ALTER DEFAULT PRIVILEGES IN SCHEMA your_schema 
--     GRANT SELECT ON TABLES TO mcp_readonly;

-- ============================================================================
-- STEP 6: Grant SELECT on sequences (for serial columns)
-- ============================================================================
-- Optional: if you need to read sequence values

GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO mcp_readonly;

ALTER DEFAULT PRIVILEGES IN SCHEMA public 
    GRANT SELECT ON SEQUENCES TO mcp_readonly;

-- ============================================================================
-- STEP 7: Verify permissions
-- ============================================================================
-- Check what the user can access

-- View granted privileges
SELECT 
    grantee,
    table_schema,
    table_name,
    privilege_type
FROM information_schema.table_privileges
WHERE grantee = 'mcp_readonly'
ORDER BY table_schema, table_name;

-- ============================================================================
-- STEP 8: Test the connection (run in a new session)
-- ============================================================================
-- Switch to the new user and test
-- \c your_database mcp_readonly

-- Test SELECT (should work)
-- SELECT version();
-- SELECT * FROM your_table LIMIT 1;

-- Test INSERT (should fail)
-- INSERT INTO your_table (column1) VALUES ('test'); -- Should fail

-- ============================================================================
-- OPTIONAL: Table-level permissions (granular control)
-- ============================================================================
-- If you want to grant access to specific tables only:

-- REVOKE SELECT ON ALL TABLES IN SCHEMA public FROM mcp_readonly;
-- GRANT SELECT ON public.users TO mcp_readonly;
-- GRANT SELECT ON public.orders TO mcp_readonly;
-- GRANT SELECT ON public.products TO mcp_readonly;

-- ============================================================================
-- OPTIONAL: Row-level security (advanced)
-- ============================================================================
-- If you need row-level restrictions:

-- Enable RLS on a table
-- ALTER TABLE public.sensitive_table ENABLE ROW LEVEL SECURITY;

-- Create policy (example: only show public records)
-- CREATE POLICY mcp_readonly_policy ON public.sensitive_table
--     FOR SELECT
--     TO mcp_readonly
--     USING (is_public = true);

-- ============================================================================
-- OPTIONAL: Revoke dangerous permissions
-- ============================================================================
-- Ensure user cannot create, modify, or delete

REVOKE CREATE ON SCHEMA public FROM mcp_readonly;
REVOKE ALL ON SCHEMA public FROM mcp_readonly;
GRANT USAGE ON SCHEMA public TO mcp_readonly;

-- ============================================================================
-- SECURITY BEST PRACTICES
-- ============================================================================
-- 1. Use strong passwords (20+ characters, mixed case, numbers, symbols)
-- 2. Rotate passwords regularly
-- 3. Use SSL/TLS for connections in production
-- 4. Monitor audit logs for suspicious queries
-- 5. Use table whitelisting in the MCP server config
-- 6. Set appropriate query timeouts and row limits
-- 7. Regularly review and audit permissions
-- 8. Consider row-level security for sensitive data
-- 9. Use connection pooling to limit concurrent connections
-- 10. Set statement_timeout to prevent long-running queries

-- Set statement timeout for this role (optional)
-- ALTER ROLE mcp_readonly SET statement_timeout = '30s';

-- ============================================================================
-- CLEANUP (if needed)
-- ============================================================================
-- To remove the user and all permissions:
-- REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM mcp_readonly;
-- REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM mcp_readonly;
-- REVOKE USAGE ON SCHEMA public FROM mcp_readonly;
-- REVOKE CONNECT ON DATABASE your_database FROM mcp_readonly;
-- DROP ROLE mcp_readonly;

-- ============================================================================
-- CONNECTION STRING FOR .env FILE
-- ============================================================================
-- After running this script, use these settings in your .env file:
--
-- POSTGRES_HOST=localhost
-- POSTGRES_PORT=5432
-- POSTGRES_DATABASE=your_database
-- POSTGRES_USER=mcp_readonly
-- POSTGRES_PASSWORD=secure_password_here
-- POSTGRES_SSL=prefer
--
-- ============================================================================
