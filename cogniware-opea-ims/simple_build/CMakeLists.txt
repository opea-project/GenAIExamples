cmake_minimum_required(VERSION 3.15)
project(cogniware_simple VERSION 1.0.0 LANGUAGES CXX CUDA)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Set CUDA standard
set(CMAKE_CUDA_STANDARD 17)
set(CMAKE_CUDA_STANDARD_REQUIRED ON)

# Find required packages
find_package(CUDA REQUIRED)
find_package(Threads REQUIRED)

# Set CUDA architecture for RTX 4050 (Ada Lovelace)
set(CMAKE_CUDA_ARCHITECTURES 89)
set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} -O3 -arch=sm_89")

# Compiler flags
if(MSVC)
    add_compile_options(/W4 /utf-8)
else()
    add_compile_options(-Wall -Wextra -O3)
    add_compile_options(-march=native -mtune=native)
endif()

# Add source files
set(SOURCES
    ../src/llm_inference_core.cpp
    ../src/engine.cpp
    ../src/knowledge_training_interface/cuda_kernels.cu
)

set(HEADERS
    ../include/llm_inference_core.h
    ../include/engine.h
)

# Create main library
add_library(cogniware_simple SHARED ${SOURCES} ${HEADERS})

# Set include directories
target_include_directories(cogniware_simple
    PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/../include
    ${CUDA_INCLUDE_DIRS}
    PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/../src
)

# Link libraries
target_link_libraries(cogniware_simple
    PUBLIC
    ${CUDA_LIBRARIES}
    ${CUDA_CUBLAS_LIBRARIES}
    ${CUDA_CURAND_LIBRARIES}
    Threads::Threads
)

# Set properties
set_target_properties(cogniware_simple PROPERTIES
    CUDA_SEPARABLE_COMPILATION ON
    POSITION_INDEPENDENT_CODE ON
)

# Create Python module
find_package(pybind11 REQUIRED)
pybind11_add_module(cogniware_python ../python/msmartcompute_engine_python.cpp)
target_link_libraries(cogniware_python PRIVATE cogniware_simple)

# Install targets
install(TARGETS cogniware_simple cogniware_python
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION bin
)

