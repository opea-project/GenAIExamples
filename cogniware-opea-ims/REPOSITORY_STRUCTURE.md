# 📁 COGNIWARE CORE - REPOSITORY STRUCTURE

**Version**: 2.0.0  
**Date**: October 19, 2025  
**Status**: ✅ **FULLY ORGANIZED**

---

## 🎯 CLEAN ROOT DIRECTORY

The root directory now contains ONLY essential files:

```
cogniware-core/
├── README.md                    ⭐ Main documentation (START HERE)
├── DEFAULT_CREDENTIALS.md        🔐 Default credentials (CRITICAL)
├── REPOSITORY_STRUCTURE.md       📁 This file
├── requirements.txt              📦 Python dependencies
├── config.json                   ⚙️  Configuration file
├── CMakeLists.txt               🔨 Build configuration
└── test_build.py                🧪 Build test script
```

**Total**: 7 essential files

---

## 📂 COMPLETE DIRECTORY STRUCTURE

```
cogniware-core/
│
├── 📄 README.md                           ⭐ Start here
├── 🔐 DEFAULT_CREDENTIALS.md              All login credentials
├── 📁 REPOSITORY_STRUCTURE.md             This file
├── 📦 requirements.txt                    Python dependencies
├── ⚙️  config.json                         Configuration
├── 🔨 CMakeLists.txt                      Build config
├── 🧪 test_build.py                       Build test
│
├── 📜 scripts/                            All automation scripts
│   ├── 00_master_setup.sh ⭐              Run everything
│   ├── 01_check_requirements.sh          Check dependencies
│   ├── 02_install_requirements.sh        Install dependencies
│   ├── 03_setup_services.sh              Setup and start services
│   ├── 04_start_services.sh              Start all services
│   ├── 05_stop_services.sh               Stop all services
│   ├── 06_verify_deliverables.sh         Verify installation
│   ├── 07_build.sh                       Build C++ engine
│   ├── 08_test_build.sh                  Test C++ build
│   ├── deploy.sh                         Production deployment
│   ├── start_all_services.sh             Alternative start script
│   ├── setup_demo_data.sh                Demo data setup
│   ├── installer.sh                      Legacy installer
│   └── ... (other utility scripts)
│
├── 🐍 python/                             Python source code
│   ├── api_server_admin.py               Admin API server
│   ├── api_server_production.py          Production API server
│   ├── api_server_business_protected.py  Business Protected API
│   ├── api_server_business.py            Business API
│   ├── api_server.py                     Demo API
│   ├── cogniware_llms.py ⭐              12 built-in LLMs
│   ├── parallel_llm_executor.py ⭐       Patent-compliant executor
│   ├── licensing_service.py              Licensing system
│   ├── natural_language_engine.py        NL processing
│   ├── llm_manager.py                    LLM management
│   ├── mcp_browser_automation.py         Browser automation
│   ├── document_processor_advanced.py    Document processing
│   ├── auth_middleware.py                Authentication
│   └── ... (other Python modules)
│
├── 🎨 ui/                                 User interface files
│   ├── login.html ⭐                      Login portal
│   ├── admin-portal-enhanced.html        Admin portal
│   ├── user-portal.html                  User portal
│   ├── admin-dashboard.html              Admin dashboard
│   ├── corporate-design-system.css ⭐    Design system
│   ├── shared-utilities.js ⭐            Shared JS utilities
│   ├── parallel-llm-visualizer.js ⭐     Parallel visualization
│   ├── llm-management.js                 LLM management UI
│   └── ... (other UI files)
│
├── 📚 docs/                               Documentation
│   ├── INDEX.md ⭐                        Documentation index
│   ├── DOCUMENTATION_ORGANIZED.md        Organization summary
│   ├── FINAL_DELIVERY_REPORT.md ⭐       Complete delivery
│   ├── guides/                           55+ user guides
│   │   ├── QUICK_START_GUIDE.md ⭐       Quick start
│   │   ├── USER_PERSONAS_GUIDE.md ⭐     7 user roles
│   │   ├── COGNIWARE_LLMS_GUIDE.md ⭐    LLM reference
│   │   ├── PARALLEL_LLM_EXECUTION_GUIDE.md ⭐ Patent system
│   │   ├── COMPLETE_DELIVERY_SUMMARY.md  Delivery summary
│   │   ├── DEPLOYMENT_GUIDE.md           Deployment
│   │   ├── USE_CASES_GUIDE.md            30+ use cases
│   │   ├── LICENSING_GUIDE.md            Licensing
│   │   ├── BUILD_GUIDE.md                Building
│   │   └── ... (46 more guides)
│   │
│   └── (24 technical specification files)
│
├── 🔌 api/                                API Collections
│   ├── Cogniware-Parallel-LLM-API.postman_collection.json ⭐
│   ├── Cogniware-Core-API.postman_collection.json
│   ├── Cogniware-Business-API.postman_collection.json
│   └── openapi.yaml                      OpenAPI spec
│
├── 🗄️  databases/                         Databases
│   ├── licenses.db                       Main database
│   ├── llms.db                           LLM metadata
│   └── test_db.db                        Test database
│
├── 📂 misc/                               Miscellaneous files
│   ├── docker/                           Docker files
│   │   ├── docker-compose.yml
│   │   ├── Dockerfile
│   │   ├── Dockerfile.cpu
│   │   └── Dockerfile.dev
│   ├── old-cmake/                        Old CMake files
│   │   ├── CMakeLists_simple.txt
│   │   └── CMakeLists_simple_engine.txt
│   ├── logs/                             Old log files
│   │   ├── admin_server.log
│   │   ├── business_server.log
│   │   ├── production_server.log
│   │   └── server.log
│   ├── install_dependencies.sh           Legacy installers
│   ├── install_dependencies.ps1
│   ├── setup.bat
│   ├── verify_deliverables.sh
│   ├── init-db.sql
│   └── libsimple_engine.so*
│
├── 📝 logs/                               Active logs
│   ├── admin.log
│   ├── production.log
│   ├── business-protected.log
│   ├── business.log
│   ├── demo.log
│   └── webserver.log
│
├── 🏗️  build/                             Build artifacts
│   └── (CMake build output)
│
├── 📦 models/                             LLM models
│   └── (Downloaded models)
│
├── 📄 documents/                          Document storage
│   └── (Uploaded documents)
│
├── 💾 projects/                           User projects
│   └── (User project data)
│
├── 🖼️  screenshots/                       Screenshots
│   └── (Browser automation screenshots)
│
├── 🧪 tests/                              Test files
│   └── (C++ test files)
│
├── 📥 examples/                           Example code
│   └── (Usage examples)
│
├── 🔧 include/                            C++ headers
│   └── (Header files)
│
├── 💻 src/                                C++ source
│   └── (C++ implementation)
│
├── 🐍 venv/                               Python virtual env
│   └── (Python packages)
│
└── ... (other supporting directories)
```

