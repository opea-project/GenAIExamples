#include <gtest/gtest.h>
#include <spdlog/spdlog.h>
#include "virtualization/virtual_compute_node.h"
#include <chrono>
#include <thread>

using namespace cogniware::virtualization;

class VirtualComputeNodeSystemTest : public ::testing::Test {
protected:
    void SetUp() override {
        spdlog::set_level(spdlog::level::debug);
        
        // Initialize the global system
        auto& system = GlobalVirtualComputeNodeSystem::getInstance();
        ASSERT_TRUE(system.initialize()) << "Failed to initialize global virtual compute node system";
    }
    
    void TearDown() override {
        // Shutdown the global system
        auto& system = GlobalVirtualComputeNodeSystem::getInstance();
        system.shutdown();
    }
};

TEST_F(VirtualComputeNodeSystemTest, TestSystemInitialization) {
    auto& system = GlobalVirtualComputeNodeSystem::getInstance();
    
    EXPECT_TRUE(system.isInitialized()) << "System should be initialized";
    
    // Test component access
    auto nodeManager = system.getNodeManager();
    EXPECT_NE(nodeManager, nullptr) << "Node manager should not be null";
}

TEST_F(VirtualComputeNodeSystemTest, TestVirtualNodeCreation) {
    auto& system = GlobalVirtualComputeNodeSystem::getInstance();
    
    // Create virtual node configuration
    VirtualNodeConfig config;
    config.nodeId = "test_node_1";
    config.type = VirtualNodeType::TENSOR_CORE_NODE;
    config.memorySize = 1024 * 1024 * 1024; // 1GB
    config.computeCores = 64;
    config.tensorCores = 32;
    config.priority = 0.8f;
    config.ownerLLM = "test_llm";
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    // Create node
    auto node = system.createNode(config);
    EXPECT_NE(node, nullptr) << "Node should be created";
    
    if (node) {
        EXPECT_EQ(node->getNodeId(), config.nodeId) << "Node ID should match";
        EXPECT_EQ(node->getNodeType(), config.type) << "Node type should match";
        EXPECT_EQ(node->getStatus(), NodeStatus::ACTIVE) << "Node should be active";
        EXPECT_TRUE(node->isInitialized()) << "Node should be initialized";
    }
}

TEST_F(VirtualComputeNodeSystemTest, TestResourceAllocation) {
    auto& system = GlobalVirtualComputeNodeSystem::getInstance();
    
    // Create node first
    VirtualNodeConfig config;
    config.nodeId = "test_node_2";
    config.type = VirtualNodeType::CUDA_CORE_NODE;
    config.memorySize = 2048 * 1024 * 1024; // 2GB
    config.computeCores = 128;
    config.tensorCores = 64;
    config.priority = 0.9f;
    config.ownerLLM = "test_llm";
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto node = system.createNode(config);
    ASSERT_NE(node, nullptr) << "Node should be created";
    
    // Create resource allocation request
    ResourceAllocationRequest request;
    request.requestId = "test_request_1";
    request.llmId = "test_llm";
    request.requestedMemory = 512 * 1024 * 1024; // 512MB
    request.requestedCores = 32;
    request.requestedTensorCores = 16;
    request.priority = 0.7f;
    request.timeout = std::chrono::milliseconds(5000);
    request.requirements["precision"] = "fp16";
    request.requirements["optimization"] = "high";
    
    // Allocate resources
    auto response = system.allocateResources(request);
    EXPECT_TRUE(response.success) << "Resource allocation should succeed";
    EXPECT_EQ(response.requestId, request.requestId) << "Request ID should match";
    EXPECT_EQ(response.nodeId, config.nodeId) << "Node ID should match";
    EXPECT_EQ(response.allocatedMemory, request.requestedMemory) << "Allocated memory should match";
    EXPECT_EQ(response.allocatedCores, request.requestedCores) << "Allocated cores should match";
    EXPECT_EQ(response.allocatedTensorCores, request.requestedTensorCores) << "Allocated tensor cores should match";
    
    // Verify node has resources allocated
    EXPECT_TRUE(node->isResourceAllocated()) << "Node should have resources allocated";
    EXPECT_EQ(node->getAvailableMemory(), config.memorySize - request.requestedMemory) << "Available memory should be reduced";
    EXPECT_EQ(node->getAvailableCores(), config.computeCores - request.requestedCores) << "Available cores should be reduced";
    EXPECT_EQ(node->getAvailableTensorCores(), config.tensorCores - request.requestedTensorCores) << "Available tensor cores should be reduced";
}

