#include "memory_virtualization_manager.h"
#include <spdlog/spdlog.h>
#include <cuda_runtime.h>
#include <algorithm>
#include <chrono>
#include <thread>
#include <mutex>
#include <queue>
#include <unordered_map>
#include <memory>

namespace msmartcompute {

MemoryVirtualizationManager& MemoryVirtualizationManager::getInstance() {
    static MemoryVirtualizationManager instance;
    return instance;
}

bool MemoryVirtualizationManager::initialize(const MemoryVirtualizationConfig& config) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    config_ = config;
    
    // Initialize CUDA
    cudaError_t cudaStatus = cudaSetDevice(config_.deviceId);
    if (cudaStatus != cudaSuccess) {
        spdlog::error("Failed to set CUDA device: {}", cudaGetErrorString(cudaStatus));
        return false;
    }
    
    // Get device properties
    cudaDeviceProp prop;
    cudaStatus = cudaGetDeviceProperties(&prop, config_.deviceId);
    if (cudaStatus != cudaSuccess) {
        spdlog::error("Failed to get device properties: {}", cudaGetErrorString(cudaStatus));
        return false;
    }
    
    deviceProps_ = prop;
    
    // Initialize memory pools
    if (!initializeMemoryPools()) {
        spdlog::error("Failed to initialize memory pools");
        return false;
    }
    
    // Initialize page tables
    if (!initializePageTables()) {
        spdlog::error("Failed to initialize page tables");
        return false;
    }
    
    // Initialize memory defragmentation
    if (!initializeDefragmentation()) {
        spdlog::error("Failed to initialize defragmentation");
        return false;
    }
    
    // Start memory monitoring thread
    running_ = true;
    monitoringThread_ = std::thread(&MemoryVirtualizationManager::monitoringLoop, this);
    
    spdlog::info("Memory Virtualization Manager initialized successfully");
    return true;
}

void MemoryVirtualizationManager::shutdown() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!running_) return;
    
    running_ = false;
    
    // Stop monitoring thread
    if (monitoringThread_.joinable()) {
        monitoringThread_.join();
    }
    
    // Cleanup memory pools
    cleanupMemoryPools();
    
    // Cleanup page tables
    cleanupPageTables();
    
    // Cleanup defragmentation
    cleanupDefragmentation();
    
    spdlog::info("Memory Virtualization Manager shutdown completed");
}

bool MemoryVirtualizationManager::createVirtualMemorySpace(int virtualGPUId, size_t size) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Check if virtual memory space already exists
    if (virtualMemorySpaces_.find(virtualGPUId) != virtualMemorySpaces_.end()) {
        spdlog::error("Virtual memory space for GPU {} already exists", virtualGPUId);
        return false;
    }
    
    // Create virtual memory space
    VirtualMemorySpace space;
    space.virtualGPUId = virtualGPUId;
    space.totalSize = size;
    space.allocatedSize = 0;
    space.freeSize = size;
    space.pageTable = std::make_unique<PageTable>();
    
    // Initialize page table
    if (!space.pageTable->initialize(size, config_.pageSize)) {
        spdlog::error("Failed to initialize page table for virtual GPU {}", virtualGPUId);
        return false;
    }
    
    // Allocate physical memory pool
    cudaError_t status = cudaMalloc(&space.physicalMemoryPool, size);
    if (status != cudaSuccess) {
        spdlog::error("Failed to allocate physical memory pool for virtual GPU {}: {}", 
                     virtualGPUId, cudaGetErrorString(status));
        return false;
    }
    
    virtualMemorySpaces_[virtualGPUId] = space;
    
    spdlog::info("Virtual memory space created for GPU {} with size {} MB", 
                 virtualGPUId, size / (1024 * 1024));
    return true;
}

bool MemoryVirtualizationManager::destroyVirtualMemorySpace(int virtualGPUId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = virtualMemorySpaces_.find(virtualGPUId);
    if (it == virtualMemorySpaces_.end()) {
        spdlog::error("Virtual memory space for GPU {} not found", virtualGPUId);
        return false;
    }
    
    VirtualMemorySpace& space = it->second;
    
    // Free all allocated memory
    for (auto& allocation : space.allocations) {
        if (allocation.physicalAddress) {
            cudaFree(allocation.physicalAddress);
        }
    }
    space.allocations.clear();
    
    // Free physical memory pool
    if (space.physicalMemoryPool) {
        cudaFree(space.physicalMemoryPool);
        space.physicalMemoryPool = nullptr;
    }
    
    // Destroy page table
    space.pageTable->shutdown();
    
    virtualMemorySpaces_.erase(it);
    
    spdlog::info("Virtual memory space destroyed for GPU {}", virtualGPUId);
    return true;
}

