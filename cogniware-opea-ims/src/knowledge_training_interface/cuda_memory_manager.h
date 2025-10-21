#ifndef MSMARTCOMPUTE_CUDA_MEMORY_MANAGER_H
#define MSMARTCOMPUTE_CUDA_MEMORY_MANAGER_H

#include <cuda_runtime.h>
#include <memory>
#include <vector>
#include <unordered_map>
#include <mutex>
#include <string>
#include <functional>

namespace cogniware {

/**
 * @brief Memory allocation strategy
 */
enum class MemoryStrategy {
    POOL,           // Use memory pool
    DIRECT,         // Direct allocation
    STREAMING       // Streaming memory allocation
};

/**
 * @brief Memory block information
 */
struct MemoryBlock {
    void* ptr;
    size_t size;
    bool inUse;
    cudaStream_t stream;
    std::string tag;
};

/**
 * @brief Memory pool configuration
 */
struct MemoryPoolConfig {
    size_t initialSize;
    size_t maxSize;
    size_t blockSize;
    MemoryStrategy strategy;
    float growthFactor;
    size_t maxBlocks;
};

/**
 * @brief CUDA memory manager class
 */
class CUDAMemoryManager {
public:
    static CUDAMemoryManager& getInstance();

    // Memory pool management
    bool initialize(const MemoryPoolConfig& config);
    void shutdown();
    bool setMemoryStrategy(MemoryStrategy strategy);
    MemoryStrategy getMemoryStrategy() const;

    // Memory allocation
    void* allocate(size_t size, const std::string& tag = "", cudaStream_t stream = nullptr);
    void free(void* ptr);
    void* reallocate(void* ptr, size_t newSize);

    // Memory operations
    bool copyToDevice(const void* hostPtr, void* devicePtr, size_t size, cudaStream_t stream = nullptr);
    bool copyToHost(const void* devicePtr, void* hostPtr, size_t size, cudaStream_t stream = nullptr);
    bool memset(void* ptr, int value, size_t size, cudaStream_t stream = nullptr);

    // Memory pool operations
    size_t getTotalMemory() const;
    size_t getFreeMemory() const;
    size_t getUsedMemory() const;
    void defragment();
    void clear();

    // Memory tracking
    void setMemoryCallback(std::function<void(size_t, size_t)> callback);
    void enableMemoryTracking(bool enable);
    void printMemoryStats() const;

private:
    CUDAMemoryManager() = default;
    ~CUDAMemoryManager() = default;
    CUDAMemoryManager(const CUDAMemoryManager&) = delete;
    CUDAMemoryManager& operator=(const CUDAMemoryManager&) = delete;

    // Memory pool management
    bool initializePool();
    void cleanupPool();
    void* allocateFromPool(size_t size);
    void freeToPool(void* ptr);
    bool growPool(size_t minSize);

    // Memory block management
    MemoryBlock* findFreeBlock(size_t size);
    void splitBlock(MemoryBlock* block, size_t size);
    void mergeBlocks();
    void defragmentBlocks();

    // Memory tracking
    void updateMemoryStats();
    void notifyMemoryCallback();

    // Configuration
    MemoryPoolConfig config_;
    MemoryStrategy strategy_;
    std::mutex mutex_;

    // Memory pool
    std::vector<MemoryBlock> blocks_;
    size_t totalMemory_;
    size_t usedMemory_;
    size_t freeMemory_;

    // Memory tracking
    bool trackingEnabled_;
    std::function<void(size_t, size_t)> memoryCallback_;
    std::unordered_map<std::string, size_t> tagMemoryUsage_;
};

} // namespace cogniware

#endif // MSMARTCOMPUTE_CUDA_MEMORY_MANAGER_H 