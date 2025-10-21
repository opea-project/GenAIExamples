# 🚀 CogniDream Platform - START HERE

## Welcome to CogniDream!

This guide will help you get started with the complete AI-powered development platform.

---

## 🎯 Quick Start (2 Minutes)

### 1. Start All Services
```bash
cd /home/deadbrainviv/Documents/GitHub/cogniware-core
./scripts/04_start_services.sh
```

Wait for all 7 services to start (Admin, Production, Business, Demo, MCP, Web Server).

### 2. Open Your Browser
```
http://localhost:8000
```

### 3. Explore the Landing Page
- See all 6 AI-powered modules
- Beautiful gradient design
- Module descriptions and features

### 4. Login
- Click "Get Started" or "Login"
- **Username**: `user`
- **Password**: `Cogniware@2025`

### 5. Choose Your Module
Click any of the 6 module cards:
- 💻 **Code IDE** - Create entire projects
- 🤖 **AI Chat** - Conversational assistant
- 📄 **Document Analysis** - Analyze PDFs/DOCX
- 🗄️ **Database Q&A** - Natural language queries
- 🌐 **Browser Automation** - Web scraping
- ⚙️ **Admin Portal** - System management

---

## 🌟 Platform Overview

### Main Landing Page
**URL**: `http://localhost:8000/` or `http://localhost:8000/index.html`

**Features**:
```
┌────────────────────────────────────────────┐
│  🚀 CogniDream                   Get Started│
├────────────────────────────────────────────┤
│                                            │
│         Build Anything with AI             │
│    Your complete AI-powered development    │
│              platform                       │
│                                            │
│    [Start Creating] [Explore Modules]      │
│                                            │
├────────────────────────────────────────────┤
│                                            │
│  Powerful AI Modules                       │
│  Choose your workspace                     │
│                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Code IDE │ │AI Chat   │ │Documents │  │
│  │   NEW    │ │ ENHANCED │ │PRODUCTION│  │
│  └──────────┘ └──────────┘ └──────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │Database  │ │ Browser  │ │  Admin   │  │
│  │  SMART   │ │AUTOMATED │ │ CONTROL  │  │
│  └──────────┘ └──────────┘ └──────────┘  │
│                                            │
├────────────────────────────────────────────┤
│  Why Choose CogniDream?                    │
│  • Parallel LLM Processing (2.5x faster)   │
│  • Context Management with MCP             │
│  • Production Ready - No Simulations       │
│  ...8 more features                        │
└────────────────────────────────────────────┘
```

---

## 💻 Module 1: Code IDE

### Access
```
http://localhost:8000/code-ide.html
```

### What It Does
Creates **entire projects** with folder structures and multiple files using AI.

### Interface
```
┌─────────────────────────────────────────────────────┐
│ 🚀 CogniDream IDE    [+New Project] [✨Generate AI] │
├──────────┬──────────────────────────┬───────────────┤
│          │                          │               │
│ EXPLORER │  Monaco Code Editor      │  AI Assistant │
│          │                          │               │
│ 📁 app/  │  def main():            │  How can I    │
│   main.py│      # Your code        │  help you?    │
│   models │      pass               │               │
│ 📁 tests │                          │  [Chat area]  │
│          │  [Tabs for open files]  │               │
│          │                          │  [AI input]   │
│          │                          │  [✨ Send]    │
│          │                          │               │
└──────────┴──────────────────────────┴───────────────┘
```

### Workflow
1. Click "+ New Project"
2. Choose template (FastAPI, React, Django, Flask, Express, Python CLI, Blank)
3. Enter project name and description
4. Click "Create Project"
5. Project generates with complete structure
6. Browse files in file tree
7. Click file to edit in Monaco Editor
8. Use AI to generate more code
9. Auto-saves changes

### Example
```
User: Create "my-customer-api"
Template: FastAPI

Generated:
✓ app/main.py (FastAPI with CRUD endpoints)
✓ app/models.py (Pydantic models)
✓ app/database.py (DB config)
✓ tests/test_main.py (Unit tests)
✓ requirements.txt
✓ README.md
✓ .gitignore

Then ask AI:
"Add JWT authentication middleware"
"Create endpoint for user registration"
"Add database models for Orders"

AI generates code that fits your existing structure!
```

---

## 🤖 Module 2: AI Chat Assistant

### Access
```
http://localhost:8000/user-portal-chat.html
```

### What It Does
Conversational AI with **parallel LLM processing** for chat-based interactions.

