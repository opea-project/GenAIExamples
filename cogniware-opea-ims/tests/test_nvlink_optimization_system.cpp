#include <gtest/gtest.h>
#include <spdlog/spdlog.h>
#include "nvlink/nvlink_optimization.h"
#include <chrono>
#include <thread>

using namespace cogniware::nvlink;

class NVLinkOptimizationSystemTest : public ::testing::Test {
protected:
    void SetUp() override {
        spdlog::set_level(spdlog::level::debug);
        
        // Initialize the global system
        auto& system = GlobalNVLinkOptimizationSystem::getInstance();
        ASSERT_TRUE(system.initialize()) << "Failed to initialize global NVLink optimization system";
    }
    
    void TearDown() override {
        // Shutdown the global system
        auto& system = GlobalNVLinkOptimizationSystem::getInstance();
        system.shutdown();
    }
};

TEST_F(NVLinkOptimizationSystemTest, TestSystemInitialization) {
    auto& system = GlobalNVLinkOptimizationSystem::getInstance();
    
    EXPECT_TRUE(system.isInitialized()) << "System should be initialized";
    
    // Test component access
    auto topologyManager = system.getTopologyManager();
    EXPECT_NE(topologyManager, nullptr) << "Topology manager should not be null";
}

TEST_F(NVLinkOptimizationSystemTest, TestOptimizerCreation) {
    auto& system = GlobalNVLinkOptimizationSystem::getInstance();
    
    // Create NVLink optimizer configuration
    NVLinkConfig config;
    config.linkId = "nvlink_1";
    config.sourceGPU = 0;
    config.destinationGPU = 1;
    config.linkWidth = 4;
    config.linkSpeed = 25.0f; // 25 GB/s
    config.bandwidth = 25.0f;
    config.latency = 100.0f; // 100 ns
    config.isActive = true;
    config.topology = NVLinkTopology::RING;
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    // Create optimizer
    auto optimizer = system.createOptimizer(config);
    EXPECT_NE(optimizer, nullptr) << "Optimizer should be created";
    
    if (optimizer) {
        EXPECT_EQ(optimizer->getOptimizerId(), config.linkId) << "Optimizer ID should match";
        EXPECT_TRUE(optimizer->isInitialized()) << "Optimizer should be initialized";
    }
}

TEST_F(NVLinkOptimizationSystemTest, TestCommunication) {
    auto& system = GlobalNVLinkOptimizationSystem::getInstance();
    
    // Create optimizer first
    NVLinkConfig config;
    config.linkId = "nvlink_2";
    config.sourceGPU = 0;
    config.destinationGPU = 1;
    config.linkWidth = 4;
    config.linkSpeed = 25.0f;
    config.bandwidth = 25.0f;
    config.latency = 100.0f;
    config.isActive = true;
    config.topology = NVLinkTopology::RING;
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto optimizer = system.createOptimizer(config);
    ASSERT_NE(optimizer, nullptr) << "Optimizer should be created";
    
    // Create communication request
    NVLinkRequest request;
    request.requestId = "comm_request_1";
    request.sourceGPU = 0;
    request.destinationGPU = 1;
    request.sourcePtr = malloc(1024); // Allocate test memory
    request.destinationPtr = malloc(1024);
    request.size = 1024;
    request.pattern = NVLinkPattern::POINT_TO_POINT;
    request.priority = 0.5f;
    request.timeout = std::chrono::milliseconds(5000);
    request.createdAt = std::chrono::system_clock::now();
    
    // Execute communication
    auto response = system.communicate(request);
    EXPECT_TRUE(response.success) << "Communication should succeed";
    EXPECT_EQ(response.requestId, request.requestId) << "Request ID should match";
    EXPECT_GT(response.bandwidth, 0.0f) << "Bandwidth should be positive";
    EXPECT_GT(response.latency, 0.0f) << "Latency should be positive";
    EXPECT_GT(response.throughput, 0.0f) << "Throughput should be positive";
    
    // Cleanup
    free(request.sourcePtr);
    free(request.destinationPtr);
}

