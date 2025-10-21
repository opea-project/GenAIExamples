#include <gtest/gtest.h>
#include <spdlog/spdlog.h>
#include "parallel/parallel_llm_execution.h"
#include <chrono>
#include <thread>

using namespace cogniware::parallel;

class ParallelLLMExecutionSystemTest : public ::testing::Test {
protected:
    void SetUp() override {
        spdlog::set_level(spdlog::level::debug);
        
        // Initialize the global system
        auto& system = GlobalParallelLLMExecutionSystem::getInstance();
        ASSERT_TRUE(system.initialize()) << "Failed to initialize global parallel LLM execution system";
    }
    
    void TearDown() override {
        // Shutdown the global system
        auto& system = GlobalParallelLLMExecutionSystem::getInstance();
        system.shutdown();
    }
};

TEST_F(ParallelLLMExecutionSystemTest, TestSystemInitialization) {
    auto& system = GlobalParallelLLMExecutionSystem::getInstance();
    
    EXPECT_TRUE(system.isInitialized()) << "System should be initialized";
    
    // Test component access
    auto executionManager = system.getExecutionManager();
    EXPECT_NE(executionManager, nullptr) << "Execution manager should not be null";
}

TEST_F(ParallelLLMExecutionSystemTest, TestLLMCreation) {
    auto& system = GlobalParallelLLMExecutionSystem::getInstance();
    
    // Create LLM execution configuration
    LLMExecutionConfig config;
    config.llmId = "test_llm_1";
    config.modelPath = "/path/to/model";
    config.modelType = "GPT";
    config.maxSequenceLength = 2048;
    config.batchSize = 4;
    config.numLayers = 12;
    config.hiddenSize = 768;
    config.numHeads = 12;
    config.learningRate = 0.001f;
    config.mode = LLMExecutionMode::PARALLEL;
    config.priority = LLMPriority::NORMAL;
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    // Create LLM
    auto llm = system.createLLM(config);
    EXPECT_NE(llm, nullptr) << "LLM should be created";
    
    if (llm) {
        EXPECT_EQ(llm->getLLMId(), config.llmId) << "LLM ID should match";
        EXPECT_EQ(llm->getStatus(), LLMExecutionStatus::READY) << "LLM should be ready";
        EXPECT_TRUE(llm->isInitialized()) << "LLM should be initialized";
    }
}

TEST_F(ParallelLLMExecutionSystemTest, TestLLMExecution) {
    auto& system = GlobalParallelLLMExecutionSystem::getInstance();
    
    // Create LLM first
    LLMExecutionConfig config;
    config.llmId = "test_llm_2";
    config.modelPath = "/path/to/model";
    config.modelType = "GPT";
    config.maxSequenceLength = 2048;
    config.batchSize = 4;
    config.numLayers = 12;
    config.hiddenSize = 768;
    config.numHeads = 12;
    config.learningRate = 0.001f;
    config.mode = LLMExecutionMode::PARALLEL;
    config.priority = LLMPriority::NORMAL;
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto llm = system.createLLM(config);
    ASSERT_NE(llm, nullptr) << "LLM should be created";
    
    // Create execution request
    LLMExecutionRequest request;
    request.requestId = "test_request_1";
    request.llmId = config.llmId;
    request.inputText = "Hello, world!";
    request.maxOutputLength = 100;
    request.temperature = 0.7f;
    request.topP = 0.9f;
    request.topK = 50;
    request.streamOutput = false;
    request.prompt = "You are a helpful assistant.";
    request.timeout = std::chrono::milliseconds(5000);
    request.createdAt = std::chrono::system_clock::now();
    
    // Execute request
    auto response = system.execute(request);
    EXPECT_TRUE(response.success) << "Execution should succeed";
    EXPECT_EQ(response.requestId, request.requestId) << "Request ID should match";
    EXPECT_EQ(response.llmId, request.llmId) << "LLM ID should match";
    EXPECT_FALSE(response.outputText.empty()) << "Output text should not be empty";
    EXPECT_GT(response.latency, 0.0f) << "Latency should be positive";
    EXPECT_GT(response.throughput, 0.0f) << "Throughput should be positive";
}

