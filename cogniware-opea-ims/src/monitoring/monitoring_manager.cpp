#include "monitoring/monitoring_manager.h"
#include <spdlog/spdlog.h>
#include <fstream>
#include <json/json.h>
#include <uuid/uuid.h>
#include <sstream>
#include <iomanip>
#include <ctime>

namespace cogniware {
namespace monitoring {

MonitoringManager::MonitoringManager()
    : metrics_collector_(std::make_unique<MetricsCollector>())
    , is_running_(false)
    , collection_interval_(std::chrono::seconds(1)) {
}

MonitoringManager::~MonitoringManager() {
    shutdown();
}

void MonitoringManager::initialize(const std::string& config_path) {
    try {
        load_configuration(config_path);
        spdlog::info("MonitoringManager initialized with config: {}", config_path);
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize MonitoringManager: {}", e.what());
        throw;
    }
}

void MonitoringManager::configure(const std::unordered_map<std::string, std::string>& config) {
    try {
        if (config.contains("collection_interval")) {
            collection_interval_ = std::chrono::seconds(
                std::stoi(config.at("collection_interval")));
        }
        spdlog::info("MonitoringManager configured with new settings");
    } catch (const std::exception& e) {
        spdlog::error("Failed to configure MonitoringManager: {}", e.what());
        throw;
    }
}

void MonitoringManager::shutdown() {
    stop_collection();
    if (collection_thread_.joinable()) {
        collection_thread_.join();
    }
    spdlog::info("MonitoringManager shut down");
}

void MonitoringManager::start_collection() {
    if (is_running_.exchange(true)) {
        return;
    }

    collection_thread_ = std::thread([this]() {
        collection_loop();
    });
    spdlog::info("Metric collection started");
}

void MonitoringManager::stop_collection() {
    is_running_ = false;
    spdlog::info("Metric collection stopped");
}

void MonitoringManager::set_collection_interval(std::chrono::seconds interval) {
    collection_interval_ = interval;
    spdlog::info("Collection interval set to {} seconds", interval.count());
}

void MonitoringManager::record_model_metrics(
    const std::string& model_id,
    const std::unordered_map<std::string, float>& metrics) {
    for (const auto& [name, value] : metrics) {
        std::string metric_name = "model." + model_id + "." + name;
        metrics_collector_->record_metric(metric_name, value, "", "");
    }
}

void MonitoringManager::record_system_metrics(
    const std::unordered_map<std::string, float>& metrics) {
    for (const auto& [name, value] : metrics) {
        std::string metric_name = "system." + name;
        metrics_collector_->record_metric(metric_name, value, "", "");
    }
}

void MonitoringManager::record_error(const std::string& component,
                                   const std::string& error_message) {
    std::string full_message = component + ": " + error_message;
    metrics_collector_->record_error(full_message);
    
    std::lock_guard<std::mutex> lock(events_mutex_);
    event_history_.push_back({
        "error",
        full_message,
        std::chrono::system_clock::now()
    });
}

void MonitoringManager::record_event(const std::string& event_type,
                                   const std::string& description) {
    std::lock_guard<std::mutex> lock(events_mutex_);
    event_history_.push_back({
        event_type,
        description,
        std::chrono::system_clock::now()
    });
}

std::unordered_map<std::string, float> MonitoringManager::get_current_metrics() const {
    return metrics_collector_->get_metrics();
}

std::vector<MetricValue> MonitoringManager::get_metric_history(
    const std::string& metric_name, size_t max_points) const {
    return metrics_collector_->get_metric_history(metric_name, max_points);
}

MetricStatistics MonitoringManager::get_metric_statistics(
    const std::string& metric_name) const {
    return metrics_collector_->get_statistics(metric_name);
}

std::vector<std::string> MonitoringManager::get_available_metrics() const {
    return metrics_collector_->get_metric_names();
}

void MonitoringManager::set_alert_threshold(const std::string& metric_name,
                                          float threshold,
                                          const std::string& severity) {
    std::lock_guard<std::mutex> lock(alerts_mutex_);
    alert_thresholds_[metric_name] = {threshold, severity};
    spdlog::info("Alert threshold set for {}: {} ({})", 
                metric_name, threshold, severity);
}

void MonitoringManager::clear_alert_threshold(const std::string& metric_name) {
    std::lock_guard<std::mutex> lock(alerts_mutex_);
    alert_thresholds_.erase(metric_name);
    spdlog::info("Alert threshold cleared for {}", metric_name);
}

std::vector<MonitoringManager::Alert> MonitoringManager::get_active_alerts() const {
    std::lock_guard<std::mutex> lock(alerts_mutex_);
    return active_alerts_;
}

void MonitoringManager::acknowledge_alert(const std::string& alert_id) {
    std::lock_guard<std::mutex> lock(alerts_mutex_);
    active_alerts_.erase(
        std::remove_if(active_alerts_.begin(), active_alerts_.end(),
                      [&](const Alert& alert) { return alert.id == alert_id; }),
        active_alerts_.end());
}

void MonitoringManager::export_metrics(const std::string& format,
                                     const std::string& output_path) {
    try {
        std::ofstream out(output_path);
        if (!out) {
            throw std::runtime_error("Failed to open output file: " + output_path);
        }

        if (format == "json") {
            Json::Value root;
            auto metrics = get_current_metrics();
            for (const auto& [name, value] : metrics) {
                root[name] = value;
            }
            out << root.toStyledString();
        } else if (format == "csv") {
            auto metrics = get_current_metrics();
            out << "metric_name,value,timestamp\n";
            auto now = std::chrono::system_clock::now();
            for (const auto& [name, value] : metrics) {
                out << name << "," << value << ","
                    << std::chrono::duration_cast<std::chrono::seconds>(
                           now.time_since_epoch()).count() << "\n";
            }
        } else {
            throw std::runtime_error("Unsupported export format: " + format);
        }
        spdlog::info("Metrics exported to {} in {} format", output_path, format);
    } catch (const std::exception& e) {
        spdlog::error("Failed to export metrics: {}", e.what());
        throw;
    }
}

void MonitoringManager::generate_report(const std::string& report_type,
                                      const std::string& output_path) {
    try {
        std::ofstream out(output_path);
        if (!out) {
            throw std::runtime_error("Failed to open output file: " + output_path);
        }

        if (report_type == "summary") {
            out << "Monitoring Report - " << std::put_time(
                std::localtime(&std::time(nullptr)), "%Y-%m-%d %H:%M:%S") << "\n\n";
            
            // Current metrics
            out << "Current Metrics:\n";
            auto metrics = get_current_metrics();
            for (const auto& [name, value] : metrics) {
                out << name << ": " << value << "\n";
            }
            out << "\n";

            // Active alerts
            out << "Active Alerts:\n";
            auto alerts = get_active_alerts();
            for (const auto& alert : alerts) {
                out << alert.id << " - " << alert.message << " (" << alert.severity << ")\n";
            }
            out << "\n";

            // Recent events
            out << "Recent Events:\n";
            std::lock_guard<std::mutex> lock(events_mutex_);
            for (auto it = event_history_.rbegin(); 
                 it != event_history_.rend() && std::distance(event_history_.rbegin(), it) < 10; 
                 ++it) {
                out << it->type << ": " << it->description << "\n";
            }
        } else {
            throw std::runtime_error("Unsupported report type: " + report_type);
        }
        spdlog::info("Report generated: {} ({})", output_path, report_type);
    } catch (const std::exception& e) {
        spdlog::error("Failed to generate report: {}", e.what());
        throw;
    }
}

void MonitoringManager::collection_loop() {
    while (is_running_) {
        try {
            metrics_collector_->collect_metrics();
            check_alert_thresholds();
            process_metrics();
            cleanup_old_data();
        } catch (const std::exception& e) {
            spdlog::error("Error in collection loop: {}", e.what());
        }
        std::this_thread::sleep_for(collection_interval_);
    }
}

void MonitoringManager::check_alert_thresholds() {
    std::lock_guard<std::mutex> lock(alerts_mutex_);
    auto metrics = get_current_metrics();

    for (const auto& [metric_name, threshold] : alert_thresholds_) {
        if (metrics.contains(metric_name)) {
            float value = metrics[metric_name];
            if (value > threshold.value) {
                // Generate unique alert ID
                uuid_t uuid;
                uuid_generate(uuid);
                char uuid_str[37];
                uuid_unparse_lower(uuid, uuid_str);

                Alert alert{
                    uuid_str,
                    metric_name,
                    "Metric " + metric_name + " exceeded threshold: " +
                        std::to_string(value) + " > " + std::to_string(threshold.value),
                    threshold.severity,
                    std::chrono::system_clock::now()
                };

                // Check if similar alert already exists
                auto it = std::find_if(active_alerts_.begin(), active_alerts_.end(),
                    [&](const Alert& a) {
                        return a.metric_name == metric_name && a.severity == threshold.severity;
                    });

                if (it == active_alerts_.end()) {
                    active_alerts_.push_back(alert);
                    spdlog::warn("Alert generated: {}", alert.message);
                }
            }
        }
    }
}

void MonitoringManager::process_metrics() {
    // Process and aggregate metrics as needed
    auto metrics = get_current_metrics();
    for (const auto& [name, value] : metrics) {
        // Add any metric processing logic here
    }
}

void MonitoringManager::cleanup_old_data() {
    // Clean up old events
    std::lock_guard<std::mutex> lock(events_mutex_);
    auto now = std::chrono::system_clock::now();
    auto max_age = std::chrono::hours(24);
    
    event_history_.erase(
        std::remove_if(event_history_.begin(), event_history_.end(),
            [&](const Event& event) {
                return (now - event.timestamp) > max_age;
            }),
        event_history_.end());

    // Clean up old alerts
    std::lock_guard<std::mutex> alert_lock(alerts_mutex_);
    active_alerts_.erase(
        std::remove_if(active_alerts_.begin(), active_alerts_.end(),
            [&](const Alert& alert) {
                return (now - alert.timestamp) > max_age;
            }),
        active_alerts_.end());
}

void MonitoringManager::load_configuration(const std::string& config_path) {
    try {
        std::ifstream file(config_path);
        if (!file) {
            throw std::runtime_error("Failed to open config file: " + config_path);
        }

        Json::Value root;
        Json::CharReaderBuilder builder;
        std::string errors;
        if (!Json::parseFromStream(builder, file, &root, &errors)) {
            throw std::runtime_error("Failed to parse config file: " + errors);
        }

        // Load collection interval
        if (root.isMember("collection_interval")) {
            collection_interval_ = std::chrono::seconds(
                root["collection_interval"].asInt());
        }

        // Load alert thresholds
        if (root.isMember("alert_thresholds")) {
            const Json::Value& thresholds = root["alert_thresholds"];
            for (const auto& name : thresholds.getMemberNames()) {
                const Json::Value& threshold = thresholds[name];
                alert_thresholds_[name] = {
                    threshold["value"].asFloat(),
                    threshold["severity"].asString()
                };
            }
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to load configuration: {}", e.what());
        throw;
    }
}

void MonitoringManager::save_configuration(const std::string& config_path) {
    try {
        Json::Value root;
        root["collection_interval"] = collection_interval_.count();

        Json::Value thresholds;
        std::lock_guard<std::mutex> lock(alerts_mutex_);
        for (const auto& [name, threshold] : alert_thresholds_) {
            Json::Value threshold_obj;
            threshold_obj["value"] = threshold.value;
            threshold_obj["severity"] = threshold.severity;
            thresholds[name] = threshold_obj;
        }
        root["alert_thresholds"] = thresholds;

        std::ofstream file(config_path);
        if (!file) {
            throw std::runtime_error("Failed to open config file for writing: " + config_path);
        }

        Json::StreamWriterBuilder writer;
        file << Json::writeString(writer, root);
    } catch (const std::exception& e) {
        spdlog::error("Failed to save configuration: {}", e.what());
        throw;
    }
}

} // namespace monitoring
} // namespace cogniware 