TEST_F(VirtualComputeNodeSystemTest, TestTaskExecution) {
    auto& system = GlobalVirtualComputeNodeSystem::getInstance();
    
    // Create node
    VirtualNodeConfig config;
    config.nodeId = "test_node_3";
    config.type = VirtualNodeType::MIXED_NODE;
    config.memorySize = 1024 * 1024 * 1024; // 1GB
    config.computeCores = 64;
    config.tensorCores = 32;
    config.priority = 0.8f;
    config.ownerLLM = "test_llm";
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto node = system.createNode(config);
    ASSERT_NE(node, nullptr) << "Node should be created";
    
    // Allocate resources
    ResourceAllocationRequest request;
    request.requestId = "test_request_2";
    request.llmId = "test_llm";
    request.requestedMemory = 256 * 1024 * 1024; // 256MB
    request.requestedCores = 16;
    request.requestedTensorCores = 8;
    request.priority = 0.7f;
    request.timeout = std::chrono::milliseconds(5000);
    
    auto response = system.allocateResources(request);
    ASSERT_TRUE(response.success) << "Resource allocation should succeed";
    
    // Execute task
    std::string taskId = "test_task_1";
    bool taskExecuted = false;
    std::function<void()> task = [&taskExecuted]() {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        taskExecuted = true;
    };
    
    bool success = node->executeTask(taskId, task);
    EXPECT_TRUE(success) << "Task execution should succeed";
    
    // Wait for task to complete
    std::this_thread::sleep_for(std::chrono::milliseconds(200));
    
    // Verify task was executed
    EXPECT_TRUE(taskExecuted) << "Task should have been executed";
    EXPECT_FALSE(node->isTaskRunning(taskId)) << "Task should not be running anymore";
    
    // Get active tasks
    auto activeTasks = node->getActiveTasks();
    EXPECT_TRUE(activeTasks.empty()) << "No active tasks should remain";
}

TEST_F(VirtualComputeNodeSystemTest, TestTaskCancellation) {
    auto& system = GlobalVirtualComputeNodeSystem::getInstance();
    
    // Create node
    VirtualNodeConfig config;
    config.nodeId = "test_node_4";
    config.type = VirtualNodeType::DEDICATED_NODE;
    config.memorySize = 1024 * 1024 * 1024; // 1GB
    config.computeCores = 64;
    config.tensorCores = 32;
    config.priority = 0.8f;
    config.ownerLLM = "test_llm";
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto node = system.createNode(config);
    ASSERT_NE(node, nullptr) << "Node should be created";
    
    // Allocate resources
    ResourceAllocationRequest request;
    request.requestId = "test_request_3";
    request.llmId = "test_llm";
    request.requestedMemory = 256 * 1024 * 1024; // 256MB
    request.requestedCores = 16;
    request.requestedTensorCores = 8;
    request.priority = 0.7f;
    request.timeout = std::chrono::milliseconds(5000);
    
    auto response = system.allocateResources(request);
    ASSERT_TRUE(response.success) << "Resource allocation should succeed";
    
    // Execute long-running task
    std::string taskId = "test_task_2";
    bool taskStarted = false;
    bool taskCancelled = false;
    std::function<void()> task = [&taskStarted, &taskCancelled]() {
        taskStarted = true;
        std::this_thread::sleep_for(std::chrono::milliseconds(1000));
        taskCancelled = true;
    };
    
    bool success = node->executeTask(taskId, task);
    EXPECT_TRUE(success) << "Task execution should succeed";
    
    // Wait for task to start
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    EXPECT_TRUE(taskStarted) << "Task should have started";
    EXPECT_TRUE(node->isTaskRunning(taskId)) << "Task should be running";
    
    // Cancel task
    bool cancelled = node->cancelTask(taskId);
    EXPECT_TRUE(cancelled) << "Task cancellation should succeed";
    
    // Wait for cancellation to take effect
    std::this_thread::sleep_for(std::chrono::milliseconds(200));
    EXPECT_FALSE(node->isTaskRunning(taskId)) << "Task should not be running after cancellation";
}

