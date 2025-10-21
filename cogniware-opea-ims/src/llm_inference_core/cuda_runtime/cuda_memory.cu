#include "cuda_memory.h"
#include "cuda_utils.h"
#include <spdlog/spdlog.h>
#include <unordered_map>
#include <mutex>
#include <stdexcept>

namespace msmartcompute {
namespace llm_inference {

// Implementation of CUDAMemoryManager
struct CUDAMemoryManager::Impl {
    std::unordered_map<void*, MemoryAllocation> allocations;
    std::unordered_map<int, size_t> device_memory_limits;
    std::unordered_map<int, size_t> device_memory_used;
    std::mutex mutex;
};

CUDAMemoryManager& CUDAMemoryManager::getInstance() {
    static CUDAMemoryManager instance;
    return instance;
}

CUDAMemoryManager::CUDAMemoryManager() : pimpl(std::make_unique<Impl>()) {
    // Initialize memory manager
    int device_count = getDeviceCount();
    for (int i = 0; i < device_count; ++i) {
        initializeDevice(i);
    }
}

CUDAMemoryManager::~CUDAMemoryManager() {
    clear();
}

void CUDAMemoryManager::initializeDevice(int device_id) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    // Set device
    setDevice(device_id);
    
    // Get total memory
    size_t free, total;
    getDeviceMemoryInfo(free, total, device_id);
    
    // Set default memory limit to 90% of total memory
    pimpl->device_memory_limits[device_id] = total * 0.9;
    pimpl->device_memory_used[device_id] = 0;
    
    spdlog::info("Initialized CUDA memory manager for device {}: {} MB total, {} MB limit",
                 device_id, total / (1024 * 1024), pimpl->device_memory_limits[device_id] / (1024 * 1024));
}

void CUDAMemoryManager::cleanupDevice(int device_id) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    // Free all allocations for this device
    for (auto it = pimpl->allocations.begin(); it != pimpl->allocations.end();) {
        if (it->second.device_id == device_id) {
            deallocate(it->first);
            it = pimpl->allocations.erase(it);
        } else {
            ++it;
        }
    }
    
    // Reset memory stats
    pimpl->device_memory_used[device_id] = 0;
}

void CUDAMemoryManager::checkMemoryLimit(size_t size, int device_id) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    if (pimpl->device_memory_used[device_id] + size > pimpl->device_memory_limits[device_id]) {
        throw std::runtime_error("Memory allocation would exceed device limit");
    }
}

void CUDAMemoryManager::updateMemoryStats(int device_id) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    size_t used = 0;
    for (const auto& alloc : pimpl->allocations) {
        if (alloc.second.device_id == device_id) {
            used += alloc.second.size;
        }
    }
    
    pimpl->device_memory_used[device_id] = used;
}

void* CUDAMemoryManager::allocate(size_t size, MemoryType type, const std::string& tag) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    void* ptr = nullptr;
    int device_id = getCurrentDevice();
    
    try {
        switch (type) {
            case MemoryType::HOST:
                ptr = allocateHostMemory(size);
                break;
            case MemoryType::DEVICE:
                checkMemoryLimit(size, device_id);
                ptr = allocateDeviceMemory(size, device_id);
                break;
            case MemoryType::MANAGED:
                checkMemoryLimit(size, device_id);
                ptr = allocateManagedMemory(size);
                break;
            case MemoryType::PINNED_HOST:
                ptr = allocatePinnedHostMemory(size);
                break;
            case MemoryType::SHARED:
                checkMemoryLimit(size, device_id);
                ptr = allocateManagedMemory(size);
                break;
            default:
                throw std::runtime_error("Invalid memory type");
        }
        
        // Record allocation
        MemoryAllocation alloc{
            ptr,
            size,
            type,
            device_id,
            false,
            tag
        };
        pimpl->allocations[ptr] = alloc;
        
        // Update memory stats
        if (type == MemoryType::DEVICE || type == MemoryType::MANAGED || type == MemoryType::SHARED) {
            pimpl->device_memory_used[device_id] += size;
        }
        
        spdlog::debug("Allocated {} bytes of {} memory on device {} with tag '{}'",
                     size, static_cast<int>(type), device_id, tag);
        
        return ptr;
    } catch (const std::exception& e) {
        spdlog::error("Failed to allocate memory: {}", e.what());
        throw;
    }
}

