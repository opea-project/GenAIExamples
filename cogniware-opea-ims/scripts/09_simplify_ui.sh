#!/bin/bash
################################################################################
# Simplify UI Script
# Removes manual forms and adds example-driven interface
################################################################################

cd "$(dirname "$0")/../ui"

echo "📝 Simplifying User Portal..."

# Backup original
cp user-portal.html user-portal.html.backup

# Create simplified workspaces
cat > workspace-simplified.html << 'EOF'
            <!-- Code Generation Workspace -->
            <div class="workspace" id="workspace-codegen">
                <!-- Natural Language Input -->
                <div class="nl-input-bar">
                    <h3>🤖 Natural Language Input <span class="llm-indicator" id="nlLLMStatus">Checking LLMs...</span></h3>
                    <div class="nl-input-container">
                        <input type="text" id="nlCodeInput" placeholder='Describe what you want to create...'>
                        <button onclick="processNaturalLanguage('code_generation', this)">✨ Process with CogniDream</button>
                    </div>
                    <div class="nl-status" id="nlCodeStatus"></div>
                </div>
                
                <!-- Examples Section -->
                <div id="codegenExamples"></div>
                
                <!-- Results -->
                <div id="codegenResult"></div>
            </div>

            <!-- Browser Automation Workspace -->
            <div class="workspace" id="workspace-browser">
                <div class="nl-input-bar">
                    <h3>🤖 Natural Language Input <span class="llm-indicator" id="nlBrowserLLMStatus">MCP Enabled</span></h3>
                    <div class="nl-input-container">
                        <input type="text" id="nlBrowserInput" placeholder='Describe the browser automation task...'>
                        <button onclick="processNaturalLanguage('browser', this)">✨ Process with CogniDream</button>
                    </div>
                    <div class="nl-status" id="nlBrowserStatus"></div>
                </div>
                
                <!-- Examples Section -->
                <div id="browserExamples"></div>
                
                <!-- Results -->
                <div id="browserResult"></div>
            </div>

            <!-- Database Workspace -->
            <div class="workspace" id="workspace-database">
                <div class="nl-input-bar">
                    <h3>🤖 Natural Language Input <span class="llm-indicator" id="nlDatabaseLLMStatus">MCP Enabled</span></h3>
                    <div class="nl-input-container">
                        <input type="text" id="nlDatabaseInput" placeholder='Ask a question about your data...'>
                        <button onclick="processNaturalLanguage('database', this)">✨ Process with CogniDream</button>
                    </div>
                    <div class="nl-status" id="nlDatabaseStatus"></div>
                </div>
                
                <!-- Examples Section -->
                <div id="databaseExamples"></div>
                
                <!-- Results -->
                <div id="dbResult"></div>
            </div>

            <!-- Documents Workspace -->
            <div class="workspace" id="workspace-documents">
                <div class="nl-input-bar">
                    <h3>🤖 Natural Language Input <span class="llm-indicator" id="nlDocumentsLLMStatus">MCP Enabled</span></h3>
                    <div class="nl-input-container">
                        <input type="text" id="nlDocumentsInput" placeholder='Ask questions about your documents...'>
                        <button onclick="processNaturalLanguage('documents', this)">✨ Process with CogniDream</button>
                    </div>
                    <div class="nl-status" id="nlDocumentsStatus"></div>
                </div>
                
                <!-- Examples Section -->
                <div id="documentsExamples"></div>
                
                <!-- Results -->
                <div id="documentsResult"></div>
            </div>
EOF

echo "✅ Created simplified workspace template"

# Add workspace-examples.js script reference if not present
if ! grep -q "workspace-examples.js" user-portal.html; then
    # Find the parallel-llm-visualizer line and add after it
    sed -i '/parallel-llm-visualizer-enhanced.js/a\    <script src="workspace-examples.js"><\/script>' user-portal.html
    echo "✅ Added workspace-examples.js reference"
fi

# Add initialization code for examples
cat >> init-examples.js << 'EOF'
// Initialize examples when workspaces load
document.addEventListener('DOMContentLoaded', function() {
    // Add examples to each workspace
    if (typeof renderExamplesSection === 'function') {
        document.getElementById('codegenExamples').innerHTML = renderExamplesSection('code_generation');
        document.getElementById('browserExamples').innerHTML = renderExamplesSection('browser');
        document.getElementById('databaseExamples').innerHTML = renderExamplesSection('database');
        document.getElementById('documentsExamples').innerHTML = renderExamplesSection('documents');
    }
});
EOF

echo "✅ Created initialization script"

echo ""
echo "To complete the simplification:"
echo "1. Manually replace workspace sections in user-portal.html with workspace-simplified.html content"
echo "2. Or use the backup and make targeted edits"
echo ""
echo "Files created:"
echo "  - workspace-simplified.html (template)"
echo "  - init-examples.js (initialization)"
echo "  - user-portal.html.backup (backup)"


