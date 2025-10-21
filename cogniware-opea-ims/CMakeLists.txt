cmake_minimum_required(VERSION 3.15)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Project name and version
project(simple_engine VERSION 1.0.0)

# Find required packages
find_package(Threads REQUIRED)
find_package(nlohmann_json REQUIRED)
find_package(pybind11 REQUIRED)
find_package(Python3 REQUIRED COMPONENTS Interpreter Development)
find_package(spdlog REQUIRED)
find_package(fmt REQUIRED)

# Find CUDA
find_package(CUDA REQUIRED)
enable_language(CUDA)

# Add source files
set(SIMPLE_ENGINE_SOURCES
    src/simple_engine/simple_engine.cpp
    src/simple_engine/simple_api.cpp
)

set(SIMPLE_ENGINE_HEADERS
    src/simple_engine/simple_engine.h
    src/simple_engine/simple_api.h
)

# Add enhanced engine sources
set(ENHANCED_ENGINE_SOURCES
    src/enhanced_engine/enhanced_engine.cpp
)

set(ENHANCED_ENGINE_HEADERS
    src/enhanced_engine/enhanced_engine.h
)

# Add core inference engine sources
set(CORE_INFERENCE_SOURCES
    src/llm_inference_core/llm_inference_core.cpp
    src/llm_inference_core/inference/inference_engine.cpp
    src/llm_inference_core/model/model_manager.cpp
    src/llm_inference_core/tokenizer_interface/bpe_tokenizer.cpp
    src/llm_inference_core/tokenizer_interface/tokenizer_factory.cpp
    src/llm_inference_core/model/huggingface_model_selector.cpp
    src/llm_inference_core/model/ollama_model_selector.cpp
    src/llm_inference_core/model/model_selector_factory.cpp
    src/core/customized_kernel.cpp
    src/core/customized_driver.cpp
    src/core/python_cpp_bridge.cpp
    src/optimization/tensor_core_optimizer.cpp
    src/optimization/tensor_core_workload_balancer.cpp
    src/optimization/tensor_core_memory_optimizer.cpp
    src/optimization/tensor_core_precision_optimizer.cpp
    src/optimization/tensor_core_optimization_manager.cpp
    src/virtualization/virtual_compute_node.cpp
    src/virtualization/virtual_compute_node_manager.cpp
    src/virtualization/global_virtual_compute_node_system.cpp
    src/memory/memory_partitioning.cpp
    src/memory/memory_partitioning_manager.cpp
    src/memory/global_memory_partitioning_system.cpp
    src/parallel/parallel_llm_execution.cpp
    src/parallel/parallel_llm_execution_manager.cpp
    src/parallel/global_parallel_llm_execution_system.cpp
    src/nvlink/nvlink_optimization.cpp
    src/nvlink/nvlink_topology_manager.cpp
    src/nvlink/global_nvlink_optimization_system.cpp
    src/cuda/cuda_stream_management.cpp
    src/cuda/cuda_stream_manager.cpp
    src/cuda/global_cuda_stream_management_system.cpp
    src/scheduler/compute_node_scheduler.cpp
    src/scheduler/compute_node_scheduler_manager.cpp
    src/scheduler/global_compute_node_scheduler_system.cpp
    src/bridge/python_cpp_bridge.cpp
    src/bridge/python_cpp_bridge_manager.cpp
    src/bridge/global_python_cpp_bridge_system.cpp
    src/orchestration/multi_llm_orchestrator.cpp
    src/orchestration/multi_llm_orchestrator_manager.cpp
    src/orchestration/global_multi_llm_orchestration_system.cpp
    src/inference/inference_sharing.cpp
    src/inference/inference_sharing_manager.cpp
    src/inference/global_inference_sharing_system.cpp
    src/multimodal/multimodal_processor.cpp
    src/multimodal/multimodal_processor_manager.cpp
    src/multimodal/global_multimodal_system.cpp
    src/multimodal/multimodal_cuda_kernels.cu
    src/mcp/mcp_server.cpp
    src/mcp/mcp_client.cpp
    src/mcp/mcp_manager.cpp
    src/mcp/mcp_filesystem.cpp
    src/mcp/mcp_internet.cpp
    src/mcp/mcp_database.cpp
    src/mcp/mcp_application.cpp
    src/mcp/mcp_system_services.cpp
    src/mcp/mcp_security.cpp
    src/mcp/mcp_resources.cpp
    src/mcp/mcp_tool_registry.cpp
    src/api/rest_api.cpp
    src/benchmark/performance_benchmark.cpp
    src/async/async_processor.cpp
    src/model/model_manager.cpp
    src/monitoring/monitoring_system.cpp
    src/optimization/optimizer.cpp
    src/ipc/inter_llm_bus.cpp
    src/distributed/distributed_system.cpp
    src/gpu/gpu_virtualization.cpp
    src/training/training_interface.cpp
)

