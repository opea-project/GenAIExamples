#include <gtest/gtest.h>
#include <spdlog/spdlog.h>
#include "bridge/python_cpp_bridge.h"
#include <chrono>
#include <thread>

using namespace cogniware::bridge;

class PythonCppBridgeSystemTest : public ::testing::Test {
protected:
    void SetUp() override {
        spdlog::set_level(spdlog::level::debug);
        
        // Initialize the global system
        auto& system = GlobalPythonCppBridgeSystem::getInstance();
        ASSERT_TRUE(system.initialize()) << "Failed to initialize global Python-C++ bridge system";
    }
    
    void TearDown() override {
        // Shutdown the global system
        auto& system = GlobalPythonCppBridgeSystem::getInstance();
        system.shutdown();
    }
};

TEST_F(PythonCppBridgeSystemTest, TestSystemInitialization) {
    auto& system = GlobalPythonCppBridgeSystem::getInstance();
    
    EXPECT_TRUE(system.isInitialized()) << "System should be initialized";
    
    // Test component access
    auto bridgeManager = system.getBridgeManager();
    EXPECT_NE(bridgeManager, nullptr) << "Bridge manager should not be null";
}

TEST_F(PythonCppBridgeSystemTest, TestBridgeCreation) {
    auto& system = GlobalPythonCppBridgeSystem::getInstance();
    
    // Create bridge configuration
    BridgeConfig config;
    config.bridgeId = "bridge_1";
    config.type = BridgeType::MEMORY_BRIDGE;
    config.pythonModule = "test_module";
    config.pythonClass = "TestClass";
    config.cppInterface = "TestInterface";
    config.enableMemorySharing = true;
    config.enableResourceMonitoring = true;
    config.timeout = std::chrono::milliseconds(5000);
    config.createdAt = std::chrono::system_clock::now();
    
    // Create bridge
    auto bridge = system.createBridge(config);
    EXPECT_NE(bridge, nullptr) << "Bridge should be created";
    
    if (bridge) {
        EXPECT_EQ(bridge->getBridgeId(), config.bridgeId) << "Bridge ID should match";
        EXPECT_TRUE(bridge->isInitialized()) << "Bridge should be initialized";
        EXPECT_EQ(bridge->getBridgeType(), config.type) << "Bridge type should match";
    }
}

TEST_F(PythonCppBridgeSystemTest, TestMemoryPointerRegistration) {
    auto& system = GlobalPythonCppBridgeSystem::getInstance();
    
    // Create bridge first
    BridgeConfig config;
    config.bridgeId = "bridge_2";
    config.type = BridgeType::MEMORY_BRIDGE;
    config.pythonModule = "test_module";
    config.pythonClass = "TestClass";
    config.cppInterface = "TestInterface";
    config.enableMemorySharing = true;
    config.enableResourceMonitoring = true;
    config.timeout = std::chrono::milliseconds(5000);
    config.createdAt = std::chrono::system_clock::now();
    
    auto bridge = system.createBridge(config);
    ASSERT_NE(bridge, nullptr) << "Bridge should be created";
    
    // Register memory pointer
    void* testAddress = malloc(1024);
    size_t testSize = 1024;
    MemoryAccessType accessType = MemoryAccessType::READ_WRITE;
    
    std::string pointerId = system.registerMemoryPointer(testAddress, testSize, accessType);
    EXPECT_FALSE(pointerId.empty()) << "Memory pointer should be registered";
    
    if (!pointerId.empty()) {
        // Test memory pointer info
        auto pointerInfo = system.getMemoryPointerInfo(pointerId);
        EXPECT_EQ(pointerInfo.pointerId, pointerId) << "Pointer ID should match";
        EXPECT_EQ(pointerInfo.address, testAddress) << "Address should match";
        EXPECT_EQ(pointerInfo.size, testSize) << "Size should match";
        EXPECT_EQ(pointerInfo.accessType, accessType) << "Access type should match";
        
        // Test unregistration
        bool unregistered = system.unregisterMemoryPointer(pointerId);
        EXPECT_TRUE(unregistered) << "Memory pointer should be unregistered";
    }
    
    free(testAddress);
}

