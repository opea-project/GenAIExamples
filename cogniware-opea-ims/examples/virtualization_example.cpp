#include "virtualization/cuda_virtualization_driver.h"
#include "virtualization/memory_virtualization_manager.h"
#include "virtualization/compute_virtualization_manager.h"
#include <spdlog/spdlog.h>
#include <iostream>
#include <vector>
#include <thread>
#include <chrono>

using namespace cogniware;

void printVirtualGPUInfo(const VirtualGPUInfo& info) {
    std::cout << "Virtual GPU " << info.virtualGPUId << ":" << std::endl;
    std::cout << "  Status: ";
    switch (info.status) {
        case VirtualGPUStatus::CREATED: std::cout << "CREATED"; break;
        case VirtualGPUStatus::RUNNING: std::cout << "RUNNING"; break;
        case VirtualGPUStatus::PAUSED: std::cout << "PAUSED"; break;
        case VirtualGPUStatus::ERROR: std::cout << "ERROR"; break;
        case VirtualGPUStatus::DESTROYED: std::cout << "DESTROYED"; break;
        default: std::cout << "UNKNOWN"; break;
    }
    std::cout << std::endl;
    std::cout << "  Memory: " << info.memoryAllocated / (1024*1024) << "MB / " 
              << info.memoryLimit / (1024*1024) << "MB (" 
              << (info.memoryUtilization * 100) << "%)" << std::endl;
    std::cout << "  Compute: " << (info.computeUtilization * 100) << "%" << std::endl;
    std::cout << "  Active Streams: " << info.activeStreams << "/" << info.numStreams << std::endl;
    std::cout << std::endl;
}

void printVirtualMemoryInfo(const VirtualMemoryInfo& info) {
    std::cout << "Virtual Memory Space " << info.virtualGPUId << ":" << std::endl;
    std::cout << "  Total: " << info.totalSize / (1024*1024) << "MB" << std::endl;
    std::cout << "  Allocated: " << info.allocatedSize / (1024*1024) << "MB" << std::endl;
    std::cout << "  Free: " << info.freeSize / (1024*1024) << "MB" << std::endl;
    std::cout << "  Fragmentation: " << (info.fragmentationLevel * 100) << "%" << std::endl;
    std::cout << std::endl;
}

void printVirtualComputeUnitInfo(const VirtualComputeUnitInfo& info) {
    std::cout << "Virtual Compute Unit " << info.virtualGPUId << ":" << std::endl;
    std::cout << "  Status: ";
    switch (info.status) {
        case VirtualComputeUnitStatus::CREATED: std::cout << "CREATED"; break;
        case VirtualComputeUnitStatus::RUNNING: std::cout << "RUNNING"; break;
        case VirtualComputeUnitStatus::PAUSED: std::cout << "PAUSED"; break;
        case VirtualComputeUnitStatus::ERROR: std::cout << "ERROR"; break;
        case VirtualComputeUnitStatus::DESTROYED: std::cout << "DESTROYED"; break;
        default: std::cout << "UNKNOWN"; break;
    }
    std::cout << std::endl;
    std::cout << "  Compute Units: " << info.numComputeUnits << std::endl;
    std::cout << "  Compute Utilization: " << (info.computeUtilization * 100) << "%" << std::endl;
    std::cout << "  Memory Utilization: " << (info.memoryUtilization * 100) << "%" << std::endl;
    std::cout << "  Active Kernels: " << info.activeKernels << std::endl;
    std::cout << "  Total Kernels Executed: " << info.totalKernelsExecuted << std::endl;
    std::cout << "  Streams: " << info.numStreams << std::endl;
    std::cout << std::endl;
}

