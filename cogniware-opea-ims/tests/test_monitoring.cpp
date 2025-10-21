#include <gtest/gtest.h>
#include "monitoring/monitoring_manager.h"
#include <thread>
#include <chrono>
#include <fstream>
#include <filesystem>

using namespace cogniware::monitoring;

class MonitoringTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Create a temporary config file
        config_path_ = std::filesystem::temp_directory_path() / "monitoring_test_config.json";
        std::ofstream config_file(config_path_);
        config_file << R"({
            "collection_interval": 1,
            "alert_thresholds": {
                "test_metric": {
                    "value": 100.0,
                    "severity": "warning"
                }
            }
        })";
        config_file.close();

        // Initialize monitoring manager
        MonitoringManager::get_instance().initialize(config_path_.string());
    }

    void TearDown() override {
        // Clean up
        MonitoringManager::get_instance().shutdown();
        std::filesystem::remove(config_path_);
    }

    std::filesystem::path config_path_;
};

TEST_F(MonitoringTest, MetricCollection) {
    auto& manager = MonitoringManager::get_instance();
    
    // Start collection
    manager.start_collection();
    
    // Record some metrics
    std::unordered_map<std::string, float> model_metrics = {
        {"inference_time", 50.0f},
        {"memory_usage", 1024.0f}
    };
    manager.record_model_metrics("test_model", model_metrics);
    
    // Wait for collection
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    
    // Check metrics
    auto metrics = manager.get_current_metrics();
    EXPECT_TRUE(metrics.contains("model.test_model.inference_time"));
    EXPECT_TRUE(metrics.contains("model.test_model.memory_usage"));
    EXPECT_FLOAT_EQ(metrics["model.test_model.inference_time"], 50.0f);
    EXPECT_FLOAT_EQ(metrics["model.test_model.memory_usage"], 1024.0f);
}

TEST_F(MonitoringTest, AlertThresholds) {
    auto& manager = MonitoringManager::get_instance();
    manager.start_collection();
    
    // Record metric below threshold
    std::unordered_map<std::string, float> metrics = {{"test_metric", 50.0f}};
    manager.record_system_metrics(metrics);
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    
    // Check no alerts
    EXPECT_TRUE(manager.get_active_alerts().empty());
    
    // Record metric above threshold
    metrics["test_metric"] = 150.0f;
    manager.record_system_metrics(metrics);
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    
    // Check alert generated
    auto alerts = manager.get_active_alerts();
    EXPECT_FALSE(alerts.empty());
    EXPECT_EQ(alerts[0].metric_name, "system.test_metric");
    EXPECT_EQ(alerts[0].severity, "warning");
}

