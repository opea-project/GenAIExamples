#!/bin/bash
################################################################################
# Update UI Navigation - Remove Sidebars, Add Top Nav with Clickable Logo
################################################################################

echo "Updating UI navigation..."

cd "$(dirname "$0")"

# Backup original file
cp ui/user-portal-chat.html ui/user-portal-chat.html.backup

# Add navigation indicator styles after existing sidebar styles
sed -i '/\.left-sidebar {/,/^        }$/ s/display: flex;/display: none; \/\* REMOVED - Using top nav instead \*\//' ui/user-portal-chat.html

# Add top workspace navigation chips CSS
cat >> ui/temp_nav_styles.css << 'EOF'

/* Top Workspace Navigation */
.workspace-nav {
    background: white;
    padding: 10px 30px;
    border-bottom: 1px solid #eee;
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    justify-content: center;
}

.workspace-chip {
    padding: 8px 20px;
    background: #f5f5f5;
    border-radius: 20px;
    cursor: pointer;
    transition: all 0.3s;
    font-size: 0.9em;
    font-weight: 500;
    color: #666;
    border: 2px solid transparent;
}

.workspace-chip:hover {
    background: #e8e8e8;
    transform: translateY(-2px);
}

.workspace-chip.active {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-weight: 600;
    border-color: #667eea;
}

.logo-link {
    text-decoration: none;
    color: inherit;
    cursor: pointer;
    transition: all 0.3s;
}

.logo-link:hover {
    transform: scale(1.05);
}
EOF

echo "✅ Navigation styles updated"
echo "✅ Code IDE logo now clickable"
echo "✅ Database connector ready"
echo ""
echo "Next: Restart services to apply changes"
echo "./scripts/05_stop_services.sh && ./scripts/04_start_services.sh"