---

## 🎯 ESSENTIAL FILES (ROOT)

### 1. README.md
**Purpose**: Main platform documentation  
**Size**: ~1,010 lines  
**Contents**:
- Platform overview
- Quick start guide
- Feature list
- Installation instructions
- Default credentials
- API examples
- Links to all other documentation

**When to use**: First time setup, overview needed

### 2. DEFAULT_CREDENTIALS.md
**Purpose**: All login credentials and security info  
**Size**: ~800 lines  
**Contents**:
- Super administrator credentials
- Regular user credentials
- Password requirements
- Change password procedures
- Emergency access procedures
- Security best practices
- Account management

**When to use**: Need login credentials, password issues

### 3. REPOSITORY_STRUCTURE.md
**Purpose**: This file - explains repository organization  
**Contents**:
- Directory structure
- File locations
- Navigation guide

**When to use**: Understanding project layout

### 4. requirements.txt
**Purpose**: Python package dependencies  
**Contents**: List of required Python packages

**When to use**: Installing Python dependencies

### 5. config.json
**Purpose**: Platform configuration  
**Contents**:
- Server ports
- File paths
- Feature flags

**When to use**: Configuring the platform

### 6. CMakeLists.txt
**Purpose**: C++ build configuration  
**Contents**: CMake build instructions for C++ engine

**When to use**: Building C++ components

### 7. test_build.py
**Purpose**: Test C++ build  
**Contents**: Python script to verify C++ build

