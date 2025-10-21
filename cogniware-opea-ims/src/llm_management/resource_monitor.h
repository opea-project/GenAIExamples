#pragma once

#include <memory>
#include <string>
#include <vector>
#include <unordered_map>
#include <mutex>
#include <atomic>
#include <chrono>

namespace cogniware {
namespace llm_management {

// Resource usage statistics
struct ResourceStats {
    double gpu_memory_usage;      // GPU memory usage in MB
    double gpu_utilization;       // GPU utilization percentage
    double cpu_memory_usage;      // CPU memory usage in MB
    double cpu_utilization;       // CPU utilization percentage
    int64_t active_requests;      // Number of active requests
    int64_t queued_requests;      // Number of queued requests
    std::chrono::system_clock::time_point timestamp;

    ResourceStats() : 
        gpu_memory_usage(0.0),
        gpu_utilization(0.0),
        cpu_memory_usage(0.0),
        cpu_utilization(0.0),
        active_requests(0),
        queued_requests(0) {}
};

// Resource thresholds
struct ResourceThresholds {
    double max_gpu_memory;        // Maximum GPU memory usage in MB
    double max_gpu_utilization;   // Maximum GPU utilization percentage
    double max_cpu_memory;        // Maximum CPU memory usage in MB
    double max_cpu_utilization;   // Maximum CPU utilization percentage
    int64_t max_active_requests;  // Maximum number of active requests
    int64_t max_queued_requests;  // Maximum number of queued requests

    ResourceThresholds() :
        max_gpu_memory(0.0),
        max_gpu_utilization(0.0),
        max_cpu_memory(0.0),
        max_cpu_utilization(0.0),
        max_active_requests(0),
        max_queued_requests(0) {}
};

// Resource monitor class
class ResourceMonitor {
public:
    ResourceMonitor();
    ~ResourceMonitor();

    // Prevent copying
    ResourceMonitor(const ResourceMonitor&) = delete;
    ResourceMonitor& operator=(const ResourceMonitor&) = delete;

    // Configuration
    void setThresholds(const ResourceThresholds& thresholds);
    ResourceThresholds getThresholds() const;
    void setMonitoringInterval(std::chrono::milliseconds interval);
    std::chrono::milliseconds getMonitoringInterval() const;

    // Resource monitoring
    void startMonitoring();
    void stopMonitoring();
    bool isMonitoring() const;
    ResourceStats getCurrentStats() const;
    std::vector<ResourceStats> getHistoricalStats(std::chrono::seconds duration) const;

    // Resource checks
    bool checkResourceAvailability() const;
    bool checkResourceLimits() const;
    std::string getResourceStatus() const;

    // Resource updates
    void updateResourceUsage(const ResourceStats& stats);
    void incrementActiveRequests();
    void decrementActiveRequests();
    void incrementQueuedRequests();
    void decrementQueuedRequests();

    // Resource alerts
    void setResourceAlertCallback(std::function<void(const ResourceStats&)> callback);
    void clearResourceAlertCallback();

private:
    // Internal implementation
    struct Impl;
    std::unique_ptr<Impl> pimpl;
};

} // namespace llm_management
} // namespace cogniware