void* MemoryVirtualizationManager::allocateMemory(int virtualGPUId, size_t size, size_t alignment) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = virtualMemorySpaces_.find(virtualGPUId);
    if (it == virtualMemorySpaces_.end()) {
        spdlog::error("Virtual memory space for GPU {} not found", virtualGPUId);
        return nullptr;
    }
    
    VirtualMemorySpace& space = it->second;
    
    // Check if enough memory is available
    if (space.allocatedSize + size > space.totalSize) {
        spdlog::error("Insufficient memory in virtual GPU {}: requested {} bytes, available {} bytes", 
                     virtualGPUId, size, space.freeSize);
        return nullptr;
    }
    
    // Allocate physical memory
    void* physicalAddress = nullptr;
    cudaError_t status = cudaMalloc(&physicalAddress, size);
    if (status != cudaSuccess) {
        spdlog::error("Failed to allocate physical memory for virtual GPU {}: {}", 
                     virtualGPUId, cudaGetErrorString(status));
        return nullptr;
    }
    
    // Create virtual address mapping
    void* virtualAddress = space.pageTable->allocateVirtualAddress(size, alignment);
    if (!virtualAddress) {
        spdlog::error("Failed to allocate virtual address for virtual GPU {}", virtualGPUId);
        cudaFree(physicalAddress);
        return nullptr;
    }
    
    // Map virtual address to physical address
    if (!space.pageTable->mapVirtualToPhysical(virtualAddress, physicalAddress, size)) {
        spdlog::error("Failed to map virtual to physical address for virtual GPU {}", virtualGPUId);
        cudaFree(physicalAddress);
        space.pageTable->freeVirtualAddress(virtualAddress);
        return nullptr;
    }
    
    // Track allocation
    MemoryAllocation alloc;
    alloc.virtualAddress = virtualAddress;
    alloc.physicalAddress = physicalAddress;
    alloc.size = size;
    alloc.alignment = alignment;
    alloc.timestamp = std::chrono::steady_clock::now();
    space.allocations.push_back(alloc);
    
    // Update memory statistics
    space.allocatedSize += size;
    space.freeSize = space.totalSize - space.allocatedSize;
    
    spdlog::debug("Allocated {} bytes in virtual GPU {}: virtual={}, physical={}", 
                  size, virtualGPUId, virtualAddress, physicalAddress);
    
    return virtualAddress;
}

bool MemoryVirtualizationManager::freeMemory(int virtualGPUId, void* virtualAddress) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = virtualMemorySpaces_.find(virtualGPUId);
    if (it == virtualMemorySpaces_.end()) {
        spdlog::error("Virtual memory space for GPU {} not found", virtualGPUId);
        return false;
    }
    
    VirtualMemorySpace& space = it->second;
    
    // Find allocation
    auto allocIt = std::find_if(space.allocations.begin(), space.allocations.end(),
        [virtualAddress](const MemoryAllocation& alloc) {
            return alloc.virtualAddress == virtualAddress;
        });
    
    if (allocIt == space.allocations.end()) {
        spdlog::error("Memory allocation not found in virtual GPU {}", virtualGPUId);
        return false;
    }
    
    // Free physical memory
    cudaError_t status = cudaFree(allocIt->physicalAddress);
    if (status != cudaSuccess) {
        spdlog::error("Failed to free physical memory for virtual GPU {}: {}", 
                     virtualGPUId, cudaGetErrorString(status));
        return false;
    }
    
    // Unmap virtual address
    if (!space.pageTable->unmapVirtualAddress(virtualAddress)) {
        spdlog::error("Failed to unmap virtual address for virtual GPU {}", virtualGPUId);
        return false;
    }
    
    // Free virtual address
    space.pageTable->freeVirtualAddress(virtualAddress);
    
    // Update memory statistics
    space.allocatedSize -= allocIt->size;
    space.freeSize = space.totalSize - space.allocatedSize;
    
    // Remove allocation
    space.allocations.erase(allocIt);
    
    spdlog::debug("Freed memory in virtual GPU {}: virtual={}", virtualGPUId, virtualAddress);
    return true;
}

bool MemoryVirtualizationManager::copyMemory(int virtualGPUId, 
                                            void* dst, const void* src, 
                                            size_t size, cudaMemcpyKind kind) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = virtualMemorySpaces_.find(virtualGPUId);
    if (it == virtualMemorySpaces_.end()) {
        spdlog::error("Virtual memory space for GPU {} not found", virtualGPUId);
        return false;
    }
    
    VirtualMemorySpace& space = it->second;
    
    // Get physical addresses
    void* physicalDst = space.pageTable->getPhysicalAddress(dst);
    void* physicalSrc = space.pageTable->getPhysicalAddress(const_cast<void*>(src));
    
    if (!physicalDst || !physicalSrc) {
        spdlog::error("Failed to get physical addresses for memory copy in virtual GPU {}", virtualGPUId);
        return false;
    }
    
    // Perform memory copy
    cudaError_t status = cudaMemcpy(physicalDst, physicalSrc, size, kind);
    if (status != cudaSuccess) {
        spdlog::error("Failed to copy memory in virtual GPU {}: {}", 
                     virtualGPUId, cudaGetErrorString(status));
        return false;
    }
    
    return true;
}