TEST_F(NVLinkOptimizationSystemTest, TestAsyncCommunication) {
    auto& system = GlobalNVLinkOptimizationSystem::getInstance();
    
    // Create optimizer first
    NVLinkConfig config;
    config.linkId = "nvlink_3";
    config.sourceGPU = 0;
    config.destinationGPU = 1;
    config.linkWidth = 4;
    config.linkSpeed = 25.0f;
    config.bandwidth = 25.0f;
    config.latency = 100.0f;
    config.isActive = true;
    config.topology = NVLinkTopology::RING;
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto optimizer = system.createOptimizer(config);
    ASSERT_NE(optimizer, nullptr) << "Optimizer should be created";
    
    // Create communication request
    NVLinkRequest request;
    request.requestId = "comm_request_2";
    request.sourceGPU = 0;
    request.destinationGPU = 1;
    request.sourcePtr = malloc(1024);
    request.destinationPtr = malloc(1024);
    request.size = 1024;
    request.pattern = NVLinkPattern::POINT_TO_POINT;
    request.priority = 0.5f;
    request.timeout = std::chrono::milliseconds(5000);
    request.createdAt = std::chrono::system_clock::now();
    
    // Execute async communication
    auto future = system.communicateAsync(request);
    EXPECT_TRUE(future.valid()) << "Future should be valid";
    
    // Wait for completion
    auto response = future.get();
    EXPECT_TRUE(response.success) << "Async communication should succeed";
    EXPECT_EQ(response.requestId, request.requestId) << "Request ID should match";
    EXPECT_GT(response.bandwidth, 0.0f) << "Bandwidth should be positive";
    EXPECT_GT(response.latency, 0.0f) << "Latency should be positive";
    EXPECT_GT(response.throughput, 0.0f) << "Throughput should be positive";
    
    // Cleanup
    free(request.sourcePtr);
    free(request.destinationPtr);
}

TEST_F(NVLinkOptimizationSystemTest, TestOptimizerManagement) {
    auto& system = GlobalNVLinkOptimizationSystem::getInstance();
    
    // Create multiple optimizers
    std::vector<std::string> optimizerIds;
    for (int i = 0; i < 4; ++i) {
        NVLinkConfig config;
        config.linkId = "nvlink_" + std::to_string(i + 4);
        config.sourceGPU = i;
        config.destinationGPU = (i + 1) % 4;
        config.linkWidth = 4;
        config.linkSpeed = 25.0f;
        config.bandwidth = 25.0f;
        config.latency = 100.0f;
        config.isActive = true;
        config.topology = NVLinkTopology::RING;
        config.createdAt = std::chrono::system_clock::now();
        config.lastUsed = std::chrono::system_clock::now();
        
        auto optimizer = system.createOptimizer(config);
        ASSERT_NE(optimizer, nullptr) << "Optimizer " << i << " should be created";
        optimizerIds.push_back(config.linkId);
    }
    
    // Test optimizer retrieval
    for (const auto& optimizerId : optimizerIds) {
        auto optimizer = system.getOptimizer(optimizerId);
        EXPECT_NE(optimizer, nullptr) << "Optimizer " << optimizerId << " should be retrievable";
        EXPECT_EQ(optimizer->getOptimizerId(), optimizerId) << "Optimizer ID should match";
    }
    
    // Test getting all optimizers
    auto allOptimizers = system.getAllOptimizers();
    EXPECT_GE(allOptimizers.size(), 4) << "Should have at least 4 optimizers";
    
    // Test optimizer destruction
    for (const auto& optimizerId : optimizerIds) {
        bool destroyed = system.destroyOptimizer(optimizerId);
        EXPECT_TRUE(destroyed) << "Optimizer " << optimizerId << " should be destroyed";
    }
}