### Interface
```
┌─────────────────────────────────────────────────────┐
│ Chat with CogniDream        7 Interface + 2 Knowledge│
│                             🏆 Patent-Compliant MCP  │
├──────────┬──────────────────────────┬───────────────┤
│          │                          │               │
│ Modules  │  Conversation            │  📚 Examples  │
│          │                          │               │
│ 💻 Code  │ You: Generate Fibonacci  │  Example 1:   │
│ 📄 Docs  │                          │  REST API...  │
│ 🗄️ DB    │ AI: [Shows LLM cards]   │               │
│ 🌐 Web   │     [Code output]        │  Example 2:   │
│          │     [Download button]    │  Data proc... │
│          │                          │               │
│ 🚪Logout │ [Type message...] [Send] │  Example 3... │
│          │                          │               │
└──────────┴──────────────────────────┴───────────────┘
```

### Features
- Chat-based conversation
- Parallel LLM processing (2 Interface + 1 Knowledge)
- Patent compliance displayed
- Download all outputs
- Performance metrics
- Examples sidebar
- Multi-workspace support

---

## 📄 Module 3: Document Analysis

### Access
```
http://localhost:8000/user-portal-chat.html?module=documents
```

### What It Does
**Real content extraction** from documents with OCR and NLP.

### Supported Formats
- PDF (.pdf)
- Word (.docx, .doc)
- Excel (.xlsx, .xls)
- PowerPoint (.pptx, .ppt)
- Text (.txt)
- Markdown (.md)
- CSV (.csv)
- JSON (.json)

### Workflow
1. Auto-opens Documents workspace
2. Upload your document
3. Ask question: "What are the main points?"
4. Get real analysis:
   - Document type (Legal, Financial, Technical)
   - Statistics (word count, sentences)
   - Main topics extracted
   - Entity recognition (dates, emails, numbers)
   - Smart Q&A with relevant passages
5. Download analysis report

### Example Output
```
📄 Document Analysis for 'TheForeignMarriageAct1969.pdf'

🔍 Document Type: Legal Document
📊 Statistics:
  • Total Words: 6,545
  • Total Sentences: 387
  • Pages: 24

🎯 Main Topics:
  1. Marriage
  2. Registration
  3. Consular

🔑 Key Elements:
  • Dates: 1969-05-10, 1970-01-01
  • Numerical Data: 87 instances

💡 Answer: [Relevant passages from document]

✅ Production Analysis: Real content extraction completed.
```

---

## 🗄️ Module 4: Database Q&A

### Access
```
http://localhost:8000/user-portal-chat.html?module=database
```

### What It Does
Natural language to SQL queries with results export.

### Workflow
1. Auto-opens Database workspace
2. Enter database name (e.g., "customers_db")
3. Ask: "Show top 10 customers by revenue"
4. Get:
   - Generated SQL query
   - Results table
   - Summary statistics
5. Download as CSV

---

## 🌐 Module 5: Browser Automation

### Access
```
http://localhost:8000/user-portal-chat.html?module=browser
```

### What It Does
Automate web interactions and data extraction.

### Workflow
1. Auto-opens Browser workspace
2. Enter target URL
3. Describe task: "Extract all product prices"
4. Get:
   - Automation steps
   - Extracted data
   - Screenshots (if captured)
5. Download automation log

---

## ⚙️ Module 6: Admin Portal

### Access
```
http://localhost:8000/admin-portal-enhanced.html
```

### Requires
Admin credentials (username: `admin`, password: `Admin@2025`)

### What It Does
Manage the entire platform (LLMs, users, licenses, analytics).

### Tabs
1. **LLM Management**:
   - Cogniware LLMs (12 built-in)
   - Import from External
   - View statistics

2. **User Management**:
   - Create/edit/delete users
   - Assign roles
   - View activity logs

3. **License Management**:
   - Create licenses
   - Assign to organizations
   - Monitor usage

4. **Analytics Dashboard**:
   - Request statistics
   - Performance metrics
   - System health

---

## 🔄 Navigation Flow

### Complete User Flow

```
Landing Page (index.html)
        ↓
    Click Module
        ↓
   Login Required?
        ↓ Yes
  Login Page (login.html)
        ↓
  Enter credentials
        ↓
   Authenticated!
        ↓
 Back to Landing (index.html)
        ↓
   User Bar Appears
   (shows logged-in status)
        ↓
  Click Module Again
        ↓
   Direct Access!
        ↓
┌───────┴────────┐
│                │
Code IDE    Chat Portal → Select Workspace
                │         (Documents/Database/Browser)
                │                ↓
                │         Use AI Features
                │                ↓
                │         Download Output
                │                ↓
                └───────→ Return to Landing
                         (via nav or back button)
```

### Quick Navigation

**From Any Page**:
- Click logo → Back to landing
- Browser back button → Previous page
- Direct URLs → Jump to specific module

**Deep Linking**:
- `?module=documents` → Auto-open Documents
- `?module=database` → Auto-open Database
- `?module=browser` → Auto-open Browser
- `?module=code_generation` → Auto-open Code Gen

---

## 📱 Responsive Design

