#include <gtest/gtest.h>
#include <torch/script.h>
#include <torch/torch.h>
#include <memory>
#include <string>
#include <map>
#include "optimization/model_optimizer.h"

namespace cogniware {
namespace {

TEST(ModelOptimizerTest, OptimizeModel) {
    // Create a dummy model
    auto model = torch::jit::script(torch::nn::Linear(10, 10));
    std::string model_path = "dummy_model.pt";
    torch::jit::save(model, model_path);

    // Create optimizer and load the model
    ModelOptimizer optimizer;
    ASSERT_TRUE(optimizer.load_model(model_path, "dummy"));

    // Configure optimization settings
    std::map<std::string, std::string> config;
    config["quantization"] = "8bit";
    config["pruning"] = "structured";
    config["target_sparsity"] = "0.5";
    config["distillation"] = "enabled";
    config["teacher_model_path"] = "dummy_teacher.pt";
    config["temperature"] = "1.0";
    config["alpha"] = "0.5";

    // Initialize optimization
    ASSERT_TRUE(optimizer.initialize_optimization(config));

    // Run optimization pipeline
    ASSERT_TRUE(optimizer.optimize_model());

    // Clean up
    std::remove(model_path.c_str());
}

} // namespace
} // namespace cogniware 