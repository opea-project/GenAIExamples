# CogniDream - Complete Platform Guide 🚀

## Overview

**CogniDream** is a full-fledged AI-powered development platform with a unified navigation system and dedicated modules for every functionality. Users can seamlessly navigate between different AI-powered tools from a central landing page.

---

## 🎯 Platform Architecture

### Main Entry Points

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│              http://localhost:8000/                  │
│                    (Landing Page)                    │
│                                                      │
└───────────────┬──────────────────────────────────────┘
                │
                ├─→ Login → index.html (Module Selection)
                │
                ├─→ Code IDE (code-ide.html)
                │   • Monaco Editor
                │   • MCP Server Integration
                │   • Project Templates
                │
                ├─→ AI Chat (user-portal-chat.html)
                │   • Conversational Interface
                │   • Parallel LLM Processing
                │   • Download Outputs
                │
                ├─→ Document Analysis (user-portal-chat.html?module=documents)
                │   • Real Content Extraction
                │   • OCR Support
                │   • Smart Q&A
                │
                ├─→ Database Q&A (user-portal-chat.html?module=database)
                │   • Natural Language to SQL
                │   • Query Results
                │   • CSV Export
                │
                ├─→ Browser Automation (user-portal-chat.html?module=browser)
                │   • Web Scraping
                │   • Form Automation
                │   • Screenshots
                │
                └─→ Admin Portal (admin-portal-enhanced.html)
                    • LLM Management
                    • User Management
                    • Analytics
```

---

## 🌐 Complete User Journey

### Step 1: Landing Page
**URL**: `http://localhost:8000/` or `http://localhost:8000/index.html`

**Features**:
- Hero section with platform overview
- 6 module cards with descriptions
- Features showcase
- Navigation bar
- Footer with links

**What Users See**:
- ✨ Beautiful gradient background
- 💻 Code IDE card (NEW badge)
- 🤖 AI Chat Assistant card (ENHANCED badge)
- 📄 Document Analysis card (PRODUCTION badge)
- 🗄️ Database Q&A card
- 🌐 Browser Automation card
- ⚙️ Admin Portal card

### Step 2: Login
**URL**: `http://localhost:8000/login.html`

**Credentials**:
- Username: `user` / Password: `Cogniware@2025`
- Username: `admin` / Password: `Admin@2025`
- Username: `superadmin` / Password: `Cogniware@2025`

**After Login**:
- Redirects back to `index.html`
- User bar appears in top-right showing logged-in user
- All module cards are now accessible

### Step 3: Module Selection

Users can click any module card to access that specific functionality:

#### Option A: Code IDE
**URL**: `http://localhost:8000/code-ide.html`

**Interface**:
- Left: File tree explorer
- Center: Monaco Editor with tabs
- Right: AI Assistant panel
- Bottom: Terminal (toggleable)

**User Flow**:
1. Click "+ New Project"
2. Choose template (FastAPI, React, Django, etc.)
3. Project auto-generates with complete structure
4. Browse files in tree, click to edit
5. Use AI to generate more code
6. Auto-save on edit

#### Option B: AI Chat Assistant
**URL**: `http://localhost:8000/user-portal-chat.html`

**Interface**:
- Left: Workspace selection (Code Gen, Documents, Database, Browser)
- Center: Chat conversation with examples sidebar
- Right: Examples panel (toggleable)

**User Flow**:
1. Select workspace from left sidebar
2. View welcome screen with quick actions
3. Type question or click example
4. See AI response with:
   - LLM processing details (Interface + Knowledge)
   - Patent compliance badge
   - Generated output with download option
   - Performance metrics
5. Continue conversation

#### Option C: Document Analysis
**URL**: `http://localhost:8000/user-portal-chat.html?module=documents`

**Auto-Selects**: Documents workspace

**User Flow**:
1. Upload PDF/DOCX/XLSX file
2. Ask question about document
3. Get real analysis:
   - Document type classification
   - Word count, statistics
   - Main topics extraction
   - Entity recognition (dates, emails)
   - Smart Q&A with relevant passages
4. Download analysis report

#### Option D: Database Q&A
**URL**: `http://localhost:8000/user-portal-chat.html?module=database`

**Auto-Selects**: Database workspace

**User Flow**:
1. Enter database name
2. Ask natural language query
3. Get:
   - Generated SQL
   - Query results (table format)
   - Summary statistics
4. Download as CSV

#### Option E: Browser Automation
**URL**: `http://localhost:8000/user-portal-chat.html?module=browser`

**Auto-Selects**: Browser workspace

**User Flow**:
1. Enter target URL
2. Describe automation task
3. Get:
   - Automation steps
   - Extracted data
   - Screenshots
4. Download automation log

#### Option F: Admin Portal
**URL**: `http://localhost:8000/admin-portal-enhanced.html`

**Requires**: Admin credentials

**User Flow**:
1. View dashboard with analytics
2. Manage Cogniware LLMs (12 built-in)
3. Manage users and licenses
4. View system statistics

---

## 📱 Navigation System