All pages work on:
- ✅ Desktop (1920x1080+)
- ✅ Laptop (1366x768+)
- ✅ Tablet (768x1024+)
- ✅ Mobile (375x667+)

**Mobile Adaptations**:
- Hamburger menu for navigation
- Collapsible sidebars
- Touch-friendly buttons
- Responsive grids

---

## 🎓 Use Case Examples

### Example 1: Full-Stack Developer
```
Day 1:
1. Open Code IDE
2. Create FastAPI backend
3. Generate authentication endpoints
4. Generate database models
5. Write unit tests

Day 2:
1. Create React frontend
2. Generate dashboard components
3. Connect to API
4. Add charts and graphs

Total Time: 2 hours (vs 2 days manually)
```

### Example 2: Data Analyst
```
Workflow:
1. Upload quarterly report PDF (Document Analysis)
2. Ask: "What are the key findings?"
3. Get summary with extracted numbers
4. Switch to Database Q&A
5. Query: "Show revenue by product category"
6. Download CSV for Excel

Total Time: 5 minutes
```

### Example 3: QA Engineer
```
Testing:
1. Open Browser Automation
2. Enter: https://staging.myapp.com
3. "Fill login form and check dashboard"
4. Get automation script
5. "Take screenshot of results page"
6. Download automation log

Total Time: 2 minutes per test case
```

---

## 🔧 Troubleshooting

### Issue: Services Not Starting

**Solution**:
```bash
cd /home/deadbrainviv/Documents/GitHub/cogniware-core
./scripts/05_stop_services.sh  # Stop all
./scripts/04_start_services.sh # Start all
```

### Issue: Can't Login

**Check**:
1. Is Production API running?
   ```bash
   curl http://localhost:8090/health
   ```
2. Using correct credentials?
   - user / Cogniware@2025
   - admin / Admin@2025
3. Clear browser cache: Ctrl+Shift+Delete

### Issue: Module Not Loading

**Solutions**:
- Hard refresh: Ctrl+Shift+R
- Check browser console (F12)
- Verify all services running:
  ```bash
  curl http://localhost:8090/health  # Production
  curl http://localhost:8091/mcp/health  # MCP
  curl http://localhost:8000/  # Web
  ```

### Issue: AI Not Responding

**Check**:
1. LLM count shows "7 Interface + 2 Knowledge"?
2. Token valid? Try logout and login again
3. Network tab shows requests going through?

---

## 📖 Platform Features Summary

### ✨ What Makes CogniDream Special

| Feature | Description | Benefit |
|---------|-------------|---------|
| **Parallel LLM Processing** | Runs 2 Interface + 1 Knowledge LLMs simultaneously | 2.5x faster than sequential |
| **MCP Server** | Provides full context to LLMs | Better, context-aware code |
| **Production Ready** | Real extraction, no simulations | Actually usable outputs |
| **7 Project Templates** | FastAPI, React, Django, Flask, Express, Python CLI, Blank | Quick project setup |
| **Monaco Editor** | Same engine as VS Code | Professional editing |
| **Download Everything** | All outputs downloadable | Export and use anywhere |
| **Beautiful UI** | Modern gradients, animations | Professional look |
| **Real-Time Metrics** | See processing time, speedup, confidence | Transparency |
| **Chat Interface** | Conversational AI | Natural interaction |
| **Multi-Format** | 8+ document formats | Universal compatibility |

---

## 🗺️ Platform Map

### All URLs

**Main Entry Points**:
```
Landing Page:      http://localhost:8000/
Login:             http://localhost:8000/login.html
```

**User Modules**:
```
Code IDE:          http://localhost:8000/code-ide.html
AI Chat:           http://localhost:8000/user-portal-chat.html
Documents:         http://localhost:8000/user-portal-chat.html?module=documents
Database:          http://localhost:8000/user-portal-chat.html?module=database
Browser:           http://localhost:8000/user-portal-chat.html?module=browser
```

**Admin**:
```
Admin Portal:      http://localhost:8000/admin-portal-enhanced.html
```

**API Endpoints**:
```
Production API:    http://localhost:8090
MCP Server:        http://localhost:8091
Admin API:         http://localhost:8099
Business API:      http://localhost:8095
Business Protected: http://localhost:8096
Demo API:          http://localhost:8080
```

---

## 📊 Service Status

### Check All Services
```bash
echo "Production API:" && curl -s http://localhost:8090/health
echo "MCP Server:" && curl -s http://localhost:8091/mcp/health
echo "Web Server:" && curl -s http://localhost:8000/ | head -1
```

### Expected Output
```
Production API:
{"status": "healthy", "timestamp": ..., "version": "1.0.0-production"}

MCP Server:
{"status": "healthy", "service": "MCP Server"}

Web Server:
<!DOCTYPE html>
```

