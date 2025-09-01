import sys
import os

import argparse # Import argparse
# Add the parent directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from datetime import datetime, timedelta, timezone

# Import app and db from the local main module
import importlib.util
spec = importlib.util.spec_from_file_location("main", os.path.join(project_root, "main.py"))
main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main)
app = main.app
db = main.db

from models import News, Category, User, Image, UserCoins, CoinTransaction  # Import coin models
from faker import Faker
import random
import json
import itertools

# Initialize Faker for generating fake data
fake = Faker()

def generate_markdown_content(min_paras=10, max_paras=30):
    """Generates longer fake content with random Markdown styling."""
    num_paragraphs = random.randint(min_paras, max_paras)
    paragraphs = fake.paragraphs(nb=num_paragraphs)
    
    styled_content = []
    
    for i, para in enumerate(paragraphs):
        # --- Add Headings Occasionally ---
        # More likely at the beginning or spaced out
        if i == 0 or random.random() < 0.15: 
            heading_level = random.randint(2, 4) # H2, H3, H4
            heading_text = fake.sentence(nb_words=random.randint(3, 7)).rstrip('.')
            styled_content.append(f"{'#' * heading_level} {heading_text}")
            styled_content.append("") # Add a blank line after heading

        # --- Apply Inline Styles ---
        words = para.split(' ')
        if len(words) > 5: # Only apply to longer paragraphs
            # Bold
            if random.random() < 0.25:
                start = random.randint(0, len(words) - 2)
                end = random.randint(start + 1, min(start + 5, len(words) -1))
                words[start] = f"**{words[start]}"
                words[end] = f"{words[end]}**"
                
            # Italic
            if random.random() < 0.25:
                 # Avoid nesting directly next to bold maybe
                start = random.randint(0, len(words) - 2)
                end = random.randint(start + 1, min(start + 5, len(words) -1))
                # Simple check to avoid immediate nesting like ** *word* **
                if not words[start].startswith('**'): words[start] = f"*{words[start]}"
                if not words[end].endswith('**'): words[end] = f"{words[end]}*"

        styled_para = ' '.join(words)

        # --- Add Blockquotes Occasionally ---
        if random.random() < 0.1:
            styled_para = f"> {styled_para}"
            
        styled_content.append(styled_para)
        styled_content.append("") # Add blank line between paragraphs for Markdown

    # --- Add Lists Occasionally ---
    if random.random() < 0.2:
        styled_content.append("---") # Separator
        styled_content.append("") 
        list_type = random.choice(['-', '*']) # Unordered list
        list_items = [f"{list_type} {fake.sentence(nb_words=random.randint(5, 10))}" for _ in range(random.randint(3, 6))]
        styled_content.extend(list_items)
        styled_content.append("")

    return "\n".join(styled_content) # Use single newline as we added blanks

