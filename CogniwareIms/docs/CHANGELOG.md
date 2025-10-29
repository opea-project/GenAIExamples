# Changelog

All notable changes to the Cogniware OPEA IMS project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Security

#### Fixed
- **aiohttp updated to 3.10.10** - Resolves multiple high and critical vulnerabilities:
  - Directory traversal vulnerability (GHSA-5h86-8mv2-jq9f) - High
  - DoS via malformed POST requests (GHSA-5m98-qgg9-wh84) - High
  - HTTP parser leniency issues (GHSA-8qpw-xqxj-h4r2) - Moderate
  - XSS on static file index pages - Moderate

#### Updated Security Dependencies
- `fastapi`: 0.104.1 → 0.115.0
- `uvicorn[standard]`: 0.24.0 → 0.31.0
- `python-multipart`: 0.0.6 → 0.0.12
- `bcrypt`: 4.1.1 → 4.2.0
- `cryptography`: 41.0.7 → 43.0.1
- `httpx`: 0.25.2 → 0.27.2

#### Documented
- **python-jose 3.3.0** - Critical vulnerabilities documented with migration plan to PyJWT
  - Algorithm confusion (GHSA-6c5p-j8vq-pqhj) - Critical
  - DoS via compressed JWE (GHSA-cjwg-qfpm-7377) - Moderate
  - Migration guide created in `SECURITY_UPDATES.md`
  - Follow-up PR planned for PyJWT migration

### Changed

#### Data Handling
- **BREAKING**: Sample data files (7,479 CSV, ~32MB) now **excluded from Git repository**
  - Per OPEA guidelines to maintain manageable repository size
  - Data must be downloaded separately before first use
  - See `DATA_SETUP.md` for instructions

#### Updated Dependencies

**Database**:
- `sqlalchemy`: 2.0.23 → 2.0.35
- `psycopg2-binary`: 2.9.9 → 2.9.10
- `alembic`: 1.12.1 → 1.13.3

**Caching**:
- `redis`: 5.0.1 → 5.2.0
- `hiredis`: 2.2.3 → 3.0.0

**Data Processing**:
- `pandas`: 2.1.3 → 2.2.3
- `numpy`: 1.26.2 → 2.1.2
- `openpyxl`: 3.1.2 → 3.1.5
- `python-docx`: 1.1.0 → 1.1.2

**Validation**:
- `pydantic`: 2.5.2 → 2.9.2
- `pydantic-settings`: 2.1.0 → 2.5.2
- `email-validator`: 2.1.0 → 2.2.0

**Utilities**:
- `python-dotenv`: 1.0.0 → 1.0.1
- `PyYAML`: 6.0.1 → 6.0.2

**AI/ML**:
- `scikit-learn`: 1.3.2 → 1.5.2

**Testing**:
- `pytest`: 7.4.3 → 8.3.3
- `pytest-asyncio`: 0.21.1 → 0.24.0
- `pytest-cov`: 4.1.0 → 6.0.0

**Code Quality**:
- `black`: 23.11.0 → 24.10.0
- `flake8`: 6.1.0 → 7.1.1
- `mypy`: 1.7.1 → 1.11.2

### Added

#### Documentation
- **`SECURITY_UPDATES.md`** - Comprehensive security vulnerability tracking
  - Complete CVE descriptions and fixes
  - Migration guide: python-jose → PyJWT
  - Testing requirements and compliance status
  - Additional security best practices

- **`DATA_SETUP.md`** - Complete data download and setup guide
  - Quick start and detailed instructions
  - Automated and manual download options
  - Data hosting guide for maintainers
  - Custom data instructions
  - Comprehensive troubleshooting and FAQ

- **`data/README.md`** - Data directory documentation
  - Data structure and file listing
  - Download instructions
  - Usage in application
  - Troubleshooting tips