TEST_F(PythonCppBridgeSystemTest, TestResourceRegistration) {
    auto& system = GlobalPythonCppBridgeSystem::getInstance();
    
    // Create bridge first
    BridgeConfig config;
    config.bridgeId = "bridge_3";
    config.type = BridgeType::RESOURCE_BRIDGE;
    config.pythonModule = "test_module";
    config.pythonClass = "TestClass";
    config.cppInterface = "TestInterface";
    config.enableMemorySharing = true;
    config.enableResourceMonitoring = true;
    config.timeout = std::chrono::milliseconds(5000);
    config.createdAt = std::chrono::system_clock::now();
    
    auto bridge = system.createBridge(config);
    ASSERT_NE(bridge, nullptr) << "Bridge should be created";
    
    // Register resource
    ResourceInfo resourceInfo;
    resourceInfo.name = "Test Resource";
    resourceInfo.type = ResourceType::GPU_MEMORY;
    resourceInfo.totalCapacity = 16 * 1024 * 1024 * 1024; // 16GB
    resourceInfo.usedCapacity = 0;
    resourceInfo.availableCapacity = 16 * 1024 * 1024 * 1024; // 16GB
    resourceInfo.utilization = 0.0f;
    resourceInfo.isAvailable = true;
    resourceInfo.lastUpdated = std::chrono::system_clock::now();
    
    std::string resourceId = system.registerResource(resourceInfo);
    EXPECT_FALSE(resourceId.empty()) << "Resource should be registered";
    
    if (!resourceId.empty()) {
        // Test resource info
        auto retrievedResourceInfo = system.getResourceInfo(resourceId);
        EXPECT_EQ(retrievedResourceInfo.resourceId, resourceId) << "Resource ID should match";
        EXPECT_EQ(retrievedResourceInfo.name, resourceInfo.name) << "Resource name should match";
        EXPECT_EQ(retrievedResourceInfo.type, resourceInfo.type) << "Resource type should match";
        EXPECT_EQ(retrievedResourceInfo.totalCapacity, resourceInfo.totalCapacity) << "Total capacity should match";
        
        // Test unregistration
        bool unregistered = system.unregisterResource(resourceId);
        EXPECT_TRUE(unregistered) << "Resource should be unregistered";
    }
}

TEST_F(PythonCppBridgeSystemTest, TestBridgeManagement) {
    auto& system = GlobalPythonCppBridgeSystem::getInstance();
    
    // Create multiple bridges
    std::vector<std::string> bridgeIds;
    for (int i = 0; i < 4; ++i) {
        BridgeConfig config;
        config.bridgeId = "bridge_" + std::to_string(i + 4);
        config.type = BridgeType::MEMORY_BRIDGE;
        config.pythonModule = "test_module";
        config.pythonClass = "TestClass";
        config.cppInterface = "TestInterface";
        config.enableMemorySharing = true;
        config.enableResourceMonitoring = true;
        config.timeout = std::chrono::milliseconds(5000);
        config.createdAt = std::chrono::system_clock::now();
        
        auto bridge = system.createBridge(config);
        ASSERT_NE(bridge, nullptr) << "Bridge " << i << " should be created";
        bridgeIds.push_back(config.bridgeId);
    }
    
    // Test bridge retrieval
    for (const auto& bridgeId : bridgeIds) {
        auto bridge = system.getBridge(bridgeId);
        EXPECT_NE(bridge, nullptr) << "Bridge " << bridgeId << " should be retrievable";
        EXPECT_EQ(bridge->getBridgeId(), bridgeId) << "Bridge ID should match";
    }
    
    // Test getting all bridges
    auto allBridges = system.getAllBridges();
    EXPECT_GE(allBridges.size(), 4) << "Should have at least 4 bridges";
    
    // Test bridge destruction
    for (const auto& bridgeId : bridgeIds) {
        bool destroyed = system.destroyBridge(bridgeId);
        EXPECT_TRUE(destroyed) << "Bridge " << bridgeId << " should be destroyed";
    }
}

