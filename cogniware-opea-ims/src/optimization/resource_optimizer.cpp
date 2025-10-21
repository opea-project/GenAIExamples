#include "optimization/resource_optimizer.h"
#include <spdlog/spdlog.h>
#include <cuda_runtime.h>
#include <sys/sysinfo.h>
#include <algorithm>
#include <chrono>
#include <thread>

namespace cogniware {

ResourceOptimizer::ResourceOptimizer()
    : monitoring_active_(false)
    , memory_threshold_(0.8f)  // 80% memory utilization threshold
    , gpu_threshold_(0.9f)     // 90% GPU utilization threshold
{
    spdlog::info("ResourceOptimizer initialized");
}

ResourceOptimizer::MemoryMetrics ResourceOptimizer::get_memory_metrics() {
    MemoryMetrics metrics;
    
    try {
        struct sysinfo si;
        if (sysinfo(&si) == 0) {
            metrics.total_memory = si.totalram;
            metrics.free_memory = si.freeram;
            metrics.used_memory = metrics.total_memory - metrics.free_memory;
            metrics.memory_utilization = static_cast<float>(metrics.used_memory) / 
                                       static_cast<float>(metrics.total_memory);
        } else {
            spdlog::error("Failed to get system memory info");
        }
    } catch (const std::exception& e) {
        spdlog::error("Error getting memory metrics: {}", e.what());
    }
    
    return metrics;
}

bool ResourceOptimizer::optimize_memory_usage() {
    try {
        auto metrics = get_memory_metrics();
        
        if (metrics.memory_utilization > memory_threshold_) {
            spdlog::warn("Memory utilization ({:.2f}%) exceeds threshold ({:.2f}%)",
                        metrics.memory_utilization * 100,
                        memory_threshold_ * 100);
            
            // Implement memory optimization strategies
            cleanup_unused_resources();
            
            // Check if optimization was successful
            metrics = get_memory_metrics();
            return metrics.memory_utilization <= memory_threshold_;
        }
        
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Failed to optimize memory usage: {}", e.what());
        return false;
    }
}

void ResourceOptimizer::set_memory_threshold(float threshold) {
    if (threshold > 0.0f && threshold <= 1.0f) {
        memory_threshold_ = threshold;
        spdlog::info("Memory threshold set to {:.2f}%", threshold * 100);
    } else {
        spdlog::error("Invalid memory threshold: {}", threshold);
    }
}

ResourceOptimizer::GPUMetrics ResourceOptimizer::get_gpu_metrics(int device_id) {
    GPUMetrics metrics;
    
    try {
        cudaDeviceProp prop;
        if (cudaGetDeviceProperties(&prop, device_id) == cudaSuccess) {
            metrics.total_memory = prop.totalGlobalMem;
            
            size_t free_memory, total_memory;
            if (cudaMemGetInfo(&free_memory, &total_memory) == cudaSuccess) {
                metrics.free_memory = free_memory;
                metrics.used_memory = total_memory - free_memory;
            }
            
            // Get GPU utilization (requires NVML)
            int utilization;
            if (cudaDeviceGetAttribute(&utilization, 
                                     cudaDevAttrComputeMode, 
                                     device_id) == cudaSuccess) {
                metrics.utilization = static_cast<float>(utilization) / 100.0f;
            }
            
            // Get temperature (requires NVML)
            int temperature;
            if (cudaDeviceGetAttribute(&temperature, 
                                     cudaDevAttrMaxThreadsPerBlock, 
                                     device_id) == cudaSuccess) {
                metrics.temperature = static_cast<float>(temperature);
            }
            
            // Get power usage (requires NVML)
            int power;
            if (cudaDeviceGetAttribute(&power, 
                                     cudaDevAttrMaxThreadsPerMultiProcessor, 
                                     device_id) == cudaSuccess) {
                metrics.power_usage = power;
            }
        } else {
            spdlog::error("Failed to get GPU properties for device {}", device_id);
        }
    } catch (const std::exception& e) {
        spdlog::error("Error getting GPU metrics: {}", e.what());
    }
    
    return metrics;
}

bool ResourceOptimizer::optimize_gpu_usage(int device_id) {
    try {
        auto metrics = get_gpu_metrics(device_id);
        
        if (metrics.utilization > gpu_threshold_) {
            spdlog::warn("GPU utilization ({:.2f}%) exceeds threshold ({:.2f}%)",
                        metrics.utilization * 100,
                        gpu_threshold_ * 100);
            
            // Implement GPU optimization strategies
            // 1. Check for memory fragmentation
            if (metrics.used_memory > metrics.total_memory * 0.8f) {
                cudaDeviceReset();
                spdlog::info("Reset GPU device {} to clear memory", device_id);
            }
            
            // 2. Optimize resource distribution
            optimize_resource_distribution();
            
            // Check if optimization was successful
            metrics = get_gpu_metrics(device_id);
            return metrics.utilization <= gpu_threshold_;
        }
        
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Failed to optimize GPU usage: {}", e.what());
        return false;
    }
}

void ResourceOptimizer::set_gpu_threshold(float threshold) {
    if (threshold > 0.0f && threshold <= 1.0f) {
        gpu_threshold_ = threshold;
        spdlog::info("GPU threshold set to {:.2f}%", threshold * 100);
    } else {
        spdlog::error("Invalid GPU threshold: {}", threshold);
    }
}

bool ResourceOptimizer::allocate_resources(
    const std::string& model_id,
    const ResourceAllocation& allocation) {
    
    try {
        // Check resource availability
        if (!check_resource_availability(allocation)) {
            spdlog::error("Insufficient resources for model {}", model_id);
            return false;
        }
        
        // Store allocation
        current_allocations_[model_id] = allocation;
        allocation_timestamps_[model_id] = std::chrono::steady_clock::now();
        
        spdlog::info("Allocated resources for model {}", model_id);
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Failed to allocate resources for model {}: {}", 
                     model_id, e.what());
        return false;
    }
}

