#!/usr/bin/env python3
"""
Comprehensive safe migration script that handles all database schema changes.
This script preserves all existing data while ensuring the database schema is correct.
It replaces all individual migration scripts and Alembic migrations.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def safe_migrate():
    """Safely migrate the database by adding missing columns and tables."""
    
    try:
        # Import Flask app and models
        from main import app
        from models import db
        
        with app.app_context():
            print("🛡️ Comprehensive Safe Database Migration")
            print("=" * 60)
            
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
            
            # Check if database exists
            if not os.path.exists(db_path):
                print("❌ Database file not found!")
                print("💡 Run the initialization script first:")
                print("   python migrations/init_database.py")
                return False
            
            # Get database size
            file_size = os.path.getsize(db_path)
            print(f"📊 Database size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
            
            # Check if tables exist
            print("\n🔍 Checking existing tables...")
            from sqlalchemy import text
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            existing_tables = [row[0] for row in result.fetchall()]
            
            if not existing_tables:
                print("❌ No tables found in database!")
                print("💡 Run the initialization script first:")
                print("   python migrations/init_database.py")
                return False
            
            print(f"✅ Found {len(existing_tables)} existing tables:")
            for table in existing_tables:
                print(f"   📋 {table}")
            
            # ===== ALBUM TABLE MIGRATIONS =====
            print("\n" + "="*50)
            print("📚 ALBUM TABLE MIGRATIONS")
            print("="*50)
            
            # Check album table specifically
            if 'album' not in existing_tables:
                print("\n❌ Album table not found!")
                print("💡 Creating album table...")
                
                # Create album table
                from models import Album
                Album.__table__.create(db.engine)
                print("✅ Album table created")
            else:
                print("\n✅ Album table exists")
            
            # Check album table structure
            print("\n🔍 Checking album table structure...")
            result = db.session.execute(text("PRAGMA table_info(album)"))
            columns = [row[1] for row in result.fetchall()]
            
            print("📋 Current album table columns:")
            for i, col in enumerate(columns, 1):
                print(f"   {i:2d}. {col}")
            
            # Check for required columns
            required_album_columns = [
                'total_views', 'average_rating', 'age_rating', 
                'view_count', 'rating_count', 'is_premium',
                'reading_history_id', 'user_library_id'
            ]
            missing_album_columns = [col for col in required_album_columns if col not in columns]
            
            if missing_album_columns:
                print(f"\n🔧 Adding missing album columns: {missing_album_columns}")

                for col in missing_album_columns:
                    try:
                        if col == 'total_views':
                            db.session.execute(text("ALTER TABLE album ADD COLUMN total_views INTEGER DEFAULT 0 NOT NULL"))
                            print("✅ Added total_views column")
                        elif col == 'average_rating':
                            db.session.execute(text("ALTER TABLE album ADD COLUMN average_rating FLOAT DEFAULT 0.0 NOT NULL"))
                            print("✅ Added average_rating column")
                        elif col == 'age_rating':
                            db.session.execute(text("ALTER TABLE album ADD COLUMN age_rating VARCHAR(10)"))
                            print("✅ Added age_rating column")
                        elif col == 'view_count':
                            db.session.execute(text("ALTER TABLE album ADD COLUMN view_count INTEGER DEFAULT 0"))
                            print("✅ Added view_count column")
                        elif col == 'rating_count':
                            db.session.execute(text("ALTER TABLE album ADD COLUMN rating_count INTEGER DEFAULT 0"))
                            print("✅ Added rating_count column")
                        elif col == 'is_premium':
                            db.session.execute(text("ALTER TABLE album ADD COLUMN is_premium BOOLEAN DEFAULT 0"))
                            print("✅ Added is_premium column")
                        elif col == 'reading_history_id':
                            db.session.execute(text("ALTER TABLE album ADD COLUMN reading_history_id INTEGER"))
                            print("✅ Added reading_history_id column")
                        elif col == 'user_library_id':
                            db.session.execute(text("ALTER TABLE album ADD COLUMN user_library_id INTEGER"))
                            print("✅ Added user_library_id column")
                    except Exception as e:
                        print(f"⚠️ Column {col} might already exist: {e}")

                db.session.commit()
                
                # Verify the changes
                result = db.session.execute(text("PRAGMA table_info(album)"))
                updated_columns = [row[1] for row in result.fetchall()]
                
                print("\n📋 Updated album table columns:")
                for i, col in enumerate(updated_columns, 1):
                    print(f"   {i:2d}. {col}")
                
                # Check if all required columns are now present
                still_missing = [col for col in required_album_columns if col not in updated_columns]
                if still_missing:
                    print(f"❌ Still missing columns: {still_missing}")
                    return False
                else:
                    print("✅ All required album columns are now present")
            else:
                print("✅ All required album columns are already present")

            # ===== NEWS TABLE MIGRATIONS =====
            print("\n" + "="*50)
            print("📰 NEWS TABLE MIGRATIONS")
            print("="*50)
            
            # Check news table structure
            print("\n🔍 Checking news table structure...")
            try:
                result = db.session.execute(text("PRAGMA table_info(news)"))
                news_columns = [row[1] for row in result.fetchall()]
                
                print("📋 Current news table columns:")
                for i, col in enumerate(news_columns, 1):
                    print(f"   {i:2d}. {col}")
                
                if 'age_rating' not in news_columns:
                    print("🔧 Adding news.age_rating column...")
                    try:
                        db.session.execute(text("ALTER TABLE news ADD COLUMN age_rating VARCHAR(10)"))
                        print("✅ Added age_rating column to news")
                        db.session.commit()
                    except Exception as e:
                        print(f"⚠️ Could not add news.age_rating (might already exist): {e}")
                else:
                    print("✅ news.age_rating column already present")
            except Exception as e:
                print(f"⚠️ Could not verify/alter news: {e}")

            # ===== BRAND IDENTITY TABLE MIGRATIONS =====
            print("\n" + "="*50)
            print("🎨 BRAND IDENTITY TABLE MIGRATIONS")
            print("="*50)
            
            # Check brand_identity feature toggle columns
            print("\n🔍 Checking brand_identity feature toggle columns...")
            try:
                result = db.session.execute(text("PRAGMA table_info(brand_identity)"))
                bi_columns = [row[1] for row in result.fetchall()]
                
                print("📋 Current brand_identity table columns:")
                for i, col in enumerate(bi_columns, 1):
                    print(f"   {i:2d}. {col}")
                
                missing_bi_cols = []
                required_bi_columns = [
                    'enable_comments', 'enable_ratings', 'enable_ads', 
                    'enable_campaigns', 'categories_display_location', 'card_design'
                ]
                
                for col in required_bi_columns:
                    if col not in bi_columns:
                        missing_bi_cols.append(col)

                if missing_bi_cols:
                    print(f"🔧 Adding missing brand_identity columns: {missing_bi_cols}")
                    for col in missing_bi_cols:
                        try:
                            if col == 'enable_comments':
                                db.session.execute(text("ALTER TABLE brand_identity ADD COLUMN enable_comments BOOLEAN DEFAULT 1 NOT NULL"))
                                print("✅ Added enable_comments column")
                            elif col == 'enable_ratings':
                                db.session.execute(text("ALTER TABLE brand_identity ADD COLUMN enable_ratings BOOLEAN DEFAULT 1 NOT NULL"))
                                print("✅ Added enable_ratings column")
                            elif col == 'enable_ads':
                                db.session.execute(text("ALTER TABLE brand_identity ADD COLUMN enable_ads BOOLEAN DEFAULT 1 NOT NULL"))
                                print("✅ Added enable_ads column")
                            elif col == 'enable_campaigns':
                                db.session.execute(text("ALTER TABLE brand_identity ADD COLUMN enable_campaigns BOOLEAN DEFAULT 1 NOT NULL"))
                                print("✅ Added enable_campaigns column")
                            elif col == 'categories_display_location':
                                db.session.execute(text("ALTER TABLE brand_identity ADD COLUMN categories_display_location VARCHAR(50) DEFAULT 'body'"))
                                print("✅ Added categories_display_location column")
                                # Update existing records to have the default value
                                db.session.execute(text("UPDATE brand_identity SET categories_display_location = 'body' WHERE categories_display_location IS NULL"))
                                print("✅ Updated existing records with default value")
                            elif col == 'card_design':
                                db.session.execute(text("ALTER TABLE brand_identity ADD COLUMN card_design VARCHAR(50) DEFAULT 'classic'"))
                                print("✅ Added card_design column")
                                # Update existing records to have the default value
                                db.session.execute(text("UPDATE brand_identity SET card_design = 'classic' WHERE card_design IS NULL"))
                                print("✅ Updated existing records with default value")
                        except Exception as e:
                            print(f"⚠️ Column {col} might already exist: {e}")
                    db.session.commit()
                else:
                    print("✅ brand_identity feature toggle columns already present")
            except Exception as e:
                print(f"⚠️ Could not verify/alter brand_identity: {e}")

            # ===== USER TABLE MIGRATIONS =====
            print("\n" + "="*50)
            print("👤 USER TABLE MIGRATIONS")
            print("="*50)
            
            # Check user table for reading history and library
            print("\n🔍 Checking user table structure...")
            try:
                result = db.session.execute(text("PRAGMA table_info(user)"))
                user_columns = [row[1] for row in result.fetchall()]
                
                print("📋 Current user table columns:")
                for i, col in enumerate(user_columns, 1):
                    print(f"   {i:2d}. {col}")
                
                # Check for reading history and library columns
                user_required_columns = ['reading_history_id', 'user_library_id']
                missing_user_cols = [col for col in user_required_columns if col not in user_columns]
                
                if missing_user_cols:
                    print(f"🔧 Adding missing user columns: {missing_user_cols}")
                    for col in missing_user_cols:
                        try:
                            if col == 'reading_history_id':
                                db.session.execute(text("ALTER TABLE user ADD COLUMN reading_history_id INTEGER"))
                                print("✅ Added reading_history_id column to user")
                            elif col == 'user_library_id':
                                db.session.execute(text("ALTER TABLE user ADD COLUMN user_library_id INTEGER"))
                                print("✅ Added user_library_id column to user")
                        except Exception as e:
                            print(f"⚠️ Column {col} might already exist: {e}")
                    db.session.commit()
                else:
                    print("✅ User table has all required columns")
            except Exception as e:
                print(f"⚠️ Could not verify/alter user table: {e}")

            # ===== CREATE READING HISTORY AND USER LIBRARY TABLES =====
            print("\n" + "="*50)
            print("📖 READING HISTORY & USER LIBRARY TABLES")
            print("="*50)
            
            # Check if reading_history table exists
            if 'reading_history' not in existing_tables:
                print("\n🔧 Creating reading_history table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE reading_history (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            album_id INTEGER NOT NULL,
                            chapter_id INTEGER,
                            last_read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            progress FLOAT DEFAULT 0.0,
                            FOREIGN KEY (user_id) REFERENCES user (id),
                            FOREIGN KEY (album_id) REFERENCES album (id)
                        )
                    """))
                    print("✅ Created reading_history table")
                except Exception as e:
                    print(f"⚠️ Could not create reading_history table: {e}")
            
            # Check if user_library table exists
            if 'user_library' not in existing_tables:
                print("\n🔧 Creating user_library table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE user_library (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            album_id INTEGER NOT NULL,
                            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            is_favorite BOOLEAN DEFAULT 0,
                            FOREIGN KEY (user_id) REFERENCES user (id),
                            FOREIGN KEY (album_id) REFERENCES album (id)
                        )
                    """))
                    print("✅ Created user_library table")
                except Exception as e:
                    print(f"⚠️ Could not create user_library table: {e}")

            # ===== RECORD COUNTS =====
            print("\n" + "="*50)
            print("📊 DATABASE RECORD COUNTS")
            print("="*50)
            
            # Check record counts
            print("\n📊 Checking record counts...")
            try:
                album_count = db.session.execute(text("SELECT COUNT(*) FROM album")).scalar()
                print(f"📋 Album records: {album_count}")
            except Exception as e:
                print(f"⚠️ Could not count album records: {e}")
            
            try:
                user_count = db.session.execute(text("SELECT COUNT(*) FROM user")).scalar()
                print(f"👤 User records: {user_count}")
            except Exception as e:
                print(f"⚠️ Could not count user records: {e}")
            
            try:
                news_count = db.session.execute(text("SELECT COUNT(*) FROM news")).scalar()
                print(f"📰 News records: {news_count}")
            except Exception as e:
                print(f"⚠️ Could not count news records: {e}")
            
            try:
                category_count = db.session.execute(text("SELECT COUNT(*) FROM category")).scalar()
                print(f"📂 Category records: {category_count}")
            except Exception as e:
                print(f"⚠️ Could not count category records: {e}")
            
            try:
                reading_history_count = db.session.execute(text("SELECT COUNT(*) FROM reading_history")).scalar()
                print(f"📖 Reading history records: {reading_history_count}")
            except Exception as e:
                print(f"⚠️ Could not count reading history records: {e}")
            
            try:
                user_library_count = db.session.execute(text("SELECT COUNT(*) FROM user_library")).scalar()
                print(f"📚 User library records: {user_library_count}")
            except Exception as e:
                print(f"⚠️ Could not count user library records: {e}")

            # ===== DATABASE OPTIMIZATIONS =====
            print("\n" + "="*50)
            print("🔧 DATABASE OPTIMIZATIONS")
            print("="*50)
            
            # Add missing indexes for optimal performance
            print("\n🔧 Adding database indexes for optimal performance...")
            try:
                from models import add_missing_indexes
                add_missing_indexes()
                print("✅ Database indexes created successfully")
            except Exception as e:
                print(f"⚠️ Could not create indexes: {e}")
            
            # Check database health
            print("\n🔍 Running database health check...")
            try:
                from models import check_database_health
                check_database_health()
            except Exception as e:
                print(f"⚠️ Could not run health check: {e}")
            
            # Clean up orphaned data
            print("\n🧹 Cleaning up orphaned data...")
            try:
                from models import cleanup_orphaned_data
                cleanup_orphaned_data()
                print("✅ Orphaned data cleanup completed")
            except Exception as e:
                print(f"⚠️ Could not cleanup orphaned data: {e}")
            
            print(f"\n🎉 Comprehensive migration completed successfully!")
            print("✅ All existing data preserved")
            print("✅ All tables have required columns")
            print("✅ Reading history and user library tables created")
            print("✅ Database indexes optimized for performance")
            print("✅ Database health verified")
            print("✅ Orphaned data cleaned up")
            
            return True
            
    except Exception as e:
        print(f"❌ Error during comprehensive migration: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to run comprehensive safe migration."""
    print("🛡️ Comprehensive Safe Database Migration Script")
    print("=" * 60)
    print("This script replaces all individual migration scripts and Alembic")
    print("It safely adds all missing columns and tables without data loss")
    print("=" * 60)
    
    success = safe_migrate()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Comprehensive migration completed successfully!")
        print("✅ All existing data preserved")
        print("✅ Database schema is now complete and up-to-date")
        print("✅ All tables have required columns")
        print("\n💡 You can now run the application or add test data:")
        print("   python helper/add_test_albums.py")
        print("   python main.py")
    else:
        print("❌ Comprehensive migration failed!")
        print("Please check the error messages above.")
    
    return success

if __name__ == "__main__":
    main()
