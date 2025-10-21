#include "monitoring/metrics_collector.h"
#include <spdlog/spdlog.h>
#include <chrono>
#include <thread>
#include <sstream>
#include <iomanip>
#include <cuda_runtime.h>
#include <algorithm>
#include <numeric>
#include <cmath>

namespace cogniware {
namespace monitoring {

MetricsCollector::MetricsCollector()
    : collection_active_(false)
    , registry_(std::make_shared<prometheus::Registry>()) {
    
    // Initialize alert thresholds
    alert_thresholds_ = {
        100.0f,  // max_latency (ms)
        0.01f,   // max_error_rate (1%)
        0.9f,    // max_resource_utilization (90%)
        10       // max_failed_requests
    };
    
    spdlog::info("MetricsCollector initialized");

    // Initialize default metrics
    enable_metric("inference_time");
    enable_metric("memory_usage");
    enable_metric("gpu_utilization");
    enable_metric("latency");
    enable_metric("throughput");
    enable_metric("resource_utilization");
    enable_metric("queue_size");
    enable_metric("cache_hit_rate");
    enable_metric("batch_size");
}

void MetricsCollector::record_inference_metrics(
    const std::string& model_id,
    const PerformanceMetrics& metrics) {
    
    try {
        std::lock_guard<std::mutex> lock(metrics_mutex_);
        model_metrics_[model_id] = metrics;
        
        // Update Prometheus metrics
        if (registry_) {
            auto& counter = inference_counters_[model_id];
            if (!counter) {
                counter = std::make_shared<prometheus::Counter>(
                    prometheus::Counter::Build()
                        .Name("model_inference_total")
                        .Help("Total number of inferences")
                        .Register(*registry_)
                );
            }
            counter->Increment();
            
            auto& histogram = latency_histograms_[model_id];
            if (!histogram) {
                histogram = std::make_shared<prometheus::Histogram>(
                    prometheus::Histogram::Build()
                        .Name("model_inference_latency")
                        .Help("Inference latency in milliseconds")
                        .Register(*registry_)
                );
            }
            histogram->Observe(metrics.inference_latency);
        }
        
        // Check for alerts
        check_alerts();
    } catch (const std::exception& e) {
        spdlog::error("Failed to record inference metrics for model {}: {}", 
                     model_id, e.what());
    }
}

MetricsCollector::PerformanceMetrics MetricsCollector::get_model_metrics(
    const std::string& model_id) {
    
    try {
        std::lock_guard<std::mutex> lock(metrics_mutex_);
        auto it = model_metrics_.find(model_id);
        if (it != model_metrics_.end()) {
            return it->second;
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to get model metrics for {}: {}", 
                     model_id, e.what());
    }
    
    return PerformanceMetrics{};
}

void MetricsCollector::record_resource_metrics(const ResourceMetrics& metrics) {
    try {
        std::lock_guard<std::mutex> lock(metrics_mutex_);
        current_resource_metrics_ = metrics;
        
        // Update Prometheus metrics
        if (registry_) {
            auto& gauge = resource_gauges_["cpu_utilization"];
            if (!gauge) {
                gauge = std::make_shared<prometheus::Gauge>(
                    prometheus::Gauge::Build()
                        .Name("system_cpu_utilization")
                        .Help("CPU utilization percentage")
                        .Register(*registry_)
                );
            }
            gauge->Set(metrics.cpu_utilization);
            
            // Update other resource metrics similarly
            update_prometheus_metrics();
        }
        
        // Check for alerts
        check_alerts();
    } catch (const std::exception& e) {
        spdlog::error("Failed to record resource metrics: {}", e.what());
    }
}

MetricsCollector::ResourceMetrics MetricsCollector::get_resource_metrics() {
    try {
        std::lock_guard<std::mutex> lock(metrics_mutex_);
        return current_resource_metrics_;
    } catch (const std::exception& e) {
        spdlog::error("Failed to get resource metrics: {}", e.what());
        return ResourceMetrics{};
    }
}

void MetricsCollector::update_health_metrics(const HealthMetrics& metrics) {
    try {
        std::lock_guard<std::mutex> lock(metrics_mutex_);
        current_health_metrics_ = metrics;
        
        // Update Prometheus metrics
        if (registry_) {
            auto& gauge = resource_gauges_["system_health"];
            if (!gauge) {
                gauge = std::make_shared<prometheus::Gauge>(
                    prometheus::Gauge::Build()
                        .Name("system_health")
                        .Help("System health status")
                        .Register(*registry_)
                );
            }
            gauge->Set(metrics.is_healthy ? 1.0 : 0.0);
            
            // Update other health metrics
            update_prometheus_metrics();
        }
        
        // Check for alerts
        check_alerts();
    } catch (const std::exception& e) {
        spdlog::error("Failed to update health metrics: {}", e.what());
    }
}

MetricsCollector::HealthMetrics MetricsCollector::get_health_metrics() {
    try {
        std::lock_guard<std::mutex> lock(metrics_mutex_);
        return current_health_metrics_;
    } catch (const std::exception& e) {
        spdlog::error("Failed to get health metrics: {}", e.what());
        return HealthMetrics{};
    }
}

void MetricsCollector::register_metrics(
    std::shared_ptr<prometheus::Registry> registry) {
    
    try {
        registry_ = registry;
        
        // Register all metrics
        for (const auto& [model_id, _] : model_metrics_) {
            inference_counters_[model_id] = std::make_shared<prometheus::Counter>(
                prometheus::Counter::Build()
                    .Name("model_inference_total")
                    .Help("Total number of inferences")
                    .Register(*registry_)
            );
            
            latency_histograms_[model_id] = std::make_shared<prometheus::Histogram>(
                prometheus::Histogram::Build()
                    .Name("model_inference_latency")
                    .Help("Inference latency in milliseconds")
                    .Register(*registry_)
            );
        }
        
        // Register resource metrics
        resource_gauges_["cpu_utilization"] = std::make_shared<prometheus::Gauge>(
            prometheus::Gauge::Build()
                .Name("system_cpu_utilization")
                .Help("CPU utilization percentage")
                .Register(*registry_)
        );
        
        // Register other metrics...
        
        spdlog::info("Metrics registered with Prometheus");
    } catch (const std::exception& e) {
        spdlog::error("Failed to register metrics: {}", e.what());
    }
}

void MetricsCollector::update_prometheus_metrics() {
    try {
        if (!registry_) {
            return;
        }
        
        // Update model metrics
        for (const auto& [model_id, metrics] : model_metrics_) {
            if (auto counter = inference_counters_[model_id]) {
                counter->Increment();
            }
            
            if (auto histogram = latency_histograms_[model_id]) {
                histogram->Observe(metrics.inference_latency);
            }
        }
        
        // Update resource metrics
        if (auto gauge = resource_gauges_["cpu_utilization"]) {
            gauge->Set(current_resource_metrics_.cpu_utilization);
        }
        
        // Update other metrics...
    } catch (const std::exception& e) {
        spdlog::error("Failed to update Prometheus metrics: {}", e.what());
    }
}

void MetricsCollector::add_alert(const Alert& alert) {
    try {
        std::lock_guard<std::mutex> lock(metrics_mutex_);
        active_alerts_.push_back(alert);
        
        spdlog::warn("Alert added: {} - {}", alert.alert_type, alert.message);
    } catch (const std::exception& e) {
        spdlog::error("Failed to add alert: {}", e.what());
    }
}

std::vector<MetricsCollector::Alert> MetricsCollector::get_active_alerts() {
    try {
        std::lock_guard<std::mutex> lock(metrics_mutex_);
        return active_alerts_;
    } catch (const std::exception& e) {
        spdlog::error("Failed to get active alerts: {}", e.what());
        return {};
    }
}

void MetricsCollector::clear_alerts(const std::string& alert_type) {
    try {
        std::lock_guard<std::mutex> lock(metrics_mutex_);
        
        active_alerts_.erase(
            std::remove_if(active_alerts_.begin(),
                          active_alerts_.end(),
                          [&](const Alert& alert) {
                              return alert.alert_type == alert_type;
                          }),
            active_alerts_.end()
        );
        
        spdlog::info("Cleared alerts of type {}", alert_type);
    } catch (const std::exception& e) {
        spdlog::error("Failed to clear alerts: {}", e.what());
    }
}

MetricsCollector::MetricsSnapshot MetricsCollector::get_metrics_snapshot() {
    try {
        std::lock_guard<std::mutex> lock(metrics_mutex_);
        
        return MetricsSnapshot{
            model_metrics_,
            current_resource_metrics_,
            current_health_metrics_,
            active_alerts_,
            std::chrono::system_clock::now()
        };
    } catch (const std::exception& e) {
        spdlog::error("Failed to get metrics snapshot: {}", e.what());
        return MetricsSnapshot{};
    }
}

void MetricsCollector::export_metrics(const std::string& format) {
    try {
        if (!registry_) {
            spdlog::error("No Prometheus registry available");
            return;
        }
        
        if (format == "prometheus") {
            // Export in Prometheus format
            std::stringstream ss;
            prometheus::TextSerializer serializer;
            serializer.Serialize(ss, registry_->Collect());
            
            spdlog::info("Metrics exported in Prometheus format");
            // You can write the metrics to a file or send them to a metrics server
        } else {
            spdlog::error("Unsupported metrics format: {}", format);
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to export metrics: {}", e.what());
    }
}

void MetricsCollector::collection_loop() {
    while (collection_active_) {
        try {
            process_metrics();
            std::this_thread::sleep_for(std::chrono::seconds(5));
        } catch (const std::exception& e) {
            spdlog::error("Error in collection loop: {}", e.what());
        }
    }
}

void MetricsCollector::process_metrics() {
    try {
        // Process model metrics
        for (const auto& [model_id, metrics] : model_metrics_) {
            // Calculate derived metrics
            float efficiency = metrics.throughput / 
                             (metrics.resource_utilization + 0.001f);
            
            // Update performance history
            PerformanceMetrics updated_metrics = metrics;
            updated_metrics.resource_efficiency = efficiency;
            model_metrics_[model_id] = updated_metrics;
        }
        
        // Process resource metrics
        // Add any resource-specific processing here
        
        // Clean up old metrics
        cleanup_old_metrics();
    } catch (const std::exception& e) {
        spdlog::error("Failed to process metrics: {}", e.what());
    }
}

void MetricsCollector::check_alerts() {
    try {
        // Check model metrics
        for (const auto& [model_id, metrics] : model_metrics_) {
            if (metrics.inference_latency > alert_thresholds_.max_latency) {
                add_alert({
                    "high_latency",
                    "High inference latency for model " + model_id,
                    "warning",
                    std::chrono::system_clock::now()
                });
            }
            
            if (metrics.error_rate > alert_thresholds_.max_error_rate) {
                add_alert({
                    "high_error_rate",
                    "High error rate for model " + model_id,
                    "error",
                    std::chrono::system_clock::now()
                });
            }
        }
        
        // Check resource metrics
        if (current_resource_metrics_.cpu_utilization > 
            alert_thresholds_.max_resource_utilization) {
            add_alert({
                "high_cpu_utilization",
                "High CPU utilization",
                "warning",
                std::chrono::system_clock::now()
            });
        }
        
        // Check health metrics
        if (!current_health_metrics_.is_healthy) {
            add_alert({
                "system_unhealthy",
                "System is unhealthy",
                "error",
                std::chrono::system_clock::now()
            });
        }
        
        if (current_health_metrics_.failed_requests > 
            alert_thresholds_.max_failed_requests) {
            add_alert({
                "high_failed_requests",
                "High number of failed requests",
                "warning",
                std::chrono::system_clock::now()
            });
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to check alerts: {}", e.what());
    }
}

void MetricsCollector::cleanup_old_metrics() {
    try {
        auto now = std::chrono::system_clock::now();
        
        // Remove old model metrics (older than 1 hour)
        for (auto it = model_metrics_.begin(); it != model_metrics_.end();) {
            if (now - it->second.timestamp > std::chrono::hours(1)) {
                it = model_metrics_.erase(it);
            } else {
                ++it;
            }
        }
        
        // Remove old alerts (older than 24 hours)
        active_alerts_.erase(
            std::remove_if(active_alerts_.begin(),
                          active_alerts_.end(),
                          [&](const Alert& alert) {
                              return now - alert.timestamp > std::chrono::hours(24);
                          }),
            active_alerts_.end()
        );
    } catch (const std::exception& e) {
        spdlog::error("Failed to cleanup old metrics: {}", e.what());
    }
}

void MetricsCollector::update_alert_thresholds(
    const AlertThresholds& thresholds) {
    
    try {
        alert_thresholds_ = thresholds;
        spdlog::info("Alert thresholds updated");
    } catch (const std::exception& e) {
        spdlog::error("Failed to update alert thresholds: {}", e.what());
    }
}

void MetricsCollector::record_inference_latency(const std::string& model_name,
                                              std::chrono::microseconds latency) {
    std::lock_guard<std::mutex> lock(model_stats_mutex_);
    auto& stats = model_stats_[model_name];
    stats.total_requests++;
    stats.total_latency += latency.count();
}

void MetricsCollector::record_token_count(const std::string& model_name,
                                        int input_tokens, int output_tokens) {
    std::lock_guard<std::mutex> lock(model_stats_mutex_);
    auto& stats = model_stats_[model_name];
    stats.total_input_tokens += input_tokens;
    stats.total_output_tokens += output_tokens;
}

void MetricsCollector::record_gpu_memory_usage(int device_id, size_t used_memory) {
    std::lock_guard<std::mutex> lock(gpu_stats_mutex_);
    auto& stats = gpu_stats_[device_id];
    stats.used_memory = used_memory;
    
    // Get total GPU memory
    cudaDeviceProp prop;
    cudaGetDeviceProperties(&prop, device_id);
    stats.total_memory = prop.totalGlobalMem;
    
    // Calculate utilization
    stats.utilization = static_cast<double>(used_memory) / prop.totalGlobalMem;
}

void MetricsCollector::record_error(const std::string& model_name,
                                  const std::string& error_type) {
    std::lock_guard<std::mutex> lock(model_stats_mutex_);
    auto& stats = model_stats_[model_name];
    stats.error_counts[error_type]++;
}

MetricsCollector::ModelMetrics MetricsCollector::get_model_metrics(
    const std::string& model_name) const {
    std::lock_guard<std::mutex> lock(model_stats_mutex_);
    
    ModelMetrics metrics;
    auto it = model_stats_.find(model_name);
    if (it != model_stats_.end()) {
        const auto& stats = it->second;
        metrics.total_requests = stats.total_requests;
        metrics.total_input_tokens = stats.total_input_tokens;
        metrics.total_output_tokens = stats.total_output_tokens;
        
        if (stats.total_requests > 0) {
            metrics.avg_latency = static_cast<double>(stats.total_latency) / 
                                stats.total_requests;
        }
        
        // Copy error counts
        std::lock_guard<std::mutex> error_lock(stats.mutex);
        for (const auto& [error_type, count] : stats.error_counts) {
            metrics.error_counts[error_type] = count;
        }
    }
    
    return metrics;
}

MetricsCollector::GPUMetrics MetricsCollector::get_gpu_metrics(int device_id) const {
    std::lock_guard<std::mutex> lock(gpu_stats_mutex_);
    
    GPUMetrics metrics;
    auto it = gpu_stats_.find(device_id);
    if (it != gpu_stats_.end()) {
        const auto& stats = it->second;
        metrics.used_memory = stats.used_memory;
        metrics.total_memory = stats.total_memory;
        metrics.utilization = stats.utilization;
    }
    
    return metrics;
}

void MetricsCollector::reset_metrics() {
    std::lock_guard<std::mutex> model_lock(model_stats_mutex_);
    std::lock_guard<std::mutex> gpu_lock(gpu_stats_mutex_);
    
    // Reset model stats
    for (auto& [_, stats] : model_stats_) {
        stats.total_requests = 0;
        stats.total_input_tokens = 0;
        stats.total_output_tokens = 0;
        stats.total_latency = 0;
        
        std::lock_guard<std::mutex> error_lock(stats.mutex);
        for (auto& [_, count] : stats.error_counts) {
            count = 0;
        }
    }
    
    // Reset GPU stats
    for (auto& [_, stats] : gpu_stats_) {
        stats.used_memory = 0;
        stats.utilization = 0.0;
    }
}

void MetricsCollector::collect_metrics() {
    if (is_collecting_.exchange(true)) {
        return;
    }

    std::lock_guard<std::mutex> lock(mutex_);
    auto now = std::chrono::system_clock::now();

    // Check if it's time to collect metrics
    if (now - last_collection_ < collection_interval_) {
        is_collecting_ = false;
        return;
    }

    // Update all current metrics
    for (const auto& [name, enabled] : enabled_metrics_) {
        if (enabled && metric_history_.contains(name)) {
            auto& history = metric_history_[name];
            if (!history.empty()) {
                current_metrics_[name] = history.back().value;
            }
        }
    }

    // Prune old metrics
    prune_old_metrics();

    // Notify callback if set
    if (metrics_callback_) {
        notify_callback();
    }

    last_collection_ = now;
    is_collecting_ = false;
}

std::unordered_map<std::string, float> MetricsCollector::get_metrics() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return current_metrics_;
}

void MetricsCollector::set_callback(
    std::function<void(const std::unordered_map<std::string, float>&)> callback) {
    std::lock_guard<std::mutex> lock(mutex_);
    metrics_callback_ = std::move(callback);
}

void MetricsCollector::record_inference_time(const std::string& model_id, int64_t milliseconds) {
    record_metric("inference_time", static_cast<float>(milliseconds), "ms", 
                 "Inference time for model " + model_id);
}

void MetricsCollector::record_memory_usage(const std::string& model_id, size_t bytes) {
    record_metric("memory_usage", static_cast<float>(bytes), "bytes", 
                 "Memory usage for model " + model_id);
}

void MetricsCollector::record_gpu_utilization(const std::string& model_id, float utilization) {
    record_metric("gpu_utilization", utilization, "percent", 
                 "GPU utilization for model " + model_id);
}

void MetricsCollector::record_error(const std::string& error_message) {
    std::lock_guard<std::mutex> lock(mutex_);
    error_history_.push_back(error_message);
    if (error_history_.size() > 1000) {
        error_history_.erase(error_history_.begin());
    }
}

void MetricsCollector::record_latency(const std::string& operation, int64_t microseconds) {
    record_metric("latency", static_cast<float>(microseconds), "us", 
                 "Latency for operation " + operation);
}

void MetricsCollector::record_throughput(const std::string& operation, float items_per_second) {
    record_metric("throughput", items_per_second, "items/s", 
                 "Throughput for operation " + operation);
}

void MetricsCollector::record_resource_utilization(const std::string& resource, float utilization) {
    record_metric("resource_utilization", utilization, "percent", 
                 "Utilization of resource " + resource);
}

void MetricsCollector::record_queue_size(const std::string& queue, size_t size) {
    record_metric("queue_size", static_cast<float>(size), "items", 
                 "Size of queue " + queue);
}

void MetricsCollector::record_cache_hit_rate(const std::string& cache, float hit_rate) {
    record_metric("cache_hit_rate", hit_rate, "percent", 
                 "Hit rate for cache " + cache);
}

void MetricsCollector::record_batch_size(const std::string& operation, size_t batch_size) {
    record_metric("batch_size", static_cast<float>(batch_size), "items", 
                 "Batch size for operation " + operation);
}

MetricStatistics MetricsCollector::get_statistics(const std::string& metric_name) const {
    std::lock_guard<std::mutex> lock(mutex_);
    if (!metric_history_.contains(metric_name)) {
        return MetricStatistics{0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0};
    }
    return calculate_statistics(metric_history_.at(metric_name));
}

std::vector<MetricValue> MetricsCollector::get_metric_history(
    const std::string& metric_name, size_t max_points) const {
    std::lock_guard<std::mutex> lock(mutex_);
    if (!metric_history_.contains(metric_name)) {
        return {};
    }
    
    const auto& history = metric_history_.at(metric_name);
    size_t start_idx = history.size() > max_points ? history.size() - max_points : 0;
    return std::vector<MetricValue>(history.begin() + start_idx, history.end());
}

float MetricsCollector::get_current_value(const std::string& metric_name) const {
    std::lock_guard<std::mutex> lock(mutex_);
    return current_metrics_.contains(metric_name) ? current_metrics_.at(metric_name) : 0.0f;
}

std::vector<std::string> MetricsCollector::get_metric_names() const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<std::string> names;
    names.reserve(enabled_metrics_.size());
    for (const auto& [name, enabled] : enabled_metrics_) {
        if (enabled) {
            names.push_back(name);
        }
    }
    return names;
}

void MetricsCollector::reset_metrics() {
    std::lock_guard<std::mutex> lock(mutex_);
    metric_history_.clear();
    current_metrics_.clear();
    error_history_.clear();
}

void MetricsCollector::set_metric_threshold(const std::string& metric_name, float threshold) {
    std::lock_guard<std::mutex> lock(mutex_);
    metric_thresholds_[metric_name] = threshold;
}

void MetricsCollector::set_metric_window_size(const std::string& metric_name, size_t window_size) {
    std::lock_guard<std::mutex> lock(mutex_);
    metric_window_sizes_[metric_name] = window_size;
}

void MetricsCollector::enable_metric(const std::string& metric_name) {
    std::lock_guard<std::mutex> lock(mutex_);
    enabled_metrics_[metric_name] = true;
}

void MetricsCollector::disable_metric(const std::string& metric_name) {
    std::lock_guard<std::mutex> lock(mutex_);
    enabled_metrics_[metric_name] = false;
}

void MetricsCollector::update_statistics(const std::string& metric_name, float value) {
    if (!enabled_metrics_[metric_name]) {
        return;
    }

    auto& history = metric_history_[metric_name];
    history.push_back({value, std::chrono::system_clock::now(), "", ""});

    // Apply window size limit
    size_t window_size = metric_window_sizes_.contains(metric_name) ? 
                        metric_window_sizes_[metric_name] : default_window_size_;
    while (history.size() > window_size) {
        history.pop_front();
    }

    // Update current value
    current_metrics_[metric_name] = value;

    // Check thresholds
    check_thresholds(metric_name, value);
}

void MetricsCollector::check_thresholds(const std::string& metric_name, float value) {
    if (metric_thresholds_.contains(metric_name)) {
        float threshold = metric_thresholds_[metric_name];
        if (value > threshold) {
            spdlog::warn("Metric {} exceeded threshold: {} > {}", 
                        metric_name, value, threshold);
        }
    }
}

void MetricsCollector::prune_old_metrics() {
    auto now = std::chrono::system_clock::now();
    auto max_age = std::chrono::hours(24);

    for (auto& [name, history] : metric_history_) {
        while (!history.empty() && 
               (now - history.front().timestamp) > max_age) {
            history.pop_front();
        }
    }
}

MetricStatistics MetricsCollector::calculate_statistics(
    const std::deque<MetricValue>& values) const {
    if (values.empty()) {
        return MetricStatistics{0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0};
    }

    std::vector<float> sorted_values;
    sorted_values.reserve(values.size());
    for (const auto& value : values) {
        sorted_values.push_back(value.value);
    }
    std::sort(sorted_values.begin(), sorted_values.end());

    float min = sorted_values.front();
    float max = sorted_values.back();
    float sum = std::accumulate(sorted_values.begin(), sorted_values.end(), 0.0f);
    float mean = sum / sorted_values.size();

    float variance = 0.0f;
    for (float value : sorted_values) {
        float diff = value - mean;
        variance += diff * diff;
    }
    variance /= sorted_values.size();
    float std_dev = std::sqrt(variance);

    size_t p95_idx = static_cast<size_t>(sorted_values.size() * 0.95);
    size_t p99_idx = static_cast<size_t>(sorted_values.size() * 0.99);
    float p95 = sorted_values[p95_idx];
    float p99 = sorted_values[p99_idx];

    return MetricStatistics{min, max, mean, std_dev, p95, p99, sorted_values.size()};
}

void MetricsCollector::notify_callback() {
    if (metrics_callback_) {
        metrics_callback_(current_metrics_);
    }
}

} // namespace monitoring
} // namespace cogniware 