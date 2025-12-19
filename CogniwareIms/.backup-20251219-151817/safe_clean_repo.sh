#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# SAFE script to clean repository history
# This script ensures CogniwareIms/ is preserved and only removes files outside it

set -e

echo "=========================================="
echo "Safe Clean Repository - Preserve CogniwareIms"
echo "=========================================="
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "ERROR: Not in a git repository"
    exit 1
fi

REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

echo "Repository: $REPO_ROOT"
echo ""

# Step 1: Verify CogniwareIms exists BEFORE doing anything
echo "Step 1: Verifying CogniwareIms/ exists..."
echo ""

if [ ! -d "CogniwareIms" ] && [ ! -d "cogniware-opea-ims" ]; then
    echo "❌ ERROR: CogniwareIms/ directory not found!"
    echo ""
    echo "Attempting to restore..."
    if [ -f "CogniwareIms/restore_cogniware_ims.sh" ]; then
        bash CogniwareIms/restore_cogniware_ims.sh
    else
        echo "Please restore CogniwareIms/ first using restore_cogniware_ims.sh"
        exit 1
    fi
fi

# Determine the path
if [ -d "CogniwareIms" ]; then
    COGNIWARE_PATH="CogniwareIms/"
    echo "✅ Found CogniwareIms/ directory"
elif [ -d "cogniware-opea-ims" ]; then
    COGNIWARE_PATH="cogniware-opea-ims/"
    echo "✅ Found cogniware-opea-ims/ directory"
    read -p "Rename to CogniwareIms/? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        mv cogniware-opea-ims CogniwareIms
        COGNIWARE_PATH="CogniwareIms/"
    fi
fi

echo "Using path: $COGNIWARE_PATH"
echo ""

# Step 2: Create backup BEFORE any operations
echo "Step 2: Creating backup..."
echo ""

CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
BACKUP_BRANCH="${CURRENT_BRANCH}-backup-$(date +%Y%m%d-%H%M%S)"

# Check if we can create backup
if git rev-parse --verify "$CURRENT_BRANCH" >/dev/null 2>&1; then
    if git branch "$BACKUP_BRANCH" 2>/dev/null; then
        echo "✅ Backup created: $BACKUP_BRANCH"
    else
        echo "⚠️  Could not create backup branch, but continuing..."
    fi
else
    echo "⚠️  No commits to backup, but continuing..."
fi

# Also create a backup of the CogniwareIms folder itself
if [ -d "$COGNIWARE_PATH" ]; then
    BACKUP_DIR="${COGNIWARE_PATH}.backup-$(date +%Y%m%d-%H%M%S)"
    echo "Creating file system backup: $BACKUP_DIR"
    cp -r "$COGNIWARE_PATH" "$BACKUP_DIR" 2>/dev/null || true
    echo "✅ File system backup created: $BACKUP_DIR"
fi

echo ""

# Step 3: Check current state
echo "Step 3: Analyzing current state..."
echo ""

# Count files
TOTAL_FILES=$(git ls-files 2>/dev/null | wc -l)
COGNIWARE_FILES=$(git ls-files "$COGNIWARE_PATH" 2>/dev/null | wc -l)
OUTSIDE_FILES=$(git ls-files 2>/dev/null | grep -v "^${COGNIWARE_PATH}" | wc -l)

echo "  Total files in repo: $TOTAL_FILES"
echo "  Files in $COGNIWARE_PATH: $COGNIWARE_FILES"
echo "  Files outside $COGNIWARE_PATH: $OUTSIDE_FILES"
echo ""

if [ "$OUTSIDE_FILES" -eq 0 ]; then
    echo "✅ Repository already clean - only $COGNIWARE_PATH files exist"
    echo "No filtering needed."
    exit 0
fi

# Step 4: Use the SAFE method - create new branch with only CogniwareIms
echo "Step 4: Creating clean branch with only CogniwareIms files..."
echo ""
echo "This method is SAFE - it creates a new branch without rewriting history"
echo ""

CLEAN_BRANCH="${CURRENT_BRANCH}-cogniware-only-$(date +%Y%m%d-%H%M%S)"

# Check if branch exists
if git show-ref --verify --quiet "refs/heads/$CLEAN_BRANCH" 2>/dev/null; then
    git branch -D "$CLEAN_BRANCH" 2>/dev/null || true
fi

# Create orphan branch
echo "Creating new orphan branch: $CLEAN_BRANCH"
git checkout --orphan "$CLEAN_BRANCH" 2>/dev/null || true

# Remove all files
echo "Removing all files..."
git rm -rf . 2>/dev/null || true

