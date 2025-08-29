#!/usr/bin/env python3
"""
Helper script to batch import DOCX files as News articles.

Usage:
    python helper/import_docx_news.py /path/to/docx/files/ [category_id] [--preview]

Features:
    - Batch import multiple DOCX files
    - Auto-detect title from filename or document content
    - Set category, date, and other metadata
    - Preview mode to see what would be imported
    - Error handling and logging
"""

import os
import sys
import argparse
from datetime import date, datetime
from pathlib import Path
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from models import db, News, Category, User
from routes.routes_news import extract_title_from_content, infer_age_rating_from_content

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('docx_import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def import_docx_files(directory_path, category_id=None, preview=False, author_id=None):
    """
    Import all DOCX files from a directory as News articles.
    
    Args:
        directory_path (str): Path to directory containing DOCX files
        category_id (int): Category ID to assign to all articles
        preview (bool): If True, only show what would be imported
        author_id (int): User ID to set as author (defaults to first admin)
    """
    directory = Path(directory_path)
    
    if not directory.exists():
        logger.error(f"Directory not found: {directory_path}")
        return
    
    # Find all DOCX files
    docx_files = list(directory.glob("*.docx"))
    if not docx_files:
        logger.warning(f"No DOCX files found in {directory_path}")
        return
    
    logger.info(f"Found {len(docx_files)} DOCX files to process")
    
    # Get category
    category = None
    if category_id:
        category = Category.query.get(category_id)
        if not category:
            logger.error(f"Category with ID {category_id} not found")
            return
        logger.info(f"Using category: {category.name}")
    
    # Get author
    if not author_id:
        # Find first admin user
        author = User.query.filter(
            User.role.in_(['ADMIN', 'SUPERUSER', 'OWNER'])
        ).first()
        if not author:
            logger.error("No admin user found to set as author")
            return
        author_id = author.id
        logger.info(f"Using author: {author.username}")
    
    # Process each file
    success_count = 0
    error_count = 0
    
    for docx_file in docx_files:
        try:
            logger.info(f"Processing: {docx_file.name}")
            
            # Read DOCX content
            try:
                import mammoth
                with open(docx_file, "rb") as f:
                    result = mammoth.convert_to_html(f)
                    content = result.value
                    messages = result.messages
                    
                    if messages:
                        logger.warning(f"Warnings for {docx_file.name}: {messages}")
            except Exception as e:
                logger.error(f"Failed to read DOCX file {docx_file.name}: {e}")
                error_count += 1
                continue
            
            # Extract title
            title = extract_title_from_content(content)
            if not title:
                # Use filename without extension
                title = docx_file.stem
            
            # Infer age rating
            age_rating = infer_age_rating_from_content(content)
            
            # Create news data
            news_data = {
                'title': title,
                'content': content,
                'category_id': category.id if category else None,
                'date': date.today(),
                'author_id': author_id,
                'age_rating': age_rating,
                'is_news': True,
                'is_visible': True,
                'is_premium': False,
                'is_main_news': False
            }
            
            if preview:
                logger.info(f"PREVIEW - Would create: {title}")
                logger.info(f"  Category: {category.name if category else 'None'}")
                logger.info(f"  Age Rating: {age_rating}")
                logger.info(f"  Content length: {len(content)} characters")
                logger.info(f"  Author: {author.username if author else 'Unknown'}")
                logger.info("-" * 50)
            else:
                # Create the news article
                news = News(**news_data)
                db.session.add(news)
                db.session.commit()
                
                logger.info(f"✅ Created: {title} (ID: {news.id})")
                success_count += 1
                
        except Exception as e:
            logger.error(f"Error processing {docx_file.name}: {e}")
            error_count += 1
            db.session.rollback()
    
    # Summary
    if preview:
        logger.info(f"PREVIEW SUMMARY: Would import {len(docx_files)} files")
    else:
        logger.info(f"IMPORT SUMMARY: Successfully imported {success_count} files, {error_count} errors")

def main():
    parser = argparse.ArgumentParser(description="Batch import DOCX files as News articles")
    parser.add_argument("directory", help="Directory containing DOCX files")
    parser.add_argument("category_id", nargs="?", type=int, help="Category ID to assign to all articles")
    parser.add_argument("--preview", action="store_true", help="Preview mode - don't actually import")
    parser.add_argument("--author", type=int, help="User ID to set as author")
    
    args = parser.parse_args()
    
    with app.app_context():
        import_docx_files(
            args.directory,
            category_id=args.category_id,
            preview=args.preview,
            author_id=args.author
        )

if __name__ == "__main__":
    main()
