#ifndef MSMARTCOMPUTE_MEMORY_VIRTUALIZATION_MANAGER_H
#define MSMARTCOMPUTE_MEMORY_VIRTUALIZATION_MANAGER_H

#include <cuda_runtime.h>
#include <vector>
#include <unordered_map>
#include <memory>
#include <mutex>
#include <thread>
#include <chrono>
#include <string>

namespace cogniware {

// Forward declarations
class PageTable;
class PageTableManager;
class DefragmentationEngine;

/**
 * @brief Memory virtualization configuration
 */
struct MemoryVirtualizationConfig {
    int deviceId = 0;                    // Physical GPU device ID
    size_t pageSize = 4096;              // Page size in bytes
    size_t maxPages = 1048576;           // Maximum number of pages (4GB / 4KB)
    int numMemoryPools = 8;              // Number of memory pools
    size_t basePoolSize = 1024 * 1024;   // Base pool size (1MB)
    size_t baseBlockSize = 1024;         // Base block size (1KB)
    float defragmentationThreshold = 0.3f; // Fragmentation threshold for defragmentation
    bool enableAutomaticDefragmentation = true;
    int monitoringInterval = 1000;       // Monitoring interval in milliseconds
};

/**
 * @brief Memory pool structure
 */
struct MemoryPool {
    void* memory = nullptr;              // Pool memory
    size_t blockSize;                    // Block size
    size_t totalSize;                    // Total pool size
    size_t allocatedSize;                // Allocated size
    size_t freeSize;                     // Free size
    std::vector<void*> freeBlocks;       // Free block list
};

/**
 * @brief Memory allocation tracking
 */
struct MemoryAllocation {
    void* virtualAddress;                // Virtual address
    void* physicalAddress;               // Physical address
    size_t size;                         // Allocation size
    size_t alignment;                    // Alignment requirement
    std::chrono::steady_clock::time_point timestamp;  // Allocation timestamp
    std::string tag;                     // Allocation tag
};

/**
 * @brief Virtual memory space
 */
struct VirtualMemorySpace {
    int virtualGPUId;                    // Virtual GPU ID
    size_t totalSize;                    // Total memory size
    size_t allocatedSize;                // Allocated memory size
    size_t freeSize;                     // Free memory size
    void* physicalMemoryPool;            // Physical memory pool
    std::unique_ptr<PageTable> pageTable; // Page table
    std::vector<MemoryAllocation> allocations; // Memory allocations
};

/**
 * @brief Virtual memory information
 */
struct VirtualMemoryInfo {
    int virtualGPUId;                    // Virtual GPU ID
    size_t totalSize;                    // Total memory size
    size_t allocatedSize;                // Allocated memory size
    size_t freeSize;                     // Free memory size
    float fragmentationLevel;            // Memory fragmentation level (0.0-1.0)
};

/**
 * @brief Memory Virtualization Manager
 * 
 * This class provides advanced memory virtualization capabilities for GPU memory.
 * It includes features like:
 * - Virtual memory spaces for each virtual GPU
 * - Page table management for virtual-to-physical address mapping
 * - Memory pools for efficient allocation
 * - Automatic defragmentation
 * - Memory monitoring and statistics
 */
class MemoryVirtualizationManager {
public:
    // Singleton pattern
    static MemoryVirtualizationManager& getInstance();
    
    // Disable copy constructor and assignment operator
    MemoryVirtualizationManager(const MemoryVirtualizationManager&) = delete;
    MemoryVirtualizationManager& operator=(const MemoryVirtualizationManager&) = delete;
    
    // Initialization and shutdown
    bool initialize(const MemoryVirtualizationConfig& config);
    void shutdown();
    
    // Virtual memory space management
    bool createVirtualMemorySpace(int virtualGPUId, size_t size);
    bool destroyVirtualMemorySpace(int virtualGPUId);
    
    // Memory allocation and deallocation
    void* allocateMemory(int virtualGPUId, size_t size, size_t alignment = 1);
    bool freeMemory(int virtualGPUId, void* virtualAddress);
    
    // Memory operations
    bool copyMemory(int virtualGPUId, void* dst, const void* src, size_t size, cudaMemcpyKind kind);
    bool memset(int virtualGPUId, void* virtualAddress, int value, size_t size);
    
    // Memory information and statistics
    VirtualMemoryInfo getVirtualMemoryInfo(int virtualGPUId) const;
    std::vector<VirtualMemoryInfo> getAllVirtualMemoryInfo() const;
    
    // Memory optimization
    bool defragment(int virtualGPUId);
    bool compact(int virtualGPUId);
    
    // Configuration
    MemoryVirtualizationConfig getConfig() const { return config_; }
    bool isInitialized() const { return initialized_; }

private:
    // Private constructor for singleton
    MemoryVirtualizationManager() = default;
    ~MemoryVirtualizationManager() = default;
    
