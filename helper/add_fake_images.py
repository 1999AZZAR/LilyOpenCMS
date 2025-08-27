import sys
import os
from datetime import datetime, timedelta, timezone
import random
import requests
import time
import subprocess
import signal
import atexit
import mimetypes
import re
from io import BytesIO

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

from models import User

# Try to import PIL for image generation
try:
    from PIL import Image as PILImage, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from faker import Faker

# Initialize Faker
fake = Faker()

# --- Configuration ---
BASE_URL = "http://127.0.0.1:5000"
LOGIN_URL = f"{BASE_URL}/login"
API_URL = f"{BASE_URL}/api/images"

# Credentials
LOGIN_USERNAME = os.environ.get("FLASK_LOGIN_USER", "suadmin")
LOGIN_PASSWORD = os.environ.get("FLASK_LOGIN_PASS", "suladang")

# Relative path to the uploads folder from the project root
SOURCE_IMAGES_FOLDER_RELATIVE = "images_to_upload"
# Define allowed image extensions (lowercase)
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

# Colors for placeholder generation - Extended vibrant palette
PLACEHOLDER_COLORS = [
    # Vibrant Reds & Pinks
    '#FF6B6B', '#FF4757', '#FF3838', '#FF1744', '#F50057', '#E91E63', '#C2185B', '#AD1457',
    '#FF4081', '#F50057', '#E91E63', '#C2185B', '#FF1744', '#D500F9', '#AA00FF', '#6200EA',
    
    # Vibrant Blues & Cyans
    '#4ECDC4', '#45B7D1', '#85C1E9', '#2196F3', '#03A9F4', '#00BCD4', '#00ACC1', '#0097A7',
    '#00BCD4', '#26C6DA', '#00BCD4', '#00ACC1', '#0097A7', '#00838F', '#006064', '#0277BD',
    
    # Vibrant Greens & Teals
    '#96CEB4', '#82E0AA', '#4CAF50', '#66BB6A', '#81C784', '#A5D6A7', '#C8E6C9', '#E8F5E8',
    '#00BCD4', '#26C6DA', '#4DD0E1', '#80DEEA', '#B2EBF2', '#E0F7FA', '#00ACC1', '#0097A7',
    
    # Vibrant Yellows & Oranges
    '#FFEAA7', '#F7DC6F', '#F4D03F', '#F39C12', '#E67E22', '#D35400', '#E67E22', '#D35400',
    '#FF9800', '#FFB74D', '#FFCC02', '#FFEB3B', '#FFF176', '#FFF59D', '#FFF9C4', '#FFFDE7',
    
    # Vibrant Purples & Magentas
    '#DDA0DD', '#BB8FCE', '#9C27B0', '#BA68C8', '#CE93D8', '#E1BEE7', '#F3E5F5', '#FCE4EC',
    '#E91E63', '#F06292', '#F8BBD9', '#FCE4EC', '#F3E5F5', '#E1BEE7', '#CE93D8', '#BA68C8',
    
    # Vibrant Grays & Neutrals
    '#607D8B', '#78909C', '#90A4AE', '#B0BEC5', '#CFD8DC', '#ECEFF1', '#F5F5F5', '#FAFAFA',
    '#424242', '#616161', '#757575', '#9E9E9E', '#BDBDBD', '#E0E0E0', '#EEEEEE', '#F5F5F5',
    
    # Additional Vibrant Colors
    '#FF5722', '#FF7043', '#FF8A65', '#FFAB91', '#FFCCBC', '#FBE9E7', '#FF1744', '#FF4081',
    '#3F51B5', '#5C6BC0', '#7986CB', '#9FA8DA', '#C5CAE9', '#E8EAF6', '#303F9F', '#3949AB',
    '#009688', '#26A69A', '#4DB6AC', '#80CBC4', '#B2DFDB', '#E0F2F1', '#00695C', '#00796B',
    '#8BC34A', '#9CCC65', '#AED581', '#C5E1A5', '#DCEDC8', '#F1F8E9', '#689F38', '#7CB342',
    '#FFC107', '#FFD54F', '#FFE082', '#FFECB3', '#FFF8E1', '#FFFDE7', '#FF8F00', '#FFA000',
    '#FF5722', '#FF7043', '#FF8A65', '#FFAB91', '#FFCCBC', '#FBE9E7', '#D84315', '#E64A19',
    '#6A4C93', '#8E6C88', '#B39DDB', '#D1C4E9', '#EDE7F6', '#F3E5F5', '#512DA8', '#673AB7',
    '#00BCD4', '#26C6DA', '#4DD0E1', '#80DEEA', '#B2EBF2', '#E0F7FA', '#0097A7', '#00838F',
    '#4CAF50', '#66BB6A', '#81C784', '#A5D6A7', '#C8E6C9', '#E8F5E8', '#388E3C', '#43A047',
    '#FF9800', '#FFB74D', '#FFCC02', '#FFEB3B', '#FFF176', '#FFF59D', '#F57C00', '#FB8C00',
    '#9C27B0', '#BA68C8', '#CE93D8', '#E1BEE7', '#F3E5F5', '#FCE4EC', '#7B1FA2', '#8E24AA',
    '#607D8B', '#78909C', '#90A4AE', '#B0BEC5', '#CFD8DC', '#ECEFF1', '#455A64', '#546E7A'
]

