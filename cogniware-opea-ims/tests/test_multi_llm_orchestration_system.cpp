#include <gtest/gtest.h>
#include <spdlog/spdlog.h>
#include "orchestration/multi_llm_orchestrator.h"
#include <chrono>
#include <thread>

using namespace cogniware::orchestration;

class MultiLLMOrchestrationSystemTest : public ::testing::Test {
protected:
    void SetUp() override {
        spdlog::set_level(spdlog::level::debug);
        
        // Initialize the global system
        auto& system = GlobalMultiLLMOrchestrationSystem::getInstance();
        ASSERT_TRUE(system.initialize()) << "Failed to initialize global multi-LLM orchestration system";
    }
    
    void TearDown() override {
        // Shutdown the global system
        auto& system = GlobalMultiLLMOrchestrationSystem::getInstance();
        system.shutdown();
    }
};

TEST_F(MultiLLMOrchestrationSystemTest, TestSystemInitialization) {
    auto& system = GlobalMultiLLMOrchestrationSystem::getInstance();
    
    EXPECT_TRUE(system.isInitialized()) << "System should be initialized";
    
    // Test component access
    auto orchestratorManager = system.getOrchestratorManager();
    EXPECT_NE(orchestratorManager, nullptr) << "Orchestrator manager should not be null";
}

TEST_F(MultiLLMOrchestrationSystemTest, TestOrchestratorCreation) {
    auto& system = GlobalMultiLLMOrchestrationSystem::getInstance();
    
    // Create orchestrator configuration
    OrchestrationConfig config;
    config.orchestratorId = "orchestrator_1";
    config.type = OrchestrationType::PARALLEL;
    config.maxConcurrentLLMs = 4;
    config.maxQueueSize = 100;
    config.timeout = std::chrono::milliseconds(5000);
    config.enableLoadBalancing = true;
    config.enableResultAggregation = true;
    config.createdAt = std::chrono::system_clock::now();
    
    // Create orchestrator
    auto orchestrator = system.createOrchestrator(config);
    EXPECT_NE(orchestrator, nullptr) << "Orchestrator should be created";
    
    if (orchestrator) {
        EXPECT_EQ(orchestrator->getOrchestratorId(), config.orchestratorId) << "Orchestrator ID should match";
        EXPECT_TRUE(orchestrator->isInitialized()) << "Orchestrator should be initialized";
        EXPECT_EQ(orchestrator->getOrchestrationType(), config.type) << "Orchestration type should match";
    }
}

TEST_F(MultiLLMOrchestrationSystemTest, TestLLMRegistration) {
    auto& system = GlobalMultiLLMOrchestrationSystem::getInstance();
    
    // Create orchestrator first
    OrchestrationConfig config;
    config.orchestratorId = "orchestrator_2";
    config.type = OrchestrationType::PARALLEL;
    config.maxConcurrentLLMs = 4;
    config.maxQueueSize = 100;
    config.timeout = std::chrono::milliseconds(5000);
    config.enableLoadBalancing = true;
    config.enableResultAggregation = true;
    config.createdAt = std::chrono::system_clock::now();
    
    auto orchestrator = system.createOrchestrator(config);
    ASSERT_NE(orchestrator, nullptr) << "Orchestrator should be created";
    
    // Register LLM instances
    std::vector<LLMInstance> llmInstances;
    for (int i = 0; i < 4; ++i) {
        LLMInstance llmInstance;
        llmInstance.llmId = "llm_" + std::to_string(i + 1);
        llmInstance.modelName = "Test Model " + std::to_string(i + 1);
        llmInstance.modelPath = "/path/to/model" + std::to_string(i + 1);
        llmInstance.status = LLMStatus::READY;
        llmInstance.utilization = 0.0f;
        llmInstance.activeTasks = 0;
        llmInstance.maxTasks = 10;
        llmInstance.lastUpdated = std::chrono::system_clock::now();
        
        bool registered = orchestrator->registerLLM(llmInstance);
        EXPECT_TRUE(registered) << "LLM " << llmInstance.llmId << " should be registered";
        
        if (registered) {
            llmInstances.push_back(llmInstance);
        }
    }
    
    // Test LLM retrieval
    auto registeredLLMs = orchestrator->getRegisteredLLMs();
    EXPECT_EQ(registeredLLMs.size(), llmInstances.size()) << "All LLMs should be registered";
    
    for (const auto& llmInstance : llmInstances) {
        auto retrievedLLM = orchestrator->getLLMInstance(llmInstance.llmId);
        EXPECT_EQ(retrievedLLM.llmId, llmInstance.llmId) << "LLM ID should match";
        EXPECT_EQ(retrievedLLM.modelName, llmInstance.modelName) << "Model name should match";
        EXPECT_EQ(retrievedLLM.status, llmInstance.status) << "Status should match";
    }
}