TEST_F(PythonCppBridgeSystemTest, TestPerformanceMonitoring) {
    auto& system = GlobalPythonCppBridgeSystem::getInstance();
    
    // Create bridge first
    BridgeConfig config;
    config.bridgeId = "bridge_8";
    config.type = BridgeType::MONITORING_BRIDGE;
    config.pythonModule = "test_module";
    config.pythonClass = "TestClass";
    config.cppInterface = "TestInterface";
    config.enableMemorySharing = true;
    config.enableResourceMonitoring = true;
    config.timeout = std::chrono::milliseconds(5000);
    config.createdAt = std::chrono::system_clock::now();
    
    auto bridge = system.createBridge(config);
    ASSERT_NE(bridge, nullptr) << "Bridge should be created";
    
    // Enable profiling
    EXPECT_TRUE(bridge->enableProfiling()) << "Profiling should be enabled";
    
    // Get performance metrics
    auto metrics = bridge->getPerformanceMetrics();
    EXPECT_FALSE(metrics.empty()) << "Performance metrics should not be empty";
    EXPECT_GE(metrics["utilization"], 0.0) << "Utilization should be non-negative";
    EXPECT_GE(metrics["memory_pointers"], 0.0) << "Memory pointers should be non-negative";
    EXPECT_GE(metrics["resources"], 0.0) << "Resources should be non-negative";
    EXPECT_GE(metrics["python_calls"], 0.0) << "Python calls should be non-negative";
    EXPECT_GE(metrics["memory_accesses"], 0.0) << "Memory accesses should be non-negative";
    EXPECT_GE(metrics["resource_updates"], 0.0) << "Resource updates should be non-negative";
    
    // Get profiling data
    auto profilingData = bridge->getProfilingData();
    EXPECT_FALSE(profilingData.empty()) << "Profiling data should not be empty";
    EXPECT_GE(profilingData["utilization"], 0.0) << "Profiling utilization should be non-negative";
    EXPECT_GE(profilingData["memory_pointers"], 0.0) << "Profiling memory pointers should be non-negative";
    EXPECT_GE(profilingData["resources"], 0.0) << "Profiling resources should be non-negative";
    EXPECT_GE(profilingData["python_calls"], 0.0) << "Profiling python calls should be non-negative";
    EXPECT_GE(profilingData["memory_accesses"], 0.0) << "Profiling memory accesses should be non-negative";
    EXPECT_GE(profilingData["resource_updates"], 0.0) << "Profiling resource updates should be non-negative";
    EXPECT_GE(profilingData["registered_pointers"], 0.0) << "Registered pointers should be non-negative";
    EXPECT_GE(profilingData["registered_resources"], 0.0) << "Registered resources should be non-negative";
    EXPECT_GE(profilingData["bridge_type"], 0.0) << "Bridge type should be non-negative";
    EXPECT_GE(profilingData["python_module"], 0.0) << "Python module should be non-negative";
    EXPECT_GE(profilingData["bridge_status"], 0.0) << "Bridge status should be non-negative";
    
    // Get utilization
    float utilization = bridge->getUtilization();
    EXPECT_GE(utilization, 0.0f) << "Utilization should be non-negative";
    EXPECT_LE(utilization, 1.0f) << "Utilization should not exceed 1.0";
    
    // Disable profiling
    EXPECT_TRUE(bridge->disableProfiling()) << "Profiling should be disabled";
}

