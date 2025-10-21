#include "cuda_memory_manager.h"
#include <spdlog/spdlog.h>
#include <algorithm>
#include <cstring>

namespace msmartcompute {

CUDAMemoryManager& CUDAMemoryManager::getInstance() {
    static CUDAMemoryManager instance;
    return instance;
}

bool CUDAMemoryManager::initialize(const MemoryPoolConfig& config) {
    config_ = config;
    
    // Initialize CUDA
    cudaError_t cudaStatus = cudaSetDevice(config_.deviceId);
    if (cudaStatus != cudaSuccess) {
        spdlog::error("Failed to set CUDA device: {}", cudaGetErrorString(cudaStatus));
        return false;
    }
    
    // Create memory pool
    if (config_.strategy == MemoryStrategy::POOL) {
        size_t poolSize = config_.initialPoolSize;
        cudaStatus = cudaMalloc(&poolMemory_, poolSize);
        if (cudaStatus != cudaSuccess) {
            spdlog::error("Failed to allocate memory pool: {}", cudaGetErrorString(cudaStatus));
            return false;
        }
        
        // Initialize free blocks list
        MemoryBlock block;
        block.address = poolMemory_;
        block.size = poolSize;
        block.isFree = true;
        freeBlocks_.push_back(block);
    }
    
    return true;
}

void CUDAMemoryManager::shutdown() {
    // Free all allocated memory
    for (auto& block : allocatedBlocks_) {
        if (block.address) {
            cudaFree(block.address);
        }
    }
    allocatedBlocks_.clear();
    
    // Free memory pool
    if (poolMemory_) {
        cudaFree(poolMemory_);
        poolMemory_ = nullptr;
    }
    freeBlocks_.clear();
}

bool CUDAMemoryManager::setMemoryStrategy(MemoryStrategy strategy) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (strategy == strategy_) {
        return true;
    }

    if (strategy == MemoryStrategy::POOL) {
        if (!initializePool()) {
            spdlog::error("Failed to initialize memory pool");
            return false;
        }
    } else {
        cleanupPool();
    }

    strategy_ = strategy;
    return true;
}

MemoryStrategy CUDAMemoryManager::getMemoryStrategy() const {
    return strategy_;
}

void* CUDAMemoryManager::allocate(size_t size, size_t alignment) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (config_.strategy == MemoryStrategy::POOL) {
        return allocateFromPool(size, alignment);
    } else if (config_.strategy == MemoryStrategy::DIRECT) {
        return allocateDirect(size, alignment);
    } else { // STREAMING
        return allocateStreaming(size, alignment);
    }
}

void CUDAMemoryManager::free(void* ptr) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!ptr) return;
    
    if (config_.strategy == MemoryStrategy::POOL) {
        freeToPool(ptr);
    } else {
        cudaFree(ptr);
    }
}

void* CUDAMemoryManager::reallocate(void* ptr, size_t newSize) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!ptr) {
        return allocate(newSize);
    }
    
    if (config_.strategy == MemoryStrategy::POOL) {
        return reallocateInPool(ptr, newSize);
    } else {
        void* newPtr = allocate(newSize);
        if (newPtr) {
            // Copy data to new location
            cudaMemcpy(newPtr, ptr, newSize, cudaMemcpyDeviceToDevice);
            free(ptr);
        }
        return newPtr;
    }
}

bool CUDAMemoryManager::copyToDevice(void* dst, const void* src, size_t size) {
    cudaError_t status = cudaMemcpy(dst, src, size, cudaMemcpyHostToDevice);
    if (status != cudaSuccess) {
        spdlog::error("Failed to copy memory to device: {}", cudaGetErrorString(status));
        return false;
    }
    return true;
}

bool CUDAMemoryManager::copyToHost(void* dst, const void* src, size_t size) {
    cudaError_t status = cudaMemcpy(dst, src, size, cudaMemcpyDeviceToHost);
    if (status != cudaSuccess) {
        spdlog::error("Failed to copy memory to host: {}", cudaGetErrorString(status));
        return false;
    }
    return true;
}

