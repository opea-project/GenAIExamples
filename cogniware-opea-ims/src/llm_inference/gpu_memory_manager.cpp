#include "../../include/llm_inference/gpu_memory_manager.h"
#include <spdlog/spdlog.h>
#include <cuda_runtime.h>
#include <stdexcept>
#include <algorithm>

namespace cogniware {
namespace llm_inference {

GPUMemoryManager& GPUMemoryManager::getInstance() {
    static GPUMemoryManager instance;
    return instance;
}

GPUMemoryManager::GPUMemoryManager()
    : total_memory_(0)
    , used_memory_(0)
    , max_memory_(0) {
    try {
        // Get total GPU memory
        cudaDeviceProp prop;
        cudaError_t error = cudaGetDeviceProperties(&prop, 0);
        if (error != cudaSuccess) {
            throw std::runtime_error("Failed to get GPU properties: " + std::string(cudaGetErrorString(error)));
        }
        total_memory_ = prop.totalGlobalMem;
        max_memory_ = total_memory_ * 0.9; // Use 90% of total memory
        spdlog::info("GPU Memory Manager initialized with {} MB total memory", total_memory_ / (1024 * 1024));
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize GPU Memory Manager: {}", e.what());
        throw;
    }
}

GPUMemoryManager::~GPUMemoryManager() {
    try {
        // Free all allocated memory
        for (const auto& [ptr, size] : allocated_memory_) {
            cudaFree(ptr);
        }
        allocated_memory_.clear();
        used_memory_ = 0;
        spdlog::info("GPU Memory Manager cleaned up");
    } catch (const std::exception& e) {
        spdlog::error("Error during GPU Memory Manager cleanup: {}", e.what());
    }
}

void* GPUMemoryManager::allocate(size_t size) {
    try {
        std::lock_guard<std::mutex> lock(mutex_);

        // Check if we have enough memory
        if (used_memory_ + size > max_memory_) {
            throw std::runtime_error("Not enough GPU memory available");
        }

        // Allocate memory
        void* ptr;
        cudaError_t error = cudaMalloc(&ptr, size);
        if (error != cudaSuccess) {
            throw std::runtime_error("Failed to allocate GPU memory: " + std::string(cudaGetErrorString(error)));
        }

        // Track allocation
        allocated_memory_.push_back({ptr, size});
        used_memory_ += size;

        spdlog::debug("Allocated {} bytes of GPU memory, total used: {} MB",
            size, used_memory_ / (1024 * 1024));

        return ptr;
    } catch (const std::exception& e) {
        spdlog::error("Memory allocation failed: {}", e.what());
        throw;
    }
}

void GPUMemoryManager::deallocate(void* ptr) {
    try {
        std::lock_guard<std::mutex> lock(mutex_);

        // Find the allocation
        auto it = std::find_if(allocated_memory_.begin(), allocated_memory_.end(),
            [ptr](const auto& alloc) { return alloc.first == ptr; });

        if (it == allocated_memory_.end()) {
            throw std::runtime_error("Attempted to deallocate untracked memory");
        }

        // Free memory
        cudaError_t error = cudaFree(ptr);
        if (error != cudaSuccess) {
            throw std::runtime_error("Failed to deallocate GPU memory: " + std::string(cudaGetErrorString(error)));
        }

        // Update tracking
        used_memory_ -= it->second;
        allocated_memory_.erase(it);

        spdlog::debug("Deallocated GPU memory, total used: {} MB", used_memory_ / (1024 * 1024));
    } catch (const std::exception& e) {
        spdlog::error("Memory deallocation failed: {}", e.what());
        throw;
    }
}

void GPUMemoryManager::copyToDevice(void* dst, const void* src, size_t size) {
    try {
        cudaError_t error = cudaMemcpy(dst, src, size, cudaMemcpyHostToDevice);
        if (error != cudaSuccess) {
            throw std::runtime_error("Failed to copy memory to device: " + std::string(cudaGetErrorString(error)));
        }
    } catch (const std::exception& e) {
        spdlog::error("Memory copy to device failed: {}", e.what());
        throw;
    }
}

void GPUMemoryManager::copyToHost(void* dst, const void* src, size_t size) {
    try {
        cudaError_t error = cudaMemcpy(dst, src, size, cudaMemcpyDeviceToHost);
        if (error != cudaSuccess) {
            throw std::runtime_error("Failed to copy memory to host: " + std::string(cudaGetErrorString(error)));
        }
    } catch (const std::exception& e) {
        spdlog::error("Memory copy to host failed: {}", e.what());
        throw;
    }
}

void GPUMemoryManager::setMaxMemory(size_t max_memory) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (max_memory > total_memory_) {
        throw std::runtime_error("Maximum memory cannot exceed total GPU memory");
    }
    max_memory_ = max_memory;
    spdlog::info("Set maximum GPU memory to {} MB", max_memory_ / (1024 * 1024));
}

size_t GPUMemoryManager::getTotalMemory() const {
    return total_memory_;
}

size_t GPUMemoryManager::getUsedMemory() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return used_memory_;
}

size_t GPUMemoryManager::getAvailableMemory() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return max_memory_ - used_memory_;
}

void GPUMemoryManager::reset() {
    try {
        std::lock_guard<std::mutex> lock(mutex_);

        // Free all allocated memory
        for (const auto& [ptr, size] : allocated_memory_) {
            cudaFree(ptr);
        }
        allocated_memory_.clear();
        used_memory_ = 0;

        spdlog::info("GPU Memory Manager reset");
    } catch (const std::exception& e) {
        spdlog::error("Failed to reset GPU Memory Manager: {}", e.what());
        throw;
    }
}

} // namespace llm_inference
} // namespace cogniware 