TEST_F(PythonCppBridgeSystemTest, TestSystemMetrics) {
    auto& system = GlobalPythonCppBridgeSystem::getInstance();
    
    // Get system metrics
    auto metrics = system.getSystemMetrics();
    EXPECT_FALSE(metrics.empty()) << "System metrics should not be empty";
    EXPECT_GT(metrics["total_bridges"], 0.0) << "Total bridges should be positive";
    EXPECT_GE(metrics["registered_pointers"], 0.0) << "Registered pointers should be non-negative";
    EXPECT_GE(metrics["registered_resources"], 0.0) << "Registered resources should be non-negative";
    EXPECT_GE(metrics["average_utilization"], 0.0) << "Average utilization should be non-negative";
    EXPECT_EQ(metrics["system_initialized"], 1.0) << "System should be initialized";
    EXPECT_GT(metrics["configuration_items"], 0.0) << "Configuration items should be positive";
}

TEST_F(PythonCppBridgeSystemTest, TestSystemConfiguration) {
    auto& system = GlobalPythonCppBridgeSystem::getInstance();
    
    // Test system configuration
    std::map<std::string, std::string> config = {
        {"max_bridges", "20"},
        {"python_path", "/usr/lib/python3.12"},
        {"memory_sharing_strategy", "optimized"},
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

TEST_F(PythonCppBridgeSystemTest, TestAdvancedBridgeFeatures) {
    auto& system = GlobalPythonCppBridgeSystem::getInstance();
    
    // Create bridge first
    BridgeConfig config;
    config.bridgeId = "bridge_10";
    config.type = BridgeType::CONTROL_BRIDGE;
    config.pythonModule = "test_module";
    config.pythonClass = "TestClass";
    config.cppInterface = "TestInterface";
    config.enableMemorySharing = true;
    config.enableResourceMonitoring = true;
    config.timeout = std::chrono::milliseconds(5000);
    config.createdAt = std::chrono::system_clock::now();
    
    auto bridge = system.createBridge(config);
    ASSERT_NE(bridge, nullptr) << "Bridge should be created";
    
    // Cast to advanced bridge
    auto advancedBridge = std::dynamic_pointer_cast<AdvancedPythonCppBridge>(bridge);
    ASSERT_NE(advancedBridge, nullptr) << "Bridge should be an advanced bridge";
    
    // Test advanced features
    EXPECT_TRUE(advancedBridge->connect()) << "Bridge connection should succeed";
    EXPECT_TRUE(advancedBridge->isConnected()) << "Bridge should be connected";
    EXPECT_TRUE(advancedBridge->suspend()) << "Bridge suspension should succeed";
    EXPECT_TRUE(advancedBridge->resume()) << "Bridge resumption should succeed";
    EXPECT_TRUE(advancedBridge->optimize()) << "Bridge optimization should succeed";
    
    // Test bridge info
    auto bridgeInfo = advancedBridge->getBridgeInfo();
    EXPECT_FALSE(bridgeInfo.empty()) << "Bridge info should not be empty";
    EXPECT_EQ(bridgeInfo["bridge_id"], config.bridgeId) << "Bridge ID should match";
    EXPECT_EQ(bridgeInfo["bridge_type"], std::to_string(static_cast<int>(config.type))) << "Bridge type should match";
    
    // Test configuration validation
    EXPECT_TRUE(advancedBridge->validateConfiguration()) << "Configuration validation should succeed";
    
    // Test memory sharing
    EXPECT_TRUE(advancedBridge->setMemorySharing(true)) << "Memory sharing should be enabled";
    EXPECT_TRUE(advancedBridge->isMemorySharingEnabled()) << "Memory sharing should be enabled";
    
    // Test resource monitoring
    EXPECT_TRUE(advancedBridge->setResourceMonitoring(true)) << "Resource monitoring should be enabled";
    EXPECT_TRUE(advancedBridge->isResourceMonitoringEnabled()) << "Resource monitoring should be enabled";
    
    // Test timeout
    EXPECT_TRUE(advancedBridge->setTimeout(std::chrono::milliseconds(10000))) << "Timeout should be set";
    EXPECT_EQ(advancedBridge->getTimeout(), std::chrono::milliseconds(10000)) << "Timeout should match";
    
    // Test disconnect
    EXPECT_TRUE(advancedBridge->disconnect()) << "Bridge disconnection should succeed";
    EXPECT_FALSE(advancedBridge->isConnected()) << "Bridge should be disconnected";
}

TEST_F(PythonCppBridgeSystemTest, TestBridgeManagerFeatures) {
    auto& system = GlobalPythonCppBridgeSystem::getInstance();
    
    auto bridgeManager = system.getBridgeManager();
    ASSERT_NE(bridgeManager, nullptr) << "Bridge manager should not be null";
    
    // Test bridge manager operations
    EXPECT_TRUE(bridgeManager->optimizeSystem()) << "System optimization should succeed";
    EXPECT_TRUE(bridgeManager->balanceLoad()) << "Load balancing should succeed";
    EXPECT_TRUE(bridgeManager->cleanupIdleBridges()) << "Idle bridge cleanup should succeed";
    EXPECT_TRUE(bridgeManager->validateSystem()) << "System validation should succeed";
    
    // Test system metrics
    auto systemMetrics = bridgeManager->getSystemMetrics();
    EXPECT_FALSE(systemMetrics.empty()) << "System metrics should not be empty";
    EXPECT_GT(systemMetrics["total_bridges"], 0.0) << "Total bridges should be positive";
    
    // Test bridge counts
    auto bridgeCounts = bridgeManager->getBridgeCounts();
    EXPECT_FALSE(bridgeCounts.empty()) << "Bridge counts should not be empty";
    EXPECT_GT(bridgeCounts["total"], 0) << "Total bridge count should be positive";
    
    // Test memory metrics
    auto memoryMetrics = bridgeManager->getMemoryMetrics();
    EXPECT_FALSE(memoryMetrics.empty()) << "Memory metrics should not be empty";
    EXPECT_GE(memoryMetrics["total_pointers"], 0.0) << "Total pointers should be non-negative";
    EXPECT_GE(memoryMetrics["active_pointers"], 0.0) << "Active pointers should be non-negative";
    
    // Test resource metrics
    auto resourceMetrics = bridgeManager->getResourceMetrics();
    EXPECT_FALSE(resourceMetrics.empty()) << "Resource metrics should not be empty";
    EXPECT_GE(resourceMetrics["total_resources"], 0.0) << "Total resources should be non-negative";
    EXPECT_GE(resourceMetrics["active_resources"], 0.0) << "Active resources should be non-negative";
    
    // Test system profiling
    EXPECT_TRUE(bridgeManager->enableSystemProfiling()) << "System profiling should be enabled";
    auto profilingData = bridgeManager->getSystemProfilingData();
    EXPECT_FALSE(profilingData.empty()) << "System profiling data should not be empty";
    EXPECT_TRUE(bridgeManager->disableSystemProfiling()) << "System profiling should be disabled";
}

TEST_F(PythonCppBridgeSystemTest, TestBridgeTypes) {
    auto& system = GlobalPythonCppBridgeSystem::getInstance();
    
    // Test different bridge types
    std::vector<BridgeType> types = {
        BridgeType::MEMORY_BRIDGE,
        BridgeType::RESOURCE_BRIDGE,
        BridgeType::CONTROL_BRIDGE,
        BridgeType::DATA_BRIDGE,
        BridgeType::MONITORING_BRIDGE
    };
    
    for (const auto& type : types) {
        BridgeConfig config;
        config.bridgeId = "bridge_type_test_" + std::to_string(static_cast<int>(type));
        config.type = type;
        config.pythonModule = "test_module";
        config.pythonClass = "TestClass";
        config.cppInterface = "TestInterface";
        config.enableMemorySharing = true;
        config.enableResourceMonitoring = true;
        config.timeout = std::chrono::milliseconds(5000);
        config.createdAt = std::chrono::system_clock::now();
        
        auto bridge = system.createBridge(config);
        EXPECT_NE(bridge, nullptr) << "Bridge for type " << static_cast<int>(type) << " should be created";
        
        if (bridge) {
            EXPECT_EQ(bridge->getBridgeType(), type) << "Bridge type should match";
        }
    }
}

TEST_F(PythonCppBridgeSystemTest, TestMemoryAccessTypes) {
    auto& system = GlobalPythonCppBridgeSystem::getInstance();
    
    // Create bridge first
    BridgeConfig config;
    config.bridgeId = "bridge_11";
    config.type = BridgeType::MEMORY_BRIDGE;
    config.pythonModule = "test_module";
    config.pythonClass = "TestClass";
    config.cppInterface = "TestInterface";
    config.enableMemorySharing = true;
    config.enableResourceMonitoring = true;
    config.timeout = std::chrono::milliseconds(5000);
    config.createdAt = std::chrono::system_clock::now();
    
    auto bridge = system.createBridge(config);
    ASSERT_NE(bridge, nullptr) << "Bridge should be created";
    
    // Test different memory access types
    std::vector<MemoryAccessType> accessTypes = {
        MemoryAccessType::READ_ONLY,
        MemoryAccessType::WRITE_ONLY,
        MemoryAccessType::READ_WRITE,
        MemoryAccessType::EXCLUSIVE
    };
    
    for (const auto& accessType : accessTypes) {
        void* testAddress = malloc(1024);
        size_t testSize = 1024;
        
        std::string pointerId = system.registerMemoryPointer(testAddress, testSize, accessType);
        EXPECT_FALSE(pointerId.empty()) << "Memory pointer with access type " << static_cast<int>(accessType) << " should be registered";
        
        if (!pointerId.empty()) {
            auto pointerInfo = system.getMemoryPointerInfo(pointerId);
            EXPECT_EQ(pointerInfo.accessType, accessType) << "Access type should match";
            
            system.unregisterMemoryPointer(pointerId);
        }
        
        free(testAddress);
    }
}

TEST_F(PythonCppBridgeSystemTest, TestResourceTypes) {
    auto& system = GlobalPythonCppBridgeSystem::getInstance();
    
    // Create bridge first
    BridgeConfig config;
    config.bridgeId = "bridge_12";
    config.type = BridgeType::RESOURCE_BRIDGE;
    config.pythonModule = "test_module";
    config.pythonClass = "TestClass";
    config.cppInterface = "TestInterface";
    config.enableMemorySharing = true;
    config.enableResourceMonitoring = true;
    config.timeout = std::chrono::milliseconds(5000);
    config.createdAt = std::chrono::system_clock::now();
    
    auto bridge = system.createBridge(config);
    ASSERT_NE(bridge, nullptr) << "Bridge should be created";
    
    // Test different resource types
    std::vector<ResourceType> resourceTypes = {
        ResourceType::GPU_MEMORY,
        ResourceType::CPU_MEMORY,
        ResourceType::COMPUTE_CORES,
        ResourceType::TENSOR_CORES,
        ResourceType::CUDA_STREAMS,
        ResourceType::VIRTUAL_NODES
    };
    
    for (const auto& resourceType : resourceTypes) {
        ResourceInfo resourceInfo;
        resourceInfo.name = "Test Resource " + std::to_string(static_cast<int>(resourceType));
        resourceInfo.type = resourceType;
        resourceInfo.totalCapacity = 16 * 1024 * 1024 * 1024; // 16GB
        resourceInfo.usedCapacity = 0;
        resourceInfo.availableCapacity = 16 * 1024 * 1024 * 1024; // 16GB
        resourceInfo.utilization = 0.0f;
        resourceInfo.isAvailable = true;
        resourceInfo.lastUpdated = std::chrono::system_clock::now();
        
        std::string resourceId = system.registerResource(resourceInfo);
        EXPECT_FALSE(resourceId.empty()) << "Resource with type " << static_cast<int>(resourceType) << " should be registered";
        
        if (!resourceId.empty()) {
            auto retrievedResourceInfo = system.getResourceInfo(resourceId);
            EXPECT_EQ(retrievedResourceInfo.type, resourceType) << "Resource type should match";
            
            system.unregisterResource(resourceId);
        }
    }
}

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    
    // Set up logging
    spdlog::set_level(spdlog::level::info);
    
    return RUN_ALL_TESTS();
}
