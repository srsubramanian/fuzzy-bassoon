#!/usr/bin/env python3
"""
Test script for PostgreSQL MCP Server
"""
import asyncio
import os
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from fuzzy_bassoon.server import get_db_pool, SecurityConfig, app


async def test_connection():
    """Test database connection"""
    print("🔍 Testing PostgreSQL MCP Server Connection...")
    print("=" * 60)
    
    # Check environment variables
    required_vars = ["POSTGRES_HOST", "POSTGRES_DATABASE", "POSTGRES_USER"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\n💡 Set them in .env file or export them:")
        print("   export POSTGRES_HOST=localhost")
        print("   export POSTGRES_DATABASE=postgres")
        print("   export POSTGRES_USER=postgres")
        print("   export POSTGRES_PASSWORD=your_password")
        return False
    
    print(f"✅ Environment variables configured")
    print(f"   Host: {os.getenv('POSTGRES_HOST')}")
    print(f"   Port: {os.getenv('POSTGRES_PORT', '5432')}")
    print(f"   Database: {os.getenv('POSTGRES_DATABASE')}")
    print(f"   User: {os.getenv('POSTGRES_USER')}")
    print()
    
    # Test security config
    print("🔒 Security Configuration:")
    SecurityConfig.log_config()
    print()
    
    # Test database connection
    try:
        print("🔌 Testing database connection...")
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Test basic query
            result = await conn.fetchval("SELECT version()")
            print(f"✅ Connected successfully!")
            print(f"   PostgreSQL Version: {result[:50]}...")
            print()
            
            # Test table listing
            tables = await conn.fetch("""
                SELECT schemaname, tablename 
                FROM pg_tables 
                WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                LIMIT 5
            """)
            
            if tables:
                print(f"📊 Sample tables found: {len(tables)}")
                for table in tables:
                    print(f"   - {table['schemaname']}.{table['tablename']}")
            else:
                print("ℹ️  No user tables found in database")
            print()
        
        print("✅ All tests passed!")
        print("\n🚀 Ready to start the MCP server with: fuzzy-bassoon")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Verify PostgreSQL is running")
        print("   2. Check credentials and database name")
        print("   3. Ensure user has SELECT permissions")
        print("   4. Try connecting manually: psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DATABASE")
        return False


def main():
    """Main test function"""
    # Load .env file if it exists
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        print(f"📄 Loading environment from {env_file}")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
        print()
    
    # Run async test
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
