#pragma once

#include <string>
#include <unordered_map>
#include <vector>
#include <chrono>
#include <functional>
#include <mutex>
#include <atomic>
#include <deque>

namespace cogniware {
namespace monitoring {

struct MetricValue {
    float value;
    std::chrono::system_clock::time_point timestamp;
    std::string unit;
    std::string description;
};

struct MetricStatistics {
    float min;
    float max;
    float mean;
    float std_dev;
    float p95;
    float p99;
    size_t count;
};

class MetricsCollector {
public:
    MetricsCollector();
    ~MetricsCollector() = default;

    // Metric collection
    void collect_metrics();
    std::unordered_map<std::string, float> get_metrics() const;
    void set_callback(std::function<void(const std::unordered_map<std::string, float>&)> callback);

    // Metric recording
    void record_inference_time(const std::string& model_id, int64_t milliseconds);
    void record_memory_usage(const std::string& model_id, size_t bytes);
    void record_gpu_utilization(const std::string& model_id, float utilization);
    void record_error(const std::string& error_message);
    void record_latency(const std::string& operation, int64_t microseconds);
    void record_throughput(const std::string& operation, float items_per_second);
    void record_resource_utilization(const std::string& resource, float utilization);
    void record_queue_size(const std::string& queue, size_t size);
    void record_cache_hit_rate(const std::string& cache, float hit_rate);
    void record_batch_size(const std::string& operation, size_t batch_size);

    // Metric retrieval
    MetricStatistics get_statistics(const std::string& metric_name) const;
    std::vector<MetricValue> get_metric_history(const std::string& metric_name, 
                                              size_t max_points = 1000) const;
    float get_current_value(const std::string& metric_name) const;
    std::vector<std::string> get_metric_names() const;

    // Metric management
    void reset_metrics();
    void set_metric_threshold(const std::string& metric_name, float threshold);
    void set_metric_window_size(const std::string& metric_name, size_t window_size);
    void enable_metric(const std::string& metric_name);
    void disable_metric(const std::string& metric_name);

private:
    // Metric storage
    std::unordered_map<std::string, std::deque<MetricValue>> metric_history_;
    std::unordered_map<std::string, float> current_metrics_;
    std::unordered_map<std::string, float> metric_thresholds_;
    std::unordered_map<std::string, size_t> metric_window_sizes_;
    std::unordered_map<std::string, bool> enabled_metrics_;
    std::vector<std::string> error_history_;

    // Configuration
    std::function<void(const std::unordered_map<std::string, float>&)> metrics_callback_;
    size_t default_window_size_ = 1000;
    std::chrono::seconds collection_interval_ = std::chrono::seconds(1);
    std::chrono::system_clock::time_point last_collection_;

    // Thread safety
    mutable std::mutex mutex_;
    std::atomic<bool> is_collecting_;

    // Helper functions
    void update_statistics(const std::string& metric_name, float value);
    void check_thresholds(const std::string& metric_name, float value);
    void prune_old_metrics();
    MetricStatistics calculate_statistics(const std::deque<MetricValue>& values) const;
    void notify_callback();
};

} // namespace monitoring
} // namespace cogniware 