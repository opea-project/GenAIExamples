# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Quick start guide for EdgeCraft RAG CLI."""

import json
import sys
from cli.client import EcragApiClient


def test_connection(host: str = "http://localhost", port: int = 16010):
    """Test connection to EdgeCraft RAG server."""
    client = EcragApiClient(host=host, server_port=port)
    
    try:
        print(f"Testing connection to {client.server_url}...")
        result = client.get_system_info()
        
        if "error" in result:
            print(f"❌ Connection failed: {result['error']}")
            return False
        
        print("✓ Connection successful!")
        print(f"  System Info: {json.dumps(result, indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return False


def quick_start_guide():
    """Print quick start guide."""
    guide = """
╔══════════════════════════════════════════════════════════════╗
║         EdgeCraft RAG CLI - Quick Start Guide                ║
╚══════════════════════════════════════════════════════════════╝

INSTALLATION:
  Requires Python 3.8+

  Recommended (from EdgeCraftRAG/cli/):
    pip install -e .
    ecrag --help

  If pip reports externally-managed environment (PEP 668):
    pip install --break-system-packages -e .
    ecrag --help

  Optional (non-editable install):
    pip install .
    ecrag --help

BASIC USAGE:
  # Check help
  ecrag --help
  ecrag pipeline --help

CONFIGURATION:
  Set environment variables for connection:
    export ECRAG_HOST=http://your-host
    export ECRAG_PORT=16010
    export ECRAG_MEGA_PORT=16011

COMMON COMMANDS:
  
  Pipeline Management:
    ecrag pipeline list
    ecrag pipeline get --name <name>
    ecrag pipeline create --name <name> --file pipeline.json
    ecrag pipeline activate --name <name>

  Knowledge Base:
    ecrag kb list
    ecrag kb create --name <name>
    ecrag kb add-files --name <name> --paths /path/to/file

  Models:
    ecrag model list
    ecrag model load --type LLM --id <model-id>

  Query & Chat:
    ecrag query "Your question"
    ecrag chat retrieve --query "Your question"
    ecrag chat rag --query "Your question"
    ecrag chat mega --query "Your question"

  System:
    ecrag system info
    ecrag system devices

TROUBLESHOOTING:
  Connection refused?
    - Make sure EdgeCraft RAG server is running
    - Check HOST (default: http://localhost) and PORT (default: 16010)
    - Try: ecrag system info

  Command not found?
    - Make sure you're in the EdgeCraftRAG directory
    - Try: ecrag <command>

  Module not found?
    - Verify cli/ directory exists with __init__.py
    - Check PYTHONPATH includes the EdgeCraftRAG directory

For more information, see cli/README.md
"""
    print(guide)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        host = sys.argv[2] if len(sys.argv) > 2 else "http://localhost"
        port = int(sys.argv[3]) if len(sys.argv) > 3 else 16010
        test_connection(host, port)
    elif len(sys.argv) > 1 and sys.argv[1] == "--guide":
        quick_start_guide()
    else:
        quick_start_guide()
        print("\nRun with --test to check connection to server")
