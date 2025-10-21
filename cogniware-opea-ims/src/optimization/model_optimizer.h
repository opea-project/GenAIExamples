#pragma once

#include <string>
#include <vector>
#include <memory>
#include <unordered_map>
#include <nlohmann/json.hpp>
#include <torch/torch.h>

namespace cognidream {

/**
 * @brief Class for optimizing model performance and resource usage
 */
class ModelOptimizer {
public:
    static ModelOptimizer& getInstance();

    // Delete copy constructor and assignment operator
    ModelOptimizer(const ModelOptimizer&) = delete;
    ModelOptimizer& operator=(const ModelOptimizer&) = delete;

    // Model optimization methods
    bool optimizeModel(const std::string& model_id, const nlohmann::json& config);
    bool quantizeModel(const std::string& model_id, const std::string& precision);
    bool pruneModel(const std::string& model_id, float sparsity);
    bool fuseOperations(const std::string& model_id);
    
    // Performance optimization
    bool enableCaching(const std::string& model_id);
    bool optimizeMemoryUsage(const std::string& model_id);
    bool enableParallelProcessing(const std::string& model_id);
    
    // Resource optimization
    bool optimizeBatchSize(const std::string& model_id);
    bool optimizeThreadCount(const std::string& model_id);
    bool optimizeMemoryAllocation(const std::string& model_id);
    
    // Model analysis
    nlohmann::json analyzeModelPerformance(const std::string& model_id);
    nlohmann::json getOptimizationStats(const std::string& model_id);
    std::vector<std::string> getAvailableOptimizations(const std::string& model_id);

private:
    ModelOptimizer() = default;
    ~ModelOptimizer() = default;

    // Internal state
    std::unordered_map<std::string, torch::jit::script::Module> optimized_models_;
    std::unordered_map<std::string, nlohmann::json> optimization_configs_;
    std::unordered_map<std::string, nlohmann::json> performance_stats_;

    // Helper methods
    bool validateOptimizationConfig(const nlohmann::json& config) const;
    void updatePerformanceStats(const std::string& model_id);
    bool applyOptimization(const std::string& model_id, const std::string& optimization_type);
    torch::jit::script::Module loadModel(const std::string& model_id);
    void saveOptimizedModel(const std::string& model_id, const torch::jit::script::Module& model);
};

} // namespace cognidream 