**When to use**: After building C++ engine

---

## 📜 SCRIPTS DIRECTORY

**Location**: `scripts/`  
**Total**: 15+ scripts

### Core Scripts (Use These)

**00_master_setup.sh** ⭐ **RUN THIS FOR COMPLETE SETUP**
- Runs all scripts in sequence
- Complete installation and verification
- Recommended for first-time setup

**01_check_requirements.sh**
- Checks system dependencies
- Verifies Python version
- Checks disk space and memory
- Reports missing components

**02_install_requirements.sh**
- Installs all dependencies
- Skip-if-exists logic
- Python packages
- Optional system packages

**03_setup_services.sh**
- Creates systemd services (if root)
- Starts all services
- Configures auto-start

**04_start_services.sh**
- Starts all 6 services
- Verifies they're running
- Shows access URLs

**05_stop_services.sh**
- Stops all services
- Clean shutdown

**06_verify_deliverables.sh**
- Verifies all components
- Tests services
- Checks files
- Reports success rate

**07_build.sh**
- Builds C++ engine
- Uses CMake

**08_test_build.sh**
- Tests C++ build
- Runs test suite

### Legacy Scripts

- deploy.sh - Full deployment (with systemd)
- start_all_services.sh - Alternative start script
- setup_demo_data.sh - Demo data setup
- installer.sh - Legacy installer

---

## 📚 DOCS DIRECTORY

**Location**: `docs/`  
**Total**: 80+ documents

### docs/INDEX.md
**Master index** of all documentation with:
- Navigation by category
- Navigation by user role
- Recommended reading order

### docs/guides/ (55 guides)

**Essential Guides**:
- QUICK_START_GUIDE.md - Get started in 5 min
- USER_PERSONAS_GUIDE.md - 7 user roles (1,783 lines)
- COGNIWARE_LLMS_GUIDE.md - 12 LLM models
- PARALLEL_LLM_EXECUTION_GUIDE.md - Patent system
- DEPLOYMENT_GUIDE.md - Production deployment
- USE_CASES_GUIDE.md - 30+ business use cases
- LICENSING_GUIDE.md - License management
- BUILD_GUIDE.md - Building from source

**Status & Summaries**:
- COMPLETE_DELIVERY_SUMMARY.md
- FINAL_PLATFORM_STATUS.md
- PLATFORM_ENHANCEMENTS_SUMMARY.md
- SERVICES_RUNNING.md
- ... (8 more)

**Technical Guides**:
- API_SERVER_GUIDE.md
- BUSINESS_API_GUIDE.md
- ENDPOINT_REFERENCE.md
- ... (5 more)

**Plus 35 more** specialized guides and references

### docs/ (24 technical specs)

- CORE_INFERENCE_ENGINE.md
- PARALLEL_LLM_EXECUTION_SYSTEM.md
- MULTI_LLM_ORCHESTRATION_SYSTEM.md
- PATENT_SPECIFICATION.md
- ... (20 more)

---

## 🎨 UI DIRECTORY

**Location**: `ui/`  
**Total**: 8 HTML files, 3 JS files, 1 CSS file

### HTML Files
- **login.html** ⭐ Corporate login portal
- **admin-portal-enhanced.html** - Super admin portal
- **user-portal.html** - User portal  
- **admin-dashboard.html** - Admin dashboard
- admin-portal.html - Original admin
- dashboard.html - Original dashboard
- index.html - Landing page

### CSS Files
- **corporate-design-system.css** ⭐ Complete design system

### JavaScript Files
- **shared-utilities.js** ⭐ 50+ utility functions
- **parallel-llm-visualizer.js** ⭐ Parallel visualization
- **llm-management.js** - LLM management UI
- admin-portal-enhanced.js - Admin portal logic

---

## 🐍 PYTHON DIRECTORY

**Location**: `python/`  
**Total**: 28 Python files

### Core API Servers (5)
- api_server_admin.py (8099) - Admin operations
- api_server_production.py (8090) - Production with GPU
- api_server_business_protected.py (8096) - Protected business
- api_server_business.py (8095) - Legacy business
- api_server.py (8080) - Demo server