bool CUDAMemoryManager::memset(void* ptr, int value, size_t size) {
    cudaError_t status = cudaMemset(ptr, value, size);
    if (status != cudaSuccess) {
        spdlog::error("Failed to set memory: {}", cudaGetErrorString(status));
        return false;
    }
    return true;
}

size_t CUDAMemoryManager::getTotalMemory() const {
    return totalMemory_;
}

size_t CUDAMemoryManager::getFreeMemory() const {
    return freeMemory_;
}

size_t CUDAMemoryManager::getUsedMemory() const {
    return usedMemory_;
}

void CUDAMemoryManager::defragment() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (config_.strategy != MemoryStrategy::POOL) return;
    
    // Sort free blocks by address
    std::sort(freeBlocks_.begin(), freeBlocks_.end(),
        [](const MemoryBlock& a, const MemoryBlock& b) {
            return a.address < b.address;
        });
    
    // Merge adjacent free blocks
    for (size_t i = 0; i < freeBlocks_.size() - 1; ++i) {
        if (freeBlocks_[i].isFree && freeBlocks_[i + 1].isFree) {
            uintptr_t endAddr = reinterpret_cast<uintptr_t>(freeBlocks_[i].address) + freeBlocks_[i].size;
            if (endAddr == reinterpret_cast<uintptr_t>(freeBlocks_[i + 1].address)) {
                freeBlocks_[i].size += freeBlocks_[i + 1].size;
                freeBlocks_.erase(freeBlocks_.begin() + i + 1);
                --i;
            }
        }
    }
}

void CUDAMemoryManager::clear() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Free all allocated memory
    for (auto& block : allocatedBlocks_) {
        if (block.address) {
            cudaFree(block.address);
        }
    }
    allocatedBlocks_.clear();
    
    // Reset memory pool
    if (poolMemory_) {
        cudaFree(poolMemory_);
        poolMemory_ = nullptr;
        
        size_t poolSize = config_.initialPoolSize;
        cudaMalloc(&poolMemory_, poolSize);
        
        MemoryBlock block;
        block.address = poolMemory_;
        block.size = poolSize;
        block.isFree = true;
        freeBlocks_.clear();
        freeBlocks_.push_back(block);
    }
}

void CUDAMemoryManager::setMemoryCallback(std::function<void(size_t, size_t)> callback) {
    std::lock_guard<std::mutex> lock(mutex_);
    memoryCallback_ = callback;
}

void CUDAMemoryManager::enableMemoryTracking(bool enable) {
    std::lock_guard<std::mutex> lock(mutex_);
    trackingEnabled_ = enable;
}

void CUDAMemoryManager::printMemoryStats() const {
    spdlog::info("Memory Stats:");
    spdlog::info("  Total Memory: {} bytes", totalMemory_);
    spdlog::info("  Used Memory: {} bytes", usedMemory_);
    spdlog::info("  Free Memory: {} bytes", freeMemory_);
    spdlog::info("  Memory Utilization: {:.2f}%", 
        (static_cast<float>(usedMemory_) / totalMemory_) * 100.0f);
}

bool CUDAMemoryManager::initializePool() {
    void* ptr = nullptr;
    cudaError_t status = cudaMalloc(&ptr, config_.initialSize);
    if (status != cudaSuccess) {
        spdlog::error("Failed to allocate initial memory pool: {}", cudaGetErrorString(status));
        return false;
    }

    MemoryBlock block{ptr, config_.initialSize, false, nullptr, "pool"};
    blocks_.push_back(block);

    totalMemory_ = config_.initialSize;
    usedMemory_ = 0;
    freeMemory_ = config_.initialSize;

    return true;
}

void CUDAMemoryManager::cleanupPool() {
    for (const auto& block : blocks_) {
        if (block.ptr) {
            cudaFree(block.ptr);
        }
    }
    blocks_.clear();
    totalMemory_ = 0;
    usedMemory_ = 0;
    freeMemory_ = 0;
}

