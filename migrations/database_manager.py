#!/usr/bin/env python3
"""
Comprehensive Database Management Script for LilyOpenCMS
Provides various database operations for maintenance, optimization, and monitoring.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """Main function to run database management operations."""
    print("🔧 LilyOpenCMS Database Manager")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("Usage: python migrations/database_manager.py <command>")
        print("\nAvailable commands:")
        print("  migrate     - Run safe migration")
        print("  optimize    - Optimize database performance")
        print("  health      - Check database health")
        print("  cleanup     - Clean up orphaned data")
        print("  stats       - Show database statistics")
        print("  indexes     - Create/update database indexes")
        print("  backup      - Create database backup")
        print("  restore     - Restore database from backup")
        print("  reset       - Reset database (DANGEROUS!)")
        print("  full        - Run full database maintenance")
        return
    
    command = sys.argv[1].lower()
    
    try:
        # Import Flask app and models
        from main import app
        from models import db, add_missing_indexes, check_database_health, optimize_database, cleanup_orphaned_data, get_database_stats
        
        with app.app_context():
            if command == "migrate":
                run_migration()
            elif command == "optimize":
                run_optimization()
            elif command == "health":
                run_health_check()
            elif command == "cleanup":
                run_cleanup()
            elif command == "stats":
                run_stats()
            elif command == "indexes":
                run_indexes()
            elif command == "backup":
                run_backup()
            elif command == "restore":
                run_restore()
            elif command == "reset":
                run_reset()
            elif command == "full":
                run_full_maintenance()
            else:
                print(f"❌ Unknown command: {command}")
                print("Use 'python migrations/database_manager.py' to see available commands")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def run_migration():
    """Run safe database migration."""
    print("🛡️ Running safe database migration...")
    try:
        from migrations.safe_migrate import safe_migrate
        success = safe_migrate()
        if success:
            print("✅ Migration completed successfully!")
        else:
            print("❌ Migration failed!")
    except Exception as e:
        print(f"❌ Migration error: {e}")


def run_optimization():
    """Run database optimization."""
    print("🔧 Running database optimization...")
    try:
        from models import optimize_database
        optimize_database()
        print("✅ Optimization completed!")
    except Exception as e:
        print(f"❌ Optimization error: {e}")


def run_health_check():
    """Run database health check."""
    print("🔍 Running database health check...")
    try:
        from models import check_database_health
        check_database_health()
        print("✅ Health check completed!")
    except Exception as e:
        print(f"❌ Health check error: {e}")


def run_cleanup():
    """Run orphaned data cleanup."""
    print("🧹 Running orphaned data cleanup...")
    try:
        from models import cleanup_orphaned_data
        cleanup_orphaned_data()
        print("✅ Cleanup completed!")
    except Exception as e:
        print(f"❌ Cleanup error: {e}")


def run_stats():
    """Show database statistics."""
    print("📊 Getting database statistics...")
    try:
        from models import get_database_stats
        stats = get_database_stats()
        
        print("\n📊 Database Statistics:")
        print("=" * 40)
        
        for key, value in stats.items():
            if key.endswith('_count'):
                table_name = key.replace('_count', '').replace('_', ' ').title()
                print(f"{table_name}: {value:,}")
            elif key == 'database_size_bytes':
                size_mb = value / (1024 * 1024)
                print(f"Database Size: {size_mb:.2f} MB")
        
        print("✅ Statistics retrieved!")
    except Exception as e:
        print(f"❌ Statistics error: {e}")


def run_indexes():
    """Create/update database indexes."""
    print("🔧 Creating/updating database indexes...")
    try:
        from models import add_missing_indexes
        add_missing_indexes()
        print("✅ Indexes created/updated!")
    except Exception as e:
        print(f"❌ Indexes error: {e}")


def run_backup():
    """Create database backup."""
    print("💾 Creating database backup...")
    try:
        from main import app
        import shutil
        from datetime import datetime
        
        # Get database path
        database_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if database_uri.startswith('sqlite:///'):
            db_path = database_uri.replace('sqlite:///', '')
        elif database_uri.startswith('sqlite://'):
            db_path = database_uri.replace('sqlite://', '')
        else:
            db_path = database_uri
        
        # Create backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{db_path}.backup_{timestamp}"
        
        # Copy database file
        shutil.copy2(db_path, backup_path)
        
        # Get file size
        file_size = os.path.getsize(backup_path)
        size_mb = file_size / (1024 * 1024)
        
        print(f"✅ Backup created: {backup_path}")
        print(f"📊 Backup size: {size_mb:.2f} MB")
        
    except Exception as e:
        print(f"❌ Backup error: {e}")


def run_restore():
    """Restore database from backup."""
    print("🔄 Restoring database from backup...")
    
    if len(sys.argv) < 3:
        print("❌ Please specify backup file path:")
        print("   python migrations/database_manager.py restore <backup_file>")
        return
    
    backup_file = sys.argv[2]
    
    if not os.path.exists(backup_file):
        print(f"❌ Backup file not found: {backup_file}")
        return
    
    try:
        from main import app
        import shutil
        
        # Get database path
        database_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if database_uri.startswith('sqlite:///'):
            db_path = database_uri.replace('sqlite:///', '')
        elif database_uri.startswith('sqlite://'):
            db_path = database_uri.replace('sqlite://', '')
        else:
            db_path = database_uri
        
        # Create current backup before restore
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_backup = f"{db_path}.before_restore_{timestamp}"
        shutil.copy2(db_path, current_backup)
        
        # Restore from backup
        shutil.copy2(backup_file, db_path)
        
        print(f"✅ Database restored from: {backup_file}")
        print(f"📋 Current database backed up to: {current_backup}")
        
    except Exception as e:
        print(f"❌ Restore error: {e}")


def run_reset():
    """Reset database (DANGEROUS!)."""
    print("⚠️ WARNING: This will delete all data!")
    print("⚠️ This action cannot be undone!")
    
    confirm = input("Type 'YES' to confirm database reset: ")
    if confirm != "YES":
        print("❌ Database reset cancelled.")
        return
    
    try:
        from models import drop_all_tables, create_all_tables
        
        print("🗑️ Dropping all tables...")
        drop_all_tables()
        
        print("🔧 Creating all tables...")
        create_all_tables()
        
        print("✅ Database reset completed!")
        print("💡 You may need to run data seeding scripts.")
        
    except Exception as e:
        print(f"❌ Reset error: {e}")


def run_full_maintenance():
    """Run full database maintenance."""
    print("🔧 Running full database maintenance...")
    print("=" * 60)
    
    # Run all maintenance tasks
    run_migration()
    print()
    
    run_cleanup()
    print()
    
    run_indexes()
    print()
    
    run_optimization()
    print()
    
    run_health_check()
    print()
    
    run_stats()
    print()
    
    print("🎉 Full database maintenance completed!")


if __name__ == "__main__":
    main()
