#!/usr/bin/env python3
"""
Helper script to add test album data to the database.
This script creates sample albums with chapters using real data from the database.
Only runs if sufficient data is available.
"""

import sys
import os
import random

# Add the parent directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Now import the app
from main import app
from models import db, Album, AlbumChapter, News, Category, User, UserRole, Image
from datetime import datetime, timezone
from faker import Faker

# Initialize Faker for generating fake data
fake = Faker()

def check_and_clear_existing_albums():
    """Check if albums exist and clear them if found."""
    with app.app_context():
        existing_albums = Album.query.count()
        if existing_albums > 0:
            print(f"🗑️  Found {existing_albums} existing albums. Clearing them...")
            
            # Delete all album chapters first (foreign key constraint)
            deleted_chapters = AlbumChapter.query.delete()
            print(f"   - Deleted {deleted_chapters} album chapters")
            
            # Delete all albums
            deleted_albums = Album.query.delete()
            print(f"   - Deleted {deleted_albums} albums")
            
            db.session.commit()
            print("✅ Successfully cleared existing albums")
            return True
        else:
            print("✅ No existing albums found. Proceeding with creation...")
            return False

def generate_album_title(category_name):
    """Generate realistic album titles based on category."""
    title_templates = {
        'Teknologi': [
            "Seri {category}: {topic}",
            "{topic} di Era Digital",
            "Panduan Lengkap {topic}",
            "Eksplorasi {topic}",
            "Seri {category}: {topic} Terkini"
        ],
        'Bisnis': [
            "Strategi {topic} untuk Bisnis",
            "Panduan {topic} di {category}",
            "Seri {category}: {topic}",
            "Masterclass {topic}",
            "Seri {category}: {topic} Sukses"
        ],
        'Lifestyle': [
            "Seri {category}: {topic}",
            "Panduan {topic} untuk Hidup Sehat",
            "Seri {category}: {topic} Terkini",
            "Eksplorasi {topic}",
            "Seri {category}: {topic} Populer"
        ],
        'Travel': [
            "Petualangan {topic}",
            "Seri {category}: {topic}",
            "Panduan Wisata {topic}",
            "Eksplorasi {topic}",
            "Seri {category}: {topic} Terbaik"
        ],
        'Kesehatan': [
            "Seri {category}: {topic}",
            "Panduan {topic} untuk Kesehatan",
            "Seri {category}: {topic} Terkini",
            "Eksplorasi {topic}",
            "Seri {category}: {topic} Sehat"
        ],
        'Pendidikan': [
            "Seri {category}: {topic}",
            "Panduan {topic} untuk Belajar",
            "Seri {category}: {topic} Terkini",
            "Eksplorasi {topic}",
            "Seri {category}: {topic} Berkualitas"
        ]
    }
    
    # Get templates for this category or use default
    templates = title_templates.get(category_name, [
        "Seri {category}: {topic}",
        "Panduan {topic}",
        "Eksplorasi {topic}",
        "Seri {category}: {topic} Terkini"
    ])
    
    # Generate topic based on category
    topics = {
        'Teknologi': ['AI dan Machine Learning', 'Blockchain', 'Cloud Computing', 'Cybersecurity', 'IoT', 'Mobile Development', 'Web Development', 'Data Science', 'Artificial Intelligence', 'Blockchain Technology', 'Cloud Computing', 'Cybersecurity', 'Internet of Things', 'Mobile Development', 'Web Development', 'Data Science'],
        'Bisnis': ['Startup', 'Marketing Digital', 'E-commerce', 'Investasi', 'Manajemen', 'Strategi Bisnis', 'Fintech', 'Entrepreneurship', 'Startup', 'Marketing Digital', 'E-commerce', 'Investasi', 'Manajemen', 'Strategi Bisnis', 'Fintech', 'Entrepreneurship'],
        'Lifestyle': ['Fashion', 'Beauty', 'Fitness', 'Wellness', 'Hobi', 'Entertainment', 'Food', 'Home Living', 'Fashion', 'Beauty', 'Fitness', 'Wellness', 'Hobi', 'Entertainment', 'Food', 'Home Living'],
        'Travel': ['Backpacking', 'Budget Travel', 'Luxury Travel', 'Adventure', 'Cultural Tourism', 'Food Tourism', 'Eco Tourism', 'City Exploration', 'Backpacking', 'Budget Travel', 'Luxury Travel', 'Adventure', 'Cultural Tourism', 'Food Tourism', 'Eco Tourism', 'City Exploration'],
        'Kesehatan': ['Nutrisi', 'Mental Health', 'Physical Fitness', 'Preventive Care', 'Alternative Medicine', 'Wellness', 'Medical Technology', 'Nutrisi', 'Mental Health', 'Physical Fitness', 'Preventive Care', 'Alternative Medicine', 'Wellness', 'Medical Technology'],
        'Pendidikan': ['Online Learning', 'Skill Development', 'Language Learning', 'Academic Research', 'Educational Technology', 'Teaching Methods', 'Online Learning', 'Skill Development', 'Language Learning', 'Academic Research', 'Educational Technology', 'Teaching Methods'],
        'Investasi': ['Pasar Modal', 'Portofolio Investasi', 'Analisis Fundamental', 'Analisis Teknikal', 'Strategi Investasi', 'Manajemen Risiko', 'Perencanaan Keuangan', 'Pengembangan Karir', 'Pasar Modal', 'Portofolio Investasi', 'Analisis Fundamental', 'Analisis Teknikal', 'Strategi Investasi', 'Manajemen Risiko', 'Perencanaan Keuangan', 'Pengembangan Karir'],
        'Kesehatan': ['Nutrisi', 'Mental Health', 'Physical Fitness', 'Preventive Care', 'Alternative Medicine', 'Wellness', 'Medical Technology', 'Nutrisi', 'Mental Health', 'Physical Fitness', 'Preventive Care', 'Alternative Medicine', 'Wellness', 'Medical Technology'],
        'Lainnya': ['Pembelajaran', 'Eksplorasi', 'Panduan', 'Seri', 'Kumpulan', 'Artikel', 'Terbaru', 'Terpopuler', 'Terpilih', 'Terinspirasi', 'Terbaik', 'Terbaru', 'Terpopuler', 'Terpilih', 'Terinspirasi', 'Terbaik']
    }
    
    category_topics = topics.get(category_name, ['Pembelajaran', 'Eksplorasi', 'Panduan', 'Seri'])
    topic = random.choice(category_topics)
    
    template = random.choice(templates)
    return template.format(category=category_name, topic=topic)

