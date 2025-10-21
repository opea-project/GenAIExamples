#pragma once

#include <cuda_runtime.h>
#include <cublas_v2.h>
#include <cudnn.h>
#include <vector>
#include <memory>
#include <mutex>
#include <atomic>
#include <map>
#include <string>
#include <chrono>
#include <functional>

namespace cogniware {
namespace optimization {

// Tensor core types
enum class TensorCoreType {
    FP16_TENSOR_CORE,      // FP16 tensor cores
    INT8_TENSOR_CORE,      // INT8 tensor cores
    TF32_TENSOR_CORE,      // TF32 tensor cores
    BF16_TENSOR_CORE,      // BF16 tensor cores
    MIXED_PRECISION_CORE   // Mixed precision cores
};

// Optimization strategies
enum class OptimizationStrategy {
    DORMANT_CORE_ACTIVATION,    // Activate dormant tensor cores
    WORKLOAD_BALANCING,         // Balance workload across cores
    MEMORY_OPTIMIZATION,        // Optimize memory access patterns
    PRECISION_OPTIMIZATION,     // Optimize precision for performance
    PARALLEL_EXECUTION,         // Parallel execution optimization
    CACHE_OPTIMIZATION,         // Cache optimization
    PIPELINE_OPTIMIZATION       // Pipeline optimization
};

// Tensor core configuration
struct TensorCoreConfig {
    TensorCoreType type;
    int coreId;
    bool isActive;
    bool isDormant;
    float utilization;
    size_t memoryBandwidth;
    size_t computeThroughput;
    std::chrono::system_clock::time_point lastUsed;
    std::map<std::string, std::string> parameters;
};

// Optimization metrics
struct OptimizationMetrics {
    float totalUtilization;
    float dormantCoreUtilization;
    float performanceImprovement;
    size_t memoryBandwidthUsed;
    size_t computeThroughput;
    std::chrono::milliseconds executionTime;
    size_t coresActivated;
    size_t coresOptimized;
    std::map<std::string, float> coreMetrics;
};

// Tensor core optimizer interface
class TensorCoreOptimizer {
public:
    virtual ~TensorCoreOptimizer() = default;

    // Core management
    virtual bool initialize() = 0;
    virtual void shutdown() = 0;
    virtual bool isInitialized() const = 0;

    // Tensor core discovery and management
    virtual std::vector<TensorCoreConfig> getAvailableTensorCores() = 0;
    virtual std::vector<TensorCoreConfig> getDormantTensorCores() = 0;
    virtual bool activateTensorCore(int coreId) = 0;
    virtual bool deactivateTensorCore(int coreId) = 0;
    virtual TensorCoreConfig getTensorCoreConfig(int coreId) = 0;

    // Optimization strategies
    virtual bool optimizeForWorkload(const std::string& workloadType, 
                                   const std::map<std::string, std::string>& parameters) = 0;
    virtual bool activateDormantCores() = 0;
    virtual bool balanceWorkload() = 0;
    virtual bool optimizeMemoryAccess() = 0;
    virtual bool optimizePrecision() = 0;
    virtual bool optimizeParallelExecution() = 0;
    virtual bool optimizeCache() = 0;
    virtual bool optimizePipeline() = 0;

    // Performance monitoring
    virtual OptimizationMetrics getOptimizationMetrics() = 0;
    virtual std::map<std::string, float> getCoreUtilization() = 0;
    virtual bool enableProfiling() = 0;
    virtual bool disableProfiling() = 0;
    virtual std::map<std::string, double> getProfilingData() = 0;

    // Advanced optimization
    virtual bool optimizeForLLM(const std::string& llmId, 
                              const std::map<std::string, std::string>& requirements) = 0;
    virtual bool optimizeForTask(const std::string& taskType, 
                               const std::map<std::string, std::string>& parameters) = 0;
    virtual bool optimizeForModel(const std::string& modelType, 
                                const std::map<std::string, std::string>& config) = 0;
};

// Advanced tensor core optimizer implementation
class AdvancedTensorCoreOptimizer : public TensorCoreOptimizer {
public:
    AdvancedTensorCoreOptimizer();
    ~AdvancedTensorCoreOptimizer() override;