TEST_F(ParallelLLMExecutionSystemTest, TestAsyncExecution) {
    auto& system = GlobalParallelLLMExecutionSystem::getInstance();
    
    // Create LLM first
    LLMExecutionConfig config;
    config.llmId = "test_llm_3";
    config.modelPath = "/path/to/model";
    config.modelType = "GPT";
    config.maxSequenceLength = 2048;
    config.batchSize = 4;
    config.numLayers = 12;
    config.hiddenSize = 768;
    config.numHeads = 12;
    config.learningRate = 0.001f;
    config.mode = LLMExecutionMode::PARALLEL;
    config.priority = LLMPriority::NORMAL;
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto llm = system.createLLM(config);
    ASSERT_NE(llm, nullptr) << "LLM should be created";
    
    // Create execution request
    LLMExecutionRequest request;
    request.requestId = "test_request_2";
    request.llmId = config.llmId;
    request.inputText = "Hello, world!";
    request.maxOutputLength = 100;
    request.temperature = 0.7f;
    request.topP = 0.9f;
    request.topK = 50;
    request.streamOutput = false;
    request.prompt = "You are a helpful assistant.";
    request.timeout = std::chrono::milliseconds(5000);
    request.createdAt = std::chrono::system_clock::now();
    
    // Execute async request
    auto future = system.executeAsync(request);
    EXPECT_TRUE(future.valid()) << "Future should be valid";
    
    // Wait for completion
    auto response = future.get();
    EXPECT_TRUE(response.success) << "Async execution should succeed";
    EXPECT_EQ(response.requestId, request.requestId) << "Request ID should match";
    EXPECT_EQ(response.llmId, request.llmId) << "LLM ID should match";
    EXPECT_FALSE(response.outputText.empty()) << "Output text should not be empty";
    EXPECT_GT(response.latency, 0.0f) << "Latency should be positive";
    EXPECT_GT(response.throughput, 0.0f) << "Throughput should be positive";
}

TEST_F(ParallelLLMExecutionSystemTest, TestParallelExecution) {
    auto& system = GlobalParallelLLMExecutionSystem::getInstance();
    
    // Create multiple LLMs
    std::vector<std::string> llmIds;
    for (int i = 0; i < 4; ++i) {
        LLMExecutionConfig config;
        config.llmId = "test_llm_" + std::to_string(i + 4);
        config.modelPath = "/path/to/model";
        config.modelType = "GPT";
        config.maxSequenceLength = 2048;
        config.batchSize = 4;
        config.numLayers = 12;
        config.hiddenSize = 768;
        config.numHeads = 12;
        config.learningRate = 0.001f;
        config.mode = LLMExecutionMode::PARALLEL;
        config.priority = LLMPriority::NORMAL;
        config.createdAt = std::chrono::system_clock::now();
        config.lastUsed = std::chrono::system_clock::now();
        
        auto llm = system.createLLM(config);
        ASSERT_NE(llm, nullptr) << "LLM " << i << " should be created";
        llmIds.push_back(config.llmId);
    }
    
    // Create parallel execution requests
    std::vector<LLMExecutionRequest> requests;
    for (int i = 0; i < 4; ++i) {
        LLMExecutionRequest request;
        request.requestId = "test_request_" + std::to_string(i + 3);
        request.llmId = llmIds[i];
        request.inputText = "Hello, world " + std::to_string(i) + "!";
        request.maxOutputLength = 100;
        request.temperature = 0.7f;
        request.topP = 0.9f;
        request.topK = 50;
        request.streamOutput = false;
        request.prompt = "You are a helpful assistant.";
        request.timeout = std::chrono::milliseconds(5000);
        request.createdAt = std::chrono::system_clock::now();
        
        requests.push_back(request);
    }
    
    // Execute parallel requests
    auto responses = system.executeParallel(requests);
    EXPECT_EQ(responses.size(), requests.size()) << "Should have same number of responses";
    
    for (size_t i = 0; i < responses.size(); ++i) {
        EXPECT_TRUE(responses[i].success) << "Response " << i << " should succeed";
        EXPECT_EQ(responses[i].requestId, requests[i].requestId) << "Request ID should match";
        EXPECT_EQ(responses[i].llmId, requests[i].llmId) << "LLM ID should match";
        EXPECT_FALSE(responses[i].outputText.empty()) << "Output text should not be empty";
        EXPECT_GT(responses[i].latency, 0.0f) << "Latency should be positive";
        EXPECT_GT(responses[i].throughput, 0.0f) << "Throughput should be positive";
    }
}

