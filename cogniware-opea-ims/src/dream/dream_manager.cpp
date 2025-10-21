#include "dream/dream_manager.h"
#include <cuda_runtime.h>
#include <algorithm>
#include <random>
#include <sstream>
#include <iomanip>
#include <spdlog/spdlog.h>

namespace cogniware {
namespace dream {

void DreamManager::initialize_resources(int num_gpus) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    devices_.resize(num_gpus);
    for (int i = 0; i < num_gpus; i++) {
        devices_[i].device_id = i;
        
        // Set device
        cudaSetDevice(i);
        
        // Get device properties
        cudaDeviceProp prop;
        cudaGetDeviceProperties(&prop, i);
        
        // Create streams
        const int num_streams = 4;  // Default number of streams per device
        devices_[i].streams.resize(num_streams);
        for (int j = 0; j < num_streams; j++) {
            cudaStreamCreate(&devices_[i].streams[j]);
        }
        
        spdlog::info("Initialized GPU {}: {}", i, prop.name);
    }
}

void DreamManager::release_resources() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    for (auto& device : devices_) {
        cudaSetDevice(device.device_id);
        
        // Release all streams
        for (auto& stream : device.streams) {
            cudaStreamDestroy(stream);
        }
        
        // Free all allocated memory
        for (auto& task_pair : device.tasks) {
            for (auto* ptr : task_pair.second.allocated_memory) {
                cudaFree(ptr);
            }
        }
    }
    
    devices_.clear();
    task_to_device_.clear();
}

ResourceMetrics DreamManager::get_resource_metrics(int device_id) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (device_id < 0 || device_id >= devices_.size()) {
        throw std::runtime_error("Invalid device ID");
    }
    
    ResourceMetrics metrics;
    cudaSetDevice(device_id);
    
    // Get GPU utilization
    cudaDeviceProp prop;
    cudaGetDeviceProperties(&prop, device_id);
    
    // Get memory info
    size_t free, total;
    cudaMemGetInfo(&free, &total);
    
    metrics.free_memory = free;
    metrics.total_memory = total;
    metrics.memory_utilization = 1.0f - (static_cast<float>(free) / total);
    
    // Get active streams
    metrics.active_streams = devices_[device_id].active_streams;
    
    // Estimate compute utilization based on active tasks
    metrics.compute_utilization = static_cast<float>(metrics.active_streams) / 
                                devices_[device_id].streams.size();
    
    return metrics;
}

std::string DreamManager::schedule_task(const std::string& model_name,
                                      const std::vector<int>& input_tokens,
                                      int priority) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Generate unique task ID
    std::stringstream ss;
    ss << model_name << "_" << std::hex << std::time(nullptr) << "_" 
       << std::uniform_int_distribution<>(0, 9999)(std::random_device());
    std::string task_id = ss.str();
    
    // Estimate required memory
    size_t required_memory = input_tokens.size() * sizeof(int) * 2;  // Rough estimate
    
    // Select device
    int device_id = select_device(model_name, required_memory);
    
    // Create task
    Task task;
    task.model_name = model_name;
    task.input_tokens = input_tokens;
    task.priority = priority;
    task.start_time = std::chrono::system_clock::now();
    task.status = "scheduled";
    task.completed = false;
    
    // Assign stream
    task.stream = devices_[device_id].streams[devices_[device_id].active_streams++];
    
    // Store task
    devices_[device_id].tasks[task_id] = task;
    task_to_device_[task_id] = device_id;
    
    spdlog::info("Scheduled task {} on device {}", task_id, device_id);
    
    return task_id;
}

void DreamManager::cancel_task(const std::string& task_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = task_to_device_.find(task_id);
    if (it == task_to_device_.end()) {
        throw std::runtime_error("Task not found: " + task_id);
    }
    
    int device_id = it->second;
    auto& device = devices_[device_id];
    
    // Free allocated memory
    for (auto* ptr : device.tasks[task_id].allocated_memory) {
        cudaFree(ptr);
    }
    
    // Release stream
    device.active_streams--;
    
    // Remove task
    device.tasks.erase(task_id);
    task_to_device_.erase(task_id);
    
    spdlog::info("Cancelled task {}", task_id);
}

