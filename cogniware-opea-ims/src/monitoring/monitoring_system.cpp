#include "monitoring/monitoring_system.h"
#include <mutex>
#include <thread>

namespace cogniware {
namespace monitoring {

class MonitoringSystem::Impl {
public:
    std::vector<Metric> metrics;
    std::vector<Alert> alerts;
    mutable std::mutex mutex;
    bool running = false;
};

MonitoringSystem::MonitoringSystem() : pImpl(std::make_unique<Impl>()) {}
MonitoringSystem::~MonitoringSystem() { stop(); }

void MonitoringSystem::recordMetric(const std::string& name, double value,
                                   const std::unordered_map<std::string, std::string>& labels) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    Metric m{name, value, std::chrono::system_clock::now(), labels};
    pImpl->metrics.push_back(m);
}

std::vector<Metric> MonitoringSystem::queryMetrics(const std::string& name,
                                                   std::chrono::system_clock::time_point since,
                                                   size_t limit) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    std::vector<Metric> result;
    for (const auto& m : pImpl->metrics) {
        if ((name.empty() || m.name == name) && 
            (since == std::chrono::system_clock::time_point{} || m.timestamp >= since)) {
            result.push_back(m);
            if (result.size() >= limit) break;
        }
    }
    return result;
}

std::string MonitoringSystem::createAlert(const std::string& name, const std::string& condition) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    Alert a{name, condition, "info", false, {}};
    pImpl->alerts.push_back(a);
    return name;
}

std::vector<Alert> MonitoringSystem::listAlerts() {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    return pImpl->alerts;
}

void MonitoringSystem::start() { pImpl->running = true; }
void MonitoringSystem::stop() { pImpl->running = false; }

} // namespace monitoring
} // namespace cogniware

