#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Script to fix all pre-commit hook issues

set -e

echo "Fixing pre-commit issues in cogniware-opea-ims..."

# 1. Fix end-of-file issues (add newline at end of files)
echo "1. Fixing end-of-file issues..."
find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.md" -o -name "*.sh" -o -name "*.ts" -o -name "*.tsx" \) \
  ! -path "./node_modules/*" \
  ! -path "./.git/*" \
  ! -path "./data/*" \
  ! -path "./.next/*" \
  -exec sh -c 'tail -c1 "$1" | read -r _ || echo >> "$1"' _ {} \;

# 2. Fix trailing whitespace
echo "2. Fixing trailing whitespace..."
find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.md" -o -name "*.sh" -o -name "*.ts" -o -name "*.tsx" \) \
  ! -path "./node_modules/*" \
  ! -path "./.git/*" \
  ! -path "./data/*" \
  ! -path "./.next/*" \
  -exec sed -i '' 's/[[:space:]]*$//' {} \;

# 3. Sort requirements.txt
echo "3. Sorting requirements.txt..."
if [ -f "backend/requirements.txt" ]; then
  sort -u backend/requirements.txt -o backend/requirements.txt
fi

# 4. Make shell scripts executable
echo "4. Making shell scripts executable..."
find . -name "*.sh" -type f ! -path "./.git/*" -exec chmod +x {} \;

echo "✅ All pre-commit issues fixed!"
echo ""
echo "Next steps:"
echo "  git add ."
echo "  git commit -m 'Fix pre-commit issues'"

