#include <gtest/gtest.h>
#include "optimization/model_optimizer.h"
#include <torch/torch.h>

namespace cognidream {
namespace test {

class ModelOptimizerTest : public ::testing::Test {
protected:
    void SetUp() override {
        optimizer = &ModelOptimizer::getInstance();
    }

    ModelOptimizer* optimizer;
};

TEST_F(ModelOptimizerTest, OptimizeModel) {
    nlohmann::json config = {
        {"quantization", "int8"},
        {"pruning", {{"sparsity", 0.5}}},
        {"fuse_operations", true}
    };

    EXPECT_TRUE(optimizer->optimizeModel("test_model", config));
}

TEST_F(ModelOptimizerTest, QuantizeModel) {
    EXPECT_TRUE(optimizer->quantizeModel("test_model", "int8"));
    EXPECT_FALSE(optimizer->quantizeModel("test_model", "invalid_precision"));
}

TEST_F(ModelOptimizerTest, PruneModel) {
    EXPECT_TRUE(optimizer->pruneModel("test_model", 0.5));
    EXPECT_FALSE(optimizer->pruneModel("test_model", -0.1));
    EXPECT_FALSE(optimizer->pruneModel("test_model", 1.1));
}

TEST_F(ModelOptimizerTest, FuseOperations) {
    EXPECT_TRUE(optimizer->fuseOperations("test_model"));
}

TEST_F(ModelOptimizerTest, EnableCaching) {
    EXPECT_TRUE(optimizer->enableCaching("test_model"));
}

TEST_F(ModelOptimizerTest, OptimizeMemoryUsage) {
    EXPECT_TRUE(optimizer->optimizeMemoryUsage("test_model"));
}

TEST_F(ModelOptimizerTest, EnableParallelProcessing) {
    EXPECT_TRUE(optimizer->enableParallelProcessing("test_model"));
}

TEST_F(ModelOptimizerTest, AnalyzeModelPerformance) {
    auto metrics = optimizer->analyzeModelPerformance("test_model");
    EXPECT_FALSE(metrics.empty());
    EXPECT_TRUE(metrics.contains("model_size"));
    EXPECT_TRUE(metrics.contains("num_parameters"));
}

TEST_F(ModelOptimizerTest, GetOptimizationStats) {
    auto stats = optimizer->getOptimizationStats("test_model");
    EXPECT_FALSE(stats.empty());
}

TEST_F(ModelOptimizerTest, GetAvailableOptimizations) {
    auto optimizations = optimizer->getAvailableOptimizations("test_model");
    EXPECT_FALSE(optimizations.empty());
    EXPECT_TRUE(std::find(optimizations.begin(), optimizations.end(), "quantization") != optimizations.end());
    EXPECT_TRUE(std::find(optimizations.begin(), optimizations.end(), "pruning") != optimizations.end());
}

} // namespace test
} // namespace cognidream 