### LLM System ⭐
- **cogniware_llms.py** - 12 LLM definitions
- **parallel_llm_executor.py** - Patent-compliant executor
- **natural_language_engine.py** - NL processing
- **llm_manager.py** - LLM management

### Core Services
- licensing_service.py - Licensing and users
- auth_middleware.py - Authentication
- mcp_browser_automation.py - Browser automation
- document_processor_advanced.py - Document processing

### Supporting Files
- cogniware_api.py, cognidream_api.py, etc.

---

## 🔌 API DIRECTORY

**Location**: `api/`  
**Total**: 4 files

- **Cogniware-Parallel-LLM-API.postman_collection.json** ⭐ NEW
  - 30+ parallel LLM requests
  - 8 organized folders
  - All strategies covered

- Cogniware-Core-API.postman_collection.json
  - Core API requests

- Cogniware-Business-API.postman_collection.json
  - Business API requests

- openapi.yaml
  - OpenAPI specification

---

## 🗄️ DATA DIRECTORIES

### databases/
- licenses.db - Main database (users, orgs, licenses)
- llms.db - LLM metadata
- test_db.db - Test database

### models/
- Downloaded LLM models (when imported)

### documents/
- User-uploaded documents

### projects/
- User project data

### logs/
- admin.log, production.log, etc.
- Active service logs

---

## 🏗️ BUILD DIRECTORIES

### build/
- CMake build output
- Compiled libraries
- Test executables

### build_simple/
- Simple build output

### build_simple_engine/
- Engine build output

---

## 📦 MISC DIRECTORY

**Location**: `misc/`  
**Purpose**: Non-essential files kept for reference

### misc/docker/
- docker-compose.yml
- Dockerfile variants
- Container configs

### misc/old-cmake/
- Old CMakeLists variants
- Legacy build files

### misc/logs/
- Old log files
- Historical logs

### misc/ (root files)
- Legacy installers
- Old setup scripts
- Library files
- SQL scripts

---

## 🧭 NAVIGATION GUIDE

### Finding What You Need

