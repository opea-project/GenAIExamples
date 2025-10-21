import os
import ctypes
import json
from typing import Dict, Any, Optional, List
import numpy as np
import torch

class MSmartComputeEngine:
    """Python interface for the cogniware engine."""
    
    def __init__(self, device_id: int = 0):
        """Initialize the engine with the specified CUDA device."""
        # Load the shared library
        lib_path = os.path.join(os.path.dirname(__file__), 
                               '../build/lib/libcogniware_engine_cpp.so')
        self._lib = ctypes.CDLL(lib_path)
        
        # Set function signatures
        self._lib.initialize_engine.argtypes = [ctypes.c_int]
        self._lib.initialize_engine.restype = ctypes.c_bool
        
        self._lib.process_request.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self._lib.process_request.restype = ctypes.c_char_p
        
        self._lib.shutdown_engine.argtypes = []
        self._lib.shutdown_engine.restype = None
        
        # Initialize the engine
        if not self._lib.initialize_engine(device_id):
            raise RuntimeError("Failed to initialize cogniware engine")
        
        self.device_id = device_id
    
    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request using the engine."""
        try:
            # Convert request to JSON string
            request_json = json.dumps(request_data).encode('utf-8')
            
            # Allocate response buffer
            response_buffer = ctypes.create_string_buffer(1024 * 1024)  # 1MB buffer
            
            # Process request
            response = self._lib.process_request(request_json, response_buffer)
            if not response:
                raise RuntimeError("Failed to process request")
            
            # Parse response
            return json.loads(response.decode('utf-8'))
        except Exception as e:
            raise RuntimeError(f"Error processing request: {str(e)}")
    
    def shutdown(self):
        """Shutdown the engine."""
        self._lib.shutdown_engine()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

# Example usage
if __name__ == "__main__":
    # Initialize engine
    engine = MSmartComputeEngine(device_id=0)
    
    try:
        # Process a request
        request = {
            "model": "gpt-4",
            "prompt": "Hello, world!",
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        response = engine.process_request(request)
        print(f"Response: {response}")
    finally:
        # Shutdown engine
        engine.shutdown() 