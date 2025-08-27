#!/usr/bin/env python3
"""
Script to check the current album table structure and verify if migration is needed.
"""

import sys
import os
import sqlite3
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_album_table():
    """Check the current album table structure."""
    
    # Database path - adjust this to match your production database location
    db_path = "/home/lilycmsc/domains/lilycms.com/public_html/beranda/instance/database.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Checking album table structure...")
        print("=" * 50)
        
        # Get table info
        cursor.execute("PRAGMA table_info(album)")
        columns = cursor.fetchall()
        
        print("📋 Current album table columns:")
        print("-" * 50)
        
        required_columns = ['total_views', 'average_rating']
        missing_columns = []
        
        for column in columns:
            col_id, col_name, col_type, not_null, default_val, primary_key = column
            status = "✅" if col_name in required_columns else "  "
            print(f"{status} {col_id:2d}. {col_name:<20} {col_type:<15} {'NOT NULL' if not_null else 'NULL':<10} {default_val or 'NULL'}")
            
            if col_name in required_columns:
                required_columns.remove(col_name)
        
        # Check for missing columns
        if required_columns:
            print("\n❌ Missing required columns:")
            for col in required_columns:
                print(f"   - {col}")
            print("\n💡 Run the migration script to add these columns:")
            print("   python migrations/add_album_views_rating.py")
            return False
        else:
            print("\n✅ All required columns are present!")
            print("🎉 The album table is ready for use.")
            return True
            
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
    """Main function to check the table structure."""
    print("🔍 Album Table Structure Checker")
    print("=" * 50)
    
    success = check_album_table()
    
    print("=" * 50)
    if success:
        print("✅ Table structure is correct!")
    else:
        print("❌ Table structure needs migration!")
    
    return success

if __name__ == "__main__":
    main()
