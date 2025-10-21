#ifndef GPU_MEMORY_MANAGER_H
#define GPU_MEMORY_MANAGER_H

#include <cuda_runtime.h>
#include <memory>
#include <vector>
#include <mutex>
#include <unordered_map>

namespace cogniware {

class GPUMemoryManager {
public:
    static GPUMemoryManager& getInstance();

    // Memory allocation
    void* allocate(size_t size);
    void free(void* ptr);

    // Memory pool management
    void* allocateFromPool(size_t size);
    void returnToPool(void* ptr);

    // Memory tracking
    size_t getTotalMemory() const;
    size_t getFreeMemory() const;
    size_t getUsedMemory() const;

    // Memory operations
    bool copyToDevice(void* dst, const void* src, size_t size);
    bool copyToHost(void* dst, const void* src, size_t size);

    // Stream management
    cudaStream_t createStream();
    void destroyStream(cudaStream_t stream);
    bool synchronizeStream(cudaStream_t stream);

private:
    GPUMemoryManager();
    ~GPUMemoryManager();

    // Prevent copying
    GPUMemoryManager(const GPUMemoryManager&) = delete;
    GPUMemoryManager& operator=(const GPUMemoryManager&) = delete;

    // Memory pool
    struct MemoryBlock {
        void* ptr;
        size_t size;
        bool in_use;
    };
    std::vector<MemoryBlock> memory_pool_;
    std::mutex pool_mutex_;

    // Memory tracking
    size_t total_memory_;
    size_t used_memory_;
    std::unordered_map<void*, size_t> allocation_sizes_;
    std::mutex tracking_mutex_;

    // Stream management
    std::vector<cudaStream_t> streams_;
    std::mutex stream_mutex_;
};

} // namespace cogniware

#endif // GPU_MEMORY_MANAGER_H 