# Global variable to track server process
server_process = None

def cleanup_server():
    """Cleanup function to stop the server process."""
    global server_process
    if server_process:
        try:
            server_process.terminate()
            server_process.wait(timeout=5)
            print("🛑 Stopped Flask server")
        except subprocess.TimeoutExpired:
            server_process.kill()
            print("🛑 Force killed Flask server")
        except Exception as e:
            print(f"⚠️ Error stopping server: {e}")

# Register cleanup function
atexit.register(cleanup_server)

def start_flask_server():
    """Start the Flask server if it's not already running."""
    global server_process
    
    # First check if server is already running
    try:
        response = requests.get(f"{BASE_URL}/", timeout=2)
        if response.status_code == 200:
            print("✅ Flask server is already running")
            return True
    except requests.exceptions.RequestException:
        pass
    
    print("🚀 Starting Flask server...")
    try:
        # Start the server in a subprocess
        server_process = subprocess.Popen(
            [sys.executable, "main.py"],
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid if hasattr(os, 'setsid') else None
        )
        
        # Wait for server to start
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(f"{BASE_URL}/", timeout=2)
                if response.status_code == 200:
                    print("✅ Flask server started successfully")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(1)
            if i % 5 == 0:
                print(f"⏳ Waiting for server to start... ({i+1}/{max_retries})")
        
        print("❌ Failed to start Flask server")
        return False
        
    except Exception as e:
        print(f"❌ Error starting Flask server: {e}")
        return False