TEST_F(ParallelLLMExecutionSystemTest, TestLLMManagement) {
    auto& system = GlobalParallelLLMExecutionSystem::getInstance();
    
    // Create multiple LLMs
    std::vector<std::string> llmIds;
    for (int i = 0; i < 5; ++i) {
        LLMExecutionConfig config;
        config.llmId = "test_llm_" + std::to_string(i + 8);
        config.modelPath = "/path/to/model";
        config.modelType = "GPT";
        config.maxSequenceLength = 2048;
        config.batchSize = 4;
        config.numLayers = 12;
        config.hiddenSize = 768;
        config.numHeads = 12;
        config.learningRate = 0.001f;
        config.mode = LLMExecutionMode::PARALLEL;
        config.priority = LLMPriority::NORMAL;
        config.createdAt = std::chrono::system_clock::now();
        config.lastUsed = std::chrono::system_clock::now();
        
        auto llm = system.createLLM(config);
        ASSERT_NE(llm, nullptr) << "LLM " << i << " should be created";
        llmIds.push_back(config.llmId);
    }
    
    // Test LLM retrieval
    for (const auto& llmId : llmIds) {
        auto llm = system.getLLM(llmId);
        EXPECT_NE(llm, nullptr) << "LLM " << llmId << " should be retrievable";
        EXPECT_EQ(llm->getLLMId(), llmId) << "LLM ID should match";
    }
    
    // Test getting all LLMs
    auto allLLMs = system.getAllLLMs();
    EXPECT_GE(allLLMs.size(), 5) << "Should have at least 5 LLMs";
    
    // Test LLM destruction
    for (const auto& llmId : llmIds) {
        bool destroyed = system.destroyLLM(llmId);
        EXPECT_TRUE(destroyed) << "LLM " << llmId << " should be destroyed";
    }
}

TEST_F(ParallelLLMExecutionSystemTest, TestContextManagement) {
    auto& system = GlobalParallelLLMExecutionSystem::getInstance();
    
    // Create LLM first
    LLMExecutionConfig config;
    config.llmId = "test_llm_9";
    config.modelPath = "/path/to/model";
    config.modelType = "GPT";
    config.maxSequenceLength = 2048;
    config.batchSize = 4;
    config.numLayers = 12;
    config.hiddenSize = 768;
    config.numHeads = 12;
    config.learningRate = 0.001f;
    config.mode = LLMExecutionMode::PARALLEL;
    config.priority = LLMPriority::NORMAL;
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto llm = system.createLLM(config);
    ASSERT_NE(llm, nullptr) << "LLM should be created";
    
    // Create context
    LLMExecutionContext context;
    context.contextId = "test_context_1";
    context.llmId = config.llmId;
    context.conversationHistory = {"Hello", "Hi there", "How are you?"};
    context.maxContextLength = 1000;
    context.maintainContext = true;
    context.createdAt = std::chrono::system_clock::now();
    context.lastUsed = std::chrono::system_clock::now();
    
    std::string contextId = llm->createContext(context);
    EXPECT_FALSE(contextId.empty()) << "Context ID should not be empty";
    
    // Test context retrieval
    auto retrievedContext = llm->getContext(contextId);
    EXPECT_EQ(retrievedContext.contextId, context.contextId) << "Context ID should match";
    EXPECT_EQ(retrievedContext.llmId, context.llmId) << "LLM ID should match";
    EXPECT_EQ(retrievedContext.conversationHistory.size(), context.conversationHistory.size()) << "Conversation history size should match";
    
    // Test context update
    context.conversationHistory.push_back("I'm doing well, thank you!");
    bool updated = llm->updateContext(contextId, context);
    EXPECT_TRUE(updated) << "Context update should succeed";
    
    // Test context deletion
    bool deleted = llm->deleteContext(contextId);
    EXPECT_TRUE(deleted) << "Context deletion should succeed";
}

TEST_F(ParallelLLMExecutionSystemTest, TestPerformanceMonitoring) {
    auto& system = GlobalParallelLLMExecutionSystem::getInstance();
    
    // Create LLM first
    LLMExecutionConfig config;
    config.llmId = "test_llm_10";
    config.modelPath = "/path/to/model";
    config.modelType = "GPT";
    config.maxSequenceLength = 2048;
    config.batchSize = 4;
    config.numLayers = 12;
    config.hiddenSize = 768;
    config.numHeads = 12;
    config.learningRate = 0.001f;
    config.mode = LLMExecutionMode::PARALLEL;
    config.priority = LLMPriority::NORMAL;
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto llm = system.createLLM(config);
    ASSERT_NE(llm, nullptr) << "LLM should be created";
    
    // Enable profiling
    EXPECT_TRUE(llm->enableProfiling()) << "Profiling should be enabled";
    
    // Get performance metrics
    auto metrics = llm->getPerformanceMetrics();
    EXPECT_FALSE(metrics.empty()) << "Performance metrics should not be empty";
    EXPECT_GE(metrics["utilization"], 0.0) << "Utilization should be non-negative";
    EXPECT_GE(metrics["latency"], 0.0) << "Latency should be non-negative";
    EXPECT_GE(metrics["throughput"], 0.0) << "Throughput should be non-negative";
    EXPECT_GE(metrics["request_count"], 0.0) << "Request count should be non-negative";
    EXPECT_GE(metrics["error_count"], 0.0) << "Error count should be non-negative";
    
    // Get profiling data
    auto profilingData = llm->getProfilingData();
    EXPECT_FALSE(profilingData.empty()) << "Profiling data should not be empty";
    EXPECT_GE(profilingData["utilization"], 0.0) << "Profiling utilization should be non-negative";
    EXPECT_GE(profilingData["latency"], 0.0) << "Profiling latency should be non-negative";
    EXPECT_GE(profilingData["throughput"], 0.0) << "Profiling throughput should be non-negative";
    EXPECT_GE(profilingData["request_count"], 0.0) << "Profiling request count should be non-negative";
    EXPECT_GE(profilingData["error_count"], 0.0) << "Profiling error count should be non-negative";
    EXPECT_GE(profilingData["active_requests"], 0.0) << "Active requests should be non-negative";
    EXPECT_GE(profilingData["context_count"], 0.0) << "Context count should be non-negative";
    EXPECT_GE(profilingData["device_memory_size"], 0.0) << "Device memory size should be non-negative";
    
    // Get utilization
    float utilization = llm->getUtilization();
    EXPECT_GE(utilization, 0.0f) << "Utilization should be non-negative";
    EXPECT_LE(utilization, 1.0f) << "Utilization should not exceed 1.0";
    
    // Disable profiling
    EXPECT_TRUE(llm->disableProfiling()) << "Profiling should be disabled";
}

