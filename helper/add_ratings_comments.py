#!/usr/bin/env python3
"""
Helper script to add ratings, comments, and view counts to existing news articles and albums.
This script generates realistic ratings, comments, and view counts using available users from the database.
"""

import sys
import os
import argparse
import random
from datetime import datetime, timedelta, timezone

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

from models import Rating, Comment, CommentLike, User, News, Album
from faker import Faker

# Initialize Faker for generating realistic content
fake = Faker(['id_ID'])  # Use Indonesian locale for more realistic content


def check_and_clear_existing_data():
    """Check if ratings/comments exist and clear them if found."""
    with app.app_context():
        existing_ratings = Rating.query.count()
        existing_comments = Comment.query.count()
        existing_likes = CommentLike.query.count()
        
        if existing_ratings > 0 or existing_comments > 0:
            print(f"🗑️  Found existing data:")
            print(f"   - Ratings: {existing_ratings}")
            print(f"   - Comments: {existing_comments}")
            print(f"   - Comment likes/dislikes: {existing_likes}")
            print("   Clearing existing data...")
            
            # Delete in correct order due to foreign key constraints
            deleted_likes = CommentLike.query.delete()
            print(f"   - Deleted {deleted_likes} comment likes/dislikes")
            
            deleted_comments = Comment.query.delete()
            print(f"   - Deleted {deleted_comments} comments")
            
            deleted_ratings = Rating.query.delete()
            print(f"   - Deleted {deleted_ratings} ratings")
            
            db.session.commit()
            print("✅ Successfully cleared existing ratings and comments")
            return True
        else:
            print("✅ No existing ratings or comments found. Proceeding with creation...")
            return False


def generate_comment_content():
    """Generate realistic comment content in Indonesian with more variety."""
    comment_types = [
        # Positive comments
        {
            "templates": [
                "Artikel yang sangat informatif! {detail}",
                "Terima kasih atas informasinya. {detail}",
                "Sangat membantu sekali. {detail}",
                "Bagus sekali artikelnya. {detail}",
                "Informasi yang sangat berguna. {detail}",
                "Terima kasih sudah berbagi. {detail}",
                "Sangat menarik untuk dibaca. {detail}",
                "Artikel yang bagus dan bermanfaat. {detail}",
                "Informasi yang sangat lengkap. {detail}",
                "Sangat membantu untuk memahami {detail}",
                "Artikel yang sangat edukatif. {detail}",
                "Terima kasih atas penjelasannya. {detail}",
                "Sangat informatif dan mudah dipahami. {detail}",
                "Artikel yang sangat bermanfaat. {detail}",
                "Informasi yang sangat akurat. {detail}"
            ],
            "details": [
                "saya jadi lebih paham sekarang",
                "informasinya sangat jelas",
                "penjelasannya sangat detail",
                "sangat membantu untuk referensi",
                "materinya sangat komprehensif",
                "sangat berguna untuk pembelajaran",
                "informasinya sangat up-to-date",
                "sangat membantu untuk riset",
                "penjelasannya sangat sistematis",
                "materinya sangat relevan"
            ],
            "weight": 0.6
        },
        # Question comments
        {
            "templates": [
                "Bagaimana dengan {detail}?",
                "Apakah ada informasi lebih lanjut tentang {detail}?",
                "Saya penasaran dengan {detail}",
                "Bisa dijelaskan lebih detail tentang {detail}?",
                "Ada yang bisa share pengalaman tentang {detail}?",
                "Bagaimana pendapat teman-teman tentang {detail}?",
                "Saya ingin tahu lebih banyak tentang {detail}",
                "Apakah ada referensi lain untuk {detail}?"
            ],
            "details": [
                "implementasinya",
                "pengalaman praktis",
                "best practices",
                "case study",
                "tools yang digunakan",
                "metodologi",
                "hasil akhir",
                "prosesnya"
            ],
            "weight": 0.15
        },
        # Critical comments
        {
            "templates": [
                "Artikel bagus, tapi {detail}",
                "Informasi berguna, namun {detail}",
                "Sangat membantu, cuma {detail}",
                "Bagus sekali, tapi {detail}",
                "Terima kasih, namun {detail}",
                "Sangat informatif, tapi {detail}",
                "Artikel yang baik, namun {detail}"
            ],
            "details": [
                "bisa ditambahkan contoh praktis",
                "perlu penjelasan lebih detail",
                "bisa ditambahkan referensi",
                "perlu update informasi terbaru",
                "bisa ditambahkan tips",
                "perlu contoh kasus",
                "bisa ditambahkan tutorial step-by-step"
            ],
            "weight": 0.15
        },
        # Short reactions
        {
            "templates": [
                "👍 {detail}",
                "Nice! {detail}",
                "Keren! {detail}",
                "Mantap! {detail}",
                "Bagus! {detail}",
                "Sip! {detail}",
                "Top! {detail}",
                "Wah! {detail}"
            ],
            "details": [
                "artikelnya",
                "infonya",
                "penjelasannya",
                "materinya",
                "kontennya",
                "sharingnya"
            ],
            "weight": 0.1
        },
        # Detailed comments
        {
            "templates": [
                "Artikel ini sangat membantu untuk {detail}. Saya sudah mencoba dan hasilnya {detail}. Terima kasih sudah berbagi pengalaman!",
                "Informasi yang sangat lengkap tentang {detail}. Saya suka bagaimana penjelasannya {detail}. Sangat bermanfaat untuk {detail}.",
                "Artikel yang bagus sekali! {detail} sangat jelas dijelaskan. Saya sudah mengaplikasikan dan {detail}. Recommended!",
                "Terima kasih atas artikel yang informatif ini. {detail} sangat berguna untuk {detail}. Saya akan {detail}."
            ],
            "details": [
                "pemula seperti saya",
                "sangat praktis",
                "mudah dipahami",
                "implementasi di project",
                "belajar teknologi baru",
                "referensi kerja",
                "penelitian saya",
                "pengembangan skill"
            ],
            "weight": 0.05
        }
    ]
    
    # Select comment type based on weights
    weights = [ct["weight"] for ct in comment_types]
    selected_type = random.choices(comment_types, weights=weights)[0]
    
    template = random.choice(selected_type["templates"])
    detail = random.choice(selected_type["details"])
    return template.format(detail=detail)


