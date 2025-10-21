# CUDA Virtualization Drivers Guide

This guide provides comprehensive documentation for the MSmartCompute CUDA Virtualization Drivers, which enable advanced GPU virtualization capabilities for CUDA applications.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Installation](#installation)
5. [Quick Start](#quick-start)
6. [API Reference](#api-reference)
7. [Examples](#examples)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)
10. [Performance Tuning](#performance-tuning)

## Overview

The MSmartCompute CUDA Virtualization Drivers provide a complete solution for GPU virtualization, allowing multiple virtual GPUs to run on a single physical GPU with:

- **Resource Isolation**: Each virtual GPU has isolated memory and compute resources
- **Dynamic Resource Management**: Automatic allocation and deallocation of GPU resources
- **Load Balancing**: Intelligent distribution of workloads across virtual GPUs
- **Memory Virtualization**: Advanced memory management with defragmentation
- **Compute Virtualization**: Virtual compute units with scheduling and preemption
- **Monitoring**: Real-time monitoring of resource utilization and performance

### Key Features

- **Multi-tenant GPU Support**: Run multiple applications on a single GPU
- **Resource Quotas**: Set memory and compute limits for each virtual GPU
- **Tensor Core Management**: Enable/disable tensor cores per virtual GPU
- **Mixed Precision Support**: Configure precision settings independently
- **Automatic Defragmentation**: Maintain optimal memory layout
- **Load Balancing**: Distribute workloads for optimal performance
- **Real-time Monitoring**: Track resource usage and performance metrics

## Architecture

The CUDA Virtualization Drivers consist of three main components:

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
├─────────────────────────────────────────────────────────────┤
│              CUDA Virtualization Driver                     │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │   Memory        │ │   Compute       │ │   Resource      │ │
│  │ Virtualization  │ │ Virtualization  │ │   Monitor       │ │
│  │   Manager       │ │   Manager       │ │                 │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    CUDA Runtime Layer                       │
├─────────────────────────────────────────────────────────────┤
│                    Physical GPU                             │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

1. **CUDA Virtualization Driver**: Main interface for virtualization operations
2. **Memory Virtualization Manager**: Handles memory allocation, mapping, and defragmentation
3. **Compute Virtualization Manager**: Manages compute units, scheduling, and load balancing
4. **Resource Monitor**: Tracks resource usage and performance metrics

## Components

### 1. CUDA Virtualization Driver

The main driver that provides the high-level interface for GPU virtualization.

**Key Features:**
- Virtual GPU creation and management
- Memory allocation and deallocation
- Compute operations (matrix multiplication, convolution, etc.)
- Resource monitoring and statistics

### 2. Memory Virtualization Manager

Advanced memory management system with virtual-to-physical address mapping.

**Key Features:**
- Virtual memory spaces for each virtual GPU
- Page table management
- Memory pools for efficient allocation
- Automatic defragmentation
- Memory usage monitoring

### 3. Compute Virtualization Manager

Compute unit management with scheduling and load balancing.

**Key Features:**
- Virtual compute units
- Kernel execution management
- Load balancing across compute units
- Dynamic resource scaling
- Compute share management

## Installation

### Prerequisites

- CUDA Toolkit 11.0 or higher
- cuDNN 8.0 or higher
- NVIDIA GPU with compute capability 7.0 or higher
- C++17 compatible compiler
- CMake 3.15 or higher

### Building from Source

```bash
# Clone the repository
git clone <repository-url>
cd cogniware_engine_cpp

# Create build directory
mkdir build && cd build

# Configure with CMake
cmake .. -DCMAKE_BUILD_TYPE=Release

# Build
make -j$(nproc)

# Install
sudo make install
```

### Dependencies

The following dependencies are automatically installed:

- **CUDA Runtime**: GPU computing platform
- **cuBLAS**: Basic linear algebra operations
- **cuDNN**: Deep learning primitives
- **NVML**: GPU monitoring and management
- **spdlog**: Logging library
- **jsoncpp**: JSON parsing library

## Quick Start

### Basic Usage

```cpp
#include "virtualization/cuda_virtualization_driver.h"
#include "virtualization/memory_virtualization_manager.h"
#include "virtualization/compute_virtualization_manager.h"

using namespace cogniware;

int main() {
    // Initialize virtualization drivers
    VirtualizationConfig vConfig;
    vConfig.deviceId = 0;
    vConfig.maxVirtualGPUs = 4;
    vConfig.numVirtualStreams = 8;
    
    auto& cudaDriver = CUDAVirtualizationDriver::getInstance();
    cudaDriver.initialize(vConfig);
    
    // Create a virtual GPU
    VirtualGPUConfig vgpuConfig;
    vgpuConfig.virtualGPUId = 1;
    vgpuConfig.memoryLimit = 2ULL * 1024 * 1024 * 1024; // 2GB
    vgpuConfig.numStreams = 4;
    vgpuConfig.enableTensorCores = true;
    
    cudaDriver.createVirtualGPU(vgpuConfig);
    
    // Allocate memory
    void* ptr = nullptr;
    cudaDriver.allocateMemory(1, 1024 * 1024, &ptr); // 1MB
    
    // Perform compute operations
    cudaDriver.matrixMultiply(1, A, B, C, m, n, k, CUDA_R_32F, 0);
    
    // Cleanup
    cudaDriver.freeMemory(1, ptr);
    cudaDriver.destroyVirtualGPU(1);
    cudaDriver.shutdown();
    
    return 0;
}
```

### Advanced Usage

```cpp
// Initialize all virtualization managers
auto& memoryManager = MemoryVirtualizationManager::getInstance();
auto& computeManager = ComputeVirtualizationManager::getInstance();

MemoryVirtualizationConfig mConfig;
mConfig.deviceId = 0;
mConfig.pageSize = 4096;
mConfig.enableAutomaticDefragmentation = true;

ComputeVirtualizationConfig cConfig;
cConfig.deviceId = 0;
cConfig.maxVirtualComputeUnits = 8;
cConfig.enableDynamicScaling = true;

memoryManager.initialize(mConfig);
computeManager.initialize(cConfig);

// Create virtual memory space
memoryManager.createVirtualMemorySpace(1, 4ULL * 1024 * 1024 * 1024);

// Create virtual compute unit
VirtualComputeUnitConfig vcuConfig;
vcuConfig.numComputeUnits = 4;
vcuConfig.numStreams = 2;
vcuConfig.enableTensorCores = true;

computeManager.createVirtualComputeUnit(1, vcuConfig);

// Execute kernels
KernelConfig kernelConfig;
kernelConfig.kernelName = "matrix_multiply";
kernelConfig.gridDim = dim3(32, 32);
kernelConfig.blockDim = dim3(16, 16);

computeManager.executeKernel(1, kernelConfig, 0);
```

## API Reference

### CUDA Virtualization Driver

#### Initialization

```cpp
bool initialize(const VirtualizationConfig& config);
void shutdown();
```

#### Virtual GPU Management

```cpp
bool createVirtualGPU(const VirtualGPUConfig& config);
bool destroyVirtualGPU(int virtualGPUId);
VirtualGPUStatus getVirtualGPUStatus(int virtualGPUId) const;
VirtualGPUInfo getVirtualGPUInfo(int virtualGPUId) const;
std::vector<VirtualGPUInfo> getAllVirtualGPUInfo() const;
```

#### Memory Management

```cpp
bool allocateMemory(int virtualGPUId, size_t size, void** ptr);
bool freeMemory(int virtualGPUId, void* ptr);
bool copyMemory(int virtualGPUId, void* dst, const void* src, size_t size, cudaMemcpyKind kind);
bool memset(int virtualGPUId, void* ptr, int value, size_t size);
```

#### Compute Operations

```cpp
bool matrixMultiply(int virtualGPUId, const void* A, const void* B, void* C,
                   int m, int n, int k, cudaDataType_t dataType, int streamId = 0);

bool convolutionForward(int virtualGPUId, const void* input, const void* filter, void* output,
                       int batchSize, int inChannels, int outChannels,
                       int height, int width, int kernelSize,
                       int stride, int padding, cudaDataType_t dataType, int streamId = 0);

bool activationForward(int virtualGPUId, const void* input, void* output,
                      int batchSize, int channels, int height, int width,
                      const std::string& activationType, cudaDataType_t dataType, int streamId = 0);
```

### Memory Virtualization Manager

#### Initialization

```cpp
bool initialize(const MemoryVirtualizationConfig& config);
void shutdown();
```

#### Virtual Memory Space Management

```cpp
bool createVirtualMemorySpace(int virtualGPUId, size_t size);
bool destroyVirtualMemorySpace(int virtualGPUId);
```

#### Memory Operations

```cpp
void* allocateMemory(int virtualGPUId, size_t size, size_t alignment = 1);
bool freeMemory(int virtualGPUId, void* virtualAddress);
bool copyMemory(int virtualGPUId, void* dst, const void* src, size_t size, cudaMemcpyKind kind);
bool memset(int virtualGPUId, void* virtualAddress, int value, size_t size);
```

#### Memory Optimization

```cpp
bool defragment(int virtualGPUId);
bool compact(int virtualGPUId);
VirtualMemoryInfo getVirtualMemoryInfo(int virtualGPUId) const;
```

### Compute Virtualization Manager

#### Initialization

```cpp
bool initialize(const ComputeVirtualizationConfig& config);
void shutdown();
```

#### Virtual Compute Unit Management

```cpp
bool createVirtualComputeUnit(int virtualGPUId, const VirtualComputeUnitConfig& config);
bool destroyVirtualComputeUnit(int virtualGPUId);
VirtualComputeUnitInfo getVirtualComputeUnitInfo(int virtualGPUId) const;
```

#### Kernel Execution

```cpp
bool executeKernel(int virtualGPUId, const KernelConfig& kernelConfig, int streamId = 0);
bool synchronize(int virtualGPUId, int streamId);
bool cancelKernel(int virtualGPUId, int executionId);
```

#### Resource Management

```cpp
bool setComputeShare(int virtualGPUId, float computeShare);
bool enableTensorCores(int virtualGPUId);
bool disableTensorCores(int virtualGPUId);
bool scaleComputeUnits(int virtualGPUId, int numComputeUnits);
```

## Examples

### Example 1: Basic Virtual GPU Usage

```cpp
#include "virtualization/cuda_virtualization_driver.h"

int main() {
    // Initialize driver
    VirtualizationConfig config;
    config.deviceId = 0;
    config.maxVirtualGPUs = 2;
    
    auto& driver = CUDAVirtualizationDriver::getInstance();
    driver.initialize(config);
    
    // Create virtual GPU
    VirtualGPUConfig vgpuConfig;
    vgpuConfig.virtualGPUId = 1;
    vgpuConfig.memoryLimit = 1ULL * 1024 * 1024 * 1024; // 1GB
    vgpuConfig.numStreams = 2;
    
    driver.createVirtualGPU(vgpuConfig);
    
    // Allocate and use memory
    void* ptr = nullptr;
    driver.allocateMemory(1, 1024 * 1024, &ptr);
    
    // Perform operations
    // ... your CUDA operations here ...
    
    // Cleanup
    driver.freeMemory(1, ptr);
    driver.destroyVirtualGPU(1);
    driver.shutdown();
    
    return 0;
}
```

### Example 2: Multi-tenant GPU Application

```cpp
#include "virtualization/cuda_virtualization_driver.h"
#include <thread>
#include <vector>

void runApplication(int virtualGPUId, const std::string& appName) {
    auto& driver = CUDAVirtualizationDriver::getInstance();
    
    // Allocate memory for this application
    void* data = nullptr;
    driver.allocateMemory(virtualGPUId, 512 * 1024 * 1024, &data);
    
    // Run application-specific operations
    for (int i = 0; i < 100; ++i) {
        // Perform matrix operations
        // ... application logic ...
        
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
    
    // Cleanup
    driver.freeMemory(virtualGPUId, data);
}

int main() {
    // Initialize driver
    VirtualizationConfig config;
    config.deviceId = 0;
    config.maxVirtualGPUs = 4;
    
    auto& driver = CUDAVirtualizationDriver::getInstance();
    driver.initialize(config);
    
    // Create virtual GPUs for different applications
    std::vector<VirtualGPUConfig> vgpuConfigs = {
        {1, 2ULL * 1024 * 1024 * 1024, 4, true, true, 0.4f, "App1"},
        {2, 1ULL * 1024 * 1024 * 1024, 2, true, false, 0.3f, "App2"},
        {3, 1ULL * 1024 * 1024 * 1024, 2, false, false, 0.3f, "App3"}
    };
    
    for (const auto& config : vgpuConfigs) {
        driver.createVirtualGPU(config);
    }
    
    // Run applications in parallel
    std::vector<std::thread> threads;
    threads.emplace_back(runApplication, 1, "Application 1");
    threads.emplace_back(runApplication, 2, "Application 2");
    threads.emplace_back(runApplication, 3, "Application 3");
    
    // Wait for all applications to complete
    for (auto& thread : threads) {
        thread.join();
    }
    
    // Cleanup
    for (int i = 1; i <= 3; ++i) {
        driver.destroyVirtualGPU(i);
    }
    
    driver.shutdown();
    return 0;
}
```

### Example 3: Advanced Memory Management

```cpp
#include "virtualization/memory_virtualization_manager.h"

int main() {
    // Initialize memory manager
    MemoryVirtualizationConfig config;
    config.deviceId = 0;
    config.enableAutomaticDefragmentation = true;
    config.defragmentationThreshold = 0.3f;
    
    auto& memoryManager = MemoryVirtualizationManager::getInstance();
    memoryManager.initialize(config);
    
    // Create virtual memory spaces
    memoryManager.createVirtualMemorySpace(1, 4ULL * 1024 * 1024 * 1024);
    memoryManager.createVirtualMemorySpace(2, 2ULL * 1024 * 1024 * 1024);
    
    // Allocate memory with different patterns
    std::vector<void*> allocations1, allocations2;
    
    // Allocate in virtual GPU 1
    for (int i = 0; i < 10; ++i) {
        void* ptr = memoryManager.allocateMemory(1, 1024 * 1024, 4096);
        allocations1.push_back(ptr);
    }
    
    // Allocate in virtual GPU 2
    for (int i = 0; i < 5; ++i) {
        void* ptr = memoryManager.allocateMemory(2, 512 * 1024, 4096);
        allocations2.push_back(ptr);
    }
    
    // Free some allocations to create fragmentation
    for (int i = 0; i < 5; i += 2) {
        memoryManager.freeMemory(1, allocations1[i]);
        memoryManager.freeMemory(2, allocations2[i]);
    }
    
    // Trigger defragmentation
    memoryManager.defragment(1);
    memoryManager.defragment(2);
    
    // Get memory information
    auto info1 = memoryManager.getVirtualMemoryInfo(1);
    auto info2 = memoryManager.getVirtualMemoryInfo(2);
    
    std::cout << "Virtual GPU 1 fragmentation: " << (info1.fragmentationLevel * 100) << "%" << std::endl;
    std::cout << "Virtual GPU 2 fragmentation: " << (info2.fragmentationLevel * 100) << "%" << std::endl;
    
    // Cleanup
    for (void* ptr : allocations1) {
        if (ptr) memoryManager.freeMemory(1, ptr);
    }
    for (void* ptr : allocations2) {
        if (ptr) memoryManager.freeMemory(2, ptr);
    }
    
    memoryManager.destroyVirtualMemorySpace(1);
    memoryManager.destroyVirtualMemorySpace(2);
    memoryManager.shutdown();
    
    return 0;
}
```

## Best Practices

### 1. Resource Planning

- **Memory Allocation**: Plan memory usage based on application requirements
- **Compute Units**: Allocate compute units based on workload characteristics
- **Streams**: Use multiple streams for overlapping operations

### 2. Performance Optimization

- **Memory Pools**: Use memory pools for frequently allocated/deallocated memory
- **Defragmentation**: Monitor fragmentation levels and trigger defragmentation when needed
- **Load Balancing**: Distribute workloads evenly across virtual GPUs

### 3. Error Handling

```cpp
// Always check return values
if (!cudaDriver.createVirtualGPU(config)) {
    spdlog::error("Failed to create virtual GPU");
    return -1;
}

// Use try-catch for exception handling
try {
    void* ptr = nullptr;
    if (!cudaDriver.allocateMemory(virtualGPUId, size, &ptr)) {
        throw std::runtime_error("Memory allocation failed");
    }
} catch (const std::exception& e) {
    spdlog::error("Error: {}", e.what());
}
```

### 4. Resource Management

```cpp
// Use RAII for resource management
class VirtualGPUResource {
public:
    VirtualGPUResource(int virtualGPUId, const VirtualGPUConfig& config) 
        : virtualGPUId_(virtualGPUId) {
        cudaDriver_.createVirtualGPU(config);
    }
    
    ~VirtualGPUResource() {
        cudaDriver_.destroyVirtualGPU(virtualGPUId_);
    }
    
private:
    int virtualGPUId_;
    CUDAVirtualizationDriver& cudaDriver_ = CUDAVirtualizationDriver::getInstance();
};
```

### 5. Monitoring and Logging

```cpp
// Enable detailed logging
spdlog::set_level(spdlog::level::debug);

// Monitor resource usage
auto info = cudaDriver.getVirtualGPUInfo(virtualGPUId);
if (info.memoryUtilization > 0.8f) {
    spdlog::warn("High memory utilization: {}%", info.memoryUtilization * 100);
}
```

## Troubleshooting

### Common Issues

#### 1. Initialization Failures

**Problem**: Driver initialization fails
**Solution**: 
- Check CUDA installation and version
- Verify GPU compatibility
- Ensure sufficient system resources

#### 2. Memory Allocation Failures

**Problem**: Memory allocation returns nullptr
**Solution**:
- Check available memory in virtual GPU
- Verify memory limits
- Consider defragmentation

#### 3. Performance Issues

**Problem**: Poor performance compared to native CUDA
**Solution**:
- Check resource allocation
- Monitor fragmentation levels
- Optimize workload distribution

#### 4. Kernel Execution Failures

**Problem**: Kernels fail to execute
**Solution**:
- Verify compute unit allocation
- Check stream availability
- Monitor compute utilization

### Debug Information

Enable debug logging for detailed information:

```cpp
spdlog::set_level(spdlog::level::debug);
```

### Performance Monitoring

Use the monitoring APIs to track performance:

```cpp
// Monitor GPU utilization
float utilization = cudaDriver.getGPUUtilization();

// Monitor memory usage
auto memInfo = memoryManager.getVirtualMemoryInfo(virtualGPUId);

// Monitor compute usage
auto computeInfo = computeManager.getVirtualComputeUnitInfo(virtualGPUId);
```

## Performance Tuning

### 1. Memory Optimization

- **Pool Sizes**: Adjust memory pool sizes based on allocation patterns
- **Defragmentation Threshold**: Set appropriate defragmentation thresholds
- **Page Size**: Optimize page size for your workload

### 2. Compute Optimization

- **Compute Shares**: Balance compute shares across virtual GPUs
- **Stream Count**: Optimize number of streams for your workload
- **Kernel Scheduling**: Use appropriate scheduling policies

### 3. Load Balancing

- **Strategy Selection**: Choose appropriate load balancing strategy
- **Rebalancing Frequency**: Adjust rebalancing frequency
- **Threshold Tuning**: Set appropriate rebalancing thresholds

### 4. Monitoring and Profiling

```cpp
// Profile memory usage
auto start = std::chrono::high_resolution_clock::now();
// ... operations ...
auto end = std::chrono::high_resolution_clock::now();
auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

// Monitor resource utilization
auto info = cudaDriver.getVirtualGPUInfo(virtualGPUId);
spdlog::info("Memory utilization: {}%, Compute utilization: {}%", 
             info.memoryUtilization * 100, info.computeUtilization * 100);
```

## Conclusion

The MSmartCompute CUDA Virtualization Drivers provide a comprehensive solution for GPU virtualization, enabling efficient multi-tenant GPU computing. By following the guidelines in this document, you can effectively utilize these drivers to optimize your GPU applications and achieve better resource utilization.

For additional support and examples, refer to the source code and unit tests in the repository. 