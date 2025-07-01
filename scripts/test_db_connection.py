#!/usr/bin/env python3
"""
Database connection test script for Render deployment.
Run this to test if your DATABASE_URL is working correctly.
"""

import os
import sys
from urllib.parse import urlparse

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("python-dotenv not installed, trying to load .env manually...")

def test_database_connection():
    """Test database connection with detailed diagnostics."""
    
    print("🔍 Database Connection Test")
    print("=" * 50)
    
    # Check if DATABASE_URL is set
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable is not set!")
        print("Please check your .env file or set it in your environment.")
        return False
    
    print(f"✅ DATABASE_URL is set")
    
    # Parse the URL to show details (without password)
    try:
        parsed = urlparse(database_url)
        print(f"📊 Connection Details:")
        print(f"   Host: {parsed.hostname}")
        print(f"   Port: {parsed.port}")
        print(f"   Database: {parsed.path[1:] if parsed.path else 'N/A'}")
        print(f"   Username: {parsed.username}")
        print(f"   Password: {'***' if parsed.password else 'Not set'}")
    except Exception as e:
        print(f"❌ Error parsing DATABASE_URL: {e}")
        return False
    
    # Test if we can import required modules
    try:
        import psycopg2
        print("✅ psycopg2 is available")
    except ImportError:
        print("❌ psycopg2 is not installed")
        return False
    
    try:
        import sqlalchemy
        print("✅ SQLAlchemy is available")
    except ImportError:
        print("❌ SQLAlchemy is not installed")
        return False
    
    # Test direct psycopg2 connection
    print("\n🔌 Testing direct psycopg2 connection...")
    try:
        import psycopg2
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        print(f"✅ Direct connection successful: {result}")
        
        # Get database info
        cursor.execute("SELECT current_database(), current_user, version()")
        db_name, user, version = cursor.fetchone()
        print(f"📊 Database: {db_name}")
        print(f"📊 User: {user}")
        print(f"📊 Version: {version.split()[0] if version else 'Unknown'}")
        
        # Check tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📊 Existing tables: {tables}")
        
        cursor.close()
        conn.close()
        print("✅ Direct connection test passed!")
        
    except Exception as e:
        print(f"❌ Direct connection failed: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        return False
    
    # Test SQLAlchemy connection
    print("\n🔌 Testing SQLAlchemy connection...")
    try:
        from sqlalchemy import create_engine, text
        
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            test_value = result.scalar()
            print(f"✅ SQLAlchemy connection successful: {test_value}")
        
        print("✅ SQLAlchemy connection test passed!")
        
    except Exception as e:
        print(f"❌ SQLAlchemy connection failed: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        return False
    
    print("\n🎉 All database connection tests passed!")
    return True

if __name__ == "__main__":
    success = test_database_connection()
    sys.exit(0 if success else 1) 