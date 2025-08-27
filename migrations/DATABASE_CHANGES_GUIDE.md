# Database Changes Guide

## How to Add New Database Fields

When you need to add new columns or tables to the database, follow this simple process:

### 1. Update Your Model

First, add the new field to your model in `models.py`:

```python
class Album(db.Model):
    # ... existing fields ...
    new_field = db.Column(db.String(100), default='default_value')
```

### 2. Update safe_migrate.py

Add the migration logic to `safe_migrate.py`. Find the appropriate section and add:

```python
# In the appropriate table section (e.g., ALBUM TABLE MIGRATIONS)
required_album_columns = [
    'total_views', 'average_rating', 'age_rating', 
    'view_count', 'rating_count', 'is_premium',
    'reading_history_id', 'user_library_id',
    'new_field'  # Add your new field here
]

# In the migration logic section:
elif col == 'new_field':
    db.session.execute(text("ALTER TABLE album ADD COLUMN new_field VARCHAR(100) DEFAULT 'default_value'"))
    print("✅ Added new_field column")
```

### 3. Add Indexes (if needed)

If the new field will be frequently queried, add an index in `models.py`:

```python
# In the add_missing_indexes() function
db.session.execute(text("""
    CREATE INDEX IF NOT EXISTS idx_album_new_field 
    ON album (new_field)
"""))
```

### 4. Run the Migration

```bash
python migrations/safe_migrate.py
```

## How to Add New Tables

### 1. Create the Model

Add your new model to `models.py`:

```python
class NewTable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### 2. Update safe_migrate.py

Add table creation logic to `safe_migrate.py`:

```python
# In the CREATE TABLES section:
if 'new_table' not in existing_tables:
    print("\n🔧 Creating new_table...")
    try:
        db.session.execute(text("""
            CREATE TABLE new_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("✅ Created new_table")
    except Exception as e:
        print(f"⚠️ Could not create new_table: {e}")
```

### 3. Add to get_all_models()

Update the `get_all_models()` function in `models.py`:

```python
def get_all_models():
    return [
        # ... existing models ...
        NewTable,  # Add your new model here
    ]
```

### 4. Run the Migration

```bash
python migrations/safe_migrate.py
```

## Database Management Tools

### Database Manager Script

Use the comprehensive database manager for various operations:

```bash
# Run safe migration
python migrations/database_manager.py migrate

# Optimize database performance
python migrations/database_manager.py optimize

# Check database health
python migrations/database_manager.py health

# Clean up orphaned data
python migrations/database_manager.py cleanup

# Show database statistics
python migrations/database_manager.py stats

# Create/update indexes
python migrations/database_manager.py indexes

# Create database backup
python migrations/database_manager.py backup

# Restore from backup
python migrations/database_manager.py restore <backup_file>

# Run full maintenance
python migrations/database_manager.py full
```

### Direct Model Functions

You can also use functions directly from `models.py`:

```python
from models import (
    add_missing_indexes,
    check_database_health,
    optimize_database,
    cleanup_orphaned_data,
    get_database_stats,
    create_all_tables
)

# Add indexes for optimal performance
add_missing_indexes()

# Check database health
check_database_health()

# Optimize database
optimize_database()

# Clean up orphaned data
cleanup_orphaned_data()

# Get statistics
stats = get_database_stats()
```

## Database Optimizations

### Automatic Indexes

The system automatically creates optimized indexes for:

- **News**: category, author, date, visibility, premium status
- **Albums**: author, category, visibility, premium status, chapters
- **Users**: role, active status, premium subscriptions
- **Comments**: content type, approval status, user activity
- **Ratings**: content type, creation date
- **Reading History**: user, content, last read date
- **User Library**: user, content type
- **Ads**: active status, priority, campaign
- **All Policy/Guideline tables**: order, active status

### Performance Monitoring

The system includes comprehensive performance monitoring:

- **Health Checks**: Orphaned data detection, duplicate prevention
- **Statistics**: Table sizes, record counts, database size
- **Optimization**: ANALYZE, VACUUM, REINDEX operations
- **Cleanup**: Automatic removal of orphaned records

## Best Practices

1. **Always backup your database** before running migrations
2. **Test migrations** on a copy of your data first
3. **Use appropriate data types** and constraints
4. **Add meaningful default values** for new columns
5. **Add indexes** for frequently queried fields
6. **Update the documentation** when adding new features
7. **Run health checks** regularly
8. **Monitor performance** using the statistics functions

## Common Patterns

### Adding a Boolean Column
```python
elif col == 'is_featured':
    db.session.execute(text("ALTER TABLE album ADD COLUMN is_featured BOOLEAN DEFAULT 0"))
    print("✅ Added is_featured column")
```

### Adding a Foreign Key
```python
elif col == 'category_id':
    db.session.execute(text("ALTER TABLE album ADD COLUMN category_id INTEGER"))
    print("✅ Added category_id column")
```

### Adding a Timestamp
```python
elif col == 'updated_at':
    db.session.execute(text("ALTER TABLE album ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
    print("✅ Added updated_at column")
```

### Adding an Indexed Field
```python
# In the model
new_field = db.Column(db.String(100), nullable=False, index=True)

# In add_missing_indexes()
db.session.execute(text("""
    CREATE INDEX IF NOT EXISTS idx_table_new_field 
    ON table_name (new_field)
"""))
```

## Troubleshooting

### Column Already Exists
The migration script handles this automatically - it will show a warning but continue.

### Table Not Found
Make sure the table name in your migration matches the actual table name in the database.

### Permission Errors
Ensure the database file has proper write permissions.

### Performance Issues
Run the optimization commands:
```bash
python migrations/database_manager.py optimize
python migrations/database_manager.py indexes
```

### Data Integrity Issues
Run health checks and cleanup:
```bash
python migrations/database_manager.py health
python migrations/database_manager.py cleanup
```

## Migration Checklist

Before committing database changes:

- [ ] Updated the model in `models.py`
- [ ] Added migration logic to `safe_migrate.py`
- [ ] Added indexes for performance (if needed)
- [ ] Updated `get_all_models()` function
- [ ] Tested the migration on development data
- [ ] Updated this guide if needed
- [ ] Committed all changes

## Why This Approach?

This safe migration approach is:
- **Simple**: One file to maintain
- **Safe**: Never drops data
- **Reliable**: Works consistently
- **Clear**: All changes visible in one place
- **Reversible**: Can be run multiple times safely
- **Optimized**: Automatic index creation and performance monitoring
- **Monitored**: Health checks and statistics
- **Maintained**: Comprehensive management tools