TEST_F(MultiLLMOrchestrationSystemTest, TestRequestProcessing) {
    auto& system = GlobalMultiLLMOrchestrationSystem::getInstance();
    
    // Create orchestrator first
    OrchestrationConfig config;
    config.orchestratorId = "orchestrator_3";
    config.type = OrchestrationType::PARALLEL;
    config.maxConcurrentLLMs = 4;
    config.maxQueueSize = 100;
    config.timeout = std::chrono::milliseconds(5000);
    config.enableLoadBalancing = true;
    config.enableResultAggregation = true;
    config.createdAt = std::chrono::system_clock::now();
    
    auto orchestrator = system.createOrchestrator(config);
    ASSERT_NE(orchestrator, nullptr) << "Orchestrator should be created";
    
    // Register LLM instances
    for (int i = 0; i < 4; ++i) {
        LLMInstance llmInstance;
        llmInstance.llmId = "llm_" + std::to_string(i + 1);
        llmInstance.modelName = "Test Model " + std::to_string(i + 1);
        llmInstance.modelPath = "/path/to/model" + std::to_string(i + 1);
        llmInstance.status = LLMStatus::READY;
        llmInstance.utilization = 0.0f;
        llmInstance.activeTasks = 0;
        llmInstance.maxTasks = 10;
        llmInstance.lastUpdated = std::chrono::system_clock::now();
        
        orchestrator->registerLLM(llmInstance);
    }
    
    // Test request processing
    std::string requestId = "request_1";
    std::string prompt = "Test prompt for multi-LLM orchestration";
    std::map<std::string, std::string> parameters = {
        {"temperature", "0.7"},
        {"max_tokens", "100"},
        {"top_p", "0.9"}
    };
    
    auto result = orchestrator->processRequest(requestId, prompt, parameters);
    EXPECT_FALSE(result.requestId.empty()) << "Request ID should not be empty";
    EXPECT_GT(result.confidence, 0.0f) << "Confidence should be positive";
    EXPECT_FALSE(result.responses.empty()) << "Responses should not be empty";
    EXPECT_FALSE(result.aggregatedResponse.empty()) << "Aggregated response should not be empty";
}

