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

### 3. Run the Migration

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

### 3. Run the Migration

```bash
python migrations/safe_migrate.py
```

## Best Practices

1. **Always backup your database** before running migrations
2. **Test on development first** before production
3. **Use appropriate data types** and constraints
4. **Add meaningful default values** for new columns
5. **Update the documentation** when adding new features

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

## Troubleshooting

### Column Already Exists
The migration script handles this automatically - it will show a warning but continue.

### Table Not Found
Make sure the table name in your migration matches the actual table name in the database.

### Permission Errors
Ensure the database file has proper write permissions.

## Migration Checklist

Before committing database changes:

- [ ] Updated the model in `models.py`
- [ ] Added migration logic to `safe_migrate.py`
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