TEST_F(VirtualComputeNodeSystemTest, TestPerformanceMonitoring) {
    auto& system = GlobalVirtualComputeNodeSystem::getInstance();
    
    // Create node
    VirtualNodeConfig config;
    config.nodeId = "test_node_5";
    config.type = VirtualNodeType::SHARED_NODE;
    config.memorySize = 1024 * 1024 * 1024; // 1GB
    config.computeCores = 64;
    config.tensorCores = 32;
    config.priority = 0.8f;
    config.ownerLLM = "test_llm";
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto node = system.createNode(config);
    ASSERT_NE(node, nullptr) << "Node should be created";
    
    // Enable profiling
    EXPECT_TRUE(node->enableProfiling()) << "Profiling should be enabled";
    
    // Allocate resources
    ResourceAllocationRequest request;
    request.requestId = "test_request_4";
    request.llmId = "test_llm";
    request.requestedMemory = 512 * 1024 * 1024; // 512MB
    request.requestedCores = 32;
    request.requestedTensorCores = 16;
    request.priority = 0.7f;
    request.timeout = std::chrono::milliseconds(5000);
    
    auto response = system.allocateResources(request);
    ASSERT_TRUE(response.success) << "Resource allocation should succeed";
    
    // Get performance metrics
    auto metrics = node->getPerformanceMetrics();
    EXPECT_FALSE(metrics.empty()) << "Performance metrics should not be empty";
    EXPECT_GT(metrics["utilization"], 0.0) << "Utilization should be positive";
    EXPECT_GT(metrics["memory_usage"], 0.0) << "Memory usage should be positive";
    EXPECT_GT(metrics["core_usage"], 0.0) << "Core usage should be positive";
    EXPECT_GT(metrics["tensor_core_usage"], 0.0) << "Tensor core usage should be positive";
    
    // Get profiling data
    auto profilingData = node->getProfilingData();
    EXPECT_FALSE(profilingData.empty()) << "Profiling data should not be empty";
    EXPECT_GT(profilingData["utilization"], 0.0) << "Profiling utilization should be positive";
    EXPECT_GT(profilingData["available_memory"], 0.0) << "Available memory should be positive";
    EXPECT_GT(profilingData["available_cores"], 0.0) << "Available cores should be positive";
    EXPECT_GT(profilingData["available_tensor_cores"], 0.0) << "Available tensor cores should be positive";
    
    // Get utilization
    float utilization = node->getUtilization();
    EXPECT_GT(utilization, 0.0f) << "Utilization should be positive";
    EXPECT_LE(utilization, 1.0f) << "Utilization should not exceed 1.0";
    
    // Disable profiling
    EXPECT_TRUE(node->disableProfiling()) << "Profiling should be disabled";
}

TEST_F(VirtualComputeNodeSystemTest, TestNodeManagement) {
    auto& system = GlobalVirtualComputeNodeSystem::getInstance();
    auto nodeManager = system.getNodeManager();
    
    ASSERT_NE(nodeManager, nullptr) << "Node manager should not be null";
    
    // Create multiple nodes
    std::vector<std::string> nodeIds;
    for (int i = 0; i < 5; ++i) {
        VirtualNodeConfig config;
        config.nodeId = "test_node_" + std::to_string(i + 10);
        config.type = static_cast<VirtualNodeType>(i % 6);
        config.memorySize = 1024 * 1024 * 1024; // 1GB
        config.computeCores = 64;
        config.tensorCores = 32;
        config.priority = 0.5f + (i * 0.1f);
        config.ownerLLM = "test_llm_" + std::to_string(i);
        config.createdAt = std::chrono::system_clock::now();
        config.lastUsed = std::chrono::system_clock::now();
        
        auto node = system.createNode(config);
        ASSERT_NE(node, nullptr) << "Node " << i << " should be created";
        nodeIds.push_back(config.nodeId);
    }
    
    // Test node retrieval
    for (const auto& nodeId : nodeIds) {
        auto node = system.getNode(nodeId);
        EXPECT_NE(node, nullptr) << "Node " << nodeId << " should be retrievable";
    }
    
    // Test getting all nodes
    auto allNodes = system.getAllNodes();
    EXPECT_GE(allNodes.size(), 5) << "Should have at least 5 nodes";
    
    // Test node management operations
    auto node = system.getNode(nodeIds[0]);
    ASSERT_NE(node, nullptr) << "Node should be retrievable";
    
    // Test node configuration update
    auto config = node->getConfig();
    config.priority = 0.9f;
    EXPECT_TRUE(node->updateConfig(config)) << "Config update should succeed";
    EXPECT_EQ(node->getPriority(), 0.9f) << "Priority should be updated";
    
    // Test node priority setting
    EXPECT_TRUE(node->setPriority(0.7f)) << "Priority setting should succeed";
    EXPECT_EQ(node->getPriority(), 0.7f) << "Priority should be set";
}

