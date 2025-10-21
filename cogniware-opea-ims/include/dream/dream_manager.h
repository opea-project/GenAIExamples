#pragma once

#include <string>
#include <vector>
#include <memory>
#include <mutex>
#include <unordered_map>
#include <chrono>
#include <atomic>
#include <cuda_runtime.h>

namespace cogniware {
namespace dream {

struct ResourceMetrics {
    float gpu_utilization;
    float memory_utilization;
    float compute_utilization;
    int active_streams;
    size_t free_memory;
    size_t total_memory;
};

struct TaskMetrics {
    std::string task_id;
    std::string model_name;
    std::chrono::microseconds execution_time;
    size_t memory_usage;
    int priority;
    bool completed;
    std::string status;
};

class DreamManager {
public:
    static DreamManager& get_instance() {
        static DreamManager instance;
        return instance;
    }

    // Resource management
    void initialize_resources(int num_gpus);
    void release_resources();
    ResourceMetrics get_resource_metrics(int device_id) const;
    
    // Task management
    std::string schedule_task(const std::string& model_name, 
                            const std::vector<int>& input_tokens,
                            int priority = 0);
    void cancel_task(const std::string& task_id);
    TaskMetrics get_task_metrics(const std::string& task_id) const;
    
    // Stream management
    cudaStream_t get_stream(const std::string& task_id);
    void release_stream(const std::string& task_id);
    
    // Memory management
    void* allocate_memory(size_t size, const std::string& task_id);
    void free_memory(void* ptr, const std::string& task_id);
    
    // Priority management
    void set_task_priority(const std::string& task_id, int priority);
    void update_task_status(const std::string& task_id, const std::string& status);
    
    // Resource optimization
    void optimize_resource_allocation();
    void balance_load();
    
    // Monitoring
    std::vector<TaskMetrics> get_active_tasks() const;
    std::vector<ResourceMetrics> get_all_resource_metrics() const;

private:
    DreamManager() = default;
    ~DreamManager() = default;
    
    // Prevent copying
    DreamManager(const DreamManager&) = delete;
    DreamManager& operator=(const DreamManager&) = delete;
    
    struct Task {
        std::string model_name;
        std::vector<int> input_tokens;
        int priority;
        std::chrono::system_clock::time_point start_time;
        cudaStream_t stream;
        std::vector<void*> allocated_memory;
        std::string status;
        bool completed;
    };
    
    struct Device {
        int device_id;
        std::vector<cudaStream_t> streams;
        std::unordered_map<std::string, Task> tasks;
        std::atomic<size_t> used_memory{0};
        std::atomic<int> active_streams{0};
        
        Device() : device_id(-1) {}
        Device(int id) : device_id(id) {}
        
        // Copy constructor
        Device(const Device& other) 
            : device_id(other.device_id),
              streams(other.streams),
              tasks(other.tasks),
              used_memory(other.used_memory.load()),
              active_streams(other.active_streams.load()) {}
        
        // Assignment operator
        Device& operator=(const Device& other) {
            if (this != &other) {
                device_id = other.device_id;
                streams = other.streams;
                tasks = other.tasks;
                used_memory.store(other.used_memory.load());
                active_streams.store(other.active_streams.load());
            }
            return *this;
        }
    };
    
    std::vector<Device> devices_;
    std::unordered_map<std::string, int> task_to_device_;
    mutable std::mutex mutex_;
    
    // Helper methods
    int select_device(const std::string& model_name, size_t required_memory);
    void cleanup_completed_tasks();
    void update_device_metrics(int device_id);
    void rebalance_tasks();
};

} // namespace dream
} // namespace cogniware 