def generate_album_description(category_name, title):
    """Generate realistic album descriptions."""
    description_templates = [
        "Kumpulan artikel {category} yang dikurasi dengan baik untuk memberikan wawasan mendalam tentang {topic}. Album ini menyajikan berbagai perspektif dan analisis mendalam yang akan membantu pembaca memahami kompleksitas dan nuansa dari topik yang dibahas. Setiap artikel dipilih berdasarkan relevansi, akurasi, dan nilai edukatifnya untuk memastikan pengalaman membaca yang optimal.",
        "Seri lengkap tentang {topic} dalam kategori {category} yang disusun secara sistematis untuk memudahkan pembelajaran. Album ini dirancang dengan struktur yang logis dan progresif, mulai dari konsep dasar hingga aspek yang lebih kompleks. Pembaca akan menemukan berbagai sudut pandang, studi kasus, dan praktik terbaik yang dapat diterapkan dalam konteks nyata.",
        "Eksplorasi mendalam tentang {topic} melalui berbagai artikel {category} yang informatif dan up-to-date. Album ini menggabungkan penelitian terkini, wawasan dari para ahli, dan analisis mendalam untuk memberikan pemahaman yang komprehensif. Setiap artikel dirancang untuk membangun pengetahuan secara bertahap, memastikan pembaca dapat mengikuti perkembangan topik dengan mudah.",
        "Panduan komprehensif tentang {topic} yang mencakup aspek-aspek penting dalam dunia {category}. Album ini menyajikan berbagai dimensi dari topik yang dibahas, termasuk aspek teoritis, praktis, dan implementatif. Pembaca akan menemukan kombinasi yang seimbang antara konsep akademis dan aplikasi praktis yang dapat langsung diterapkan.",
        "Koleksi artikel terbaik tentang {topic} yang dipilih untuk memberikan perspektif yang luas dalam {category}. Album ini menghadirkan berbagai pendekatan, metodologi, dan sudut pandang yang berbeda untuk memberikan pemahaman yang holistik. Setiap artikel dipilih berdasarkan kualitas konten, relevansi, dan kemampuannya untuk menambah nilai bagi pembaca.",
        "Kumpulan artikel terbaru tentang {topic} yang dikumpulkan untuk memberikan wawasan mendalam dan informasi terkini. Album ini menampilkan perkembangan terbaru dalam bidang {category}, termasuk inovasi, tren, dan praktik terbaik yang sedang berkembang. Pembaca akan mendapatkan akses ke informasi yang up-to-date dan relevan dengan kondisi saat ini.",
        "Seri edukatif yang komprehensif tentang {topic} dalam konteks {category} yang dirancang untuk memenuhi kebutuhan berbagai tingkat pemahaman. Album ini menyajikan konten yang dapat diakses oleh pemula namun tetap memberikan kedalaman yang memuaskan bagi pembaca yang lebih berpengalaman. Setiap artikel dirancang dengan pendekatan yang sistematis dan mudah dipahami.",
        "Eksplorasi mendalam dan terstruktur tentang {topic} yang menghadirkan berbagai aspek dalam dunia {category}. Album ini menggabungkan teori dan praktik, penelitian dan implementasi, serta konsep dan aplikasi untuk memberikan pemahaman yang menyeluruh. Pembaca akan menemukan berbagai sumber informasi yang dapat dipercaya dan relevan dengan kebutuhan mereka.",
        "Kumpulan artikel yang dikurasi dengan teliti tentang {topic} yang menyajikan berbagai perspektif dan pendekatan dalam {category}. Album ini dirancang untuk memberikan pengalaman belajar yang kaya dan beragam, dengan setiap artikel menambahkan dimensi baru pada pemahaman tentang topik yang dibahas. Konten disusun dengan mempertimbangkan kebutuhan pembaca dari berbagai latar belakang.",
        "Seri lengkap dan mendalam tentang {topic} yang menghadirkan berbagai aspek penting dalam {category}. Album ini menyajikan kombinasi yang seimbang antara informasi teoritis dan praktis, dengan fokus pada aplikasi nyata dan implementasi yang efektif. Setiap artikel dipilih berdasarkan kemampuannya untuk memberikan nilai tambah dan wawasan yang berguna bagi pembaca."
    ]
    
    # Extract topic from title
    topic = title.replace(f"Seri {category_name}: ", "").replace(f" di Era Digital", "").replace(f" untuk Bisnis", "").replace(f" untuk Hidup Sehat", "").replace(f" Terkini", "").replace(f" Populer", "").replace(f" Sukses", "").replace(f" Sehat", "").replace(f" Berkualitas", "").replace(f" Terbaik", "").replace(f" Terbaru", "")
    
    template = random.choice(description_templates)
    return template.format(category=category_name, topic=topic)

