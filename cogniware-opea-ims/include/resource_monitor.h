#ifndef RESOURCE_MONITOR_H
#define RESOURCE_MONITOR_H

#include <string>
#include <vector>
#include <mutex>
#include <thread>
#include <atomic>
#include <functional>
#include <chrono>
#include "gpu_memory_manager.h"

namespace cogniware {

struct GPUStats {
    size_t total_memory;
    size_t used_memory;
    size_t free_memory;
    float utilization;
    float temperature;
    float power_usage;
};

struct ModelStats {
    std::string model_id;
    size_t parameter_count;
    size_t vram_usage;
    size_t active_requests;
    float average_latency;
    float throughput;
};

class ResourceMonitor {
public:
    static ResourceMonitor& getInstance();

    // Monitoring control
    void startMonitoring();
    void stopMonitoring();
    bool isMonitoring() const;

    // Statistics access
    GPUStats getGPUStats() const;
    std::vector<ModelStats> getModelStats() const;
    ModelStats getModelStats(const std::string& model_id) const;

    // Resource limits
    void setMaxVRAMUsage(size_t max_vram_mb);
    void setMaxGPUUtilization(float max_utilization);
    size_t getMaxVRAMUsage() const;
    float getMaxGPUUtilization() const;

    // Callbacks
    using ResourceAlertCallback = std::function<void(const std::string&, const GPUStats&)>;
    void setResourceAlertCallback(ResourceAlertCallback callback);

private:
    ResourceMonitor();
    ~ResourceMonitor();

    // Prevent copying
    ResourceMonitor(const ResourceMonitor&) = delete;
    ResourceMonitor& operator=(const ResourceMonitor&) = delete;

    // Monitoring thread
    void monitoringThread();
    void updateStats();
    bool checkResourceLimits();

    // Internal state
    std::atomic<bool> monitoring_;
    std::thread monitor_thread_;
    mutable std::mutex stats_mutex_;

    // Current statistics
    GPUStats current_gpu_stats_;
    std::vector<ModelStats> current_model_stats_;

    // Resource limits
    size_t max_vram_usage_;
    float max_gpu_utilization_;

    // Alert callback
    ResourceAlertCallback alert_callback_;
    std::mutex callback_mutex_;

    // Monitoring interval
    std::chrono::milliseconds monitoring_interval_;
};

} // namespace cogniware

#endif // RESOURCE_MONITOR_H 