TaskMetrics DreamManager::get_task_metrics(const std::string& task_id) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = task_to_device_.find(task_id);
    if (it == task_to_device_.end()) {
        throw std::runtime_error("Task not found: " + task_id);
    }
    
    const auto& task = devices_[it->second].tasks.at(task_id);
    
    TaskMetrics metrics;
    metrics.task_id = task_id;
    metrics.model_name = task.model_name;
    metrics.priority = task.priority;
    metrics.completed = task.completed;
    metrics.status = task.status;
    
    // Calculate execution time
    auto end_time = task.completed ? 
        task.start_time + std::chrono::seconds(1) :  // Placeholder for completed time
        std::chrono::system_clock::now();
    metrics.execution_time = std::chrono::duration_cast<std::chrono::microseconds>(
        end_time - task.start_time);
    
    // Calculate memory usage
    metrics.memory_usage = 0;
    for (auto* ptr : task.allocated_memory) {
        size_t size;
        cudaMemSize(ptr, &size);
        metrics.memory_usage += size;
    }
    
    return metrics;
}

cudaStream_t DreamManager::get_stream(const std::string& task_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = task_to_device_.find(task_id);
    if (it == task_to_device_.end()) {
        throw std::runtime_error("Task not found: " + task_id);
    }
    
    return devices_[it->second].tasks[task_id].stream;
}

void DreamManager::release_stream(const std::string& task_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = task_to_device_.find(task_id);
    if (it == task_to_device_.end()) {
        throw std::runtime_error("Task not found: " + task_id);
    }
    
    devices_[it->second].active_streams--;
}

void* DreamManager::allocate_memory(size_t size, const std::string& task_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = task_to_device_.find(task_id);
    if (it == task_to_device_.end()) {
        throw std::runtime_error("Task not found: " + task_id);
    }
    
    int device_id = it->second;
    cudaSetDevice(device_id);
    
    void* ptr;
    cudaMalloc(&ptr, size);
    if (!ptr) {
        throw std::runtime_error("Failed to allocate GPU memory");
    }
    
    devices_[device_id].tasks[task_id].allocated_memory.push_back(ptr);
    devices_[device_id].used_memory += size;
    
    return ptr;
}

void DreamManager::free_memory(void* ptr, const std::string& task_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = task_to_device_.find(task_id);
    if (it == task_to_device_.end()) {
        throw std::runtime_error("Task not found: " + task_id);
    }
    
    int device_id = it->second;
    auto& task = devices_[device_id].tasks[task_id];
    
    // Find and remove pointer from allocated memory list
    auto ptr_it = std::find(task.allocated_memory.begin(), 
                          task.allocated_memory.end(), ptr);
    if (ptr_it != task.allocated_memory.end()) {
        size_t size;
        cudaMemSize(ptr, &size);
        devices_[device_id].used_memory -= size;
        cudaFree(ptr);
        task.allocated_memory.erase(ptr_it);
    }
}

void DreamManager::set_task_priority(const std::string& task_id, int priority) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = task_to_device_.find(task_id);
    if (it == task_to_device_.end()) {
        throw std::runtime_error("Task not found: " + task_id);
    }
    
    devices_[it->second].tasks[task_id].priority = priority;
}

void DreamManager::update_task_status(const std::string& task_id, 
                                    const std::string& status) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = task_to_device_.find(task_id);
    if (it == task_to_device_.end()) {
        throw std::runtime_error("Task not found: " + task_id);
    }
    
    devices_[it->second].tasks[task_id].status = status;
    if (status == "completed") {
        devices_[it->second].tasks[task_id].completed = true;
    }
}

void DreamManager::optimize_resource_allocation() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    for (auto& device : devices_) {
        // Clean up completed tasks
        cleanup_completed_tasks();
        
        // Update device metrics
        update_device_metrics(device.device_id);
        
        // Rebalance tasks if needed
        rebalance_tasks();
    }
}

