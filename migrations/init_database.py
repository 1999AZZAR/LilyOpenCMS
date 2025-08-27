#!/usr/bin/env python3
"""
Database initialization script that creates all necessary tables with the correct schema.
This script ensures the database is properly set up with all required tables and columns.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def init_database():
    """Initialize the database with all necessary tables."""
    
    try:
        # Import Flask app and models
        from main import app
        from models import db
        
        with app.app_context():
            print("🚀 Initializing database...")
            print("=" * 50)
            
            # Get database info
            database_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            print(f"🔍 Database URI: {database_uri}")
            
            # Extract database path
            if database_uri.startswith('sqlite:///'):
                db_path = database_uri.replace('sqlite:///', '')
            elif database_uri.startswith('sqlite://'):
                db_path = database_uri.replace('sqlite://', '')
            else:
                db_path = database_uri
            
            print(f"📁 Database path: {db_path}")
            
            # Create database directory if it doesn't exist
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                print(f"📁 Created database directory: {db_dir}")
            
            # Drop all tables and recreate them
            print("🗑️ Dropping all existing tables...")
            db.drop_all()
            print("✅ All tables dropped")
            
            # Create all tables
            print("🏗️ Creating all tables...")
            db.create_all()
            print("✅ All tables created")
            
            # Verify the album table structure
            print("\n🔍 Verifying album table structure...")
            
            # Get table info using raw SQL
            from sqlalchemy import text
            result = db.session.execute(text("PRAGMA table_info(album)"))
            columns = [row[1] for row in result.fetchall()]
            
            print("📋 Album table columns:")
            for i, col in enumerate(columns, 1):
                print(f"   {i:2d}. {col}")
            
            # Check for required columns
            required_columns = ['total_views', 'average_rating']
            missing_columns = [col for col in required_columns if col not in columns]
            
            if missing_columns:
                print(f"\n❌ Missing columns: {missing_columns}")
                print("🔧 Adding missing columns...")
                
                                        for col in missing_columns:
                            if col == 'total_views':
                                db.session.execute(text("ALTER TABLE album ADD COLUMN total_views INTEGER DEFAULT 0 NOT NULL"))
                                print("✅ Added total_views column")
                            elif col == 'average_rating':
                                db.session.execute(text("ALTER TABLE album ADD COLUMN average_rating FLOAT DEFAULT 0.0 NOT NULL"))
                                print("✅ Added average_rating column")
                
                db.session.commit()
                
                # Verify again
                result = db.session.execute(text("PRAGMA table_info(album)"))
                updated_columns = [row[1] for row in result.fetchall()]
                
                print("\n📋 Updated album table columns:")
                for i, col in enumerate(updated_columns, 1):
                    print(f"   {i:2d}. {col}")
            else:
                print("✅ All required columns are present")
            
            # List all tables
            print("\n📊 All database tables:")
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result.fetchall()]
            
            for i, table in enumerate(tables, 1):
                print(f"   {i:2d}. {table}")
            
            print(f"\n🎉 Database initialization completed!")
            print(f"✅ Created {len(tables)} tables")
            print(f"✅ Album table has {len(columns)} columns")
            
            return True
            
    except Exception as e:
        print(f"❌ Error during database initialization: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_database():
    """Verify that the database is properly initialized."""
    
    try:
        from main import app
        from models import db, Album, User, Category, News, Image
        
        with app.app_context():
            print("\n🔍 Verifying database setup...")
            print("=" * 50)
            
            # Check if tables exist
            tables_to_check = [
                ('album', Album),
                ('user', User),
                ('category', Category),
                ('news', News),
                ('image', Image)
            ]
            
            for table_name, model_class in tables_to_check:
                try:
                    # Try to query the table
                    count = model_class.query.count()
                    print(f"✅ {table_name} table: {count} records")
                except Exception as e:
                    print(f"❌ {table_name} table error: {e}")
            
            # Check album table structure specifically
            try:
                from sqlalchemy import text
                result = db.session.execute(text("PRAGMA table_info(album)"))
                columns = [row[1] for row in result.fetchall()]
                
                required_columns = ['total_views', 'average_rating']
                missing = [col for col in required_columns if col not in columns]
                
                if missing:
                    print(f"❌ Album table missing columns: {missing}")
                    return False
                else:
                    print("✅ Album table has all required columns")
                    return True
                    
            except Exception as e:
                print(f"❌ Error checking album table: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False

def main():
    """Main function to initialize the database."""
    print("🚀 Database Initialization Script")
    print("=" * 50)
    
    # Initialize database
    success = init_database()
    
    if success:
        # Verify the setup
        verify_success = verify_database()
        
        print("\n" + "=" * 50)
        if verify_success:
            print("🎉 Database initialization completed successfully!")
            print("✅ All tables created with correct schema")
            print("✅ Album table has all required columns")
            print("\n💡 You can now run the album generation script:")
            print("   python helper/add_test_albums.py")
        else:
            print("❌ Database verification failed!")
            print("Please check the error messages above.")
    else:
        print("❌ Database initialization failed!")
        print("Please check the error messages above.")
    
    return success

if __name__ == "__main__":
    main()
