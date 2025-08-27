#!/usr/bin/env python3
"""
Migration script to add total_views and average_rating columns to the album table.
This script should be run on the production server to sync the database schema.
"""

import sys
import os
import sqlite3
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_migration():
    """Run the migration to add missing columns to the album table."""
    
    # Database path - adjust this to match your production database location
    db_path = "/home/lilycmsc/domains/lilycms.com/public_html/beranda/instance/database.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        print("Please update the db_path variable in this script to point to your database file.")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Checking current album table structure...")
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(album)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"Current columns: {columns}")
        
        # Check if total_views column exists
        if 'total_views' not in columns:
            print("📊 Adding total_views column...")
            cursor.execute("ALTER TABLE album ADD COLUMN total_views INTEGER DEFAULT 0 NOT NULL")
            print("✅ total_views column added successfully")
        else:
            print("✅ total_views column already exists")
        
        # Check if average_rating column exists
        if 'average_rating' not in columns:
            print("⭐ Adding average_rating column...")
            cursor.execute("ALTER TABLE album ADD COLUMN average_rating FLOAT DEFAULT 0.0 NOT NULL")
            print("✅ average_rating column added successfully")
        else:
            print("✅ average_rating column already exists")
        
        # Commit the changes
        conn.commit()
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(album)")
        updated_columns = [column[1] for column in cursor.fetchall()]
        print(f"Updated columns: {updated_columns}")
        
        # Check if both columns are now present
        if 'total_views' in updated_columns and 'average_rating' in updated_columns:
            print("🎉 Migration completed successfully!")
            print("✅ Both total_views and average_rating columns are now available")
            return True
        else:
            print("❌ Migration failed - columns not found after update")
            return False
            
    except sqlite3.Error as e:
        print(f"❌ SQLite error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Main function to run the migration."""
    print("🚀 Starting Album Migration...")
    print("=" * 50)
    
    success = run_migration()
    
    print("=" * 50)
    if success:
        print("✅ Migration completed successfully!")
        print("You can now run the album generation script.")
    else:
        print("❌ Migration failed!")
        print("Please check the error messages above and try again.")
    
    return success

if __name__ == "__main__":
    main()