bool MemoryVirtualizationManager::memset(int virtualGPUId, void* virtualAddress, int value, size_t size) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = virtualMemorySpaces_.find(virtualGPUId);
    if (it == virtualMemorySpaces_.end()) {
        spdlog::error("Virtual memory space for GPU {} not found", virtualGPUId);
        return false;
    }
    
    VirtualMemorySpace& space = it->second;
    
    // Get physical address
    void* physicalAddress = space.pageTable->getPhysicalAddress(virtualAddress);
    if (!physicalAddress) {
        spdlog::error("Failed to get physical address for memset in virtual GPU {}", virtualGPUId);
        return false;
    }
    
    // Perform memset
    cudaError_t status = cudaMemset(physicalAddress, value, size);
    if (status != cudaSuccess) {
        spdlog::error("Failed to memset in virtual GPU {}: {}", 
                     virtualGPUId, cudaGetErrorString(status));
        return false;
    }
    
    return true;
}

VirtualMemoryInfo MemoryVirtualizationManager::getVirtualMemoryInfo(int virtualGPUId) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    VirtualMemoryInfo info;
    info.virtualGPUId = virtualGPUId;
    info.totalSize = 0;
    info.allocatedSize = 0;
    info.freeSize = 0;
    info.fragmentationLevel = 0.0f;
    
    auto it = virtualMemorySpaces_.find(virtualGPUId);
    if (it == virtualMemorySpaces_.end()) {
        return info;
    }
    
    const VirtualMemorySpace& space = it->second;
    info.totalSize = space.totalSize;
    info.allocatedSize = space.allocatedSize;
    info.freeSize = space.freeSize;
    info.fragmentationLevel = calculateFragmentationLevel(space);
    
    return info;
}

std::vector<VirtualMemoryInfo> MemoryVirtualizationManager::getAllVirtualMemoryInfo() const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    std::vector<VirtualMemoryInfo> infos;
    infos.reserve(virtualMemorySpaces_.size());
    
    for (const auto& pair : virtualMemorySpaces_) {
        infos.push_back(getVirtualMemoryInfo(pair.first));
    }
    
    return infos;
}

bool MemoryVirtualizationManager::defragment(int virtualGPUId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = virtualMemorySpaces_.find(virtualGPUId);
    if (it == virtualMemorySpaces_.end()) {
        spdlog::error("Virtual memory space for GPU {} not found", virtualGPUId);
        return false;
    }
    
    VirtualMemorySpace& space = it->second;
    
    // Perform defragmentation
    if (!defragmentationEngine_->defragment(space)) {
        spdlog::error("Failed to defragment virtual memory space for GPU {}", virtualGPUId);
        return false;
    }
    
    spdlog::info("Defragmentation completed for virtual GPU {}", virtualGPUId);
    return true;
}

bool MemoryVirtualizationManager::initializeMemoryPools() {
    // Initialize different memory pools for different allocation sizes
    memoryPools_.resize(config_.numMemoryPools);
    
    for (int i = 0; i < config_.numMemoryPools; ++i) {
        size_t poolSize = config_.basePoolSize * (1 << i);  // Exponential growth
        size_t blockSize = config_.baseBlockSize * (1 << i);
        
        MemoryPool& pool = memoryPools_[i];
        pool.blockSize = blockSize;
        pool.totalSize = poolSize;
        pool.allocatedSize = 0;
        pool.freeSize = poolSize;
        
        // Allocate pool memory
        cudaError_t status = cudaMalloc(&pool.memory, poolSize);
        if (status != cudaSuccess) {
            spdlog::error("Failed to allocate memory pool {}: {}", i, cudaGetErrorString(status));
            return false;
        }
        
        // Initialize free blocks
        pool.freeBlocks.clear();
        size_t numBlocks = poolSize / blockSize;
        for (size_t j = 0; j < numBlocks; ++j) {
            void* blockAddress = static_cast<char*>(pool.memory) + (j * blockSize);
            pool.freeBlocks.push_back(blockAddress);
        }
    }
    
    spdlog::info("Memory pools initialized with {} pools", config_.numMemoryPools);
    return true;
}

