# Local Configuration Management Guide

This guide explains how to manage local configuration files that can be edited without causing Git conflicts during pulls.

## Overview

Certain files in this project are configured to use Git's `skip-worktree` feature, which allows local modifications while keeping the files tracked in the repository. This is useful for configuration files that need to be customized per environment.

## Configured Files

The following files are set up for local modifications:

- `config/redis_config.txt` - Redis configuration
- `robots.txt` - SEO robots file
- `static/pic/favicon.ico` - Website favicon
- `static/pic/favicon.png` - Website favicon (PNG)
- `static/pic/logo.png` - Main logo
- `static/pic/logo_footer.png` - Footer logo
- `static/pic/placeholder.png` - Placeholder image

## How It Works

When `skip-worktree` is enabled for a file:
- The file remains tracked in Git
- Local modifications are ignored by Git operations
- `git pull` will not overwrite your local changes
- The file will not appear in `git status` as modified

## Management Script

Use the provided script to manage skip-worktree settings:

```bash
# Check current status
./config/manage_skip_worktree.sh status

# Enable skip-worktree for all configured files
./config/manage_skip_worktree.sh enable

# Disable skip-worktree for all configured files
./config/manage_skip_worktree.sh disable

# List all configured files
./config/manage_skip_worktree.sh list
```

## Manual Commands

You can also manage skip-worktree manually:

```bash
# Enable skip-worktree for a specific file
git update-index --skip-worktree path/to/file

# Disable skip-worktree for a specific file
git update-index --no-skip-worktree path/to/file

# Check which files have skip-worktree enabled
git ls-files -v | grep "^S"
```

## Important Notes

1. **Files remain in repository**: These files are still tracked and will be included in commits
2. **Local changes persist**: Your local modifications will not be overwritten by git pull
3. **Manual management**: If you need to update these files from the repository, temporarily disable skip-worktree
4. **Team coordination**: Inform team members about local configuration requirements

## Troubleshooting

### If you need to update a skip-worktree file from the repository:

```bash
# Temporarily disable skip-worktree
git update-index --no-skip-worktree path/to/file

# Pull the latest changes
git pull

# Re-enable skip-worktree
git update-index --skip-worktree path/to/file
```

### If git status shows unexpected changes:

```bash
# Check skip-worktree status
git ls-files -v | grep "^S"

# Verify file modifications
git diff path/to/file
```

## Best Practices

1. **Document local changes**: Keep notes of what you've customized locally
2. **Regular updates**: Periodically check if upstream changes need to be incorporated
3. **Team communication**: Coordinate with team members about local configuration needs
4. **Backup local configs**: Keep backups of your local configurations
