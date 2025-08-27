# Database Migrations

This directory contains database migration scripts for LilyOpenCMS.

## Migration Strategy

We use a **safe migration approach** that preserves all existing data while ensuring the database schema is correct. This is much safer and more reliable than using Alembic migrations.

## Files

### Core Migration Scripts

- **`safe_migrate.py`** - **Main migration script** that handles all database schema changes
- **`init_database.py`** - Initializes a new database with all tables
- **`check_db_path.py`** - Utility to check database path and configuration
- **`find_db.py`** - Utility to locate the database file

### Removed Files

The following files have been removed to simplify the migration process:
- `alembic.ini` - Alembic configuration (no longer needed)
- `env.py` - Alembic environment (no longer needed)
- `script.py.mako` - Alembic template (no longer needed)
- `versions/` - Alembic migration files (no longer needed)
- Individual migration scripts (consolidated into `safe_migrate.py`)

## Usage

### First Time Setup

1. **Initialize the database:**
   ```bash
   python migrations/init_database.py
   ```

2. **Run safe migration to ensure all columns exist:**
   ```bash
   python migrations/safe_migrate.py
   ```

### Development Workflow

When you make changes to the database models in `models.py`:

1. **Update `safe_migrate.py`** to include the new columns/tables
2. **Run the safe migration:**
   ```bash
   python migrations/safe_migrate.py
   ```

This approach ensures:
- ✅ No data loss
- ✅ Safe column additions
- ✅ Automatic table creation
- ✅ Clear migration history in one file

## Why Safe Migration?

### Advantages over Alembic:

1. **No Data Loss** - Only adds missing columns, never drops data
2. **Simple** - One file to maintain instead of multiple migration files
3. **Reliable** - Works consistently across different environments
4. **Clear** - All migration logic is visible in one place
5. **Safe** - Can be run multiple times without issues

### How it Works:

1. Checks existing tables and columns
2. Adds missing columns with appropriate defaults
3. Creates missing tables if needed
4. Preserves all existing data
5. Provides detailed feedback on what was changed

## Database Schema

The migration script handles these tables:

- **album** - Main content table with views, ratings, age ratings
- **news** - News articles with age ratings
- **user** - User accounts with reading history and library
- **brand_identity** - UI configuration and feature toggles
- **reading_history** - User reading progress tracking
- **user_library** - User's saved albums and favorites
- **category** - Content categories
- **comment** - User comments
- **rating** - User ratings
- **ads** - Advertisement management
- **subscription** - Premium subscription system

## Troubleshooting

### Common Issues:

1. **Database not found:**
   ```bash
   python migrations/init_database.py
   ```

2. **Permission errors:**
   - Ensure write permissions to the database directory

3. **Column already exists:**
   - Safe migration handles this automatically

### Getting Help:

- Check the console output for detailed information
- The script provides clear error messages
- All operations are logged with emojis for easy reading

## Best Practices

1. **Always backup your database** before running migrations
2. **Test migrations** on a copy of your data first
3. **Update `safe_migrate.py`** when adding new model fields
4. **Run migrations** before deploying to production
5. **Check the output** to ensure all changes were applied

## Migration History

All migration logic is now consolidated in `safe_migrate.py`. This includes:

- Album table enhancements (views, ratings, age ratings)
- News table age rating support
- Brand identity feature toggles
- User reading history and library
- Premium content system
- Advertisement system
- Subscription management

This approach makes it easy to understand what changes have been made and ensures consistency across all environments.