TEST_F(MultiLLMOrchestrationSystemTest, TestAsyncRequestProcessing) {
    auto& system = GlobalMultiLLMOrchestrationSystem::getInstance();
    
    // Create orchestrator first
    OrchestrationConfig config;
    config.orchestratorId = "orchestrator_4";
    config.type = OrchestrationType::PARALLEL;
    config.maxConcurrentLLMs = 4;
    config.maxQueueSize = 100;
    config.timeout = std::chrono::milliseconds(5000);
    config.enableLoadBalancing = true;
    config.enableResultAggregation = true;
    config.createdAt = std::chrono::system_clock::now();
    
    auto orchestrator = system.createOrchestrator(config);
    ASSERT_NE(orchestrator, nullptr) << "Orchestrator should be created";
    
    // Register LLM instances
    for (int i = 0; i < 4; ++i) {
        LLMInstance llmInstance;
        llmInstance.llmId = "llm_" + std::to_string(i + 1);
        llmInstance.modelName = "Test Model " + std::to_string(i + 1);
        llmInstance.modelPath = "/path/to/model" + std::to_string(i + 1);
        llmInstance.status = LLMStatus::READY;
        llmInstance.utilization = 0.0f;
        llmInstance.activeTasks = 0;
        llmInstance.maxTasks = 10;
        llmInstance.lastUpdated = std::chrono::system_clock::now();
        
        orchestrator->registerLLM(llmInstance);
    }
    
    // Test async request processing
    std::string requestId = "async_request_1";
    std::string prompt = "Test async prompt for multi-LLM orchestration";
    std::map<std::string, std::string> parameters = {
        {"temperature", "0.7"},
        {"max_tokens", "100"},
        {"top_p", "0.9"}
    };
    
    auto future = orchestrator->processRequestAsync(requestId, prompt, parameters);
    EXPECT_TRUE(future.valid()) << "Future should be valid";
    
    // Wait for completion
    auto result = future.get();
    EXPECT_FALSE(result.requestId.empty()) << "Request ID should not be empty";
    EXPECT_GT(result.confidence, 0.0f) << "Confidence should be positive";
    EXPECT_FALSE(result.responses.empty()) << "Responses should not be empty";
    EXPECT_FALSE(result.aggregatedResponse.empty()) << "Aggregated response should not be empty";
}

TEST_F(MultiLLMOrchestrationSystemTest, TestRequestCancellation) {
    auto& system = GlobalMultiLLMOrchestrationSystem::getInstance();
    
    // Create orchestrator first
    OrchestrationConfig config;
    config.orchestratorId = "orchestrator_5";
    config.type = OrchestrationType::PARALLEL;
    config.maxConcurrentLLMs = 4;
    config.maxQueueSize = 100;
    config.timeout = std::chrono::milliseconds(5000);
    config.enableLoadBalancing = true;
    config.enableResultAggregation = true;
    config.createdAt = std::chrono::system_clock::now();
    
    auto orchestrator = system.createOrchestrator(config);
    ASSERT_NE(orchestrator, nullptr) << "Orchestrator should be created";
    
    // Register LLM instances
    for (int i = 0; i < 4; ++i) {
        LLMInstance llmInstance;
        llmInstance.llmId = "llm_" + std::to_string(i + 1);
        llmInstance.modelName = "Test Model " + std::to_string(i + 1);
        llmInstance.modelPath = "/path/to/model" + std::to_string(i + 1);
        llmInstance.status = LLMStatus::READY;
        llmInstance.utilization = 0.0f;
        llmInstance.activeTasks = 0;
        llmInstance.maxTasks = 10;
        llmInstance.lastUpdated = std::chrono::system_clock::now();
        
        orchestrator->registerLLM(llmInstance);
    }
    
    // Test request cancellation
    std::string requestId = "cancellable_request_1";
    std::string prompt = "Test prompt for cancellation";
    std::map<std::string, std::string> parameters = {
        {"temperature", "0.7"},
        {"max_tokens", "100"},
        {"top_p", "0.9"}
    };
    
    // Start async request
    auto future = orchestrator->processRequestAsync(requestId, prompt, parameters);
    EXPECT_TRUE(future.valid()) << "Future should be valid";
    
    // Cancel request
    bool cancelled = orchestrator->cancelRequest(requestId);
    EXPECT_TRUE(cancelled) << "Request should be cancelled";
    
    // Check if request is no longer active
    bool isActive = orchestrator->isRequestActive(requestId);
    EXPECT_FALSE(isActive) << "Request should not be active after cancellation";
}