void CUDAMemoryManager::deallocate(void* ptr) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    auto it = pimpl->allocations.find(ptr);
    if (it == pimpl->allocations.end()) {
        throw std::runtime_error("Attempt to deallocate unknown pointer");
    }
    
    const auto& alloc = it->second;
    int device_id = alloc.device_id;
    
    try {
        switch (alloc.type) {
            case MemoryType::HOST:
                deallocateHostMemory(ptr);
                break;
            case MemoryType::DEVICE:
                deallocateDeviceMemory(ptr);
                break;
            case MemoryType::MANAGED:
                deallocateManagedMemory(ptr);
                break;
            case MemoryType::PINNED_HOST:
                deallocatePinnedHostMemory(ptr);
                break;
            case MemoryType::SHARED:
                deallocateManagedMemory(ptr);
                break;
        }
        
        // Update memory stats
        if (alloc.type == MemoryType::DEVICE || alloc.type == MemoryType::MANAGED || alloc.type == MemoryType::SHARED) {
            pimpl->device_memory_used[device_id] -= alloc.size;
        }
        
        // Remove allocation record
        pimpl->allocations.erase(it);
        
        spdlog::debug("Deallocated {} bytes of {} memory on device {} with tag '{}'",
                     alloc.size, static_cast<int>(alloc.type), device_id, alloc.tag);
    } catch (const std::exception& e) {
        spdlog::error("Failed to deallocate memory: {}", e.what());
        throw;
    }
}

void* CUDAMemoryManager::reallocate(void* ptr, size_t new_size) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    auto it = pimpl->allocations.find(ptr);
    if (it == pimpl->allocations.end()) {
        throw std::runtime_error("Attempt to reallocate unknown pointer");
    }
    
    const auto& old_alloc = it->second;
    int device_id = old_alloc.device_id;
    
    try {
        // Allocate new memory
        void* new_ptr = allocate(new_size, old_alloc.type, old_alloc.tag);
        
        // Copy data
        size_t copy_size = std::min(old_alloc.size, new_size);
        copy(new_ptr, ptr, copy_size, old_alloc.type, old_alloc.type);
        
        // Deallocate old memory
        deallocate(ptr);
        
        return new_ptr;
    } catch (const std::exception& e) {
        spdlog::error("Failed to reallocate memory: {}", e.what());
        throw;
    }
}

