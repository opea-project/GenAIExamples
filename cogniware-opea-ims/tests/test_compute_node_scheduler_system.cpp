#include <gtest/gtest.h>
#include <spdlog/spdlog.h>
#include "scheduler/compute_node_scheduler.h"
#include <chrono>
#include <thread>

using namespace cogniware::scheduler;

class ComputeNodeSchedulerSystemTest : public ::testing::Test {
protected:
    void SetUp() override {
        spdlog::set_level(spdlog::level::debug);
        
        // Initialize the global system
        auto& system = GlobalComputeNodeSchedulerSystem::getInstance();
        ASSERT_TRUE(system.initialize()) << "Failed to initialize global compute node scheduler system";
    }
    
    void TearDown() override {
        // Shutdown the global system
        auto& system = GlobalComputeNodeSchedulerSystem::getInstance();
        system.shutdown();
    }
};

TEST_F(ComputeNodeSchedulerSystemTest, TestSystemInitialization) {
    auto& system = GlobalComputeNodeSchedulerSystem::getInstance();
    
    EXPECT_TRUE(system.isInitialized()) << "System should be initialized";
    
    // Test component access
    auto schedulerManager = system.getSchedulerManager();
    EXPECT_NE(schedulerManager, nullptr) << "Scheduler manager should not be null";
}

TEST_F(ComputeNodeSchedulerSystemTest, TestSchedulerCreation) {
    auto& system = GlobalComputeNodeSchedulerSystem::getInstance();
    
    // Create scheduler configuration
    SchedulerConfig config;
    config.schedulerId = "scheduler_1";
    config.type = SchedulerType::FIFO;
    config.maxQueueSize = 100;
    config.maxConcurrentTasks = 10;
    config.taskTimeout = std::chrono::milliseconds(5000);
    config.enableLoadBalancing = true;
    config.enableAutoScaling = true;
    config.createdAt = std::chrono::system_clock::now();
    
    // Create scheduler
    auto scheduler = system.createScheduler(config);
    EXPECT_NE(scheduler, nullptr) << "Scheduler should be created";
    
    if (scheduler) {
        EXPECT_EQ(scheduler->getSchedulerId(), config.schedulerId) << "Scheduler ID should match";
        EXPECT_TRUE(scheduler->isInitialized()) << "Scheduler should be initialized";
        EXPECT_EQ(scheduler->getSchedulerType(), config.type) << "Scheduler type should match";
    }
}

TEST_F(ComputeNodeSchedulerSystemTest, TestTaskExecution) {
    auto& system = GlobalComputeNodeSchedulerSystem::getInstance();
    
    // Create scheduler first
    SchedulerConfig config;
    config.schedulerId = "scheduler_2";
    config.type = SchedulerType::FIFO;
    config.maxQueueSize = 100;
    config.maxConcurrentTasks = 10;
    config.taskTimeout = std::chrono::milliseconds(5000);
    config.enableLoadBalancing = true;
    config.enableAutoScaling = true;
    config.createdAt = std::chrono::system_clock::now();
    
    auto scheduler = system.createScheduler(config);
    ASSERT_NE(scheduler, nullptr) << "Scheduler should be created";
    
    // Register compute node
    ComputeNodeInfo nodeInfo;
    nodeInfo.nodeId = "node_1";
    nodeInfo.nodeName = "Compute Node 1";
    nodeInfo.nodeType = "GPU";
    nodeInfo.totalCores = 8;
    nodeInfo.availableCores = 8;
    nodeInfo.totalMemory = 16 * 1024 * 1024 * 1024; // 16GB
    nodeInfo.availableMemory = 16 * 1024 * 1024 * 1024; // 16GB
    nodeInfo.cpuUtilization = 0.0f;
    nodeInfo.memoryUtilization = 0.0f;
    nodeInfo.activeTasks = 0;
    nodeInfo.maxTasks = 10;
    nodeInfo.isOnline = true;
    nodeInfo.lastUpdated = std::chrono::system_clock::now();
    
    EXPECT_TRUE(scheduler->registerNode(nodeInfo)) << "Node registration should succeed";
    
    // Create task
    TaskExecutionRequest request;
    request.requestId = "request_1";
    request.taskId = "task_1";
    request.taskFunction = []() { /* Simulate task execution */ };
    request.dependencies = {};
    request.priority = TaskPriority::NORMAL;
    request.weight = 0.5f;
    request.timeout = std::chrono::milliseconds(5000);
    request.createdAt = std::chrono::system_clock::now();
    
    // Execute task
    auto result = system.submitTask(request);
    EXPECT_TRUE(result.success) << "Task execution should succeed";
    EXPECT_EQ(result.taskId, request.taskId) << "Task ID should match";
    EXPECT_GT(result.executionTime, 0.0f) << "Execution time should be positive";
    EXPECT_GE(result.cpuUtilization, 0.0f) << "CPU utilization should be non-negative";
    EXPECT_GE(result.memoryUtilization, 0.0f) << "Memory utilization should be non-negative";
}