TEST_F(NVLinkOptimizationSystemTest, TestOptimizationStrategies) {
    auto& system = GlobalNVLinkOptimizationSystem::getInstance();
    
    // Create optimizer first
    NVLinkConfig config;
    config.linkId = "nvlink_8";
    config.sourceGPU = 0;
    config.destinationGPU = 1;
    config.linkWidth = 4;
    config.linkSpeed = 25.0f;
    config.bandwidth = 25.0f;
    config.latency = 100.0f;
    config.isActive = true;
    config.topology = NVLinkTopology::RING;
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto optimizer = system.createOptimizer(config);
    ASSERT_NE(optimizer, nullptr) << "Optimizer should be created";
    
    // Cast to advanced optimizer
    auto advancedOptimizer = std::dynamic_pointer_cast<AdvancedNVLinkOptimizer>(optimizer);
    ASSERT_NE(advancedOptimizer, nullptr) << "Optimizer should be an advanced optimizer";
    
    // Test optimization strategies
    EXPECT_TRUE(advancedOptimizer->optimizeBandwidth()) << "Bandwidth optimization should succeed";
    EXPECT_TRUE(advancedOptimizer->optimizeLatency()) << "Latency optimization should succeed";
    EXPECT_TRUE(advancedOptimizer->optimizeThroughput()) << "Throughput optimization should succeed";
    EXPECT_TRUE(advancedOptimizer->optimizeBalanced()) << "Balanced optimization should succeed";
    
    // Test custom optimization
    std::map<std::string, std::string> customParams = {
        {"link_speed", "30.0"},
        {"latency", "80.0"},
        {"bandwidth", "30.0"},
        {"link_width", "6"}
    };
    EXPECT_TRUE(advancedOptimizer->optimizeCustom(customParams)) << "Custom optimization should succeed";
    
    // Test optimization strategy setting
    EXPECT_TRUE(advancedOptimizer->setOptimizationStrategy(NVLinkOptimizationStrategy::BANDWIDTH_OPTIMIZATION)) << "Strategy setting should succeed";
    EXPECT_EQ(advancedOptimizer->getOptimizationStrategy(), NVLinkOptimizationStrategy::BANDWIDTH_OPTIMIZATION) << "Strategy should match";
}

TEST_F(NVLinkOptimizationSystemTest, TestPerformanceMonitoring) {
    auto& system = GlobalNVLinkOptimizationSystem::getInstance();
    
    // Create optimizer first
    NVLinkConfig config;
    config.linkId = "nvlink_9";
    config.sourceGPU = 0;
    config.destinationGPU = 1;
    config.linkWidth = 4;
    config.linkSpeed = 25.0f;
    config.bandwidth = 25.0f;
    config.latency = 100.0f;
    config.isActive = true;
    config.topology = NVLinkTopology::RING;
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto optimizer = system.createOptimizer(config);
    ASSERT_NE(optimizer, nullptr) << "Optimizer should be created";
    
    // Enable profiling
    EXPECT_TRUE(optimizer->enableProfiling()) << "Profiling should be enabled";
    
    // Get performance metrics
    auto metrics = optimizer->getPerformanceMetrics();
    EXPECT_FALSE(metrics.empty()) << "Performance metrics should not be empty";
    EXPECT_GE(metrics["utilization"], 0.0) << "Utilization should be non-negative";
    EXPECT_GE(metrics["bandwidth"], 0.0) << "Bandwidth should be non-negative";
    EXPECT_GE(metrics["latency"], 0.0) << "Latency should be non-negative";
    EXPECT_GE(metrics["throughput"], 0.0) << "Throughput should be non-negative";
    EXPECT_GE(metrics["request_count"], 0.0) << "Request count should be non-negative";
    EXPECT_GE(metrics["error_count"], 0.0) << "Error count should be non-negative";
    
    // Get profiling data
    auto profilingData = optimizer->getProfilingData();
    EXPECT_FALSE(profilingData.empty()) << "Profiling data should not be empty";
    EXPECT_GE(profilingData["utilization"], 0.0) << "Profiling utilization should be non-negative";
    EXPECT_GE(profilingData["bandwidth"], 0.0) << "Profiling bandwidth should be non-negative";
    EXPECT_GE(profilingData["latency"], 0.0) << "Profiling latency should be non-negative";
    EXPECT_GE(profilingData["throughput"], 0.0) << "Profiling throughput should be non-negative";
    EXPECT_GE(profilingData["request_count"], 0.0) << "Profiling request count should be non-negative";
    EXPECT_GE(profilingData["error_count"], 0.0) << "Profiling error count should be non-negative";
    EXPECT_GE(profilingData["active_requests"], 0.0) << "Active requests should be non-negative";
    EXPECT_GE(profilingData["link_speed"], 0.0) << "Link speed should be non-negative";
    EXPECT_GE(profilingData["link_width"], 0.0) << "Link width should be non-negative";
    EXPECT_GE(profilingData["source_gpu"], 0.0) << "Source GPU should be non-negative";
    EXPECT_GE(profilingData["destination_gpu"], 0.0) << "Destination GPU should be non-negative";
    
    // Get utilization
    float utilization = optimizer->getUtilization();
    EXPECT_GE(utilization, 0.0f) << "Utilization should be non-negative";
    EXPECT_LE(utilization, 1.0f) << "Utilization should not exceed 1.0";
    
    // Disable profiling
    EXPECT_TRUE(optimizer->disableProfiling()) << "Profiling should be disabled";
}

