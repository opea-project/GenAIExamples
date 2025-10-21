#!/bin/bash
# UI Enhancement Script - Updates user portal with all improvements

cd "$(dirname "$0")/ui"

echo "Updating UI with enhancements..."

# 1. Change "Process with AI" to "Process with CogniDream"
sed -i 's/Process with AI/Process with CogniDream/g' user-portal.html
echo "✅ Updated button text to CogniDream"

# 2. Add enhanced CSS link
sed -i '/<title>Cogniware Core - User Portal<\/title>/a\    <link rel="stylesheet" href="user-portal-enhanced.css">' user-portal.html
echo "✅ Added enhanced CSS link"

# 3. Update visualizer script reference
sed -i 's/parallel-llm-visualizer.js/parallel-llm-visualizer-enhanced.js/g' user-portal.html
echo "✅ Updated visualizer reference"

echo ""
echo "UI Enhancement Complete!"
echo "Please restart services to apply changes."

