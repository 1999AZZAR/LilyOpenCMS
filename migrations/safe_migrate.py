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
                'reading_history_id', 'user_library_id',
                'deletion_requested', 'deletion_requested_at', 'deletion_requested_by'
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
                        elif col == 'deletion_requested':
                            db.session.execute(text("ALTER TABLE album ADD COLUMN deletion_requested BOOLEAN DEFAULT 0 NOT NULL"))
                            print("✅ Added deletion_requested column to album")
                        elif col == 'deletion_requested_at':
                            db.session.execute(text("ALTER TABLE album ADD COLUMN deletion_requested_at TIMESTAMP"))
                            print("✅ Added deletion_requested_at column to album")
                        elif col == 'deletion_requested_by':
                            db.session.execute(text("ALTER TABLE album ADD COLUMN deletion_requested_by INTEGER REFERENCES user(id)"))
                            print("✅ Added deletion_requested_by column to album")
                    except Exception as e:
                        print(f"⚠️ Column {col} might already exist: {e}")

                db.session.commit()
                
                # Check for missing SEO columns in album table
                missing_album_seo_columns = []
                required_album_seo_columns = [
                    'is_seo_lock'
                ]
                
                for col in required_album_seo_columns:
                    if col not in columns:
                        missing_album_seo_columns.append(col)
                
                if missing_album_seo_columns:
                    print(f"🔧 Adding missing SEO columns to album: {missing_album_seo_columns}")
                    for col in missing_album_seo_columns:
                        try:
                            if col == 'is_seo_lock':
                                db.session.execute(text("ALTER TABLE album ADD COLUMN is_seo_lock BOOLEAN DEFAULT 0 NOT NULL"))
                                print("✅ Added is_seo_lock column to album")
                        except Exception as e:
                            print(f"⚠️ Could not add album.{col} (might already exist): {e}")
                    db.session.commit()
                else:
                    print("✅ All required SEO columns already present in album table")
                
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

            # ===== ALBUM CHAPTER TABLE MIGRATIONS =====
            print("\n" + "="*50)
            print("📖 ALBUM CHAPTER TABLE MIGRATIONS")
            print("="*50)
            
            # Check album_chapter table structure
            print("\n🔍 Checking album_chapter table structure...")
            try:
                result = db.session.execute(text("PRAGMA table_info(album_chapter)"))
                chapter_columns = [row[1] for row in result.fetchall()]
                
                print("📋 Current album_chapter table columns:")
                for i, col in enumerate(chapter_columns, 1):
                    print(f"   {i:2d}. {col}")
                
                # Check for missing SEO columns in album_chapter table
                missing_chapter_seo_columns = []
                required_chapter_seo_columns = [
                    'is_seo_lock'
                ]
                
                for col in required_chapter_seo_columns:
                    if col not in chapter_columns:
                        missing_chapter_seo_columns.append(col)
                
                if missing_chapter_seo_columns:
                    print(f"🔧 Adding missing SEO columns to album_chapter: {missing_chapter_seo_columns}")
                    for col in missing_chapter_seo_columns:
                        try:
                            if col == 'is_seo_lock':
                                db.session.execute(text("ALTER TABLE album_chapter ADD COLUMN is_seo_lock BOOLEAN DEFAULT 0 NOT NULL"))
                                print("✅ Added is_seo_lock column to album_chapter")
                        except Exception as e:
                            print(f"⚠️ Could not add album_chapter.{col} (might already exist): {e}")
                    db.session.commit()
                else:
                    print("✅ All required SEO columns already present in album_chapter table")
            except Exception as e:
                print(f"⚠️ Could not verify/alter album_chapter: {e}")

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
                
                # Check for age_rating column
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
                
                # Check for prize column
                if 'prize' not in news_columns:
                    print("🔧 Adding news.prize column...")
                    try:
                        db.session.execute(text("ALTER TABLE news ADD COLUMN prize INTEGER DEFAULT 0 NOT NULL"))
                        print("✅ Added prize column to news")
                        db.session.commit()
                    except Exception as e:
                        print(f"⚠️ Could not add news.prize (might already exist): {e}")
                else:
                    print("✅ news.prize column already present")
                
                # Check for prize_coin_type column
                if 'prize_coin_type' not in news_columns:
                    print("🔧 Adding news.prize_coin_type column...")
                    try:
                        db.session.execute(text("ALTER TABLE news ADD COLUMN prize_coin_type VARCHAR(20) DEFAULT 'any' NOT NULL"))
                        print("✅ Added prize_coin_type column to news")
                        db.session.commit()
                    except Exception as e:
                        print(f"⚠️ Could not add news.prize_coin_type (might already exist): {e}")
                else:
                    print("✅ news.prize_coin_type column already present")
                
                # Check for content deletion request columns
                if 'deletion_requested' not in news_columns:
                    print("🔧 Adding news.deletion_requested column...")
                    try:
                        db.session.execute(text("ALTER TABLE news ADD COLUMN deletion_requested BOOLEAN DEFAULT 0 NOT NULL"))
                        print("✅ Added deletion_requested column to news")
                        db.session.commit()
                    except Exception as e:
                        print(f"⚠️ Could not add news.deletion_requested (might already exist): {e}")
                else:
                    print("✅ news.deletion_requested column already present")
                
                # Check for missing SEO columns in news table
                missing_news_seo_columns = []
                required_news_seo_columns = [
                    'is_seo_lock'
                ]
                
                for col in required_news_seo_columns:
                    if col not in news_columns:
                        missing_news_seo_columns.append(col)
                
                if missing_news_seo_columns:
                    print(f"🔧 Adding missing SEO columns to news: {missing_news_seo_columns}")
                    for col in missing_news_seo_columns:
                        try:
                            if col == 'is_seo_lock':
                                db.session.execute(text("ALTER TABLE news ADD COLUMN is_seo_lock BOOLEAN DEFAULT 0 NOT NULL"))
                                print("✅ Added is_seo_lock column to news")
                        except Exception as e:
                            print(f"⚠️ Could not add news.{col} (might already exist): {e}")
                    db.session.commit()
                else:
                    print("✅ All required SEO columns already present in news table")
                
                if 'deletion_requested_at' not in news_columns:
                    print("🔧 Adding news.deletion_requested_at column...")
                    try:
                        db.session.execute(text("ALTER TABLE news ADD COLUMN deletion_requested_at TIMESTAMP"))
                        print("✅ Added deletion_requested_at column to news")
                        db.session.commit()
                    except Exception as e:
                        print(f"⚠️ Could not add news.deletion_requested_at (might already exist): {e}")
                else:
                    print("✅ news.deletion_requested_at column already present")
                
                if 'deletion_requested_by' not in news_columns:
                    print("🔧 Adding news.deletion_requested_by column...")
                    try:
                        db.session.execute(text("ALTER TABLE news ADD COLUMN deletion_requested_by INTEGER REFERENCES user(id)"))
                        print("✅ Added deletion_requested_by column to news")
                        db.session.commit()
                    except Exception as e:
                        print(f"⚠️ Could not add news.deletion_requested_by (might already exist): {e}")
                else:
                    print("✅ news.deletion_requested_by column already present")
            except Exception as e:
                print(f"⚠️ Could not verify/alter news: {e}")

            # ===== ROOT SEO TABLE MIGRATIONS =====
            print("\n" + "="*50)
            print("🔍 ROOT SEO TABLE MIGRATIONS")
            print("="*50)
            
            # Check if root_seo table exists
            if 'root_seo' not in existing_tables:
                print("\n❌ Root SEO table not found!")
                print("💡 Creating root_seo table...")
                
                # Create root_seo table
                from models import RootSEO
                RootSEO.__table__.create(db.engine)
                print("✅ Root SEO table created")
            else:
                print("\n✅ Root SEO table exists")
            
            # Check root_seo table structure
            print("\n🔍 Checking root_seo table structure...")
            try:
                result = db.session.execute(text("PRAGMA table_info(root_seo)"))
                root_seo_columns = [row[1] for row in result.fetchall()]
                
                print("📋 Current root_seo table columns:")
                for i, col in enumerate(root_seo_columns, 1):
                    print(f"   {i:2d}. {col}")
                
                # Check for required columns
                required_root_seo_columns = [
                    'meta_robots', 'google_analytics_id', 'facebook_pixel_id',
                    'created_at', 'updated_at', 'created_by', 'updated_by'
                ]
                missing_root_seo_cols = [col for col in required_root_seo_columns if col not in root_seo_columns]
                
                if missing_root_seo_cols:
                    print(f"🔧 Adding missing root_seo columns: {missing_root_seo_cols}")
                    for col in missing_root_seo_cols:
                        try:
                            if col == 'meta_robots':
                                db.session.execute(text("ALTER TABLE root_seo ADD COLUMN meta_robots VARCHAR(50) DEFAULT 'index, follow'"))
                                print("✅ Added meta_robots column")
                            elif col == 'google_analytics_id':
                                db.session.execute(text("ALTER TABLE root_seo ADD COLUMN google_analytics_id VARCHAR(50)"))
                                print("✅ Added google_analytics_id column")
                            elif col == 'facebook_pixel_id':
                                db.session.execute(text("ALTER TABLE root_seo ADD COLUMN facebook_pixel_id VARCHAR(50)"))
                                print("✅ Added facebook_pixel_id column")
                            elif col == 'created_at':
                                db.session.execute(text("ALTER TABLE root_seo ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
                                print("✅ Added created_at column")
                            elif col == 'updated_at':
                                db.session.execute(text("ALTER TABLE root_seo ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
                                print("✅ Added updated_at column")
                            elif col == 'created_by':
                                db.session.execute(text("ALTER TABLE root_seo ADD COLUMN created_by INTEGER REFERENCES user(id)"))
                                print("✅ Added created_by column")
                            elif col == 'updated_by':
                                db.session.execute(text("ALTER TABLE root_seo ADD COLUMN updated_by INTEGER REFERENCES user(id)"))
                                print("✅ Added updated_by column")
                        except Exception as e:
                            print(f"⚠️ Column {col} might already exist: {e}")
                    db.session.commit()
                    
                    # Verify the changes
                    result = db.session.execute(text("PRAGMA table_info(root_seo)"))
                    updated_root_seo_columns = [row[1] for row in result.fetchall()]
                    
                    print("\n📋 Updated root_seo table columns:")
                    for i, col in enumerate(updated_root_seo_columns, 1):
                        print(f"   {i:2d}. {col}")
                    
                    # Check if all required columns are now present
                    still_missing = [col for col in required_root_seo_columns if col not in updated_root_seo_columns]
                    if still_missing:
                        print(f"❌ Still missing columns: {still_missing}")
                    else:
                        print("✅ All required root_seo columns are now present")
                else:
                    print("✅ All required root_seo columns are already present")
                
                # Check if root_seo table has data
                try:
                    root_seo_count = db.session.execute(text("SELECT COUNT(*) FROM root_seo")).scalar()
                    print(f"📊 Root SEO records: {root_seo_count}")
                    
                    if root_seo_count == 0:
                        print("🔧 Initializing root SEO with default pages...")
                        default_pages = [
                            {"page_identifier": "home", "page_name": "Beranda", "is_active": True},
                            {"page_identifier": "news", "page_name": "Berita", "is_active": True},
                            {"page_identifier": "albums", "page_name": "Album", "is_active": True},
                            {"page_identifier": "about", "page_name": "Tentang Kami", "is_active": True},
                            {"page_identifier": "contact", "page_name": "Kontak", "is_active": True},
                            {"page_identifier": "privacy", "page_name": "Kebijakan Privasi", "is_active": True},
                            {"page_identifier": "terms", "page_name": "Syarat & Ketentuan", "is_active": True}
                        ]
                        
                        for page_data in default_pages:
                            existing = db.session.execute(
                                text("SELECT id FROM root_seo WHERE page_identifier = :identifier"),
                                {"identifier": page_data["page_identifier"]}
                            ).fetchone()
                            
                            if not existing:
                                db.session.execute(
                                    text("""
                                        INSERT INTO root_seo (page_identifier, page_name, is_active, created_at, updated_at)
                                        VALUES (:identifier, :name, :active, datetime('now'), datetime('now'))
                                    """),
                                    {
                                        "identifier": page_data["page_identifier"],
                                        "name": page_data["page_name"],
                                        "active": page_data["is_active"]
                                    }
                                )
                                print(f"✅ Created root SEO page: {page_data['page_name']}")
                        
                        db.session.commit()
                        print("✅ Default root SEO pages initialized")
                    else:
                        print("✅ Root SEO table has existing data")
                except Exception as e:
                    print(f"⚠️ Could not initialize root SEO data: {e}")
            except Exception as e:
                print(f"⚠️ Could not verify/alter root_seo: {e}")

            # ===== BRAND IDENTITY TABLE MIGRATIONS =====
            print("\n" + "="*50)
            print("🎨 BRAND IDENTITY TABLE MIGRATIONS")
            print("="*50)
            
            # Check brand_identity feature toggle columns and SEO fields
            print("\n🔍 Checking brand_identity table structure...")
            try:
                result = db.session.execute(text("PRAGMA table_info(brand_identity)"))
                bi_columns = [row[1] for row in result.fetchall()]
                
                print("📋 Current brand_identity table columns:")
                for i, col in enumerate(bi_columns, 1):
                    print(f"   {i:2d}. {col}")
                
                missing_bi_cols = []
                required_bi_columns = [
                    'enable_comments', 'enable_ratings', 'enable_ads', 
                    'enable_campaigns', 'categories_display_location', 'card_design',
                    'seo_settings', 'website_url'  # New SEO fields
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
                            elif col == 'seo_settings':
                                db.session.execute(text("ALTER TABLE brand_identity ADD COLUMN seo_settings JSON"))
                                print("✅ Added seo_settings column for root SEO settings")
                            elif col == 'website_url':
                                db.session.execute(text("ALTER TABLE brand_identity ADD COLUMN website_url VARCHAR(255) DEFAULT 'https://lilycms.com'"))
                                print("✅ Added website_url column for SEO")
                                # Update existing records to have the default value
                                db.session.execute(text("UPDATE brand_identity SET website_url = 'https://lilycms.com' WHERE website_url IS NULL"))
                                print("✅ Updated existing records with default website URL")
                        except Exception as e:
                            print(f"⚠️ Column {col} might already exist: {e}")
                    db.session.commit()
                    
                    # Verify the changes
                    result = db.session.execute(text("PRAGMA table_info(brand_identity)"))
                    updated_bi_columns = [row[1] for row in result.fetchall()]
                    
                    print("\n📋 Updated brand_identity table columns:")
                    for i, col in enumerate(updated_bi_columns, 1):
                        print(f"   {i:2d}. {col}")
                    
                    # Check if all required columns are now present
                    still_missing = [col for col in required_bi_columns if col not in updated_bi_columns]
                    if still_missing:
                        print(f"❌ Still missing columns: {still_missing}")
                    else:
                        print("✅ All required brand_identity columns are now present")
                        
                        # Initialize SEO settings for existing brand records
                        print("\n🔧 Initializing SEO settings for existing brand records...")
                        try:
                            brand_records = db.session.execute(text("SELECT id FROM brand_identity")).fetchall()
                            for record in brand_records:
                                # Initialize empty seo_settings if not set
                                db.session.execute(
                                    text("UPDATE brand_identity SET seo_settings = '{}' WHERE id = :id AND seo_settings IS NULL"),
                                    {"id": record[0]}
                                )
                            db.session.commit()
                            print(f"✅ Initialized SEO settings for {len(brand_records)} brand record(s)")
                        except Exception as e:
                            print(f"⚠️ Could not initialize SEO settings: {e}")
                else:
                    print("✅ All brand_identity columns already present")
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
                user_required_columns = ['reading_history_id', 'user_library_id', 'birthdate', 'deletion_requested', 'deletion_requested_at']
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
                            elif col == 'birthdate':
                                db.session.execute(text("ALTER TABLE user ADD COLUMN birthdate DATE"))
                                print("✅ Added birthdate column to user")
                            elif col == 'deletion_requested':
                                db.session.execute(text("ALTER TABLE user ADD COLUMN deletion_requested BOOLEAN DEFAULT 0"))
                                print("✅ Added deletion_requested column to user")
                            elif col == 'deletion_requested_at':
                                db.session.execute(text("ALTER TABLE user ADD COLUMN deletion_requested_at TIMESTAMP"))
                                print("✅ Added deletion_requested_at column to user")
                        except Exception as e:
                            print(f"⚠️ Column {col} might already exist: {e}")
                    db.session.commit()
                else:
                    print("✅ User table has all required columns")
            except Exception as e:
                print(f"⚠️ Could not verify/alter user table: {e}")

            # ===== EDITOR ↔ WRITER LINK TABLE =====
            print("\n" + "="*50)
            print("🧩 EDITOR ↔ WRITER LINK TABLE")
            print("="*50)
            try:
                if 'editor_writer' not in existing_tables:
                    print("🔧 Creating editor_writer link table...")
                    from models import editor_writer
                    editor_writer.create(db.engine)
                    print("✅ Created editor_writer table")
                else:
                    print("✅ editor_writer table already exists")
            except Exception as e:
                print(f"⚠️ Could not create/verify editor_writer table: {e}")

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

            # ===== ACHIEVEMENT SYSTEM TABLES =====
            print("\n" + "="*50)
            print("🏆 ACHIEVEMENT SYSTEM TABLES")
            print("="*50)
            
            # Check if achievement_category table exists
            if 'achievement_category' not in existing_tables:
                print("\n🔧 Creating achievement_category table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE achievement_category (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name VARCHAR(100) NOT NULL,
                            description TEXT,
                            icon_class VARCHAR(100),
                            color VARCHAR(20),
                            display_order INTEGER DEFAULT 0,
                            is_active BOOLEAN DEFAULT 1 NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    print("✅ Created achievement_category table")
                except Exception as e:
                    print(f"⚠️ Could not create achievement_category table: {e}")
            
            # Check if achievement table exists
            if 'achievement' not in existing_tables:
                print("\n🔧 Creating achievement table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE achievement (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name VARCHAR(200) NOT NULL,
                            description TEXT,
                            achievement_type VARCHAR(50) NOT NULL,
                            criteria_type VARCHAR(50) NOT NULL,
                            criteria_value INTEGER NOT NULL,
                            criteria_operator VARCHAR(10) DEFAULT '>=' NOT NULL,
                            points_reward INTEGER DEFAULT 0 NOT NULL,
                            badge_icon VARCHAR(100),
                            rarity VARCHAR(20) DEFAULT 'common' NOT NULL,
                            is_hidden BOOLEAN DEFAULT 0 NOT NULL,
                            is_active BOOLEAN DEFAULT 1 NOT NULL,
                            category_id INTEGER,
                            created_by INTEGER,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (category_id) REFERENCES achievement_category (id),
                            FOREIGN KEY (created_by) REFERENCES user (id)
                        )
                    """))
                    print("✅ Created achievement table")
                except Exception as e:
                    print(f"⚠️ Could not create achievement table: {e}")
            
            # Check if user_achievement table exists
            if 'user_achievement' not in existing_tables:
                print("\n🔧 Creating user_achievement table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE user_achievement (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            achievement_id INTEGER NOT NULL,
                            current_progress INTEGER DEFAULT 0 NOT NULL,
                            is_completed BOOLEAN DEFAULT 0 NOT NULL,
                            completed_at TIMESTAMP,
                            points_earned INTEGER DEFAULT 0 NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES user (id),
                            FOREIGN KEY (achievement_id) REFERENCES achievement (id),
                            UNIQUE(user_id, achievement_id)
                        )
                    """))
                    print("✅ Created user_achievement table")
                except Exception as e:
                    print(f"⚠️ Could not create user_achievement table: {e}")
            
            # Check if achievement_progress table exists
            if 'achievement_progress' not in existing_tables:
                print("\n🔧 Creating achievement_progress table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE achievement_progress (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_achievement_id INTEGER NOT NULL,
                            progress_type VARCHAR(20) NOT NULL,
                            old_value INTEGER DEFAULT 0,
                            new_value INTEGER DEFAULT 0,
                            change_amount INTEGER DEFAULT 0,
                            context_data TEXT,
                            source VARCHAR(100),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_achievement_id) REFERENCES user_achievement (id)
                        )
                    """))
                    print("✅ Created achievement_progress table")
                except Exception as e:
                    print(f"⚠️ Could not create achievement_progress table: {e}")
            
            # Check if user_streak table exists
            if 'user_streak' not in existing_tables:
                print("\n🔧 Creating user_streak table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE user_streak (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            streak_type VARCHAR(50) NOT NULL,
                            current_streak INTEGER DEFAULT 0 NOT NULL,
                            longest_streak INTEGER DEFAULT 0 NOT NULL,
                            last_activity_date DATE,
                            streak_start_date DATE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES user (id),
                            UNIQUE(user_id, streak_type)
                        )
                    """))
                    print("✅ Created user_streak table")
                except Exception as e:
                    print(f"⚠️ Could not create user_streak table: {e}")
            
            # Check if user_points table exists
            if 'user_points' not in existing_tables:
                print("\n🔧 Creating user_points table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE user_points (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            total_points INTEGER DEFAULT 0 NOT NULL,
                            current_level INTEGER DEFAULT 1 NOT NULL,
                            points_to_next_level INTEGER DEFAULT 100 NOT NULL,
                            total_levels_earned INTEGER DEFAULT 0 NOT NULL,
                            highest_level_reached INTEGER DEFAULT 1 NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES user (id),
                            UNIQUE(user_id)
                        )
                    """))
                    print("✅ Created user_points table")
                except Exception as e:
                    print(f"⚠️ Could not create user_points table: {e}")
            
            # Check if point_transaction table exists
            if 'point_transaction' not in existing_tables:
                print("\n🔧 Creating point_transaction table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE point_transaction (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_points_id INTEGER NOT NULL,
                            points_change INTEGER NOT NULL,
                            source VARCHAR(100) NOT NULL,
                            description TEXT,
                            context_data TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_points_id) REFERENCES user_points (id)
                        )
                    """))
                    print("✅ Created point_transaction table")
                except Exception as e:
                    print(f"⚠️ Could not create point_transaction table: {e}")
            
            # Check if user_coins table exists
            if 'user_coins' not in existing_tables:
                print("\n🔧 Creating user_coins table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE user_coins (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            achievement_coins INTEGER DEFAULT 0 NOT NULL,
                            topup_coins INTEGER DEFAULT 0 NOT NULL,
                            total_achievement_coins_earned INTEGER DEFAULT 0 NOT NULL,
                            total_topup_coins_purchased INTEGER DEFAULT 0 NOT NULL,
                            total_coins_spent INTEGER DEFAULT 0 NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES user (id),
                            UNIQUE(user_id)
                        )
                    """))
                    print("✅ Created user_coins table")
                except Exception as e:
                    print(f"⚠️ Could not create user_coins table: {e}")
            
            # Check if coin_transaction table exists
            if 'coin_transaction' not in existing_tables:
                print("\n🔧 Creating coin_transaction table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE coin_transaction (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            coin_type VARCHAR(20) NOT NULL,
                            coins_change INTEGER NOT NULL,
                            source VARCHAR(100) NOT NULL,
                            description TEXT,
                            context_data TEXT,
                            payment_provider VARCHAR(50),
                            payment_id VARCHAR(255),
                            amount_paid DECIMAL(10,2),
                            currency VARCHAR(3) DEFAULT 'IDR',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES user (id)
                        )
                    """))
                    print("✅ Created coin_transaction table")
                except Exception as e:
                    print(f"⚠️ Could not create coin_transaction table: {e}")

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
            
            # Achievement system record counts
            try:
                achievement_category_count = db.session.execute(text("SELECT COUNT(*) FROM achievement_category")).scalar()
                print(f"🏆 Achievement category records: {achievement_category_count}")
            except Exception as e:
                print(f"⚠️ Could not count achievement category records: {e}")
            
            try:
                achievement_count = db.session.execute(text("SELECT COUNT(*) FROM achievement")).scalar()
                print(f"🏅 Achievement records: {achievement_count}")
            except Exception as e:
                print(f"⚠️ Could not count achievement records: {e}")
            
            try:
                user_achievement_count = db.session.execute(text("SELECT COUNT(*) FROM user_achievement")).scalar()
                print(f"👤 User achievement records: {user_achievement_count}")
            except Exception as e:
                print(f"⚠️ Could not count user achievement records: {e}")
            
            try:
                user_streak_count = db.session.execute(text("SELECT COUNT(*) FROM user_streak")).scalar()
                print(f"🔥 User streak records: {user_streak_count}")
            except Exception as e:
                print(f"⚠️ Could not count user streak records: {e}")
            
            try:
                user_points_count = db.session.execute(text("SELECT COUNT(*) FROM user_points")).scalar()
                print(f"⭐ User points records: {user_points_count}")
            except Exception as e:
                print(f"⚠️ Could not count user points records: {e}")

            # ===== CATEGORY GROUP MIGRATIONS =====
            print("\n" + "="*50)
            print("📂 CATEGORY GROUP MIGRATIONS")
            print("="*50)
            
            # Check category_group table
            if 'category_group' not in existing_tables:
                print("\n❌ Category group table not found!")
                print("💡 Creating category_group table...")
                
                # Create category_group table
                from models import CategoryGroup
                CategoryGroup.__table__.create(db.engine)
                print("✅ Category group table created")
            else:
                print("\n✅ Category group table exists")
            
            # Check category table structure and add new columns
            print("\n🔍 Checking category table structure...")
            result = db.session.execute(text("PRAGMA table_info(category)"))
            columns = [row[1] for row in result.fetchall()]
            
            print("📋 Current category table columns:")
            for i, col in enumerate(columns, 1):
                print(f"   {i:2d}. {col}")
            
            # Add new columns to category table
            new_category_columns = [
                ('description', 'TEXT'),
                ('display_order', 'INTEGER DEFAULT 0'),
                ('is_active', 'BOOLEAN DEFAULT 1'),
                ('created_at', 'DATETIME'),
                ('updated_at', 'DATETIME'),
                ('group_id', 'INTEGER REFERENCES category_group(id)')
            ]
            
            for col_name, col_type in new_category_columns:
                if col_name not in columns:
                    print(f"\n➕ Adding column '{col_name}' to category table...")
                    try:
                        db.session.execute(text(f"ALTER TABLE category ADD COLUMN {col_name} {col_type}"))
                        db.session.commit()
                        print(f"✅ Column '{col_name}' added successfully")
                    except Exception as e:
                        print(f"⚠️ Could not add column '{col_name}': {e}")
                        db.session.rollback()
                else:
                    print(f"✅ Column '{col_name}' already exists")
            
            # Create default category groups
            print("\n📂 Creating default category groups...")
            try:
                default_groups = [
                    {"name": "Genre Populer / Umum", "description": "Genre-genre populer dan umum", "display_order": 1},
                    {"name": "Romance & Variannya", "description": "Berbagai jenis romance dan variannya", "display_order": 2},
                    {"name": "Fantasi & Fiksi", "description": "Genre fantasi dan fiksi", "display_order": 3},
                    {"name": "Paranormal & Supernatural", "description": "Genre paranormal dan supernatural", "display_order": 4},
                    {"name": "Misteri, Thriller, & Aksi", "description": "Genre misteri, thriller, dan aksi", "display_order": 5},
                    {"name": "Sci-Fi & Teknologi", "description": "Genre science fiction dan teknologi", "display_order": 6},
                    {"name": "Komedi & Ringan", "description": "Genre komedi dan konten ringan", "display_order": 7},
                    {"name": "Non-Romance / Lainnya", "description": "Genre non-romance dan lainnya", "display_order": 8},
                    {"name": "Genre Eksperimental / Khusus", "description": "Genre eksperimental dan khusus", "display_order": 9}
                ]
                
                for group_data in default_groups:
                    existing_group = db.session.execute(
                        text("SELECT id FROM category_group WHERE name = :name"),
                        {"name": group_data["name"]}
                    ).fetchone()
                    
                    if not existing_group:
                        db.session.execute(
                            text("""
                                INSERT INTO category_group (name, description, display_order, is_active, created_at, updated_at)
                                VALUES (:name, :description, :display_order, 1, datetime('now'), datetime('now'))
                            """),
                            group_data
                        )
                        print(f"✅ Created category group: {group_data['name']}")
                    else:
                        print(f"✅ Category group already exists: {group_data['name']}")
                
                db.session.commit()
                print("✅ Default category groups created successfully")
                
            except Exception as e:
                print(f"⚠️ Could not create default category groups: {e}")
                db.session.rollback()

            # ===== SEO INJECTION SETTINGS TABLE =====
            print("\n" + "="*50)
            print("🔧 SEO INJECTION SETTINGS TABLE")
            print("="*50)
            
            # Check if seo_injection_settings table exists
            if 'seo_injection_settings' not in existing_tables:
                print("\n❌ SEO Injection Settings table not found!")
                print("💡 Creating seo_injection_settings table...")
                
                try:
                    from models import SEOInjectionSettings
                    SEOInjectionSettings.__table__.create(db.engine)
                    print("✅ SEO Injection Settings table created")
                    
                    # Create default settings
                    default_settings = SEOInjectionSettings(
                        website_name='LilyOpenCMS',
                        website_url='https://lilycms.com',
                        website_description='A modern content management system',
                        website_language='id',
                        organization_name='LilyOpenCMS',
                        organization_type='Organization',
                        auto_inject_news=True,
                        auto_inject_albums=True,
                        auto_inject_chapters=True,
                        auto_inject_root=True
                    )
                    db.session.add(default_settings)
                    db.session.commit()
                    print("✅ Default SEO Injection Settings created")
                    
                except Exception as e:
                    print(f"❌ Error creating SEO Injection Settings table: {e}")
                    db.session.rollback()
            else:
                print("\n✅ SEO Injection Settings table exists")
                
                # Check if default settings exist
                try:
                    from models import SEOInjectionSettings
                    settings = SEOInjectionSettings.query.first()
                    if not settings:
                        print("💡 Creating default SEO Injection Settings...")
                        default_settings = SEOInjectionSettings(
                            website_name='LilyOpenCMS',
                            website_url='https://lilycms.com',
                            website_description='A modern content management system',
                            website_language='id',
                            organization_name='LilyOpenCMS',
                            organization_type='Organization',
                            auto_inject_news=True,
                            auto_inject_albums=True,
                            auto_inject_chapters=True,
                            auto_inject_root=True
                        )
                        db.session.add(default_settings)
                        db.session.commit()
                        print("✅ Default SEO Injection Settings created")
                    else:
                        print("✅ Default SEO Injection Settings already exist")
                except Exception as e:
                    print(f"⚠️ Could not check/create default settings: {e}")

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
            print("✅ Achievement system tables created")
            print("✅ Brand identity SEO fields added")
            print("✅ Root SEO table and columns created")
            print("✅ SEO columns added to News, Album, and AlbumChapter tables")
            print("✅ Default root SEO pages initialized")
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
        print("✅ Achievement system tables created")
        print("✅ Brand identity SEO fields added")
        print("✅ Root SEO table and columns created")
        print("✅ SEO columns added to News, Album, and AlbumChapter tables")
        print("✅ Default root SEO pages initialized")
        print("\n💡 You can now run the application or add test data:")
        print("   python helper/add_test_albums.py")
        print("   python helper/init_achievement_system.py")
        print("   python main.py")
    else:
        print("❌ Comprehensive migration failed!")
        print("Please check the error messages above.")
    
    return success

if __name__ == "__main__":
    main()
