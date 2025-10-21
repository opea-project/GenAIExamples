#pragma once

#include <string>
#include <vector>
#include <memory>
#include <unordered_map>
#include <chrono>

namespace cogniware {
namespace monitoring {

struct Metric {
    std::string name;
    double value;
    std::chrono::system_clock::time_point timestamp;
    std::unordered_map<std::string, std::string> labels;
};

struct Alert {
    std::string name;
    std::string description;
    std::string severity;
    bool triggered;
    std::chrono::system_clock::time_point triggered_at;
};

class MonitoringSystem {
public:
    MonitoringSystem();
    ~MonitoringSystem();

    void recordMetric(const std::string& name, double value,
                     const std::unordered_map<std::string, std::string>& labels = {});
    
    std::vector<Metric> queryMetrics(const std::string& name,
                                    std::chrono::system_clock::time_point since = {},
                                    size_t limit = 1000);
    
    std::string createAlert(const std::string& name, const std::string& condition);
    std::vector<Alert> listAlerts();
    
    void start();
    void stop();

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

} // namespace monitoring
} // namespace cogniware

