#pragma once

#include <cuda_runtime.h>
#include <memory>
#include <mutex>
#include <unordered_map>
#include <string>
#include <vector>
#include <optional>

namespace cogniware {
namespace llm_inference {

// Memory allocation types
enum class MemoryType {
    HOST,           // Regular host memory
    DEVICE,         // Device memory
    MANAGED,        // Unified memory
    PINNED_HOST,    // Pinned host memory
    SHARED          // Shared memory between host and device
};

// Memory allocation information
struct MemoryAllocation {
    void* ptr;
    size_t size;
    MemoryType type;
    int device_id;
    bool is_initialized;
    std::optional<std::string> tag;  // Optional tag for debugging
};

// Memory statistics
struct MemoryStats {
    size_t total_allocated;
    size_t peak_allocated;
    size_t current_used;
    size_t total_allocations;
    size_t total_deallocations;
};

class GPUMemoryManager {
public:
    static GPUMemoryManager& getInstance();

    // Prevent copying
    GPUMemoryManager(const GPUMemoryManager&) = delete;
    GPUMemoryManager& operator=(const GPUMemoryManager&) = delete;

    // Memory allocation and deallocation
    void* allocate(size_t size, MemoryType type, const std::string& tag = "");
    void deallocate(void* ptr);
    void* reallocate(void* ptr, size_t new_size);

    // Memory operations
    void copy(void* dst, const void* src, size_t size, MemoryType dst_type, MemoryType src_type);
    void memset(void* ptr, int value, size_t size, MemoryType type);
    void prefetch(void* ptr, size_t size, int device_id);

    // Memory limits
    void setMemoryLimit(size_t limit, int device_id);
    size_t getMemoryLimit(int device_id) const;
    bool checkMemoryLimit(size_t size, int device_id) const;

    // Memory information
    MemoryAllocation getMemoryInfo(void* ptr) const;
    std::vector<MemoryAllocation> getAllAllocations() const;
    MemoryStats getMemoryStats(int device_id) const;
    size_t getTotalMemory(int device_id) const;
    size_t getFreeMemory(int device_id) const;

    // Memory management
    void clear();
    void reset();

private:
    GPUMemoryManager();
    ~GPUMemoryManager();

    void initializeDevice(int device_id);
    void cleanupDevice(int device_id);
    bool checkAllocation(void* ptr) const;
    void updateMemoryStats(size_t size, bool is_allocation, int device_id);

    struct Impl;
    std::unique_ptr<Impl> pimpl;
};

// Helper functions
inline void* allocateMemory(size_t size, MemoryType type, const std::string& tag = "") {
    return GPUMemoryManager::getInstance().allocate(size, type, tag);
}

inline void deallocateMemory(void* ptr) {
    GPUMemoryManager::getInstance().deallocate(ptr);
}

inline void* reallocateMemory(void* ptr, size_t new_size) {
    return GPUMemoryManager::getInstance().reallocate(ptr, new_size);
}

inline void copyMemory(void* dst, const void* src, size_t size, 
                      MemoryType dst_type, MemoryType src_type) {
    GPUMemoryManager::getInstance().copy(dst, src, size, dst_type, src_type);
}

inline void setMemory(void* ptr, int value, size_t size, MemoryType type) {
    GPUMemoryManager::getInstance().memset(ptr, value, size, type);
}

inline void prefetchMemory(void* ptr, size_t size, int device_id) {
    GPUMemoryManager::getInstance().prefetch(ptr, size, device_id);
}

inline void setMemoryLimit(size_t limit, int device_id) {
    GPUMemoryManager::getInstance().setMemoryLimit(limit, device_id);
}

inline size_t getMemoryLimit(int device_id) {
    return GPUMemoryManager::getInstance().getMemoryLimit(device_id);
}

inline bool checkMemoryLimit(size_t size, int device_id) {
    return GPUMemoryManager::getInstance().checkMemoryLimit(size, device_id);
}

inline MemoryAllocation getMemoryInfo(void* ptr) {
    return GPUMemoryManager::getInstance().getMemoryInfo(ptr);
}

inline std::vector<MemoryAllocation> getAllAllocations() {
    return GPUMemoryManager::getInstance().getAllAllocations();
}

inline MemoryStats getMemoryStats(int device_id) {
    return GPUMemoryManager::getInstance().getMemoryStats(device_id);
}

inline size_t getTotalMemory(int device_id) {
    return GPUMemoryManager::getInstance().getTotalMemory(device_id);
}

inline size_t getFreeMemory(int device_id) {
    return GPUMemoryManager::getInstance().getFreeMemory(device_id);
}

inline void clearMemory() {
    GPUMemoryManager::getInstance().clear();
}

inline void resetMemory() {
    GPUMemoryManager::getInstance().reset();
}

} // namespace llm_inference
} // namespace cogniware