    // Core management
    bool initialize() override;
    void shutdown() override;
    bool isInitialized() const override;

    // Tensor core discovery and management
    std::vector<TensorCoreConfig> getAvailableTensorCores() override;
    std::vector<TensorCoreConfig> getDormantTensorCores() override;
    bool activateTensorCore(int coreId) override;
    bool deactivateTensorCore(int coreId) override;
    TensorCoreConfig getTensorCoreConfig(int coreId) override;

    // Optimization strategies
    bool optimizeForWorkload(const std::string& workloadType, 
                           const std::map<std::string, std::string>& parameters) override;
    bool activateDormantCores() override;
    bool balanceWorkload() override;
    bool optimizeMemoryAccess() override;
    bool optimizePrecision() override;
    bool optimizeParallelExecution() override;
    bool optimizeCache() override;
    bool optimizePipeline() override;

    // Performance monitoring
    OptimizationMetrics getOptimizationMetrics() override;
    std::map<std::string, float> getCoreUtilization() override;
    bool enableProfiling() override;
    bool disableProfiling() override;
    std::map<std::string, double> getProfilingData() override;

    // Advanced optimization
    bool optimizeForLLM(const std::string& llmId, 
                      const std::map<std::string, std::string>& requirements) override;
    bool optimizeForTask(const std::string& taskType, 
                       const std::map<std::string, std::string>& parameters) override;
    bool optimizeForModel(const std::string& modelType, 
                        const std::map<std::string, std::string>& config) override;

    // Advanced features
    bool enableDormantCoreActivation();
    bool disableDormantCoreActivation();
    bool setOptimizationStrategy(OptimizationStrategy strategy);
    OptimizationStrategy getCurrentStrategy() const;
    bool runOptimizationBenchmark();
    std::map<std::string, double> getBenchmarkResults();
    bool compareWithStandardDriver();
    std::map<std::string, double> getPerformanceComparison();

private:
    // Internal state
    bool initialized_;
    std::vector<TensorCoreConfig> tensorCores_;
    std::map<int, TensorCoreConfig> coreConfigs_;
    std::map<std::string, float> coreUtilization_;
    OptimizationMetrics currentMetrics_;
    OptimizationStrategy currentStrategy_;
    bool profilingEnabled_;
    std::mutex optimizerMutex_;

    // CUDA handles
    cublasHandle_t cublasHandle_;
    cudnnHandle_t cudnnHandle_;
    cudaStream_t optimizationStream_;

    // Helper methods
    bool initializeCUDA();
    void shutdownCUDA();
    bool discoverTensorCores();
    bool analyzeCoreUtilization();
    bool activateDormantCore(int coreId);
    bool deactivateCore(int coreId);
    void updateCoreMetrics(int coreId);
    bool runOptimizationAlgorithm(OptimizationStrategy strategy);
    bool validateOptimization();
    void updateOptimizationMetrics();
    bool benchmarkCorePerformance(int coreId);
    bool compareCorePerformance(int coreId);
};

// Tensor core workload balancer
class TensorCoreWorkloadBalancer {
public:
    TensorCoreWorkloadBalancer();
    ~TensorCoreWorkloadBalancer();

    // Workload balancing
    bool balanceWorkload(const std::vector<std::string>& llmIds);
    bool distributeTasks(const std::map<std::string, std::string>& tasks);
    bool optimizeCoreAssignment(const std::vector<int>& coreIds);
    bool rebalanceWorkload();

    // Load monitoring
    std::map<int, float> getCoreLoads();
    std::map<std::string, float> getLLMLoads();
    bool isLoadBalanced();
    float getLoadImbalance();

    // Configuration
    void setBalancingStrategy(const std::string& strategy);
    std::string getBalancingStrategy() const;
    void setLoadThreshold(float threshold);
    float getLoadThreshold() const;

private:
    std::map<int, float> coreLoads_;
    std::map<std::string, float> llmLoads_;
    std::string balancingStrategy_;
    float loadThreshold_;
    std::mutex balancerMutex_;

    // Helper methods
    bool calculateCoreLoads();
    bool calculateLLMLoads();
    bool redistributeWorkload();
    bool optimizeCoreAssignment();
};

// Tensor core memory optimizer
class TensorCoreMemoryOptimizer {
public:
    TensorCoreMemoryOptimizer();
    ~TensorCoreMemoryOptimizer();

