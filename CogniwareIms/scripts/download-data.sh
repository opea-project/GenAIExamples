#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

##############################################################################
# Data Download Script for Cogniware OPEA IMS
#
# This script downloads the sample CSV data files required for the
# Inventory Management System demo.
#
# The data files are hosted separately to keep the GitHub repository size
# manageable per OPEA project guidelines.
##############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DATA_URL="https://github.com/Cogniware-Inc/Cogniware-OPEA-IMS-Data/archive/refs/heads/main.zip"
DATA_DIR="$(dirname "$0")/../assets/data"
TEMP_FILE="/tmp/cogniware-opea-ims-data.zip"
CHECKSUM_URL=""  # Checksum not available for GitHub archive

# Functions
print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}  Cogniware OPEA IMS - Data Downloader${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

check_dependencies() {
    print_info "Checking dependencies..."

    local missing_deps=()

    if ! command -v curl &> /dev/null && ! command -v wget &> /dev/null; then
        missing_deps+=("curl or wget")
    fi

    if ! command -v unzip &> /dev/null; then
        missing_deps+=("unzip")
    fi

    if ! command -v tar &> /dev/null; then
        print_warning "tar not found, but may not be needed for ZIP archives"
    fi

    if ! command -v sha256sum &> /dev/null && ! command -v shasum &> /dev/null; then
        print_warning "sha256sum/shasum not found, checksum verification will be skipped"
    fi

    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing required dependencies: ${missing_deps[*]}"
        exit 1
    fi

    print_success "All dependencies available"
}

download_file() {
    local url=$1
    local output=$2

    print_info "Downloading from: $url"

    if command -v curl &> /dev/null; then
        curl -L -# -o "$output" "$url" || {
            print_error "Download failed"
            return 1
        }
    elif command -v wget &> /dev/null; then
        wget --progress=bar:force -O "$output" "$url" || {
            print_error "Download failed"
            return 1
        }
    fi

    print_success "Download complete"
}

verify_checksum() {
    local file=$1
    local checksum_file=$2

    print_info "Verifying checksum..."

    # Download checksum file
    if ! download_file "$checksum_file" "${file}.sha256"; then
        print_warning "Could not download checksum file, skipping verification"
        return 0
    fi

    # Verify checksum
    if command -v sha256sum &> /dev/null; then
        if sha256sum -c "${file}.sha256" &> /dev/null; then
            print_success "Checksum verified"
            return 0
        else
            print_error "Checksum verification failed"
            return 1
        fi
    elif command -v shasum &> /dev/null; then
        if shasum -a 256 -c "${file}.sha256" &> /dev/null; then
            print_success "Checksum verified"
            return 0
        else
            print_error "Checksum verification failed"
            return 1
        fi
    else
        print_warning "No checksum tool available, skipping verification"
        return 0
    fi
}

extract_data() {
    local archive=$1
    local destination=$2

    print_info "Extracting data files..."

    # Create destination directory
    mkdir -p "$destination"

    # Detect archive type and extract
    if [[ "$archive" == *.tar.gz ]]; then
        tar -xzf "$archive" -C "$destination" || {
            print_error "Extraction failed"
            return 1
        }
    elif [[ "$archive" == *.zip ]]; then
        # For GitHub archives, extract and move files from subdirectory
        unzip -q "$archive" -d /tmp/cogniware-data-extract || {
            print_error "Extraction failed"
            return 1
        }
        # GitHub archives have a subdirectory like Cogniware-OPEA-IMS-Data-main
        local extracted_dir=$(find /tmp/cogniware-data-extract -maxdepth 1 -type d -name "*OPEA-IMS-Data*" | head -1)
        if [ -d "$extracted_dir/data" ]; then
            cp -r "$extracted_dir/data/"* "$destination/" || {
                print_error "Failed to copy data files"
                return 1
            }
            rm -rf /tmp/cogniware-data-extract
        else
            print_error "Data directory not found in archive"
            rm -rf /tmp/cogniware-data-extract
            return 1
        fi
    else
        print_error "Unsupported archive format"
        return 1
    fi

    print_success "Extraction complete"
}

count_files() {
    local dir=$1
    local count=$(find "$dir" -type f -name "*.csv" | wc -l)
    echo "$count"
}

cleanup() {
    print_info "Cleaning up temporary files..."
    rm -f "$TEMP_FILE" "${TEMP_FILE}.sha256"
    rm -rf /tmp/cogniware-data-extract
    print_success "Cleanup complete"
}

main() {
    print_header

    # Check if data already exists
    if [ -d "$DATA_DIR" ] && [ "$(count_files "$DATA_DIR")" -gt 0 ]; then
        print_warning "Data directory already exists with $(count_files "$DATA_DIR") files"
        read -p "Do you want to re-download? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Skipping download"
            exit 0
        fi
        rm -rf "$DATA_DIR"
    fi

    # Check dependencies
    check_dependencies

    # Download data
    print_info "Downloading sample data from GitHub (~32MB)..."
    echo ""
    print_info "Source: https://github.com/Cogniware-Inc/Cogniware-OPEA-IMS-Data"
    echo ""

    # Download and extract
    if ! download_file "$DATA_URL" "$TEMP_FILE"; then
        cleanup
        exit 1
    fi

    # Note: Checksum verification skipped for GitHub archive
    # GitHub archives don't have stable checksums due to metadata

    if ! extract_data "$TEMP_FILE" "$DATA_DIR"; then
        cleanup
        exit 1
    fi

    # Cleanup
    cleanup

    # Summary
    echo ""
    print_success "Data setup complete!"
    print_info "Total CSV files: $(count_files "$DATA_DIR")"
    print_info "Data directory: $DATA_DIR"
    echo ""
    print_info "You can now start the application with: ./start.sh"
}

# Run main function
main "$@"