TEST_F(NVLinkOptimizationSystemTest, TestSystemMetrics) {
    auto& system = GlobalNVLinkOptimizationSystem::getInstance();
    
    // Get system metrics
    auto metrics = system.getSystemMetrics();
    EXPECT_FALSE(metrics.empty()) << "System metrics should not be empty";
    EXPECT_GT(metrics["total_optimizers"], 0.0) << "Total optimizers should be positive";
    EXPECT_GE(metrics["active_requests"], 0.0) << "Active requests should be non-negative";
    EXPECT_GE(metrics["average_utilization"], 0.0) << "Average utilization should be non-negative";
    EXPECT_EQ(metrics["system_initialized"], 1.0) << "System should be initialized";
    EXPECT_GT(metrics["configuration_items"], 0.0) << "Configuration items should be positive";
}

TEST_F(NVLinkOptimizationSystemTest, TestSystemConfiguration) {
    auto& system = GlobalNVLinkOptimizationSystem::getInstance();
    
    // Test system configuration
    std::map<std::string, std::string> config = {
        {"max_optimizers", "20"},
        {"topology_strategy", "optimized"},
        {"load_balancing_strategy", "least_loaded"},
        {"auto_cleanup", "enabled"},
        {"system_optimization", "enabled"},
        {"profiling", "enabled"}
    };
    
    system.setSystemConfiguration(config);
    
    auto retrievedConfig = system.getSystemConfiguration();
    EXPECT_EQ(retrievedConfig.size(), config.size()) << "Configuration size should match";
    
    for (const auto& item : config) {
        EXPECT_EQ(retrievedConfig[item.first], item.second) 
            << "Configuration item " << item.first << " should match";
    }
}

