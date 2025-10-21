#include <gtest/gtest.h>
#include <spdlog/spdlog.h>
#include "optimization/tensor_core_optimizer.h"
#include <chrono>
#include <thread>

using namespace cogniware::optimization;

class TensorCoreOptimizationTest : public ::testing::Test {
protected:
    void SetUp() override {
        spdlog::set_level(spdlog::level::debug);
        
        // Initialize the optimization manager
        auto& manager = TensorCoreOptimizationManager::getInstance();
        ASSERT_TRUE(manager.initialize()) << "Failed to initialize tensor core optimization manager";
    }
    
    void TearDown() override {
        // Shutdown the optimization manager
        auto& manager = TensorCoreOptimizationManager::getInstance();
        manager.shutdown();
    }
};

TEST_F(TensorCoreOptimizationTest, TestManagerInitialization) {
    auto& manager = TensorCoreOptimizationManager::getInstance();
    
    EXPECT_TRUE(manager.isInitialized()) << "Manager should be initialized";
    
    // Test component access
    auto optimizer = manager.getOptimizer();
    EXPECT_NE(optimizer, nullptr) << "Optimizer should not be null";
    
    auto workloadBalancer = manager.getWorkloadBalancer();
    EXPECT_NE(workloadBalancer, nullptr) << "Workload balancer should not be null";
    
    auto memoryOptimizer = manager.getMemoryOptimizer();
    EXPECT_NE(memoryOptimizer, nullptr) << "Memory optimizer should not be null";
    
    auto precisionOptimizer = manager.getPrecisionOptimizer();
    EXPECT_NE(precisionOptimizer, nullptr) << "Precision optimizer should not be null";
}

TEST_F(TensorCoreOptimizationTest, TestTensorCoreDiscovery) {
    auto& manager = TensorCoreOptimizationManager::getInstance();
    auto optimizer = manager.getOptimizer();
    
    ASSERT_NE(optimizer, nullptr) << "Optimizer should not be null";
    
    // Test tensor core discovery
    auto availableCores = optimizer->getAvailableTensorCores();
    EXPECT_GT(availableCores.size(), 0) << "Should discover tensor cores";
    
    auto dormantCores = optimizer->getDormantTensorCores();
    EXPECT_GE(dormantCores.size(), 0) << "Should have dormant cores";
    
    spdlog::info("Discovered {} available cores, {} dormant cores", 
                availableCores.size(), dormantCores.size());
}

TEST_F(TensorCoreOptimizationTest, TestDormantCoreActivation) {
    auto& manager = TensorCoreOptimizationManager::getInstance();
    auto optimizer = manager.getOptimizer();
    
    ASSERT_NE(optimizer, nullptr) << "Optimizer should not be null";
    
    // Test dormant core activation
    bool activated = optimizer->activateDormantCores();
    EXPECT_TRUE(activated) << "Should activate dormant cores";
    
    // Verify cores are activated
    auto availableCores = optimizer->getAvailableTensorCores();
    int activeCount = 0;
    for (const auto& core : availableCores) {
        if (core.isActive) {
            activeCount++;
        }
    }
    
    EXPECT_GT(activeCount, 0) << "Should have active cores after activation";
    spdlog::info("Activated {} cores", activeCount);
}

TEST_F(TensorCoreOptimizationTest, TestWorkloadOptimization) {
    auto& manager = TensorCoreOptimizationManager::getInstance();
    auto optimizer = manager.getOptimizer();
    
    ASSERT_NE(optimizer, nullptr) << "Optimizer should not be null";
    
    // Test workload optimization strategies
    std::vector<std::string> workloadTypes = {"inference", "training", "embedding", "mixed"};
    
    for (const auto& workloadType : workloadTypes) {
        std::map<std::string, std::string> parameters = {
            {"precision", "mixed"},
            {"memory_bandwidth", "1.2"},
            {"compute_throughput", "1.1"}
        };
        
        bool optimized = optimizer->optimizeForWorkload(workloadType, parameters);
        EXPECT_TRUE(optimized) << "Should optimize for workload type: " << workloadType;
        
        spdlog::info("Optimized for workload type: {}", workloadType);
    }
}