- **`PR_REVIEW_RESPONSE.md`** - Detailed response to OPEA PR review
  - Issue tracking and resolution
  - Testing performed
  - Migration timeline

- **`PR_COMMENT_RESPONSE.md`** - Concise PR comment for GitHub

- **`CHANGELOG.md`** - This file

#### Scripts
- **`scripts/download-data.sh`** - Automated data download script
  - Dependency checking (curl/wget, tar)
  - Download with progress indication
  - SHA-256 checksum verification
  - Error handling and recovery
  - User-friendly colored output
  - Support for multiple hosting services

#### Configuration
- **`data/.gitkeep`** - Ensures data directory tracked in Git

### Modified

#### Configuration Files
- **`.gitignore`** - Added data directory exclusion
  ```gitignore
  # Data files - Download separately (see DATA_SETUP.md)
  data/
  !data/.gitkeep
  !data/README.md
  ```

- **`backend/requirements.txt`** - All 28 dependencies updated to latest stable versions

#### Documentation Updates
- **`README.md`** - Enhanced Quick Start section
  - Added Step 1: Download Sample Data
  - Prominent warning about data requirement
  - Updated documentation links
  - Added `SECURITY_UPDATES.md` reference

### Migration Guide

#### For New Users

```bash
# New workflow with data download
git clone [repository]
cd cogniware-opea-ims
./scripts/download-data.sh  # NEW: Required step
./start.sh
```

#### For Existing Users

```bash
# If you have existing data directory, no action needed
# The data directory is now in .gitignore

# To update dependencies:
docker-compose down
docker-compose pull
docker-compose up -d --build
```

#### For Maintainers Preparing Data Release

```bash
# Create data archive
tar -czf sample-data.tar.gz data/

# Generate checksum
sha256sum sample-data.tar.gz > sample-data.sha256

# Upload to GitHub Releases or cloud storage
# Update DATA_URL in scripts/download-data.sh
```

---

## [1.0.0] - 2025-10-13 (Initial Release)

### Added
- Complete AI-powered inventory management system
- OPEA GenAI microservices integration
- Intel Xeon processor optimizations
- Multi-format file upload support
- Natural language query capabilities
- DBQnA agent for NL-to-SQL conversion
- Document summarization service
- Interactive conversational AI agent
- Real-time analytics and forecasting
- Enterprise-grade security features
- Full Docker containerization
- Production-ready deployment
- Comprehensive documentation

### OPEA Components Used
- Embedding Service (BAAI/bge-base-en-v1.5)
- Retrieval Service (Redis vector store)
- LLM Service (Intel/neural-chat-7b-v3-3)
- ChatQnA Gateway

### Technology Stack
- **Backend**: FastAPI, Python 3.11
- **Frontend**: Next.js 14, React 18, TypeScript
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Containerization**: Docker, Docker Compose
- **Platform**: Intel Xeon (CPU-only, no GPU required)

### Sample Data
- 7,479 CSV files with Intel product specifications
- Categories: Processors, FPGAs, server components, storage, networking
- Total size: ~32 MB

---

## Release Notes

### Version Numbering

- **Major version** (1.x.x) - Breaking changes, major features
- **Minor version** (x.1.x) - New features, backward compatible
- **Patch version** (x.x.1) - Bug fixes, security updates

### Support

- **Current version**: 1.0.0 (initial release)
- **Next planned**: 1.1.0 (python-jose migration, additional features)
- **Security updates**: Applied as needed to all supported versions

### Links

- **GitHub**: [Cogniware OPEA IMS](https://github.com/Cogniware-Inc/cogniware-opea-ims)
- **OPEA Project**: [opea-project/GenAIExamples](https://github.com/opea-project/GenAIExamples)
- **Documentation**: See `docs/` directory
- **Issues**: GitHub Issues
- **Security**: security@cogniware.com

---

*Changelog follows [Keep a Changelog](https://keepachangelog.com/) format*
*Last Updated: October 17, 2025*