TEST_F(VirtualComputeNodeSystemTest, TestAdvancedNodeFeatures) {
    auto& system = GlobalVirtualComputeNodeSystem::getInstance();
    
    // Create node
    VirtualNodeConfig config;
    config.nodeId = "test_node_6";
    config.type = VirtualNodeType::TENSOR_CORE_NODE;
    config.memorySize = 2048 * 1024 * 1024; // 2GB
    config.computeCores = 128;
    config.tensorCores = 64;
    config.priority = 0.8f;
    config.ownerLLM = "test_llm";
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto node = system.createNode(config);
    ASSERT_NE(node, nullptr) << "Node should be created";
    
    // Cast to advanced node
    auto advancedNode = std::dynamic_pointer_cast<AdvancedVirtualComputeNode>(node);
    ASSERT_NE(advancedNode, nullptr) << "Node should be an advanced node";
    
    // Test advanced features
    EXPECT_TRUE(advancedNode->suspend()) << "Node suspension should succeed";
    EXPECT_EQ(advancedNode->getStatus(), NodeStatus::SUSPENDED) << "Node should be suspended";
    
    EXPECT_TRUE(advancedNode->resume()) << "Node resumption should succeed";
    EXPECT_EQ(advancedNode->getStatus(), NodeStatus::ACTIVE) << "Node should be active";
    
    EXPECT_TRUE(advancedNode->migrate("target_node")) << "Node migration should succeed";
    EXPECT_TRUE(advancedNode->clone("cloned_node")) << "Node cloning should succeed";
    
    EXPECT_TRUE(advancedNode->scale(4096 * 1024 * 1024, 256, 128)) << "Node scaling should succeed";
    
    EXPECT_TRUE(advancedNode->optimize()) << "Node optimization should succeed";
    
    // Test resource info
    auto resourceInfo = advancedNode->getResourceInfo();
    EXPECT_FALSE(resourceInfo.empty()) << "Resource info should not be empty";
    EXPECT_EQ(resourceInfo["node_id"], config.nodeId) << "Node ID should match";
    EXPECT_EQ(resourceInfo["node_type"], std::to_string(static_cast<int>(config.type))) << "Node type should match";
    
    // Test resource validation
    EXPECT_TRUE(advancedNode->validateResources()) << "Resource validation should pass";
}

TEST_F(VirtualComputeNodeSystemTest, TestSystemManagement) {
    auto& system = GlobalVirtualComputeNodeSystem::getInstance();
    auto nodeManager = system.getNodeManager();
    
    ASSERT_NE(nodeManager, nullptr) << "Node manager should not be null";
    
    // Test system optimization
    EXPECT_TRUE(nodeManager->optimizeSystem()) << "System optimization should succeed";
    
    // Test load balancing
    EXPECT_TRUE(nodeManager->balanceLoad()) << "Load balancing should succeed";
    
    // Test system validation
    EXPECT_TRUE(nodeManager->validateSystem()) << "System validation should pass";
    
    // Test system metrics
    auto systemMetrics = system.getSystemMetrics();
    EXPECT_FALSE(systemMetrics.empty()) << "System metrics should not be empty";
    EXPECT_GT(systemMetrics["total_nodes"], 0.0) << "Total nodes should be positive";
    EXPECT_GT(systemMetrics["active_nodes"], 0.0) << "Active nodes should be positive";
    
    // Test node counts
    auto nodeCounts = nodeManager->getNodeCounts();
    EXPECT_FALSE(nodeCounts.empty()) << "Node counts should not be empty";
    EXPECT_GT(nodeCounts["total"], 0) << "Total node count should be positive";
    
    // Test resource utilization
    auto utilization = nodeManager->getResourceUtilization();
    EXPECT_FALSE(utilization.empty()) << "Resource utilization should not be empty";
    EXPECT_GE(utilization["memory"], 0.0) << "Memory utilization should be non-negative";
    EXPECT_GE(utilization["cores"], 0.0) << "Core utilization should be non-negative";
    EXPECT_GE(utilization["tensor_cores"], 0.0) << "Tensor core utilization should be non-negative";
}

