#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Script to restore CogniwareIms folder after accidental deletion
# This script attempts multiple recovery methods

set -e

echo "=========================================="
echo "Restore CogniwareIms Folder"
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

# Method 1: Check if CogniwareIms exists in working directory (maybe just not tracked)
if [ -d "CogniwareIms" ]; then
    echo "✅ CogniwareIms/ directory exists in working directory"
    exit 0
fi

# Method 2: Try to restore from backup branch
echo "Step 1: Checking for backup branches..."
BACKUP_BRANCHES=$(git branch -a | grep -i backup | head -5)

if [ -n "$BACKUP_BRANCHES" ]; then
    echo "Found backup branches:"
    echo "$BACKUP_BRANCHES"
    echo ""
    
    # Try the most recent backup
    LATEST_BACKUP=$(echo "$BACKUP_BRANCHES" | head -1 | sed 's/.*\///' | xargs)
    echo "Attempting to restore from: $LATEST_BACKUP"
    
    if git show "$LATEST_BACKUP:CogniwareIms" >/dev/null 2>&1; then
        echo "Found CogniwareIms in backup branch"
        git checkout "$LATEST_BACKUP" -- CogniwareIms/ 2>/dev/null || true
        if [ -d "CogniwareIms" ]; then
            echo "✅ Restored CogniwareIms/ from backup branch"
            exit 0
        fi
    fi
fi

# Method 3: Try to restore from remote
echo ""
echo "Step 2: Checking remote branches..."
git fetch origin 2>/dev/null || true
git fetch upstream 2>/dev/null || true

# Check origin/main
if git show-ref --verify --quiet refs/remotes/origin/main 2>/dev/null; then
    echo "Checking origin/main..."
    if git show "origin/main:CogniwareIms" >/dev/null 2>&1; then
        echo "Found CogniwareIms in origin/main"
        git checkout origin/main -- CogniwareIms/ 2>&1 || true
        if [ -d "CogniwareIms" ]; then
            echo "✅ Restored CogniwareIms/ from origin/main"
            exit 0
        fi
    fi
fi

# Check upstream/main
if git show-ref --verify --quiet refs/remotes/upstream/main 2>/dev/null; then
    echo "Checking upstream/main..."
    if git show "upstream/main:CogniwareIms" >/dev/null 2>&1; then
        echo "Found CogniwareIms in upstream/main"
        git checkout upstream/main -- CogniwareIms/ 2>&1 || true
        if [ -d "CogniwareIms" ]; then
            echo "✅ Restored CogniwareIms/ from upstream/main"
            exit 0
        fi
    fi
fi

# Method 4: Check git reflog for previous HEAD
echo ""
echo "Step 3: Checking git reflog..."
REFLOG_ENTRIES=$(git reflog | head -20)

if [ -n "$REFLOG_ENTRIES" ]; then
    echo "Found reflog entries, checking for CogniwareIms..."
    
    for entry in $(git reflog | head -10 | awk '{print $1}'); do
        if git show "$entry:CogniwareIms" >/dev/null 2>&1; then
            echo "Found CogniwareIms at: $entry"
            git checkout "$entry" -- CogniwareIms/ 2>&1 || true
            if [ -d "CogniwareIms" ]; then
                echo "✅ Restored CogniwareIms/ from reflog"
                exit 0
            fi
        fi
    done
fi

# Method 5: Check if it exists in any commit
echo ""
echo "Step 4: Searching all commits for CogniwareIms..."
COMMITS_WITH_COGNIWARE=$(git log --all --oneline --name-only | grep -B1 "CogniwareIms" | grep "^[a-f0-9]" | head -5)

if [ -n "$COMMITS_WITH_COGNIWARE" ]; then
    echo "Found commits with CogniwareIms:"
    echo "$COMMITS_WITH_COGNIWARE"
    echo ""
    
    FIRST_COMMIT=$(echo "$COMMITS_WITH_COGNIWARE" | head -1)
    echo "Attempting to restore from commit: $FIRST_COMMIT"
    git checkout "$FIRST_COMMIT" -- CogniwareIms/ 2>&1 || true
    
    if [ -d "CogniwareIms" ]; then
        echo "✅ Restored CogniwareIms/ from commit $FIRST_COMMIT"
        exit 0
    fi
fi

# Method 6: Check if there's a cogniware-opea-ims folder (alternative name)
if [ -d "cogniware-opea-ims" ]; then
    echo "✅ Found cogniware-opea-ims/ directory"
    echo "Renaming to CogniwareIms/..."
    mv cogniware-opea-ims CogniwareIms
    echo "✅ Renamed to CogniwareIms/"
    exit 0
fi

# If all methods fail
echo ""
echo "=========================================="
echo "❌ Could not restore CogniwareIms/"
echo "=========================================="
echo ""
echo "Recovery methods attempted:"
echo "1. ✅ Checked working directory"
echo "2. ✅ Checked backup branches"
echo "3. ✅ Checked remote branches (origin/main, upstream/main)"
echo "4. ✅ Checked git reflog"
echo "5. ✅ Searched all commits"
echo "6. ✅ Checked for alternative names"
echo ""
echo "Next steps:"
echo "1. Check if you have a local backup of CogniwareIms/"
echo "2. Clone from the original repository:"
echo "   git clone https://github.com/Cogniware-Inc/GenAIExamples.git"
echo "3. Copy CogniwareIms/ from another location"
echo "4. Restore from a backup if you have one"
echo ""
exit 1

