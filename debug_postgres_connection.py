#!/usr/bin/env python3
"""
Comprehensive PostgreSQL connection diagnostic script for Supabase.
This script will help identify exactly what's wrong with the database connection.
"""
import asyncio
import asyncpg
import os
import socket
import dns.resolver
from dotenv import load_dotenv
from urllib.parse import urlparse
import sys

async def test_basic_connection():
    """Test the basic connection with the provided URL."""
    print("=" * 60)
    print("BASIC CONNECTION TEST")
    print("=" * 60)
    
    load_dotenv('backend/.env')
    db_url = os.environ.get('SUPABASE_DB_URL')
    
    if not db_url:
        print("❌ SUPABASE_DB_URL not found in environment")
        return False
    
    print(f"Database URL: {db_url}")
    
    try:
        print("🔗 Attempting to connect...")
        conn = await asyncpg.connect(db_url)
        print("✅ Connection successful!")
        
        # Test a simple query
        result = await conn.fetchval('SELECT version()')
        print(f"PostgreSQL version: {result}")
        
        # Test user permissions
        user_result = await conn.fetchval('SELECT current_user')
        print(f"Connected as user: {user_result}")
        
        # Test database name
        db_result = await conn.fetchval('SELECT current_database()')
        print(f"Connected to database: {db_result}")
        
        await conn.close()
        print("✅ Connection closed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

def test_dns_resolution():
    """Test DNS resolution for the hostname."""
    print("\n" + "=" * 60)
    print("DNS RESOLUTION TEST")
    print("=" * 60)
    
    load_dotenv('backend/.env')
    db_url = os.environ.get('SUPABASE_DB_URL')
    
    if not db_url:
        print("❌ SUPABASE_DB_URL not found")
        return False
    
    # Parse the URL to get hostname
    parsed = urlparse(db_url)
    hostname = parsed.hostname
    port = parsed.port or 5432
    
    print(f"Hostname: {hostname}")
    print(f"Port: {port}")
    
    # Test DNS resolution
    try:
        print("🔍 Testing DNS resolution...")
        ip_addresses = socket.gethostbyname_ex(hostname)
        print(f"✅ DNS resolution successful")
        print(f"Primary IP: {ip_addresses[2][0]}")
        print(f"All IPs: {ip_addresses[2]}")
        
        # Test TCP connection to the port
        print(f"🔗 Testing TCP connection to {hostname}:{port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((hostname, port))
        sock.close()
        
        if result == 0:
            print(f"✅ TCP connection successful to {hostname}:{port}")
            return True
        else:
            print(f"❌ TCP connection failed to {hostname}:{port} (error code: {result})")
            return False
            
    except socket.gaierror as e:
        print(f"❌ DNS resolution failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def test_url_parsing():
    """Test URL parsing and component extraction."""
    print("\n" + "=" * 60)
    print("URL PARSING TEST")
    print("=" * 60)
    
    load_dotenv('backend/.env')
    db_url = os.environ.get('SUPABASE_DB_URL')
    
    if not db_url:
        print("❌ SUPABASE_DB_URL not found")
        return False
    
    print(f"Original URL: {db_url}")
    
    try:
        parsed = urlparse(db_url)
        print(f"Scheme: {parsed.scheme}")
        print(f"Username: {parsed.username}")
        print(f"Password: {'*' * len(parsed.password) if parsed.password else 'None'}")
        print(f"Hostname: {parsed.hostname}")
        print(f"Port: {parsed.port}")
        print(f"Database: {parsed.path.lstrip('/')}")
        
        # Reconstruct URL to verify
        reconstructed = f"{parsed.scheme}://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port or 5432}{parsed.path}"
        print(f"Reconstructed: {reconstructed}")
        
        if reconstructed == db_url:
            print("✅ URL parsing successful")
            return True
        else:
            print("⚠️  URL reconstruction differs from original")
            return False
            
    except Exception as e:
        print(f"❌ URL parsing failed: {e}")
        return False

async def test_alternative_connection_methods():
    """Test alternative connection methods and formats."""
    print("\n" + "=" * 60)
    print("ALTERNATIVE CONNECTION METHODS TEST")
    print("=" * 60)
    
    load_dotenv('backend/.env')
    db_url = os.environ.get('SUPABASE_DB_URL')
    
    if not db_url:
        print("❌ SUPABASE_DB_URL not found")
        return False
    
    parsed = urlparse(db_url)
    
    # Method 1: Using connection parameters instead of URL
    print("🔗 Testing connection with explicit parameters...")
    try:
        conn = await asyncpg.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip('/'),
            ssl='require'  # Supabase requires SSL
        )
        print("✅ Connection with explicit parameters successful!")
        await conn.close()
        return True
    except Exception as e:
        print(f"❌ Connection with explicit parameters failed: {e}")
    
    # Method 2: Try different SSL modes
    print("🔗 Testing connection with different SSL settings...")
    ssl_modes = ['require', 'prefer', 'allow', 'disable']
    
    for ssl_mode in ssl_modes:
        try:
            print(f"  Trying SSL mode: {ssl_mode}")
            conn = await asyncpg.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path.lstrip('/'),
                ssl=ssl_mode
            )
            print(f"✅ Connection successful with SSL mode: {ssl_mode}")
            await conn.close()
            return True
        except Exception as e:
            print(f"  ❌ SSL mode {ssl_mode} failed: {e}")
    
    return False

def check_supabase_project_status():
    """Check if the Supabase project is active and accessible."""
    print("\n" + "=" * 60)
    print("SUPABASE PROJECT STATUS CHECK")
    print("=" * 60)
    
    load_dotenv('backend/.env')
    db_url = os.environ.get('SUPABASE_DB_URL')
    
    if not db_url:
        print("❌ SUPABASE_DB_URL not found")
        return False
    
    parsed = urlparse(db_url)
    hostname = parsed.hostname
    
    if not hostname:
        print("❌ Could not extract hostname from URL")
        return False
    
    # Extract project reference from hostname
    if 'supabase.co' in hostname:
        parts = hostname.split('.')
        if len(parts) >= 3 and parts[0] == 'db':
            project_ref = parts[1]
            print(f"Project reference: {project_ref}")
            print(f"Full hostname: {hostname}")
            
            # Check if this looks like a valid Supabase hostname format
            if len(project_ref) > 10:  # Supabase project refs are usually long
                print("✅ Hostname format looks correct for Supabase")
                
                # Suggest checking Supabase dashboard
                print("\n💡 SUGGESTIONS:")
                print("1. Check your Supabase dashboard to ensure the project is not paused")
                print("2. Verify the database URL in Settings > Database")
                print("3. Make sure you're using the 'Direct connection' URL, not the 'Pooler' URL")
                print("4. Check if your database has been paused due to inactivity")
                
                return True
            else:
                print("⚠️  Project reference seems too short")
        else:
            print("⚠️  Hostname doesn't match expected Supabase format")
    else:
        print("⚠️  This doesn't appear to be a Supabase hostname")
    
    return False

async def test_connection_pool():
    """Test creating a connection pool like our application does."""
    print("\n" + "=" * 60)
    print("CONNECTION POOL TEST")
    print("=" * 60)
    
    load_dotenv('backend/.env')
    db_url = os.environ.get('SUPABASE_DB_URL')
    
    if not db_url:
        print("❌ SUPABASE_DB_URL not found")
        return False
    
    try:
        print("🔗 Creating connection pool...")
        pool = await asyncpg.create_pool(
            db_url,
            min_size=1,
            max_size=5,
            max_queries=50,
            max_inactive_connection_lifetime=300,
            command_timeout=30,
            server_settings={
                'jit': 'off',
            }
        )
        print("✅ Connection pool created successfully!")
        
        # Test acquiring a connection from the pool
        print("🔗 Testing connection acquisition from pool...")
        async with pool.acquire() as conn:
            result = await conn.fetchval('SELECT 1')
            print(f"✅ Pool connection test successful: {result}")
        
        await pool.close()
        print("✅ Connection pool closed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Connection pool test failed: {e}")
        return False

async def test_supabase_pooler_connection():
    """Test connection using Supabase pooler format."""
    print("\n" + "=" * 60)
    print("SUPABASE POOLER CONNECTION TEST")
    print("=" * 60)
    
    load_dotenv('backend/.env')
    db_url = os.environ.get('SUPABASE_DB_URL')
    
    if not db_url:
        print("❌ SUPABASE_DB_URL not found")
        return False
    
    parsed = urlparse(db_url)
    
    # Extract project reference from the direct connection URL
    if 'supabase.co' in parsed.hostname:
        parts = parsed.hostname.split('.')
        if len(parts) >= 3 and parts[0] == 'db':
            project_ref = parts[1]
            
            # Construct pooler URLs to try different regions
            regions = ['us-east-1', 'us-west-1', 'eu-west-1', 'ap-southeast-1']
            
            for region in regions:
                pooler_url = f"postgresql://postgres.{project_ref}:{parsed.password}@aws-0-{region}.pooler.supabase.com:5432/postgres"
                print(f"🔗 Testing pooler connection for {region}...")
                print(f"URL: postgresql://postgres.{project_ref}:***@aws-0-{region}.pooler.supabase.com:5432/postgres")
                
                try:
                    conn = await asyncpg.connect(pooler_url)
                    print(f"✅ Pooler connection successful for {region}!")
                    
                    # Test a simple query
                    result = await conn.fetchval('SELECT version()')
                    print(f"PostgreSQL version: {result[:50]}...")
                    
                    await conn.close()
                    print(f"✅ Pooler connection closed successfully")
                    
                    # Update the environment variable suggestion
                    print(f"\n💡 SUCCESS! Use this URL in your .env file:")
                    print(f"SUPABASE_DB_URL={pooler_url}")
                    
                    return True
                    
                except Exception as e:
                    print(f"❌ Pooler connection failed for {region}: {e}")
                    continue
            
            print("❌ All pooler regions failed")
            return False
    
    print("❌ Could not extract project reference from hostname")
    return False

async def main():
    """Run all diagnostic tests."""
    print("🔍 PostgreSQL Connection Diagnostic Tool")
    print("This will help identify issues with your Supabase database connection")
    
    # Load environment first
    env_path = 'backend/.env'
    if not os.path.exists(env_path):
        print(f"❌ Environment file not found: {env_path}")
        print("Please ensure backend/.env exists with SUPABASE_DB_URL")
        return
    
    load_dotenv(env_path)
    db_url = os.environ.get('SUPABASE_DB_URL')
    if not db_url:
        print("❌ SUPABASE_DB_URL not found in backend/.env")
        return
    
    print(f"Environment file: {env_path}")
    print(f"Database URL found: {db_url[:30]}...")
    
    # Run all tests
    tests = [
        ("URL Parsing", test_url_parsing),
        ("DNS Resolution", test_dns_resolution),
        ("Supabase Project Status", check_supabase_project_status),
        ("Basic Connection", test_basic_connection),
        ("Alternative Methods", test_alternative_connection_methods),
        ("Connection Pool", test_connection_pool),
        ("Supabase Pooler Connection", test_supabase_pooler_connection),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    print(f"\nPassed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Your connection should work.")
    elif passed_tests == 0:
        print("🚨 All tests failed. There's a fundamental issue with the connection.")
        print("\n💡 Next steps:")
        print("1. Double-check your SUPABASE_DB_URL in backend/.env")
        print("2. Verify your Supabase project is active and not paused")
        print("3. Get the correct database URL from Supabase dashboard")
    else:
        print("⚠️  Some tests passed, some failed. There may be a configuration issue.")

if __name__ == "__main__":
    # Check if required packages are available
    try:
        import dns.resolver
    except ImportError:
        print("Installing required package: dnspython")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "dnspython"])
        import dns.resolver
    
    asyncio.run(main()) 