void CUDAMemoryManager::copy(void* dst, const void* src, size_t size, MemoryType dst_type, MemoryType src_type) {
    try {
        if (dst_type == MemoryType::DEVICE && src_type == MemoryType::HOST) {
            copyHostToDevice(dst, src, size);
        } else if (dst_type == MemoryType::HOST && src_type == MemoryType::DEVICE) {
            copyDeviceToHost(dst, src, size);
        } else if (dst_type == MemoryType::DEVICE && src_type == MemoryType::DEVICE) {
            copyDeviceToDevice(dst, src, size);
        } else if (dst_type == MemoryType::HOST && src_type == MemoryType::HOST) {
            copyHostToHost(dst, src, size);
        } else {
            throw std::runtime_error("Unsupported memory copy operation");
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to copy memory: {}", e.what());
        throw;
    }
}

void CUDAMemoryManager::memset(void* ptr, int value, size_t size, MemoryType type) {
    try {
        switch (type) {
            case MemoryType::HOST:
                memsetHost(ptr, value, size);
                break;
            case MemoryType::DEVICE:
                memsetDevice(ptr, value, size);
                break;
            case MemoryType::MANAGED:
                memsetManaged(ptr, value, size);
                break;
            default:
                throw std::runtime_error("Unsupported memory type for memset");
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to memset memory: {}", e.what());
        throw;
    }
}

void CUDAMemoryManager::prefetch(void* ptr, size_t size, int device_id) {
    try {
        prefetchToDevice(ptr, size, device_id);
    } catch (const std::exception& e) {
        spdlog::error("Failed to prefetch memory: {}", e.what());
        throw;
    }
}

size_t CUDAMemoryManager::getTotalMemory(int device_id) const {
    size_t free, total;
    getDeviceMemoryInfo(free, total, device_id);
    return total;
}

size_t CUDAMemoryManager::getFreeMemory(int device_id) const {
    size_t free, total;
    getDeviceMemoryInfo(free, total, device_id);
    return free;
}

size_t CUDAMemoryManager::getUsedMemory(int device_id) const {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    return pimpl->device_memory_used.at(device_id);
}

std::vector<MemoryAllocation> CUDAMemoryManager::getAllocations() const {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    std::vector<MemoryAllocation> result;
    result.reserve(pimpl->allocations.size());
    for (const auto& pair : pimpl->allocations) {
        result.push_back(pair.second);
    }
    return result;
}

MemoryAllocation CUDAMemoryManager::getAllocationInfo(void* ptr) const {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    auto it = pimpl->allocations.find(ptr);
    if (it == pimpl->allocations.end()) {
        throw std::runtime_error("Unknown pointer");
    }
    return it->second;
}

void CUDAMemoryManager::setMaxMemory(size_t max_memory, int device_id) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    pimpl->device_memory_limits[device_id] = max_memory;
}

void CUDAMemoryManager::clear() {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    // Free all allocations
    for (const auto& pair : pimpl->allocations) {
        try {
            deallocate(pair.first);
        } catch (const std::exception& e) {
            spdlog::error("Failed to deallocate memory during clear: {}", e.what());
        }
    }
    
    pimpl->allocations.clear();
    pimpl->device_memory_used.clear();
}

void CUDAMemoryManager::reset() {
    clear();
    
    // Reinitialize all devices
    int device_count = getDeviceCount();
    for (int i = 0; i < device_count; ++i) {
        initializeDevice(i);
    }
}

// Helper function implementations
void* allocateHostMemory(size_t size) {
    void* ptr = nullptr;
    CUDA_CHECK(cudaMallocHost(&ptr, size));
    return ptr;
}

void* allocateDeviceMemory(size_t size, int device_id) {
    void* ptr = nullptr;
    CUDA_CHECK(cudaSetDevice(device_id));
    CUDA_CHECK(cudaMalloc(&ptr, size));
    return ptr;
}

void* allocateManagedMemory(size_t size) {
    void* ptr = nullptr;
    CUDA_CHECK(cudaMallocManaged(&ptr, size));
    return ptr;
}

void* allocatePinnedHostMemory(size_t size) {
    void* ptr = nullptr;
    CUDA_CHECK(cudaMallocHost(&ptr, size));
    return ptr;
}

void deallocateHostMemory(void* ptr) {
    CUDA_CHECK(cudaFreeHost(ptr));
}

void deallocateDeviceMemory(void* ptr) {
    CUDA_CHECK(cudaFree(ptr));
}

void deallocateManagedMemory(void* ptr) {
    CUDA_CHECK(cudaFree(ptr));
}

void deallocatePinnedHostMemory(void* ptr) {
    CUDA_CHECK(cudaFreeHost(ptr));
}

void copyHostToDevice(void* dst, const void* src, size_t size) {
    CUDA_CHECK(cudaMemcpy(dst, src, size, cudaMemcpyHostToDevice));
}

void copyDeviceToHost(void* dst, const void* src, size_t size) {
    CUDA_CHECK(cudaMemcpy(dst, src, size, cudaMemcpyDeviceToHost));
}

void copyDeviceToDevice(void* dst, const void* src, size_t size) {
    CUDA_CHECK(cudaMemcpy(dst, src, size, cudaMemcpyDeviceToDevice));
}

void copyHostToHost(void* dst, const void* src, size_t size) {
    CUDA_CHECK(cudaMemcpy(dst, src, size, cudaMemcpyHostToHost));
}

void memsetHost(void* ptr, int value, size_t size) {
    CUDA_CHECK(cudaMemsetHost(ptr, value, size));
}

void memsetDevice(void* ptr, int value, size_t size) {
    CUDA_CHECK(cudaMemset(ptr, value, size));
}

void memsetManaged(void* ptr, int value, size_t size) {
    CUDA_CHECK(cudaMemset(ptr, value, size));
}

void prefetchToDevice(void* ptr, size_t size, int device_id) {
    CUDA_CHECK(cudaMemPrefetchAsync(ptr, size, device_id));
}

void prefetchToHost(void* ptr, size_t size) {
    CUDA_CHECK(cudaMemPrefetchAsync(ptr, size, cudaCpuDeviceId));
}

} // namespace llm_inference
} // namespace msmartcompute 