def generate_album_comment_content():
    """Generate realistic comment content for albums with more variety."""
    comment_types = [
        # Positive album comments
        {
            "templates": [
                "Album yang sangat menarik! {detail}",
                "Cerita yang sangat bagus. {detail}",
                "Sangat menantikan chapter selanjutnya. {detail}",
                "Plot yang sangat menarik. {detail}",
                "Karakter yang sangat berkembang dengan baik. {detail}",
                "Cerita yang sangat menghibur. {detail}",
                "Sangat suka dengan alur ceritanya. {detail}",
                "Album yang sangat direkomendasikan. {detail}",
                "Cerita yang sangat mendalam. {detail}",
                "Sangat menikmati setiap chapter. {detail}"
            ],
            "details": [
                "sangat menantikan kelanjutannya",
                "plot twist yang tidak terduga",
                "karakter yang sangat relatable",
                "cerita yang sangat original",
                "pengembangan karakter yang bagus",
                "alur cerita yang sangat smooth",
                "ending yang sangat memuaskan",
                "cerita yang sangat menghibur",
                "karakter yang sangat memorable",
                "plot yang sangat well-structured"
            ],
            "weight": 0.5
        },
        # Chapter-specific comments
        {
            "templates": [
                "Chapter {detail} sangat epic!",
                "Chapter {detail} bikin penasaran banget",
                "Chapter {detail} plot twistnya keren",
                "Chapter {detail} karakternya berkembang bagus",
                "Chapter {detail} endingnya unexpected",
                "Chapter {detail} sangat emotional",
                "Chapter {detail} action scenenya keren",
                "Chapter {detail} dialognya bagus"
            ],
            "details": [
                "terakhir",
                "ini",
                "sebelumnya",
                "awal",
                "pertengahan",
                "penutup"
            ],
            "weight": 0.2
        },
        # Character-focused comments
        {
            "templates": [
                "Karakter {detail} sangat menarik",
                "Saya suka dengan karakter {detail}",
                "Karakter {detail} developmentnya bagus",
                "Karakter {detail} sangat relatable",
                "Karakter {detail} bikin penasaran",
                "Karakter {detail} sangat memorable"
            ],
            "details": [
                "protagonis",
                "antagonis",
                "supporting character",
                "main character",
                "hero",
                "villain",
                "side character"
            ],
            "weight": 0.15
        },
        # Short reactions
        {
            "templates": [
                "🔥 {detail}",
                "💯 {detail}",
                "👏 {detail}",
                "🎉 {detail}",
                "💪 {detail}",
                "✨ {detail}",
                "🌟 {detail}",
                "💎 {detail}"
            ],
            "details": [
                "albumnya",
                "ceritanya",
                "plotnya",
                "karakternya",
                "chapternya",
                "endingnya"
            ],
            "weight": 0.1
        },
        # Questions about continuation
        {
            "templates": [
                "Kapan chapter selanjutnya? {detail}",
                "Chapter selanjutnya kapan ya? {detail}",
                "Menunggu chapter berikutnya. {detail}",
                "Update chapter selanjutnya dong! {detail}",
                "Kapan lanjutannya? {detail}"
            ],
            "details": [
                "penasaran banget",
                "sangat menantikan",
                "tidak sabar",
                "sangat excited",
                "sudah tidak sabar"
            ],
            "weight": 0.05
        },
        # Detailed album comments
        {
            "templates": [
                "Album yang sangat bagus! {detail} sangat menarik dan {detail}. Saya suka bagaimana {detail}. Sangat direkomendasikan!",
                "Cerita yang luar biasa! {detail} sangat well-developed dan {detail}. Plot twist di {detail} sangat unexpected. Keren!",
                "Sangat menikmati album ini. {detail} sangat relatable dan {detail}. Karakter development di {detail} sangat bagus.",
                "Album yang sangat menghibur! {detail} sangat original dan {detail}. Saya suka bagaimana {detail}. Menunggu chapter selanjutnya!"
            ],
            "details": [
                "karakter protagonis",
                "alur cerita",
                "plot development",
                "world building",
                "dialog antar karakter",
                "action scenes",
                "emotional moments",
                "character development",
                "plot twists",
                "story pacing"
            ],
            "weight": 0.05
        }
    ]
    
    # Select comment type based on weights
    weights = [ct["weight"] for ct in comment_types]
    selected_type = random.choices(comment_types, weights=weights)[0]
    
    template = random.choice(selected_type["templates"])
    detail = random.choice(selected_type["details"])
    return template.format(detail=detail)