void DreamManager::balance_load() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Calculate average load
    float total_load = 0.0f;
    for (const auto& device : devices_) {
        total_load += static_cast<float>(device.active_streams) / device.streams.size();
    }
    float avg_load = total_load / devices_.size();
    
    // Move tasks from overloaded to underloaded devices
    for (size_t i = 0; i < devices_.size(); i++) {
        float device_load = static_cast<float>(devices_[i].active_streams) / 
                          devices_[i].streams.size();
        
        if (device_load > avg_load * 1.2f) {  // 20% threshold
            // Find tasks to move
            for (auto& task_pair : devices_[i].tasks) {
                if (!task_pair.second.completed) {
                    // Find least loaded device
                    int target_device = -1;
                    float min_load = 1.0f;
                    
                    for (size_t j = 0; j < devices_.size(); j++) {
                        if (j != i) {
                            float load = static_cast<float>(devices_[j].active_streams) / 
                                       devices_[j].streams.size();
                            if (load < min_load) {
                                min_load = load;
                                target_device = j;
                            }
                        }
                    }
                    
                    if (target_device != -1) {
                        // Move task
                        devices_[target_device].tasks[task_pair.first] = task_pair.second;
                        task_to_device_[task_pair.first] = target_device;
                        devices_[i].tasks.erase(task_pair.first);
                        
                        // Update stream counts
                        devices_[i].active_streams--;
                        devices_[target_device].active_streams++;
                        
                        spdlog::info("Moved task {} from device {} to {}", 
                                   task_pair.first, i, target_device);
                    }
                }
            }
        }
    }
}

std::vector<TaskMetrics> DreamManager::get_active_tasks() const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    std::vector<TaskMetrics> metrics;
    for (const auto& device : devices_) {
        for (const auto& task_pair : device.tasks) {
            if (!task_pair.second.completed) {
                metrics.push_back(get_task_metrics(task_pair.first));
            }
        }
    }
    return metrics;
}

std::vector<ResourceMetrics> DreamManager::get_all_resource_metrics() const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    std::vector<ResourceMetrics> metrics;
    for (size_t i = 0; i < devices_.size(); i++) {
        metrics.push_back(get_resource_metrics(i));
    }
    return metrics;
}

int DreamManager::select_device(const std::string& model_name, 
                              size_t required_memory) {
    // Simple device selection based on available memory and load
    int selected_device = -1;
    float min_load = 1.0f;
    
    for (size_t i = 0; i < devices_.size(); i++) {
        size_t free, total;
        cudaSetDevice(i);
        cudaMemGetInfo(&free, &total);
        
        if (free >= required_memory) {
            float load = static_cast<float>(devices_[i].active_streams) / 
                        devices_[i].streams.size();
            if (load < min_load) {
                min_load = load;
                selected_device = i;
            }
        }
    }
    
    if (selected_device == -1) {
        throw std::runtime_error("No device with sufficient memory available");
    }
    
    return selected_device;
}

void DreamManager::cleanup_completed_tasks() {
    for (auto& device : devices_) {
        for (auto it = device.tasks.begin(); it != device.tasks.end();) {
            if (it->second.completed) {
                // Free allocated memory
                for (auto* ptr : it->second.allocated_memory) {
                    cudaFree(ptr);
                }
                
                // Release stream
                device.active_streams--;
                
                // Remove task
                task_to_device_.erase(it->first);
                it = device.tasks.erase(it);
            } else {
                ++it;
            }
        }
    }
}

void DreamManager::update_device_metrics(int device_id) {
    cudaSetDevice(device_id);
    
    // Update memory usage
    size_t free, total;
    cudaMemGetInfo(&free, &total);
    devices_[device_id].used_memory = total - free;
}

void DreamManager::rebalance_tasks() {
    // Implement task rebalancing logic here
    // This could involve moving tasks between devices based on:
    // - Current load
    // - Task priorities
    // - Memory usage
    // - GPU utilization
}

} // namespace dream
} // namespace cogniware 