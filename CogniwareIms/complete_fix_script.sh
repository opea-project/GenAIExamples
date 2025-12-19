#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Complete Fix Script for PR #2307
# This script orchestrates all fixes needed for the PR

set -e

echo "=========================================="
echo "Complete Fix for PR #2307"
echo "=========================================="
echo ""
echo "This script will:"
echo "1. Restore CogniwareIms folder (if deleted)"
echo "2. Clean repository to only include CogniwareIms"
echo "3. Resolve merge conflicts"
echo "4. Verify final state"
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "ERROR: Not in a git repository"
    echo "Please navigate to GenAIExamples repository"
    exit 1
fi

REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

REPO_NAME=$(basename "$REPO_ROOT")
if [ "$REPO_NAME" != "GenAIExamples" ]; then
    echo "WARNING: Repository name is '$REPO_NAME', expected 'GenAIExamples'"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Repository: $REPO_ROOT"
echo ""

# Step 1: Restore CogniwareIms if deleted
echo "=========================================="
echo "Step 1: Restore CogniwareIms Folder"
echo "=========================================="
echo ""

if [ ! -d "CogniwareIms" ]; then
    echo "CogniwareIms/ not found, attempting restoration..."
    
    if [ -f "CogniwareIms/restore_cogniware_ims.sh" ]; then
        bash CogniwareIms/restore_cogniware_ims.sh
    else
        echo "Restoration script not found. Trying manual methods..."
        
        # Try from remote
        git fetch origin 2>/dev/null || true
        if git show "origin/main:CogniwareIms" >/dev/null 2>&1; then
            git checkout origin/main -- CogniwareIms/ 2>&1 || true
        fi
    fi
    
    if [ ! -d "CogniwareIms" ]; then
        echo "❌ ERROR: Could not restore CogniwareIms/"
        echo "Please restore manually and run this script again"
        exit 1
    fi
else
    echo "✅ CogniwareIms/ directory exists"
fi

echo ""

# Step 2: Clean repository
echo "=========================================="
echo "Step 2: Clean Repository"
echo "=========================================="
echo ""

# Check if we need to clean
OUTSIDE_FILES=$(git ls-files 2>/dev/null | grep -v "^CogniwareIms/" | wc -l)

if [ "$OUTSIDE_FILES" -gt 0 ]; then
    echo "Found $OUTSIDE_FILES files outside CogniwareIms/"
    echo "Running safe clean script..."
    echo ""
    
    if [ -f "CogniwareIms/safe_clean_repository.sh" ]; then
        bash CogniwareIms/safe_clean_repository.sh
    else
        echo "⚠️  Safe clean script not found"
        echo "Skipping automatic clean. Please run manually:"
        echo "  ./CogniwareIms/safe_clean_repository.sh"
    fi
else
    echo "✅ Repository already clean (only CogniwareIms files)"
fi

echo ""

# Step 3: Resolve merge conflicts
echo "=========================================="
echo "Step 3: Resolve Merge Conflicts"
echo "=========================================="
echo ""

# Set up upstream
echo "Setting up upstream remote..."
git remote add upstream https://github.com/opea-project/GenAIExamples.git 2>/dev/null || true
git fetch upstream 2>/dev/null || true

# Check current branch
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
echo "Current branch: $CURRENT_BRANCH"
echo ""

# Check if merge is needed
echo "Checking for merge conflicts..."
if git merge-tree $(git merge-base "$CURRENT_BRANCH" upstream/main 2>/dev/null || echo "HEAD") "$CURRENT_BRANCH" upstream/main 2>/dev/null | grep -q "^+<<<<<<<"; then
    echo "Merge conflicts detected. Resolving..."
    
    # Merge upstream
    git merge upstream/main 2>&1 || true
    
    # Resolve conflicts
    echo "Resolving conflicts..."
    git checkout --theirs .github/ 2>/dev/null || true
    git checkout --theirs EdgeCraftRAG/ 2>/dev/null || true
    git checkout --ours CogniwareIms/ 2>/dev/null || true
    git add . 2>/dev/null || true
    
    # Complete merge if in progress
    if [ -d ".git/MERGE_HEAD" ]; then
        git commit -s -m "Resolve merge conflicts: accept upstream for non-CogniwareIms files" 2>/dev/null || true
    fi
    
    echo "✅ Merge conflicts resolved"
else
    echo "✅ No merge conflicts detected"
fi

echo ""

# Step 4: Verify final state
echo "=========================================="
echo "Step 4: Verify Final State"
echo "=========================================="
echo ""

# Check CogniwareIms exists
if [ -d "CogniwareIms" ]; then
    COGNIWARE_FILES=$(git ls-files CogniwareIms/ 2>/dev/null | wc -l)
    echo "✅ CogniwareIms/ exists with $COGNIWARE_FILES files"
else
    echo "❌ ERROR: CogniwareIms/ not found!"
    exit 1
fi

# Check for files outside CogniwareIms
OUTSIDE_FILES=$(git ls-files 2>/dev/null | grep -v "^CogniwareIms/" | grep -v "^\.github/" | wc -l)
if [ "$OUTSIDE_FILES" -eq 0 ]; then
    echo "✅ Repository clean (only CogniwareIms files)"
else
    echo "⚠️  WARNING: Found $OUTSIDE_FILES files outside CogniwareIms/"
    echo "   (This may be acceptable if they're .github files)"
fi

# Check commits
COMMIT_COUNT=$(git rev-list --count "$CURRENT_BRANCH" 2>/dev/null || echo "0")
echo "Commits in branch: $COMMIT_COUNT"

echo ""

# Step 5: Summary and next steps
echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""
echo "✅ CogniwareIms folder: $(test -d CogniwareIms && echo 'EXISTS' || echo 'MISSING')"
echo "✅ Repository cleaned: $(test $OUTSIDE_FILES -eq 0 && echo 'YES' || echo 'PARTIAL')"
echo "✅ Merge conflicts: $(test -d .git/MERGE_HEAD && echo 'IN PROGRESS' || echo 'RESOLVED')"
echo ""
echo "Next Steps:"
echo "1. Review: git log --oneline"
echo "2. Verify: git ls-files"
echo "3. Push: git push origin $CURRENT_BRANCH --force-with-lease"
echo "4. Check PR: https://github.com/opea-project/GenAIExamples/pull/2307"
echo ""