void* CUDAMemoryManager::allocateFromPool(size_t size, size_t alignment) {
    // Find best fit block
    auto bestFit = std::min_element(freeBlocks_.begin(), freeBlocks_.end(),
        [size](const MemoryBlock& a, const MemoryBlock& b) {
            if (!a.isFree) return false;
            if (!b.isFree) return true;
            return a.size >= size && (b.size < size || a.size < b.size);
        });
    
    if (bestFit == freeBlocks_.end() || bestFit->size < size) {
        // No suitable block found, try to defragment
        defragment();
        
        // Try again after defragmentation
        bestFit = std::min_element(freeBlocks_.begin(), freeBlocks_.end(),
            [size](const MemoryBlock& a, const MemoryBlock& b) {
                if (!a.isFree) return false;
                if (!b.isFree) return true;
                return a.size >= size && (b.size < size || a.size < b.size);
            });
            
        if (bestFit == freeBlocks_.end() || bestFit->size < size) {
            spdlog::error("Failed to allocate memory from pool: insufficient space");
            return nullptr;
        }
    }
    
    // Split block if necessary
    if (bestFit->size > size + config_.minBlockSize) {
        MemoryBlock newBlock;
        newBlock.address = static_cast<char*>(bestFit->address) + size;
        newBlock.size = bestFit->size - size;
        newBlock.isFree = true;
        
        bestFit->size = size;
        freeBlocks_.push_back(newBlock);
    }
    
    bestFit->isFree = false;
    allocatedBlocks_.push_back(*bestFit);
    
    return bestFit->address;
}

void* CUDAMemoryManager::allocateDirect(size_t size, size_t alignment) {
    void* ptr = nullptr;
    cudaError_t status = cudaMalloc(&ptr, size);
    if (status != cudaSuccess) {
        spdlog::error("Failed to allocate memory directly: {}", cudaGetErrorString(status));
        return nullptr;
    }
    
    MemoryBlock block;
    block.address = ptr;
    block.size = size;
    block.isFree = false;
    allocatedBlocks_.push_back(block);
    
    return ptr;
}

void* CUDAMemoryManager::allocateStreaming(size_t size, size_t alignment) {
    // For streaming strategy, we use a circular buffer
    if (streamingBuffer_.size() < config_.numStreamingBuffers) {
        void* ptr = nullptr;
        cudaError_t status = cudaMalloc(&ptr, size);
        if (status != cudaSuccess) {
            spdlog::error("Failed to allocate streaming buffer: {}", cudaGetErrorString(status));
            return nullptr;
        }
        
        streamingBuffer_.push_back(ptr);
        return ptr;
    }
    
    // Reuse oldest buffer
    void* ptr = streamingBuffer_.front();
    streamingBuffer_.pop_front();
    streamingBuffer_.push_back(ptr);
    
    return ptr;
}

void CUDAMemoryManager::freeToPool(void* ptr) {
    auto it = std::find_if(allocatedBlocks_.begin(), allocatedBlocks_.end(),
        [ptr](const MemoryBlock& block) {
            return block.address == ptr;
        });
        
    if (it != allocatedBlocks_.end()) {
        it->isFree = true;
        freeBlocks_.push_back(*it);
        allocatedBlocks_.erase(it);
    }
}

void* CUDAMemoryManager::reallocateInPool(void* ptr, size_t newSize) {
    auto it = std::find_if(allocatedBlocks_.begin(), allocatedBlocks_.end(),
        [ptr](const MemoryBlock& block) {
            return block.address == ptr;
        });
        
    if (it == allocatedBlocks_.end()) {
        return nullptr;
    }
    
    if (it->size >= newSize) {
        return ptr;
    }
    
    void* newPtr = allocateFromPool(newSize, 0);
    if (newPtr) {
        cudaMemcpy(newPtr, ptr, it->size, cudaMemcpyDeviceToDevice);
        freeToPool(ptr);
    }
    
    return newPtr;
}

} // namespace msmartcompute 