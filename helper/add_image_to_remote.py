import requests
import os
import sys
import re
import mimetypes  # This was missing!
from faker import Faker
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# Initialize Faker
fake = Faker()

# --- Configuration ---
# Get URL from user input instead of hardcoding
def get_base_url():
    """Ask user for the base URL"""
    print("\n" + "="*50)
    print("LilyCMS Remote Image Uploader")
    print("="*50)
    
    while True:
        url = input("\n🌐 Enter the website URL (e.g., https://lilycms.com): ").strip()
        
        # Basic URL validation
        if not url:
            print("❌ URL cannot be empty. Please try again.")
            continue
            
        if not url.startswith(('http://', 'https://')):
            print("❌ URL must start with http:// or https://. Please try again.")
            continue
            
        # Remove trailing slash if present
        url = url.rstrip('/')
        
        # Confirm URL
        confirm = input(f"✅ Confirm URL: {url} (y/n): ").strip().lower()
        if confirm in ['y', 'yes']:
            return url
        else:
            print("🔄 Please enter the URL again.")

# Get credentials from user input
def get_credentials():
    """Ask user for login credentials"""
    print("\n🔐 Login Credentials")
    print("-" * 30)
    
    username = input("👤 Username: ").strip()
    if not username:
        print("❌ Username cannot be empty.")
        return None, None
        
    password = input("🔒 Password: ").strip()
    if not password:
        print("❌ Password cannot be empty.")
        return None, None
        
    return username, password

# Path to images - updated to use images_to_upload
SOURCE_IMAGES_FOLDER = "./images_to_upload"

# Browser-like headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
}

def create_session():
    """Create a requests session with proper headers and settings"""
    session = requests.Session()
    session.headers.update(HEADERS)
    session.verify = False  # Disable SSL verification
    session.allow_redirects = True
    return session

def get_csrf_token(session, login_page):
    """Extract CSRF token from login page"""
    # Try multiple patterns to find CSRF token
    patterns = [
        r'name="csrf_token"\s+value="([^"]+)"',
        r'csrf_token["\']?\s*:\s*["\']([^"\']+)["\']',
        r'<meta[^>]+name=["\']csrf-token["\'][^>]+content=["\']([^"\']+)["\']'
    ]

    for pattern in patterns:
        match = re.search(pattern, login_page)
        if match:
            return match.group(1)
    return None

def login(session, base_url, username, password):
    """Login to the website and return authenticated session"""
    login_url = f"{base_url}/login"
    
    try:
        # First GET request to get cookies and CSRF token
        print("🔍 Fetching login page...")
        response = session.get(login_url)
        response.raise_for_status()

        # Get CSRF token
        csrf_token = get_csrf_token(session, response.text)
        if not csrf_token:
            print("⚠️ Warning: Could not find CSRF token, trying without it")

        # Prepare login data
        login_data = {
            'username': username,
            'password': password,
            'remember': 'y'
        }
        if csrf_token:
            login_data['csrf_token'] = csrf_token

        # POST login request
        print("🔐 Attempting login...")
        login_response = session.post(
            login_url,
            data=login_data,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': login_url,
                'Origin': base_url
            }
        )
        login_response.raise_for_status()

        # Check if login was successful
        if 'login' in login_response.url.lower():
            print("❌ Login failed - check credentials or CSRF token")
            return None

        print("✅ Login successful!")
        return session

    except requests.exceptions.RequestException as e:
        print(f"❌ Login failed: {str(e)}")
        return None

def upload_image(session, image_path, base_url):
    """Upload a single image"""
    api_url = f"{base_url}/api/images"
    
    try:
        filename = os.path.basename(image_path)
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_type = 'application/octet-stream'

        with open(image_path, 'rb') as f:
            files = {'file': (filename, f, mime_type)}
            data = {
                'name': os.path.splitext(filename)[0],
                'description': fake.sentence()
            }

            print(f"⬆️ Uploading {filename}...")
            response = session.post(
                api_url,
                files=files,
                data=data,
                headers={
                    'Referer': f"{base_url}/upload",
                    'Origin': base_url
                }
            )

            if response.status_code in [200, 201]:
                print(f"✅ Successfully uploaded {filename}")
                return True
            else:
                print(f"❌ Upload failed for {filename}: {response.status_code} - {response.text}")
                return False

    except Exception as e:
        print(f"❌ Error uploading {image_path}: {str(e)}")
        return False

def count_images_in_directory(directory_path):
    """Count the number of image files in a directory."""
    if not os.path.exists(directory_path):
        return 0
    
    image_count = 0
    allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
    
    for filename in os.listdir(directory_path):
        filepath = os.path.join(directory_path, filename)
        if os.path.isfile(filepath):
            _, ext = os.path.splitext(filename)
            if ext.lower() in allowed_extensions:
                image_count += 1
    
    return image_count

def main():
    """Main function to handle image uploads"""
    print("\n" + "="*50)
    print("LilyCMS Remote Image Uploader")
    print("="*50)

    # Get base URL from user
    base_url = get_base_url()
    if not base_url:
        print("❌ Invalid URL provided. Exiting.")
        return

    # Get credentials from user
    username, password = get_credentials()
    if not username or not password:
        print("❌ Invalid credentials provided. Exiting.")
        return

    # Create session and login
    session = create_session()
    if not login(session, base_url, username, password):
        print("❌ Cannot proceed without successful login")
        return

    # Check images directory
    if not os.path.exists(SOURCE_IMAGES_FOLDER):
        print(f"❌ Error: Directory '{SOURCE_IMAGES_FOLDER}' not found")
        print(f"💡 Please place your images in the '{SOURCE_IMAGES_FOLDER}' folder")
        return

    # Count images in directory
    image_count = count_images_in_directory(SOURCE_IMAGES_FOLDER)
    print(f"\n📁 Found {image_count} images in '{SOURCE_IMAGES_FOLDER}'")

    if image_count == 0:
        print(f"❌ No images found in '{SOURCE_IMAGES_FOLDER}'")
        print(f"💡 Please add some images to the '{SOURCE_IMAGES_FOLDER}' folder")
        return

    # Get list of image files
    image_files = [
        f for f in os.listdir(SOURCE_IMAGES_FOLDER)
        if os.path.isfile(os.path.join(SOURCE_IMAGES_FOLDER, f)) and
        f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))
    ]

    print(f"\n🚀 Starting upload to: {base_url}")
    print(f"📊 Total images to upload: {len(image_files)}")

    # Upload each image
    success_count = 0
    for i, image_file in enumerate(image_files, 1):
        print(f"\n📤 [{i}/{len(image_files)}] Processing: {image_file}")
        image_path = os.path.join(SOURCE_IMAGES_FOLDER, image_file)
        if upload_image(session, image_path, base_url):
            success_count += 1

    # Final summary
    print("\n" + "="*50)
    print("📊 UPLOAD SUMMARY")
    print("="*50)
    print(f"✅ Successfully uploaded: {success_count}/{len(image_files)} images")
    print(f"❌ Failed uploads: {len(image_files) - success_count}")
    print(f"🌐 Target website: {base_url}")
    print(f"📁 Source folder: {SOURCE_IMAGES_FOLDER}")
    
    if success_count == len(image_files):
        print("\n🎉 All images uploaded successfully!")
    elif success_count > 0:
        print(f"\n⚠️ {success_count} images uploaded successfully, {len(image_files) - success_count} failed.")
    else:
        print("\n❌ No images were uploaded successfully.")

if __name__ == "__main__":
    main()
