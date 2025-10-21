/**
 * @file resource_monitor.cpp
 * @brief Implementation of the resource monitor
 */

#include "resource_monitor.h"
#include <spdlog/spdlog.h>
#include <thread>
#include <condition_variable>
#include <deque>
#include <algorithm>

namespace cogniware {
namespace llm_management {

// Internal implementation
struct ResourceMonitor::Impl {
    ResourceThresholds thresholds;
    std::chrono::milliseconds monitoring_interval;
    std::atomic<bool> is_monitoring;
    std::atomic<bool> should_stop;
    std::thread monitoring_thread;
    std::mutex stats_mutex;
    std::condition_variable stop_cv;
    ResourceStats current_stats;
    std::deque<ResourceStats> historical_stats;
    std::function<void(const ResourceStats&)> alert_callback;
    static constexpr size_t MAX_HISTORY_SIZE = 3600; // 1 hour of history at 1-second intervals

    Impl() : 
        monitoring_interval(std::chrono::seconds(1)),
        is_monitoring(false),
        should_stop(false) {}

    void monitoringLoop() {
        while (!should_stop) {
            updateStats();
            checkThresholds();
            std::this_thread::sleep_for(monitoring_interval);
        }
    }

    void updateStats() {
        // TODO: Implement actual resource monitoring using system APIs
        // For now, we'll just use the current stats
        std::lock_guard<std::mutex> lock(stats_mutex);
        current_stats.timestamp = std::chrono::system_clock::now();
        historical_stats.push_back(current_stats);
        
        // Trim history if needed
        while (historical_stats.size() > MAX_HISTORY_SIZE) {
            historical_stats.pop_front();
        }
    }