TEST_F(TensorCoreOptimizationTest, TestOptimizationStrategies) {
    auto& manager = TensorCoreOptimizationManager::getInstance();
    auto optimizer = manager.getOptimizer();
    
    ASSERT_NE(optimizer, nullptr) << "Optimizer should not be null";
    
    // Test individual optimization strategies
    EXPECT_TRUE(optimizer->activateDormantCores()) << "Should activate dormant cores";
    EXPECT_TRUE(optimizer->balanceWorkload()) << "Should balance workload";
    EXPECT_TRUE(optimizer->optimizeMemoryAccess()) << "Should optimize memory access";
    EXPECT_TRUE(optimizer->optimizePrecision()) << "Should optimize precision";
    EXPECT_TRUE(optimizer->optimizeParallelExecution()) << "Should optimize parallel execution";
    EXPECT_TRUE(optimizer->optimizeCache()) << "Should optimize cache";
    EXPECT_TRUE(optimizer->optimizePipeline()) << "Should optimize pipeline";
    
    spdlog::info("All optimization strategies completed successfully");
}

TEST_F(TensorCoreOptimizationTest, TestLLMOptimization) {
    auto& manager = TensorCoreOptimizationManager::getInstance();
    auto optimizer = manager.getOptimizer();
    
    ASSERT_NE(optimizer, nullptr) << "Optimizer should not be null";
    
    // Test LLM-specific optimization
    std::vector<std::string> llmIds = {"interface_llm", "knowledge_llm", "embedding_llm", "multimodal_llm"};
    
    for (const auto& llmId : llmIds) {
        std::map<std::string, std::string> requirements = {
            {"model_type", "gpt"},
            {"precision", "mixed"},
            {"memory_bandwidth", "1.3"},
            {"compute_throughput", "1.2"}
        };
        
        bool optimized = optimizer->optimizeForLLM(llmId, requirements);
        EXPECT_TRUE(optimized) << "Should optimize for LLM: " << llmId;
        
        spdlog::info("Optimized for LLM: {}", llmId);
    }
}

TEST_F(TensorCoreOptimizationTest, TestWorkloadBalancing) {
    auto& manager = TensorCoreOptimizationManager::getInstance();
    auto workloadBalancer = manager.getWorkloadBalancer();
    
    ASSERT_NE(workloadBalancer, nullptr) << "Workload balancer should not be null";
    
    // Test workload balancing
    std::vector<std::string> llmIds = {"llm1", "llm2", "llm3", "llm4"};
    bool balanced = workloadBalancer->balanceWorkload(llmIds);
    EXPECT_TRUE(balanced) << "Should balance workload";
    
    // Test load monitoring
    auto coreLoads = workloadBalancer->getCoreLoads();
    EXPECT_FALSE(coreLoads.empty()) << "Should have core loads";
    
    auto llmLoads = workloadBalancer->getLLMLoads();
    EXPECT_FALSE(llmLoads.empty()) << "Should have LLM loads";
    
    bool isBalanced = workloadBalancer->isLoadBalanced();
    EXPECT_TRUE(isBalanced) << "Workload should be balanced";
    
    float loadImbalance = workloadBalancer->getLoadImbalance();
    EXPECT_GE(loadImbalance, 0.0f) << "Load imbalance should be non-negative";
    
    spdlog::info("Workload balancing completed, imbalance: {:.2f}", loadImbalance);
}

TEST_F(TensorCoreOptimizationTest, TestMemoryOptimization) {
    auto& manager = TensorCoreOptimizationManager::getInstance();
    auto memoryOptimizer = manager.getMemoryOptimizer();
    
    ASSERT_NE(memoryOptimizer, nullptr) << "Memory optimizer should not be null";
    
    // Test memory optimization strategies
    EXPECT_TRUE(memoryOptimizer->optimizeMemoryLayout()) << "Should optimize memory layout";
    EXPECT_TRUE(memoryOptimizer->optimizeMemoryAccessPatterns()) << "Should optimize access patterns";
    EXPECT_TRUE(memoryOptimizer->optimizeMemoryBandwidth()) << "Should optimize bandwidth";
    EXPECT_TRUE(memoryOptimizer->optimizeMemoryCoalescing()) << "Should optimize coalescing";
    EXPECT_TRUE(memoryOptimizer->optimizeMemoryPrefetching()) << "Should optimize prefetching";
    
    // Test memory monitoring
    auto memoryUsage = memoryOptimizer->getMemoryUsage();
    EXPECT_FALSE(memoryUsage.empty()) << "Should have memory usage data";
    
    auto memoryBandwidth = memoryOptimizer->getMemoryBandwidth();
    EXPECT_FALSE(memoryBandwidth.empty()) << "Should have bandwidth data";
    
    bool isOptimized = memoryOptimizer->isMemoryOptimized();
    EXPECT_TRUE(isOptimized) << "Memory should be optimized";
    
    float efficiency = memoryOptimizer->getMemoryEfficiency();
    EXPECT_GT(efficiency, 0.0f) << "Memory efficiency should be positive";
    
    spdlog::info("Memory optimization completed, efficiency: {:.2f}", efficiency);
}

