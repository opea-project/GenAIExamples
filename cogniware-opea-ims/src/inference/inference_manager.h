#pragma once

#include <string>
#include <memory>
#include <map>
#include <vector>
#include <torch/torch.h>
#include "../optimization/model_optimizer.h"
#include "../optimization/performance_test.h"

namespace cogniware {

class InferenceManager {
public:
    InferenceManager();
    ~InferenceManager();

    // Model management
    bool load_model(const std::string& model_path, const std::string& model_type);
    bool optimize_model(const std::map<std::string, std::string>& config);
    
    // Inference methods
    torch::Tensor run_inference(const torch::Tensor& input);
    std::vector<torch::Tensor> run_batch_inference(
        const std::vector<torch::Tensor>& inputs);
    
    // Performance monitoring
    void start_monitoring();
    void stop_monitoring();
    std::map<std::string, float> get_performance_metrics();
    
    // Advanced features
    bool enable_auto_optimization();
    bool set_batch_size(int batch_size);
    bool set_precision(const std::string& precision);
    
private:
    std::shared_ptr<ModelOptimizer> optimizer_;
    std::unique_ptr<PerformanceTest> performance_test_;
    bool is_monitoring_;
    int batch_size_;
    std::string precision_;
    
    // Helper methods
    bool validate_input(const torch::Tensor& input);
    void log_inference_metrics(const std::string& metric_name, float value);
    bool apply_auto_optimization();
};

} // namespace cogniware 