def generate_chapter_title(album_title, chapter_number, category_name):
    """Generate realistic chapter titles based on album theme."""
    # Extract main topic from album title
    main_topic = album_title.replace(f"Seri {category_name}: ", "").replace(f" di Era Digital", "").replace(f" untuk Bisnis", "").replace(f" untuk Hidup Sehat", "").replace(f" Terkini", "").replace(f" Populer", "").replace(f" Sukses", "").replace(f" Sehat", "").replace(f" Berkualitas", "").replace(f" Terbaik", "").replace(f" Terbaru", "")
    
    chapter_templates = {
        'Teknologi': [
            "Pengenalan {topic}",
            "Dasar-dasar {topic}",
            "Implementasi {topic}",
            "Best Practices {topic}",
            "Trend {topic} Terkini",
            "Case Study {topic}"
        ],
        'Bisnis': [
            "Strategi {topic}",
            "Analisis {topic}",
            "Implementasi {topic}",
            "Success Story {topic}",
            "Tips dan Trik {topic}",
            "Future of {topic}"
        ],
        'Lifestyle': [
            "Panduan {topic}",
            "Tips {topic}",
            "Trend {topic}",
            "Inspirasi {topic}",
            "How-to {topic}",
            "Best of {topic}"
        ],
        'Travel': [
            "Destinasi {topic}",
            "Panduan {topic}",
            "Tips {topic}",
            "Experience {topic}",
            "Hidden Gem {topic}",
            "Must-visit {topic}"
        ],
        'Kesehatan': [
            "Panduan {topic}",
            "Tips {topic}",
            "Manfaat {topic}",
            "Cara {topic}",
            "Best Practice {topic}",
            "Research {topic}"
        ],
        'Pendidikan': [
            "Pengenalan {topic}",
            "Metode {topic}",
            "Strategi {topic}",
            "Best Practice {topic}",
            "Case Study {topic}",
            "Future of {topic}"
        ],
        'Investasi': [
            "Pengenalan {topic}",
            "Metode {topic}",
            "Strategi {topic}",
            "Best Practice {topic}",
            "Case Study {topic}",
            "Future of {topic}"
        ],
        'Kesehatan': [
            "Pengenalan {topic}",
            "Metode {topic}",
            "Strategi {topic}",
            "Best Practice {topic}",
            "Case Study {topic}",
            "Future of {topic}"
        ],
        'Lainnya': [
            "Pengenalan {topic}",
            "Metode {topic}",
            "Strategi {topic}",
            "Best Practice {topic}",
            "Case Study {topic}",
            "Future of {topic}"
        ]
    }
    
    templates = chapter_templates.get(category_name, [
        "Pengenalan {topic}",
        "Panduan {topic}",
        "Tips {topic}",
        "Best Practice {topic}",
        "Case Study {topic}"
    ])
    
    template = random.choice(templates)
    return template.format(topic=main_topic)

