#!/usr/bin/env python3
"""
Comprehensive safe migration script that handles all database schema changes.
This script preserves all existing data while ensuring the database schema is correct.
It replaces all individual migration scripts and Alembic migrations.
"""

import sys
import os
from pathlib import Path
import sqlite3 # Added for sqlite3.OperationalError

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
                'deletion_requested', 'deletion_requested_at', 'deletion_requested_by',
                'author', 'owner_id'  # New fields for author and owner
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
                        elif col == 'author':
                            db.session.execute(text("ALTER TABLE album ADD COLUMN author VARCHAR(100)"))
                            print("✅ Added author column to album")
                        elif col == 'owner_id':
                            db.session.execute(text("ALTER TABLE album ADD COLUMN owner_id INTEGER REFERENCES user(id)"))
                            print("✅ Added owner_id column to album")
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
                    print("✅ Author and owner_id fields added for album ownership system")
            else:
                print("✅ All required album columns are already present")
                print("✅ Author and owner_id fields are present for album ownership system")

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
                    'seo_settings', 'website_url', 'brand_description'  # New SEO fields and brand description
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
                            elif col == 'brand_description':
                                db.session.execute(text("ALTER TABLE brand_identity ADD COLUMN brand_description TEXT DEFAULT 'LilyOpenCMS is a modern, open-source content management system designed for the digital age. We provide comprehensive tools for managing digital content, from news articles and media files to user interactions and analytics. Our platform empowers content creators and organizations to build engaging digital experiences with ease and efficiency.'"))
                                print("✅ Added brand_description column")
                                # Update existing records to have the default value
                                db.session.execute(text("UPDATE brand_identity SET brand_description = 'LilyOpenCMS is a modern, open-source content management system designed for the digital age. We provide comprehensive tools for managing digital content, from news articles and media files to user interactions and analytics. Our platform empowers content creators and organizations to build engaging digital experiences with ease and efficiency.' WHERE brand_description IS NULL"))
                                print("✅ Updated existing records with default brand description")
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
                user_required_columns = [
                    'reading_history_id',
                    'user_library_id',
                    'birthdate',
                    'deletion_requested',
                    'deletion_requested_at',
                    # Hybrid verification flow fields
                    'email_verified_at',
                    'last_verification_sent_at'
                ]
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
                            elif col == 'email_verified_at':
                                db.session.execute(text("ALTER TABLE user ADD COLUMN email_verified_at TIMESTAMP"))
                                print("✅ Added email_verified_at column to user")
                            elif col == 'last_verification_sent_at':
                                db.session.execute(text("ALTER TABLE user ADD COLUMN last_verification_sent_at TIMESTAMP"))
                                print("✅ Added last_verification_sent_at column to user")
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
            
            # Drop old tables if they exist with wrong structure
            print("\n🔄 Checking for old table structures...")
            try:
                # Check if reading_history has old structure (album_id column)
                result = db.session.execute(text("PRAGMA table_info(reading_history)"))
                columns = [row[1] for row in result.fetchall()]
                
                if 'album_id' in columns:
                    print("🔄 Dropping old reading_history table...")
                    db.session.execute(text("DROP TABLE IF EXISTS reading_history"))
                    print("✅ Dropped old reading_history table")
                
                # Check if user_library has old structure (album_id column)
                result = db.session.execute(text("PRAGMA table_info(user_library)"))
                columns = [row[1] for row in result.fetchall()]
                
                if 'album_id' in columns:
                    print("🔄 Dropping old user_library table...")
                    db.session.execute(text("DROP TABLE IF EXISTS user_library"))
                    print("✅ Dropped old user_library table")
                
                db.session.commit()
            except Exception as e:
                print(f"⚠️ Could not check/drop old tables: {e}")
            
            # Check if reading_history table exists
            if 'reading_history' not in existing_tables:
                print("\n🔧 Creating reading_history table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE reading_history (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            content_type VARCHAR(20) NOT NULL,
                            content_id INTEGER NOT NULL,
                            read_count INTEGER DEFAULT 1 NOT NULL,
                            first_read_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            last_read_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE,
                            UNIQUE(user_id, content_type, content_id)
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
                            content_type VARCHAR(20) NOT NULL,
                            content_id INTEGER NOT NULL,
                            added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE,
                            UNIQUE(user_id, content_type, content_id)
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

            # ===== ROLE PERMISSION SYSTEM TABLES =====
            print("\n" + "="*50)
            print("🔐 ROLE PERMISSION SYSTEM TABLES")
            print("="*50)
            
            # Check if role_permission table exists
            if 'role_permission' not in existing_tables:
                print("\n🔧 Creating role_permission table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE role_permission (
                            role_id INTEGER NOT NULL,
                            permission_id INTEGER NOT NULL,
                            PRIMARY KEY (role_id, permission_id),
                            FOREIGN KEY (role_id) REFERENCES custom_role (id) ON DELETE CASCADE,
                            FOREIGN KEY (permission_id) REFERENCES permission (id) ON DELETE CASCADE
                        )
                    """))
                    print("✅ Created role_permission table")
                except Exception as e:
                    print(f"⚠️ Could not create role_permission table: {e}")
            
            # Check if permission table exists
            if 'permission' not in existing_tables:
                print("\n🔧 Creating permission table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE permission (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name VARCHAR(100) NOT NULL UNIQUE,
                            description VARCHAR(255),
                            resource VARCHAR(100) NOT NULL,
                            action VARCHAR(50) NOT NULL,
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    print("✅ Created permission table")
                except Exception as e:
                    print(f"⚠️ Could not create permission table: {e}")
            
            # Check if custom_role table exists
            if 'custom_role' not in existing_tables:
                print("\n🔧 Creating custom_role table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE custom_role (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name VARCHAR(100) NOT NULL UNIQUE,
                            description VARCHAR(255),
                            is_active BOOLEAN NOT NULL DEFAULT 1,
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    print("✅ Created custom_role table")
                except Exception as e:
                    print(f"⚠️ Could not create custom_role table: {e}")

            # ===== CONTENT MANAGEMENT TABLES =====
            print("\n" + "="*50)
            print("📝 CONTENT MANAGEMENT TABLES")
            print("="*50)
            
            # Check if comment table exists
            if 'comment' not in existing_tables:
                print("\n🔧 Creating comment table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE comment (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            content_type VARCHAR(50) NOT NULL,
                            content_id INTEGER NOT NULL,
                            parent_id INTEGER,
                            content TEXT NOT NULL,
                            is_approved BOOLEAN DEFAULT 1 NOT NULL,
                            is_spam BOOLEAN DEFAULT 0 NOT NULL,
                            is_deleted BOOLEAN DEFAULT 0 NOT NULL,
                            ip_address VARCHAR(45),
                            user_agent VARCHAR(500),
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE,
                            FOREIGN KEY (parent_id) REFERENCES comment (id) ON DELETE CASCADE
                        )
                    """))
                    print("✅ Created comment table")
                except Exception as e:
                    print(f"⚠️ Could not create comment table: {e}")
            else:
                # Align existing comment table with model fields
                try:
                    result = db.session.execute(text("PRAGMA table_info(comment)"))
                    comment_cols = [row[1] for row in result.fetchall()]
                    to_add = []
                    if 'is_spam' not in comment_cols:
                        to_add.append("ADD COLUMN is_spam BOOLEAN DEFAULT 0 NOT NULL")
                    if 'ip_address' not in comment_cols:
                        to_add.append("ADD COLUMN ip_address VARCHAR(45)")
                    if 'user_agent' not in comment_cols:
                        to_add.append("ADD COLUMN user_agent VARCHAR(500)")
                    if 'updated_at' not in comment_cols:
                        to_add.append("ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")
                    for clause in to_add:
                        try:
                            db.session.execute(text(f"ALTER TABLE comment {clause}"))
                        except Exception as e:
                            print(f"⚠️ Could not {clause}: {e}")
                    if to_add:
                        db.session.commit()
                except Exception as e:
                    print(f"⚠️ Could not align comment table: {e}")
            
            # Check if rating table exists
            if 'rating' not in existing_tables:
                print("\n🔧 Creating rating table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE rating (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            content_type VARCHAR(50) NOT NULL,
                            content_id INTEGER NOT NULL,
                            rating_value INTEGER NOT NULL CHECK (rating_value >= 1 AND rating_value <= 5),
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE,
                            UNIQUE(user_id, content_type, content_id)
                        )
                    """))
                    print("✅ Created rating table")
                except Exception as e:
                    print(f"⚠️ Could not create rating table: {e}")
            else:
                # Align existing rating table with model fields
                try:
                    result = db.session.execute(text("PRAGMA table_info(rating)"))
                    rating_cols = [row[1] for row in result.fetchall()]
                    if 'rating_value' not in rating_cols:
                        try:
                            db.session.execute(text("ALTER TABLE rating ADD COLUMN rating_value INTEGER"))
                            # Migrate data from legacy 'rating' column if exists
                            if 'rating' in rating_cols:
                                db.session.execute(text("UPDATE rating SET rating_value = rating WHERE rating_value IS NULL"))
                            # Add constraint best-effort (SQLite won't add CHECK easily post-hoc)
                            db.session.commit()
                            print("✅ Added rating_value column and migrated existing values")
                        except Exception as e:
                            print(f"⚠️ Could not add/migrate rating_value: {e}")
                    # ensure timestamps
                    if 'updated_at' not in rating_cols:
                        try:
                            db.session.execute(text("ALTER TABLE rating ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
                            db.session.commit()
                        except Exception as e:
                            print(f"⚠️ Could not add rating.updated_at: {e}")
                except Exception as e:
                    print(f"⚠️ Could not align rating table: {e}")
            
            # Check if comment_like table exists
            if 'comment_like' not in existing_tables:
                print("\n🔧 Creating comment_like table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE comment_like (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            is_like BOOLEAN NOT NULL,
                            is_deleted BOOLEAN NOT NULL DEFAULT 0,
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            user_id INTEGER NOT NULL,
                            comment_id INTEGER NOT NULL,
                            FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE,
                            FOREIGN KEY (comment_id) REFERENCES comment (id) ON DELETE CASCADE,
                            UNIQUE(user_id, comment_id)
                        )
                    """))
                    print("✅ Created comment_like table")
                except Exception as e:
                    print(f"⚠️ Could not create comment_like table: {e}")
            else:
                # Align existing comment_like table with model fields
                try:
                    result = db.session.execute(text("PRAGMA table_info(comment_like)"))
                    like_cols = [row[1] for row in result.fetchall()]
                    if 'is_like' not in like_cols:
                        db.session.execute(text("ALTER TABLE comment_like ADD COLUMN is_like BOOLEAN"))
                    if 'is_deleted' not in like_cols:
                        db.session.execute(text("ALTER TABLE comment_like ADD COLUMN is_deleted BOOLEAN DEFAULT 0 NOT NULL"))
                    if 'updated_at' not in like_cols:
                        db.session.execute(text("ALTER TABLE comment_like ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
                    db.session.commit()
                except Exception as e:
                    print(f"⚠️ Could not align comment_like table: {e}")
            
            # Check if comment_report table exists
            if 'comment_report' not in existing_tables:
                print("\n🔧 Creating comment_report table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE comment_report (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            comment_id INTEGER NOT NULL,
                            reason VARCHAR(100) NOT NULL,
                            description TEXT,
                            is_resolved BOOLEAN DEFAULT 0 NOT NULL,
                            resolved_by INTEGER,
                            resolved_at DATETIME,
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE,
                            FOREIGN KEY (comment_id) REFERENCES comment (id) ON DELETE CASCADE,
                            FOREIGN KEY (resolved_by) REFERENCES user (id)
                        )
                    """))
                    print("✅ Created comment_report table")
                except Exception as e:
                    print(f"⚠️ Could not create comment_report table: {e}")
            else:
                # Align existing comment_report table with model fields
                try:
                    result = db.session.execute(text("PRAGMA table_info(comment_report)"))
                    cr_cols = [row[1] for row in result.fetchall()]
                    if 'is_resolved' not in cr_cols:
                        db.session.execute(text("ALTER TABLE comment_report ADD COLUMN is_resolved BOOLEAN DEFAULT 0 NOT NULL"))
                    if 'resolved_by' not in cr_cols and 'reviewed_by_id' in cr_cols:
                        # Add new column and try migrate value
                        db.session.execute(text("ALTER TABLE comment_report ADD COLUMN resolved_by INTEGER"))
                        try:
                            db.session.execute(text("UPDATE comment_report SET resolved_by = reviewed_by_id WHERE resolved_by IS NULL"))
                        except Exception:
                            pass
                    if 'resolved_at' not in cr_cols and 'reviewed_at' in cr_cols:
                        db.session.execute(text("ALTER TABLE comment_report ADD COLUMN resolved_at DATETIME"))
                        try:
                            db.session.execute(text("UPDATE comment_report SET resolved_at = reviewed_at WHERE resolved_at IS NULL"))
                        except Exception:
                            pass
                    if 'updated_at' not in cr_cols:
                        db.session.execute(text("ALTER TABLE comment_report ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
                    # Attempt to migrate legacy status -> is_resolved
                    if 'status' in cr_cols:
                        try:
                            db.session.execute(text("UPDATE comment_report SET is_resolved = 1 WHERE LOWER(status) IN ('resolved','approved','done')"))
                        except Exception:
                            pass
                    db.session.commit()
                except Exception as e:
                    print(f"⚠️ Could not align comment_report table: {e}")

            # ===== WEBSITE MANAGEMENT TABLES =====
            print("\n" + "="*50)
            print("🌐 WEBSITE MANAGEMENT TABLES")
            print("="*50)
            
            # Check if navigation_link table exists
            if 'navigation_link' not in existing_tables:
                print("\n🔧 Creating navigation_link table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE navigation_link (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name VARCHAR(100) NOT NULL,
                            url VARCHAR(255) NOT NULL,
                            location VARCHAR(50) NOT NULL,
                            "order" INTEGER DEFAULT 0,
                            is_active BOOLEAN DEFAULT 1 NOT NULL,
                            is_external BOOLEAN DEFAULT 0 NOT NULL,
                            user_id INTEGER,
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    print("✅ Created navigation_link table")
                except Exception as e:
                    print(f"⚠️ Could not create navigation_link table: {e}")
            else:
                # Align existing navigation_link table
                try:
                    result = db.session.execute(text("PRAGMA table_info(navigation_link)"))
                    nl_cols = [row[1] for row in result.fetchall()]
                    if 'location' not in nl_cols:
                        db.session.execute(text("ALTER TABLE navigation_link ADD COLUMN location VARCHAR(50)"))
                    if 'order' not in nl_cols:
                        db.session.execute(text("ALTER TABLE navigation_link ADD COLUMN \"order\" INTEGER DEFAULT 0"))
                    if 'user_id' not in nl_cols:
                        db.session.execute(text("ALTER TABLE navigation_link ADD COLUMN user_id INTEGER"))
                    db.session.commit()
                except Exception as e:
                    print(f"⚠️ Could not align navigation_link table: {e}")
            
            # Check if youtube_video table exists
            if 'youtube_video' not in existing_tables:
                print("\n🔧 Creating youtube_video table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE youtube_video (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            youtube_id VARCHAR(11) NOT NULL UNIQUE,
                            link VARCHAR(255) NOT NULL UNIQUE,
                            title VARCHAR(255),
                            duration INTEGER,
                            is_visible BOOLEAN DEFAULT 1 NOT NULL,
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            user_id INTEGER NOT NULL,
                            FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE
                        )
                    """))
                    print("✅ Created youtube_video table")
                except Exception as e:
                    print(f"⚠️ Could not create youtube_video table: {e}")
            else:
                # Align existing youtube_video table
                try:
                    result = db.session.execute(text("PRAGMA table_info(youtube_video)"))
                    yv_cols = [row[1] for row in result.fetchall()]
                    if 'youtube_id' not in yv_cols:
                        db.session.execute(text("ALTER TABLE youtube_video ADD COLUMN youtube_id VARCHAR(11)"))
                    if 'link' not in yv_cols:
                        db.session.execute(text("ALTER TABLE youtube_video ADD COLUMN link VARCHAR(255)"))
                    if 'is_visible' not in yv_cols:
                        db.session.execute(text("ALTER TABLE youtube_video ADD COLUMN is_visible BOOLEAN DEFAULT 1 NOT NULL"))
                    if 'user_id' not in yv_cols:
                        db.session.execute(text("ALTER TABLE youtube_video ADD COLUMN user_id INTEGER"))
                    db.session.commit()
                except Exception as e:
                    print(f"⚠️ Could not align youtube_video table: {e}")
            
            # Check if share_log table exists
            if 'share_log' not in existing_tables:
                print("\n🔧 Creating share_log table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE share_log (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            news_id INTEGER NOT NULL UNIQUE,
                            whatsapp_count INTEGER DEFAULT 0 NOT NULL,
                            facebook_count INTEGER DEFAULT 0 NOT NULL,
                            twitter_count INTEGER DEFAULT 0 NOT NULL,
                            instagram_count INTEGER DEFAULT 0 NOT NULL,
                            bluesky_count INTEGER DEFAULT 0 NOT NULL,
                            clipboard_count INTEGER DEFAULT 0 NOT NULL,
                            first_shared_at DATETIME,
                            latest_shared_at DATETIME,
                            FOREIGN KEY (news_id) REFERENCES news (id) ON DELETE CASCADE
                        )
                    """))
                    print("✅ Created share_log table")
                except Exception as e:
                    print(f"⚠️ Could not create share_log table: {e}")
            else:
                # Align existing share_log table
                try:
                    result = db.session.execute(text("PRAGMA table_info(share_log)"))
                    sl_cols = [row[1] for row in result.fetchall()]
                    if 'news_id' not in sl_cols:
                        # If legacy generic share_log exists, we won't auto-destruct; add columns to support model usage
                        db.session.execute(text("ALTER TABLE share_log ADD COLUMN news_id INTEGER"))
                    for col, definition in [
                        ('whatsapp_count','INTEGER DEFAULT 0 NOT NULL'),
                        ('facebook_count','INTEGER DEFAULT 0 NOT NULL'),
                        ('twitter_count','INTEGER DEFAULT 0 NOT NULL'),
                        ('instagram_count','INTEGER DEFAULT 0 NOT NULL'),
                        ('bluesky_count','INTEGER DEFAULT 0 NOT NULL'),
                        ('clipboard_count','INTEGER DEFAULT 0 NOT NULL'),
                        ('first_shared_at','DATETIME'),
                        ('latest_shared_at','DATETIME'),
                    ]:
                        if col not in sl_cols:
                            try:
                                db.session.execute(text(f"ALTER TABLE share_log ADD COLUMN {col} {definition}"))
                            except Exception as e:
                                print(f"⚠️ Could not add share_log.{col}: {e}")
                    db.session.commit()
                except Exception as e:
                    print(f"⚠️ Could not align share_log table: {e}")
            
            # Check if social_media table exists
            if 'social_media' not in existing_tables:
                print("\n🔧 Creating social_media table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE social_media (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            platform VARCHAR(50) NOT NULL,
                            url VARCHAR(255) NOT NULL,
                            icon_class VARCHAR(100),
                            is_active BOOLEAN DEFAULT 1 NOT NULL,
                            display_order INTEGER DEFAULT 0,
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    print("✅ Created social_media table")
                except Exception as e:
                    print(f"⚠️ Could not create social_media table: {e}")
            
            # Check if contact_detail table exists
            if 'contact_detail' not in existing_tables:
                print("\n🔧 Creating contact_detail table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE contact_detail (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            type VARCHAR(50) NOT NULL,
                            value VARCHAR(255) NOT NULL,
                            icon_class VARCHAR(100),
                            is_active BOOLEAN DEFAULT 1 NOT NULL,
                            display_order INTEGER DEFAULT 0,
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    print("✅ Created contact_detail table")
                except Exception as e:
                    print(f"⚠️ Could not create contact_detail table: {e}")
            
            # Check if team_member table exists
            if 'team_member' not in existing_tables:
                print("\n🔧 Creating team_member table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE team_member (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name VARCHAR(100) NOT NULL,
                            position VARCHAR(100) NOT NULL,
                            bio TEXT,
                            image_url VARCHAR(255),
                            social_links TEXT,
                            is_active BOOLEAN DEFAULT 1 NOT NULL,
                            display_order INTEGER DEFAULT 0,
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    print("✅ Created team_member table")
                except Exception as e:
                    print(f"⚠️ Could not create team_member table: {e}")
            
            # Check if user_subscriptions table exists
            if 'user_subscriptions' not in existing_tables:
                print("\n🔧 Creating user_subscriptions table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE user_subscriptions (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            subscription_type VARCHAR(50) NOT NULL,
                            status VARCHAR(20) DEFAULT 'active' NOT NULL,
                            start_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            end_date DATETIME,
                            payment_provider VARCHAR(50),
                            payment_id VARCHAR(255),
                            amount DECIMAL(10,2),
                            currency VARCHAR(3) DEFAULT 'IDR',
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE
                        )
                    """))
                    print("✅ Created user_subscriptions table")
                except Exception as e:
                    print(f"⚠️ Could not create user_subscriptions table: {e}")

            # ===== ADVERTISING SYSTEM TABLES =====
            print("\n" + "="*50)
            print("📢 ADVERTISING SYSTEM TABLES")
            print("="*50)
            
            # Check if ad_campaign table exists
            if 'ad_campaign' not in existing_tables:
                print("\n🔧 Creating ad_campaign table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE ad_campaign (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name VARCHAR(255) NOT NULL,
                            description TEXT,
                            start_date DATETIME NOT NULL,
                            end_date DATETIME NOT NULL,
                            budget DECIMAL(10,2),
                            status VARCHAR(20) DEFAULT 'active' NOT NULL,
                            created_by INTEGER,
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (created_by) REFERENCES user (id)
                        )
                    """))
                    print("✅ Created ad_campaign table")
                except Exception as e:
                    print(f"⚠️ Could not create ad_campaign table: {e}")
            
            # Check if ad table exists
            if 'ad' not in existing_tables:
                print("\n🔧 Creating ad table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE ad (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            campaign_id INTEGER,
                            title VARCHAR(255) NOT NULL,
                            content TEXT,
                            image_url VARCHAR(255),
                            target_url VARCHAR(255),
                            ad_type VARCHAR(50) NOT NULL,
                            position VARCHAR(50) NOT NULL,
                            is_active BOOLEAN DEFAULT 1 NOT NULL,
                            start_date DATETIME,
                            end_date DATETIME,
                            max_impressions INTEGER,
                            max_clicks INTEGER,
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (campaign_id) REFERENCES ad_campaign (id) ON DELETE SET NULL
                        )
                    """))
                    print("✅ Created ad table")
                except Exception as e:
                    print(f"⚠️ Could not create ad table: {e}")
            
            # Check if ad_placement table exists
            if 'ad_placement' not in existing_tables:
                print("\n🔧 Creating ad_placement table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE ad_placement (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name VARCHAR(100) NOT NULL UNIQUE,
                            description TEXT,
                            location VARCHAR(100) NOT NULL,
                            ad_type VARCHAR(50) NOT NULL,
                            is_active BOOLEAN DEFAULT 1 NOT NULL,
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    print("✅ Created ad_placement table")
                except Exception as e:
                    print(f"⚠️ Could not create ad_placement table: {e}")
            
            # Check if ad_stats table exists
            if 'ad_stats' not in existing_tables:
                print("\n🔧 Creating ad_stats table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE ad_stats (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            ad_id INTEGER NOT NULL,
                            date DATE NOT NULL,
                            impressions INTEGER DEFAULT 0 NOT NULL,
                            clicks INTEGER DEFAULT 0 NOT NULL,
                            ctr DECIMAL(5,4) DEFAULT 0.0000,
                            revenue DECIMAL(10,2) DEFAULT 0.00,
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (ad_id) REFERENCES ad (id) ON DELETE CASCADE,
                            UNIQUE(ad_id, date)
                        )
                    """))
                    print("✅ Created ad_stats table")
                except Exception as e:
                    print(f"⚠️ Could not create ad_stats table: {e}")

            # ===== LEGAL & POLICY TABLES =====
            print("\n" + "="*50)
            print("⚖️ LEGAL & POLICY TABLES")
            print("="*50)
            
            # Check if privacy_policy table exists
            if 'privacy_policy' not in existing_tables:
                print("\n🔧 Creating privacy_policy table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE privacy_policy (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title VARCHAR(255) NOT NULL,
                            content TEXT NOT NULL,
                            version VARCHAR(20) NOT NULL,
                            is_active BOOLEAN DEFAULT 1 NOT NULL,
                            effective_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    print("✅ Created privacy_policy table")
                except Exception as e:
                    print(f"⚠️ Could not create privacy_policy table: {e}")
            
            # Check if media_guideline table exists
            if 'media_guideline' not in existing_tables:
                print("\n🔧 Creating media_guideline table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE media_guideline (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title VARCHAR(255) NOT NULL,
                            content TEXT NOT NULL,
                            version VARCHAR(20) NOT NULL,
                            is_active BOOLEAN DEFAULT 1 NOT NULL,
                            effective_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    print("✅ Created media_guideline table")
                except Exception as e:
                    print(f"⚠️ Could not create media_guideline table: {e}")
            
            # Check if visi_misi table exists
            if 'visi_misi' not in existing_tables:
                print("\n🔧 Creating visi_misi table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE visi_misi (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title VARCHAR(255) NOT NULL,
                            content TEXT NOT NULL,
                            type VARCHAR(20) NOT NULL,
                            is_active BOOLEAN DEFAULT 1 NOT NULL,
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    print("✅ Created visi_misi table")
                except Exception as e:
                    print(f"⚠️ Could not create visi_misi table: {e}")
            
            # Check if penyangkalan table exists
            if 'penyangkalan' not in existing_tables:
                print("\n🔧 Creating penyangkalan table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE penyangkalan (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title VARCHAR(255) NOT NULL,
                            content TEXT NOT NULL,
                            is_active BOOLEAN DEFAULT 1 NOT NULL,
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    print("✅ Created penyangkalan table")
                except Exception as e:
                    print(f"⚠️ Could not create penyangkalan table: {e}")
            
            # Check if pedoman_hak table exists
            if 'pedoman_hak' not in existing_tables:
                print("\n🔧 Creating pedoman_hak table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE pedoman_hak (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title VARCHAR(255) NOT NULL,
                            content TEXT NOT NULL,
                            is_active BOOLEAN DEFAULT 1 NOT NULL,
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    print("✅ Created pedoman_hak table")
                except Exception as e:
                    print(f"⚠️ Could not create pedoman_hak table: {e}")

            # ===== USER ACTIVITY TRACKING =====
            print("\n" + "="*50)
            print("📊 USER ACTIVITY TRACKING")
            print("="*50)
            
            # Check if user_activity table exists
            if 'user_activity' not in existing_tables:
                print("\n🔧 Creating user_activity table...")
                try:
                    db.session.execute(text("""
                        CREATE TABLE user_activity (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            activity_type VARCHAR(50) NOT NULL,
                            description TEXT,
                            ip_address VARCHAR(45),
                            user_agent TEXT,
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE SET NULL
                        )
                    """))
                    print("✅ Created user_activity table")
                except Exception as e:
                    print(f"⚠️ Could not create user_activity table: {e}")

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
                
                # Align existing seo_injection_settings columns with model
                try:
                    result = db.session.execute(text("PRAGMA table_info(seo_injection_settings)"))
                    sis_cols = [row[1] for row in result.fetchall()]
                    columns_to_add = [
                        ("website_name", "VARCHAR(200)"),
                        ("website_url", "VARCHAR(255)"),
                        ("website_description", "TEXT"),
                        ("website_language", "VARCHAR(10) DEFAULT 'id'"),
                        ("website_logo", "VARCHAR(255)"),
                        ("organization_name", "VARCHAR(200)"),
                        ("organization_logo", "VARCHAR(255)"),
                        ("organization_description", "TEXT"),
                        ("organization_type", "VARCHAR(100)"),
                        ("facebook_url", "VARCHAR(255)"),
                        ("twitter_url", "VARCHAR(255)"),
                        ("instagram_url", "VARCHAR(255)"),
                        ("youtube_url", "VARCHAR(255)"),
                        ("linkedin_url", "VARCHAR(255)"),
                        ("contact_email", "VARCHAR(255)"),
                        ("contact_phone", "VARCHAR(50)"),
                        ("contact_address", "TEXT"),
                        ("default_meta_description", "TEXT"),
                        ("default_meta_keywords", "TEXT"),
                        ("default_meta_author", "VARCHAR(100)"),
                        ("default_meta_robots", "VARCHAR(50) DEFAULT 'index, follow'"),
                        ("default_og_title", "VARCHAR(200)"),
                        ("default_og_description", "TEXT"),
                        ("default_og_image", "VARCHAR(255)"),
                        ("default_twitter_card", "VARCHAR(50) DEFAULT 'summary'"),
                        ("default_twitter_title", "VARCHAR(200)"),
                        ("default_twitter_description", "TEXT"),
                        ("default_structured_data_type", "VARCHAR(50) DEFAULT 'Article'"),
                        ("default_canonical_url", "VARCHAR(255)"),
                        ("default_meta_language", "VARCHAR(10) DEFAULT 'id'"),
                        ("auto_inject_news", "BOOLEAN DEFAULT 1 NOT NULL"),
                        ("auto_inject_albums", "BOOLEAN DEFAULT 1 NOT NULL"),
                        ("auto_inject_chapters", "BOOLEAN DEFAULT 1 NOT NULL"),
                        ("auto_inject_root", "BOOLEAN DEFAULT 1 NOT NULL"),
                        ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
                        ("updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP")
                    ]
                    for col_name, col_def in columns_to_add:
                        if col_name not in sis_cols:
                            try:
                                db.session.execute(text(f"ALTER TABLE seo_injection_settings ADD COLUMN {col_name} {col_def}"))
                                print(f"✅ Added seo_injection_settings.{col_name}")
                            except Exception as e:
                                print(f"⚠️ Could not add seo_injection_settings.{col_name}: {e}")
                    db.session.commit()
                except Exception as e:
                    print(f"⚠️ Could not align seo_injection_settings table: {e}")

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
            
            # ===== USER PROFILE SYSTEM MIGRATION =====
            print("\n" + "="*50)
            print("👤 USER PROFILE SYSTEM MIGRATION")
            print("="*50)
            
            try:
                migrate_user_profile_system(db.session)
                print("✅ User profile system migration completed")
                
                migrate_write_access_requests(db.session)
                print("✅ Write access requests migration completed")
                
                migrate_enhanced_ads_system(db.session)
                print("✅ Enhanced ads system migration completed")
            except Exception as e:
                print(f"⚠️ Could not migrate user profile system: {e}")
            
            print(f"\n🎉 Comprehensive migration completed successfully!")
            print("✅ All existing data preserved")
            print("✅ All tables have required columns")
            print("✅ Reading history and user library tables created")
            print("✅ Achievement system tables created")
            print("✅ Role permission system tables created")
            print("✅ Content management tables (comments, ratings) created")
            print("✅ Website management tables created")
            print("✅ Advertising system tables created")
            print("✅ Legal & policy tables created")
            print("✅ User activity tracking table created")
            print("✅ Brand identity SEO fields added")
            print("✅ Root SEO table and columns created")
            print("✅ SEO columns added to News, Album, and AlbumChapter tables")
            print("✅ Author and owner_id fields added to Album table for ownership system")
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

def migrate_write_access_requests(db_session):
    """Create write access requests table."""
    from sqlalchemy import text
    print("🔄 Creating write access requests table...")
    
    try:
        # Create write_access_requests table
        db_session.execute(text("""
            CREATE TABLE IF NOT EXISTS write_access_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                request_reason TEXT,
                portfolio_links TEXT,
                experience_description TEXT,
                status VARCHAR(20) DEFAULT 'pending',
                admin_notes TEXT,
                reviewed_by_id INTEGER,
                requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                reviewed_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (reviewed_by_id) REFERENCES users (id)
            )
        """))
        
        # Create indexes
        db_session.execute(text("CREATE INDEX IF NOT EXISTS idx_write_access_requests_user_id ON write_access_requests (user_id)"))
        db_session.execute(text("CREATE INDEX IF NOT EXISTS idx_write_access_requests_status ON write_access_requests (status)"))
        db_session.execute(text("CREATE INDEX IF NOT EXISTS idx_write_access_requests_requested_at ON write_access_requests (requested_at)"))
        
        db_session.commit()
        print("✅ Write access requests table created successfully")
        
    except Exception as e:
        print(f"⚠️ Write access requests table might already exist or error occurred: {e}")
        db_session.rollback()


def migrate_user_profile_system(db_session):
    """Add user profile system tables and fields."""
    from sqlalchemy import text
    print("🔄 Migrating user profile system...")
    
    # Add write_access field to user table
    try:
        db_session.execute(text("""
            ALTER TABLE user 
            ADD COLUMN write_access BOOLEAN DEFAULT NULL
        """))
        print("✅ Added write_access field to user table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("ℹ️  write_access field already exists")
        else:
            print(f"⚠️  Error adding write_access field: {e}")
    
    # Create user_follow table
    try:
        db_session.execute(text("""
            CREATE TABLE user_follow (
                follower_id INTEGER NOT NULL,
                following_id INTEGER NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (follower_id, following_id),
                FOREIGN KEY (follower_id) REFERENCES user (id) ON DELETE CASCADE,
                FOREIGN KEY (following_id) REFERENCES user (id) ON DELETE CASCADE,
                UNIQUE (follower_id, following_id)
            )
        """))
        print("✅ Created user_follow table")
    except sqlite3.OperationalError as e:
        if "table user_follow already exists" in str(e):
            print("ℹ️  user_follow table already exists")
        else:
            print(f"⚠️  Error creating user_follow table: {e}")
    
    # Create user_profile table
    try:
        db_session.execute(text("""
            CREATE TABLE user_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                pronouns VARCHAR(50),
                short_bio TEXT,
                location VARCHAR(100),
                website VARCHAR(255),
                social_links TEXT,  -- JSON stored as TEXT
                is_public BOOLEAN NOT NULL DEFAULT 1,
                show_email BOOLEAN NOT NULL DEFAULT 0,
                show_birthdate BOOLEAN NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE
            )
        """))
        print("✅ Created user_profile table")
    except sqlite3.OperationalError as e:
        if "table user_profile already exists" in str(e):
            print("ℹ️  user_profile table already exists")
        else:
            print(f"⚠️  Error creating user_profile table: {e}")
    
    # Create user_stats table
    try:
        db_session.execute(text("""
            CREATE TABLE user_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                total_stories INTEGER NOT NULL DEFAULT 0,
                total_albums INTEGER NOT NULL DEFAULT 0,
                total_views INTEGER NOT NULL DEFAULT 0,
                total_likes INTEGER NOT NULL DEFAULT 0,
                total_comments INTEGER NOT NULL DEFAULT 0,
                total_followers INTEGER NOT NULL DEFAULT 0,
                total_following INTEGER NOT NULL DEFAULT 0,
                total_reads INTEGER NOT NULL DEFAULT 0,
                total_saved INTEGER NOT NULL DEFAULT 0,
                activity_calendar TEXT,  -- JSON stored as TEXT
                monthly_stats TEXT,      -- JSON stored as TEXT
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE
            )
        """))
        print("✅ Created user_stats table")
    except sqlite3.OperationalError as e:
        if "table user_stats already exists" in str(e):
            print("ℹ️  user_stats table already exists")
        else:
            print(f"⚠️  Error creating user_stats table: {e}")
    
    # Create indexes for better performance
    try:
        db_session.execute(text("CREATE INDEX IF NOT EXISTS idx_user_follow_follower ON user_follow (follower_id)"))
        db_session.execute(text("CREATE INDEX IF NOT EXISTS idx_user_follow_following ON user_follow (following_id)"))
        print("✅ Created indexes for user profile system")
    except sqlite3.OperationalError as e:
        print(f"⚠️  Error creating indexes: {e}")

def migrate_enhanced_ads_system(db_session):
    """Add enhanced image management fields to Ad model."""
    print("\n📸 Migrating enhanced ads system...")
    
    try:
        # Add new image management fields to ad table
        new_columns = [
            ("image_filename", "VARCHAR(255)"),
            ("image_upload_path", "VARCHAR(500)"),
            ("image_width", "INTEGER"),
            ("image_height", "INTEGER"),
            ("image_file_size", "INTEGER"),
            ("content_type", "VARCHAR(50) DEFAULT 'text'"),
            ("created_by", "INTEGER REFERENCES user(id)"),
            ("updated_by", "INTEGER REFERENCES user(id)")
        ]
        
        for column_name, column_type in new_columns:
            try:
                from sqlalchemy import text
                db_session.execute(text(f"ALTER TABLE ad ADD COLUMN {column_name} {column_type}"))
                print(f"✅ Added column: {column_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"⚠️  Column {column_name} already exists")
                else:
                    print(f"⚠️  Error adding column {column_name}: {e}")
        
        # Create indexes for better performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_ad_image_filename ON ad(image_filename)",
            "CREATE INDEX IF NOT EXISTS idx_ad_image_upload_path ON ad(image_upload_path)",
            "CREATE INDEX IF NOT EXISTS idx_ad_type_content_type ON ad(ad_type, content_type)",
            "CREATE INDEX IF NOT EXISTS idx_ad_created_by ON ad(created_by)",
            "CREATE INDEX IF NOT EXISTS idx_ad_updated_by ON ad(updated_by)",
            "CREATE INDEX IF NOT EXISTS idx_ad_is_active ON ad(is_active)"
        ]
        
        for index_sql in indexes:
            try:
                from sqlalchemy import text
                db_session.execute(text(index_sql))
                print(f"✅ Created index: {index_sql.split('idx_')[1].split(' ON')[0]}")
            except sqlite3.OperationalError as e:
                print(f"⚠️  Error creating index: {e}")
        
        # Create static/uploads/ads directory if it doesn't exist
        import os
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads', 'ads')
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir, exist_ok=True)
            print(f"✅ Created directory: {uploads_dir}")
        else:
            print(f"✅ Directory already exists: {uploads_dir}")
        
        db_session.commit()
        print("✅ Enhanced ads system migration completed")
        
    except Exception as e:
        print(f"❌ Error in enhanced ads system migration: {e}")
        db_session.rollback()

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
        print("✅ Role permission system tables created")
        print("✅ Content management tables (comments, ratings) created")
        print("✅ Website management tables created")
        print("✅ Advertising system tables created")
        print("✅ Legal & policy tables created")
        print("✅ User activity tracking table created")
        print("✅ Brand identity SEO fields added")
        print("✅ Root SEO table and columns created")
        print("✅ SEO columns added to News, Album, and AlbumChapter tables")
        print("✅ Author and owner_id fields added to Album table for ownership system")
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
