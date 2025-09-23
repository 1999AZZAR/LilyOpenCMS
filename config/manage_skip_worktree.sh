#!/bin/bash

# Script to manage skip-worktree files for local configuration
# These files can be edited locally without conflicts during git pull

# Files that should be skip-worktree (local modifications allowed)
SKIP_WORKTREE_FILES=(
    "config/redis_config.txt"
    "robots.txt"
    "sitemap.xml"
    "sitemap.xml.gz"
    "config/smtp_config.txt"
    "static/pic/favicon.ico"
    "static/pic/favicon.png"
    "static/pic/logo.png"
    "static/pic/logo_footer.png"
    "static/pic/placeholder.png"
)

case "$1" in
    "enable")
        echo "Enabling skip-worktree for local configuration files..."
        for file in "${SKIP_WORKTREE_FILES[@]}"; do
            if [ -f "$file" ]; then
                git update-index --skip-worktree "$file"
                echo "✓ Skip-worktree enabled for: $file"
            else
                echo "⚠ File not found: $file"
            fi
        done
        ;;
    "disable")
        echo "Disabling skip-worktree for local configuration files..."
        for file in "${SKIP_WORKTREE_FILES[@]}"; do
            if [ -f "$file" ]; then
                git update-index --no-skip-worktree "$file"
                echo "✓ Skip-worktree disabled for: $file"
            else
                echo "⚠ File not found: $file"
            fi
        done
        ;;
    "status")
        echo "Current skip-worktree status:"
        git ls-files -v | grep "^S" | while read line; do
            echo "  $line"
        done
        ;;
    "list")
        echo "Files configured for skip-worktree:"
        for file in "${SKIP_WORKTREE_FILES[@]}"; do
            echo "  $file"
        done
        ;;
    *)
        echo "Usage: $0 {enable|disable|status|list}"
        echo ""
        echo "Commands:"
        echo "  enable  - Enable skip-worktree for all configured files"
        echo "  disable - Disable skip-worktree for all configured files"
        echo "  status  - Show current skip-worktree status"
        echo "  list    - List all files configured for skip-worktree"
        echo ""
        echo "This allows local modifications to these files without git conflicts."
        echo "Files remain tracked in the repository but local changes are ignored."
        ;;
esac