    // Configuration
    MemoryVirtualizationConfig config_;
    cudaDeviceProp deviceProps_;
    bool initialized_ = false;
    
    // Memory pools
    std::vector<MemoryPool> memoryPools_;
    
    // Virtual memory spaces
    std::unordered_map<int, VirtualMemorySpace> virtualMemorySpaces_;
    
    // Page table management
    std::unique_ptr<PageTableManager> pageTableManager_;
    
    // Defragmentation engine
    std::unique_ptr<DefragmentationEngine> defragmentationEngine_;
    
    // Threading
    std::thread monitoringThread_;
    mutable std::mutex mutex_;
    bool running_ = false;
    
    // Initialization helpers
    bool initializeMemoryPools();
    bool initializePageTables();
    bool initializeDefragmentation();
    
    // Cleanup helpers
    void cleanupMemoryPools();
    void cleanupPageTables();
    void cleanupDefragmentation();
    
    // Monitoring
    void monitoringLoop();
    void updateMemoryStatistics();
    void checkFragmentation();
    void performAutomaticDefragmentation();
    
    // Utility functions
    float calculateFragmentationLevel(const VirtualMemorySpace& space) const;
    bool validateVirtualAddress(int virtualGPUId, void* virtualAddress) const;
    void* findBestFitPool(size_t size) const;
    
    // Memory pool management
    void* allocateFromPool(size_t size);
    bool freeToPool(void* ptr);
    void* reallocateInPool(void* ptr, size_t newSize);
    
    // Error handling
    void logError(const std::string& operation, const std::string& error) const;
    void logWarning(const std::string& operation, const std::string& warning) const;
};

/**
 * @brief Page Table Entry
 */
struct PageTableEntry {
    void* virtualAddress;                // Virtual address
    void* physicalAddress;               // Physical address
    size_t size;                         // Page size
    bool valid;                          // Valid flag
    bool dirty;                          // Dirty flag
    bool accessed;                       // Accessed flag
    std::chrono::steady_clock::time_point lastAccess; // Last access time
};

/**
 * @brief Page Table
 */
class PageTable {
public:
    PageTable() = default;
    ~PageTable() = default;
    
    bool initialize(size_t virtualMemorySize, size_t pageSize);
    void shutdown();
    
    void* allocateVirtualAddress(size_t size, size_t alignment);
    bool freeVirtualAddress(void* virtualAddress);
    bool mapVirtualToPhysical(void* virtualAddress, void* physicalAddress, size_t size);
    bool unmapVirtualAddress(void* virtualAddress);
    void* getPhysicalAddress(void* virtualAddress) const;
    
    size_t getPageSize() const { return pageSize_; }
    size_t getTotalPages() const { return totalPages_; }
    size_t getUsedPages() const { return usedPages_; }

private:
    size_t pageSize_ = 4096;
    size_t totalPages_ = 0;
    size_t usedPages_ = 0;
    void* baseVirtualAddress_ = nullptr;
    std::vector<PageTableEntry> entries_;
    std::vector<void*> freeVirtualAddresses_;
    
    bool findFreeVirtualAddress(size_t size, size_t alignment, void** address);
    size_t getPageIndex(void* virtualAddress) const;
    bool isValidVirtualAddress(void* virtualAddress) const;
};

/**
 * @brief Page Table Manager
 */
class PageTableManager {
public:
    PageTableManager() = default;
    ~PageTableManager() = default;
    
    bool initialize(size_t pageSize, size_t maxPages);
    void shutdown();
    
    std::unique_ptr<PageTable> createPageTable(size_t virtualMemorySize);
    void destroyPageTable(std::unique_ptr<PageTable> pageTable);
    
    size_t getPageSize() const { return pageSize_; }
    size_t getMaxPages() const { return maxPages_; }

private:
    size_t pageSize_ = 4096;
    size_t maxPages_ = 1048576;
    std::vector<std::unique_ptr<PageTable>> pageTables_;
};

/**
 * @brief Defragmentation Engine
 */
class DefragmentationEngine {
public:
    DefragmentationEngine() = default;
    ~DefragmentationEngine() = default;
    
    bool initialize(float threshold);
    void shutdown();
    
    bool defragment(VirtualMemorySpace& space);
    bool compact(VirtualMemorySpace& space);
    
    float getThreshold() const { return threshold_; }

private:
    float threshold_ = 0.3f;
    bool running_ = false;
    
    bool shouldDefragment(const VirtualMemorySpace& space) const;
    bool moveAllocation(VirtualMemorySpace& space, MemoryAllocation& alloc, void* newVirtualAddress);
    void* findOptimalLocation(const VirtualMemorySpace& space, size_t size) const;
};

} // namespace cogniware

#endif // MSMARTCOMPUTE_MEMORY_VIRTUALIZATION_MANAGER_H 