**Need to**:
- **Get started?** → README.md
- **Login?** → DEFAULT_CREDENTIALS.md
- **Install?** → scripts/00_master_setup.sh
- **Find docs?** → docs/INDEX.md
- **API reference?** → api/*.postman_collection.json
- **Understand layout?** → This file (REPOSITORY_STRUCTURE.md)

### By Task

**Installation**:
1. scripts/00_master_setup.sh (complete setup)
2. OR scripts/01_check_requirements.sh → 02 → 03 → 04

**Development**:
1. README.md (overview)
2. docs/guides/BUILD_GUIDE.md (building)
3. scripts/07_build.sh (build command)

**Usage**:
1. DEFAULT_CREDENTIALS.md (login)
2. http://localhost:8000/login.html (web portal)
3. docs/guides/USER_PERSONAS_GUIDE.md (features)

**Documentation**:
1. docs/INDEX.md (find anything)
2. docs/guides/ (browse all)
3. README.md (links to key docs)

---

## 📊 STATISTICS

### Directory Counts

| Directory | Files | Purpose |
|-----------|-------|---------|
| **Root** | 7 | Essential only |
| **scripts/** | 15+ | Automation |
| **python/** | 28 | Source code |
| **ui/** | 12 | User interface |
| **docs/** | 80+ | Documentation |
| **api/** | 4 | API collections |
| **misc/** | 20+ | Archives |

### File Type Distribution

- **Python**: ~30 files
- **JavaScript**: ~5 files
- **HTML**: ~8 files
- **CSS**: ~2 files
- **Markdown**: ~80 files
- **JSON**: ~4 files
- **Shell Scripts**: ~15 files
- **C++**: ~200 files (in src/)
- **Headers**: ~80 files (in include/)

**Total Source Files**: ~400+

---

## ✅ CLEANUP ACCOMPLISHED

### Removed from Root

✅ **56 documentation files** → Moved to `docs/guides/`  
✅ **6 shell scripts** → Moved to `scripts/`  
✅ **4 Docker files** → Moved to `misc/docker/`  
✅ **2 old CMake files** → Moved to `misc/old-cmake/`  
✅ **5 log files** → Moved to `misc/logs/`  
✅ **3 legacy installers** → Moved to `misc/`  
✅ **Library files** → Moved to `misc/`  

**Total cleaned**: 77 files

### Kept in Root (7 essential files)

✅ README.md - Main docs  
✅ DEFAULT_CREDENTIALS.md - Credentials  
✅ REPOSITORY_STRUCTURE.md - This file  
✅ requirements.txt - Python deps  
✅ config.json - Configuration  
✅ CMakeLists.txt - Build config  
✅ test_build.py - Build test  

---

## 🚀 QUICK START COMMANDS

### Complete Setup

```bash
# Run master setup script
./scripts/00_master_setup.sh
```

### Manual Setup

```bash
# 1. Check requirements
./scripts/01_check_requirements.sh

# 2. Install dependencies
./scripts/02_install_requirements.sh

# 3. Setup and start services
./scripts/03_setup_services.sh

# 4. Verify installation
./scripts/06_verify_deliverables.sh
```

### Daily Operations

```bash
# Start services
./scripts/04_start_services.sh

# Stop services
./scripts/05_stop_services.sh

# Check status
./scripts/06_verify_deliverables.sh
```

---

## 📖 DOCUMENTATION STRUCTURE

### Three-Tier System

**Tier 1: Root (Essential)**
- README.md - First stop
- DEFAULT_CREDENTIALS.md - Critical info

**Tier 2: Index (Navigation)**
- docs/INDEX.md - Find anything

**Tier 3: Guides (Detailed)**
- docs/guides/*.md - Complete information

### Finding Information

```
Question: "How do I install?"
Answer: README.md → Quick Start section
        OR docs/guides/QUICK_START_GUIDE.md

Question: "What are the login credentials?"
Answer: DEFAULT_CREDENTIALS.md

Question: "How do parallel LLMs work?"
Answer: docs/guides/PARALLEL_LLM_EXECUTION_GUIDE.md

Question: "Where is X documented?"
Answer: docs/INDEX.md → search for X
```

---

## 🎓 BEST PRACTICES

### For Developers

1. **Keep root clean**: Add new files to appropriate subdirectories
2. **Update INDEX.md**: When adding new documentation
3. **Use scripts**: Don't run commands manually
4. **Follow structure**: Put files in correct locations

### For Documentation

1. **New guides** → `docs/guides/`
2. **Technical specs** → `docs/`
3. **Update INDEX.md** → Add to catalog
4. **Link from README** → If essential

### For Code

1. **Python** → `python/`
2. **JavaScript** → `ui/`
3. **C++** → `src/` and `include/`
4. **Tests** → `tests/`

### For Scripts

1. **All scripts** → `scripts/`
2. **Make executable**: `chmod +x`
3. **Number sequentially**: For execution order
4. **Document**: Add header comments

---

## 🎊 BENEFITS OF NEW STRUCTURE

### Before Organization

❌ 56 docs in root - cluttered  
❌ Scripts scattered  
❌ Hard to find files  
❌ Confusing layout  
❌ No clear entry point  

### After Organization

✅ 7 essential files in root - clean  
✅ All scripts in `scripts/` - organized  
✅ All docs in `docs/` - structured  
✅ Easy navigation with INDEX  
✅ Clear entry points (README, DEFAULT_CREDENTIALS)  
✅ Professional structure  

---

## 📞 SUPPORT

**Can't find something?**

1. Check `docs/INDEX.md`
2. Search: `grep -r "search term" docs/`
3. Read `README.md`
4. Email: support@cogniware.com

---

## ✨ SUMMARY

✅ **Root directory cleaned**: 77 files → 7 essential files  
✅ **Scripts organized**: 15+ scripts in `scripts/`  
✅ **Docs organized**: 80+ docs in `docs/`  
✅ **Misc archived**: Non-essential files in `misc/`  
✅ **Clear structure**: Professional repository layout  
✅ **Easy navigation**: INDEX.md + README.md  
✅ **All replacements done**: msmartcompute → cogniware  

**Repository is now clean, organized, and professional!**

---

**© 2025 Cogniware Incorporated - All Rights Reserved**

*Repository Reorganized: October 19, 2025*  
*Structure Version: 2.0*  
*Cleanliness: Professional Grade*

