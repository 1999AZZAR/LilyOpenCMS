import sys
import os
import argparse
import random
from faker import Faker
# Add the parent directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)  # Insert at beginning to prioritize local imports

from models import db, Category, CategoryGroup  # Import CategoryGroup as well

# Import app from the local main module
import importlib.util
spec = importlib.util.spec_from_file_location("main", os.path.join(project_root, "main.py"))
main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main)
app = main.app

# Initialize Faker
fake = Faker()

# Define the comprehensive category groups and their categories
category_groups_data = {
    "Genre Populer / Umum": [
        "Romance (Romansa)",
        "Drama", 
        "Young Adult (Remaja)",
        "Coming of Age (Perjalanan Dewasa)",
        "Slice of Life (Potongan Kehidupan)"
    ],
    "Romance & Variannya": [
        "Billionaire Romance (Romansa Miliarder)",
        "Office Romance (Romansa Kantor)",
        "CEO Romance",
        "Enemies to Lovers (Musuh Jadi Kekasih)",
        "Marriage Contract (Pernikahan Kontrak)",
        "Second Chance Romance (Cinta Kesempatan Kedua)",
        "Forbidden Love (Cinta Terlarang)",
        "Historical Romance (Romansa Historis)",
        "Royal Romance (Romansa Kerajaan)",
        "Sweet Romance (Romansa Manis)",
        "Erotica"
    ],
    "Fantasi & Fiksi": [
        "Fantasy (Fantasi)",
        "Fan Fiction",
        "Urban Fantasy",
        "Dark Fantasy",
        "High Fantasy (Fantasi Epik)",
        "Historical Fantasy",
        "Time Travel (Perjalanan Waktu)",
        "Parallel Universe (Semesta Paralel)"
    ],
    "Paranormal & Supernatural": [
        "Werewolf / Shifter",
        "Vampire",
        "Witch / Wizard (Penyihir)",
        "Demon / Angel",
        "Hybrid Fantasy (Campuran Dunia Supernatural)",
        "Ghost & Spirit (Hantu / Arwah)"
    ],
    "Misteri, Thriller, & Aksi": [
        "Mystery (Misteri)",
        "Detective / Crime (Detektif / Kriminal)",
        "Psychological Thriller",
        "Action & Adventure",
        "Suspense",
        "Horror",
        "Legal Thriller (Thriller Hukum)",
        "Political Thriller"
    ],
    "Sci-Fi & Teknologi": [
        "Science Fiction (Fiksi Ilmiah)",
        "Dystopian",
        "Post-Apocalyptic (Pasca-Apokaliptik)",
        "Cyberpunk",
        "Space Opera"
    ],
    "Komedi & Ringan": [
        "Comedy Romance",
        "Satire / Parody",
        "Chick Lit",
        "Rom-Com (Romantic Comedy)"
    ],
    "Non-Romance / Lainnya": [
        "Family Drama",
        "Friendship",
        "Self-Help Fiction",
        "Motivational Fiction",
        "Historical Fiction (Fiksi Historis)"
    ],
    "Genre Eksperimental / Khusus": [
        "LitRPG (Literary Role Playing Game)",
        "Game-based Fantasy",
        "Short Stories (Cerpen)",
        "Poetry & Prose (Puisi & Prosa)",
        "Interactive Fiction"
    ]
}

# Legacy default categories (for backward compatibility)
legacy_categories = [
    "Teknologi",
    "Olahraga",
    "Keuangan",
    "Hiburan",
    "Kesehatan",
    "Sains",
    "Pendidikan",
    "Perjalanan",
    "Makanan",
    "Lifestyle",
    "Otomotif",
    "Politik",
    "Lingkungan",
    "Seni & Budaya",
    "Mode",
    "Bisnis",
    "Properti",
    "Opini",
    "Internasional",
    "Regional",
    "Games",
    "Fotografi",
    "Parenting",
    "Lainnya" 
]


