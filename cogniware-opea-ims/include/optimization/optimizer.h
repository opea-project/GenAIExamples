#pragma once

#include <string>
#include <vector>
#include <memory>

namespace cogniware {
namespace optimization {

enum class OptimizationType {
    QUANTIZATION,
    PRUNING,
    FUSION,
    DISTILLATION
};

struct OptimizationConfig {
    OptimizationType type;
    std::string model_id;
    std::unordered_map<std::string, std::string> parameters;
};

struct OptimizationResult {
    bool success;
    std::string optimized_model_id;
    double size_reduction_percent;
    double speed_improvement_factor;
    std::string error_message;
};

class ModelOptimizer {
public:
    ModelOptimizer();
    ~ModelOptimizer();

    OptimizationResult optimize(const OptimizationConfig& config);
    
    OptimizationResult quantize(const std::string& model_id, int bits = 8);
    OptimizationResult prune(const std::string& model_id, double sparsity = 0.5);
    OptimizationResult fuse(const std::vector<std::string>& model_ids);

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

} // namespace optimization
} // namespace cogniware