set(CORE_INFERENCE_HEADERS
    include/llm_inference_core/llm_inference_core.h
    include/llm_inference_core/inference/inference_engine.h
    include/llm_inference_core/model/model_manager.h
    include/llm_inference_core/model/model_selector.h
    include/llm_inference_core/model/model_downloader.h
    include/llm_inference_core/model/model_configurator.h
    include/llm_inference_core/model/model_registry.h
    include/llm_inference_core/model/model_manager_system.h
    include/core/customized_kernel.h
    include/core/python_cpp_bridge.h
    include/optimization/tensor_core_optimizer.h
    include/virtualization/virtual_compute_node.h
    include/memory/memory_partitioning.h
    include/parallel/parallel_llm_execution.h
    include/nvlink/nvlink_optimization.h
    include/cuda/cuda_stream_management.h
    include/scheduler/compute_node_scheduler.h
    include/bridge/python_cpp_bridge.h
    include/orchestration/multi_llm_orchestrator.h
    include/inference/inference_sharing.h
    include/multimodal/multimodal_processor.h
    include/mcp/mcp_core.h
    include/mcp/mcp_filesystem.h
    include/mcp/mcp_internet.h
    include/mcp/mcp_database.h
    include/mcp/mcp_application.h
    include/mcp/mcp_system_services.h
    include/mcp/mcp_security.h
    include/mcp/mcp_resources.h
    include/mcp/mcp_tool_registry.h
    include/api/rest_api.h
    include/benchmark/performance_benchmark.h
    include/async/async_processor.h
    include/model/model_manager.h
    include/monitoring/monitoring_system.h
    include/optimization/optimizer.h
    include/ipc/inter_llm_bus.h
    include/distributed/distributed_system.h
    include/gpu/gpu_virtualization.h
    include/training/training_interface.h
    src/llm_inference_core/tokenizer_interface/base_tokenizer.h
    src/llm_inference_core/tokenizer_interface/bpe_tokenizer.h
    src/llm_inference_core/tokenizer_interface/tokenizer_factory.h
)

# Create shared library
add_library(simple_engine SHARED ${SIMPLE_ENGINE_SOURCES} ${SIMPLE_ENGINE_HEADERS})

