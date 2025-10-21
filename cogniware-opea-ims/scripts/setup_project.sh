#!/bin/bash

# Create directory structure
mkdir -p include
mkdir -p src/llm_inference_core/model_loader
mkdir -p src/llm_inference_core/cuda_runtime
mkdir -p src/llm_inference_core/inference_pipeline
mkdir -p src/llm_inference_core/tokenizer_interface
mkdir -p src/llm_management
mkdir -p src/knowledge_training_interface
mkdir -p src/dream_engine_components
mkdir -p src/inter_llm_bus
mkdir -p src/api
mkdir -p src/utils
mkdir -p tests
mkdir -p third_party
mkdir -p docs

# Create header files
touch include/msmartcompute_api.h
touch include/internal_types.h

# Create source files
touch src/llm_inference_core/model_loader/gguf_loader.cpp
touch src/llm_inference_core/model_loader/gguf_loader.h
touch src/llm_inference_core/model_loader/safetensors_loader.cpp
touch src/llm_inference_core/model_loader/safetensors_loader.h
touch src/llm_inference_core/model_loader/model_parser_utils.cpp
touch src/llm_inference_core/model_loader/model_parser_utils.h

touch src/llm_inference_core/cuda_runtime/attention_kernels.cu
touch src/llm_inference_core/cuda_runtime/attention_kernels.h
touch src/llm_inference_core/cuda_runtime/matrix_vector_ops.cu
touch src/llm_inference_core/cuda_runtime/matrix_vector_ops.h
touch src/llm_inference_core/cuda_runtime/activation_kernels.cu
touch src/llm_inference_core/cuda_runtime/activation_kernels.h
touch src/llm_inference_core/cuda_runtime/gpu_memory_manager.cpp
touch src/llm_inference_core/cuda_runtime/gpu_memory_manager.h
touch src/llm_inference_core/cuda_runtime/cuda_stream_manager.cpp
touch src/llm_inference_core/cuda_runtime/cuda_stream_manager.h
touch src/llm_inference_core/cuda_runtime/cuda_utils.cu
touch src/llm_inference_core/cuda_runtime/cuda_utils.h

touch src/llm_inference_core/inference_pipeline/transformer_block.cpp
touch src/llm_inference_core/inference_pipeline/transformer_block.h
touch src/llm_inference_core/inference_pipeline/sampling_strategies.cpp
touch src/llm_inference_core/inference_pipeline/sampling_strategies.h
touch src/llm_inference_core/inference_pipeline/kv_cache_manager.cpp
touch src/llm_inference_core/inference_pipeline/kv_cache_manager.h
touch src/llm_inference_core/inference_pipeline/inference_engine.cpp
touch src/llm_inference_core/inference_pipeline/inference_engine.h

touch src/llm_inference_core/tokenizer_interface/base_tokenizer.h
touch src/llm_inference_core/tokenizer_interface/bpe_tokenizer.cpp
touch src/llm_inference_core/tokenizer_interface/bpe_tokenizer.h
touch src/llm_inference_core/tokenizer_interface/sentencepiece_wrapper.cpp
touch src/llm_inference_core/tokenizer_interface/sentencepiece_wrapper.h

touch src/llm_management/llm_instance.cpp
touch src/llm_management/llm_instance.h
touch src/llm_management/llm_instance_manager.cpp
touch src/llm_management/llm_instance_manager.h
touch src/llm_management/concurrency_controller.cpp
touch src/llm_management/concurrency_controller.h
touch src/llm_management/resource_monitor.cpp
touch src/llm_management/resource_monitor.h
touch src/llm_management/request_queue.cpp
touch src/llm_management/request_queue.h

touch src/knowledge_training_interface/data_ingestion_api.cpp
touch src/knowledge_training_interface/data_ingestion_api.h
touch src/knowledge_training_interface/training_control_hooks.cpp
touch src/knowledge_training_interface/training_control_hooks.h
touch src/knowledge_training_interface/shared_memory_manager_cpp.cpp
touch src/knowledge_training_interface/shared_memory_manager_cpp.h

touch src/dream_engine_components/fast_router_core.cpp
touch src/dream_engine_components/fast_router_core.h
touch src/dream_engine_components/vector_search_client_cpp.cpp
touch src/dream_engine_components/vector_search_client_cpp.h

touch src/inter_llm_bus/shared_tensor_buffer.cpp
touch src/inter_llm_bus/shared_tensor_buffer.h
touch src/inter_llm_bus/ipc_manager.cpp
touch src/inter_llm_bus/ipc_manager.h

touch src/api/msmartcompute_c_api.cpp

touch src/utils/config_parser_cpp.cpp
touch src/utils/config_parser_cpp.h
touch src/utils/logger_cpp.cpp
touch src/utils/logger_cpp.h
touch src/utils/error_handler_cpp.cpp
touch src/utils/error_handler_cpp.h

# Create test files
touch tests/test_model_loader.cpp
touch tests/test_cuda_kernels.cpp
touch tests/test_inference_pipeline.cpp
touch tests/test_llm_management.cpp
touch tests/test_c_api.cpp

# Create build and test scripts
touch scripts/build.sh
touch scripts/run_tests.sh

# Make scripts executable
chmod +x scripts/build.sh
chmod +x scripts/run_tests.sh

echo "Project structure created successfully!" 