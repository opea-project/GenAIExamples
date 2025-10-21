#!/bin/bash
################################################################################
# Sync Local Projects to Production Server
################################################################################

REMOTE_HOST="185.141.218.141"
REMOTE_USER="root"
REMOTE_PASSWORD="CogniDream2025"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║         Syncing Projects to Production                          ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

cd "$(dirname "$0")"

# Check if projects directory exists
if [ ! -d "projects" ] || [ -z "$(ls -A projects 2>/dev/null)" ]; then
    echo "❌ No local projects found to sync"
    exit 1
fi

# Count projects
PROJECT_COUNT=$(ls -d projects/*/ 2>/dev/null | wc -l)

echo -e "${BLUE}Found ${PROJECT_COUNT} local project(s) to sync${NC}"
echo ""

# List projects
echo "Projects to sync:"
for proj in projects/*/; do
    if [ -d "$proj" ]; then
        name=$(basename "$proj")
        files=$(find "$proj" -type f | wc -l)
        echo "  • $name ($files files)"
    fi
done

echo ""
echo -e "${BLUE}Syncing to production server...${NC}"

# Create projects directory on remote if it doesn't exist
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST \
    'mkdir -p /opt/cognidream/projects'

# Sync each project
for proj in projects/*/; do
    if [ -d "$proj" ]; then
        name=$(basename "$proj")
        echo -n "  Syncing $name... "
        
        sshpass -p "$REMOTE_PASSWORD" scp -r -q -o StrictHostKeyChecking=no \
            "$proj" \
            $REMOTE_USER@$REMOTE_HOST:/opt/cognidream/projects/
        
        echo -e "${GREEN}✓${NC}"
    fi
done

# Set correct permissions
echo ""
echo -e "${BLUE}Setting permissions...${NC}"
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST \
    'chown -R cognidream:cognidream /opt/cognidream/projects && chmod -R 755 /opt/cognidream/projects'

echo -e "${GREEN}✅ Permissions set${NC}"

# Verify
echo ""
echo -e "${BLUE}Verifying sync...${NC}"
REMOTE_COUNT=$(sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST \
    'ls -d /opt/cognidream/projects/*/ 2>/dev/null | wc -l')

echo "Local projects: $PROJECT_COUNT"
echo "Remote projects: $REMOTE_COUNT"

if [ "$PROJECT_COUNT" -eq "$REMOTE_COUNT" ]; then
    echo -e "${GREEN}✅ Sync successful!${NC}"
else
    echo "⚠️  Count mismatch - please verify manually"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║              Projects Synced to Production                       ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Access your projects at:"
echo -e "${GREEN}   https://demo.cogniware.ai/code-ide.html${NC}"
echo ""
echo "📂 Projects are now available in the 'Open Project...' dropdown"
echo ""
echo "✨ Continue developing on production!"
echo ""