def create_placeholder_image(width=800, height=600, text="Placeholder", color=None):
    """Create a placeholder image programmatically with enhanced visual effects."""
    if not PIL_AVAILABLE:
        return None
        
    if color is None:
        color = random.choice(PLACEHOLDER_COLORS)
    
    # Create image with enhanced background
    img = PILImage.new('RGB', (width, height), color)
    draw = ImageDraw.Draw(img)
    
    # Add gradient effect or pattern
    effect_type = random.choice(['gradient', 'solid', 'pattern'])
    
    if effect_type == 'gradient':
        # Create a simple gradient effect
        for y in range(height):
            # Create a subtle gradient from top to bottom
            factor = y / height
            r, g, b = int(int(color[1:3], 16) * (1 - factor * 0.3)), int(int(color[3:5], 16) * (1 - factor * 0.3)), int(int(color[5:7], 16) * (1 - factor * 0.3))
            r, g, b = max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))
            for x in range(width):
                img.putpixel((x, y), (r, g, b))
    
    elif effect_type == 'pattern':
        # Add a subtle pattern overlay
        for y in range(0, height, 20):
            for x in range(0, width, 20):
                if (x + y) % 40 == 0:
                    # Create a subtle pattern
                    r, g, b = int(int(color[1:3], 16)), int(int(color[3:5], 16)), int(int(color[5:7], 16))
                    r, g, b = min(255, r + 20), min(255, g + 20), min(255, b + 20)
                    draw.rectangle([x, y, x + 10, y + 10], fill=(r, g, b))
    
    # Try to use a better font, fallback to default
    try:
        font_size = min(36, width // 20)  # Responsive font size
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except (OSError, IOError):
        try:
            font = ImageFont.load_default()
        except:
            font = None
    
    # Add text to center with enhanced styling
    if font:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Add text shadow for better readability
        shadow_offset = 2
        draw.text((x + shadow_offset, y + shadow_offset), text, fill='#000000', font=font)
        draw.text((x, y), text, fill='white', font=font)
    
    return img

def count_images_in_directory(directory_path):
    """Count the number of image files in a directory."""
    if not os.path.exists(directory_path):
        return 0
    
    image_count = 0
    for filename in os.listdir(directory_path):
        filepath = os.path.join(directory_path, filename)
        if os.path.isfile(filepath):
            _, ext = os.path.splitext(filename)
            if ext.lower() in ALLOWED_EXTENSIONS:
                image_count += 1
    
    return image_count

def generate_placeholder_images(count=150):
    """Generate placeholder images in the source directory following the topic list."""
    source_dir_absolute = os.path.join(project_root, SOURCE_IMAGES_FOLDER_RELATIVE)
    
    # Create source directory if it doesn't exist
    os.makedirs(source_dir_absolute, exist_ok=True)
    
    print(f"Generating {count} placeholder images in {source_dir_absolute}...")
    
    image_topics = [
        # Business & Finance (25 topics)
        "Business", "Finance", "Marketing", "Sales", "Management", "Startup", 
        "Entrepreneurship", "Economy", "Investment", "Stock Market", 
        "Cryptocurrency", "E-commerce", "Real Estate", "Logistics", 
        "Human Resources", "Advertising", "Networking", "Consulting",
        "Strategy", "Analytics", "Branding", "Customer Service", "Operations",
        "Supply Chain", "Retail",

        # Technology & Engineering (25 topics)
        "Technology", "Software", "AI", "Machine Learning", "Data Science", 
        "Web Development", "Cybersecurity", "Blockchain", "Robotics", "Gadgets", 
        "Gaming", "Innovation", "Digital", "Quantum Computing", "Engineering",
        "Cloud Computing", "Mobile Apps", "IoT", "Virtual Reality", "Augmented Reality",
        "Automation", "API Development", "DevOps", "Database", "Networking",

        # Science & Nature (20 topics)
        "Science", "Nature", "Environment", "Sustainability", "Space Exploration", 
        "Astronomy", "Physics", "Chemistry", "Biology", "Geology", "Ecology", 
        "Weather", "Climate Change", "Conservation", "Wildlife", "Oceanography",
        "Meteorology", "Botany", "Zoology", "Microbiology",

        # Health & Wellness (20 topics)
        "Health", "Fitness", "Wellness", "Mental Health", "Nutrition", "Medicine", 
        "Psychology", "Yoga", "Meditation", "Skincare", "Mindfulness", 
        "Personal Development", "Dental Care", "Physical Therapy", "Alternative Medicine",
        "Aromatherapy", "Massage", "Acupuncture", "Herbal Medicine", "Holistic Health",

        # Arts & Culture (25 topics)
        "Art", "Culture", "Design", "Photography", "Music", "Movies", "Books", 
        "Fashion", "Theater", "Dance", "Animation", "Comics", "Poetry", 
        "Sculpture", "Pop Culture", "Streaming", "Podcasts", "Digital Art",
        "Street Art", "Graffiti", "Calligraphy", "Typography", "Illustration",
        "Film Making", "Documentary",

        # Home, Food & Hobbies (20 topics)
        "Home", "Garden", "DIY", "Crafting", "Cooking", "Baking", "Food", 
        "Interior Design", "Architecture", "Organization", "Minimalism", "Pets",
        "Landscaping", "Home Improvement", "Furniture", "Kitchen Design",
        "Wine Making", "Beer Brewing", "Cheese Making", "Fermentation",

        # Society & Humanities (15 topics)
        "Society", "Politics", "News", "Education", "History", "Law", "Philosophy", 
        "Community", "Activism", "World Events", "Geography", "Archaeology",
        "Mythology", "Languages", "Anthropology"
    ]
    
    # Calculate how many times to cycle through the topics to reach 115 images
    topics_count = len(image_topics)
    cycles_needed = count // topics_count
    remaining_images = count % topics_count
    
    print(f"📊 Topic distribution: {cycles_needed} full cycles + {remaining_images} additional images")
    print(f"📊 Total topics available: {topics_count}")
    print(f"🎯 Target images: {count}")
    
    if topics_count >= count:
        print(f"✅ Perfect! We have enough topics ({topics_count}) for {count} images")
    else:
        print(f"⚠️ Note: We have {topics_count} topics for {count} images (will cycle through topics)")
    
    image_counter = 0
    
    # Generate images following the topic list order
    for cycle in range(cycles_needed):
        for topic_index, topic in enumerate(image_topics):
            if image_counter >= count:
                break
                
            if PIL_AVAILABLE:
                # Generate different sized images with more variety
                sizes = [
                    (800, 600), (1200, 800), (600, 400), (1000, 600),
                    (1024, 768), (1280, 720), (1920, 1080), (1366, 768),
                    (1440, 900), (1600, 900), (1680, 1050), (1920, 1200),
                    (2560, 1440), (3840, 2160), (720, 480), (640, 480),
                    (800, 480), (960, 540), (1280, 960), (1600, 1200)
                ]
                width, height = random.choice(sizes)
                
                color = random.choice(PLACEHOLDER_COLORS)
                
                # Create image with topic name only (no numbering)
                img = create_placeholder_image(width, height, f"{topic}", color)
                
                if img:
                    filename = f"{topic.lower().replace(' ', '_')}.jpg"
                    filepath = os.path.join(source_dir_absolute, filename)
                    img.save(filepath, 'JPEG', quality=85)
                    print(f"  ✅ Created {filename} (Topic: {topic})")
                else:
                    print(f"  ❌ Failed to create image {image_counter+1}")
            else:
                # Create a simple text file as placeholder when PIL is not available
                filename = f"{topic.lower().replace(' ', '_')}.txt"
                filepath = os.path.join(source_dir_absolute, filename)
                with open(filepath, 'w') as f:
                    f.write(f"{topic} image - Install PIL/Pillow to generate actual images")
                print(f"  📝 Created text placeholder {filename} (Topic: {topic})")
            
            image_counter += 1
    
    # Generate remaining images if needed
    for topic_index in range(remaining_images):
        if image_counter >= count:
            break
            
        topic = image_topics[topic_index]
        
        if PIL_AVAILABLE:
            # Generate different sized images with more variety
            sizes = [
                (800, 600), (1200, 800), (600, 400), (1000, 600),
                (1024, 768), (1280, 720), (1920, 1080), (1366, 768),
                (1440, 900), (1600, 900), (1680, 1050), (1920, 1200),
                (2560, 1440), (3840, 2160), (720, 480), (640, 480),
                (800, 480), (960, 540), (1280, 960), (1600, 1200)
            ]
            width, height = random.choice(sizes)
            
            color = random.choice(PLACEHOLDER_COLORS)
            
            # Create image with topic name only (no numbering)
            img = create_placeholder_image(width, height, f"{topic}", color)
            
            if img:
                filename = f"{topic.lower().replace(' ', '_')}.jpg"
                filepath = os.path.join(source_dir_absolute, filename)
                img.save(filepath, 'JPEG', quality=85)
                print(f"  ✅ Created {filename} (Topic: {topic})")
            else:
                print(f"  ❌ Failed to create image {image_counter+1}")
        else:
            # Create a simple text file as placeholder when PIL is not available
            filename = f"{topic.lower().replace(' ', '_')}.txt"
            filepath = os.path.join(source_dir_absolute, filename)
            with open(filepath, 'w') as f:
                f.write(f"{topic} image - Install PIL/Pillow to generate actual images")
            print(f"  📝 Created text placeholder {filename} (Topic: {topic})")
        
        image_counter += 1
    
    print(f"🎯 Generated {image_counter} images following the topic list")

def login_and_get_session():
    """Logs into the Flask app and returns a session object with cookies."""
    session = requests.Session()
    
    # Retry logic for login
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"Attempting login as {LOGIN_USERNAME} (attempt {attempt + 1}/{max_retries})...")
            
            # Fetch login page to get CSRF token
            login_page_resp = session.get(LOGIN_URL, timeout=10)
            login_page_resp.raise_for_status()
            
            # Try multiple ways to get CSRF token
            csrf_token = None
            
            # Method 1: Look for meta tag
            meta_match = re.search(r'<meta[^>]+name=["\']csrf-token["\'][^>]+content=["\']([^"\']+)["\']', login_page_resp.text, re.IGNORECASE)
            if meta_match:
                csrf_token = meta_match.group(1)
                print(f"   Found CSRF token in meta tag: {csrf_token[:10]}...")
            
            # Method 2: Look for input field
            if not csrf_token:
                input_match = re.search(r'<input[^>]+name=["\']csrf_token["\'][^>]+value=["\']([^"\']+)["\']', login_page_resp.text, re.IGNORECASE)
                if input_match:
                    csrf_token = input_match.group(1)
                    print(f"   Found CSRF token in input field: {csrf_token[:10]}...")
            
            # Method 3: Look for any csrf token in the page
            if not csrf_token:
                csrf_match = re.search(r'csrf_token["\']?\s*:\s*["\']([^"\']+)["\']', login_page_resp.text, re.IGNORECASE)
                if csrf_match:
                    csrf_token = csrf_match.group(1)
                    print(f"   Found CSRF token in script: {csrf_token[:10]}...")

            login_data = {
                "username": LOGIN_USERNAME,
                "password": LOGIN_PASSWORD,
                "remember": "y"
            }
            if csrf_token:
                login_data["csrf_token"] = csrf_token

            login_resp = session.post(LOGIN_URL, data=login_data, allow_redirects=True, timeout=10)
            login_resp.raise_for_status()

            # Check if login was successful
            if login_resp.url == LOGIN_URL or "Invalid username or password" in login_resp.text:
                print("❌ Login failed. Please check credentials and CSRF handling.")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return None

            print("✅ Login successful.")
            return session
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Login attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return None
    
    return None

