#include "inference_manager.h"
#include <spdlog/spdlog.h>

namespace cogniware {

InferenceManager::InferenceManager()
    : optimizer_(std::make_shared<ModelOptimizer>()),
      performance_test_(std::make_unique<PerformanceTest>(optimizer_)),
      is_monitoring_(false),
      batch_size_(1),
      precision_("fp32") {}

InferenceManager::~InferenceManager() {
    if (is_monitoring_) {
        stop_monitoring();
    }
}

bool InferenceManager::load_model(const std::string& model_path, const std::string& model_type) {
    if (!optimizer_->load_model(model_path, model_type)) {
        spdlog::error("Failed to load model from {}", model_path);
        return false;
    }
    
    // Initialize with default optimization settings
    std::map<std::string, std::string> default_config = {
        {"quantization", "8bit"},
        {"pruning", "structured"},
        {"target_sparsity", "0.3"}
    };
    
    return optimize_model(default_config);
}

bool InferenceManager::optimize_model(const std::map<std::string, std::string>& config) {
    if (!optimizer_->initialize_optimization(config)) {
        spdlog::error("Failed to initialize optimization with provided config");
        return false;
    }
    
    if (!optimizer_->optimize_model()) {
        spdlog::error("Failed to optimize model");
        return false;
    }
    
    // Benchmark optimization impact
    auto impact = performance_test_->benchmark_optimization_impact();
    spdlog::info("Optimization impact: {:.2f}x speedup, {:.2f}% memory reduction",
                 impact["speedup_factor"],
                 impact["memory_reduction_percent"]);
    
    return true;
}

torch::Tensor InferenceManager::run_inference(const torch::Tensor& input) {
    if (!validate_input(input)) {
        throw std::runtime_error("Invalid input tensor");
    }
    
    auto start = std::chrono::high_resolution_clock::now();
    auto output = optimizer_->optimize_model();
    auto end = std::chrono::high_resolution_clock::now();
    
    if (is_monitoring_) {
        float inference_time = std::chrono::duration_cast<std::chrono::microseconds>(
            end - start).count() / 1000.0f;
        log_inference_metrics("inference_time_ms", inference_time);
    }
    
    return output;
}

std::vector<torch::Tensor> InferenceManager::run_batch_inference(
    const std::vector<torch::Tensor>& inputs) {
    std::vector<torch::Tensor> outputs;
    outputs.reserve(inputs.size());
    
    for (const auto& input : inputs) {
        outputs.push_back(run_inference(input));
    }
    
    return outputs;
}

void InferenceManager::start_monitoring() {
    is_monitoring_ = true;
    performance_test_->start_detailed_profiling();
}

void InferenceManager::stop_monitoring() {
    is_monitoring_ = false;
    performance_test_->stop_detailed_profiling();
}

std::map<std::string, float> InferenceManager::get_performance_metrics() {
    return performance_test_->get_detailed_metrics();
}

bool InferenceManager::enable_auto_optimization() {
    // Try different optimization strategies and select the best one
    std::vector<std::map<std::string, std::string>> strategies = {
        {{"quantization", "8bit"}},
        {{"quantization", "4bit"}},
        {{"pruning", "structured"}, {"target_sparsity", "0.3"}},
        {{"pruning", "unstructured"}, {"threshold", "0.1"}},
        {{"distillation", "enabled"}}
    };
    
    auto results = performance_test_->compare_optimization_strategies(strategies);
    
    // Find the best strategy based on speedup and memory reduction
    float best_score = 0.0f;
    size_t best_strategy = 0;
    
    for (size_t i = 0; i < strategies.size(); ++i) {
        float score = results["strategy_" + std::to_string(i) + "_speedup"] *
                     (1.0f + results["strategy_" + std::to_string(i) + "_memory_reduction"] / 100.0f);
        
        if (score > best_score) {
            best_score = score;
            best_strategy = i;
        }
    }
    
    return optimize_model(strategies[best_strategy]);
}

bool InferenceManager::set_batch_size(int batch_size) {
    if (batch_size <= 0) {
        spdlog::error("Invalid batch size: {}", batch_size);
        return false;
    }
    
    batch_size_ = batch_size;
    return true;
}

bool InferenceManager::set_precision(const std::string& precision) {
    if (precision != "fp32" && precision != "fp16" && precision != "int8") {
        spdlog::error("Unsupported precision: {}", precision);
        return false;
    }
    
    precision_ = precision;
    std::map<std::string, std::string> config = {
        {"precision", precision}
    };
    
    return optimize_model(config);
}

bool InferenceManager::validate_input(const torch::Tensor& input) {
    if (!input.defined()) {
        spdlog::error("Input tensor is undefined");
        return false;
    }
    
    if (!input.is_cuda()) {
        spdlog::error("Input tensor is not on GPU");
        return false;
    }
    
    return true;
}

void InferenceManager::log_inference_metrics(const std::string& metric_name, float value) {
    spdlog::info("Inference metric - {}: {:.2f}", metric_name, value);
}

bool InferenceManager::apply_auto_optimization() {
    // Monitor performance for a short period
    start_monitoring();
    std::this_thread::sleep_for(std::chrono::seconds(5));
    auto metrics = get_performance_metrics();
    stop_monitoring();
    
    // If performance is below threshold, try to optimize
    if (metrics["average_inference_time_ms"] > 100.0f) {
        return enable_auto_optimization();
    }
    
    return true;
}

} // namespace cogniware 