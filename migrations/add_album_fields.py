"""
Migration script to add missing fields to Album model
"""

from sqlalchemy import text
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import db

def upgrade():
    """Add missing fields to Album table"""
    try:
        # Add total_views column if it doesn't exist
        db.session.execute(text("""
            ALTER TABLE album 
            ADD COLUMN total_views INTEGER DEFAULT 0 NOT NULL
        """))
        
        # Add average_rating column if it doesn't exist
        db.session.execute(text("""
            ALTER TABLE album 
            ADD COLUMN average_rating FLOAT DEFAULT 0.0 NOT NULL
        """))
        
        db.session.commit()
        print("✅ Successfully added missing fields to Album table")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error adding fields to Album table: {e}")
        # Check if columns already exist
        try:
            db.session.execute(text("SELECT total_views FROM album LIMIT 1"))
            print("ℹ️  total_views column already exists")
        except:
            print("ℹ️  total_views column does not exist")
            
        try:
            db.session.execute(text("SELECT average_rating FROM album LIMIT 1"))
            print("ℹ️  average_rating column already exists")
        except:
            print("ℹ️  average_rating column does not exist")

if __name__ == "__main__":
    from main import app
    with app.app_context():
        upgrade()