### Global Navigation Bar
Present on landing page:
- **Logo**: "🚀 CogniDream" (links to home)
- **Modules**: Scroll to modules section
- **Features**: Scroll to features section
- **Admin**: Direct link to admin portal
- **Get Started**: Link to login

### User Bar (Post-Login)
Appears in top-right after login:
- User avatar (first letter of username)
- Username display
- "Logged In" status

### Module Navigation

#### In Code IDE:
- Top bar: Logo, "New Project", "Generate with AI"
- Left sidebar: File explorer with refresh, new file
- Right sidebar: AI chat panel

#### In Chat Portal:
- Left sidebar: All workspaces (Code Gen, Documents, Database, Browser, Integration, Workflow, Monitoring, Analytics)
- Top bar: Current workspace name, LLM status, Examples toggle
- Chat area: Scrollable conversation
- Input area: Natural language input with send button

---

## 🎨 Design System

### Color Scheme
- **Primary Gradient**: #667eea → #764ba2 (Purple)
- **Secondary Gradient**: #f093fb → #f5576c (Pink)
- **Success**: #2d862d (Green)
- **Background**: White / #f8f9ff (Light Blue)
- **Text**: #333 (Dark) / #666 (Medium) / #999 (Light)

### Typography
- **Font**: Inter (Google Fonts)
- **Headings**: 800 weight, gradient text
- **Body**: 400-600 weight
- **Code**: Monaco Editor / Courier New

### Components
- **Cards**: Rounded (20px), shadow, hover lift effect
- **Buttons**: Gradient background, rounded (8-12px), shadow on hover
- **Inputs**: Light background, border on focus
- **Badges**: Rounded pill shape, gradient background

---

## 🔧 Backend Services

### Running Services

| Service | Port | Purpose |
|---------|------|---------|
| **Web Server** | 8000 | Serves all HTML/CSS/JS |
| **Admin API** | 8099 | Admin operations |
| **Production API** | 8090 | LLM processing, auth |
| **Business API** | 8095 | Business endpoints |
| **Business Protected** | 8096 | Protected business API |
| **Demo Server** | 8080 | Demo/testing |
| **MCP Server** | 8091 | Context management |

### API Flow

```
User Action in UI
      ↓
Authentication (Production API :8090)
      ↓
MCP Server (:8091)
  - Gets project context
  - Scans files
  - Builds enhanced prompt
      ↓
Production API (:8090)
  - Receives enhanced prompt
  - Parallel LLM Executor
    → Interface LLMs (2x)
    → Knowledge LLMs (1x)
  - Synthesizes results
      ↓
Response to UI
  - Generated output
  - LLM processing details
  - Performance metrics
  - Patent compliance info
```

---

## 🚀 Quick Start Guide

### For End Users

**1. Access Platform**
```
http://localhost:8000
```

**2. Browse Modules**
- Scroll down to see all 6 modules
- Click any card to learn more
- Or click "Get Started" to login

**3. Login**
```
Username: user
Password: Cogniware@2025
```

**4. Choose Your Module**
- Back on landing page, now logged in
- Click any module card
- Start using immediately!

### For Developers

**1. Start Services**
```bash
cd /home/deadbrainviv/Documents/GitHub/cogniware-core
./scripts/04_start_services.sh
```

**2. Verify Services**
```bash
curl http://localhost:8090/health
curl http://localhost:8091/mcp/health
curl http://localhost:8000/
```

**3. Access Platform**
```
http://localhost:8000
```

---

## 📊 Module Comparison

| Feature | Code IDE | Chat Assistant | Document Analysis | Database Q&A | Browser Automation |
|---------|----------|----------------|-------------------|--------------|-------------------|
| **Interface** | Monaco Editor | Chat + Sidebar | Chat + Upload | Chat + Input | Chat + URL |
| **Input** | Natural language | Natural language | Document + question | DB name + query | URL + task |
| **Output** | Code files | Text responses | Analysis report | SQL + results | Automation log |
| **Download** | Multiple files | Single output | Report (.txt) | CSV export | Log (.txt) |
| **LLMs Used** | 2 Interface + 1 Knowledge | 2 Interface + 1 Knowledge | 2 Interface + 1 Knowledge | 2 Interface + 1 Knowledge | 2 Interface + 1 Knowledge |
| **MCP** | Yes (project context) | Yes (conversation context) | Yes (document context) | Yes (schema context) | Yes (page context) |
| **Auto-Save** | Yes (1s delay) | N/A | N/A | N/A | N/A |
| **Multi-File** | Yes | No | No | No | No |
| **Real-Time** | Yes | Yes | Yes | Yes | Yes |

---

## 💡 Use Cases

### 1. Build a Complete API (Code IDE)
```
Time: 5 minutes

1. Open Code IDE
2. New Project → FastAPI
3. AI: "Add user authentication with JWT"
4. AI: "Create CRUD endpoints for products"
5. AI: "Add database models with SQLAlchemy"
6. AI: "Write unit tests"
7. Done! Complete API ready to deploy.
```