TEST_F(ComputeNodeSchedulerSystemTest, TestAsyncTaskExecution) {
    auto& system = GlobalComputeNodeSchedulerSystem::getInstance();
    
    // Create scheduler first
    SchedulerConfig config;
    config.schedulerId = "scheduler_3";
    config.type = SchedulerType::PRIORITY;
    config.maxQueueSize = 100;
    config.maxConcurrentTasks = 10;
    config.taskTimeout = std::chrono::milliseconds(5000);
    config.enableLoadBalancing = true;
    config.enableAutoScaling = true;
    config.createdAt = std::chrono::system_clock::now();
    
    auto scheduler = system.createScheduler(config);
    ASSERT_NE(scheduler, nullptr) << "Scheduler should be created";
    
    // Register compute node
    ComputeNodeInfo nodeInfo;
    nodeInfo.nodeId = "node_2";
    nodeInfo.nodeName = "Compute Node 2";
    nodeInfo.nodeType = "GPU";
    nodeInfo.totalCores = 8;
    nodeInfo.availableCores = 8;
    nodeInfo.totalMemory = 16 * 1024 * 1024 * 1024; // 16GB
    nodeInfo.availableMemory = 16 * 1024 * 1024 * 1024; // 16GB
    nodeInfo.cpuUtilization = 0.0f;
    nodeInfo.memoryUtilization = 0.0f;
    nodeInfo.activeTasks = 0;
    nodeInfo.maxTasks = 10;
    nodeInfo.isOnline = true;
    nodeInfo.lastUpdated = std::chrono::system_clock::now();
    
    EXPECT_TRUE(scheduler->registerNode(nodeInfo)) << "Node registration should succeed";
    
    // Create task
    TaskExecutionRequest request;
    request.requestId = "request_2";
    request.taskId = "task_2";
    request.taskFunction = []() { /* Simulate task execution */ };
    request.dependencies = {};
    request.priority = TaskPriority::HIGH;
    request.weight = 0.8f;
    request.timeout = std::chrono::milliseconds(5000);
    request.createdAt = std::chrono::system_clock::now();
    
    // Execute async task
    auto future = system.submitTaskAsync(request);
    EXPECT_TRUE(future.valid()) << "Future should be valid";
    
    // Wait for completion
    auto result = future.get();
    EXPECT_TRUE(result.success) << "Async task execution should succeed";
    EXPECT_EQ(result.taskId, request.taskId) << "Task ID should match";
    EXPECT_GT(result.executionTime, 0.0f) << "Execution time should be positive";
    EXPECT_GE(result.cpuUtilization, 0.0f) << "CPU utilization should be non-negative";
    EXPECT_GE(result.memoryUtilization, 0.0f) << "Memory utilization should be non-negative";
}