def add_test_albums(min_chapters=4, max_chapters=12, target_albums=50):
    """Add test album data to the database using real data.
    
    Args:
        min_chapters (int): Minimum number of chapters per album (default: 4)
        max_chapters (int): Maximum number of chapters per album (default: 12)
        target_albums (int): Target number of albums to generate (default: 50)
    """
    with app.app_context():
        print("🎵 Adding test album data using real database content...")
        print(f"📊 Chapter configuration: {min_chapters}-{max_chapters} chapters per album")
        print(f"🎯 Target albums: {target_albums}")
        
        # Check and clear existing albums
        check_and_clear_existing_albums()
        
        # Get existing data
        users = User.query.filter(User.role.in_([UserRole.ADMIN, UserRole.SUPERUSER])).all()
        categories = Category.query.all()
        news_articles = News.query.filter_by(is_visible=True).all()
        images = Image.query.all()  # Get all images, visibility doesn't matter for cover images
        
        # Check minimum requirements
        if not users:
            print("❌ No admin users found. Please add users first.")
            return
        
        if not categories:
            print("❌ No categories found. Please add categories first.")
            return
        
        if len(news_articles) < min_chapters:
            print(f"❌ Insufficient news articles ({len(news_articles)}). Need at least {min_chapters} articles.")
            return
        
        if len(images) < 5:
            print(f"❌ Insufficient images ({len(images)}). Need at least 5 images.")
            print(f"   Available images: {[img.filename for img in images[:3]]}...")
            return
        
        print(f"✅ Found {len(users)} admin users, {len(categories)} categories, {len(news_articles)} news articles, {len(images)} images")
        
        # Debug image information
        visible_images = Image.query.filter_by(is_visible=True).count()
        print(f"   - Total images: {len(images)}")
        print(f"   - Visible images: {visible_images}")
        print(f"   - Hidden images: {len(images) - visible_images}")
        print(f"   - Using balanced image pool for album covers (like news generation)")
        
        # Create a balanced image pool for even distribution (like in add_fake_news.py)
        image_pool = []
        image_pool_index = 0
        
        if images:
            # Calculate how many times each image should be used for album covers
            images_needed = target_albums  # We need one image per album
            if images_needed > 0:
                times_per_image = max(1, images_needed // len(images))
                remainder = images_needed % len(images)
                
                # Create a pool where each image appears the calculated number of times
                for i, image in enumerate(images):
                    # Add base number of times
                    for _ in range(times_per_image):
                        image_pool.append(image)
                    # Add remainder to first few images
                    if i < remainder:
                        image_pool.append(image)
                
                # Shuffle the pool to randomize the order
                random.shuffle(image_pool)
                
                print(f"   Created image pool: {len(image_pool)} image slots for {images_needed} needed album covers")
                print(f"   Each image will be used approximately {times_per_image} times")
        else:
            print("⚠️ Warning: No images found in the database. All created albums will lack cover images.")
        
        # Create albums based on real news content
        albums_data = []
        
        # Group news by category to create themed albums
        news_by_category = {}
        for news in news_articles:
            if news.category:
                cat_name = news.category.name
                if cat_name not in news_by_category:
                    news_by_category[cat_name] = []
                news_by_category[cat_name].append(news)
        
        # Create multiple albums per category for variety
        for category_name, category_news in news_by_category.items():
            if len(category_news) >= min_chapters:  # Need at least min_chapters articles for an album
                # Calculate how many albums we can create for this category
                max_albums_per_category = len(category_news) // min_chapters
                num_albums_per_category = min(8, max_albums_per_category)  # Increased to 8 albums per category
                
                for album_num in range(num_albums_per_category):
                    # Generate different album themes for the same category
                    album_themes = [
                        f"Seri {category_name}",
                        f"Panduan Lengkap {category_name}",
                        f"Eksplorasi {category_name}",
                        f"Masterclass {category_name}",
                        f"Kumpulan {category_name} Terbaik",
                        f"Seri {category_name} Premium",
                        f"Eksplorasi Mendalam {category_name}",
                        f"Koleksi {category_name} Terpilih"
                    ]
                    
                    album_title = album_themes[album_num] if album_num < len(album_themes) else f"Seri {category_name} #{album_num + 1}"
                    album_description = generate_album_description(category_name, album_title)
                    
                    # Determine if premium based on category and album number
                    premium_categories = ['Teknologi', 'Bisnis', 'Investasi', 'Lifestyle', 'Kesehatan']
                    is_premium = any(premium in category_name for premium in premium_categories) and album_num < 3  # First 3 albums are premium
                    # Assign content age rating based on premium flag
                    age_rating = '17+' if is_premium else 'SU'
                    
                    # Create chapters from different news articles for each album
                    start_idx = album_num * min_chapters
                    end_idx = start_idx + max_chapters
                    album_news = category_news[start_idx:end_idx]
                    
                    # Determine actual number of chapters for this album (within min-max range)
                    available_articles = len(album_news)
                    if available_articles >= min_chapters:
                        # Randomly choose number of chapters within min-max range
                        actual_chapters = random.randint(min_chapters, min(max_chapters, available_articles))
                        album_news = album_news[:actual_chapters]  # Limit to actual chapters needed
                        
                        chapters = []
                        for i, news in enumerate(album_news, 1):
                            chapter_title = generate_chapter_title(album_title, i, category_name)
                            chapters.append({
                                "news_id": news.id,
                                "title": chapter_title,
                                "number": i
                            })
                        
                        albums_data.append({
                            "title": album_title,
                            "description": album_description,
                            "is_premium": is_premium,
                            "is_visible": True,
                            "is_completed": False,  # Will be set later based on 65% rule
                            "is_hiatus": random.random() < 0.15,  # 15% chance of hiatus
                            "category_id": category_news[0].category_id,
                            "age_rating": age_rating,
                            "chapters": chapters
                        })
        
        # Create more mixed albums for variety
        print("📝 Creating mixed-content albums...")
        
        # Get remaining news that haven't been used in category albums
        used_news_ids = set()
        for album in albums_data:
            for chapter in album["chapters"]:
                used_news_ids.add(chapter["news_id"])
        
        remaining_news = [n for n in news_articles if n.id not in used_news_ids]
        
        # Create multiple mixed albums
        mixed_album_templates = [
            {
                "title": "Kumpulan Artikel Terpopuler",
                "description": "Artikel-artikel dengan pembacaan tertinggi yang dikurasi khusus untuk pembaca setia",
                "is_premium": False,
                "is_completed": False,
                "is_hiatus": False
            },
            {
                "title": "Seri Artikel Terbaru",
                "description": "Artikel-artikel terbaru yang layak dibaca dan memberikan wawasan terkini",
                "is_premium": True,
                "is_completed": False,
                "is_hiatus": False
            },
            {
                "title": "Koleksi Artikel Pilihan Editor",
                "description": "Artikel-artikel terpilih yang direkomendasikan oleh tim editorial",
                "is_premium": True,
                "is_completed": False,
                "is_hiatus": False
            },
            {
                "title": "Seri Artikel Viral",
                "description": "Artikel-artikel yang sedang trending dan banyak dibicarakan",
                "is_premium": False,
                "is_completed": False,
                "is_hiatus": False
            },
            {
                "title": "Kumpulan Artikel Inspiratif",
                "description": "Artikel-artikel yang menginspirasi dan memotivasi pembaca",
                "is_premium": False,
                "is_completed": False,
                "is_hiatus": False
            },
            {
                "title": "Seri Artikel Premium",
                "description": "Artikel-artikel eksklusif untuk member premium",
                "is_premium": True,
                "is_completed": False,
                "is_hiatus": False
            },
            {
                "title": "Koleksi Artikel Terbaik Minggu Ini",
                "description": "Artikel-artikel terbaik yang dipilih setiap minggu",
                "is_premium": False,
                "is_completed": False,
                "is_hiatus": False
            },
            {
                "title": "Seri Artikel Trending",
                "description": "Artikel-artikel yang sedang populer dan banyak dibaca",
                "is_premium": False,
                "is_completed": False,
                "is_hiatus": False
            },
            {
                "title": "Kumpulan Artikel Edukatif",
                "description": "Artikel-artikel yang memberikan pengetahuan dan wawasan baru",
                "is_premium": False,
                "is_completed": False,
                "is_hiatus": False
            },
            {
                "title": "Seri Artikel Inovatif",
                "description": "Artikel-artikel yang membahas inovasi dan perkembangan terbaru",
                "is_premium": True,
                "is_completed": False,
                "is_hiatus": False
            }
        ]
        
        # Create mixed albums based on available remaining news
        for i, template in enumerate(mixed_album_templates):
            if len(remaining_news) >= min_chapters:
                # Determine actual number of chapters for this mixed album (within min-max range)
                available_articles = len(remaining_news)
                actual_chapters = random.randint(min_chapters, min(max_chapters, available_articles))
                album_news = remaining_news[:actual_chapters]
                remaining_news = remaining_news[actual_chapters:]  # Remove used articles
                
                chapters = []
                for j, news in enumerate(album_news, 1):
                    chapters.append({
                        "news_id": news.id,
                        "title": f"{template['title']} #{j}",
                        "number": j
                    })
                
                albums_data.append({
                    "title": template["title"],
                    "description": template["description"],
                    "is_premium": template["is_premium"],
                    "is_visible": True,
                    "is_completed": False,  # Will be set later based on 65% rule
                    "is_hiatus": template["is_hiatus"],
                    "category_id": random.choice(categories).id,
                    "age_rating": '17+' if template["is_premium"] else 'SU',
                    "chapters": chapters
                })
        
        # Create additional themed albums to reach target
        print("📝 Creating additional themed albums...")
        
        # Create more albums with different themes
        additional_themes = [
            "Seri Artikel Terkini",
            "Kumpulan Artikel Pilihan",
            "Seri Artikel Populer",
            "Koleksi Artikel Terbaik",
            "Seri Artikel Viral",
            "Kumpulan Artikel Trending",
            "Seri Artikel Premium",
            "Koleksi Artikel Edukatif",
            "Seri Artikel Inovatif",
            "Kumpulan Artikel Inspiratif"
        ]
        
        # Create additional albums until we reach target or run out of content
        while len(albums_data) < target_albums and len(remaining_news) >= min_chapters:
            theme = random.choice(additional_themes)
            available_articles = len(remaining_news)
            actual_chapters = random.randint(min_chapters, min(max_chapters, available_articles))
            album_news = remaining_news[:actual_chapters]
            remaining_news = remaining_news[actual_chapters:]
            
            chapters = []
            for j, news in enumerate(album_news, 1):
                chapters.append({
                    "news_id": news.id,
                    "title": f"{theme} #{j}",
                    "number": j
                })
            
            albums_data.append({
                "title": f"{theme} #{len(albums_data) + 1}",
                "description": f"Kumpulan artikel {theme.lower()} yang dikurasi dengan baik",
                "is_premium": random.random() < 0.3,  # 30% chance of premium
                "is_visible": True,
                "is_completed": False,  # Will be set later based on 65% rule
                "is_hiatus": random.random() < 0.1,  # 10% chance of hiatus
                "category_id": random.choice(categories).id,
                "age_rating": '17+' if random.random() < 0.3 else 'SU',
                "chapters": chapters
            })
        
        if not albums_data:
            print("❌ Could not create albums from available content.")
            return
        
        # Apply 65% completion rule
        total_albums = len(albums_data)
        max_completed = int(total_albums * 0.65)  # Max 65% completed
        completed_count = 0
        
        # Randomly select albums to mark as completed
        albums_to_complete = random.sample(albums_data, min(max_completed, len(albums_data)))
        for album in albums_to_complete:
            album["is_completed"] = True
            completed_count += 1
        
        print(f"📚 Creating {len(albums_data)} albums from real content...")
        print(f"📊 Completion rule: {completed_count}/{total_albums} albums will be completed ({(completed_count/total_albums)*100:.1f}%)")
        
        created_albums = 0
        
        for album_data in albums_data:
            try:
                # Select random admin user
                user = random.choice(users)
                
                # Select cover image using balanced pool approach
                cover_image = None
                if image_pool:
                    # Use the balanced image pool
                    if image_pool_index < len(image_pool):
                        cover_image = image_pool[image_pool_index]
                        image_pool_index += 1
                    else:
                        # If we've used all images in the pool, start over
                        image_pool_index = 0
                        cover_image = image_pool[image_pool_index]
                        image_pool_index += 1
                        print(f"   ⚠️ Reusing image pool (cycle {image_pool_index // len(image_pool) + 1})")
                elif images:
                    # Fallback to random selection if no image pool
                    cover_image = random.choice(images)
                
                # Create album
                album = Album(
                    title=album_data["title"],
                    description=album_data["description"],
                    category_id=album_data["category_id"],
                    user_id=user.id,
                    cover_image_id=cover_image.id if cover_image else None,
                    is_premium=album_data["is_premium"],
                    is_visible=album_data["is_visible"],
                    is_completed=album_data["is_completed"],
                    is_hiatus=album_data["is_hiatus"],
                    is_archived=False,
                    age_rating=album_data.get("age_rating"),
                    total_chapters=0,
                    total_reads=random.randint(0, 2000)  # Increased read range
                )
                
                album.validate()
                db.session.add(album)
                db.session.flush()  # Get the album ID
                
                # Add chapters from real news articles
                chapter_count = 0
                for chapter_data in album_data["chapters"]:
                    chapter = AlbumChapter(
                        album_id=album.id,
                        news_id=chapter_data["news_id"],
                        chapter_title=chapter_data["title"],
                        chapter_number=chapter_data["number"],
                        is_visible=True
                    )
                    
                    chapter.validate()
                    db.session.add(chapter)
                    chapter_count += 1
                
                # Update album chapter count
                album.total_chapters = chapter_count
                
                created_albums += 1
                category_name = next((cat.name for cat in categories if cat.id == album_data["category_id"]), "Unknown")
                status = "✅" if album_data["is_completed"] else "🔄"
                print(f"{status} Created album: {album.title} ({category_name}) with {chapter_count} chapters by {user.username}")
                
            except Exception as e:
                print(f"❌ Error creating album '{album_data['title']}': {e}")
                db.session.rollback()
                continue
        
        try:
            db.session.commit()
            print(f"\n🎉 Successfully created {created_albums} albums from real content!")
            print("📊 Album Statistics:")
            print(f"   - Total albums created: {created_albums}")
            print(f"   - Premium albums: {Album.query.filter_by(is_premium=True).count()}")
            print(f"   - Completed albums: {Album.query.filter_by(is_completed=True).count()}")
            print(f"   - Hiatus albums: {Album.query.filter_by(is_hiatus=True).count()}")
            print(f"   - Total chapters created: {AlbumChapter.query.count()}")
            
            # Show image distribution statistics
            if image_pool:
                print(f"📊 Image Distribution:")
                print(f"   Total images available: {len(images)}")
                print(f"   Images used in pool: {len(image_pool)}")
                print(f"   Average usage per image: {len(image_pool) / len(images):.1f} times")
                if image_pool_index > len(image_pool):
                    cycles = image_pool_index // len(image_pool)
                    print(f"   Pool reused {cycles} times for complete distribution")
            
            print("You can now test the album management functionality.")
        except Exception as e:
            print(f"❌ Error committing to database: {e}")
            db.session.rollback()

if __name__ == "__main__":
    add_test_albums() 