TEST_F(NVLinkOptimizationSystemTest, TestAdvancedOptimizerFeatures) {
    auto& system = GlobalNVLinkOptimizationSystem::getInstance();
    
    // Create optimizer first
    NVLinkConfig config;
    config.linkId = "nvlink_10";
    config.sourceGPU = 0;
    config.destinationGPU = 1;
    config.linkWidth = 4;
    config.linkSpeed = 25.0f;
    config.bandwidth = 25.0f;
    config.latency = 100.0f;
    config.isActive = true;
    config.topology = NVLinkTopology::RING;
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto optimizer = system.createOptimizer(config);
    ASSERT_NE(optimizer, nullptr) << "Optimizer should be created";
    
    // Cast to advanced optimizer
    auto advancedOptimizer = std::dynamic_pointer_cast<AdvancedNVLinkOptimizer>(optimizer);
    ASSERT_NE(advancedOptimizer, nullptr) << "Optimizer should be an advanced optimizer";
    
    // Test advanced features
    EXPECT_TRUE(advancedOptimizer->analyzeTopology()) << "Topology analysis should succeed";
    EXPECT_TRUE(advancedOptimizer->optimizeTopology()) << "Topology optimization should succeed";
    EXPECT_TRUE(advancedOptimizer->balanceLoad()) << "Load balancing should succeed";
    EXPECT_TRUE(advancedOptimizer->validateLinks()) << "Link validation should succeed";
    
    // Test topology info
    auto topologyInfo = advancedOptimizer->getTopologyInfo();
    EXPECT_FALSE(topologyInfo.empty()) << "Topology info should not be empty";
    EXPECT_EQ(topologyInfo["link_id"], config.linkId) << "Link ID should match";
    EXPECT_EQ(topologyInfo["source_gpu"], std::to_string(config.sourceGPU)) << "Source GPU should match";
    EXPECT_EQ(topologyInfo["destination_gpu"], std::to_string(config.destinationGPU)) << "Destination GPU should match";
    
    // Test link management
    EXPECT_TRUE(advancedOptimizer->setLinkPriority(0, 0.8f)) << "Link priority setting should succeed";
    EXPECT_GE(advancedOptimizer->getLinkPriority(0), 0.0f) << "Link priority should be non-negative";
    EXPECT_TRUE(advancedOptimizer->enableLink(0)) << "Link enabling should succeed";
    EXPECT_TRUE(advancedOptimizer->isLinkActive(0)) << "Link should be active";
    EXPECT_TRUE(advancedOptimizer->disableLink(0)) << "Link disabling should succeed";
}

TEST_F(NVLinkOptimizationSystemTest, TestTopologyManagement) {
    auto& system = GlobalNVLinkOptimizationSystem::getInstance();
    
    auto topologyManager = system.getTopologyManager();
    ASSERT_NE(topologyManager, nullptr) << "Topology manager should not be null";
    
    // Test topology operations
    EXPECT_TRUE(topologyManager->analyzeTopology()) << "Topology analysis should succeed";
    EXPECT_TRUE(topologyManager->optimizeTopology()) << "Topology optimization should succeed";
    EXPECT_TRUE(topologyManager->balanceLoad()) << "Load balancing should succeed";
    EXPECT_TRUE(topologyManager->validateTopology()) << "Topology validation should succeed";
    
    // Test topology info
    auto topologyInfo = topologyManager->getTopologyInfo();
    EXPECT_FALSE(topologyInfo.empty()) << "Topology info should not be empty";
    EXPECT_GT(std::stoi(topologyInfo["total_optimizers"]), 0) << "Total optimizers should be positive";
    
    // Test system management
    EXPECT_TRUE(topologyManager->optimizeSystem()) << "System optimization should succeed";
    EXPECT_TRUE(topologyManager->cleanupIdleOptimizers()) << "Idle optimizer cleanup should succeed";
    EXPECT_TRUE(topologyManager->validateSystem()) << "System validation should succeed";
    
    // Test system metrics
    auto systemMetrics = topologyManager->getSystemMetrics();
    EXPECT_FALSE(systemMetrics.empty()) << "System metrics should not be empty";
    EXPECT_GT(systemMetrics["total_optimizers"], 0.0) << "Total optimizers should be positive";
    
    // Test optimizer counts
    auto optimizerCounts = topologyManager->getOptimizerCounts();
    EXPECT_FALSE(optimizerCounts.empty()) << "Optimizer counts should not be empty";
    EXPECT_GT(optimizerCounts["total"], 0) << "Total optimizer count should be positive";
    
    // Test communication metrics
    auto communicationMetrics = topologyManager->getCommunicationMetrics();
    EXPECT_FALSE(communicationMetrics.empty()) << "Communication metrics should not be empty";
    EXPECT_GE(communicationMetrics["total_requests"], 0.0) << "Total requests should be non-negative";
    EXPECT_GE(communicationMetrics["active_requests"], 0.0) << "Active requests should be non-negative";
}

