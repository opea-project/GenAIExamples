#include <gtest/gtest.h>
#include "llm_inference_core/monitoring/resource_monitor.h"

using namespace cogniware;

class ResourceMonitorTest : public ::testing::Test {
protected:
    void SetUp() override {
        monitor = &ResourceMonitor::getInstance();
    }

    void TearDown() override {
        monitor->stopMonitoring();
    }

    ResourceMonitor* monitor;
};

TEST_F(ResourceMonitorTest, Initialization) {
    EXPECT_TRUE(monitor->startMonitoring());
    EXPECT_TRUE(monitor->isMonitoring());
}

TEST_F(ResourceMonitorTest, GPUStats) {
    ASSERT_TRUE(monitor->startMonitoring());

    auto stats = monitor->getGPUStats();
    EXPECT_GE(stats.totalMemory, 0);
    EXPECT_GE(stats.freeMemory, 0);
    EXPECT_GE(stats.usedMemory, 0);
    EXPECT_GE(stats.utilization, 0.0f);
    EXPECT_GE(stats.temperature, 0.0f);
}

TEST_F(ResourceMonitorTest, ModelStats) {
    ASSERT_TRUE(monitor->startMonitoring());

    // Test statistics for non-existent model
    auto stats = monitor->getModelStats("nonexistent-model");
    EXPECT_EQ(stats.memoryUsage, 0);
    EXPECT_EQ(stats.computeTime, 0);
    EXPECT_EQ(stats.requestCount, 0);
    EXPECT_FLOAT_EQ(stats.averageLatency, 0.0f);
}

TEST_F(ResourceMonitorTest, ResourceLimits) {
    ASSERT_TRUE(monitor->startMonitoring());

    // Set resource limits
    monitor->setMaxVRAMUsage(1024 * 1024 * 1024);  // 1GB
    monitor->setMaxGPUUtilization(80.0f);  // 80%

    // Get current stats
    auto stats = monitor->getGPUStats();
    EXPECT_GE(stats.usedMemory, 0);
    EXPECT_GE(stats.utilization, 0.0f);
}

TEST_F(ResourceMonitorTest, ResourceAlerts) {
    ASSERT_TRUE(monitor->startMonitoring());

    bool alertReceived = false;
    monitor->setResourceAlertCallback(
        [&alertReceived](const std::string& resource, const std::string& message) {
            alertReceived = true;
        }
    );

    // TODO: Trigger a resource alert and verify callback
    EXPECT_FALSE(alertReceived);
}

TEST_F(ResourceMonitorTest, MultipleInitialization) {
    EXPECT_TRUE(monitor->startMonitoring());
    EXPECT_TRUE(monitor->startMonitoring());  // Should be idempotent
}

TEST_F(ResourceMonitorTest, StopMonitoring) {
    ASSERT_TRUE(monitor->startMonitoring());
    monitor->stopMonitoring();
    EXPECT_FALSE(monitor->isMonitoring());
}

TEST_F(ResourceMonitorTest, ModelStatsUpdate) {
    ASSERT_TRUE(monitor->startMonitoring());

    // Update statistics for a model
    monitor->updateModelStats("test-model", 1024, 100, 0.5f);

    auto stats = monitor->getModelStats("test-model");
    EXPECT_EQ(stats.memoryUsage, 1024);
    EXPECT_EQ(stats.computeTime, 100);
    EXPECT_EQ(stats.requestCount, 1);
    EXPECT_FLOAT_EQ(stats.averageLatency, 0.5f);

    // Update again
    monitor->updateModelStats("test-model", 2048, 200, 0.6f);

    stats = monitor->getModelStats("test-model");
    EXPECT_EQ(stats.memoryUsage, 2048);
    EXPECT_EQ(stats.computeTime, 300);
    EXPECT_EQ(stats.requestCount, 2);
    EXPECT_GT(stats.averageLatency, 0.5f);  // Should be updated with new average
}

TEST_F(ResourceMonitorTest, ErrorHandling) {
    ASSERT_TRUE(monitor->startMonitoring());

    // Test with invalid model ID
    auto stats = monitor->getModelStats("");
    EXPECT_EQ(stats.memoryUsage, 0);
    EXPECT_EQ(stats.computeTime, 0);
    EXPECT_EQ(stats.requestCount, 0);
    EXPECT_FLOAT_EQ(stats.averageLatency, 0.0f);

    // Test with invalid resource limits
    monitor->setMaxVRAMUsage(0);
    monitor->setMaxGPUUtilization(-1.0f);

    auto gpuStats = monitor->getGPUStats();
    EXPECT_GE(gpuStats.usedMemory, 0);
    EXPECT_GE(gpuStats.utilization, 0.0f);
}

TEST_F(ResourceMonitorTest, ResourceMonitoring) {
    ASSERT_TRUE(monitor->startMonitoring());

    // Get initial stats
    auto initialStats = monitor->getGPUStats();

    // Wait a bit
    std::this_thread::sleep_for(std::chrono::milliseconds(100));

    // Get updated stats
    auto updatedStats = monitor->getGPUStats();

    // Stats should be updated
    EXPECT_NE(initialStats.usedMemory, updatedStats.usedMemory);
    EXPECT_NE(initialStats.utilization, updatedStats.utilization);
}

TEST_F(ResourceMonitorTest, ResourceAlertCallback) {
    ASSERT_TRUE(monitor->startMonitoring());

    std::string lastResource;
    std::string lastMessage;

    monitor->setResourceAlertCallback(
        [&lastResource, &lastMessage](const std::string& resource, const std::string& message) {
            lastResource = resource;
            lastMessage = message;
        }
    );

    // TODO: Trigger a resource alert and verify callback parameters
    EXPECT_TRUE(lastResource.empty());
    EXPECT_TRUE(lastMessage.empty());
}

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
} 