"""
Migration to add categories_display_location field to brand_identity table
"""

import sqlite3
import os
from pathlib import Path

def migrate():
    # Get the database path
    db_path = Path("instance/database.db")
    
    if not db_path.exists():
        print("Database not found. Skipping migration.")
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(brand_identity)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'categories_display_location' not in columns:
            # Add the new column
            cursor.execute("""
                ALTER TABLE brand_identity 
                ADD COLUMN categories_display_location VARCHAR(50) DEFAULT 'body'
            """)
            
            # Update existing records to have the default value
            cursor.execute("""
                UPDATE brand_identity 
                SET categories_display_location = 'body' 
                WHERE categories_display_location IS NULL
            """)
            
            conn.commit()
            print("✅ Successfully added categories_display_location column to brand_identity table")
        else:
            print("ℹ️  categories_display_location column already exists")
            
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