TEST_F(NVLinkOptimizationSystemTest, TestCommunicationPatterns) {
    auto& system = GlobalNVLinkOptimizationSystem::getInstance();
    
    // Create optimizer first
    NVLinkConfig config;
    config.linkId = "nvlink_11";
    config.sourceGPU = 0;
    config.destinationGPU = 1;
    config.linkWidth = 4;
    config.linkSpeed = 25.0f;
    config.bandwidth = 25.0f;
    config.latency = 100.0f;
    config.isActive = true;
    config.topology = NVLinkTopology::RING;
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto optimizer = system.createOptimizer(config);
    ASSERT_NE(optimizer, nullptr) << "Optimizer should be created";
    
    // Test different communication patterns
    std::vector<NVLinkPattern> patterns = {
        NVLinkPattern::POINT_TO_POINT,
        NVLinkPattern::BROADCAST,
        NVLinkPattern::REDUCE,
        NVLinkPattern::ALL_REDUCE,
        NVLinkPattern::SCATTER,
        NVLinkPattern::GATHER,
        NVLinkPattern::ALL_GATHER
    };
    
    for (const auto& pattern : patterns) {
        NVLinkRequest request;
        request.requestId = "pattern_test_" + std::to_string(static_cast<int>(pattern));
        request.sourceGPU = 0;
        request.destinationGPU = 1;
        request.sourcePtr = malloc(1024);
        request.destinationPtr = malloc(1024);
        request.size = 1024;
        request.pattern = pattern;
        request.priority = 0.5f;
        request.timeout = std::chrono::milliseconds(5000);
        request.createdAt = std::chrono::system_clock::now();
        
        auto response = system.communicate(request);
        EXPECT_TRUE(response.success) << "Communication pattern " << static_cast<int>(pattern) << " should succeed";
        EXPECT_EQ(response.requestId, request.requestId) << "Request ID should match";
        EXPECT_GT(response.bandwidth, 0.0f) << "Bandwidth should be positive";
        EXPECT_GT(response.latency, 0.0f) << "Latency should be positive";
        EXPECT_GT(response.throughput, 0.0f) << "Throughput should be positive";
        
        // Cleanup
        free(request.sourcePtr);
        free(request.destinationPtr);
    }
}

TEST_F(NVLinkOptimizationSystemTest, TestTopologyTypes) {
    auto& system = GlobalNVLinkOptimizationSystem::getInstance();
    
    // Test different topology types
    std::vector<NVLinkTopology> topologies = {
        NVLinkTopology::RING,
        NVLinkTopology::MESH,
        NVLinkTopology::TREE,
        NVLinkTopology::STAR,
        NVLinkTopology::CUSTOM
    };
    
    for (const auto& topology : topologies) {
        NVLinkConfig config;
        config.linkId = "topology_test_" + std::to_string(static_cast<int>(topology));
        config.sourceGPU = 0;
        config.destinationGPU = 1;
        config.linkWidth = 4;
        config.linkSpeed = 25.0f;
        config.bandwidth = 25.0f;
        config.latency = 100.0f;
        config.isActive = true;
        config.topology = topology;
        config.createdAt = std::chrono::system_clock::now();
        config.lastUsed = std::chrono::system_clock::now();
        
        auto optimizer = system.createOptimizer(config);
        EXPECT_NE(optimizer, nullptr) << "Optimizer for topology " << static_cast<int>(topology) << " should be created";
        
        if (optimizer) {
            EXPECT_EQ(optimizer->getConfig().topology, topology) << "Topology should match";
        }
    }
}

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    
    // Set up logging
    spdlog::set_level(spdlog::level::info);
    
    return RUN_ALL_TESTS();
}
