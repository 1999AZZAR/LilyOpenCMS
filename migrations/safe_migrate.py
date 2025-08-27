#!/usr/bin/env python3
"""
Safe migration script that adds missing columns without dropping existing data.
This script preserves all existing data while ensuring the database schema is correct.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def safe_migrate():
    """Safely migrate the database by adding missing columns."""
    
    try:
        # Import Flask app and models
        from main import app
        from models import db
        
        with app.app_context():
            print("🛡️ Safe Database Migration")
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
            required_columns = ['total_views', 'average_rating', 'age_rating']
            missing_columns = [col for col in required_columns if col not in columns]
            
            if missing_columns:
                print(f"\n🔧 Adding missing columns: {missing_columns}")

                for col in missing_columns:
                    try:
                        if col == 'total_views':
                            db.session.execute(text("ALTER TABLE album ADD COLUMN total_views INTEGER DEFAULT 0 NOT NULL"))
                            print("✅ Added total_views column")
                        elif col == 'average_rating':
                            db.session.execute(text("ALTER TABLE album ADD COLUMN average_rating FLOAT DEFAULT 0.0 NOT NULL"))
                            print("✅ Added average_rating column")
                        elif col == 'age_rating':
                            db.session.execute(text("ALTER TABLE album ADD COLUMN age_rating VARCHAR(10)"))
                            print("✅ Added age_rating column to album")
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
                still_missing = [col for col in required_columns if col not in updated_columns]
                if still_missing:
                    print(f"❌ Still missing columns: {still_missing}")
                    return False
                else:
                    print("✅ All required columns are now present")
            else:
                print("✅ All required columns are already present")

            # --- Ensure news has age_rating column ---
            print("\n🔍 Checking news table structure...")
            try:
                result = db.session.execute(text("PRAGMA table_info(news)"))
                news_columns = [row[1] for row in result.fetchall()]
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

            # --- Ensure brand_identity has UI toggle columns ---
            print("\n🔍 Checking brand_identity feature toggle columns...")
            try:
                result = db.session.execute(text("PRAGMA table_info(brand_identity)"))
                bi_columns = [row[1] for row in result.fetchall()]
                missing_bi_cols = []
                if 'enable_comments' not in bi_columns:
                    missing_bi_cols.append('enable_comments')
                if 'enable_ratings' not in bi_columns:
                    missing_bi_cols.append('enable_ratings')
                if 'enable_ads' not in bi_columns:
                    missing_bi_cols.append('enable_ads')
                if 'enable_campaigns' not in bi_columns:
                    missing_bi_cols.append('enable_campaigns')
                if 'categories_display_location' not in bi_columns:
                    missing_bi_cols.append('categories_display_location')
                if 'card_design' not in bi_columns:
                    missing_bi_cols.append('card_design')

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
            
            print(f"\n🎉 Safe migration completed successfully!")
            print("✅ All existing data preserved")
            print("✅ Album table has all required columns")
            
            return True
            
    except Exception as e:
        print(f"❌ Error during safe migration: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to run safe migration."""
    print("🛡️ Safe Database Migration Script")
    print("=" * 50)
    
    success = safe_migrate()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Safe migration completed successfully!")
        print("✅ All existing data preserved")
        print("✅ Database schema is now correct")
        print("\n💡 You can now run the album generation script:")
        print("   python helper/add_test_albums.py")
    else:
        print("❌ Safe migration failed!")
        print("Please check the error messages above.")
    
    return success

if __name__ == "__main__":
    main()
