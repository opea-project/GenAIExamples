#pragma once

#include <cuda_runtime.h>
#include <string>
#include <vector>
#include <memory>

namespace cogniware {
namespace llm_inference {

// Memory allocation types
enum class MemoryType {
    HOST,           // Host memory (CPU)
    DEVICE,         // Device memory (GPU)
    MANAGED,        // Unified memory
    PINNED_HOST,    // Pinned host memory
    SHARED          // Shared memory between host and device
};

// Memory allocation info
struct MemoryAllocation {
    void* ptr;              // Pointer to allocated memory
    size_t size;            // Size in bytes
    MemoryType type;        // Type of memory
    int device_id;          // Device ID for device memory
    bool is_initialized;    // Whether memory is initialized
    std::string tag;        // Optional tag for debugging
};

// Memory manager class
class CUDAMemoryManager {
public:
    static CUDAMemoryManager& getInstance();

    // Memory allocation
    void* allocate(size_t size, MemoryType type, const std::string& tag = "");
    void deallocate(void* ptr);
    void* reallocate(void* ptr, size_t new_size);

    // Memory operations
    void copy(void* dst, const void* src, size_t size, MemoryType dst_type, MemoryType src_type);
    void memset(void* ptr, int value, size_t size, MemoryType type);
    void prefetch(void* ptr, size_t size, int device_id);

    // Memory info
    size_t getTotalMemory(int device_id) const;
    size_t getFreeMemory(int device_id) const;
    size_t getUsedMemory(int device_id) const;
    std::vector<MemoryAllocation> getAllocations() const;
    MemoryAllocation getAllocationInfo(void* ptr) const;

    // Memory management
    void setMaxMemory(size_t max_memory, int device_id);
    void clear();
    void reset();

private:
    CUDAMemoryManager();
    ~CUDAMemoryManager();

    // Prevent copying
    CUDAMemoryManager(const CUDAMemoryManager&) = delete;
    CUDAMemoryManager& operator=(const CUDAMemoryManager&) = delete;

    // Helper functions
    void initializeDevice(int device_id);
    void cleanupDevice(int device_id);
    void checkMemoryLimit(size_t size, int device_id);
    void updateMemoryStats(int device_id);

    // Internal state
    struct Impl;
    std::unique_ptr<Impl> pimpl;
};

// Helper functions
void* allocateHostMemory(size_t size);
void* allocateDeviceMemory(size_t size, int device_id);
void* allocateManagedMemory(size_t size);
void* allocatePinnedHostMemory(size_t size);
void deallocateHostMemory(void* ptr);
void deallocateDeviceMemory(void* ptr);
void deallocateManagedMemory(void* ptr);
void deallocatePinnedHostMemory(void* ptr);

void copyHostToDevice(void* dst, const void* src, size_t size);
void copyDeviceToHost(void* dst, const void* src, size_t size);
void copyDeviceToDevice(void* dst, const void* src, size_t size);
void copyHostToHost(void* dst, const void* src, size_t size);

void memsetHost(void* ptr, int value, size_t size);
void memsetDevice(void* ptr, int value, size_t size);
void memsetManaged(void* ptr, int value, size_t size);

void prefetchToDevice(void* ptr, size_t size, int device_id);
void prefetchToHost(void* ptr, size_t size);

} // namespace llm_inference
} // namespace cogniware 