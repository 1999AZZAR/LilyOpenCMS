#!/usr/bin/env python3
"""
Script to check and fix album chapter count discrepancies.
This script identifies albums where total_chapters doesn't match visible chapters count.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from models import db, Album, AlbumChapter

def check_album_chapter_counts():
    """Check all albums for chapter count discrepancies."""
    with app.app_context():
        albums = Album.query.all()
        discrepancies = []
        
        print("Checking album chapter counts...")
        print("=" * 60)
        
        for album in albums:
            # Count visible chapters
            visible_chapters = AlbumChapter.query.filter_by(
                album_id=album.id, 
                is_visible=True
            ).count()
            
            # Count all chapters
            total_chapters = AlbumChapter.query.filter_by(album_id=album.id).count()
            
            # Check for discrepancies
            if album.total_chapters != visible_chapters:
                discrepancies.append({
                    'album_id': album.id,
                    'album_title': album.title,
                    'stored_count': album.total_chapters,
                    'visible_count': visible_chapters,
                    'total_count': total_chapters
                })
                
                print(f"❌ Album ID {album.id}: '{album.title}'")
                print(f"   Stored count: {album.total_chapters}")
                print(f"   Visible count: {visible_chapters}")
                print(f"   Total count: {total_chapters}")
                print()
        
        if not discrepancies:
            print("✅ All albums have correct chapter counts!")
        else:
            print(f"Found {len(discrepancies)} albums with discrepancies.")
            
        return discrepancies

def fix_album_chapter_counts():
    """Fix album chapter count discrepancies."""
    with app.app_context():
        albums = Album.query.all()
        fixed_count = 0
        
        print("Fixing album chapter counts...")
        print("=" * 60)
        
        for album in albums:
            # Update chapter count
            album.update_chapter_count()
            fixed_count += 1
            
        db.session.commit()
        print(f"✅ Updated chapter counts for {fixed_count} albums.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Check and fix album chapter counts")
    parser.add_argument("--fix", action="store_true", help="Fix discrepancies")
    parser.add_argument("--check-only", action="store_true", help="Only check, don't fix")
    
    args = parser.parse_args()
    
    if args.check_only:
        check_album_chapter_counts()
    elif args.fix:
        discrepancies = check_album_chapter_counts()
        if discrepancies:
            print("\nFixing discrepancies...")
            fix_album_chapter_counts()
            print("\nRe-checking after fix...")
            check_album_chapter_counts()
    else:
        print("Usage:")
        print("  python check_album_chapter_counts.py --check-only  # Only check")
        print("  python check_album_chapter_counts.py --fix        # Check and fix")