TEST_F(VirtualComputeNodeSystemTest, TestSystemProfiling) {
    auto& system = GlobalVirtualComputeNodeSystem::getInstance();
    auto nodeManager = system.getNodeManager();
    
    ASSERT_NE(nodeManager, nullptr) << "Node manager should not be null";
    
    // Enable system profiling
    EXPECT_TRUE(nodeManager->enableSystemProfiling()) << "System profiling should be enabled";
    
    // Get system profiling data
    auto profilingData = nodeManager->getSystemProfilingData();
    EXPECT_FALSE(profilingData.empty()) << "System profiling data should not be empty";
    EXPECT_GT(profilingData["total_nodes"], 0.0) << "Total nodes should be positive";
    EXPECT_GT(profilingData["active_nodes"], 0.0) << "Active nodes should be positive";
    EXPECT_EQ(profilingData["profiling_enabled"], 1.0) << "Profiling should be enabled";
    
    // Disable system profiling
    EXPECT_TRUE(nodeManager->disableSystemProfiling()) << "System profiling should be disabled";
}

TEST_F(VirtualComputeNodeSystemTest, TestSystemConfiguration) {
    auto& system = GlobalVirtualComputeNodeSystem::getInstance();
    
    // Test system configuration
    std::map<std::string, std::string> config = {
        {"max_nodes", "200"},
        {"max_memory", "34359738368"}, // 32GB
        {"max_cores", "2048"},
        {"max_tensor_cores", "1024"},
        {"allocation_strategy", "adaptive"},
        {"auto_cleanup", "enabled"},
        {"load_balancing", "enabled"},
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

TEST_F(VirtualComputeNodeSystemTest, TestResourceDeallocation) {
    auto& system = GlobalVirtualComputeNodeSystem::getInstance();
    
    // Create node
    VirtualNodeConfig config;
    config.nodeId = "test_node_7";
    config.type = VirtualNodeType::CUDA_CORE_NODE;
    config.memorySize = 1024 * 1024 * 1024; // 1GB
    config.computeCores = 64;
    config.tensorCores = 32;
    config.priority = 0.8f;
    config.ownerLLM = "test_llm";
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto node = system.createNode(config);
    ASSERT_NE(node, nullptr) << "Node should be created";
    
    // Allocate resources
    ResourceAllocationRequest request;
    request.requestId = "test_request_5";
    request.llmId = "test_llm";
    request.requestedMemory = 512 * 1024 * 1024; // 512MB
    request.requestedCores = 32;
    request.requestedTensorCores = 16;
    request.priority = 0.7f;
    request.timeout = std::chrono::milliseconds(5000);
    
    auto response = system.allocateResources(request);
    ASSERT_TRUE(response.success) << "Resource allocation should succeed";
    EXPECT_TRUE(node->isResourceAllocated()) << "Node should have resources allocated";
    
    // Deallocate resources
    bool deallocated = system.deallocateResources(config.nodeId);
    EXPECT_TRUE(deallocated) << "Resource deallocation should succeed";
    EXPECT_FALSE(node->isResourceAllocated()) << "Node should not have resources allocated";
    
    // Verify available resources are restored
    EXPECT_EQ(node->getAvailableMemory(), config.memorySize) << "Available memory should be restored";
    EXPECT_EQ(node->getAvailableCores(), config.computeCores) << "Available cores should be restored";
    EXPECT_EQ(node->getAvailableTensorCores(), config.tensorCores) << "Available tensor cores should be restored";
}

TEST_F(VirtualComputeNodeSystemTest, TestNodeDestruction) {
    auto& system = GlobalVirtualComputeNodeSystem::getInstance();
    
    // Create node
    VirtualNodeConfig config;
    config.nodeId = "test_node_8";
    config.type = VirtualNodeType::MEMORY_NODE;
    config.memorySize = 1024 * 1024 * 1024; // 1GB
    config.computeCores = 64;
    config.tensorCores = 32;
    config.priority = 0.8f;
    config.ownerLLM = "test_llm";
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto node = system.createNode(config);
    ASSERT_NE(node, nullptr) << "Node should be created";
    
    // Verify node exists
    auto retrievedNode = system.getNode(config.nodeId);
    EXPECT_NE(retrievedNode, nullptr) << "Node should be retrievable";
    
    // Destroy node
    bool destroyed = system.destroyNode(config.nodeId);
    EXPECT_TRUE(destroyed) << "Node destruction should succeed";
    
    // Verify node no longer exists
    auto destroyedNode = system.getNode(config.nodeId);
    EXPECT_EQ(destroyedNode, nullptr) << "Destroyed node should not be retrievable";
}

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    
    // Set up logging
    spdlog::set_level(spdlog::level::info);
    
    return RUN_ALL_TESTS();
}