bool ResourceOptimizer::release_resources(const std::string& model_id) {
    try {
        auto it = current_allocations_.find(model_id);
        if (it == current_allocations_.end()) {
            spdlog::warn("No resource allocation found for model {}", model_id);
            return false;
        }
        
        current_allocations_.erase(it);
        allocation_timestamps_.erase(model_id);
        
        spdlog::info("Released resources for model {}", model_id);
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Failed to release resources for model {}: {}", 
                     model_id, e.what());
        return false;
    }
}

void ResourceOptimizer::start_monitoring() {
    if (!monitoring_active_) {
        monitoring_active_ = true;
        monitoring_thread_ = std::thread(&ResourceOptimizer::monitoring_loop, this);
        spdlog::info("Resource monitoring started");
    }
}

void ResourceOptimizer::stop_monitoring() {
    if (monitoring_active_) {
        monitoring_active_ = false;
        if (monitoring_thread_.joinable()) {
            monitoring_thread_.join();
        }
        spdlog::info("Resource monitoring stopped");
    }
}

std::map<std::string, float> ResourceOptimizer::get_performance_metrics() {
    std::map<std::string, float> metrics;
    
    try {
        for (const auto& [model_id, perf] : performance_history_) {
            metrics[model_id + "_latency"] = perf.inference_latency;
            metrics[model_id + "_throughput"] = perf.throughput;
            metrics[model_id + "_efficiency"] = perf.resource_efficiency;
            metrics[model_id + "_cost"] = perf.cost_per_inference;
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to get performance metrics: {}", e.what());
    }
    
    return metrics;
}

bool ResourceOptimizer::scale_resources(
    const std::string& model_id,
    float scale_factor) {
    
    try {
        auto it = current_allocations_.find(model_id);
        if (it == current_allocations_.end()) {
            spdlog::error("No allocation found for model {}", model_id);
            return false;
        }
        
        auto& allocation = it->second;
        ResourceAllocation scaled_allocation{
            allocation.cpu_cores * scale_factor,
            static_cast<size_t>(allocation.memory_mb * scale_factor),
            static_cast<size_t>(allocation.gpu_memory_mb * scale_factor),
            allocation.gpu_device_id
        };
        
        if (check_resource_availability(scaled_allocation)) {
            allocation = scaled_allocation;
            spdlog::info("Scaled resources for model {} by factor {}", 
                        model_id, scale_factor);
            return true;
        }
        
        spdlog::error("Insufficient resources for scaling model {}", model_id);
        return false;
    } catch (const std::exception& e) {
        spdlog::error("Failed to scale resources for model {}: {}", 
                     model_id, e.what());
        return false;
    }
}

bool ResourceOptimizer::redistribute_resources() {
    try {
        optimize_resource_distribution();
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Failed to redistribute resources: {}", e.what());
        return false;
    }
}

void ResourceOptimizer::monitoring_loop() {
    while (monitoring_active_) {
        try {
            process_metrics();
            std::this_thread::sleep_for(std::chrono::seconds(5));
        } catch (const std::exception& e) {
            spdlog::error("Error in monitoring loop: {}", e.what());
        }
    }
}

bool ResourceOptimizer::check_resource_availability(
    const ResourceAllocation& allocation) {
    
    try {
        // Check CPU cores
        if (allocation.cpu_cores > std::thread::hardware_concurrency()) {
            return false;
        }
        
        // Check memory
        auto memory_metrics = get_memory_metrics();
        if (allocation.memory_mb * 1024 * 1024 > memory_metrics.free_memory) {
            return false;
        }
        
        // Check GPU memory
        auto gpu_metrics = get_gpu_metrics(allocation.gpu_device_id);
        if (allocation.gpu_memory_mb * 1024 * 1024 > gpu_metrics.free_memory) {
            return false;
        }
        
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Failed to check resource availability: {}", e.what());
        return false;
    }
}

void ResourceOptimizer::cleanup_unused_resources() {
    try {
        auto now = std::chrono::steady_clock::now();
        std::vector<std::string> to_remove;
        
        for (const auto& [model_id, timestamp] : allocation_timestamps_) {
            if (now - timestamp > std::chrono::minutes(30)) {
                to_remove.push_back(model_id);
            }
        }
        
        for (const auto& model_id : to_remove) {
            release_resources(model_id);
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to cleanup unused resources: {}", e.what());
    }
}

void ResourceOptimizer::optimize_resource_distribution() {
    try {
        // Implement resource distribution optimization
        // 1. Sort allocations by resource usage
        std::vector<std::pair<std::string, ResourceAllocation>> sorted_allocations(
            current_allocations_.begin(),
            current_allocations_.end()
        );
        
        std::sort(sorted_allocations.begin(), sorted_allocations.end(),
                 [](const auto& a, const auto& b) {
                     return a.second.memory_mb > b.second.memory_mb;
                 });
        
        // 2. Redistribute resources
        for (const auto& [model_id, allocation] : sorted_allocations) {
            if (!optimize_memory_usage() || !optimize_gpu_usage(allocation.gpu_device_id)) {
                spdlog::warn("Failed to optimize resources for model {}", model_id);
            }
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to optimize resource distribution: {}", e.what());
    }
}

void ResourceOptimizer::update_performance_metrics(
    const std::string& model_id,
    const PerformanceMetrics& metrics) {
    
    try {
        performance_history_[model_id] = metrics;
    } catch (const std::exception& e) {
        spdlog::error("Failed to update performance metrics for model {}: {}", 
                     model_id, e.what());
    }
}

} // namespace cogniware 