bool MemoryVirtualizationManager::initializePageTables() {
    // Initialize page table management
    pageTableManager_ = std::make_unique<PageTableManager>();
    
    if (!pageTableManager_->initialize(config_.pageSize, config_.maxPages)) {
        spdlog::error("Failed to initialize page table manager");
        return false;
    }
    
    spdlog::info("Page tables initialized with page size {} bytes", config_.pageSize);
    return true;
}

bool MemoryVirtualizationManager::initializeDefragmentation() {
    // Initialize defragmentation engine
    defragmentationEngine_ = std::make_unique<DefragmentationEngine>();
    
    if (!defragmentationEngine_->initialize(config_.defragmentationThreshold)) {
        spdlog::error("Failed to initialize defragmentation engine");
        return false;
    }
    
    spdlog::info("Defragmentation engine initialized with threshold {}", config_.defragmentationThreshold);
    return true;
}

void MemoryVirtualizationManager::cleanupMemoryPools() {
    for (auto& pool : memoryPools_) {
        if (pool.memory) {
            cudaFree(pool.memory);
            pool.memory = nullptr;
        }
        pool.freeBlocks.clear();
    }
    memoryPools_.clear();
}

void MemoryVirtualizationManager::cleanupPageTables() {
    if (pageTableManager_) {
        pageTableManager_->shutdown();
        pageTableManager_.reset();
    }
}

void MemoryVirtualizationManager::cleanupDefragmentation() {
    if (defragmentationEngine_) {
        defragmentationEngine_->shutdown();
        defragmentationEngine_.reset();
    }
}

void MemoryVirtualizationManager::monitoringLoop() {
    while (running_) {
        // Update memory statistics
        updateMemoryStatistics();
        
        // Check for fragmentation
        checkFragmentation();
        
        // Perform automatic defragmentation if needed
        performAutomaticDefragmentation();
        
        // Sleep for monitoring interval
        std::this_thread::sleep_for(std::chrono::milliseconds(config_.monitoringInterval));
    }
}

void MemoryVirtualizationManager::updateMemoryStatistics() {
    for (auto& pair : virtualMemorySpaces_) {
        VirtualMemorySpace& space = pair.second;
        
        // Update allocation statistics
        space.allocatedSize = 0;
        for (const auto& alloc : space.allocations) {
            space.allocatedSize += alloc.size;
        }
        space.freeSize = space.totalSize - space.allocatedSize;
    }
}

void MemoryVirtualizationManager::checkFragmentation() {
    for (auto& pair : virtualMemorySpaces_) {
        int virtualGPUId = pair.first;
        VirtualMemorySpace& space = pair.second;
        
        float fragmentationLevel = calculateFragmentationLevel(space);
        if (fragmentationLevel > config_.defragmentationThreshold) {
            spdlog::warn("High fragmentation detected in virtual GPU {}: {:.2f}%", 
                        virtualGPUId, fragmentationLevel * 100.0f);
        }
    }
}

void MemoryVirtualizationManager::performAutomaticDefragmentation() {
    for (auto& pair : virtualMemorySpaces_) {
        int virtualGPUId = pair.first;
        VirtualMemorySpace& space = pair.second;
        
        float fragmentationLevel = calculateFragmentationLevel(space);
        if (fragmentationLevel > config_.defragmentationThreshold && 
            config_.enableAutomaticDefragmentation) {
            
            spdlog::info("Performing automatic defragmentation for virtual GPU {}", virtualGPUId);
            defragment(virtualGPUId);
        }
    }
}

float MemoryVirtualizationManager::calculateFragmentationLevel(const VirtualMemorySpace& space) const {
    if (space.allocations.empty()) {
        return 0.0f;
    }
    
    // Calculate fragmentation based on allocation patterns
    size_t totalGaps = 0;
    size_t totalAllocated = 0;
    
    // Sort allocations by address
    std::vector<MemoryAllocation> sortedAllocs = space.allocations;
    std::sort(sortedAllocs.begin(), sortedAllocs.end(),
        [](const MemoryAllocation& a, const MemoryAllocation& b) {
            return a.virtualAddress < b.virtualAddress;
        });
    
    // Calculate gaps between allocations
    for (size_t i = 0; i < sortedAllocs.size() - 1; ++i) {
        uintptr_t currentEnd = reinterpret_cast<uintptr_t>(sortedAllocs[i].virtualAddress) + 
                              sortedAllocs[i].size;
        uintptr_t nextStart = reinterpret_cast<uintptr_t>(sortedAllocs[i + 1].virtualAddress);
        
        if (nextStart > currentEnd) {
            totalGaps += nextStart - currentEnd;
        }
        totalAllocated += sortedAllocs[i].size;
    }
    
    if (totalAllocated == 0) {
        return 0.0f;
    }
    
    return static_cast<float>(totalGaps) / totalAllocated;
}

} // namespace msmartcompute 