def add_ratings_and_comments(num_ratings=200, num_comments=150, comment_likes_prob=0.3, inject_views=True):
    """Add ratings, comments, and view counts to existing news articles and albums.
    
    Args:
        num_ratings (int): Number of ratings to generate
        num_comments (int): Number of comments to generate  
        comment_likes_prob (float): Probability of adding likes/dislikes to comments
        inject_views (bool): Whether to inject realistic view counts to albums
    """
    with app.app_context():
        print("⭐ LilyOpenCMS Ratings & Comments Generator")
        print("=" * 50)

        # Check and clear existing data first
        check_and_clear_existing_data()

        # Get existing data
        users = User.query.filter_by(is_active=True).all()
        news_articles = News.query.filter_by(is_visible=True).all()
        albums = Album.query.filter_by(is_visible=True).all()

        if not users:
            print("❌ No active users found. Please add users first.")
            return

        if not news_articles and not albums:
            print("❌ No visible news articles or albums found. Please add content first.")
            return

        print(f"✅ Found {len(users)} active users, {len(news_articles)} news articles, {len(albums)} albums")

        # Inject realistic view counts to albums
        if inject_views and albums:
            print(f"\n👁️ Injecting view counts to {len(albums)} albums...")
            views_injected = 0
            
            for album in albums:
                try:
                    # Generate realistic view counts based on album age and content
                    # Newer albums get fewer views, older albums get more
                    now = datetime.now(timezone.utc)
                    if album.created_at.tzinfo is None:
                        # Handle timezone-naive datetime
                        album_created = album.created_at.replace(tzinfo=timezone.utc)
                    else:
                        album_created = album.created_at
                    days_old = (now - album_created).days
                    
                    # Base views calculation with some randomness
                    base_views = random.randint(50, 500)
                    
                    # Age multiplier (older content tends to have more views)
                    age_multiplier = min(1.0 + (days_old * 0.1), 3.0)  # Max 3x multiplier
                    
                    # Random popularity factor (some content is just more popular)
                    popularity_factor = random.choices(
                        [0.5, 0.8, 1.0, 1.5, 2.0, 3.0, 5.0],
                        weights=[0.1, 0.15, 0.3, 0.25, 0.15, 0.04, 0.01]
                    )[0]
                    
                    # Calculate final view count
                    calculated_views = int(base_views * age_multiplier * popularity_factor)
                    
                    # Add some random variation (±20%)
                    variation = random.uniform(0.8, 1.2)
                    final_views = max(1, int(calculated_views * variation))
                    
                    # Update album view count
                    album.total_views = final_views
                    views_injected += 1
                    
                except Exception as e:
                    print(f"❌ Error injecting views for album {album.id}: {e}")
                    continue
            
            try:
                db.session.commit()
                print(f"✅ Successfully injected view counts to {views_injected} albums")
                
                # Show view count statistics
                min_views = min(album.total_views for album in albums)
                max_views = max(album.total_views for album in albums)
                avg_views = sum(album.total_views for album in albums) / len(albums)
                print(f"   View count range: {min_views} - {max_views} (avg: {avg_views:.1f})")
                
            except Exception as e:
                db.session.rollback()
                print(f"❌ Error committing view counts: {e}")

        # Add ratings
        print(f"\n📊 Adding {num_ratings} ratings...")
        ratings_added = 0
        ratings_skipped = 0

        for i in range(num_ratings):
            try:
                # Randomly select user and content
                user = random.choice(users)
                content_type = random.choice(['news', 'album'])

                if content_type == 'news':
                    if not news_articles:
                        continue
                    content = random.choice(news_articles)
                else:
                    if not albums:
                        continue
                    content = random.choice(albums)

                # Check if user already rated this content
                existing_rating = Rating.query.filter_by(
                    user_id=user.id,
                    content_type=content_type,
                    content_id=content.id
                ).first()

                if existing_rating:
                    ratings_skipped += 1
                    continue

                # Generate rating (weighted towards positive ratings)
                rating_weights = [0.05, 0.1, 0.15, 0.3, 0.4]  # 1-5 stars
                rating_value = random.choices(
                    range(1, 6), weights=rating_weights)[0]

                # Create rating
                rating = Rating(
                    rating_value=rating_value,
                    content_type=content_type,
                    content_id=content.id,
                    user_id=user.id,
                    created_at=datetime.now(
                        # Up to 30 days ago
                        timezone.utc) - timedelta(hours=random.randint(0, 720))
                )

                rating.validate()
                db.session.add(rating)
                ratings_added += 1

                if (i + 1) % 50 == 0:
                    print(f"   Added {i + 1}/{num_ratings} ratings...")

            except Exception as e:
                print(f"❌ Error creating rating #{i+1}: {e}")
                db.session.rollback()
                continue

        # Add comments
        print(f"\n💬 Adding {num_comments} comments...")
        comments_added = 0
        comments_skipped = 0

        for i in range(num_comments):
            try:
                # Randomly select user and content
                user = random.choice(users)
                content_type = random.choice(['news', 'album'])

                if content_type == 'news':
                    if not news_articles:
                        continue
                    content = random.choice(news_articles)
                    comment_content = generate_comment_content()
                else:
                    if not albums:
                        continue
                    content = random.choice(albums)
                    comment_content = generate_album_comment_content()

                # Create comment
                comment = Comment(
                    content=comment_content,
                    content_type=content_type,
                    content_id=content.id,
                    user_id=user.id,
                    is_approved=True,
                    is_spam=False,
                    is_deleted=False,
                    created_at=datetime.now(
                        # Up to 30 days ago
                        timezone.utc) - timedelta(hours=random.randint(0, 720))
                )

                comment.validate()
                db.session.add(comment)

                # Flush to get the comment ID before adding likes
                db.session.flush()

                comments_added += 1

                # Add some comment likes/dislikes
                if random.random() < comment_likes_prob:
                    # Select unique users to like/dislike the comment
                    potential_likers = [u for u in users if u.id != user.id]
                    if not potential_likers:
                        continue

                    num_likes = random.randint(
                        1, min(3, len(potential_likers)))
                    selected_likers = random.sample(
                        potential_likers, num_likes)

                    for like_user in selected_likers:
                        is_like = random.choices(
                            [True, False], weights=[0.8, 0.2])[0]

                        comment_like = CommentLike(
                            comment_id=comment.id,
                            user_id=like_user.id,
                            is_like=is_like,
                            is_deleted=False,
                            created_at=datetime.now(
                                timezone.utc) - timedelta(hours=random.randint(0, 24))
                        )

                        comment_like.validate()
                        db.session.add(comment_like)

                if (i + 1) % 50 == 0:
                    print(f"   Added {i + 1}/{num_comments} comments...")

            except Exception as e:
                print(f"❌ Error creating comment #{i+1}: {e}")
                db.session.rollback()
                continue

        # Commit all changes
        try:
            db.session.commit()
            print("-" * 50)
            print("✅ Successfully added ratings and comments!")
            print(f"   Ratings: {ratings_added} added, {ratings_skipped} skipped (already existed)")
            print(f"   Comments: {comments_added} added")

            # Show statistics
            total_ratings = Rating.query.count()
            total_comments = Comment.query.count()
            total_likes = CommentLike.query.filter_by(
                is_like=True, is_deleted=False).count()
            total_dislikes = CommentLike.query.filter_by(
                is_like=False, is_deleted=False).count()

            print(f"\n📊 Statistics:")
            print(f"   Total ratings in database: {total_ratings}")
            print(f"   Total comments in database: {total_comments}")
            print(f"   Total comment likes: {total_likes}")
            print(f"   Total comment dislikes: {total_dislikes}")

            # Show average ratings
            if news_articles:
                news_ratings = Rating.query.filter_by(
                    content_type='news').count()
                print(f"   News ratings: {news_ratings}")

            if albums:
                album_ratings = Rating.query.filter_by(
                    content_type='album').count()
                print(f"   Album ratings: {album_ratings}")
                
                # Show view count statistics
                total_album_views = sum(album.total_views for album in albums)
                avg_album_views = total_album_views / len(albums)
                min_album_views = min(album.total_views for album in albums)
                max_album_views = max(album.total_views for album in albums)
                print(f"   Album views: {total_album_views} total (avg: {avg_album_views:.1f}, range: {min_album_views}-{max_album_views})")

            print("-" * 50)

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error committing to database: {e}")
            print("-" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Add ratings, comments, and view counts to existing content.")
    parser.add_argument(
        "--num-ratings",
        type=int,
        default=200,
        help="Number of ratings to generate (default: 200)"
    )
    parser.add_argument(
        "--num-comments",
        type=int,
        default=150,
        help="Number of comments to generate (default: 150)"
    )
    parser.add_argument(
        "--comment-likes-prob",
        type=float,
        default=0.3,
        help="Probability of adding likes/dislikes to comments (default: 0.3)"
    )
    parser.add_argument(
        "--no-views",
        action="store_true",
        help="Skip injecting view counts to albums (default: False)"
    )

    args = parser.parse_args()

    # Validate arguments
    if args.num_ratings < 0:
        print("❌ Error: --num-ratings must be non-negative.", file=sys.stderr)
        sys.exit(1)
    if args.num_comments < 0:
        print("❌ Error: --num-comments must be non-negative.", file=sys.stderr)
        sys.exit(1)
    if not 0 <= args.comment_likes_prob <= 1:
        print("❌ Error: --comment-likes-prob must be between 0 and 1.", file=sys.stderr)
        sys.exit(1)

    add_ratings_and_comments(
        args.num_ratings, args.num_comments, args.comment_likes_prob, not args.no_views)