TEST_F(ComputeNodeSchedulerSystemTest, TestSchedulerManagement) {
    auto& system = GlobalComputeNodeSchedulerSystem::getInstance();
    
    // Create multiple schedulers
    std::vector<std::string> schedulerIds;
    for (int i = 0; i < 4; ++i) {
        SchedulerConfig config;
        config.schedulerId = "scheduler_" + std::to_string(i + 4);
        config.type = SchedulerType::FIFO;
        config.maxQueueSize = 100;
        config.maxConcurrentTasks = 10;
        config.taskTimeout = std::chrono::milliseconds(5000);
        config.enableLoadBalancing = true;
        config.enableAutoScaling = true;
        config.createdAt = std::chrono::system_clock::now();
        
        auto scheduler = system.createScheduler(config);
        ASSERT_NE(scheduler, nullptr) << "Scheduler " << i << " should be created";
        schedulerIds.push_back(config.schedulerId);
    }
    
    // Test scheduler retrieval
    for (const auto& schedulerId : schedulerIds) {
        auto scheduler = system.getScheduler(schedulerId);
        EXPECT_NE(scheduler, nullptr) << "Scheduler " << schedulerId << " should be retrievable";
        EXPECT_EQ(scheduler->getSchedulerId(), schedulerId) << "Scheduler ID should match";
    }
    
    // Test getting all schedulers
    auto allSchedulers = system.getAllSchedulers();
    EXPECT_GE(allSchedulers.size(), 4) << "Should have at least 4 schedulers";
    
    // Test scheduler destruction
    for (const auto& schedulerId : schedulerIds) {
        bool destroyed = system.destroyScheduler(schedulerId);
        EXPECT_TRUE(destroyed) << "Scheduler " << schedulerId << " should be destroyed";
    }
}

TEST_F(ComputeNodeSchedulerSystemTest, TestComputeNodeManagement) {
    auto& system = GlobalComputeNodeSchedulerSystem::getInstance();
    
    // Create scheduler first
    SchedulerConfig config;
    config.schedulerId = "scheduler_8";
    config.type = SchedulerType::WEIGHTED;
    config.maxQueueSize = 100;
    config.maxConcurrentTasks = 10;
    config.taskTimeout = std::chrono::milliseconds(5000);
    config.enableLoadBalancing = true;
    config.enableAutoScaling = true;
    config.createdAt = std::chrono::system_clock::now();
    
    auto scheduler = system.createScheduler(config);
    ASSERT_NE(scheduler, nullptr) << "Scheduler should be created";
    
    // Register compute nodes
    std::vector<ComputeNodeInfo> nodes;
    for (int i = 0; i < 4; ++i) {
        ComputeNodeInfo nodeInfo;
        nodeInfo.nodeId = "node_" + std::to_string(i + 1);
        nodeInfo.nodeName = "Compute Node " + std::to_string(i + 1);
        nodeInfo.nodeType = "GPU";
        nodeInfo.totalCores = 8;
        nodeInfo.availableCores = 8;
        nodeInfo.totalMemory = 16 * 1024 * 1024 * 1024; // 16GB
        nodeInfo.availableMemory = 16 * 1024 * 1024 * 1024; // 16GB
        nodeInfo.cpuUtilization = 0.0f;
        nodeInfo.memoryUtilization = 0.0f;
        nodeInfo.activeTasks = 0;
        nodeInfo.maxTasks = 10;
        nodeInfo.isOnline = true;
        nodeInfo.lastUpdated = std::chrono::system_clock::now();
        
        EXPECT_TRUE(scheduler->registerNode(nodeInfo)) << "Node " << i << " registration should succeed";
        nodes.push_back(nodeInfo);
    }
    
    // Test node retrieval
    for (const auto& node : nodes) {
        auto nodeInfo = scheduler->getNodeInfo(node.nodeId);
        EXPECT_EQ(nodeInfo.nodeId, node.nodeId) << "Node ID should match";
        EXPECT_EQ(nodeInfo.nodeName, node.nodeName) << "Node name should match";
    }
    
    // Test getting available nodes
    auto availableNodes = scheduler->getAvailableNodes();
    EXPECT_GE(availableNodes.size(), 4) << "Should have at least 4 available nodes";
    
    // Test node unregistration
    for (const auto& node : nodes) {
        bool unregistered = scheduler->unregisterNode(node.nodeId);
        EXPECT_TRUE(unregistered) << "Node " << node.nodeId << " should be unregistered";
    }
}

