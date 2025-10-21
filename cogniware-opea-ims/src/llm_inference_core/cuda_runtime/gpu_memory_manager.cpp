#include "llm_inference_core/cuda_runtime/gpu_memory_manager.h"
#include <cuda_runtime.h>
#include <algorithm>
#include <stdexcept>

namespace cogniware {

GPUMemoryManager& GPUMemoryManager::getInstance() {
    static GPUMemoryManager instance;
    return instance;
}

GPUMemoryManager::GPUMemoryManager()
    : poolSize_(0)
    , maxPoolSize_(0)
    , totalAllocated_(0)
    , peakUsage_(0) {
    initializeMemoryPool();
}

GPUMemoryManager::~GPUMemoryManager() {
    cleanupMemoryPool();
}

void* GPUMemoryManager::allocate(size_t size) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    void* ptr = nullptr;
    cudaError_t error = cudaMalloc(&ptr, size);
    
    if (error != cudaSuccess) {
        lastError_ = cudaGetErrorString(error);
        return nullptr;
    }
    
    totalAllocated_ += size;
    updatePeakUsage(totalAllocated_);
    
    return ptr;
}

void GPUMemoryManager::deallocate(void* ptr) {
    if (!ptr) return;
    
    std::lock_guard<std::mutex> lock(mutex_);
    
    cudaError_t error = cudaFree(ptr);
    if (error != cudaSuccess) {
        lastError_ = cudaGetErrorString(error);
        return;
    }
    
    // Update statistics
    auto it = std::find_if(memoryPool_.begin(), memoryPool_.end(),
        [ptr](const MemoryBlock& block) { return block.ptr == ptr; });
    
    if (it != memoryPool_.end()) {
        totalAllocated_ -= it->size;
        memoryPool_.erase(it);
    }
}

void* GPUMemoryManager::allocateFromPool(size_t size) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Try to find a free block in the pool
    void* ptr = findFreeBlock(size);
    if (ptr) {
        return ptr;
    }
    
    // If pool is full, try to defragment
    if (isMemoryPoolFull()) {
        defragmentPool();
        ptr = findFreeBlock(size);
        if (ptr) {
            return ptr;
        }
    }
    
    // If still no block found, allocate new memory
    return allocate(size);
}

void GPUMemoryManager::returnToPool(void* ptr) {
    if (!ptr) return;
    
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = std::find_if(memoryPool_.begin(), memoryPool_.end(),
        [ptr](const MemoryBlock& block) { return block.ptr == ptr; });
    
    if (it != memoryPool_.end()) {
        it->inUse = false;
    }
}

cudaStream_t GPUMemoryManager::createStream() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    cudaStream_t stream;
    cudaError_t error = cudaStreamCreate(&stream);
    
    if (error != cudaSuccess) {
        lastError_ = cudaGetErrorString(error);
        return nullptr;
    }
    
    streams_.push_back({stream, true});
    return stream;
}

void GPUMemoryManager::destroyStream(cudaStream_t stream) {
    if (!stream) return;
    
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = std::find_if(streams_.begin(), streams_.end(),
        [stream](const StreamInfo& info) { return info.stream == stream; });
    
    if (it != streams_.end()) {
        cudaStreamDestroy(stream);
        it->active = false;
    }
}

void GPUMemoryManager::synchronizeStream(cudaStream_t stream) {
    if (!stream) return;
    
    cudaError_t error = cudaStreamSynchronize(stream);
    if (error != cudaSuccess) {
        lastError_ = cudaGetErrorString(error);
    }
}

size_t GPUMemoryManager::getTotalAllocatedMemory() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return totalAllocated_;
}

size_t GPUMemoryManager::getPeakMemoryUsage() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return peakUsage_;
}

size_t GPUMemoryManager::getAvailableMemory() const {
    size_t free, total;
    cudaError_t error = cudaMemGetInfo(&free, &total);
    
    if (error != cudaSuccess) {
        const_cast<GPUMemoryManager*>(this)->lastError_ = cudaGetErrorString(error);
        return 0;
    }
    
    return free;
}

void GPUMemoryManager::copyToDevice(void* dst, const void* src, size_t size, cudaStream_t stream) {
    cudaError_t error;
    if (stream) {
        error = cudaMemcpyAsync(dst, src, size, cudaMemcpyHostToDevice, stream);
    } else {
        error = cudaMemcpy(dst, src, size, cudaMemcpyHostToDevice);
    }
    
    if (error != cudaSuccess) {
        lastError_ = cudaGetErrorString(error);
    }
}

void GPUMemoryManager::copyToHost(void* dst, const void* src, size_t size, cudaStream_t stream) {
    cudaError_t error;
    if (stream) {
        error = cudaMemcpyAsync(dst, src, size, cudaMemcpyDeviceToHost, stream);
    } else {
        error = cudaMemcpy(dst, src, size, cudaMemcpyDeviceToHost);
    }
    
    if (error != cudaSuccess) {
        lastError_ = cudaGetErrorString(error);
    }
}

void GPUMemoryManager::setPoolSize(size_t size) {
    std::lock_guard<std::mutex> lock(mutex_);
    poolSize_ = size;
    initializeMemoryPool();
}

void GPUMemoryManager::setMaxPoolSize(size_t size) {
    std::lock_guard<std::mutex> lock(mutex_);
    maxPoolSize_ = size;
}

const char* GPUMemoryManager::getLastError() const {
    return lastError_.c_str();
}

void GPUMemoryManager::clearLastError() {
    lastError_.clear();
}

void GPUMemoryManager::initializeMemoryPool() {
    cleanupMemoryPool();
    
    if (poolSize_ > 0) {
        void* ptr = allocate(poolSize_);
        if (ptr) {
            memoryPool_.push_back({ptr, poolSize_, false});
        }
    }
}

void GPUMemoryManager::cleanupMemoryPool() {
    for (const auto& block : memoryPool_) {
        if (block.ptr) {
            cudaFree(block.ptr);
        }
    }
    memoryPool_.clear();
    totalAllocated_ = 0;
}

void GPUMemoryManager::updatePeakUsage(size_t currentUsage) {
    peakUsage_ = std::max(peakUsage_, currentUsage);
}

bool GPUMemoryManager::isMemoryPoolFull() const {
    return totalAllocated_ >= maxPoolSize_;
}

void* GPUMemoryManager::findFreeBlock(size_t size) {
    for (auto& block : memoryPool_) {
        if (!block.inUse && block.size >= size) {
            block.inUse = true;
            return block.ptr;
        }
    }
    return nullptr;
}

void GPUMemoryManager::defragmentPool() {
    // Simple defragmentation: merge adjacent free blocks
    std::sort(memoryPool_.begin(), memoryPool_.end(),
        [](const MemoryBlock& a, const MemoryBlock& b) {
            return a.ptr < b.ptr;
        });
    
    for (size_t i = 0; i < memoryPool_.size() - 1; ++i) {
        if (!memoryPool_[i].inUse && !memoryPool_[i + 1].inUse) {
            memoryPool_[i].size += memoryPool_[i + 1].size;
            memoryPool_.erase(memoryPool_.begin() + i + 1);
            --i;
        }
    }
}

} // namespace cogniware



