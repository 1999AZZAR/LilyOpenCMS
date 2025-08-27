"""
Migration to add age_rating columns to news and album tables.
Supports SQLite; safe to run multiple times.
"""

import sqlite3
from pathlib import Path

def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())

def migrate(db_path: str = None):
    # Default DB path for this project
    if db_path is None:
        db_path = str(Path('instance') / 'database.db')

    db_file = Path(db_path)
    if not db_file.exists():
        print(f"Database not found at {db_path}. Skipping age_rating migration.")
        return

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()

        # news.age_rating
        if not column_exists(cur, 'news', 'age_rating'):
            cur.execute("ALTER TABLE news ADD COLUMN age_rating VARCHAR(10)")
            print("✅ Added column news.age_rating")
        else:
            print("ℹ️  Column news.age_rating already exists")

        # album.age_rating
        if not column_exists(cur, 'album', 'age_rating'):
            cur.execute("ALTER TABLE album ADD COLUMN age_rating VARCHAR(10)")
            print("✅ Added column album.age_rating")
        else:
            print("ℹ️  Column album.age_rating already exists")

        conn.commit()
    except Exception as e:
        print(f"❌ Error migrating age_rating columns: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
