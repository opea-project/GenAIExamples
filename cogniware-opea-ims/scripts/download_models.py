#!/usr/bin/env python3
"""
Script to download default models for MSmartCompute Engine
"""

import os
import sys
import requests
import json
from pathlib import Path

def download_file(url, destination):
    """Download a file from URL to destination"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Downloaded: {destination}")
        return True
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return False

def main():
    # Create models directory if it doesn't exist
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    # Default model configurations
    default_models = {
        "gpt2-small": {
            "url": "https://huggingface.co/gpt2/resolve/main/pytorch_model.bin",
            "config_url": "https://huggingface.co/gpt2/resolve/main/config.json",
            "tokenizer_url": "https://huggingface.co/gpt2/resolve/main/tokenizer.json"
        },
        "bert-base": {
            "url": "https://huggingface.co/bert-base-uncased/resolve/main/pytorch_model.bin",
            "config_url": "https://huggingface.co/bert-base-uncased/resolve/main/config.json",
            "tokenizer_url": "https://huggingface.co/bert-base-uncased/resolve/main/tokenizer.json"
        }
    }
    
    print("Downloading default models...")
    
    for model_name, model_info in default_models.items():
        model_dir = models_dir / model_name
        model_dir.mkdir(exist_ok=True)
        
        print(f"\nDownloading {model_name}...")
        
        # Download model files
        files_to_download = [
            ("model.bin", model_info["url"]),
            ("config.json", model_info["config_url"]),
            ("tokenizer.json", model_info["tokenizer_url"])
        ]
        
        for filename, url in files_to_download:
            destination = model_dir / filename
            if not destination.exists():
                download_file(url, destination)
            else:
                print(f"File already exists: {destination}")
    
    # Create a model registry file
    registry = {
        "models": {
            model_name: {
                "path": str(models_dir / model_name),
                "type": "transformer",
                "framework": "pytorch"
            }
            for model_name in default_models.keys()
        }
    }
    
    registry_file = models_dir / "model_registry.json"
    with open(registry_file, 'w') as f:
        json.dump(registry, f, indent=2)
    
    print(f"\nModel registry created: {registry_file}")
    print("Default models download completed!")

if __name__ == "__main__":
    main() 