# Set include directories
target_include_directories(simple_engine
    PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/src/simple_engine
    PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

# Link libraries
target_link_libraries(simple_engine
    Threads::Threads
    nlohmann_json::nlohmann_json
)

# Create enhanced engine library
add_library(enhanced_engine SHARED ${ENHANCED_ENGINE_SOURCES} ${ENHANCED_ENGINE_HEADERS})

# Set include directories for enhanced engine
target_include_directories(enhanced_engine
    PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/src/enhanced_engine
    PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

# Link libraries for enhanced engine
target_link_libraries(enhanced_engine
    Threads::Threads
    nlohmann_json::nlohmann_json
    ${CUDA_LIBRARIES}
    ${CUDA_CUBLAS_LIBRARIES}
    ${CUDA_CUDNN_LIBRARIES}
    spdlog::spdlog
    fmt::fmt
)

# Create core inference engine library
add_library(core_inference_engine SHARED ${CORE_INFERENCE_SOURCES} ${CORE_INFERENCE_HEADERS})

# Set include directories for core inference engine
target_include_directories(core_inference_engine
    PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src/llm_inference_core
)

# Link libraries for core inference engine
target_link_libraries(core_inference_engine
    Threads::Threads
    nlohmann_json::nlohmann_json
    ${CUDA_LIBRARIES}
    ${CUDA_CUBLAS_LIBRARIES}
    ${CUDA_CUDNN_LIBRARIES}
    spdlog::spdlog
    fmt::fmt
    curl
    pybind11::module
)

# Set properties
set_target_properties(simple_engine PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED ON
    POSITION_INDEPENDENT_CODE ON
    VERSION ${PROJECT_VERSION}
    SOVERSION 1
)

# Create executable for testing
add_executable(simple_engine_test src/simple_engine/test_simple_engine.cpp)
target_link_libraries(simple_engine_test simple_engine)

# Create enhanced engine test
add_executable(enhanced_engine_test src/enhanced_engine/test_enhanced_engine.cpp)
target_link_libraries(enhanced_engine_test enhanced_engine spdlog::spdlog fmt::fmt)

# Create core inference engine test
add_executable(core_inference_engine_test tests/test_core_inference_engine.cpp)
target_link_libraries(core_inference_engine_test core_inference_engine spdlog::spdlog fmt::fmt)

# Create model management system test
add_executable(model_management_system_test tests/test_model_management_system.cpp)
target_link_libraries(model_management_system_test core_inference_engine spdlog::spdlog fmt::fmt curl)

# Create customized kernel and driver test
add_executable(customized_kernel_driver_test tests/test_customized_kernel_driver.cpp)
target_link_libraries(customized_kernel_driver_test core_inference_engine spdlog::spdlog fmt::fmt pybind11::module)

# Create tensor core optimization test
add_executable(tensor_core_optimization_test tests/test_tensor_core_optimization.cpp)
target_link_libraries(tensor_core_optimization_test core_inference_engine spdlog::spdlog fmt::fmt gtest gtest_main)

# Create virtual compute node system test
add_executable(virtual_compute_node_system_test tests/test_virtual_compute_node_system.cpp)
target_link_libraries(virtual_compute_node_system_test core_inference_engine spdlog::spdlog fmt::fmt gtest gtest_main)

# Create memory partitioning system test
add_executable(memory_partitioning_system_test tests/test_memory_partitioning_system.cpp)
target_link_libraries(memory_partitioning_system_test core_inference_engine spdlog::spdlog fmt::fmt gtest gtest_main)

# Create parallel LLM execution system test
add_executable(parallel_llm_execution_system_test tests/test_parallel_llm_execution_system.cpp)
target_link_libraries(parallel_llm_execution_system_test core_inference_engine spdlog::spdlog fmt::fmt gtest gtest_main)

# Create NVLink optimization system test
add_executable(nvlink_optimization_system_test tests/test_nvlink_optimization_system.cpp)
target_link_libraries(nvlink_optimization_system_test core_inference_engine spdlog::spdlog fmt::fmt gtest gtest_main)

# Create CUDA stream management system test
add_executable(cuda_stream_management_system_test tests/test_cuda_stream_management_system.cpp)
target_link_libraries(cuda_stream_management_system_test core_inference_engine spdlog::spdlog fmt::fmt gtest gtest_main)

# Create compute node scheduler system test
add_executable(compute_node_scheduler_system_test tests/test_compute_node_scheduler_system.cpp)
target_link_libraries(compute_node_scheduler_system_test core_inference_engine spdlog::spdlog fmt::fmt gtest gtest_main)

# Create Python-C++ bridge system test
add_executable(python_cpp_bridge_system_test tests/test_python_cpp_bridge_system.cpp)
target_link_libraries(python_cpp_bridge_system_test core_inference_engine spdlog::spdlog fmt::fmt gtest gtest_main)

# Create multi-LLM orchestration system test
add_executable(multi_llm_orchestration_system_test tests/test_multi_llm_orchestration_system.cpp)
target_link_libraries(multi_llm_orchestration_system_test core_inference_engine spdlog::spdlog fmt::fmt gtest gtest_main)

# Create inference sharing system test
add_executable(inference_sharing_system_test tests/test_inference_sharing_system.cpp)
target_link_libraries(inference_sharing_system_test core_inference_engine spdlog::spdlog fmt::fmt gtest gtest_main)

# Create multimodal processor test
add_executable(multimodal_processor_test tests/test_multimodal_processor.cpp)
target_link_libraries(multimodal_processor_test core_inference_engine spdlog::spdlog fmt::fmt gtest gtest_main)

# Create MCP core test
add_executable(mcp_core_test tests/test_mcp_core.cpp)
target_link_libraries(mcp_core_test core_inference_engine spdlog::spdlog fmt::fmt gtest gtest_main)

# Create demo executable for document summarization
add_executable(document_summarization_demo examples/document_summarization_demo.cpp)
target_link_libraries(document_summarization_demo core_inference_engine spdlog::spdlog fmt::fmt)

# Create integration tests
add_executable(integration_tests tests/integration_tests.cpp)
target_link_libraries(integration_tests core_inference_engine spdlog::spdlog fmt::fmt gtest gtest_main)

# Create Python module
pybind11_add_module(simple_engine_py src/simple_engine/python_bindings.cpp)
target_link_libraries(simple_engine_py PRIVATE simple_engine)

# Create enhanced Python module
pybind11_add_module(enhanced_engine_py src/enhanced_engine/enhanced_python_bindings.cpp)
target_link_libraries(enhanced_engine_py PRIVATE enhanced_engine)

# Install targets
install(TARGETS simple_engine enhanced_engine core_inference_engine
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
)

install(FILES ${SIMPLE_ENGINE_HEADERS}
    DESTINATION include/simple_engine
)

install(FILES ${CORE_INFERENCE_HEADERS}
    DESTINATION include/llm_inference_core
)
