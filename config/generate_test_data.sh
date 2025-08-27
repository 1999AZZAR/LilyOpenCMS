#!/bin/bash

# Get the directory where this script is located and navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "====================================="
echo "=== LilyOpenCMS Test Data Generator ==="
echo "====================================="
echo "Project root: $PROJECT_ROOT"

# --- Function to prompt user before executing a step ---
prompt_step() {
    local description="$1"
    local command="$2"

    echo ""
    echo "----------------------------------------"
    echo "STEP: $description"
    echo "----------------------------------------"
    # Prompt the user for an action
    read -p "Choose an action -> [R]un, [S]kip, [E]xit: " -n 1 -r choice
    echo # Move to a new line after input

    case "$choice" in
        r|R)
            echo "-> Running..."
            # Use eval to correctly handle commands with quotes and arguments
            eval "$command"
            if [ $? -ne 0 ]; then
                echo ""
                echo "❌ ERROR: Step '$description' failed."
                read -p "An error occurred. Press [Enter] to stop or [C] to continue anyway: " error_choice
                # Default to stopping unless 'c' or 'C' is pressed
                if [[ "$error_choice" != "c" && "$error_choice" != "C" ]]; then
                    echo "Stopping script due to error."
                    exit 1
                fi
            else
                echo "✅ Step completed."
            fi
            ;;
        s|S)
            echo "-> Skipping step: $description"
            ;;
        e|E)
            echo "-> Exiting script as requested."
            exit 0
            ;;
        *)
            echo "-> Invalid choice. Skipping step: $description"
            ;;
    esac
}

# --- Define complex, multi-line commands as variables for clarity ---

# Command for checking Python package dependencies
DEP_CHECK_CMD="python -c \"
import sys
try:
    import requests, faker
    from PIL import Image
    print('✅ All required packages are available')
except ImportError as e:
    print(f'❌ Missing package: {e.name}')
    print('Please install with: pip install -r helper/requirements-helper.txt')
    sys.exit(1)
\""

# Command for setting up the database schema
DB_SETUP_CMD="python -c \"
import sys
try:
    from models import db
    from main import app
    with app.app_context():
        db.create_all()
    print('✅ Database schema created/updated successfully')
except Exception as e:
    print(f'❌ Failed to create database schema: {e}')
    sys.exit(1)
\""

# --- Main script execution flow ---

prompt_step "Checking Dependencies" "$DEP_CHECK_CMD"
prompt_step "Setting up Database Schema" "$DB_SETUP_CMD"
prompt_step "Initializing Permissions" "python helper/init_permissions.py"
prompt_step "Generating Users" "python helper/generate_user.py"
prompt_step "Generating Categories" "python helper/add_chategories.py"
prompt_step "Generating Images" "python helper/add_fake_images.py"
prompt_step "Generating News Articles (2500 articles)" "python helper/add_fake_news.py --image-prob 0.99 --num-news 2500"
prompt_step "Backfilling Age Ratings (News & Albums)" "python helper/add_age_data.py"
prompt_step "Generating Albums" "python helper/add_test_albums.py"
prompt_step "Adding Videos" "python helper/add_videos.py"
prompt_step "Adding Ratings (6000) and Comments (3000)" "python helper/add_ratings_comments.py --num-ratings 6000 --num-comments 3000 --comment-likes-prob 0.37"
prompt_step "Initializing Footer Data" "python helper/init_footer_data.py"
prompt_step "Initializing Navigation Data" "python helper/add_navigation_links.py"
prompt_step "Initializing Contact Details" "python helper/add_contact_details.py"
prompt_step "Generating Test Ads" "python helper/add_test_ads.py"

# --- Final message ---
echo ""
echo "====================================="
echo "=== Test Data Generation Finished ==="
echo "====================================="
echo "✅ Script finished. Check logs above for skipped or failed steps."
echo "You can now start the application with: python main.py"
echo ""
