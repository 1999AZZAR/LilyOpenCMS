#!/usr/bin/env python3
"""
Script to check the database path using Flask app context.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_database_path():
    """Check the database path using Flask app context."""
    
    try:
        # Import Flask app
        from main import app
        
        with app.app_context():
            # Get the database URI from Flask config
            database_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            print(f"🔍 Database URI: {database_uri}")
            
            # Extract the database path from the URI
            if database_uri.startswith('sqlite:///'):
                db_path = database_uri.replace('sqlite:///', '')
            elif database_uri.startswith('sqlite://'):
                db_path = database_uri.replace('sqlite://', '')
            else:
                print(f"❌ Unsupported database URI: {database_uri}")
                return False
            
            print(f"📁 Database path: {db_path}")
            
            if os.path.exists(db_path):
                print(f"✅ Database file exists at: {db_path}")
                
                # Get file size
                file_size = os.path.getsize(db_path)
                print(f"📊 Database file size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
                
                return True
            else:
                print(f"❌ Database file not found at: {db_path}")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to check database path."""
    print("🔍 Database Path Checker")
    print("=" * 50)
    
    success = check_database_path()
    
    print("=" * 50)
    if success:
        print("✅ Database path found and file exists!")
    else:
        print("❌ Database path check failed!")
    
    return success

if __name__ == "__main__":
    main()