def upload_image_via_api(session, filepath, filename, description):
    """Upload a single image via the API with retry logic."""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            # Prepare form data
            form_data = {
                "name": os.path.splitext(filename)[0],
                "description": description,
            }

            # Prepare file data
            mime_type, _ = mimetypes.guess_type(filepath)
            if not mime_type:
                mime_type = 'application/octet-stream'

            with open(filepath, 'rb') as f:
                files_payload = {
                    'file': (filename, f, mime_type)
                }
                
                print(f"   ⬆️ Uploading {filename} via API (attempt {attempt + 1}/{max_retries})...")
                response = session.post(API_URL, data=form_data, files=files_payload, timeout=30)
                
                if response.status_code in [200, 201]:
                    print(f"   ✅ Successfully uploaded {filename}")
                    return True
                else:
                    error_msg = f"Status {response.status_code}"
                    try: 
                        error_data = response.json()
                        error_msg += f": {error_data.get('error', response.text)}"
                    except: 
                        error_msg += f": {response.text}"
                    print(f"   ❌ API upload failed for {filename}. {error_msg}")
                    
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    return False
                    
        except requests.exceptions.RequestException as e:
            print(f"   ❌ API request error for {filename}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return False
        except Exception as e:
            print(f"   ❌ Unexpected error for {filename}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return False
    
    return False

def add_images_via_api():
    """Add images via the API to ensure proper handling by the image parser."""
    print("🖼️ LilyOpenCMS Image Generator & API Uploader")
    print("=" * 50)
    
    # Start Flask server if needed
    if not start_flask_server():
        print("❌ Cannot proceed without Flask server")
        return
    
    # Get the absolute path to source directory
    source_dir_absolute = os.path.join(project_root, SOURCE_IMAGES_FOLDER_RELATIVE)
    
    # Create directory if it doesn't exist
    if not os.path.isdir(source_dir_absolute):
        print("Creating directory...")
        os.makedirs(source_dir_absolute, exist_ok=True)
    
    print(f"📁 Source images directory: {source_dir_absolute}")
    
    # Count existing images
    existing_image_count = count_images_in_directory(source_dir_absolute)
    print(f"📊 Found {existing_image_count} existing images")
    
    # Check if we need to generate images based on the new logic
    target_total = 150
    minimum_threshold = 25
    
    if existing_image_count >= minimum_threshold:
        print(f"✅ Found {existing_image_count} images (>= {minimum_threshold}), skipping image generation.")
        images_to_generate = 0
    else:
        images_to_generate = target_total - existing_image_count
        print(f"📊 Found {existing_image_count} images (< {minimum_threshold})")
        print(f"🎯 Will generate {images_to_generate} images to reach {target_total} total")
        
        # Generate the needed images
        print("🔄 Generating images following the topic list...")
        generate_placeholder_images(images_to_generate)
    
    # Login to get session
    session = login_and_get_session()
    if not session:
        print("❌ Could not login. Skipping image upload.")
        return

    # Scan source directory for images to upload
    print(f"\n🔍 Scanning for image files to upload in: {source_dir_absolute}")
    added_count = 0
    skipped_count = 0
    error_count = 0

    files_in_dir = os.listdir(source_dir_absolute)
    print(f"   Found {len(files_in_dir)} total items.")

    # Sort files to process them in a consistent order
    files_in_dir.sort()

    for filename in files_in_dir:
        source_filepath = os.path.join(source_dir_absolute, filename)

        # Check if it's a file and has an allowed extension
        _, ext = os.path.splitext(filename)
        if (
            not os.path.isfile(source_filepath)
            or ext.lower() not in ALLOWED_EXTENSIONS
        ):
            skipped_count += 1
            continue

        # Generate a fake description
        description = fake.sentence(nb_words=random.randint(5, 15))

        # Upload via API
        if upload_image_via_api(session, source_filepath, filename, description):
            added_count += 1
        else:
            error_count += 1

    # Final summary
    print("-" * 50)
    if images_to_generate > 0:
        print(f"🎨 Generated {images_to_generate} new images")
    else:
        print("🎨 No new images were generated (threshold met)")
    
    if added_count > 0:
        print(f"✅ Successfully uploaded {added_count} images via API.")
    else:
        print("🤷 No new images were uploaded via API.")

    if skipped_count > 0:
        print(f"ℹ️ Skipped {skipped_count} files (not images).")
    if error_count > 0:
        print(f"⚠️ Encountered errors uploading {error_count} files.")
    
    # Final count after everything
    final_image_count = count_images_in_directory(source_dir_absolute)
    print(f"📊 Final image count in directory: {final_image_count}")
    print("-" * 50)

if __name__ == "__main__":
    try:
        add_images_via_api()
    finally:
        cleanup_server()
