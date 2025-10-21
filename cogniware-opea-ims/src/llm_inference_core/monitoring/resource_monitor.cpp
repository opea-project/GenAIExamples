#include "llm_inference_core/monitoring/resource_monitor.h"
#include <cuda_runtime.h>
#include <nvml.h>

namespace cogniware {

ResourceMonitor& ResourceMonitor::getInstance() {
    static ResourceMonitor instance;
    return instance;
}

ResourceMonitor::ResourceMonitor()
    : monitoring_(false)
    , maxVRAMUsage_(0)
    , maxGPUUtilization_(100.0f) {
    currentGPUStats_ = {0, 0, 0, 0.0f, 0.0f};
}

ResourceMonitor::~ResourceMonitor() {
    stopMonitoring();
}

bool ResourceMonitor::startMonitoring() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (monitoring_) {
        lastError_ = "Monitoring is already active";
        return false;
    }
    
    monitoring_ = true;
    monitoringThread_ = std::thread(&ResourceMonitor::monitoringThread, this);
    
    return true;
}

void ResourceMonitor::stopMonitoring() {
    {
        std::lock_guard<std::mutex> lock(mutex_);
        if (!monitoring_) {
            return;
        }
        
        monitoring_ = false;
    }
    
    if (monitoringThread_.joinable()) {
        monitoringThread_.join();
    }
}

bool ResourceMonitor::isMonitoring() const {
    return monitoring_;
}

GPUStats ResourceMonitor::getGPUStats() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return currentGPUStats_;
}

ModelStats ResourceMonitor::getModelStats(const std::string& modelId) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = modelStats_.find(modelId);
    if (it == modelStats_.end()) {
        return ModelStats{0, 0, 0, 0.0f};
    }
    
    return it->second;
}

void ResourceMonitor::setMaxVRAMUsage(size_t maxUsage) {
    maxVRAMUsage_ = maxUsage;
}

void ResourceMonitor::setMaxGPUUtilization(float maxUtilization) {
    maxGPUUtilization_ = maxUtilization;
}

void ResourceMonitor::setResourceAlertCallback(ResourceAlertCallback callback) {
    std::lock_guard<std::mutex> lock(mutex_);
    alertCallback_ = callback;
}

void ResourceMonitor::updateModelStats(const std::string& modelId,
                                     size_t memoryUsage,
                                     size_t computeTime,
                                     float latency) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto& stats = modelStats_[modelId];
    stats.memoryUsage = memoryUsage;
    stats.computeTime += computeTime;
    stats.requestCount++;
    
    // Update average latency using exponential moving average
    const float alpha = 0.1f;  // Smoothing factor
    stats.averageLatency = (1.0f - alpha) * stats.averageLatency + alpha * latency;
}

const char* ResourceMonitor::getLastError() const {
    return lastError_.c_str();
}

void ResourceMonitor::clearLastError() {
    lastError_.clear();
}

void ResourceMonitor::monitoringThread() {
    while (monitoring_) {
        checkGPUResources();
        checkModelResources();
        
        // Sleep for a short duration
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
}

void ResourceMonitor::checkGPUResources() {
    GPUStats stats = collectGPUStats();
    updateGPUStats(stats);
    
    // Check VRAM usage
    if (maxVRAMUsage_ > 0 && stats.usedMemory > maxVRAMUsage_) {
        triggerAlert("VRAM", "VRAM usage exceeded limit: " +
                    std::to_string(stats.usedMemory) + " / " +
                    std::to_string(maxVRAMUsage_));
    }
    
    // Check GPU utilization
    if (stats.utilization > maxGPUUtilization_) {
        triggerAlert("GPU", "GPU utilization exceeded limit: " +
                    std::to_string(stats.utilization) + "% / " +
                    std::to_string(maxGPUUtilization_) + "%");
    }
    
    // Check temperature
    if (stats.temperature > 80.0f) {  // 80°C threshold
        triggerAlert("GPU", "GPU temperature too high: " +
                    std::to_string(stats.temperature) + "°C");
    }
}

void ResourceMonitor::checkModelResources() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    for (const auto& pair : modelStats_) {
        const auto& modelId = pair.first;
        const auto& stats = pair.second;
        
        // Check memory usage per model
        if (maxVRAMUsage_ > 0 && stats.memoryUsage > maxVRAMUsage_ / modelStats_.size()) {
            triggerAlert("Model-" + modelId, "Model memory usage exceeded limit: " +
                        std::to_string(stats.memoryUsage) + " / " +
                        std::to_string(maxVRAMUsage_ / modelStats_.size()));
        }
        
        // Check latency
        if (stats.averageLatency > 1000.0f) {  // 1 second threshold
            triggerAlert("Model-" + modelId, "High latency detected: " +
                        std::to_string(stats.averageLatency) + "ms");
        }
    }
}

GPUStats ResourceMonitor::collectGPUStats() {
    GPUStats stats = {0, 0, 0, 0.0f, 0.0f};
    
    // Get CUDA device properties
    cudaDeviceProp prop;
    cudaError_t error = cudaGetDeviceProperties(&prop, 0);
    if (error != cudaSuccess) {
        lastError_ = cudaGetErrorString(error);
        return stats;
    }
    
    // Get memory info
    size_t free, total;
    error = cudaMemGetInfo(&free, &total);
    if (error != cudaSuccess) {
        lastError_ = cudaGetErrorString(error);
        return stats;
    }
    
    stats.totalMemory = total;
    stats.freeMemory = free;
    stats.usedMemory = total - free;
    
    // Get GPU utilization and temperature using NVML
    nvmlDevice_t device;
    nvmlReturn_t nvmlError = nvmlInit();
    if (nvmlError == NVML_SUCCESS) {
        nvmlError = nvmlDeviceGetHandleByIndex(0, &device);
        if (nvmlError == NVML_SUCCESS) {
            nvmlUtilization_t utilization;
            nvmlError = nvmlDeviceGetUtilizationRates(device, &utilization);
            if (nvmlError == NVML_SUCCESS) {
                stats.utilization = utilization.gpu;
            }
            
            unsigned int temperature;
            nvmlError = nvmlDeviceGetTemperature(device, NVML_TEMPERATURE_GPU, &temperature);
            if (nvmlError == NVML_SUCCESS) {
                stats.temperature = temperature;
            }
        }
        nvmlShutdown();
    }
    
    return stats;
}

void ResourceMonitor::updateGPUStats(const GPUStats& stats) {
    std::lock_guard<std::mutex> lock(mutex_);
    currentGPUStats_ = stats;
}

void ResourceMonitor::triggerAlert(const std::string& resource, const std::string& message) {
    if (alertCallback_) {
        alertCallback_(resource, message);
    }
}

} // namespace cogniware 