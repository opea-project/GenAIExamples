#pragma once

#include "monitoring/metrics_collector.h"
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>
#include <functional>
#include <chrono>
#include <thread>
#include <atomic>

namespace cogniware {
namespace monitoring {

class MonitoringManager {
public:
    static MonitoringManager& get_instance() {
        static MonitoringManager instance;
        return instance;
    }

    ~MonitoringManager();

    // Initialization and configuration
    void initialize(const std::string& config_path);
    void configure(const std::unordered_map<std::string, std::string>& config);
    void shutdown();

    // Metric collection control
    void start_collection();
    void stop_collection();
    void set_collection_interval(std::chrono::seconds interval);

    // Metric recording
    void record_model_metrics(const std::string& model_id,
                            const std::unordered_map<std::string, float>& metrics);
    void record_system_metrics(const std::unordered_map<std::string, float>& metrics);
    void record_error(const std::string& component, const std::string& error_message);
    void record_event(const std::string& event_type, const std::string& description);

    // Metric retrieval
    std::unordered_map<std::string, float> get_current_metrics() const;
    std::vector<MetricValue> get_metric_history(const std::string& metric_name,
                                              size_t max_points = 1000) const;
    MetricStatistics get_metric_statistics(const std::string& metric_name) const;
    std::vector<std::string> get_available_metrics() const;

    // Alert management
    struct Alert {
        std::string id;
        std::string metric_name;
        std::string message;
        std::string severity;
        std::chrono::system_clock::time_point timestamp;
    };

    void set_alert_threshold(const std::string& metric_name, float threshold,
                            const std::string& severity = "warning");
    void clear_alert_threshold(const std::string& metric_name);
    std::vector<Alert> get_active_alerts() const;
    void acknowledge_alert(const std::string& alert_id);

    // Export and reporting
    void export_metrics(const std::string& format, const std::string& output_path);
    void generate_report(const std::string& report_type, const std::string& output_path);

private:
    MonitoringManager();
    MonitoringManager(const MonitoringManager&) = delete;
    MonitoringManager& operator=(const MonitoringManager&) = delete;

    // Internal components
    std::unique_ptr<MetricsCollector> metrics_collector_;
    std::thread collection_thread_;
    std::atomic<bool> is_running_;
    std::chrono::seconds collection_interval_;

    // Alert management
    struct AlertThreshold {
        float value;
        std::string severity;
    };
    std::unordered_map<std::string, AlertThreshold> alert_thresholds_;
    std::vector<Alert> active_alerts_;
    mutable std::mutex alerts_mutex_;

    // Event history
    struct Event {
        std::string type;
        std::string description;
        std::chrono::system_clock::time_point timestamp;
    };
    std::vector<Event> event_history_;
    mutable std::mutex events_mutex_;

    // Helper functions
    void collection_loop();
    void check_alert_thresholds();
    void process_metrics();
    void cleanup_old_data();
    void load_configuration(const std::string& config_path);
    void save_configuration(const std::string& config_path);
};

} // namespace monitoring
} // namespace cogniware 