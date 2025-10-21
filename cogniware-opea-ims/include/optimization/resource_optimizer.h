#pragma once

#include <string>
#include <vector>
#include <map>
#include <memory>
#include <chrono>
#include <thread>
#include <mutex>
#include <atomic>

namespace cogniware {

class ResourceOptimizer {
public:
    ResourceOptimizer();
    
    // Memory management
    struct MemoryMetrics {
        size_t total_memory;
        size_t used_memory;
        size_t free_memory;
        float memory_utilization;
    };
    
    MemoryMetrics get_memory_metrics();
    bool optimize_memory_usage();
    void set_memory_threshold(float threshold);
    
    // GPU optimization
    struct GPUMetrics {
        float utilization;
        size_t total_memory;
        size_t used_memory;
        size_t free_memory;
        float temperature;
        int power_usage;
    };
    
    GPUMetrics get_gpu_metrics(int device_id = 0);
    bool optimize_gpu_usage(int device_id = 0);
    void set_gpu_threshold(float threshold);
    
    // Resource allocation
    struct ResourceAllocation {
        float cpu_cores;
        size_t memory_mb;
        size_t gpu_memory_mb;
        int gpu_device_id;
    };
    
    bool allocate_resources(const std::string& model_id, 
                          const ResourceAllocation& allocation);
    bool release_resources(const std::string& model_id);
    
    // Monitoring
    void start_monitoring();
    void stop_monitoring();
    std::map<std::string, float> get_performance_metrics();
    
    // Scalability
    bool scale_resources(const std::string& model_id, float scale_factor);
    bool redistribute_resources();

private:
    std::mutex metrics_mutex_;
    std::atomic<bool> monitoring_active_;
    std::thread monitoring_thread_;
    
    std::map<std::string, ResourceAllocation> current_allocations_;
    std::map<std::string, std::chrono::steady_clock::time_point> allocation_timestamps_;
    
    float memory_threshold_;
    float gpu_threshold_;
    
    // Internal methods
    void monitoring_loop();
    bool check_resource_availability(const ResourceAllocation& allocation);
    void cleanup_unused_resources();
    void optimize_resource_distribution();
    
    // Performance tracking
    struct PerformanceMetrics {
        float inference_latency;
        float throughput;
        float resource_efficiency;
        float cost_per_inference;
    };
    
    std::map<std::string, PerformanceMetrics> performance_history_;
    void update_performance_metrics(const std::string& model_id, 
                                  const PerformanceMetrics& metrics);
}; 