TEST_F(ParallelLLMExecutionSystemTest, TestSystemMetrics) {
    auto& system = GlobalParallelLLMExecutionSystem::getInstance();
    
    // Get system metrics
    auto metrics = system.getSystemMetrics();
    EXPECT_FALSE(metrics.empty()) << "System metrics should not be empty";
    EXPECT_GT(metrics["total_llms"], 0.0) << "Total LLMs should be positive";
    EXPECT_GE(metrics["active_requests"], 0.0) << "Active requests should be non-negative";
    EXPECT_GE(metrics["average_utilization"], 0.0) << "Average utilization should be non-negative";
    EXPECT_EQ(metrics["system_initialized"], 1.0) << "System should be initialized";
    EXPECT_GT(metrics["configuration_items"], 0.0) << "Configuration items should be positive";
}

TEST_F(ParallelLLMExecutionSystemTest, TestSystemConfiguration) {
    auto& system = GlobalParallelLLMExecutionSystem::getInstance();
    
    // Test system configuration
    std::map<std::string, std::string> config = {
        {"max_llms", "20"},
        {"execution_policy", "optimized"},
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

TEST_F(ParallelLLMExecutionSystemTest, TestAdvancedLLMFeatures) {
    auto& system = GlobalParallelLLMExecutionSystem::getInstance();
    
    // Create LLM first
    LLMExecutionConfig config;
    config.llmId = "test_llm_11";
    config.modelPath = "/path/to/model";
    config.modelType = "GPT";
    config.maxSequenceLength = 2048;
    config.batchSize = 4;
    config.numLayers = 12;
    config.hiddenSize = 768;
    config.numHeads = 12;
    config.learningRate = 0.001f;
    config.mode = LLMExecutionMode::PARALLEL;
    config.priority = LLMPriority::NORMAL;
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto llm = system.createLLM(config);
    ASSERT_NE(llm, nullptr) << "LLM should be created";
    
    // Cast to advanced LLM
    auto advancedLLM = std::dynamic_pointer_cast<AdvancedLLMExecutor>(llm);
    ASSERT_NE(advancedLLM, nullptr) << "LLM should be an advanced LLM";
    
    // Test advanced features
    EXPECT_TRUE(advancedLLM->suspend()) << "LLM suspension should succeed";
    EXPECT_TRUE(advancedLLM->resume()) << "LLM resumption should succeed";
    EXPECT_TRUE(advancedLLM->migrate("target_node_1")) << "LLM migration should succeed";
    EXPECT_TRUE(advancedLLM->clone("test_llm_11_clone")) << "LLM cloning should succeed";
    EXPECT_TRUE(advancedLLM->scale(8, 4096)) << "LLM scaling should succeed";
    EXPECT_TRUE(advancedLLM->optimize()) << "LLM optimization should succeed";
    
    // Test resource info
    auto resourceInfo = advancedLLM->getResourceInfo();
    EXPECT_FALSE(resourceInfo.empty()) << "Resource info should not be empty";
    EXPECT_EQ(resourceInfo["llm_id"], config.llmId) << "LLM ID should match";
    EXPECT_EQ(resourceInfo["model_type"], config.modelType) << "Model type should match";
    
    // Test resource validation
    EXPECT_TRUE(advancedLLM->validateResources()) << "Resource validation should pass";
    
    // Test model management
    EXPECT_TRUE(advancedLLM->preloadModel()) << "Model preloading should succeed";
    EXPECT_TRUE(advancedLLM->isModelLoaded()) << "Model should be loaded";
    EXPECT_TRUE(advancedLLM->unloadModel()) << "Model unloading should succeed";
}

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    
    // Set up logging
    spdlog::set_level(spdlog::level::info);
    
    return RUN_ALL_TESTS();
}
