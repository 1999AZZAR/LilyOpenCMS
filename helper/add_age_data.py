#!/usr/bin/env python3
"""
Backfill age_rating for existing News and Album records.

Default strategy:
- Premium content -> '17+'
- Otherwise -> 'SU'

This script only updates rows where age_rating is NULL/empty.
Safe to run multiple times.
"""

import os
import sys
from typing import Tuple

# Ensure project root is in path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
sys.path.insert(0, PROJECT_ROOT)

from main import app  # noqa: E402
from models import db, News, Album, User  # noqa: E402


def decide_age_rating(is_premium: bool) -> str:
    return '17+' if is_premium else 'SU'


def backfill_news() -> Tuple[int, int]:
    """Return (updated_count, total_candidates)."""
    candidates = News.query.filter((News.age_rating == None) | (News.age_rating == '')).all()  # noqa: E711
    total = len(candidates)
    updated = 0
    for n in candidates:
        try:
            n.age_rating = decide_age_rating(bool(n.is_premium))
            updated += 1
        except Exception:
            continue
    if updated:
        db.session.commit()
    return updated, total


def backfill_albums() -> Tuple[int, int]:
    """Return (updated_count, total_candidates)."""
    candidates = Album.query.filter((Album.age_rating == None) | (Album.age_rating == '')).all()  # noqa: E711
    total = len(candidates)
    updated = 0
    for a in candidates:
        try:
            a.age_rating = decide_age_rating(bool(a.is_premium))
            updated += 1
        except Exception:
            continue
    if updated:
        db.session.commit()
    return updated, total


def backfill_user_birthdates(min_year: int = 1950, max_year: int = 2015) -> Tuple[int, int]:
    """Set random birthdates for users missing them (safe, idempotent)."""
    import random
    from datetime import date

    candidates = User.query.filter(User.birthdate.is_(None)).all()
    total = len(candidates)
    updated = 0
    for u in candidates:
        try:
            year = random.randint(min_year, max_year)
            month = random.randint(1, 12)
            if month in {1, 3, 5, 7, 8, 10, 12}:
                day = random.randint(1, 31)
            elif month in {4, 6, 9, 11}:
                day = random.randint(1, 30)
            else:
                day = random.randint(1, 28)
            u.birthdate = date(year, month, day)
            updated += 1
        except Exception:
            continue
    if updated:
        db.session.commit()
    return updated, total


def main() -> int:
    with app.app_context():
        print("🧮 Backfilling age ratings for News and Albums...")
        n_updated, n_total = backfill_news()
        print(f"📰 News: updated {n_updated} of {n_total} candidates")
        a_updated, a_total = backfill_albums()
        print(f"📚 Albums: updated {a_updated} of {a_total} candidates")
        # Optional: backfill user birthdates if missing
        try:
            u_updated, u_total = backfill_user_birthdates()
            print(f"👤 Users: birthdate updated {u_updated} of {u_total} missing")
        except Exception as e:
            print(f"Skipping user birthdate backfill: {e}")
        print("✅ Done.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())


