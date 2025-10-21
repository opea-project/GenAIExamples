/**
 * @file resource_monitor.hpp
 * @brief Resource monitoring for LLM instances
 */

#ifndef MSMARTCOMPUTE_RESOURCE_MONITOR_HPP
#define MSMARTCOMPUTE_RESOURCE_MONITOR_HPP

#include <cuda_runtime.h>
#include <cuda.h>
#include <string>
#include <memory>
#include <mutex>
#include <unordered_map>

namespace cogniware {

/**
 * @brief Structure containing GPU resource statistics
 */
struct GPUResourceStats {
    size_t vram_used;
    size_t vram_total;
    float gpu_utilization;
    float memory_utilization;
    float temperature;
    float power_usage;
    int compute_mode;
    int device_id;
};

/**
 * @brief Class for monitoring GPU resources
 */
class ResourceMonitor {
public:
    /**
     * @brief Get singleton instance
     * @return Reference to the singleton instance
     */
    static ResourceMonitor& getInstance();

    /**
     * @brief Initialize the monitor
     * @return true if initialization successful, false otherwise
     */
    bool initialize();

    /**
     * @brief Get resource statistics for a specific device
     * @param device_id GPU device ID
     * @return Resource statistics
     */
    GPUResourceStats getDeviceStats(int device_id);

    /**
     * @brief Get resource statistics for all devices
     * @return Map of device ID to resource statistics
     */
    std::unordered_map<int, GPUResourceStats> getAllDeviceStats();

    /**
     * @brief Check if a device has sufficient resources
     * @param device_id GPU device ID
     * @param required_vram_mb Required VRAM in MB
     * @return true if device has sufficient resources, false otherwise
     */
    bool checkDeviceResources(int device_id, size_t required_vram_mb);

private:
    ResourceMonitor() = default;
    ~ResourceMonitor() = default;
    ResourceMonitor(const ResourceMonitor&) = delete;
    ResourceMonitor& operator=(const ResourceMonitor&) = delete;

    /**
     * @brief Get CUDA device properties
     * @param device_id GPU device ID
     * @return CUDA device properties
     */
    cudaDeviceProp getDeviceProperties(int device_id);

    /**
     * @brief Get device memory info
     * @param device_id GPU device ID
     * @param free_memory Free memory in bytes
     * @param total_memory Total memory in bytes
     */
    void getDeviceMemoryInfo(int device_id, size_t& free_memory, size_t& total_memory);

    /**
     * @brief Get device utilization
     * @param device_id GPU device ID
     * @param gpu_util GPU utilization percentage
     * @param memory_util Memory utilization percentage
     */
    void getDeviceUtilization(int device_id, float& gpu_util, float& memory_util);

    std::mutex mutex_;
    bool initialized_ = false;
    int num_devices_ = 0;
};

} // namespace cogniware

#endif // MSMARTCOMPUTE_RESOURCE_MONITOR_HPP 