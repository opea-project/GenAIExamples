# Data Setup Guide for Cogniware OPEA IMS

## Overview

This guide explains how to set up the sample data files required for the Cogniware OPEA Inventory Management System.

**Important**: Per OPEA project guidelines, the 7,479 CSV files (~32MB) are **not included** in the GitHub repository. They must be downloaded separately before first use.

---

## Quick Start

### For Users

```bash
# 1. Clone the repository
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/InventoryManagement/cogniware-opea-ims

# 2. Download sample data
./scripts/download-data.sh

# 3. Start the application
./start.sh
```

That's it! The application will now have access to the sample inventory data.

---

## Detailed Instructions

### Option 1: Automated Download (Recommended)

The easiest way to set up the data is using the provided script:

```bash
cd /path/to/cogniware-opea-ims
./scripts/download-data.sh
```

**What the script does**:

1. ✅ Checks for required dependencies (curl/wget, tar)
2. ✅ Downloads data archive from hosting service
3. ✅ Verifies data integrity (SHA-256 checksum)
4. ✅ Extracts 7,479 CSV files to `assets/data/` directory
5. ✅ Displays summary and next steps

**Requirements**:

- Internet connection
- ~40MB free disk space
- `curl` or `wget`
- `tar` command

### Option 2: Manual Download

If the automated script doesn't work, download manually:

#### Step 1: Download Data Archive

**Primary Download Location**:

```bash
# GitHub Repository Archive
wget https://github.com/Cogniware-Inc/Cogniware-OPEA-IMS-Data/archive/refs/heads/main.zip

# Or using curl
curl -L -O https://github.com/Cogniware-Inc/Cogniware-OPEA-IMS-Data/archive/refs/heads/main.zip
```