TEST_F(MultiLLMOrchestrationSystemTest, TestPerformanceMonitoring) {
    auto& system = GlobalMultiLLMOrchestrationSystem::getInstance();
    
    // Create orchestrator first
    OrchestrationConfig config;
    config.orchestratorId = "orchestrator_6";
    config.type = OrchestrationType::PARALLEL;
    config.maxConcurrentLLMs = 4;
    config.maxQueueSize = 100;
    config.timeout = std::chrono::milliseconds(5000);
    config.enableLoadBalancing = true;
    config.enableResultAggregation = true;
    config.createdAt = std::chrono::system_clock::now();
    
    auto orchestrator = system.createOrchestrator(config);
    ASSERT_NE(orchestrator, nullptr) << "Orchestrator should be created";
    
    // Enable profiling
    EXPECT_TRUE(orchestrator->enableProfiling()) << "Profiling should be enabled";
    
    // Get performance metrics
    auto metrics = orchestrator->getPerformanceMetrics();
    EXPECT_FALSE(metrics.empty()) << "Performance metrics should not be empty";
    EXPECT_GE(metrics["utilization"], 0.0) << "Utilization should be non-negative";
    EXPECT_GE(metrics["active_requests"], 0.0) << "Active requests should be non-negative";
    EXPECT_GE(metrics["registered_llms"], 0.0) << "Registered LLMs should be non-negative";
    EXPECT_GE(metrics["completed_requests"], 0.0) << "Completed requests should be non-negative";
    EXPECT_GE(metrics["failed_requests"], 0.0) << "Failed requests should be non-negative";
    EXPECT_GE(metrics["average_response_time"], 0.0) << "Average response time should be non-negative";
    
    // Get profiling data
    auto profilingData = orchestrator->getProfilingData();
    EXPECT_FALSE(profilingData.empty()) << "Profiling data should not be empty";
    EXPECT_GE(profilingData["utilization"], 0.0) << "Profiling utilization should be non-negative";
    EXPECT_GE(profilingData["active_requests"], 0.0) << "Profiling active requests should be non-negative";
    EXPECT_GE(profilingData["registered_llms"], 0.0) << "Profiling registered LLMs should be non-negative";
    EXPECT_GE(profilingData["completed_requests"], 0.0) << "Profiling completed requests should be non-negative";
    EXPECT_GE(profilingData["failed_requests"], 0.0) << "Profiling failed requests should be non-negative";
    EXPECT_GE(profilingData["average_response_time"], 0.0) << "Profiling average response time should be non-negative";
    EXPECT_GE(profilingData["orchestration_type"], 0.0) << "Orchestration type should be non-negative";
    EXPECT_GE(profilingData["max_concurrent_llms"], 0.0) << "Max concurrent LLMs should be non-negative";
    EXPECT_GE(profilingData["max_queue_size"], 0.0) << "Max queue size should be non-negative";
    EXPECT_GE(profilingData["enable_load_balancing"], 0.0) << "Enable load balancing should be non-negative";
    EXPECT_GE(profilingData["enable_result_aggregation"], 0.0) << "Enable result aggregation should be non-negative";
    
    // Get utilization
    float utilization = orchestrator->getUtilization();
    EXPECT_GE(utilization, 0.0f) << "Utilization should be non-negative";
    EXPECT_LE(utilization, 1.0f) << "Utilization should not exceed 1.0";
    
    // Disable profiling
    EXPECT_TRUE(orchestrator->disableProfiling()) << "Profiling should be disabled";
}

TEST_F(MultiLLMOrchestrationSystemTest, TestSystemMetrics) {
    auto& system = GlobalMultiLLMOrchestrationSystem::getInstance();
    
    // Get system metrics
    auto metrics = system.getSystemMetrics();
    EXPECT_FALSE(metrics.empty()) << "System metrics should not be empty";
    EXPECT_GT(metrics["total_orchestrators"], 0.0) << "Total orchestrators should be positive";
    EXPECT_GE(metrics["active_requests"], 0.0) << "Active requests should be non-negative";
    EXPECT_GE(metrics["registered_llms"], 0.0) << "Registered LLMs should be non-negative";
    EXPECT_GE(metrics["average_utilization"], 0.0) << "Average utilization should be non-negative";
    EXPECT_EQ(metrics["system_initialized"], 1.0) << "System should be initialized";
    EXPECT_GT(metrics["configuration_items"], 0.0) << "Configuration items should be positive";
}