TEST_F(MonitoringTest, MetricHistory) {
    auto& manager = MonitoringManager::get_instance();
    manager.start_collection();
    
    // Record multiple values
    for (int i = 0; i < 5; ++i) {
        std::unordered_map<std::string, float> metrics = {
            {"test_metric", static_cast<float>(i * 10)}
        };
        manager.record_system_metrics(metrics);
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
    
    // Get history
    auto history = manager.get_metric_history("system.test_metric");
    EXPECT_EQ(history.size(), 5);
    
    // Check values
    for (size_t i = 0; i < history.size(); ++i) {
        EXPECT_FLOAT_EQ(history[i].value, i * 10.0f);
    }
}

TEST_F(MonitoringTest, MetricStatistics) {
    auto& manager = MonitoringManager::get_instance();
    manager.start_collection();
    
    // Record values
    std::vector<float> values = {10.0f, 20.0f, 30.0f, 40.0f, 50.0f};
    for (float value : values) {
        std::unordered_map<std::string, float> metrics = {{"test_metric", value}};
        manager.record_system_metrics(metrics);
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
    
    // Get statistics
    auto stats = manager.get_metric_statistics("system.test_metric");
    EXPECT_FLOAT_EQ(stats.min, 10.0f);
    EXPECT_FLOAT_EQ(stats.max, 50.0f);
    EXPECT_FLOAT_EQ(stats.mean, 30.0f);
    EXPECT_EQ(stats.count, 5);
}

TEST_F(MonitoringTest, EventRecording) {
    auto& manager = MonitoringManager::get_instance();
    
    // Record events
    manager.record_event("test_event", "Test event description");
    manager.record_error("test_component", "Test error message");
    
    // Generate report
    std::string report_path = std::filesystem::temp_directory_path() / "test_report.txt";
    manager.generate_report("summary", report_path.string());
    
    // Check report file exists
    EXPECT_TRUE(std::filesystem::exists(report_path));
    
    // Clean up
    std::filesystem::remove(report_path);
}

TEST_F(MonitoringTest, MetricExport) {
    auto& manager = MonitoringManager::get_instance();
    manager.start_collection();
    
    // Record metrics
    std::unordered_map<std::string, float> metrics = {
        {"test_metric1", 100.0f},
        {"test_metric2", 200.0f}
    };
    manager.record_system_metrics(metrics);
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    
    // Export to JSON
    std::string json_path = std::filesystem::temp_directory_path() / "test_metrics.json";
    manager.export_metrics("json", json_path.string());
    EXPECT_TRUE(std::filesystem::exists(json_path));
    
    // Export to CSV
    std::string csv_path = std::filesystem::temp_directory_path() / "test_metrics.csv";
    manager.export_metrics("csv", csv_path.string());
    EXPECT_TRUE(std::filesystem::exists(csv_path));
    
    // Clean up
    std::filesystem::remove(json_path);
    std::filesystem::remove(csv_path);
}

TEST_F(MonitoringTest, ConfigurationManagement) {
    auto& manager = MonitoringManager::get_instance();
    
    // Configure new settings
    std::unordered_map<std::string, std::string> config = {
        {"collection_interval", "2"}
    };
    manager.configure(config);
    
    // Save configuration
    std::string new_config_path = std::filesystem::temp_directory_path() / "new_config.json";
    manager.save_configuration(new_config_path.string());
    
    // Check new config file exists
    EXPECT_TRUE(std::filesystem::exists(new_config_path));
    
    // Clean up
    std::filesystem::remove(new_config_path);
}

TEST_F(MonitoringTest, AlertManagement) {
    auto& manager = MonitoringManager::get_instance();
    manager.start_collection();
    
    // Set alert threshold
    manager.set_alert_threshold("test_metric", 100.0f, "critical");
    
    // Record metric above threshold
    std::unordered_map<std::string, float> metrics = {{"test_metric", 150.0f}};
    manager.record_system_metrics(metrics);
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    
    // Check alert
    auto alerts = manager.get_active_alerts();
    EXPECT_FALSE(alerts.empty());
    EXPECT_EQ(alerts[0].severity, "critical");
    
    // Acknowledge alert
    manager.acknowledge_alert(alerts[0].id);
    EXPECT_TRUE(manager.get_active_alerts().empty());
    
    // Clear threshold
    manager.clear_alert_threshold("test_metric");
    metrics["test_metric"] = 200.0f;
    manager.record_system_metrics(metrics);
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    EXPECT_TRUE(manager.get_active_alerts().empty());
}

TEST_F(MonitoringTest, MetricCleanup) {
    auto& manager = MonitoringManager::get_instance();
    manager.start_collection();
    
    // Record metrics
    for (int i = 0; i < 10; ++i) {
        std::unordered_map<std::string, float> metrics = {
            {"test_metric", static_cast<float>(i)}
        };
        manager.record_system_metrics(metrics);
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
    
    // Get history with limited points
    auto history = manager.get_metric_history("system.test_metric", 5);
    EXPECT_EQ(history.size(), 5);
    
    // Check most recent values
    for (size_t i = 0; i < history.size(); ++i) {
        EXPECT_FLOAT_EQ(history[i].value, (i + 5) * 1.0f);
    }
}

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
} 