    // Memory optimization
    bool optimizeMemoryLayout();
    bool optimizeMemoryAccessPatterns();
    bool optimizeMemoryBandwidth();
    bool optimizeMemoryCoalescing();
    bool optimizeMemoryPrefetching();

    // Memory monitoring
    std::map<std::string, size_t> getMemoryUsage();
    std::map<std::string, float> getMemoryBandwidth();
    bool isMemoryOptimized();
    float getMemoryEfficiency();

    // Configuration
    void setMemoryOptimizationLevel(int level);
    int getMemoryOptimizationLevel() const;
    void setBandwidthThreshold(float threshold);
    float getBandwidthThreshold() const;

private:
    std::map<std::string, size_t> memoryUsage_;
    std::map<std::string, float> memoryBandwidth_;
    int optimizationLevel_;
    float bandwidthThreshold_;
    std::mutex memoryMutex_;

    // Helper methods
    bool analyzeMemoryUsage();
    bool optimizeMemoryLayout();
    bool optimizeAccessPatterns();
    bool optimizeBandwidth();
    bool validateMemoryOptimization();
};

// Tensor core precision optimizer
class TensorCorePrecisionOptimizer {
public:
    TensorCorePrecisionOptimizer();
    ~TensorCorePrecisionOptimizer();

    // Precision optimization
    bool optimizePrecision(const std::string& modelType);
    bool optimizeMixedPrecision();
    bool optimizeQuantization();
    bool optimizePrecisionForTask(const std::string& taskType);

    // Precision monitoring
    std::map<std::string, float> getPrecisionMetrics();
    bool isPrecisionOptimized();
    float getPrecisionEfficiency();

    // Configuration
    void setPrecisionMode(const std::string& mode);
    std::string getPrecisionMode() const;
    void setAccuracyThreshold(float threshold);
    float getAccuracyThreshold() const;

private:
    std::map<std::string, float> precisionMetrics_;
    std::string precisionMode_;
    float accuracyThreshold_;
    std::mutex precisionMutex_;

    // Helper methods
    bool analyzePrecisionRequirements();
    bool optimizePrecisionSettings();
    bool validatePrecisionOptimization();
    bool benchmarkPrecisionPerformance();
};

// Global tensor core optimization manager
class TensorCoreOptimizationManager {
public:
    static TensorCoreOptimizationManager& getInstance();

    // Manager operations
    bool initialize();
    void shutdown();
    bool isInitialized() const;

    // Component access
    std::shared_ptr<TensorCoreOptimizer> getOptimizer();
    std::shared_ptr<TensorCoreWorkloadBalancer> getWorkloadBalancer();
    std::shared_ptr<TensorCoreMemoryOptimizer> getMemoryOptimizer();
    std::shared_ptr<TensorCorePrecisionOptimizer> getPrecisionOptimizer();

    // Global optimization
    bool optimizeSystem();
    bool optimizeForMultipleLLMs(const std::vector<std::string>& llmIds);
    bool optimizeForWorkload(const std::string& workloadType);
    bool runSystemOptimization();

    // Performance monitoring
    OptimizationMetrics getSystemOptimizationMetrics();
    std::map<std::string, double> getSystemPerformanceMetrics();
    bool enableSystemProfiling();
    bool disableSystemProfiling();

    // Configuration
    void setOptimizationConfiguration(const std::map<std::string, std::string>& config);
    std::map<std::string, std::string> getOptimizationConfiguration() const;

private:
    TensorCoreOptimizationManager();
    ~TensorCoreOptimizationManager();

    std::shared_ptr<AdvancedTensorCoreOptimizer> optimizer_;
    std::shared_ptr<TensorCoreWorkloadBalancer> workloadBalancer_;
    std::shared_ptr<TensorCoreMemoryOptimizer> memoryOptimizer_;
    std::shared_ptr<TensorCorePrecisionOptimizer> precisionOptimizer_;
    bool initialized_;
    std::map<std::string, std::string> configuration_;
    std::mutex managerMutex_;
};

} // namespace optimization
} // namespace cogniware