TEST_F(MultiLLMOrchestrationSystemTest, TestSystemConfiguration) {
    auto& system = GlobalMultiLLMOrchestrationSystem::getInstance();
    
    // Test system configuration
    std::map<std::string, std::string> config = {
        {"max_orchestrators", "20"},
        {"orchestration_strategy", "parallel"},
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

TEST_F(MultiLLMOrchestrationSystemTest, TestAdvancedOrchestratorFeatures) {
    auto& system = GlobalMultiLLMOrchestrationSystem::getInstance();
    
    // Create orchestrator first
    OrchestrationConfig config;
    config.orchestratorId = "orchestrator_7";
    config.type = OrchestrationType::PARALLEL;
    config.maxConcurrentLLMs = 4;
    config.maxQueueSize = 100;
    config.timeout = std::chrono::milliseconds(5000);
    config.enableLoadBalancing = true;
    config.enableResultAggregation = true;
    config.createdAt = std::chrono::system_clock::now();
    
    auto orchestrator = system.createOrchestrator(config);
    ASSERT_NE(orchestrator, nullptr) << "Orchestrator should be created";
    
    // Cast to advanced orchestrator
    auto advancedOrchestrator = std::dynamic_pointer_cast<AdvancedMultiLLMOrchestrator>(orchestrator);
    ASSERT_NE(advancedOrchestrator, nullptr) << "Orchestrator should be an advanced orchestrator";
    
    // Test advanced features
    EXPECT_TRUE(advancedOrchestrator->optimizeOrchestration()) << "Orchestration optimization should succeed";
    EXPECT_TRUE(advancedOrchestrator->balanceLoad()) << "Load balancing should succeed";
    EXPECT_TRUE(advancedOrchestrator->aggregateResults()) << "Result aggregation should succeed";
    
    // Test orchestrator info
    auto orchestratorInfo = advancedOrchestrator->getOrchestratorInfo();
    EXPECT_FALSE(orchestratorInfo.empty()) << "Orchestrator info should not be empty";
    EXPECT_EQ(orchestratorInfo["orchestrator_id"], config.orchestratorId) << "Orchestrator ID should match";
    EXPECT_EQ(orchestratorInfo["orchestration_type"], std::to_string(static_cast<int>(config.type))) << "Orchestration type should match";
    
    // Test configuration validation
    EXPECT_TRUE(advancedOrchestrator->validateConfiguration()) << "Configuration validation should succeed";
    
    // Test load balancing strategy
    EXPECT_TRUE(advancedOrchestrator->setLoadBalancingStrategy("least_loaded")) << "Load balancing strategy should be set";
    EXPECT_EQ(advancedOrchestrator->getLoadBalancingStrategy(), "least_loaded") << "Load balancing strategy should match";
    
    // Test result aggregation strategy
    EXPECT_TRUE(advancedOrchestrator->setResultAggregationStrategy("weighted_average")) << "Result aggregation strategy should be set";
    EXPECT_EQ(advancedOrchestrator->getResultAggregationStrategy(), "weighted_average") << "Result aggregation strategy should match";
}

TEST_F(MultiLLMOrchestrationSystemTest, TestOrchestratorManagerFeatures) {
    auto& system = GlobalMultiLLMOrchestrationSystem::getInstance();
    
    auto orchestratorManager = system.getOrchestratorManager();
    ASSERT_NE(orchestratorManager, nullptr) << "Orchestrator manager should not be null";
    
    // Test orchestrator manager operations
    EXPECT_TRUE(orchestratorManager->optimizeSystem()) << "System optimization should succeed";
    EXPECT_TRUE(orchestratorManager->balanceLoad()) << "Load balancing should succeed";
    EXPECT_TRUE(orchestratorManager->cleanupIdleOrchestrators()) << "Idle orchestrator cleanup should succeed";
    EXPECT_TRUE(orchestratorManager->validateSystem()) << "System validation should succeed";
    
    // Test system metrics
    auto systemMetrics = orchestratorManager->getSystemMetrics();
    EXPECT_FALSE(systemMetrics.empty()) << "System metrics should not be empty";
    EXPECT_GT(systemMetrics["total_orchestrators"], 0.0) << "Total orchestrators should be positive";
    
    // Test orchestrator counts
    auto orchestratorCounts = orchestratorManager->getOrchestratorCounts();
    EXPECT_FALSE(orchestratorCounts.empty()) << "Orchestrator counts should not be empty";
    EXPECT_GT(orchestratorCounts["total"], 0) << "Total orchestrator count should be positive";
    
    // Test request metrics
    auto requestMetrics = orchestratorManager->getRequestMetrics();
    EXPECT_FALSE(requestMetrics.empty()) << "Request metrics should not be empty";
    EXPECT_GE(requestMetrics["total_requests"], 0.0) << "Total requests should be non-negative";
    EXPECT_GE(requestMetrics["active_requests"], 0.0) << "Active requests should be non-negative";
    
    // Test system profiling
    EXPECT_TRUE(orchestratorManager->enableSystemProfiling()) << "System profiling should be enabled";
    auto profilingData = orchestratorManager->getSystemProfilingData();
    EXPECT_FALSE(profilingData.empty()) << "System profiling data should not be empty";
    EXPECT_TRUE(orchestratorManager->disableSystemProfiling()) << "System profiling should be disabled";
}

TEST_F(MultiLLMOrchestrationSystemTest, TestOrchestrationTypes) {
    auto& system = GlobalMultiLLMOrchestrationSystem::getInstance();
    
    // Test different orchestration types
    std::vector<OrchestrationType> types = {
        OrchestrationType::PARALLEL,
        OrchestrationType::SEQUENTIAL,
        OrchestrationType::PIPELINE,
        OrchestrationType::HYBRID
    };
    
    for (const auto& type : types) {
        OrchestrationConfig config;
        config.orchestratorId = "orchestrator_type_test_" + std::to_string(static_cast<int>(type));
        config.type = type;
        config.maxConcurrentLLMs = 4;
        config.maxQueueSize = 100;
        config.timeout = std::chrono::milliseconds(5000);
        config.enableLoadBalancing = true;
        config.enableResultAggregation = true;
        config.createdAt = std::chrono::system_clock::now();
        
        auto orchestrator = system.createOrchestrator(config);
        EXPECT_NE(orchestrator, nullptr) << "Orchestrator for type " << static_cast<int>(type) << " should be created";
        
        if (orchestrator) {
            EXPECT_EQ(orchestrator->getOrchestrationType(), type) << "Orchestration type should match";
        }
    }
}

TEST_F(MultiLLMOrchestrationSystemTest, TestLLMStatuses) {
    auto& system = GlobalMultiLLMOrchestrationSystem::getInstance();
    
    // Create orchestrator first
    OrchestrationConfig config;
    config.orchestratorId = "orchestrator_8";
    config.type = OrchestrationType::PARALLEL;
    config.maxConcurrentLLMs = 4;
    config.maxQueueSize = 100;
    config.timeout = std::chrono::milliseconds(5000);
    config.enableLoadBalancing = true;
    config.enableResultAggregation = true;
    config.createdAt = std::chrono::system_clock::now();
    
    auto orchestrator = system.createOrchestrator(config);
    ASSERT_NE(orchestrator, nullptr) << "Orchestrator should be created";
    
    // Test different LLM statuses
    std::vector<LLMStatus> statuses = {
        LLMStatus::IDLE,
        LLMStatus::LOADING,
        LLMStatus::READY,
        LLMStatus::EXECUTING,
        LLMStatus::COMPLETED,
        LLMStatus::ERROR,
        LLMStatus::SUSPENDED
    };
    
    for (const auto& status : statuses) {
        LLMInstance llmInstance;
        llmInstance.llmId = "llm_status_test_" + std::to_string(static_cast<int>(status));
        llmInstance.modelName = "Test Model " + std::to_string(static_cast<int>(status));
        llmInstance.modelPath = "/path/to/model" + std::to_string(static_cast<int>(status));
        llmInstance.status = status;
        llmInstance.utilization = 0.0f;
        llmInstance.activeTasks = 0;
        llmInstance.maxTasks = 10;
        llmInstance.lastUpdated = std::chrono::system_clock::now();
        
        bool registered = orchestrator->registerLLM(llmInstance);
        EXPECT_TRUE(registered) << "LLM with status " << static_cast<int>(status) << " should be registered";
        
        if (registered) {
            auto retrievedLLM = orchestrator->getLLMInstance(llmInstance.llmId);
            EXPECT_EQ(retrievedLLM.status, status) << "LLM status should match";
        }
    }
}

TEST_F(MultiLLMOrchestrationSystemTest, TestTaskPriorities) {
    auto& system = GlobalMultiLLMOrchestrationSystem::getInstance();
    
    // Create orchestrator first
    OrchestrationConfig config;
    config.orchestratorId = "orchestrator_9";
    config.type = OrchestrationType::PARALLEL;
    config.maxConcurrentLLMs = 4;
    config.maxQueueSize = 100;
    config.timeout = std::chrono::milliseconds(5000);
    config.enableLoadBalancing = true;
    config.enableResultAggregation = true;
    config.createdAt = std::chrono::system_clock::now();
    
    auto orchestrator = system.createOrchestrator(config);
    ASSERT_NE(orchestrator, nullptr) << "Orchestrator should be created";
    
    // Register LLM instances
    for (int i = 0; i < 4; ++i) {
        LLMInstance llmInstance;
        llmInstance.llmId = "llm_" + std::to_string(i + 1);
        llmInstance.modelName = "Test Model " + std::to_string(i + 1);
        llmInstance.modelPath = "/path/to/model" + std::to_string(i + 1);
        llmInstance.status = LLMStatus::READY;
        llmInstance.utilization = 0.0f;
        llmInstance.activeTasks = 0;
        llmInstance.maxTasks = 10;
        llmInstance.lastUpdated = std::chrono::system_clock::now();
        
        orchestrator->registerLLM(llmInstance);
    }
    
    // Test different task priorities
    std::vector<TaskPriority> priorities = {
        TaskPriority::LOW,
        TaskPriority::NORMAL,
        TaskPriority::HIGH,
        TaskPriority::CRITICAL,
        TaskPriority::URGENT
    };
    
    for (const auto& priority : priorities) {
        std::string requestId = "priority_test_" + std::to_string(static_cast<int>(priority));
        std::string prompt = "Test prompt with priority " + std::to_string(static_cast<int>(priority));
        std::map<std::string, std::string> parameters = {
            {"priority", std::to_string(static_cast<int>(priority))},
            {"temperature", "0.7"},
            {"max_tokens", "100"},
            {"top_p", "0.9"}
        };
        
        auto result = orchestrator->processRequest(requestId, prompt, parameters);
        EXPECT_FALSE(result.requestId.empty()) << "Request ID should not be empty";
        EXPECT_GT(result.confidence, 0.0f) << "Confidence should be positive";
        EXPECT_FALSE(result.responses.empty()) << "Responses should not be empty";
        EXPECT_FALSE(result.aggregatedResponse.empty()) << "Aggregated response should not be empty";
    }
}

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    
    // Set up logging
    spdlog::set_level(spdlog::level::info);
    
    return RUN_ALL_TESTS();
}
