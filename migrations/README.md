# Database Migrations

This directory contains migration scripts to update the database schema.

## Database Setup and Migration

### ✅ Automatic Database Initialization (RECOMMENDED)

The Flask application now automatically initializes the database on first startup. **No manual migration needed!**

When you start the Flask app, it will:
- ✅ Create the database file if it doesn't exist
- ✅ Create all necessary tables with correct schema
- ✅ Add missing columns to existing tables
- ✅ Ensure the album table has `total_views` and `average_rating` columns

### Manual Migration Options (Only if needed)

If you need manual control, you can use these scripts:

#### Option 1: Fresh Database Setup (DESTROYS EXISTING DATA)
If you want to start with a fresh database or don't have important data:
```bash
python migrations/init_database.py
```

#### Option 2: Safe Migration (PRESERVES EXISTING DATA)
If you have existing data that you want to keep:
```bash
python migrations/safe_migrate.py
```

### Steps

#### ✅ Automatic Setup (RECOMMENDED):
1. **Start the Flask application:**
   ```bash
   python main.py
   ```
   The database will be automatically initialized on first startup.

2. **Test the database setup:**
   ```bash
   python test_db_init.py
   ```

3. **Run the album generation:**
   ```bash
   python helper/add_test_albums.py
   ```

#### Manual Setup (Only if needed):

##### For Fresh Database Setup:
1. **Run the initialization script:**
   ```bash
   python migrations/init_database.py
   ```

##### For Safe Migration (Preserving Data):
1. **Find the database file:**
   ```bash
   python migrations/find_db.py
   ```

2. **Check database path using Flask:**
   ```bash
   python migrations/check_db_path.py
   ```

3. **Run the safe migration:**
   ```bash
   python migrations/safe_migrate.py
   ```

4. **Verify the migration:**
   ```bash
   python migrations/check_album_table.py
   ```

### What the scripts do

#### `init_database.py`:
- Creates a fresh database with all necessary tables
- **WARNING**: This will destroy all existing data
- Ensures all tables have the correct schema
- Adds missing columns to the album table

#### `safe_migrate.py`:
- Preserves all existing data
- Adds missing columns to existing tables
- Creates missing tables if they don't exist
- Shows record counts for verification

Both scripts will:
- Add `total_views` column (INTEGER, DEFAULT 0, NOT NULL)
- Add `average_rating` column (FLOAT, DEFAULT 0.0, NOT NULL)
- Verify the database structure is correct

### Database Path

The new scripts automatically detect the database path using Flask configuration. If you need to manually specify the path, update the `db_path` variable in the scripts.

The scripts will search for database files in common locations and use Flask's configuration to find the correct database path.

### After Setup/Migration

Once the setup or migration is complete, you can run the album generation script:
```bash
python helper/add_test_albums.py
```

### Verification

To verify that everything is working correctly:
```bash
python migrations/check_album_table.py
```

## Troubleshooting

### Database not found
If you get a "Database not found" error, check the `db_path` variable in the migration scripts and update it to point to your actual database file.

### Permission denied
Make sure you have read/write permissions to the database file:
```bash
ls -la /home/lilycmsc/domains/lilycms.com/public_html/beranda/instance/database.db
```

### SQLite errors
If you encounter SQLite errors, make sure:
1. The database file is not locked by another process
2. You have sufficient disk space
3. The database file is not corrupted

## Backup

It's recommended to backup your database before running migrations:
```bash
cp /home/lilycmsc/domains/lilycms.com/public_html/beranda/instance/database.db /home/lilycmsc/domains/lilycms.com/public_html/beranda/instance/database.db.backup
```