---

## 🎯 Recommended Workflow

### For First-Time Users

**Step 1**: Explore Landing Page (2 min)
- Read module descriptions
- Understand what each does
- Check "Why Choose CogniDream?" section

**Step 2**: Login (30 sec)
- Click "Get Started"
- Enter: user / Cogniware@2025
- Automatically return to landing

**Step 3**: Try Code IDE (5 min)
- Click "Code IDE" card
- Create new FastAPI project
- Browse generated files
- Ask AI to add features
- See code appear in editor

**Step 4**: Try Chat Assistant (3 min)
- Return to landing (browser back)
- Click "AI Chat" card
- Ask: "Generate a Python function for sorting"
- See parallel LLM processing
- Download generated code

**Step 5**: Try Document Analysis (3 min)
- Return to landing
- Click "Document Analysis" card
- Upload a PDF
- Ask question about it
- Get real analysis
- Download report

**Total**: 15 minutes to understand the entire platform!

---

## 💡 Tips & Tricks

### General
- **Hard Refresh**: Ctrl+Shift+R (clears cache)
- **Logout**: Available in chat portal sidebar
- **Navigate**: Use browser back button between modules
- **Deep Link**: Share URLs with ?module= parameter

### Code IDE
- **Save**: Ctrl+S (also auto-saves)
- **Find**: Ctrl+F
- **Multi-cursor**: Alt+Click
- **Toggle Terminal**: Ctrl+` (coming soon)
- **AI Generation**: Type in AI panel, Ctrl+Enter to send

### Chat Assistant
- **Examples**: Click "📚 Examples" button
- **Quick Send**: Press Enter in input
- **New Line**: Shift+Enter
- **Copy Output**: Click 📋 button
- **Download**: Click 💾 button

### Document Analysis
- **Upload First**: File must be uploaded before asking questions
- **Ask Specific**: More specific questions get better answers
- **Download**: Analysis report can be downloaded as .txt

---

## 🚀 Next Steps

After exploring the platform:

1. **Read Full Docs**:
   - `CODE_IDE_WITH_MCP.md` - Complete IDE guide
   - `PRODUCTION_DOCUMENT_PROCESSING.md` - Document analysis details
   - `UI_ENHANCEMENTS_APPLIED.md` - UI design details

2. **Create Your First Project**:
   - Use Code IDE
   - Choose appropriate template
   - Generate full application
   - Deploy it!

3. **Integrate with Your Workflow**:
   - Use Document Analysis for research
   - Use Database Q&A for data insights
   - Use Browser Automation for testing
   - Use Code IDE for development

4. **Explore Admin Portal** (if admin):
   - View analytics
   - Manage users
   - Monitor system performance

---

## 📚 Additional Resources

### Documentation Files
- `COMPLETE_PLATFORM_GUIDE.md` - This file (full navigation guide)
- `CODE_IDE_WITH_MCP.md` - IDE and MCP server documentation
- `CHAT_INTERFACE_COMPLETE.md` - Chat interface guide
- `PRODUCTION_DOCUMENT_PROCESSING.md` - Document processing details
- `UI_ENHANCEMENTS_APPLIED.md` - UI design documentation
- `DEFAULT_CREDENTIALS.md` - All login credentials
- `ALL_SERVERS_GUIDE.md` - Server configuration

### Scripts
- `./scripts/04_start_services.sh` - Start all services
- `./scripts/05_stop_services.sh` - Stop all services
- `./scripts/06_verify_deliverables.sh` - Verify installation

---

## ✅ Verification Checklist

Before using the platform, verify:

- [ ] All 7 services running
- [ ] Web server accessible (http://localhost:8000)
- [ ] Landing page loads correctly
- [ ] Can login successfully
- [ ] Code IDE accessible
- [ ] Chat interface works
- [ ] MCP server responding
- [ ] Production API healthy

**Run this**:
```bash
cd /home/deadbrainviv/Documents/GitHub/cogniware-core
./scripts/06_verify_deliverables.sh
```

---

## 🎉 You're Ready!

Open your browser:
```
http://localhost:8000
```

And start building with AI! 🚀

**Questions?** Check the documentation files or use the AI Chat Assistant! 🤖

---

## 🏆 Summary

You now have access to:

✅ **Unified Landing Page** - Central hub for all modules  
✅ **Code IDE** - Create entire projects with AI  
✅ **AI Chat** - Conversational assistant  
✅ **Document Analysis** - Real content extraction  
✅ **Database Q&A** - Natural language queries  
✅ **Browser Automation** - Web scraping  
✅ **Admin Portal** - System management  
✅ **MCP Server** - Context management  
✅ **Production Ready** - No simulations  
✅ **Beautiful UI** - Modern design  

**Enjoy building the future with CogniDream!** 🚀✨🤖