TEST_F(TensorCoreOptimizationTest, TestPrecisionOptimization) {
    auto& manager = TensorCoreOptimizationManager::getInstance();
    auto precisionOptimizer = manager.getPrecisionOptimizer();
    
    ASSERT_NE(precisionOptimizer, nullptr) << "Precision optimizer should not be null";
    
    // Test precision optimization strategies
    EXPECT_TRUE(precisionOptimizer->optimizePrecision("gpt")) << "Should optimize for GPT model";
    EXPECT_TRUE(precisionOptimizer->optimizeMixedPrecision()) << "Should optimize mixed precision";
    EXPECT_TRUE(precisionOptimizer->optimizeQuantization()) << "Should optimize quantization";
    EXPECT_TRUE(precisionOptimizer->optimizePrecisionForTask("inference")) << "Should optimize for inference";
    
    // Test precision monitoring
    auto precisionMetrics = precisionOptimizer->getPrecisionMetrics();
    EXPECT_FALSE(precisionMetrics.empty()) << "Should have precision metrics";
    
    bool isOptimized = precisionOptimizer->isPrecisionOptimized();
    EXPECT_TRUE(isOptimized) << "Precision should be optimized";
    
    float efficiency = precisionOptimizer->getPrecisionEfficiency();
    EXPECT_GT(efficiency, 0.0f) << "Precision efficiency should be positive";
    
    spdlog::info("Precision optimization completed, efficiency: {:.2f}", efficiency);
}

TEST_F(TensorCoreOptimizationTest, TestSystemOptimization) {
    auto& manager = TensorCoreOptimizationManager::getInstance();
    
    // Test system-wide optimization
    bool optimized = manager.optimizeSystem();
    EXPECT_TRUE(optimized) << "Should optimize system";
    
    // Test multi-LLM optimization
    std::vector<std::string> llmIds = {"llm1", "llm2", "llm3", "llm4"};
    bool multiOptimized = manager.optimizeForMultipleLLMs(llmIds);
    EXPECT_TRUE(multiOptimized) << "Should optimize for multiple LLMs";
    
    // Test workload optimization
    std::vector<std::string> workloadTypes = {"inference", "training", "embedding"};
    for (const auto& workloadType : workloadTypes) {
        bool workloadOptimized = manager.optimizeForWorkload(workloadType);
        EXPECT_TRUE(workloadOptimized) << "Should optimize for workload: " << workloadType;
    }
    
    // Test comprehensive system optimization
    bool systemOptimized = manager.runSystemOptimization();
    EXPECT_TRUE(systemOptimized) << "Should run system optimization";
    
    spdlog::info("System optimization completed successfully");
}

TEST_F(TensorCoreOptimizationTest, TestPerformanceMonitoring) {
    auto& manager = TensorCoreOptimizationManager::getInstance();
    auto optimizer = manager.getOptimizer();
    
    ASSERT_NE(optimizer, nullptr) << "Optimizer should not be null";
    
    // Enable profiling
    EXPECT_TRUE(optimizer->enableProfiling()) << "Should enable profiling";
    
    // Test optimization metrics
    auto metrics = optimizer->getOptimizationMetrics();
    EXPECT_GT(metrics.totalUtilization, 0.0f) << "Should have positive utilization";
    EXPECT_GE(metrics.performanceImprovement, 0.0f) << "Should have non-negative improvement";
    EXPECT_GT(metrics.memoryBandwidthUsed, 0) << "Should use memory bandwidth";
    EXPECT_GT(metrics.computeThroughput, 0) << "Should have compute throughput";
    EXPECT_GT(metrics.coresActivated, 0) << "Should have activated cores";
    
    // Test core utilization
    auto coreUtilization = optimizer->getCoreUtilization();
    EXPECT_FALSE(coreUtilization.empty()) << "Should have core utilization data";
    
    // Test profiling data
    auto profilingData = optimizer->getProfilingData();
    EXPECT_FALSE(profilingData.empty()) << "Should have profiling data";
    
    // Test system performance metrics
    auto systemMetrics = manager.getSystemPerformanceMetrics();
    EXPECT_FALSE(systemMetrics.empty()) << "Should have system performance metrics";
    
    spdlog::info("Performance monitoring completed");
    spdlog::info("Total utilization: {:.2f}", metrics.totalUtilization);
    spdlog::info("Performance improvement: {:.2f}x", metrics.performanceImprovement);
    spdlog::info("Cores activated: {}", metrics.coresActivated);
}

