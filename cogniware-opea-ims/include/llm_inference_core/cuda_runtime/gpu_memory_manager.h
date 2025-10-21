#pragma once

#include <cuda_runtime.h>
#include <memory>
#include <mutex>
#include <unordered_map>
#include <vector>

namespace cogniware {

class GPUMemoryManager {
public:
    static GPUMemoryManager& getInstance();

    // Delete copy constructor and assignment operator
    GPUMemoryManager(const GPUMemoryManager&) = delete;
    GPUMemoryManager& operator=(const GPUMemoryManager&) = delete;

    // Memory allocation and deallocation
    void* allocate(size_t size);
    void deallocate(void* ptr);
    
    // Memory pool management
    void* allocateFromPool(size_t size);
    void returnToPool(void* ptr);
    
    // Stream operations
    cudaStream_t createStream();
    void destroyStream(cudaStream_t stream);
    void synchronizeStream(cudaStream_t stream);
    
    // Memory statistics
    size_t getTotalAllocatedMemory() const;
    size_t getPeakMemoryUsage() const;
    size_t getAvailableMemory() const;
    
    // Memory transfer operations
    void copyToDevice(void* dst, const void* src, size_t size, cudaStream_t stream = nullptr);
    void copyToHost(void* dst, const void* src, size_t size, cudaStream_t stream = nullptr);
    
    // Memory pool configuration
    void setPoolSize(size_t size);
    void setMaxPoolSize(size_t size);
    
    // Error handling
    const char* getLastError() const;
    void clearLastError();

private:
    GPUMemoryManager();
    ~GPUMemoryManager();

    struct MemoryBlock {
        void* ptr;
        size_t size;
        bool inUse;
    };

    struct StreamInfo {
        cudaStream_t stream;
        bool active;
    };

    // Memory pool management
    std::vector<MemoryBlock> memoryPool_;
    size_t poolSize_;
    size_t maxPoolSize_;
    
    // Stream management
    std::vector<StreamInfo> streams_;
    
    // Statistics
    size_t totalAllocated_;
    size_t peakUsage_;
    
    // Error handling
    std::string lastError_;
    
    // Thread safety
    mutable std::mutex mutex_;
    
    // Helper methods
    void initializeMemoryPool();
    void cleanupMemoryPool();
    void updatePeakUsage(size_t currentUsage);
    bool isMemoryPoolFull() const;
    void* findFreeBlock(size_t size);
    void defragmentPool();
};

} // namespace cogniware 