def generate_fake_user_coins(users):
    """Generate fake user coins data for testing the coin system."""
    print("   Generating fake user coins data...")
    
    coins_added = 0
    for user in users:
        try:
            # Check if user already has coins data
            existing_coins = UserCoins.query.filter_by(user_id=user.id).first()
            if existing_coins:
                continue  # Skip if user already has coins
            
            # Generate random coin balances
            achievement_coins = random.randint(0, 200)  # 0-200 achievement coins
            topup_coins = random.randint(0, 500)  # 0-500 topup coins
            
            # Create user coins record
            user_coins = UserCoins(
                user_id=user.id,
                achievement_coins=achievement_coins,
                topup_coins=topup_coins,
                total_achievement_coins_earned=achievement_coins,
                total_topup_coins_purchased=topup_coins,
                total_coins_spent=0
            )
            db.session.add(user_coins)
            
            # Generate some fake transactions
            if achievement_coins > 0:
                # Add achievement coin transactions
                coins_earned = 0
                while coins_earned < achievement_coins:
                    transaction_amount = min(random.randint(1, 20), achievement_coins - coins_earned)
                    transaction = CoinTransaction(
                        user_id=user.id,
                        coin_type='achievement',
                        coins_change=transaction_amount,
                        source='achievement_reward',
                        description=f"Earned from achievement: {fake.sentence(nb_words=3)}",
                        context_data={'achievement_name': fake.word()}
                    )
                    db.session.add(transaction)
                    coins_earned += transaction_amount
            
            if topup_coins > 0:
                # Add topup coin transactions
                coins_purchased = 0
                while coins_purchased < topup_coins:
                    transaction_amount = min(random.randint(10, 100), topup_coins - coins_purchased)
                    transaction = CoinTransaction(
                        user_id=user.id,
                        coin_type='topup',
                        coins_change=transaction_amount,
                        source='topup_purchase',
                        description=f"Purchased {transaction_amount} coins",
                        payment_provider=random.choice(['paypal', 'stripe', 'bank_transfer']),
                        payment_id=f"PAY-{fake.uuid4()[:8].upper()}",
                        amount_paid=transaction_amount * 0.1,  # Assume 10 cents per coin
                        currency='USD'
                    )
                    db.session.add(transaction)
                    coins_purchased += transaction_amount
            
            coins_added += 1
            
        except Exception as e:
            print(f"   ❌ Error creating coins for user {user.username}: {e}")
            db.session.rollback()
            continue
    
    if coins_added > 0:
        try:
            db.session.commit()
            print(f"   ✅ Successfully added coin data for {coins_added} users")
            
            # Show coin statistics
            total_achievement = sum(uc.achievement_coins for uc in UserCoins.query.all())
            total_topup = sum(uc.topup_coins for uc in UserCoins.query.all())
            total_transactions = CoinTransaction.query.count()
            
            print(f"   📊 Coin Statistics:")
            print(f"      Total achievement coins: {total_achievement}")
            print(f"      Total topup coins: {total_topup}")
            print(f"      Total transactions: {total_transactions}")
            
        except Exception as e:
            db.session.rollback()
            print(f"   ❌ Error committing coin data: {e}")
    else:
        print("   ℹ️ No new coin data added (users may already have coins)")

def generate_seo_fields(title, content, author_name):
    """Generate SEO fields for the news article."""
    # Generate meta description (truncate content to 160 chars)
    content_words = content.replace('\n', ' ').split()
    meta_description = ' '.join(content_words[:25])[:160] + '...' if len(content_words) > 25 else ' '.join(content_words)
    
    # Generate keywords from title and content
    keywords = [word.lower() for word in title.split() if len(word) > 3]
    keywords.extend([word.lower() for word in content.split() if len(word) > 4 and random.random() < 0.1])
    meta_keywords = ', '.join(list(set(keywords))[:8])  # Limit to 8 unique keywords
    
    # Generate SEO slug
    seo_slug = title.lower().replace(' ', '-').replace(',', '').replace('.', '')[:50]
    
    # Generate Open Graph fields
    og_title = title[:60] if len(title) > 60 else title
    og_description = meta_description[:200] if len(meta_description) > 200 else meta_description
    
    # Generate Twitter Card fields
    twitter_card = random.choice(['summary', 'summary_large_image'])
    twitter_title = title[:70] if len(title) > 70 else title
    twitter_description = meta_description[:200] if len(meta_description) > 200 else meta_description
    
    # Generate schema markup
    schema_markup = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": title,
        "description": meta_description,
        "author": {
            "@type": "Person",
            "name": author_name
        },
        "datePublished": datetime.now(timezone.utc).isoformat(),
        "publisher": {
            "@type": "Organization",
            "name": "LilyOpenCMS"
        }
    }
    
    # Calculate SEO score (0-100)
    seo_score = 0
    if meta_description: seo_score += 15
    if meta_keywords: seo_score += 10
    if og_title: seo_score += 10
    if og_description: seo_score += 10
    if seo_slug: seo_score += 10
    if twitter_title: seo_score += 10
    if twitter_description: seo_score += 10
    if schema_markup: seo_score += 15
    if len(content) > 300: seo_score += 10  # Content length bonus
    
    return {
        'meta_description': meta_description,
        'meta_keywords': meta_keywords,
        'og_title': og_title,
        'og_description': og_description,
        'og_image': None,  # Will be set if image is available
        'canonical_url': None,  # Will be set based on slug
        'seo_slug': seo_slug,
        'schema_markup': json.dumps(schema_markup),
        'twitter_card': twitter_card,
        'twitter_title': twitter_title,
        'twitter_description': twitter_description,
        'twitter_image': None,  # Will be set if image is available
        'meta_author': author_name,
        'meta_language': 'id',  # Indonesian
        'meta_robots': 'index, follow',
        'structured_data_type': 'NewsArticle',
        'seo_score': seo_score,
        'last_seo_audit': datetime.now(timezone.utc)
    }

