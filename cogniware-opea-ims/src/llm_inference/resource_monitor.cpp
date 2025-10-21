#include "../../include/llm_inference/resource_monitor.h"
#include <spdlog/spdlog.h>
#include <cuda_runtime.h>
#include <nvml.h>
#include <thread>
#include <chrono>

namespace cogniware {
namespace llm_inference {

ResourceMonitor& ResourceMonitor::getInstance() {
    static ResourceMonitor instance;
    return instance;
}

ResourceMonitor::ResourceMonitor()
    : is_running_(false)
    , update_interval_ms_(1000)
    , gpu_memory_threshold_(0.9f)  // 90% threshold
    , cpu_memory_threshold_(0.9f)  // 90% threshold
    , gpu_util_threshold_(0.9f)    // 90% threshold
    , cpu_util_threshold_(0.9f)    // 90% threshold
{
    try {
        // Initialize NVML
        nvmlReturn_t result = nvmlInit_v2();
        if (result != NVML_SUCCESS) {
            throw std::runtime_error("Failed to initialize NVML: " + 
                std::string(nvmlErrorString(result)));
        }

        // Get device count
        unsigned int device_count;
        result = nvmlDeviceGetCount_v2(&device_count);
        if (result != NVML_SUCCESS) {
            throw std::runtime_error("Failed to get device count: " + 
                std::string(nvmlErrorString(result)));
        }

        if (device_count == 0) {
            throw std::runtime_error("No NVIDIA devices found");
        }

        // Initialize device handles
        device_handles_.resize(device_count);
        for (unsigned int i = 0; i < device_count; ++i) {
            result = nvmlDeviceGetHandleByIndex_v2(i, &device_handles_[i]);
            if (result != NVML_SUCCESS) {
                throw std::runtime_error("Failed to get device handle: " + 
                    std::string(nvmlErrorString(result)));
            }
        }

        spdlog::info("Resource Monitor initialized with {} devices", device_count);
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize Resource Monitor: {}", e.what());
        throw;
    }
}

ResourceMonitor::~ResourceMonitor() {
    try {
        stop();
        nvmlShutdown();
        spdlog::info("Resource Monitor cleaned up");
    } catch (const std::exception& e) {
        spdlog::error("Error during Resource Monitor cleanup: {}", e.what());
    }
}

void ResourceMonitor::start() {
    try {
        std::lock_guard<std::mutex> lock(mutex_);
        if (is_running_) {
            return;
        }

        is_running_ = true;
        monitor_thread_ = std::thread(&ResourceMonitor::monitorLoop, this);
        spdlog::info("Resource Monitor started");
    } catch (const std::exception& e) {
        spdlog::error("Failed to start Resource Monitor: {}", e.what());
        throw;
    }
}

void ResourceMonitor::stop() {
    try {
        {
            std::lock_guard<std::mutex> lock(mutex_);
            if (!is_running_) {
                return;
            }
            is_running_ = false;
        }

        if (monitor_thread_.joinable()) {
            monitor_thread_.join();
        }

        spdlog::info("Resource Monitor stopped");
    } catch (const std::exception& e) {
        spdlog::error("Failed to stop Resource Monitor: {}", e.what());
        throw;
    }
}

void ResourceMonitor::setUpdateInterval(size_t ms) {
    std::lock_guard<std::mutex> lock(mutex_);
    update_interval_ms_ = ms;
    spdlog::info("Set update interval to {} ms", ms);
}

void ResourceMonitor::setGPUMemoryThreshold(float threshold) {
    std::lock_guard<std::mutex> lock(mutex_);
    gpu_memory_threshold_ = threshold;
    spdlog::info("Set GPU memory threshold to {}", threshold);
}

void ResourceMonitor::setCPUMemoryThreshold(float threshold) {
    std::lock_guard<std::mutex> lock(mutex_);
    cpu_memory_threshold_ = threshold;
    spdlog::info("Set CPU memory threshold to {}", threshold);
}

void ResourceMonitor::setGPUUtilThreshold(float threshold) {
    std::lock_guard<std::mutex> lock(mutex_);
    gpu_util_threshold_ = threshold;
    spdlog::info("Set GPU utilization threshold to {}", threshold);
}

void ResourceMonitor::setCPUUtilThreshold(float threshold) {
    std::lock_guard<std::mutex> lock(mutex_);
    cpu_util_threshold_ = threshold;
    spdlog::info("Set CPU utilization threshold to {}", threshold);
}

void ResourceMonitor::registerCallback(const ResourceCallback& callback) {
    std::lock_guard<std::mutex> lock(mutex_);
    callbacks_.push_back(callback);
    spdlog::info("Registered resource callback");
}

void ResourceMonitor::unregisterCallback(const ResourceCallback& callback) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = std::find(callbacks_.begin(), callbacks_.end(), callback);
    if (it != callbacks_.end()) {
        callbacks_.erase(it);
        spdlog::info("Unregistered resource callback");
    }
}

void ResourceMonitor::monitorLoop() {
    while (true) {
        try {
            // Check if we should stop
            {
                std::lock_guard<std::mutex> lock(mutex_);
                if (!is_running_) {
                    break;
                }
            }

            // Collect metrics
            ResourceMetrics metrics;
            collectMetrics(metrics);

            // Check thresholds
            checkThresholds(metrics);

            // Notify callbacks
            notifyCallbacks(metrics);

            // Sleep until next update
            std::this_thread::sleep_for(std::chrono::milliseconds(update_interval_ms_));
        } catch (const std::exception& e) {
            spdlog::error("Error in monitor loop: {}", e.what());
        }
    }
}

void ResourceMonitor::collectMetrics(ResourceMetrics& metrics) {
    try {
        // Get GPU metrics
        for (size_t i = 0; i < device_handles_.size(); ++i) {
            nvmlDevice_t device = device_handles_[i];
            GPUDeviceMetrics device_metrics;

            // Memory info
            nvmlMemory_t memory;
            nvmlReturn_t result = nvmlDeviceGetMemoryInfo(device, &memory);
            if (result == NVML_SUCCESS) {
                device_metrics.total_memory = memory.total;
                device_metrics.used_memory = memory.used;
                device_metrics.free_memory = memory.free;
            }

            // Utilization
            nvmlUtilization_t utilization;
            result = nvmlDeviceGetUtilizationRates(device, &utilization);
            if (result == NVML_SUCCESS) {
                device_metrics.gpu_utilization = utilization.gpu;
                device_metrics.memory_utilization = utilization.memory;
            }

            // Temperature
            unsigned int temperature;
            result = nvmlDeviceGetTemperature(device, NVML_TEMPERATURE_GPU, &temperature);
            if (result == NVML_SUCCESS) {
                device_metrics.temperature = temperature;
            }

            // Power usage
            unsigned int power;
            result = nvmlDeviceGetPowerUsage(device, &power);
            if (result == NVML_SUCCESS) {
                device_metrics.power_usage = power / 1000.0f;  // Convert to watts
            }

            metrics.gpu_metrics.push_back(device_metrics);
        }

        // Get CPU metrics
        metrics.cpu_metrics.total_memory = getTotalSystemMemory();
        metrics.cpu_metrics.used_memory = getUsedSystemMemory();
        metrics.cpu_metrics.free_memory = metrics.cpu_metrics.total_memory - metrics.cpu_metrics.used_memory;
        metrics.cpu_metrics.cpu_utilization = getCPUUtilization();

        // Set timestamp
        metrics.timestamp = std::chrono::steady_clock::now();
    } catch (const std::exception& e) {
        spdlog::error("Failed to collect metrics: {}", e.what());
        throw;
    }
}

void ResourceMonitor::checkThresholds(const ResourceMetrics& metrics) {
    try {
        // Check GPU metrics
        for (const auto& device : metrics.gpu_metrics) {
            float memory_usage = static_cast<float>(device.used_memory) / device.total_memory;
            if (memory_usage > gpu_memory_threshold_) {
                spdlog::warn("GPU memory usage ({}) exceeds threshold ({})", 
                    memory_usage, gpu_memory_threshold_);
            }

            float gpu_util = device.gpu_utilization / 100.0f;
            if (gpu_util > gpu_util_threshold_) {
                spdlog::warn("GPU utilization ({}) exceeds threshold ({})", 
                    gpu_util, gpu_util_threshold_);
            }
        }

        // Check CPU metrics
        float memory_usage = static_cast<float>(metrics.cpu_metrics.used_memory) / 
            metrics.cpu_metrics.total_memory;
        if (memory_usage > cpu_memory_threshold_) {
            spdlog::warn("CPU memory usage ({}) exceeds threshold ({})", 
                memory_usage, cpu_memory_threshold_);
        }

        float cpu_util = metrics.cpu_metrics.cpu_utilization / 100.0f;
        if (cpu_util > cpu_util_threshold_) {
            spdlog::warn("CPU utilization ({}) exceeds threshold ({})", 
                cpu_util, cpu_util_threshold_);
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to check thresholds: {}", e.what());
    }
}

void ResourceMonitor::notifyCallbacks(const ResourceMetrics& metrics) {
    try {
        std::lock_guard<std::mutex> lock(mutex_);
        for (const auto& callback : callbacks_) {
            callback(metrics);
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to notify callbacks: {}", e.what());
    }
}

size_t ResourceMonitor::getTotalSystemMemory() {
    // Implementation depends on the operating system
    // This is a placeholder for Windows
    MEMORYSTATUSEX memInfo;
    memInfo.dwLength = sizeof(MEMORYSTATUSEX);
    GlobalMemoryStatusEx(&memInfo);
    return memInfo.ullTotalPhys;
}

size_t ResourceMonitor::getUsedSystemMemory() {
    // Implementation depends on the operating system
    // This is a placeholder for Windows
    MEMORYSTATUSEX memInfo;
    memInfo.dwLength = sizeof(MEMORYSTATUSEX);
    GlobalMemoryStatusEx(&memInfo);
    return memInfo.ullTotalPhys - memInfo.ullAvailPhys;
}

float ResourceMonitor::getCPUUtilization() {
    // Implementation depends on the operating system
    // This is a placeholder for Windows
    FILETIME idleTime, kernelTime, userTime;
    if (GetSystemTimes(&idleTime, &kernelTime, &userTime)) {
        ULARGE_INTEGER idle, kernel, user;
        idle.LowPart = idleTime.dwLowDateTime;
        idle.HighPart = idleTime.dwHighDateTime;
        kernel.LowPart = kernelTime.dwLowDateTime;
        kernel.HighPart = kernelTime.dwHighDateTime;
        user.LowPart = userTime.dwLowDateTime;
        user.HighPart = userTime.dwHighDateTime;

        static ULARGE_INTEGER lastIdle = idle;
        static ULARGE_INTEGER lastKernel = kernel;
        static ULARGE_INTEGER lastUser = user;

        ULARGE_INTEGER idleDiff, kernelDiff, userDiff;
        idleDiff.QuadPart = idle.QuadPart - lastIdle.QuadPart;
        kernelDiff.QuadPart = kernel.QuadPart - lastKernel.QuadPart;
        userDiff.QuadPart = user.QuadPart - lastUser.QuadPart;

        lastIdle = idle;
        lastKernel = kernel;
        lastUser = user;

        float total = static_cast<float>(kernelDiff.QuadPart + userDiff.QuadPart);
        if (total > 0) {
            return 100.0f * (1.0f - static_cast<float>(idleDiff.QuadPart) / total);
        }
    }
    return 0.0f;
}

} // namespace llm_inference
} // namespace cogniware 