TEST_F(TensorCoreOptimizationTest, TestBenchmarking) {
    auto& manager = TensorCoreOptimizationManager::getInstance();
    auto optimizer = manager.getOptimizer();
    
    ASSERT_NE(optimizer, nullptr) << "Optimizer should not be null";
    
    // Test optimization benchmarking
    bool benchmarked = optimizer->runOptimizationBenchmark();
    EXPECT_TRUE(benchmarked) << "Should run optimization benchmark";
    
    // Test benchmark results
    auto benchmarkResults = optimizer->getBenchmarkResults();
    EXPECT_FALSE(benchmarkResults.empty()) << "Should have benchmark results";
    
    // Test performance comparison
    bool compared = optimizer->compareWithStandardDriver();
    EXPECT_TRUE(compared) << "Should compare with standard driver";
    
    auto comparison = optimizer->getPerformanceComparison();
    EXPECT_FALSE(comparison.empty()) << "Should have performance comparison";
    
    spdlog::info("Benchmarking completed successfully");
    spdlog::info("Benchmark results: {} metrics", benchmarkResults.size());
    spdlog::info("Performance comparison: {} metrics", comparison.size());
}

TEST_F(TensorCoreOptimizationTest, TestConfiguration) {
    auto& manager = TensorCoreOptimizationManager::getInstance();
    
    // Test configuration management
    std::map<std::string, std::string> config = {
        {"optimization_level", "maximum"},
        {"dormant_core_activation", "enabled"},
        {"workload_balancing", "enabled"},
        {"memory_optimization", "enabled"},
        {"precision_optimization", "enabled"},
        {"parallel_execution", "enabled"},
        {"cache_optimization", "enabled"},
        {"pipeline_optimization", "enabled"}
    };
    
    manager.setOptimizationConfiguration(config);
    
    auto retrievedConfig = manager.getOptimizationConfiguration();
    EXPECT_EQ(retrievedConfig.size(), config.size()) << "Should have same number of config items";
    
    for (const auto& item : config) {
        EXPECT_EQ(retrievedConfig[item.first], item.second) 
            << "Config item " << item.first << " should match";
    }
    
    spdlog::info("Configuration management completed");
}

TEST_F(TensorCoreOptimizationTest, TestProfiling) {
    auto& manager = TensorCoreOptimizationManager::getInstance();
    
    // Test system profiling
    EXPECT_TRUE(manager.enableSystemProfiling()) << "Should enable system profiling";
    
    // Wait a bit for profiling data
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    
    // Test system performance metrics
    auto systemMetrics = manager.getSystemPerformanceMetrics();
    EXPECT_FALSE(systemMetrics.empty()) << "Should have system performance metrics";
    
    // Disable profiling
    EXPECT_TRUE(manager.disableSystemProfiling()) << "Should disable system profiling";
    
    spdlog::info("Profiling test completed");
}

TEST_F(TensorCoreOptimizationTest, TestPatentClaims) {
    auto& manager = TensorCoreOptimizationManager::getInstance();
    auto optimizer = manager.getOptimizer();
    
    ASSERT_NE(optimizer, nullptr) << "Optimizer should not be null";
    
    // Test patent claim: Dormant core activation
    EXPECT_TRUE(optimizer->enableDormantCoreActivation()) << "Should enable dormant core activation";
    
    // Test patent claim: Performance improvement
    auto metrics = optimizer->getOptimizationMetrics();
    EXPECT_GT(metrics.performanceImprovement, 1.0f) << "Should show performance improvement";
    
    // Test patent claim: Multiple LLM optimization
    std::vector<std::string> llmIds = {"llm1", "llm2", "llm3", "llm4"};
    EXPECT_TRUE(manager.optimizeForMultipleLLMs(llmIds)) << "Should optimize for multiple LLMs";
    
    // Test patent claim: Advanced optimization strategies
    EXPECT_TRUE(optimizer->setOptimizationStrategy(OptimizationStrategy::DORMANT_CORE_ACTIVATION)) 
        << "Should set optimization strategy";
    
    auto strategy = optimizer->getCurrentStrategy();
    EXPECT_EQ(strategy, OptimizationStrategy::DORMANT_CORE_ACTIVATION) 
        << "Should have correct optimization strategy";
    
    spdlog::info("Patent claims validation completed");
    spdlog::info("Performance improvement: {:.2f}x", metrics.performanceImprovement);
}

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    
    // Set up logging
    spdlog::set_level(spdlog::level::info);
    
    return RUN_ALL_TESTS();
}
