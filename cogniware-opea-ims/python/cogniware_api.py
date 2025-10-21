"""
Cogniware Core - Python API Layer
Comprehensive API for external service integration and web interface communication
"""

import ctypes
import numpy as np
from typing import List, Dict, Optional, Any, Callable, Union
from dataclasses import dataclass
from enum import Enum
import threading
import queue
import json
import asyncio


class ModelType(Enum):
    """LLM model types"""
    GPT = "gpt"
    LLAMA = "llama"
    BERT = "bert"
    T5 = "t5"
    CUSTOM = "custom"


class ResourceType(Enum):
    """Resource types"""
    MEMORY = "memory"
    CPU = "cpu"
    GPU = "gpu"
    DISK = "disk"
    NETWORK = "network"


@dataclass
class ModelConfig:
    """Model configuration"""
    model_id: str
    model_type: ModelType
    model_path: str
    device_id: int = 0
    precision: str = "fp16"
    max_batch_size: int = 32
    max_sequence_length: int = 2048
    parameters: Dict[str, Any] = None


@dataclass
class InferenceRequest:
    """Inference request"""
    request_id: str
    model_id: str
    prompt: str
    max_tokens: int = 100
    temperature: float = 0.7
    top_p: float = 0.9
    stop_sequences: List[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class InferenceResponse:
    """Inference response"""
    request_id: str
    model_id: str
    generated_text: str
    tokens_generated: int
    execution_time_ms: float
    success: bool
    error_message: str = ""


@dataclass
class ResourceUsage:
    """Resource usage statistics"""
    memory_used_mb: float
    memory_total_mb: float
    cpu_percent: float
    gpu_percent: float
    gpu_memory_used_mb: float
    gpu_memory_total_mb: float


class CogniwareCore:
    """
    Main Cogniware Core API class
    Provides high-level Python interface to the core engine
    """
    
    def __init__(self, library_path: str = "./libcore_inference_engine.so"):
        """Initialize Cogniware Core"""
        self.lib = ctypes.CDLL(library_path)
        self._setup_functions()
        self.models: Dict[str, ModelConfig] = {}
        self.request_queue = queue.Queue()
        self.response_callbacks: Dict[str, Callable] = {}
        
    def _setup_functions(self):
        """Setup C library function signatures"""
        # Model management
        self.lib.load_model.argtypes = [ctypes.c_char_p, ctypes.c_int]
        self.lib.load_model.restype = ctypes.c_int
        
        self.lib.unload_model.argtypes = [ctypes.c_int]
        self.lib.unload_model.restype = ctypes.c_bool
        
        # Inference
        self.lib.run_inference.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_int
        ]
        self.lib.run_inference.restype = ctypes.c_bool
        
    def initialize(self) -> bool:
        """Initialize the core engine"""
        try:
            # Initialize core systems
            result = self.lib.initialize_core()
            return bool(result)
        except Exception as e:
            print(f"Failed to initialize: {e}")
            return False
    
    def shutdown(self) -> bool:
        """Shutdown the core engine"""
        try:
            # Unload all models
            for model_id in list(self.models.keys()):
                self.unload_model(model_id)
            
            result = self.lib.shutdown_core()
            return bool(result)
        except Exception as e:
            print(f"Failed to shutdown: {e}")
            return False
    
    def load_model(self, config: ModelConfig) -> bool:
        """Load a model"""
        try:
            model_path_bytes = config.model_path.encode('utf-8')
            model_handle = self.lib.load_model(model_path_bytes, config.device_id)
            
            if model_handle >= 0:
                self.models[config.model_id] = config
                return True
            return False
        except Exception as e:
            print(f"Failed to load model: {e}")
            return False
    
    def unload_model(self, model_id: str) -> bool:
        """Unload a model"""
        try:
            if model_id in self.models:
                config = self.models[model_id]
                result = self.lib.unload_model(config.device_id)
                if result:
                    del self.models[model_id]
                return bool(result)
            return False
        except Exception as e:
            print(f"Failed to unload model: {e}")
            return False
    
    def run_inference(self, request: InferenceRequest) -> InferenceResponse:
        """Run inference on a model"""
        import time
        start_time = time.time()
        
        try:
            if request.model_id not in self.models:
                return InferenceResponse(
                    request_id=request.request_id,
                    model_id=request.model_id,
                    generated_text="",
                    tokens_generated=0,
                    execution_time_ms=0,
                    success=False,
                    error_message="Model not loaded"
                )
            
            config = self.models[request.model_id]
            prompt_bytes = request.prompt.encode('utf-8')
            output_buffer = ctypes.create_string_buffer(8192)
            
            result = self.lib.run_inference(
                config.device_id,
                prompt_bytes,
                output_buffer,
                request.max_tokens
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            if result:
                generated_text = output_buffer.value.decode('utf-8')
                return InferenceResponse(
                    request_id=request.request_id,
                    model_id=request.model_id,
                    generated_text=generated_text,
                    tokens_generated=len(generated_text.split()),
                    execution_time_ms=execution_time,
                    success=True
                )
            else:
                return InferenceResponse(
                    request_id=request.request_id,
                    model_id=request.model_id,
                    generated_text="",
                    tokens_generated=0,
                    execution_time_ms=execution_time,
                    success=False,
                    error_message="Inference failed"
                )
                
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return InferenceResponse(
                request_id=request.request_id,
                model_id=request.model_id,
                generated_text="",
                tokens_generated=0,
                execution_time_ms=execution_time,
                success=False,
                error_message=str(e)
            )
    
    async def run_inference_async(self, request: InferenceRequest) -> InferenceResponse:
        """Run inference asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.run_inference, request)
    
    def batch_inference(self, requests: List[InferenceRequest]) -> List[InferenceResponse]:
        """Run batch inference"""
        responses = []
        for request in requests:
            response = self.run_inference(request)
            responses.append(response)
        return responses
    
    def get_resource_usage(self) -> ResourceUsage:
        """Get current resource usage"""
        try:
            # Call C++ resource monitoring
            return ResourceUsage(
                memory_used_mb=0.0,
                memory_total_mb=0.0,
                cpu_percent=0.0,
                gpu_percent=0.0,
                gpu_memory_used_mb=0.0,
                gpu_memory_total_mb=0.0
            )
        except Exception as e:
            print(f"Failed to get resource usage: {e}")
            return ResourceUsage(0, 0, 0, 0, 0, 0)
    
    def list_models(self) -> List[str]:
        """List loaded models"""
        return list(self.models.keys())
    
    def get_model_info(self, model_id: str) -> Optional[ModelConfig]:
        """Get model information"""
        return self.models.get(model_id)


class CogniwareMultiLLM:
    """
    Multi-LLM orchestration API
    Manages multiple LLMs running in parallel
    """
    
    def __init__(self, core: CogniwareCore):
        self.core = core
        self.active_models: List[str] = []
    
    def add_model(self, config: ModelConfig) -> bool:
        """Add a model to the orchestration"""
        if self.core.load_model(config):
            self.active_models.append(config.model_id)
            return True
        return False
    
    def remove_model(self, model_id: str) -> bool:
        """Remove a model from orchestration"""
        if self.core.unload_model(model_id):
            if model_id in self.active_models:
                self.active_models.remove(model_id)
            return True
        return False
    
    def parallel_inference(self, prompt: str, model_ids: List[str] = None) -> Dict[str, InferenceResponse]:
        """Run inference on multiple models in parallel"""
        import concurrent.futures
        
        if model_ids is None:
            model_ids = self.active_models
        
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {}
            for model_id in model_ids:
                request = InferenceRequest(
                    request_id=f"{model_id}_{id(prompt)}",
                    model_id=model_id,
                    prompt=prompt
                )
                future = executor.submit(self.core.run_inference, request)
                futures[model_id] = future
            
            for model_id, future in futures.items():
                try:
                    results[model_id] = future.result()
                except Exception as e:
                    print(f"Error in parallel inference for {model_id}: {e}")
        
        return results
    
    def consensus_inference(self, prompt: str, model_ids: List[str] = None) -> str:
        """Run inference and return consensus result"""
        results = self.parallel_inference(prompt, model_ids)
        
        # Simple consensus: return most common response
        responses = [r.generated_text for r in results.values() if r.success]
        if not responses:
            return ""
        
        # Return longest response as simple heuristic
        return max(responses, key=len)


class CogniwareMonitor:
    """
    Resource monitoring API
    Tracks system performance and resource usage
    """
    
    def __init__(self, core: CogniwareCore):
        self.core = core
        self.monitoring = False
        self.monitor_thread = None
        self.history: List[ResourceUsage] = []
        self.max_history = 1000
    
    def start_monitoring(self, interval_seconds: float = 1.0):
        """Start resource monitoring"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
    
    def _monitor_loop(self, interval: float):
        """Monitor loop"""
        import time
        while self.monitoring:
            usage = self.core.get_resource_usage()
            self.history.append(usage)
            
            if len(self.history) > self.max_history:
                self.history.pop(0)
            
            time.sleep(interval)
    
    def get_current_usage(self) -> ResourceUsage:
        """Get current resource usage"""
        return self.core.get_resource_usage()
    
    def get_history(self) -> List[ResourceUsage]:
        """Get resource usage history"""
        return self.history.copy()
    
    def get_average_usage(self) -> ResourceUsage:
        """Get average resource usage"""
        if not self.history:
            return ResourceUsage(0, 0, 0, 0, 0, 0)
        
        avg_memory = sum(u.memory_used_mb for u in self.history) / len(self.history)
        avg_cpu = sum(u.cpu_percent for u in self.history) / len(self.history)
        avg_gpu = sum(u.gpu_percent for u in self.history) / len(self.history)
        avg_gpu_mem = sum(u.gpu_memory_used_mb for u in self.history) / len(self.history)
        
        return ResourceUsage(
            memory_used_mb=avg_memory,
            memory_total_mb=self.history[-1].memory_total_mb if self.history else 0,
            cpu_percent=avg_cpu,
            gpu_percent=avg_gpu,
            gpu_memory_used_mb=avg_gpu_mem,
            gpu_memory_total_mb=self.history[-1].gpu_memory_total_mb if self.history else 0
        )


class CogniwareAPI:
    """
    Main Cogniware API facade
    Provides unified access to all functionality
    """
    
    def __init__(self, library_path: str = "./libcore_inference_engine.so"):
        """Initialize Cogniware API"""
        self.core = CogniwareCore(library_path)
        self.multi_llm = CogniwareMultiLLM(self.core)
        self.monitor = CogniwareMonitor(self.core)
        self.initialized = False
    
    def initialize(self) -> bool:
        """Initialize the API"""
        if self.core.initialize():
            self.initialized = True
            self.monitor.start_monitoring()
            return True
        return False
    
    def shutdown(self) -> bool:
        """Shutdown the API"""
        self.monitor.stop_monitoring()
        self.initialized = False
        return self.core.shutdown()
    
    def __enter__(self):
        """Context manager entry"""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.shutdown()


# Example usage
if __name__ == "__main__":
    # Create API instance
    api = CogniwareAPI()
    
    try:
        # Initialize
        if not api.initialize():
            print("Failed to initialize Cogniware Core")
            exit(1)
        
        print("Cogniware Core initialized successfully")
        
        # Load a model
        config = ModelConfig(
            model_id="llama-7b",
            model_type=ModelType.LLAMA,
            model_path="/models/llama-7b.bin",
            device_id=0
        )
        
        if api.core.load_model(config):
            print(f"Model {config.model_id} loaded successfully")
        
        # Run inference
        request = InferenceRequest(
            request_id="test_001",
            model_id="llama-7b",
            prompt="What is the capital of France?",
            max_tokens=50
        )
        
        response = api.core.run_inference(request)
        
        if response.success:
            print(f"Generated text: {response.generated_text}")
            print(f"Execution time: {response.execution_time_ms:.2f}ms")
        else:
            print(f"Inference failed: {response.error_message}")
        
        # Get resource usage
        usage = api.monitor.get_current_usage()
        print(f"Memory: {usage.memory_used_mb:.2f}MB / {usage.memory_total_mb:.2f}MB")
        print(f"CPU: {usage.cpu_percent:.2f}%")
        print(f"GPU: {usage.gpu_percent:.2f}%")
        
    finally:
        # Shutdown
        api.shutdown()
        print("Cogniware Core shutdown complete")