def add_categories_with_groups(use_groups=True, num_legacy_categories=None):
    with app.app_context():
        print("📂 LilyOpenCMS Category Generator with Groups")
        print("=" * 60)
        
        if use_groups:
            print("🎯 Using new category groups system")
            print(f"📂 Creating {len(category_groups_data)} category groups...")
            
            groups_created = 0
            categories_created = 0
            
            # Create category groups and their categories
            for group_name, categories in category_groups_data.items():
                print(f"\n📂 Processing group: {group_name}")
                
                # Get or create category group
                group = CategoryGroup.query.filter_by(name=group_name).first()
                if not group:
                    group = CategoryGroup(
                        name=group_name,
                        description=f"Kategori untuk {group_name.lower()}",
                        display_order=len(category_groups_data) - list(category_groups_data.keys()).index(group_name)
                    )
                    db.session.add(group)
                    db.session.flush()  # Get the ID
                    print(f"✅ Created group: {group_name}")
                    groups_created += 1
                else:
                    print(f"✅ Group exists: {group_name}")
                
                # Create categories for this group
                for i, category_name in enumerate(categories):
                    existing_category = Category.query.filter_by(name=category_name).first()
                    if not existing_category:
                        category = Category(
                            name=category_name,
                            description=f"Kategori {category_name}",
                            display_order=i + 1,
                            group_id=group.id
                        )
                        db.session.add(category)
                        print(f"   ✅ Created category: {category_name}")
                        categories_created += 1
                    else:
                        # Update existing category to be in the group
                        existing_category.group_id = group.id
                        existing_category.display_order = i + 1
                        print(f"   ✅ Updated category: {category_name}")
            
            # Commit all changes
            if groups_created > 0 or categories_created > 0:
                try:
                    db.session.commit()
                    print(f"\n✅ Successfully created {groups_created} groups and {categories_created} categories!")
                except Exception as e:
                    db.session.rollback()
                    print(f"\n❌ Error committing categories: {e}")
                    return False
            
            # Show summary
            print("\n📊 Summary:")
            group_count = CategoryGroup.query.count()
            category_count = Category.query.count()
            print(f"   📂 Category Groups: {group_count}")
            print(f"   🏷️ Categories: {category_count}")
            
        else:
            print("🎯 Using legacy flat categories system")
            print(f"📂 Adding legacy categories...")
            
            num_defaults = len(legacy_categories)
            
            # Determine the final list of category names
            target_categories = set()  # Use a set for efficient uniqueness checks
            
            if num_legacy_categories is None:
                # Default case: use all predefined categories
                target_categories.update(legacy_categories)
                print(f"Using all {num_defaults} predefined legacy categories.")
            elif num_legacy_categories <= num_defaults:
                # User wants a subset of predefined categories
                target_categories.update(legacy_categories[:num_legacy_categories])
                print(f"Using the first {num_legacy_categories} predefined legacy categories.")
            else:
                # User wants more categories than predefined: use all defaults + generate extras
                target_categories.update(legacy_categories)
                num_to_generate = num_legacy_categories - num_defaults
                print(f"Using all {num_defaults} predefined legacy categories.")
                print(f"Attempting to generate {num_to_generate} additional unique categories using Faker...")
                
                generated_count = 0
                attempts = 0
                max_attempts = num_to_generate * 5  # Give up after a reasonable number of tries
                
                while generated_count < num_to_generate and attempts < max_attempts:
                    new_cat_name = fake.word().capitalize()
                    # Ensure it's not empty, not already default, and not already generated
                    if new_cat_name and len(new_cat_name) > 2 and new_cat_name not in target_categories:
                        target_categories.add(new_cat_name)
                        generated_count += 1
                    attempts += 1
                
                if generated_count < num_to_generate:
                    print(f"⚠️ Warning: Could only generate {generated_count} unique categories after {max_attempts} attempts (reached {len(target_categories)} total).")
                else:
                    print(f"   Successfully generated {generated_count} additional categories.")
            
            # Determine which categories to add
            categories_to_process = sorted(list(target_categories))  # Sort for consistent order
            print(f"Attempting to add {len(categories_to_process)} categories...")
            added_count = 0
            skipped_count = 0
            
            # Loop through the selected categories and add them
            for category_name in categories_to_process:
                # Check if the category already exists
                existing_category = Category.query.filter_by(name=category_name).first()
                if not existing_category:
                    # Create a new Category object (without group assignment)
                    new_category = Category(name=category_name)
                    db.session.add(new_category)
                    print(f"  + Adding '{category_name}'")
                    added_count += 1
                else:
                    skipped_count += 1
            
            # Commit the changes to the database
            if added_count > 0:
                try:
                    db.session.commit()
                    print(f"\n✅ Successfully added {added_count} new categories.")
                    if skipped_count > 0:
                        print(f"   Skipped {skipped_count} categories that already existed.")
                except Exception as e:
                    db.session.rollback()
                    print(f"\n❌ Error committing categories: {e}")
                    return False
            elif skipped_count > 0 and added_count == 0:
                print(f"\n🤷 No new categories were added ({skipped_count} selected categories already exist).")
            else:
                print("\n🤷 No categories were processed or added.")
        
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add categories to the database using the new groups system or legacy flat system.")
    parser.add_argument(
        "--legacy",
        action="store_true",
        help="Use legacy flat categories system instead of groups"
    )
    parser.add_argument(
        "--num-cat",
        type=int,
        default=None,
        help="Total number of legacy categories desired. Only used with --legacy flag."
    )
    args = parser.parse_args()
    
    # Validate num_cat if provided with legacy
    if args.legacy and args.num_cat is not None and args.num_cat <= 0:
        print("❌ Error: --num-cat must be a positive integer when using --legacy.", file=sys.stderr)
        sys.exit(1)
    
    # Use groups by default, legacy only if --legacy flag is provided
    use_groups = not args.legacy
    
    if use_groups:
        print("🎯 Using new category groups system")
        add_categories_with_groups(use_groups=True)
    else:
        print("🎯 Using legacy flat categories system")
        add_categories_with_groups(use_groups=False, num_legacy_categories=args.num_cat)