TEST_F(ComputeNodeSchedulerSystemTest, TestPerformanceMonitoring) {
    auto& system = GlobalComputeNodeSchedulerSystem::getInstance();
    
    // Create scheduler first
    SchedulerConfig config;
    config.schedulerId = "scheduler_9";
    config.type = SchedulerType::LEAST_LOADED;
    config.maxQueueSize = 100;
    config.maxConcurrentTasks = 10;
    config.taskTimeout = std::chrono::milliseconds(5000);
    config.enableLoadBalancing = true;
    config.enableAutoScaling = true;
    config.createdAt = std::chrono::system_clock::now();
    
    auto scheduler = system.createScheduler(config);
    ASSERT_NE(scheduler, nullptr) << "Scheduler should be created";
    
    // Enable profiling
    EXPECT_TRUE(scheduler->enableProfiling()) << "Profiling should be enabled";
    
    // Get performance metrics
    auto metrics = scheduler->getPerformanceMetrics();
    EXPECT_FALSE(metrics.empty()) << "Performance metrics should not be empty";
    EXPECT_GE(metrics["utilization"], 0.0) << "Utilization should be non-negative";
    EXPECT_GE(metrics["queue_size"], 0.0) << "Queue size should be non-negative";
    EXPECT_GE(metrics["active_tasks"], 0.0) << "Active tasks should be non-negative";
    EXPECT_GE(metrics["completed_tasks"], 0.0) << "Completed tasks should be non-negative";
    EXPECT_GE(metrics["failed_tasks"], 0.0) << "Failed tasks should be non-negative";
    EXPECT_GE(metrics["average_execution_time"], 0.0) << "Average execution time should be non-negative";
    
    // Get profiling data
    auto profilingData = scheduler->getProfilingData();
    EXPECT_FALSE(profilingData.empty()) << "Profiling data should not be empty";
    EXPECT_GE(profilingData["utilization"], 0.0) << "Profiling utilization should be non-negative";
    EXPECT_GE(profilingData["queue_size"], 0.0) << "Profiling queue size should be non-negative";
    EXPECT_GE(profilingData["active_tasks"], 0.0) << "Profiling active tasks should be non-negative";
    EXPECT_GE(profilingData["completed_tasks"], 0.0) << "Profiling completed tasks should be non-negative";
    EXPECT_GE(profilingData["failed_tasks"], 0.0) << "Profiling failed tasks should be non-negative";
    EXPECT_GE(profilingData["average_execution_time"], 0.0) << "Profiling average execution time should be non-negative";
    EXPECT_GE(profilingData["registered_nodes"], 0.0) << "Registered nodes should be non-negative";
    EXPECT_GE(profilingData["available_nodes"], 0.0) << "Available nodes should be non-negative";
    EXPECT_GE(profilingData["scheduler_type"], 0.0) << "Scheduler type should be non-negative";
    EXPECT_GE(profilingData["max_queue_size"], 0.0) << "Max queue size should be non-negative";
    EXPECT_GE(profilingData["max_concurrent_tasks"], 0.0) << "Max concurrent tasks should be non-negative";
    
    // Get utilization
    float utilization = scheduler->getUtilization();
    EXPECT_GE(utilization, 0.0f) << "Utilization should be non-negative";
    EXPECT_LE(utilization, 1.0f) << "Utilization should not exceed 1.0";
    
    // Disable profiling
    EXPECT_TRUE(scheduler->disableProfiling()) << "Profiling should be disabled";
}

TEST_F(ComputeNodeSchedulerSystemTest, TestSystemMetrics) {
    auto& system = GlobalComputeNodeSchedulerSystem::getInstance();
    
    // Get system metrics
    auto metrics = system.getSystemMetrics();
    EXPECT_FALSE(metrics.empty()) << "System metrics should not be empty";
    EXPECT_GT(metrics["total_schedulers"], 0.0) << "Total schedulers should be positive";
    EXPECT_GE(metrics["active_tasks"], 0.0) << "Active tasks should be non-negative";
    EXPECT_GE(metrics["average_utilization"], 0.0) << "Average utilization should be non-negative";
    EXPECT_EQ(metrics["system_initialized"], 1.0) << "System should be initialized";
    EXPECT_GT(metrics["configuration_items"], 0.0) << "Configuration items should be positive";
}