**Data Repository**: [Cogniware-OPEA-IMS-Data](https://github.com/Cogniware-Inc/Cogniware-OPEA-IMS-Data)

**Alternative Locations**:

- Direct from Cogniware: support@cogniware.com

#### Step 2: Verify Download (Optional)

**Note**: GitHub archive downloads don't have stable checksums due to metadata changes. File integrity is verified through GitHub's infrastructure.

#### Step 3: Extract Files

```bash
# Extract ZIP archive
unzip main.zip

# Move data files to correct location
mkdir -p assets/data
cp -r Cogniware-OPEA-IMS-Data-main/data/* assets/data/

# Verify file count
find assets/data -type f -name "*.csv" | wc -l
# Expected: 7479
```

#### Step 4: Cleanup

```bash
# Remove downloaded archive and extracted directory
rm main.zip
rm -rf Cogniware-OPEA-IMS-Data-main
```

### Option 3: Development Mode (Local Copy)

If you already have the data from another source:

```bash
# Copy existing data
cp -r /path/to/existing/data/* cogniware-opea-ims/assets/data/

# Or create symbolic link
ln -s /path/to/existing/data cogniware-opea-ims/assets/data
```

---

## Data Details

### What's Included

**File Statistics**:

- **Total Files**: 7,479 CSV files
- **Total Size**: ~32 MB compressed, ~45 MB extracted
- **File Types**: Product specifications and ordering information

**Product Categories**:

- Intel® Xeon® Processors (various generations)
- Intel® Core™ Processors (Consumer & Mobile)
- Intel® FPGAs (Stratix®, Arria®, Cyclone®, MAX®, Agilex®)
- Server Chassis and Components
- RAID Controllers and Storage
- Network Adapters
- Accessories and Peripherals

### File Structure

```
assets/data/
├── README.md
├── .gitkeep
└── [7,479 CSV files]
    ├── Intel® Xeon® Processor E5-4660 v3_spec.csv
    ├── Intel® Core™ i7-13700K Processor_ordering.csv
    ├── Stratix® V GX FPGA Development Kit_ordering.csv
    └── ... (7,476 more files)
```

### CSV Format

Each CSV file contains product information with columns such as:

- Product Name
- Model Number
- Specifications
- Performance Metrics
- Ordering Information
- Package Details

**Example** (`Intel® Xeon® Processor E5-4660 v3_spec.csv`):

```csv
Field,Value
Product Name,Intel® Xeon® Processor E5-4660 v3
Cores,14
Threads,28
Base Frequency,2.10 GHz
Max Turbo Frequency,2.90 GHz
Cache,35 MB
TDP,120W
...
```

---

## Hosting the Data (For Maintainers)

### Creating the Data Archive

If you're a maintainer preparing the data for distribution:

#### Step 1: Prepare Data Files

```bash
# Ensure you're in the project root
cd cogniware-opea-ims

# Verify data directory structure
ls -la assets/data/
find assets/data -type f -name "*.csv" | wc -l  # Should be 7479
```

#### Step 2: Create Compressed Archive

```bash
# Create tarball with optimal compression
tar -czf sample-data.tar.gz assets/data/ \
    --exclude='.DS_Store' \
    --exclude='._*' \
    --exclude='.gitkeep'

# Check archive size
ls -lh sample-data.tar.gz
```

#### Step 3: Generate Checksum

```bash
# Generate SHA-256 checksum
sha256sum sample-data.tar.gz > sample-data.sha256

# Or on macOS
shasum -a 256 sample-data.tar.gz > sample-data.sha256

# Display checksum
cat sample-data.sha256
```

#### Step 4: Test Archive

```bash
# Test extraction in temp directory
mkdir -p /tmp/test-data
tar -xzf sample-data.tar.gz -C /tmp/test-data

# Verify file count
find /tmp/test-data -type f -name "*.csv" | wc -l

# Cleanup
rm -rf /tmp/test-data
```

### Upload Options

#### Option A: GitHub Repository (Currently Used) ✅

**Repository**: [Cogniware-OPEA-IMS-Data](https://github.com/Cogniware-Inc/Cogniware-OPEA-IMS-Data)

1. **Repository Structure**:

   ```
   Cogniware-OPEA-IMS-Data/
   └── data/
       └── *.csv (7,479 files)
   ```

2. **Access**:
   - Direct download: `https://github.com/Cogniware-Inc/Cogniware-OPEA-IMS-Data/archive/refs/heads/main.zip`
   - Clone repository: `git clone https://github.com/Cogniware-Inc/Cogniware-OPEA-IMS-Data.git`

3. **Update Process**:
   - Push new CSV files to repository
   - Users run `./scripts/download-data.sh` to get latest
   - No URL changes needed

**Advantages**:

- ✅ Free for public repositories
- ✅ Reliable GitHub infrastructure
- ✅ Version control via Git
- ✅ Easy updates and maintenance
- ✅ Currently configured and working

#### Option B: Google Cloud Storage

```bash
# Install gsutil
# https://cloud.google.com/storage/docs/gsutil_install

# Create bucket (one-time)
gsutil mb gs://cogniware-opea-ims-data

# Make bucket public
gsutil iam ch allUsers:objectViewer gs://cogniware-opea-ims-data

# Upload files
gsutil cp sample-data.tar.gz gs://cogniware-opea-ims-data/
gsutil cp sample-data.sha256 gs://cogniware-opea-ims-data/

# Get public URL
echo "https://storage.googleapis.com/cogniware-opea-ims-data/sample-data.tar.gz"
```

**Cost**: ~$0.50/month for storage + bandwidth

#### Option C: AWS S3

```bash
# Install AWS CLI
# https://aws.amazon.com/cli/

# Create bucket
aws s3 mb s3://cogniware-opea-ims-data

# Upload files
aws s3 cp sample-data.tar.gz s3://cogniware-opea-ims-data/ --acl public-read
aws s3 cp sample-data.sha256 s3://cogniware-opea-ims-data/ --acl public-read

# Get public URL
echo "https://cogniware-opea-ims-data.s3.amazonaws.com/sample-data.tar.gz"
```

**Cost**: ~$0.50/month for storage + bandwidth

#### Option D: Azure Blob Storage

```bash
# Install Azure CLI
# https://docs.microsoft.com/cli/azure/install-azure-cli

# Create storage account
az storage account create \
    --name cogniwaredatastorage \
    --resource-group opea-ims \
    --location eastus

# Create container
az storage container create \
    --name data \
    --account-name cogniwaredatastorage \
    --public-access blob

# Upload files
az storage blob upload \
    --account-name cogniwaredatastorage \
    --container-name data \
    --name sample-data.tar.gz \
    --file sample-data.tar.gz

# Get public URL
echo "https://cogniwaredatastorage.blob.core.windows.net/data/sample-data.tar.gz"
```

**Cost**: ~$0.50/month for storage + bandwidth

---

## Using Your Own Data

### Requirements for Custom Data

If you want to use your own inventory data instead of the sample data:

#### File Format Requirements

1. **CSV Files**: UTF-8 encoding with header row
2. **Structure**: Consistent columns across similar product types
3. **Naming**: Descriptive filenames (e.g., `ProductName_spec.csv`)

#### Minimum Required Fields

For best results with the AI agents, include:

- Product name/identifier
- Category/type
- Key specifications
- Pricing/ordering information

#### Example Custom CSV

```csv
product_id,product_name,category,specification,value,unit
1001,Server Chassis X1,Chassis,Height,2,U
1001,Server Chassis X1,Chassis,Width,19,inches
1001,Server Chassis X1,Chassis,Depth,24,inches
1002,Xeon Processor Y2,Processor,Cores,16,cores
1002,Xeon Processor Y2,Processor,Frequency,2.4,GHz
```

### Setup Custom Data

1. **Place CSV files in data/ directory**:

   ```bash
   cp /path/to/your/csvs/*.csv cogniware-opea-ims/assets/data/
   ```

2. **Reinitialize knowledge base**:

   ```bash
   docker-compose up -d
   docker-compose exec backend python app/init_knowledge_base.py
   ```

3. **Test queries**:
   - Access UI: http://localhost:3000
   - Try sample queries with your product names
   - Verify AI responses are accurate

---

## Troubleshooting

### Common Issues

#### Issue: "Download script fails"

**Symptoms**:

```
✗ Download failed
```

**Solutions**:

```bash
# 1. Check internet connection
ping -c 3 google.com

# 2. Check available disk space (need ~40MB)
df -h .

# 3. Try manual download
curl -L -O [DATA_URL]

# 4. Check firewall/proxy settings
export http_proxy=http://proxy:port
export https_proxy=http://proxy:port
```

#### Issue: "Wrong number of files extracted"

**Symptoms**:

```bash
find data -name "*.csv" | wc -l
# Shows number other than 7479
```

**Solutions**:

```bash
# 1. Remove incomplete data
rm -rf data/

# 2. Re-download
./scripts/download-data.sh

# 3. If still wrong, verify archive integrity
sha256sum sample-data.tar.gz
```

#### Issue: "Data not loading in application"

**Symptoms**:

- Application starts but no inventory data
- Queries return "no results"
- Knowledge base initialization errors

**Solutions**:

```bash
# 1. Check data files exist
ls -l data/*.csv | head

# 2. Check Docker volume mounts
docker-compose config | grep volumes

# 3. Reinitialize knowledge base
docker-compose exec backend python app/init_knowledge_base.py

# 4. Check logs
docker-compose logs backend | grep -i "csv\|data\|knowledge"

# 5. Restart services
docker-compose restart
```

#### Issue: "Permission denied extracting files"

**Symptoms**:

```
tar: Cannot open: Permission denied
```

**Solutions**:

```bash
# 1. Check directory permissions
ls -ld data/

# 2. Create directory if needed
mkdir -p data

# 3. Set proper permissions
chmod 755 data/

# 4. Try extraction again
tar -xzf sample-data.tar.gz
```

#### Issue: "Checksum verification failed"

**Symptoms**:

```
sample-data.tar.gz: FAILED
```

**Solutions**:

```bash
# 1. Re-download the archive (may be corrupted)
rm sample-data.tar.gz
curl -L -O [DATA_URL]

# 2. Verify checksum file itself
cat sample-data.sha256

# 3. Skip checksum verification (not recommended)
# Edit download-data.sh and comment out verify_checksum call
```

### Performance Issues

#### Slow Download

```bash
# Try alternate download locations
# Or download during off-peak hours

# For large files, resume broken downloads:
curl -C - -L -O [DATA_URL]
wget -c [DATA_URL]
```

#### Slow Knowledge Base Initialization

```bash
# Normal: 2-5 minutes for 7,479 files
# If slower, check:

# 1. System resources
htop  # Check CPU/memory usage

# 2. Docker resources
docker stats

# 3. Increase Docker memory/CPU limits
# Docker Desktop > Settings > Resources
```

---

## Data Updates

### Checking for Updates

```bash
# Check current data version
cat data/VERSION 2>/dev/null || echo "1.0.0"

# Check for latest version
curl -s https://api.github.com/repos/Cogniware-Inc/cogniware-opea-ims/releases/latest | grep tag_name
```

### Updating Data

```bash
# Backup current data (optional)
mv data data-backup-$(date +%Y%m%d)

# Download new version
./scripts/download-data.sh

# Reinitialize knowledge base
docker-compose exec backend python app/init_knowledge_base.py
```

---

## FAQ

### Q: Why aren't the data files in the Git repository?

**A**: Per OPEA project guidelines, large binary files should not be committed to Git repositories. This keeps the repo lightweight and reduces clone times. The 7,479 CSV files (~32MB) are significant enough to warrant separate hosting.

### Q: Is the data real or simulated?

**A**: The data consists of real Intel product specifications and ordering information, collected from public sources. It's suitable for demonstration and testing purposes.

### Q: Can I use this in production?

**A**: The sample data is for demonstration only. For production use:

- Verify data accuracy with official sources
- Use your own real inventory data
- Implement proper data governance

### Q: How often is the data updated?

**A**: Sample data updates are released periodically as new Intel products become available. Check GitHub Releases for the latest version.

### Q: What if I don't want to download 7,479 files?

**A**: You can use a subset for testing:

```bash
# Download full set
./scripts/download-data.sh

# Use first 100 files for testing
mkdir data-test
ls data/*.csv | head -100 | xargs -I {} cp {} data-test/

# Update docker-compose.yml to use data-test/
```

### Q: Can I contribute additional data?

**A**: Yes! If you have product data to contribute:

1. Ensure it's publicly available information
2. Format as CSV with clear headers
3. Submit PR with data files
4. Maintainers will add to next data release

### Q: What's the data license?

**A**: The sample data consists of publicly available Intel product information. The data compilation is provided under Apache 2.0 license for demonstration purposes.

---

## Support

### Getting Help

**Documentation**:

- README.md - Main project documentation
- DEPLOYMENT_GUIDE.md - Deployment instructions
- SECURITY.md - Security guidelines

**Community**:

- GitHub Issues: https://github.com/opea-project/GenAIExamples/issues
- OPEA Discussions: https://github.com/opea-project/discussions

**Commercial Support**:

- Email: support@cogniware.com
- Website: https://cogniware.com

---

## Summary

**Quick Setup**:

```bash
git clone [repository]
cd cogniware-opea-ims
./scripts/download-data.sh  # Downloads 7,479 CSV files
./start.sh                   # Starts application
```

**Data Location**: `data/` directory (excluded from Git)
**Size**: ~32 MB compressed, ~45 MB extracted
**Files**: 7,479 CSV files with Intel product data

**Next Steps**:

1. ✅ Download data
2. ✅ Start application with `./start.sh`
3. ✅ Access UI at http://localhost:3000
4. ✅ Try sample queries

---

_Last Updated: October 17, 2025_
_Version: 1.0.0_
_For: Cogniware OPEA IMS_
