#!/usr/bin/env python3
"""
Add sample contact details for the about page.
"""

import sys
import os
# Add the parent directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)  # Insert at beginning to prioritize local imports

# Import app and db from the local main module
import importlib.util
spec = importlib.util.spec_from_file_location("main", os.path.join(project_root, "main.py"))
main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main)
app = main.app
db = main.db

from models import ContactDetail
from datetime import datetime, timezone

def add_contact_details():
    """Add sample contact details."""
    print("📞 Adding Contact Details")
    print("=" * 50)
    
    # Clear existing contact details
    ContactDetail.query.delete()
    
    contact_details = [
        {
            "title": "Email",
            "content": "info@lilycms.com",
            "section_order": 1,
            "icon_class": "envelope",
            "link": "mailto:info@lilycms.com",
        },
        {
            "title": "Telepon",
            "content": "+62 21 1234 5678",
            "section_order": 2,
            "icon_class": "phone",
            "link": "tel:+622112345678",
        },
        {
            "title": "Alamat",
            "content": "Jl. Sudirman No. 123, Jakarta Pusat, DKI Jakarta 12345",
            "section_order": 3,
            "icon_class": "map-marker-alt",
            "link": None,
        },
        {
            "title": "Website",
            "content": "www.lilycms.com",
            "section_order": 4,
            "icon_class": "globe",
            "link": "https://lilycms.com",
        },
        {
            "title": "Facebook",
            "content": "facebook.com/lilycms",
            "section_order": 5,
            "icon_class": "facebook",
            "link": "https://facebook.com/lilycms",
        },
        {
            "title": "Instagram",
            "content": "@lilycms",
            "section_order": 6,
            "icon_class": "instagram",
            "link": "https://instagram.com/lilycms",
        },
        {
            "title": "GitHub",
            "content": "github.com/lilycms",
            "section_order": 7,
            "icon_class": "github",
            "link": "https://github.com/lilycms",
        },
    ]
    
    for detail in contact_details:
        record = ContactDetail(
            title=detail["title"],
            content=detail["content"],
            section_order=detail["section_order"],
            icon_class=detail["icon_class"],
            link=detail["link"],
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.session.add(record)
        print(f"✅ Added: {detail['title']}")
    
    try:
        db.session.commit()
        print("-" * 50)
        print("✅ Successfully added contact details!")
    except Exception as e:
        print(f"❌ Error adding contact details: {str(e)}")
        db.session.rollback()

if __name__ == "__main__":
    with app.app_context():
        add_contact_details() 