def add_fake_news_with_images(num_news, image_prob, link_prob):
    """Generates fake news, ensuring all possible type combinations are covered."""
    with app.app_context():
        print("Starting fake news generation...")

        # --- Check existing news count ---
        existing_count = News.query.count()
        if existing_count > 0:
            print(f"ℹ️ Found {existing_count} existing news articles.")
            print("   Adding new articles without deleting existing ones.")
        else:
            print("🤷 No existing news articles found.")
        print("-" * 30)

        # Fetch all necessary dependent records
        print("Fetching Users, Categories, and Images from DB...")
        users = User.query.all()
        categories = Category.query.all() 
        images = Image.query.all() # Fetch ALL images, regardless of visibility

        if not users:
            print("❌ Error: No users found in the database. Please add users first.")
            return
        if not categories:
            print(
                "❌ Error: No categories found in the database. Please add categories first."
            )
            return
        if not images: # Check if the fetched images list is empty
            print(
                "⚠️ Warning: No images found in the database. All created news articles will lack images."
            )

        print(
            f"   Found {len(users)} users, {len(categories)} categories, {len(images)} total images."
        )

        # Create a balanced image pool for even distribution
        image_pool = []
        if images:
            # Calculate how many times each image should be used
            images_needed = int(num_news * image_prob)
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
                
                print(f"   Created image pool: {len(image_pool)} image slots for {images_needed} needed images")
                print(f"   Each image will be used approximately {times_per_image} times")

        added_count = 0
        image_pool_index = 0
        print(f"Attempting to generate {num_news} fake news articles...")

        # --- Generate all possible combinations for the main boolean fields ---
        bool_fields = ['is_visible', 'is_main_news', 'is_news', 'is_premium', 'has_image', 'has_external_link']
        combos = list(itertools.product([True, False], repeat=len(bool_fields)))
        combo_articles = min(len(combos), num_news)
        used_combos = 0

        for i in range(num_news):
            try:
                # Randomly select a user and a category
                author = random.choice(users)
                category = random.choice(categories)

                # --- Determine news type for this article ---
                if i < combo_articles:
                    # Use explicit combination
                    combo = combos[i]
                    combo_dict = dict(zip(bool_fields, combo))
                    is_visible = combo_dict['is_visible']
                    is_main_news = combo_dict['is_main_news']
                    is_news = combo_dict['is_news']
                    is_premium = combo_dict['is_premium']
                    has_image = combo_dict['has_image'] and (image_pool or images)
                    has_external_link = combo_dict['has_external_link']
                else:
                    # Use random/weighted as before
                    is_visible = random.choices([True, False], weights=[95, 5], k=1)[0]
                    is_main_news = random.choices([True, False], weights=[10, 90], k=1)[0]
                    is_news = random.choices([True, False], weights=[70, 30], k=1)[0]
                    is_premium = random.choices([True, False], weights=[int(args.premium_prob * 100), int((1 - args.premium_prob) * 100)], k=1)[0]
                    has_image = (image_pool or images) and (random.random() < image_prob)
                    has_external_link = random.random() < link_prob

                # --- Assign image if needed ---
                selected_image_id = None
                selected_image = None
                if has_image and image_pool:
                    # Use the balanced image pool
                    if image_pool_index < len(image_pool):
                        selected_image = image_pool[image_pool_index]
                        selected_image_id = selected_image.id
                        image_pool_index += 1
                    else:
                        # If we've used all images in the pool, start over
                        image_pool_index = 0
                        selected_image = image_pool[image_pool_index]
                        selected_image_id = selected_image.id
                        image_pool_index += 1
                        print(f"   ⚠️ Reusing image pool (cycle {image_pool_index // len(image_pool) + 1})")
                elif has_image and not image_pool:
                    # Fallback to random selection if no image pool
                    selected_image = random.choice(images)
                    selected_image_id = selected_image.id

                # --- Assign external link if needed ---
                external_source = fake.url() if has_external_link else None

                # --- Generate other fake data ---
                tags = fake.words(nb=random.randint(1, 5), unique=True)  # 1 to 5 tags
                tags_str = ", ".join(tags)
                news_title = fake.sentence(nb_words=random.randint(5, 10))
                # Use the new function to generate richer content
                news_content_str = generate_markdown_content()
                
                # --- Generate coin system data for premium content ---
                prize = 0
                prize_coin_type = 'any'
                if is_premium:
                    # Configurable chance of having a prize for premium content
                    if random.random() < args.premium_prize_prob:
                        # Prize between 5-50 coins
                        prize = random.randint(5, 50)
                        # Random coin type preference
                        prize_coin_type = random.choice(['any', 'achievement', 'topup'])
                    else:
                        # Premium content without prize (premium users can access for free)
                        prize = 0
                        prize_coin_type = 'any' 

                # Generate SEO fields
                seo_fields = generate_seo_fields(news_title, news_content_str, author.username)
                
                # Update image URLs if image is selected
                if selected_image:
                    image_url = f"/static/uploads/{selected_image.filename}"
                    seo_fields['og_image'] = image_url
                    seo_fields['twitter_image'] = image_url
                
                # Set canonical URL
                seo_fields['canonical_url'] = f"/news/{i+1}/{seo_fields['seo_slug']}"

                # Create the News instance
                news = News(
                    title=news_title,
                    content=news_content_str,
                    tagar=tags_str,
                    # Use timezone-aware datetime, spread out publication dates
                    date=datetime.now(timezone.utc) - timedelta(hours=i * 3),
                    category_id=category.id,
                    user_id=author.id,  # The user who "created" the record
                    writer=author.username,  # The displayed writer name
                    image_id=selected_image_id, # Assign the selected image_id (can be None)
                    is_visible=is_visible,
                    is_main_news=is_main_news,
                    is_news=is_news,
                    is_premium=is_premium,
                    prize=prize,  # Coin prize for premium content
                    prize_coin_type=prize_coin_type,  # Type of coins required
                    read_count=random.randint(0, 1500),  # Add some fake read counts
                    external_source=external_source,  # Random external link or None
                    is_archived=False,  # Explicitly set as not archived
                    # SEO Fields
                    meta_description=seo_fields['meta_description'],
                    meta_keywords=seo_fields['meta_keywords'],
                    og_title=seo_fields['og_title'],
                    og_description=seo_fields['og_description'],
                    og_image=seo_fields['og_image'],
                    canonical_url=seo_fields['canonical_url'],
                    seo_slug=seo_fields['seo_slug'],
                    schema_markup=seo_fields['schema_markup'],
                    twitter_card=seo_fields['twitter_card'],
                    twitter_title=seo_fields['twitter_title'],
                    twitter_description=seo_fields['twitter_description'],
                    twitter_image=seo_fields['twitter_image'],
                    meta_author=seo_fields['meta_author'],
                    meta_language=seo_fields['meta_language'],
                    meta_robots=seo_fields['meta_robots'],
                    structured_data_type=seo_fields['structured_data_type'],
                    seo_score=seo_fields['seo_score'],
                    last_seo_audit=seo_fields['last_seo_audit']
                )

                db.session.add(news)
                added_count += 1
                # Optional: Print progress for large numbers
                if (i + 1) % 50 == 0 or (i + 1) == num_news: # Print progress less often, but always at the end
                    print(f"   Generated {i + 1}/{num_news} news articles...")

            except Exception as e:
                print(f"❌ Error creating news article #{i+1}: {e.__class__.__name__} - {e}")
                db.session.rollback() # Rollback this specific add attempt
                # db.session.rollback() # Rollback this specific add attempt
                # For seeding, often better to just skip and report errors at the end

        # Commit all the valid changes to the database
        if added_count > 0:
            try:
                db.session.commit()
                print("-" * 30)
                print(
                    f"✅ Successfully added {added_count} fake news articles to the database."
                )
                if added_count < num_news:
                    print(
                        f"⚠️ Skipped {num_news - added_count} due to errors during generation."
                    )
                
                # Show image distribution statistics
                if image_pool:
                    print(f"📊 Image Distribution:")
                    print(f"   Total images available: {len(images)}")
                    print(f"   Images used in pool: {len(image_pool)}")
                    print(f"   Average usage per image: {len(image_pool) / len(images):.1f} times")
                    if image_pool_index > len(image_pool):
                        cycles = image_pool_index // len(image_pool)
                        print(f"   Pool reused {cycles} times for complete distribution")
                
                print("-" * 30)
                
                # Show premium content and coin statistics
                total_news = News.query.count()
                premium_news = News.query.filter_by(is_premium=True).count()
                premium_with_prize = News.query.filter(News.is_premium == True, News.prize > 0).count()
                premium_free = News.query.filter(News.is_premium == True, News.prize == 0).count()
                
                print(f"📊 Premium Content Statistics:")
                print(f"   Total news articles: {total_news}")
                print(f"   Premium content: {premium_news} ({premium_news/total_news*100:.1f}%)")
                print(f"   Premium with coin cost: {premium_with_prize}")
                print(f"   Premium (free for premium users): {premium_free}")
                
                # Coin type distribution
                if premium_with_prize > 0:
                    any_coins = News.query.filter(News.is_premium == True, News.prize > 0, News.prize_coin_type == 'any').count()
                    achievement_coins = News.query.filter(News.is_premium == True, News.prize > 0, News.prize_coin_type == 'achievement').count()
                    topup_coins = News.query.filter(News.is_premium == True, News.prize > 0, News.prize_coin_type == 'topup').count()
                    
                    print(f"   Coin type distribution:")
                    print(f"      Any coin type: {any_coins}")
                    print(f"      Achievement coins only: {achievement_coins}")
                    print(f"      Topup coins only: {topup_coins}")
                
                # Generate fake user coins data for testing
                print("Generating fake user coins data...")
                generate_fake_user_coins(users)
                
            except Exception as e:
                db.session.rollback()
                print("-" * 30)
                print(f"❌ Fatal Error: Could not commit news articles to database: {e.__class__.__name__} - {e}")
                print(f"   {added_count} prepared articles were rolled back.")
                print("-" * 30)
        elif added_count == 0: # Only show if nothing was added at all
            print("-" * 30)
            print("🤷 No fake news articles were added (check for errors above).")
            print("-" * 30)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate fake news articles for the database.")
    parser.add_argument(
        "--num-news",
        type=int,
        default=100,
        help="Number of fake news articles to generate (default: 100)"
    )
    parser.add_argument(
        "--image-prob",
        type=float,
        default=0.87,
        help="Probability (0-1) of a news article having an image (default: 0.87)"
    )
    parser.add_argument(
        "--link-prob",
        type=float,
        default=0.65,
        help="Probability (0-1) of a news article having an external link (default: 0.65)"
    )
    parser.add_argument(
        "--premium-prob",
        type=float,
        default=0.2,
        help="Probability (0-1) of a news article being premium (default: 0.2)"
    )
    parser.add_argument(
        "--premium-prize-prob",
        type=float,
        default=0.7,
        help="Probability (0-1) of premium content having a coin cost (default: 0.7)"
    )

    args = parser.parse_args()

    # Validate probabilities
    if not 0 <= args.image_prob <= 1:
        print("❌ Error: --image-prob must be between 0 and 1.", file=sys.stderr)
        sys.exit(1)
    if not 0 <= args.link_prob <= 1:
        print("❌ Error: --link-prob must be between 0 and 1.", file=sys.stderr)
        sys.exit(1)

    # Validate probabilities
    if not 0 <= args.premium_prob <= 1:
        print("❌ Error: --premium-prob must be between 0 and 1.", file=sys.stderr)
        sys.exit(1)
    if not 0 <= args.premium_prize_prob <= 1:
        print("❌ Error: --premium-prize-prob must be between 0 and 1.", file=sys.stderr)
        sys.exit(1)

    # Call the main function with parsed arguments
    add_fake_news_with_images(args.num_news, args.image_prob, args.link_prob)
