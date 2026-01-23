#!/usr/bin/env python3
"""
Test script for RAG Chatbot API
Tests PDF upload and query functionality

Usage:
    python test_api.py                    # Run basic tests
    python test_api.py /path/to/file.pdf  # Run full tests with PDF upload
"""

import requests
import sys
import time
from pathlib import Path

BASE_URL = "http://localhost:5000"

def print_status(message, status="info"):
    """Print colored status messages"""
    colors = {
        "info": "\033[94m",  # Blue
        "success": "\033[92m",  # Green
        "error": "\033[91m",  # Red
        "warning": "\033[93m"  # Yellow
    }
    reset = "\033[0m"
    print(f"{colors.get(status, '')}{message}{reset}")


def test_health_check():
    """Test health check endpoint"""
    print_status("\n1. Testing health check endpoint...", "info")
    try:
        response = requests.get(f"{BASE_URL}/")
        response.raise_for_status()
        data = response.json()
        print_status(f"✓ Health check passed: {data['message']}", "success")
        print(f"  Version: {data.get('version', 'N/A')}")
        print(f"  Vectorstore loaded: {data.get('vectorstore_loaded', False)}")
        return True
    except Exception as e:
        print_status(f"✗ Health check failed: {str(e)}", "error")
        return False


def test_detailed_health():
    """Test detailed health endpoint"""
    print_status("\n2. Testing detailed health endpoint...", "info")
    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        data = response.json()
        print_status("✓ Detailed health check passed", "success")
        print(f"  Status: {data.get('status')}")
        print(f"  Vectorstore available: {data.get('vectorstore_available')}")
        print(f"  OpenAI key configured: {data.get('openai_key_configured')}")
        return True
    except Exception as e:
        print_status(f"✗ Detailed health check failed: {str(e)}", "error")
        return False


def test_upload_pdf(pdf_path=None):
    """Test PDF upload endpoint"""
    print_status("\n3. Testing PDF upload...", "info")
    
    if pdf_path and Path(pdf_path).exists():
        file_path = pdf_path
    else:
        print_status("  No PDF file provided. Skipping upload test.", "warning")
        print_status("  To test upload, run: python test_api.py /path/to/file.pdf", "warning")
        return None
    
    try:
        print(f"  Uploading: {file_path}")
        with open(file_path, 'rb') as f:
            files = {'file': (Path(file_path).name, f, 'application/pdf')}
            response = requests.post(f"{BASE_URL}/upload-pdf", files=files)
            response.raise_for_status()
            data = response.json()
            
        print_status(f"✓ Upload successful!", "success")
        print(f"  Message: {data['message']}")
        print(f"  Number of chunks: {data['num_chunks']}")
        print(f"  Status: {data['status']}")
        return True
    except requests.exceptions.HTTPError as e:
        print_status(f"✗ Upload failed: {e}", "error")
        try:
            error_detail = e.response.json()
            print(f"  Error details: {error_detail}")
        except:
            pass
        return False
    except Exception as e:
        print_status(f"✗ Upload failed: {str(e)}", "error")
        return False


def test_query(query="What is this document about?"):
    """Test query endpoint"""
    print_status("\n4. Testing query endpoint...", "info")
    print(f"  Query: '{query}'")
    
    try:
        response = requests.post(
            f"{BASE_URL}/query",
            json={"query": query}
        )
        response.raise_for_status()
        data = response.json()
        
        print_status("✓ Query successful!", "success")
        print(f"  Answer: {data['answer'][:200]}{'...' if len(data['answer']) > 200 else ''}")
        return True
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            print_status("✗ No documents uploaded yet. Upload a PDF first.", "warning")
        else:
            print_status(f"✗ Query failed: {e}", "error")
            try:
                error_detail = e.response.json()
                print(f"  Error details: {error_detail}")
            except:
                pass
        return False
    except Exception as e:
        print_status(f"✗ Query failed: {str(e)}", "error")
        return False


def test_invalid_upload():
    """Test upload validation with invalid file"""
    print_status("\n5. Testing upload validation...", "info")
    
    try:
        # Try uploading a text file
        files = {'file': ('test.txt', b'This is not a PDF', 'text/plain')}
        response = requests.post(f"{BASE_URL}/upload-pdf", files=files)
        
        if response.status_code == 400:
            print_status("✓ Validation working: Invalid file rejected correctly", "success")
            return True
        else:
            print_status("✗ Validation issue: Invalid file was accepted", "error")
            return False
    except Exception as e:
        print_status(f"✗ Validation test failed: {str(e)}", "error")
        return False


def main():
    """Run all tests"""
    print_status("=" * 60)
    print_status("RAG Chatbot API Test Suite", "info")
    print_status("=" * 60)
    
    # Check if server is running
    print_status("\nChecking if server is running...", "info")
    try:
        requests.get(BASE_URL, timeout=2)
    except requests.exceptions.RequestException:
        print_status("✗ Server is not running!", "error")
        print_status(f"Please start the server first:", "warning")
        print_status(f"  cd /Users/raghavdarisi/projects/GenAISamples/rag-chatbot/api", "warning")
        print_status(f"  uvicorn server:app --reload", "warning")
        print_status(f"  OR: python server.py", "warning")
        sys.exit(1)
    
    print_status("✓ Server is running", "success")
    
    # Get PDF path from command line if provided
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Run tests
    results = []
    results.append(("Health Check", test_health_check()))
    results.append(("Detailed Health", test_detailed_health()))
    
    upload_result = test_upload_pdf(pdf_path)
    if upload_result is not None:
        results.append(("PDF Upload", upload_result))
        
        if upload_result:
            # Wait a moment for processing
            time.sleep(1)
            results.append(("Query", test_query()))
            results.append(("Query 2", test_query("Summarize the main points")))
    
    results.append(("Validation", test_invalid_upload()))
    
    # Print summary
    print_status("\n" + "=" * 60)
    print_status("Test Summary", "info")
    print_status("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "success" if result else "error"
        symbol = "✓" if result else "✗"
        print_status(f"{symbol} {test_name}", status)
    
    print_status(f"\nPassed: {passed}/{total}", "success" if passed == total else "warning")
    
    if pdf_path is None:
        print_status("\nNote: PDF upload test was skipped", "warning")
        print_status("To run full tests with PDF upload:", "info")
        print_status(f"  python test_api.py /path/to/your/document.pdf", "info")


if __name__ == "__main__":
    main()