    void checkThresholds() {
        std::lock_guard<std::mutex> lock(stats_mutex);
        bool threshold_exceeded = false;

        if (current_stats.gpu_memory_usage > thresholds.max_gpu_memory) {
            spdlog::warn("GPU memory usage exceeded threshold: {} MB > {} MB",
                        current_stats.gpu_memory_usage, thresholds.max_gpu_memory);
            threshold_exceeded = true;
        }

        if (current_stats.gpu_utilization > thresholds.max_gpu_utilization) {
            spdlog::warn("GPU utilization exceeded threshold: {}% > {}%",
                        current_stats.gpu_utilization, thresholds.max_gpu_utilization);
            threshold_exceeded = true;
        }

        if (current_stats.cpu_memory_usage > thresholds.max_cpu_memory) {
            spdlog::warn("CPU memory usage exceeded threshold: {} MB > {} MB",
                        current_stats.cpu_memory_usage, thresholds.max_cpu_memory);
            threshold_exceeded = true;
        }

        if (current_stats.cpu_utilization > thresholds.max_cpu_utilization) {
            spdlog::warn("CPU utilization exceeded threshold: {}% > {}%",
                        current_stats.cpu_utilization, thresholds.max_cpu_utilization);
            threshold_exceeded = true;
        }

        if (current_stats.active_requests > thresholds.max_active_requests) {
            spdlog::warn("Active requests exceeded threshold: {} > {}",
                        current_stats.active_requests, thresholds.max_active_requests);
            threshold_exceeded = true;
        }

        if (current_stats.queued_requests > thresholds.max_queued_requests) {
            spdlog::warn("Queued requests exceeded threshold: {} > {}",
                        current_stats.queued_requests, thresholds.max_queued_requests);
            threshold_exceeded = true;
        }

        if (threshold_exceeded && alert_callback) {
            alert_callback(current_stats);
        }
    }
};

// Constructor and destructor
ResourceMonitor::ResourceMonitor() : pimpl(std::make_unique<Impl>()) {}

ResourceMonitor::~ResourceMonitor() {
    stopMonitoring();
}

// Configuration
void ResourceMonitor::setThresholds(const ResourceThresholds& thresholds) {
    pimpl->thresholds = thresholds;
}

ResourceThresholds ResourceMonitor::getThresholds() const {
    return pimpl->thresholds;
}

void ResourceMonitor::setMonitoringInterval(std::chrono::milliseconds interval) {
    pimpl->monitoring_interval = interval;
}

std::chrono::milliseconds ResourceMonitor::getMonitoringInterval() const {
    return pimpl->monitoring_interval;
}

// Resource monitoring
void ResourceMonitor::startMonitoring() {
    if (pimpl->is_monitoring) {
        return;
    }

    pimpl->should_stop = false;
    pimpl->is_monitoring = true;
    pimpl->monitoring_thread = std::thread(&Impl::monitoringLoop, pimpl.get());
}

void ResourceMonitor::stopMonitoring() {
    if (!pimpl->is_monitoring) {
        return;
    }

    pimpl->should_stop = true;
    if (pimpl->monitoring_thread.joinable()) {
        pimpl->monitoring_thread.join();
    }
    pimpl->is_monitoring = false;
}

bool ResourceMonitor::isMonitoring() const {
    return pimpl->is_monitoring;
}

ResourceStats ResourceMonitor::getCurrentStats() const {
    std::lock_guard<std::mutex> lock(pimpl->stats_mutex);
    return pimpl->current_stats;
}

std::vector<ResourceStats> ResourceMonitor::getHistoricalStats(std::chrono::seconds duration) const {
    std::lock_guard<std::mutex> lock(pimpl->stats_mutex);
    auto now = std::chrono::system_clock::now();
    std::vector<ResourceStats> result;

    for (auto it = pimpl->historical_stats.rbegin(); it != pimpl->historical_stats.rend(); ++it) {
        if (now - it->timestamp > duration) {
            break;
        }
        result.push_back(*it);
    }

    std::reverse(result.begin(), result.end());
    return result;
}

// Resource checks
bool ResourceMonitor::checkResourceAvailability() const {
    std::lock_guard<std::mutex> lock(pimpl->stats_mutex);
    return pimpl->current_stats.active_requests < pimpl->thresholds.max_active_requests;
}

bool ResourceMonitor::checkResourceLimits() const {
    std::lock_guard<std::mutex> lock(pimpl->stats_mutex);
    return pimpl->current_stats.gpu_memory_usage <= pimpl->thresholds.max_gpu_memory &&
           pimpl->current_stats.gpu_utilization <= pimpl->thresholds.max_gpu_utilization &&
           pimpl->current_stats.cpu_memory_usage <= pimpl->thresholds.max_cpu_memory &&
           pimpl->current_stats.cpu_utilization <= pimpl->thresholds.max_cpu_utilization;
}

std::string ResourceMonitor::getResourceStatus() const {
    std::lock_guard<std::mutex> lock(pimpl->stats_mutex);
    std::stringstream ss;
    ss << "GPU Memory: " << pimpl->current_stats.gpu_memory_usage << " MB / "
       << pimpl->thresholds.max_gpu_memory << " MB\n"
       << "GPU Utilization: " << pimpl->current_stats.gpu_utilization << "% / "
       << pimpl->thresholds.max_gpu_utilization << "%\n"
       << "CPU Memory: " << pimpl->current_stats.cpu_memory_usage << " MB / "
       << pimpl->thresholds.max_cpu_memory << " MB\n"
       << "CPU Utilization: " << pimpl->current_stats.cpu_utilization << "% / "
       << pimpl->thresholds.max_cpu_utilization << "%\n"
       << "Active Requests: " << pimpl->current_stats.active_requests << " / "
       << pimpl->thresholds.max_active_requests << "\n"
       << "Queued Requests: " << pimpl->current_stats.queued_requests << " / "
       << pimpl->thresholds.max_queued_requests;
    return ss.str();
}

// Resource updates
void ResourceMonitor::updateResourceUsage(const ResourceStats& stats) {
    std::lock_guard<std::mutex> lock(pimpl->stats_mutex);
    pimpl->current_stats = stats;
}

void ResourceMonitor::incrementActiveRequests() {
    std::lock_guard<std::mutex> lock(pimpl->stats_mutex);
    ++pimpl->current_stats.active_requests;
}

void ResourceMonitor::decrementActiveRequests() {
    std::lock_guard<std::mutex> lock(pimpl->stats_mutex);
    if (pimpl->current_stats.active_requests > 0) {
        --pimpl->current_stats.active_requests;
    }
}

void ResourceMonitor::incrementQueuedRequests() {
    std::lock_guard<std::mutex> lock(pimpl->stats_mutex);
    ++pimpl->current_stats.queued_requests;
}

void ResourceMonitor::decrementQueuedRequests() {
    std::lock_guard<std::mutex> lock(pimpl->stats_mutex);
    if (pimpl->current_stats.queued_requests > 0) {
        --pimpl->current_stats.queued_requests;
    }
}

// Resource alerts
void ResourceMonitor::setResourceAlertCallback(std::function<void(const ResourceStats&)> callback) {
    pimpl->alert_callback = std::move(callback);
}

void ResourceMonitor::clearResourceAlertCallback() {
    pimpl->alert_callback = nullptr;
}

} // namespace llm_management
} // namespace cogniware
