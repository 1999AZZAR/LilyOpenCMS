#!/usr/bin/env python3
"""
Script to find the database file on the production server.
"""

import os
import subprocess
import sys

def find_database_files():
    """Find all database files in the project directory."""
    
    print("🔍 Searching for database files...")
    print("=" * 50)
    
    # Common database file patterns
    db_patterns = [
        "*.db",
        "*.sqlite",
        "*.sqlite3",
        "database.db",
        "app.db",
        "flask.db"
    ]
    
    # Common search paths
    search_paths = [
        ".",
        "./instance",
        "./data",
        "./database",
        "./db",
        "/home/lilycmsc/domains/lilycms.com/public_html/beranda",
        "/home/lilycmsc/domains/lilycms.com/public_html/beranda/instance",
        "/home/lilycmsc/domains/lilycms.com/public_html/beranda/data"
    ]
    
    found_files = []
    
    for pattern in db_patterns:
        for search_path in search_paths:
            if os.path.exists(search_path):
                try:
                    # Use find command to search
                    cmd = f"find {search_path} -name '{pattern}' -type f 2>/dev/null"
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    
                    if result.stdout.strip():
                        files = result.stdout.strip().split('\n')
                        for file in files:
                            if file and os.path.exists(file):
                                file_size = os.path.getsize(file)
                                found_files.append((file, file_size))
                                print(f"✅ Found: {file} ({file_size:,} bytes)")
                except Exception as e:
                    continue
    
    if not found_files:
        print("❌ No database files found!")
        print("\n💡 Try searching manually:")
        print("   find . -name '*.db' -type f")
        print("   find . -name '*.sqlite*' -type f")
        print("   ls -la instance/")
        print("   ls -la data/")
        return False
    
    print(f"\n📊 Found {len(found_files)} database file(s):")
    for file_path, file_size in found_files:
        print(f"   📁 {file_path} ({file_size:,} bytes)")
    
    return True

def check_flask_config():
    """Check Flask configuration for database URI."""
    
    print("\n🔍 Checking Flask configuration...")
    print("=" * 50)
    
    try:
        # Try to import Flask app
        sys.path.insert(0, os.getcwd())
        from main import app
        
        with app.app_context():
            database_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            print(f"🔗 Database URI: {database_uri}")
            
            if database_uri:
                # Extract path from URI
                if database_uri.startswith('sqlite:///'):
                    db_path = database_uri.replace('sqlite:///', '')
                elif database_uri.startswith('sqlite://'):
                    db_path = database_uri.replace('sqlite://', '')
                else:
                    db_path = database_uri
                
                print(f"📁 Extracted path: {db_path}")
                
                if os.path.exists(db_path):
                    file_size = os.path.getsize(db_path)
                    print(f"✅ Database exists: {db_path} ({file_size:,} bytes)")
                    return db_path
                else:
                    print(f"❌ Database not found at: {db_path}")
            else:
                print("❌ No database URI found in Flask config")
                
    except Exception as e:
        print(f"❌ Error checking Flask config: {e}")
    
    return None

def main():
    """Main function to find database files."""
    print("🔍 Database File Finder")
    print("=" * 50)
    
    # Search for database files
    found_files = find_database_files()
    
    # Check Flask configuration
    flask_db_path = check_flask_config()
    
    print("\n" + "=" * 50)
    if found_files or flask_db_path:
        print("✅ Database files found!")
        if flask_db_path:
            print(f"🎯 Use this path in migration scripts: {flask_db_path}")
    else:
        print("❌ No database files found!")
        print("💡 Please check the project structure and database configuration.")
    
    return found_files or flask_db_path

if __name__ == "__main__":
    main()
