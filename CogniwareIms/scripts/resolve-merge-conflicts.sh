#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Quick script to resolve merge conflicts with EdgeCraftRAG files
# Usage: Run this script when you have merge conflicts

set -e

echo "🔍 Checking git status..."
git status

echo ""
echo "📋 Resolving conflicts..."

# Accept main branch version for EdgeCraftRAG (not our project)
if [ -d "EdgeCraftRAG" ]; then
    echo "  ✓ Accepting main branch version for EdgeCraftRAG files..."
    git checkout --theirs EdgeCraftRAG/ 2>/dev/null || true
    git add EdgeCraftRAG/ 2>/dev/null || true
fi

# Accept main branch version for .github files (shared config)
if [ -f ".github/code_spell_ignore.txt" ]; then
    echo "  ✓ Accepting main branch version for .github/code_spell_ignore.txt..."
    git checkout --theirs .github/code_spell_ignore.txt 2>/dev/null || true
    git add .github/code_spell_ignore.txt 2>/dev/null || true
fi

if [ -f ".github/workflows/pr-image-size.yml" ]; then
    echo "  ✓ Accepting main branch version for .github/workflows/pr-image-size.yml..."
    git checkout --theirs .github/workflows/pr-image-size.yml 2>/dev/null || true
    git add .github/workflows/pr-image-size.yml 2>/dev/null || true
fi

# Keep our CogniwareIms changes
if [ -d "CogniwareIms" ]; then
    echo "  ✓ Keeping CogniwareIms changes..."
    git checkout --ours CogniwareIms/ 2>/dev/null || true
    git add CogniwareIms/ 2>/dev/null || true
fi

echo ""
echo "✅ Conflicts resolved!"
echo ""
echo "📝 Next steps:"
echo "   1. Review the changes: git status"
echo "   2. If rebasing: git rebase --continue"
echo "   3. If merging: git commit -s -m 'Resolve merge conflicts'"
echo "   4. Push: git push origin your-branch-name --force-with-lease"
echo ""
