#include "model_optimizer.h"
#include <spdlog/spdlog.h>
#include <torch/csrc/jit/passes/frozen_conv_folding.h>
#include <torch/csrc/jit/passes/frozen_linear_folding.h>
#include <torch/csrc/jit/passes/frozen_graph_optimizations.h>
#include <torch/csrc/jit/passes/quantization.h>

namespace cognidream {

ModelOptimizer& ModelOptimizer::getInstance() {
    static ModelOptimizer instance;
    return instance;
}

bool ModelOptimizer::optimizeModel(const std::string& model_id, const nlohmann::json& config) {
    try {
        if (!validateOptimizationConfig(config)) {
            spdlog::error("Invalid optimization configuration for model {}", model_id);
            return false;
        }

        auto model = loadModel(model_id);
        if (!model) {
            spdlog::error("Failed to load model {}", model_id);
            return false;
        }

        // Apply optimizations based on config
        if (config.contains("quantization")) {
            if (!quantizeModel(model_id, config["quantization"])) {
                spdlog::error("Failed to quantize model {}", model_id);
                return false;
            }
        }

        if (config.contains("pruning")) {
            if (!pruneModel(model_id, config["pruning"]["sparsity"])) {
                spdlog::error("Failed to prune model {}", model_id);
                return false;
            }
        }

        if (config.contains("fuse_operations") && config["fuse_operations"]) {
            if (!fuseOperations(model_id)) {
                spdlog::error("Failed to fuse operations for model {}", model_id);
                return false;
            }
        }

        // Save optimized model
        saveOptimizedModel(model_id, model);
        optimization_configs_[model_id] = config;
        updatePerformanceStats(model_id);

        spdlog::info("Successfully optimized model {}", model_id);
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Error optimizing model {}: {}", model_id, e.what());
        return false;
    }
}

bool ModelOptimizer::quantizeModel(const std::string& model_id, const std::string& precision) {
    try {
        auto model = loadModel(model_id);
        if (!model) {
            return false;
        }

        // Convert model to the specified precision
        if (precision == "int8") {
            model = torch::quantization::quantize_dynamic(model);
        } else if (precision == "int4") {
            // Implement int4 quantization
            // This is a placeholder for actual implementation
            spdlog::warn("Int4 quantization not yet implemented");
            return false;
        } else {
            spdlog::error("Unsupported quantization precision: {}", precision);
            return false;
        }

        saveOptimizedModel(model_id, model);
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Error quantizing model {}: {}", model_id, e.what());
        return false;
    }
}

bool ModelOptimizer::pruneModel(const std::string& model_id, float sparsity) {
    try {
        auto model = loadModel(model_id);
        if (!model) {
            return false;
        }

        // Apply magnitude-based pruning
        auto parameters = model.parameters();
        for (auto& param : parameters) {
            if (param.dim() > 1) {  // Only prune weight matrices
                auto threshold = torch::quantile(torch::abs(param), sparsity);
                auto mask = torch::abs(param) > threshold;
                param.mul_(mask);
            }
        }

        saveOptimizedModel(model_id, model);
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Error pruning model {}: {}", model_id, e.what());
        return false;
    }
}

bool ModelOptimizer::fuseOperations(const std::string& model_id) {
    try {
        auto model = loadModel(model_id);
        if (!model) {
            return false;
        }

        // Apply operation fusion optimizations
        torch::jit::FrozenConvFolding(model);
        torch::jit::FrozenLinearFolding(model);
        torch::jit::OptimizeFrozenGraph(model);

        saveOptimizedModel(model_id, model);
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Error fusing operations for model {}: {}", model_id, e.what());
        return false;
    }
}

bool ModelOptimizer::enableCaching(const std::string& model_id) {
    try {
        auto model = loadModel(model_id);
        if (!model) {
            return false;
        }

        // Enable JIT caching
        model.eval();
        model = torch::jit::optimize_for_inference(model);

        saveOptimizedModel(model_id, model);
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Error enabling caching for model {}: {}", model_id, e.what());
        return false;
    }
}

bool ModelOptimizer::optimizeMemoryUsage(const std::string& model_id) {
    try {
        auto model = loadModel(model_id);
        if (!model) {
            return false;
        }

        // Enable memory optimizations
        torch::jit::FrozenGraphOptimizations(model);
        
        // Enable gradient checkpointing if training
        if (model.is_training()) {
            model.enable_gradient_checkpointing();
        }

        saveOptimizedModel(model_id, model);
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Error optimizing memory usage for model {}: {}", model_id, e.what());
        return false;
    }
}

bool ModelOptimizer::enableParallelProcessing(const std::string& model_id) {
    try {
        auto model = loadModel(model_id);
        if (!model) {
            return false;
        }

        // Enable parallel processing
        torch::jit::FrozenGraphOptimizations(model);
        model = torch::jit::optimize_for_inference(model);

        saveOptimizedModel(model_id, model);
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Error enabling parallel processing for model {}: {}", model_id, e.what());
        return false;
    }
}

nlohmann::json ModelOptimizer::analyzeModelPerformance(const std::string& model_id) {
    try {
        auto model = loadModel(model_id);
        if (!model) {
            return nlohmann::json::object();
        }

        // Collect performance metrics
        nlohmann::json metrics;
        metrics["model_size"] = model.size_bytes();
        metrics["num_parameters"] = model.parameters().size();
        metrics["optimization_config"] = optimization_configs_[model_id];
        metrics["performance_stats"] = performance_stats_[model_id];

        return metrics;
    } catch (const std::exception& e) {
        spdlog::error("Error analyzing model performance for {}: {}", model_id, e.what());
        return nlohmann::json::object();
    }
}

nlohmann::json ModelOptimizer::getOptimizationStats(const std::string& model_id) {
    return performance_stats_[model_id];
}

std::vector<std::string> ModelOptimizer::getAvailableOptimizations(const std::string& model_id) {
    std::vector<std::string> optimizations = {
        "quantization",
        "pruning",
        "fuse_operations",
        "caching",
        "memory_optimization",
        "parallel_processing"
    };
    return optimizations;
}

bool ModelOptimizer::validateOptimizationConfig(const nlohmann::json& config) const {
    // Validate required fields and their types
    if (config.contains("quantization")) {
        if (!config["quantization"].is_string()) {
            return false;
        }
    }
    if (config.contains("pruning")) {
        if (!config["pruning"].contains("sparsity") || 
            !config["pruning"]["sparsity"].is_number()) {
            return false;
        }
    }
    return true;
}

void ModelOptimizer::updatePerformanceStats(const std::string& model_id) {
    auto model = loadModel(model_id);
    if (!model) {
        return;
    }

    performance_stats_[model_id] = {
        {"model_size", model.size_bytes()},
        {"num_parameters", model.parameters().size()},
        {"optimization_time", std::chrono::system_clock::now().time_since_epoch().count()}
    };
}

bool ModelOptimizer::applyOptimization(const std::string& model_id, const std::string& optimization_type) {
    if (optimization_type == "quantization") {
        return quantizeModel(model_id, "int8");
    } else if (optimization_type == "pruning") {
        return pruneModel(model_id, 0.5f);  // Default sparsity
    } else if (optimization_type == "fuse_operations") {
        return fuseOperations(model_id);
    }
    return false;
}

torch::jit::script::Module ModelOptimizer::loadModel(const std::string& model_id) {
    try {
        if (optimized_models_.contains(model_id)) {
            return optimized_models_[model_id];
        }
        // Load model from disk or other storage
        // This is a placeholder for actual implementation
        return torch::jit::script::Module();
    } catch (const std::exception& e) {
        spdlog::error("Error loading model {}: {}", model_id, e.what());
        return torch::jit::script::Module();
    }
}

void ModelOptimizer::saveOptimizedModel(const std::string& model_id, const torch::jit::script::Module& model) {
    optimized_models_[model_id] = model;
}

} // namespace cognidream 