# Add only CogniwareIms files
echo "Adding only $COGNIWARE_PATH files..."
if [ -d "$COGNIWARE_PATH" ]; then
    git add "$COGNIWARE_PATH" 2>/dev/null || true
    
    # Verify files were added
    ADDED_COUNT=$(git diff --cached --name-only | wc -l)
    echo "  Added $ADDED_COUNT files from $COGNIWARE_PATH"
    
    if [ "$ADDED_COUNT" -eq 0 ]; then
        echo "❌ ERROR: No files were added from $COGNIWARE_PATH"
        echo "Restoring from backup..."
        if [ -d "$BACKUP_DIR" ]; then
            cp -r "$BACKUP_DIR"/* "$COGNIWARE_PATH"/ 2>/dev/null || true
            git add "$COGNIWARE_PATH" 2>/dev/null || true
        fi
    fi
else
    echo "❌ ERROR: $COGNIWARE_PATH directory disappeared!"
    echo "Restoring from backup..."
    if [ -d "$BACKUP_DIR" ]; then
        mv "$BACKUP_DIR" "$COGNIWARE_PATH"
        git add "$COGNIWARE_PATH" 2>/dev/null || true
    else
        echo "❌ CRITICAL: Cannot restore $COGNIWARE_PATH"
        echo "Please restore manually and try again"
        exit 1
    fi
fi

# Create initial commit
echo ""
echo "Creating initial commit..."
if ! git diff --cached --quiet; then
    git commit -s -m "feat: initial CogniwareIms commit

- Add CogniwareIms project files
- Clean history with only CogniwareIms-related changes
- Removed all files outside CogniwareIms/ directory"
    echo "✅ Initial commit created"
else
    echo "⚠️  No changes to commit"
fi

echo ""

# Step 5: Verify final state
echo "Step 5: Verifying final state..."
echo ""

echo "Files in repository:"
FINAL_TOTAL=$(git ls-files 2>/dev/null | wc -l)
FINAL_COGNIWARE=$(git ls-files "$COGNIWARE_PATH" 2>/dev/null | wc -l)
FINAL_OUTSIDE=$(git ls-files 2>/dev/null | grep -v "^${COGNIWARE_PATH}" | wc -l)

echo "  Total files: $FINAL_TOTAL"
echo "  $COGNIWARE_PATH files: $FINAL_COGNIWARE"
echo "  Files outside: $FINAL_OUTSIDE"
echo ""

# Verify CogniwareIms still exists
if [ ! -d "$COGNIWARE_PATH" ]; then
    echo "❌ CRITICAL ERROR: $COGNIWARE_PATH was deleted!"
    echo "Restoring from backup..."
    if [ -d "$BACKUP_DIR" ]; then
        mv "$BACKUP_DIR" "$COGNIWARE_PATH"
        git add "$COGNIWARE_PATH"
        git commit --amend --no-edit
    fi
fi

if [ "$FINAL_OUTSIDE" -eq 0 ] && [ "$FINAL_COGNIWARE" -gt 0 ]; then
    echo "✅ SUCCESS: Repository is clean"
    echo "   Only $COGNIWARE_PATH files remain"
else
    echo "⚠️  WARNING: Repository may not be fully clean"
    echo "   Files outside: $FINAL_OUTSIDE"
    echo "   $COGNIWARE_PATH files: $FINAL_COGNIWARE"
fi

echo ""
echo "=========================================="
echo "Next Steps"
echo "=========================================="
echo ""
echo "1. Review the clean branch:"
echo "   git log --oneline"
echo "   git ls-files"
echo ""
echo "2. If satisfied, replace main with clean branch:"
echo "   git checkout $CURRENT_BRANCH"
echo "   git reset --hard $CLEAN_BRANCH"
echo "   git branch -D $CLEAN_BRANCH  # Optional: remove temp branch"
echo ""
echo "3. Push to update PR #2307:"
echo "   git push origin $CURRENT_BRANCH --force-with-lease"
echo ""
echo "4. If something went wrong, restore:"
if [ -n "$BACKUP_BRANCH" ]; then
    echo "   git reset --hard $BACKUP_BRANCH"
fi
if [ -d "$BACKUP_DIR" ]; then
    echo "   Or restore files from: $BACKUP_DIR"
fi
echo ""
echo "Clean branch: $CLEAN_BRANCH"
if [ -n "$BACKUP_BRANCH" ]; then
    echo "Backup branch: $BACKUP_BRANCH"
fi
if [ -d "$BACKUP_DIR" ]; then
    echo "File backup: $BACKUP_DIR"
fi
echo ""