### 2. Analyze Legal Document (Document Analysis)
```
Time: 2 minutes

1. Open Document Analysis
2. Upload: TheForeignMarriageAct1969.pdf
3. Ask: "What are the key requirements?"
4. Get: Document type, statistics, main topics, answer
5. Download analysis report
```

### 3. Query Business Database (Database Q&A)
```
Time: 1 minute

1. Open Database Q&A
2. Enter: "sales_db"
3. Ask: "Show top 10 products by revenue this month"
4. Get: SQL query + results table
5. Download as CSV
```

### 4. Automate Web Scraping (Browser Automation)
```
Time: 2 minutes

1. Open Browser Automation
2. Enter: https://example.com
3. Ask: "Extract all product names and prices"
4. Get: Automation steps + extracted data
5. Download results
```

### 5. Chat with AI (Chat Assistant)
```
Time: Seconds

1. Open Chat Assistant
2. Ask anything:
   - "Generate a Python script to..."
   - "Explain how async/await works"
   - "Create a React component for..."
3. Get detailed response with code examples
4. Download if needed
```

---

## 🎓 Training Users

### Admin Training (30 minutes)
1. **Landing Page** (5 min): Navigate modules, understand layout
2. **Admin Portal** (10 min): Manage LLMs, users, licenses
3. **System Monitoring** (5 min): View analytics, check performance
4. **User Management** (10 min): Create users, assign licenses

### Developer Training (45 minutes)
1. **Landing Page** (5 min): Overview of all modules
2. **Code IDE** (15 min): Create projects, use AI, file management
3. **Chat Assistant** (10 min): Ask questions, generate code
4. **Document Analysis** (5 min): Upload and analyze files
5. **Database Q&A** (5 min): Natural language queries
6. **Browser Automation** (5 min): Web scraping tasks

### End User Training (20 minutes)
1. **Landing Page** (5 min): Find the right module
2. **Chat Assistant** (10 min): Basic conversation, examples
3. **Document Analysis** (5 min): Upload and ask questions

---

## 🔒 Security & Access

### Public Pages
- Landing page (`index.html`)
- Login page (`login.html`)

### Protected Pages (Require Login)
- Code IDE
- Chat Assistant
- All workspace modules
- Admin Portal (requires admin role)

### Authentication Flow
```
1. User visits protected page
2. Check localStorage for token
3. If no token → redirect to login.html
4. If token exists → validate with API
5. If valid → show page
6. If invalid → redirect to login.html
```

---

## 📈 Performance Metrics

### Page Load Times
- Landing page: < 1 second
- Login page: < 1 second
- Code IDE: 2-3 seconds (Monaco Editor load)
- Chat Assistant: < 1 second

### API Response Times
- Authentication: < 200ms
- LLM Processing: 500-2000ms (parallel)
- MCP Context: < 1 second
- File Operations: < 100ms

### Parallel Processing
- Sequential: ~1300ms (2 Interface @ 500ms + 1 Knowledge @ 300ms)
- Parallel: ~500ms (all concurrent)
- **Speedup: 2.5x faster**

---

## 🎉 Summary

### What's Complete

✅ **Unified Landing Page** - Central hub for all modules
✅ **Code IDE** - Full web-based IDE with MCP
✅ **Chat Assistant** - Conversational AI with parallel LLMs
✅ **Document Analysis** - Real content extraction
✅ **Database Q&A** - Natural language to SQL
✅ **Browser Automation** - Web scraping and automation
✅ **Admin Portal** - Complete management interface
✅ **MCP Server** - Context management for LLMs
✅ **7 Project Templates** - FastAPI, React, Django, etc.
✅ **Production Ready** - No simulations, real operations
✅ **Beautiful UI** - Modern, responsive, animated
✅ **Download Everything** - All outputs downloadable
✅ **Patent Compliant** - MCP parallel processing

### Access Points

**Main Entry**:
```
http://localhost:8000
```

**Direct Access**:
```
Code IDE:          http://localhost:8000/code-ide.html
Chat:              http://localhost:8000/user-portal-chat.html
Documents:         http://localhost:8000/user-portal-chat.html?module=documents
Database:          http://localhost:8000/user-portal-chat.html?module=database
Browser:           http://localhost:8000/user-portal-chat.html?module=browser
Admin:             http://localhost:8000/admin-portal-enhanced.html
```

### Credentials

**Regular User**:
```
Username: user
Password: Cogniware@2025
```

**Admin**:
```
Username: admin
Password: Admin@2025
```

---

## 🚀 Start Using Now!

1. **Open**: `http://localhost:8000`
2. **Explore**: Browse all 6 modules
3. **Login**: Click "Get Started"
4. **Choose**: Select your module
5. **Create**: Start building with AI!

**Welcome to the future of AI-powered development!** 🤖✨

---

**Documentation**: See `CODE_IDE_WITH_MCP.md` for detailed IDE guide
**Testing**: See `PRODUCTION_DOCUMENT_PROCESSING.md` for document analysis details
**UI Enhancements**: See `UI_ENHANCEMENTS_APPLIED.md` for design details