TEST_F(ComputeNodeSchedulerSystemTest, TestSystemConfiguration) {
    auto& system = GlobalComputeNodeSchedulerSystem::getInstance();
    
    // Test system configuration
    std::map<std::string, std::string> config = {
        {"max_schedulers", "20"},
        {"scheduling_strategy", "optimized"},
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

TEST_F(ComputeNodeSchedulerSystemTest, TestAdvancedSchedulerFeatures) {
    auto& system = GlobalComputeNodeSchedulerSystem::getInstance();
    
    // Create scheduler first
    SchedulerConfig config;
    config.schedulerId = "scheduler_10";
    config.type = SchedulerType::CUSTOM;
    config.maxQueueSize = 100;
    config.maxConcurrentTasks = 10;
    config.taskTimeout = std::chrono::milliseconds(5000);
    config.enableLoadBalancing = true;
    config.enableAutoScaling = true;
    config.createdAt = std::chrono::system_clock::now();
    
    auto scheduler = system.createScheduler(config);
    ASSERT_NE(scheduler, nullptr) << "Scheduler should be created";
    
    // Cast to advanced scheduler
    auto advancedScheduler = std::dynamic_pointer_cast<AdvancedComputeNodeScheduler>(scheduler);
    ASSERT_NE(advancedScheduler, nullptr) << "Scheduler should be an advanced scheduler";
    
    // Test advanced features
    EXPECT_TRUE(advancedScheduler->optimizeScheduling()) << "Scheduling optimization should succeed";
    EXPECT_TRUE(advancedScheduler->balanceLoad()) << "Load balancing should succeed";
    EXPECT_TRUE(advancedScheduler->scaleNodes()) << "Node scaling should succeed";
    
    // Test scheduler info
    auto schedulerInfo = advancedScheduler->getSchedulerInfo();
    EXPECT_FALSE(schedulerInfo.empty()) << "Scheduler info should not be empty";
    EXPECT_EQ(schedulerInfo["scheduler_id"], config.schedulerId) << "Scheduler ID should match";
    EXPECT_EQ(schedulerInfo["scheduler_type"], std::to_string(static_cast<int>(config.type))) << "Scheduler type should match";
    
    // Test configuration validation
    EXPECT_TRUE(advancedScheduler->validateConfiguration()) << "Configuration validation should succeed";
    
    // Test task weight management
    EXPECT_TRUE(advancedScheduler->setTaskWeight("task_1", 0.8f)) << "Task weight setting should succeed";
    EXPECT_EQ(advancedScheduler->getTaskWeight("task_1"), 0.8f) << "Task weight should match";
    
    // Test node capacity management
    EXPECT_TRUE(advancedScheduler->setNodeCapacity("node_1", 20)) << "Node capacity setting should succeed";
    EXPECT_EQ(advancedScheduler->getNodeCapacity("node_1"), 20) << "Node capacity should match";
}

TEST_F(ComputeNodeSchedulerSystemTest, TestSchedulerManagerFeatures) {
    auto& system = GlobalComputeNodeSchedulerSystem::getInstance();
    
    auto schedulerManager = system.getSchedulerManager();
    ASSERT_NE(schedulerManager, nullptr) << "Scheduler manager should not be null";
    
    // Test scheduler manager operations
    EXPECT_TRUE(schedulerManager->optimizeSystem()) << "System optimization should succeed";
    EXPECT_TRUE(schedulerManager->balanceLoad()) << "Load balancing should succeed";
    EXPECT_TRUE(schedulerManager->cleanupIdleSchedulers()) << "Idle scheduler cleanup should succeed";
    EXPECT_TRUE(schedulerManager->validateSystem()) << "System validation should succeed";
    
    // Test system metrics
    auto systemMetrics = schedulerManager->getSystemMetrics();
    EXPECT_FALSE(systemMetrics.empty()) << "System metrics should not be empty";
    EXPECT_GT(systemMetrics["total_schedulers"], 0.0) << "Total schedulers should be positive";
    
    // Test scheduler counts
    auto schedulerCounts = schedulerManager->getSchedulerCounts();
    EXPECT_FALSE(schedulerCounts.empty()) << "Scheduler counts should not be empty";
    EXPECT_GT(schedulerCounts["total"], 0) << "Total scheduler count should be positive";
    
    // Test task metrics
    auto taskMetrics = schedulerManager->getTaskMetrics();
    EXPECT_FALSE(taskMetrics.empty()) << "Task metrics should not be empty";
    EXPECT_GE(taskMetrics["total_tasks"], 0.0) << "Total tasks should be non-negative";
    EXPECT_GE(taskMetrics["active_tasks"], 0.0) << "Active tasks should be non-negative";
    
    // Test system profiling
    EXPECT_TRUE(schedulerManager->enableSystemProfiling()) << "System profiling should be enabled";
    auto profilingData = schedulerManager->getSystemProfilingData();
    EXPECT_FALSE(profilingData.empty()) << "System profiling data should not be empty";
    EXPECT_TRUE(schedulerManager->disableSystemProfiling()) << "System profiling should be disabled";
}

TEST_F(ComputeNodeSchedulerSystemTest, TestSchedulerTypes) {
    auto& system = GlobalComputeNodeSchedulerSystem::getInstance();
    
    // Test different scheduler types
    std::vector<SchedulerType> types = {
        SchedulerType::FIFO,
        SchedulerType::PRIORITY,
        SchedulerType::WEIGHTED,
        SchedulerType::ROUND_ROBIN,
        SchedulerType::LEAST_LOADED,
        SchedulerType::CUSTOM
    };
    
    for (const auto& type : types) {
        SchedulerConfig config;
        config.schedulerId = "scheduler_type_test_" + std::to_string(static_cast<int>(type));
        config.type = type;
        config.maxQueueSize = 100;
        config.maxConcurrentTasks = 10;
        config.taskTimeout = std::chrono::milliseconds(5000);
        config.enableLoadBalancing = true;
        config.enableAutoScaling = true;
        config.createdAt = std::chrono::system_clock::now();
        
        auto scheduler = system.createScheduler(config);
        EXPECT_NE(scheduler, nullptr) << "Scheduler for type " << static_cast<int>(type) << " should be created";
        
        if (scheduler) {
            EXPECT_EQ(scheduler->getSchedulerType(), type) << "Scheduler type should match";
        }
    }
}

TEST_F(ComputeNodeSchedulerSystemTest, TestTaskPriorities) {
    auto& system = GlobalComputeNodeSchedulerSystem::getInstance();
    
    // Create scheduler first
    SchedulerConfig config;
    config.schedulerId = "scheduler_11";
    config.type = SchedulerType::PRIORITY;
    config.maxQueueSize = 100;
    config.maxConcurrentTasks = 10;
    config.taskTimeout = std::chrono::milliseconds(5000);
    config.enableLoadBalancing = true;
    config.enableAutoScaling = true;
    config.createdAt = std::chrono::system_clock::now();
    
    auto scheduler = system.createScheduler(config);
    ASSERT_NE(scheduler, nullptr) << "Scheduler should be created";
    
    // Register compute node
    ComputeNodeInfo nodeInfo;
    nodeInfo.nodeId = "node_1";
    nodeInfo.nodeName = "Compute Node 1";
    nodeInfo.nodeType = "GPU";
    nodeInfo.totalCores = 8;
    nodeInfo.availableCores = 8;
    nodeInfo.totalMemory = 16 * 1024 * 1024 * 1024; // 16GB
    nodeInfo.availableMemory = 16 * 1024 * 1024 * 1024; // 16GB
    nodeInfo.cpuUtilization = 0.0f;
    nodeInfo.memoryUtilization = 0.0f;
    nodeInfo.activeTasks = 0;
    nodeInfo.maxTasks = 10;
    nodeInfo.isOnline = true;
    nodeInfo.lastUpdated = std::chrono::system_clock::now();
    
    EXPECT_TRUE(scheduler->registerNode(nodeInfo)) << "Node registration should succeed";
    
    // Test different task priorities
    std::vector<TaskPriority> priorities = {
        TaskPriority::LOW,
        TaskPriority::NORMAL,
        TaskPriority::HIGH,
        TaskPriority::CRITICAL,
        TaskPriority::URGENT
    };
    
    for (const auto& priority : priorities) {
        TaskExecutionRequest request;
        request.requestId = "request_priority_test_" + std::to_string(static_cast<int>(priority));
        request.taskId = "task_priority_test_" + std::to_string(static_cast<int>(priority));
        request.taskFunction = []() { /* Simulate task execution */ };
        request.dependencies = {};
        request.priority = priority;
        request.weight = 0.5f;
        request.timeout = std::chrono::milliseconds(5000);
        request.createdAt = std::chrono::system_clock::now();
        
        auto result = system.submitTask(request);
        EXPECT_TRUE(result.success) << "Task with priority " << static_cast<int>(priority) << " should succeed";
        EXPECT_EQ(result.taskId, request.taskId) << "Task ID should match";
        EXPECT_GT(result.executionTime, 0.0f) << "Execution time should be positive";
    }
}

TEST_F(ComputeNodeSchedulerSystemTest, TestTaskStatusManagement) {
    auto& system = GlobalComputeNodeSchedulerSystem::getInstance();
    
    // Create scheduler first
    SchedulerConfig config;
    config.schedulerId = "scheduler_12";
    config.type = SchedulerType::FIFO;
    config.maxQueueSize = 100;
    config.maxConcurrentTasks = 10;
    config.taskTimeout = std::chrono::milliseconds(5000);
    config.enableLoadBalancing = true;
    config.enableAutoScaling = true;
    config.createdAt = std::chrono::system_clock::now();
    
    auto scheduler = system.createScheduler(config);
    ASSERT_NE(scheduler, nullptr) << "Scheduler should be created";
    
    // Register compute node
    ComputeNodeInfo nodeInfo;
    nodeInfo.nodeId = "node_1";
    nodeInfo.nodeName = "Compute Node 1";
    nodeInfo.nodeType = "GPU";
    nodeInfo.totalCores = 8;
    nodeInfo.availableCores = 8;
    nodeInfo.totalMemory = 16 * 1024 * 1024 * 1024; // 16GB
    nodeInfo.availableMemory = 16 * 1024 * 1024 * 1024; // 16GB
    nodeInfo.cpuUtilization = 0.0f;
    nodeInfo.memoryUtilization = 0.0f;
    nodeInfo.activeTasks = 0;
    nodeInfo.maxTasks = 10;
    nodeInfo.isOnline = true;
    nodeInfo.lastUpdated = std::chrono::system_clock::now();
    
    EXPECT_TRUE(scheduler->registerNode(nodeInfo)) << "Node registration should succeed";
    
    // Create task
    TaskExecutionRequest request;
    request.requestId = "request_1";
    request.taskId = "task_1";
    request.taskFunction = []() { /* Simulate task execution */ };
    request.dependencies = {};
    request.priority = TaskPriority::NORMAL;
    request.weight = 0.5f;
    request.timeout = std::chrono::milliseconds(5000);
    request.createdAt = std::chrono::system_clock::now();
    
    // Submit task
    auto result = system.submitTask(request);
    EXPECT_TRUE(result.success) << "Task submission should succeed";
    
    // Test task status management
    EXPECT_TRUE(scheduler->isTaskActive(request.taskId)) << "Task should be active";
    
    // Test task suspension
    EXPECT_TRUE(scheduler->suspendTask(request.taskId)) << "Task suspension should succeed";
    
    // Test task resumption
    EXPECT_TRUE(scheduler->resumeTask(request.taskId)) << "Task resumption should succeed";
    
    // Test task cancellation
    EXPECT_TRUE(scheduler->cancelTask(request.taskId)) << "Task cancellation should succeed";
    
    // Test getting active tasks
    auto activeTasks = scheduler->getActiveTasks();
    EXPECT_FALSE(activeTasks.empty()) << "Should have active tasks";
}

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    
    // Set up logging
    spdlog::set_level(spdlog::level::info);
    
    return RUN_ALL_TESTS();
}
