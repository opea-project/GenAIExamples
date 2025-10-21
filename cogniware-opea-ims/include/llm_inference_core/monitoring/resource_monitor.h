#pragma once

#include <atomic>
#include <chrono>
#include <functional>
#include <mutex>
#include <thread>
#include <unordered_map>

namespace cogniware {

struct GPUStats {
    size_t totalMemory;
    size_t freeMemory;
    size_t usedMemory;
    float utilization;
    float temperature;
};

struct ModelStats {
    size_t memoryUsage;
    size_t computeTime;
    size_t requestCount;
    float averageLatency;
};

class ResourceMonitor {
public:
    static ResourceMonitor& getInstance();

    // Delete copy constructor and assignment operator
    ResourceMonitor(const ResourceMonitor&) = delete;
    ResourceMonitor& operator=(const ResourceMonitor&) = delete;

    // Monitor lifecycle
    bool startMonitoring();
    void stopMonitoring();
    bool isMonitoring() const;
    
    // Resource statistics
    GPUStats getGPUStats() const;
    ModelStats getModelStats(const std::string& modelId) const;
    
    // Resource limits
    void setMaxVRAMUsage(size_t maxUsage);
    void setMaxGPUUtilization(float maxUtilization);
    
    // Alert callbacks
    using ResourceAlertCallback = std::function<void(const std::string&, const std::string&)>;
    void setResourceAlertCallback(ResourceAlertCallback callback);
    
    // Model statistics
    void updateModelStats(const std::string& modelId,
                         size_t memoryUsage,
                         size_t computeTime,
                         float latency);
    
    // Error handling
    const char* getLastError() const;
    void clearLastError();

private:
    ResourceMonitor();
    ~ResourceMonitor();

    // Monitoring thread function
    void monitoringThread();
    
    // Resource checking
    void checkGPUResources();
    void checkModelResources();
    
    // Statistics collection
    GPUStats collectGPUStats();
    void updateGPUStats(const GPUStats& stats);
    
    // Alert handling
    void triggerAlert(const std::string& resource, const std::string& message);
    
    // Thread synchronization
    std::mutex mutex_;
    std::thread monitoringThread_;
    
    // Monitoring state
    std::atomic<bool> monitoring_;
    std::atomic<size_t> maxVRAMUsage_;
    std::atomic<float> maxGPUUtilization_;
    
    // Statistics
    GPUStats currentGPUStats_;
    std::unordered_map<std::string, ModelStats> modelStats_;
    
    // Alert callback
    ResourceAlertCallback alertCallback_;
    
    // Error handling
    std::string lastError_;
};

} // namespace cogniware 