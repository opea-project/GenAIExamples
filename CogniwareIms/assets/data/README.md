# Sample Data for Cogniware OPEA IMS

## Overview

This directory contains sample CSV data files for the Cogniware OPEA Inventory Management System demonstration.

## Data Files Not Included in Repository

**Important**: The actual data files are **not included** in the Git repository to keep the repo size manageable per OPEA project guidelines.

- **Total Files**: 7,479 CSV files
- **Total Size**: ~32 MB
- **File Types**: Product specifications and ordering information

## Download Instructions

### Option 1: Automated Download (Recommended)

Run the download script from the project root:

```bash
./scripts/download-data.sh
```

This script will:
- Check for required dependencies
- Download the data files from the hosting service
- Verify data integrity (checksum)
- Extract files to this directory
- Provide summary statistics

### Option 2: Manual Download

1. **Download the data archive**:
   - Repository: [Cogniware-OPEA-IMS-Data](https://github.com/Cogniware-Inc/Cogniware-OPEA-IMS-Data)
   - Direct Download: `https://github.com/Cogniware-Inc/Cogniware-OPEA-IMS-Data/archive/refs/heads/main.zip`
   - Alternative: Contact Cogniware for data access

2. **Extract to this directory**:
   ```bash
   cd /path/to/cogniware-opea-ims
   unzip main.zip
   cp -r Cogniware-OPEA-IMS-Data-main/data/* data/
   rm -rf Cogniware-OPEA-IMS-Data-main main.zip
   ```

3. **Verify file count**:
   ```bash
   find data/ -type f -name "*.csv" | wc -l
   # Should show: 7479
   ```

## Data Structure

The CSV files contain Intel product information:

### File Naming Convention
```
[Product Name]_[Type].csv
```

**Examples**:
- `Intel® Xeon® Processor E5-4660 v3_spec.csv` - Specifications
- `Intel® Core™ i7-13700K Processor_ordering.csv` - Ordering info

### Product Categories

- **Processors**: Intel® Xeon®, Core™, Celeron®, Pentium®
- **FPGAs**: Stratix®, Arria®, Cyclone®, MAX®, Agilex®
- **Server Components**: Chassis, compute modules, RAID controllers
- **Storage**: SSDs, RAID batteries, drive cages
- **Networking**: Network adapters, switches
- **Accessories**: Brackets, cables, cooling solutions

### CSV Structure

Each CSV typically contains:
- Product name and model number
- Technical specifications
- Performance metrics
- Ordering information
- Package details

## Data Usage

### In the Application

The data is used for:

1. **Knowledge Base Population**: CSV files are processed and indexed
2. **Natural Language Queries**: Users can ask questions about products
3. **Inventory Simulation**: Demo inventory management scenarios
4. **DBQnA Agent Training**: NL-to-SQL conversion examples

### Example Queries

Once data is loaded, try:
- "What are the specs for Xeon E5 processors?"
- "Show me all FPGAs in the database"
- "Compare Intel Core i7 13th and 14th generation"
- "What server chassis are available?"

## Data Updates

### Current Version
- **Version**: 1.0.0
- **Date**: October 2025
- **Files**: 7,479 CSV files
- **Source**: Intel product specifications

### Future Updates

Data updates will be released as:
- New product additions
- Specification updates
- Additional product categories

Check the [Cogniware website](https://cogniware.com) for updates.

## Data License

The sample data includes:
- Intel® product specifications (public information)
- Product ordering information (public information)

**Note**: This is demonstration data. For production use, always verify with official Intel sources.

## Troubleshooting

### Data Download Issues

**Problem**: Download script fails
```bash
# Check internet connection
ping -c 3 google.com

# Check available disk space
df -h .

# Try manual download
curl -L -O [DATA_URL]
```

**Problem**: Wrong number of files
```bash
# Expected: 7,479 files
find data/ -type f -name "*.csv" | wc -l

# If incorrect, re-download
rm -rf data/
./scripts/download-data.sh
```

**Problem**: Data not loading in application
```bash
# Check Docker logs
docker-compose logs backend

# Reinitialize knowledge base
docker-compose exec backend python app/init_knowledge_base.py
```

### Data Integrity

Verify data integrity with checksums:
```bash
# If checksum file is available
sha256sum -c data-checksums.txt
```

## Development Notes

### For Contributors

When developing with this data:

1. **Never commit data files to Git**
   - .gitignore excludes data/ directory
   - Only commit this README.md

2. **Testing with subset**
   ```bash
   # Use first 100 files for quick tests
   mkdir -p data-test
   ls data/*.csv | head -100 | xargs -I {} cp {} data-test/
   ```

3. **Local development**
   - Download data once
   - Reuse for multiple dev sessions
   - No need to re-download unless data updates

### Hosting the Data

For maintainers hosting the data:

1. **Create archive**:
   ```bash
   tar -czf sample-data.tar.gz data/
   ```

2. **Generate checksum**:
   ```bash
   sha256sum sample-data.tar.gz > sample-data.sha256
   ```

3. **Upload to hosting**:
   - GitHub Releases (recommended)
   - Cloud storage (GCS, S3, Azure)
   - CDN for faster distribution

4. **Update URLs**:
   - Update `DATA_URL` in `scripts/download-data.sh`
   - Update links in `DATA_SETUP.md`
   - Update this README

## Alternative Data Sources

### Using Your Own Data

Replace sample data with your own CSV files:

1. **Format requirements**:
   - UTF-8 encoding
   - Header row with column names
   - Consistent structure

2. **Place files in data/ directory**

3. **Reinitialize knowledge base**:
   ```bash
   docker-compose exec backend python app/init_knowledge_base.py
   ```

### Connecting to Live Database

See `backend/app/core/config.py` for database connection settings.

## Support

For data-related questions:
- **Issues**: [GitHub Issues](https://github.com/Cogniware-Inc/cogniware-opea-ims/issues)
- **Discussions**: [OPEA Discussions](https://github.com/orgs/opea-project/discussions)
- **Email**: support@cogniware.com

## File Structure

```
data/
├── README.md (this file)
├── .gitkeep (ensures directory exists in Git)
└── *.csv (7,479 files - downloaded separately)
```

---

**Remember**: Download data before first use!

```bash
./scripts/download-data.sh
```

---

*Last Updated: October 17, 2025*
*For Cogniware OPEA IMS v1.0.0*