int main() {
    std::cout << "=== MSmartCompute CUDA Virtualization Example ===" << std::endl;
    std::cout << std::endl;

    // Initialize CUDA Virtualization Driver
    std::cout << "1. Initializing CUDA Virtualization Driver..." << std::endl;
    VirtualizationConfig vConfig;
    vConfig.deviceId = 0;
    vConfig.maxVirtualGPUs = 4;
    vConfig.numVirtualStreams = 8;
    vConfig.monitoringInterval = 100;
    vConfig.enableTensorCores = true;
    vConfig.enableMixedPrecision = true;

    auto& cudaDriver = CUDAVirtualizationDriver::getInstance();
    if (!cudaDriver.initialize(vConfig)) {
        std::cerr << "Failed to initialize CUDA Virtualization Driver" << std::endl;
        return 1;
    }
    std::cout << "✓ CUDA Virtualization Driver initialized" << std::endl;

    // Initialize Memory Virtualization Manager
    std::cout << "2. Initializing Memory Virtualization Manager..." << std::endl;
    MemoryVirtualizationConfig mConfig;
    mConfig.deviceId = 0;
    mConfig.pageSize = 4096;
    mConfig.maxPages = 1048576;
    mConfig.numMemoryPools = 8;
    mConfig.basePoolSize = 1024 * 1024;
    mConfig.baseBlockSize = 1024;
    mConfig.defragmentationThreshold = 0.3f;
    mConfig.enableAutomaticDefragmentation = true;
    mConfig.monitoringInterval = 1000;

    auto& memoryManager = MemoryVirtualizationManager::getInstance();
    if (!memoryManager.initialize(mConfig)) {
        std::cerr << "Failed to initialize Memory Virtualization Manager" << std::endl;
        return 1;
    }
    std::cout << "✓ Memory Virtualization Manager initialized" << std::endl;

    // Initialize Compute Virtualization Manager
    std::cout << "3. Initializing Compute Virtualization Manager..." << std::endl;
    ComputeVirtualizationConfig cConfig;
    cConfig.deviceId = 0;
    cConfig.maxVirtualComputeUnits = 8;
    cConfig.schedulingPolicy = "round_robin";
    cConfig.loadBalancingStrategy = "least_loaded";
    cConfig.timeSlice = 100;
    cConfig.monitoringInterval = 100;
    cConfig.enableDynamicScaling = true;
    cConfig.enablePreemption = false;

    auto& computeManager = ComputeVirtualizationManager::getInstance();
    if (!computeManager.initialize(cConfig)) {
        std::cerr << "Failed to initialize Compute Virtualization Manager" << std::endl;
        return 1;
    }
    std::cout << "✓ Compute Virtualization Manager initialized" << std::endl;

    // Create virtual GPUs
    std::cout << "4. Creating Virtual GPUs..." << std::endl;
    
    // Virtual GPU 1: High-performance configuration
    VirtualGPUConfig vgpu1Config;
    vgpu1Config.virtualGPUId = 1;
    vgpu1Config.memoryLimit = 4ULL * 1024 * 1024 * 1024; // 4GB
    vgpu1Config.numStreams = 4;
    vgpu1Config.enableTensorCores = true;
    vgpu1Config.enableMixedPrecision = true;
    vgpu1Config.computeShare = 0.5f;
    vgpu1Config.name = "High-Performance GPU";

    if (!cudaDriver.createVirtualGPU(vgpu1Config)) {
        std::cerr << "Failed to create Virtual GPU 1" << std::endl;
        return 1;
    }
    std::cout << "✓ Virtual GPU 1 created" << std::endl;

    // Virtual GPU 2: Balanced configuration
    VirtualGPUConfig vgpu2Config;
    vgpu2Config.virtualGPUId = 2;
    vgpu2Config.memoryLimit = 2ULL * 1024 * 1024 * 1024; // 2GB
    vgpu2Config.numStreams = 2;
    vgpu2Config.enableTensorCores = true;
    vgpu2Config.enableMixedPrecision = false;
    vgpu2Config.computeShare = 0.3f;
    vgpu2Config.name = "Balanced GPU";

    if (!cudaDriver.createVirtualGPU(vgpu2Config)) {
        std::cerr << "Failed to create Virtual GPU 2" << std::endl;
        return 1;
    }
    std::cout << "✓ Virtual GPU 2 created" << std::endl;

    // Virtual GPU 3: Lightweight configuration
    VirtualGPUConfig vgpu3Config;
    vgpu3Config.virtualGPUId = 3;
    vgpu3Config.memoryLimit = 1ULL * 1024 * 1024 * 1024; // 1GB
    vgpu3Config.numStreams = 1;
    vgpu3Config.enableTensorCores = false;
    vgpu3Config.enableMixedPrecision = false;
    vgpu3Config.computeShare = 0.2f;
    vgpu3Config.name = "Lightweight GPU";

    if (!cudaDriver.createVirtualGPU(vgpu3Config)) {
        std::cerr << "Failed to create Virtual GPU 3" << std::endl;
        return 1;
    }
    std::cout << "✓ Virtual GPU 3 created" << std::endl;

    // Create virtual memory spaces
    std::cout << "5. Creating Virtual Memory Spaces..." << std::endl;
    
    if (!memoryManager.createVirtualMemorySpace(1, 4ULL * 1024 * 1024 * 1024)) {
        std::cerr << "Failed to create virtual memory space for GPU 1" << std::endl;
        return 1;
    }
    std::cout << "✓ Virtual memory space 1 created" << std::endl;

    if (!memoryManager.createVirtualMemorySpace(2, 2ULL * 1024 * 1024 * 1024)) {
        std::cerr << "Failed to create virtual memory space for GPU 2" << std::endl;
        return 1;
    }
    std::cout << "✓ Virtual memory space 2 created" << std::endl;

    if (!memoryManager.createVirtualMemorySpace(3, 1ULL * 1024 * 1024 * 1024)) {
        std::cerr << "Failed to create virtual memory space for GPU 3" << std::endl;
        return 1;
    }
    std::cout << "✓ Virtual memory space 3 created" << std::endl;

    // Create virtual compute units
    std::cout << "6. Creating Virtual Compute Units..." << std::endl;
    
    VirtualComputeUnitConfig vcu1Config;
    vcu1Config.numComputeUnits = 8;
    vcu1Config.numStreams = 4;
    vcu1Config.maxConcurrentKernels = 16;
    vcu1Config.enableTensorCores = true;
    vcu1Config.enableMixedPrecision = true;
    vcu1Config.computeShare = 0.5f;
    vcu1Config.name = "High-Performance Compute Unit";

    if (!computeManager.createVirtualComputeUnit(1, vcu1Config)) {
        std::cerr << "Failed to create virtual compute unit 1" << std::endl;
        return 1;
    }
    std::cout << "✓ Virtual compute unit 1 created" << std::endl;

    VirtualComputeUnitConfig vcu2Config;
    vcu2Config.numComputeUnits = 4;
    vcu2Config.numStreams = 2;
    vcu2Config.maxConcurrentKernels = 8;
    vcu2Config.enableTensorCores = true;
    vcu2Config.enableMixedPrecision = false;
    vcu2Config.computeShare = 0.3f;
    vcu2Config.name = "Balanced Compute Unit";

    if (!computeManager.createVirtualComputeUnit(2, vcu2Config)) {
        std::cerr << "Failed to create virtual compute unit 2" << std::endl;
        return 1;
    }
    std::cout << "✓ Virtual compute unit 2 created" << std::endl;

    VirtualComputeUnitConfig vcu3Config;
    vcu3Config.numComputeUnits = 2;
    vcu3Config.numStreams = 1;
    vcu3Config.maxConcurrentKernels = 4;
    vcu3Config.enableTensorCores = false;
    vcu3Config.enableMixedPrecision = false;
    vcu3Config.computeShare = 0.2f;
    vcu3Config.name = "Lightweight Compute Unit";

    if (!computeManager.createVirtualComputeUnit(3, vcu3Config)) {
        std::cerr << "Failed to create virtual compute unit 3" << std::endl;
        return 1;
    }
    std::cout << "✓ Virtual compute unit 3 created" << std::endl;

    // Demonstrate memory allocation and operations
    std::cout << "7. Demonstrating Memory Operations..." << std::endl;
    
    // Allocate memory in virtual GPU 1
    void* ptr1 = nullptr;
    if (!cudaDriver.allocateMemory(1, 1024 * 1024, &ptr1)) {
        std::cerr << "Failed to allocate memory in virtual GPU 1" << std::endl;
        return 1;
    }
    std::cout << "✓ Allocated 1MB in virtual GPU 1" << std::endl;

    // Allocate memory in virtual GPU 2
    void* ptr2 = nullptr;
    if (!cudaDriver.allocateMemory(2, 512 * 1024, &ptr2)) {
        std::cerr << "Failed to allocate memory in virtual GPU 2" << std::endl;
        return 1;
    }
    std::cout << "✓ Allocated 512KB in virtual GPU 2" << std::endl;

    // Allocate memory in virtual GPU 3
    void* ptr3 = nullptr;
    if (!cudaDriver.allocateMemory(3, 256 * 1024, &ptr3)) {
        std::cerr << "Failed to allocate memory in virtual GPU 3" << std::endl;
        return 1;
    }
    std::cout << "✓ Allocated 256KB in virtual GPU 3" << std::endl;

    // Demonstrate compute operations
    std::cout << "8. Demonstrating Compute Operations..." << std::endl;
    
    // Create sample data for matrix multiplication
    const int m = 1024, n = 1024, k = 1024;
    size_t sizeA = m * k * sizeof(float);
    size_t sizeB = k * n * sizeof(float);
    size_t sizeC = m * n * sizeof(float);

    void *A1, *B1, *C1;
    void *A2, *B2, *C2;
    void *A3, *B3, *C3;

    // Allocate matrices in virtual GPUs
    cudaDriver.allocateMemory(1, sizeA, &A1);
    cudaDriver.allocateMemory(1, sizeB, &B1);
    cudaDriver.allocateMemory(1, sizeC, &C1);

    cudaDriver.allocateMemory(2, sizeA, &A2);
    cudaDriver.allocateMemory(2, sizeB, &B2);
    cudaDriver.allocateMemory(2, sizeC, &C2);

    cudaDriver.allocateMemory(3, sizeA, &A3);
    cudaDriver.allocateMemory(3, sizeB, &B3);
    cudaDriver.allocateMemory(3, sizeC, &C3);

    // Perform matrix multiplication on all virtual GPUs
    if (cudaDriver.matrixMultiply(1, A1, B1, C1, m, n, k, CUDA_R_32F, 0)) {
        std::cout << "✓ Matrix multiplication completed on virtual GPU 1" << std::endl;
    }

    if (cudaDriver.matrixMultiply(2, A2, B2, C2, m, n, k, CUDA_R_32F, 0)) {
        std::cout << "✓ Matrix multiplication completed on virtual GPU 2" << std::endl;
    }

    if (cudaDriver.matrixMultiply(3, A3, B3, C3, m, n, k, CUDA_R_32F, 0)) {
        std::cout << "✓ Matrix multiplication completed on virtual GPU 3" << std::endl;
    }

    // Demonstrate kernel execution
    std::cout << "9. Demonstrating Kernel Execution..." << std::endl;
    
    KernelConfig kernelConfig;
    kernelConfig.kernelName = "matrix_multiply";
    kernelConfig.gridDim = dim3(32, 32);
    kernelConfig.blockDim = dim3(16, 16);
    kernelConfig.sharedMemorySize = 0;
    kernelConfig.priority = 1;
    kernelConfig.kernelType = "compute";

    if (computeManager.executeKernel(1, kernelConfig, 0)) {
        std::cout << "✓ Kernel executed on virtual compute unit 1" << std::endl;
    }

    if (computeManager.executeKernel(2, kernelConfig, 0)) {
        std::cout << "✓ Kernel executed on virtual compute unit 2" << std::endl;
    }

    if (computeManager.executeKernel(3, kernelConfig, 0)) {
        std::cout << "✓ Kernel executed on virtual compute unit 3" << std::endl;
    }

    // Wait a bit for operations to complete
    std::this_thread::sleep_for(std::chrono::milliseconds(1000));

    // Display status information
    std::cout << "10. Current Status Information:" << std::endl;
    std::cout << "=================================" << std::endl;

    // Virtual GPU status
    auto vgpuInfos = cudaDriver.getAllVirtualGPUInfo();
    for (const auto& info : vgpuInfos) {
        printVirtualGPUInfo(info);
    }

    // Virtual memory status
    auto vmemInfos = memoryManager.getAllVirtualMemoryInfo();
    for (const auto& info : vmemInfos) {
        printVirtualMemoryInfo(info);
    }

    // Virtual compute unit status
    auto vcuInfos = computeManager.getAllVirtualComputeUnitInfo();
    for (const auto& info : vcuInfos) {
        printVirtualComputeUnitInfo(info);
    }

    // Demonstrate load balancing
    std::cout << "11. Demonstrating Load Balancing..." << std::endl;
    
    // Adjust compute shares to demonstrate load balancing
    computeManager.setComputeShare(1, 0.4f);
    computeManager.setComputeShare(2, 0.4f);
    computeManager.setComputeShare(3, 0.2f);
    
    std::cout << "✓ Compute shares adjusted for load balancing" << std::endl;

    // Demonstrate tensor core management
    std::cout << "12. Demonstrating Tensor Core Management..." << std::endl;
    
    computeManager.enableTensorCores(1);
    computeManager.enableTensorCores(2);
    computeManager.disableTensorCores(3);
    
    std::cout << "✓ Tensor cores configured" << std::endl;

    // Demonstrate memory defragmentation
    std::cout << "13. Demonstrating Memory Defragmentation..." << std::endl;
    
    if (memoryManager.defragment(1)) {
        std::cout << "✓ Memory defragmentation completed for virtual GPU 1" << std::endl;
    }

    if (memoryManager.defragment(2)) {
        std::cout << "✓ Memory defragmentation completed for virtual GPU 2" << std::endl;
    }

    if (memoryManager.defragment(3)) {
        std::cout << "✓ Memory defragmentation completed for virtual GPU 3" << std::endl;
    }

    // Cleanup
    std::cout << "14. Cleaning up resources..." << std::endl;
    
    // Free allocated memory
    cudaDriver.freeMemory(1, ptr1);
    cudaDriver.freeMemory(2, ptr2);
    cudaDriver.freeMemory(3, ptr3);
    
    cudaDriver.freeMemory(1, A1);
    cudaDriver.freeMemory(1, B1);
    cudaDriver.freeMemory(1, C1);
    
    cudaDriver.freeMemory(2, A2);
    cudaDriver.freeMemory(2, B2);
    cudaDriver.freeMemory(2, C2);
    
    cudaDriver.freeMemory(3, A3);
    cudaDriver.freeMemory(3, B3);
    cudaDriver.freeMemory(3, C3);

    // Destroy virtual compute units
    computeManager.destroyVirtualComputeUnit(1);
    computeManager.destroyVirtualComputeUnit(2);
    computeManager.destroyVirtualComputeUnit(3);

    // Destroy virtual memory spaces
    memoryManager.destroyVirtualMemorySpace(1);
    memoryManager.destroyVirtualMemorySpace(2);
    memoryManager.destroyVirtualMemorySpace(3);

    // Destroy virtual GPUs
    cudaDriver.destroyVirtualGPU(1);
    cudaDriver.destroyVirtualGPU(2);
    cudaDriver.destroyVirtualGPU(3);

    // Shutdown managers
    computeManager.shutdown();
    memoryManager.shutdown();
    cudaDriver.shutdown();

    std::cout << "✓ All resources cleaned up" << std::endl;
    std::cout << std::endl;
    std::cout << "=== CUDA Virtualization Example Completed Successfully ===" << std::endl;

    return 0;
} 