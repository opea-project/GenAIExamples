#include <gtest/gtest.h>
#include <torch/script.h>
#include <torch/torch.h>
#include <memory>
#include "inference/inference_manager.h"

namespace cogniware {
namespace {

class InferenceManagerTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Create a dummy model
        auto model = torch::jit::script(torch::nn::Linear(10, 10));
        model_path_ = "dummy_model.pt";
        torch::jit::save(model, model_path_);
        
        // Initialize inference manager
        manager_ = std::make_unique<InferenceManager>();
    }
    
    void TearDown() override {
        std::remove(model_path_.c_str());
    }
    
    std::string model_path_;
    std::unique_ptr<InferenceManager> manager_;
};

TEST_F(InferenceManagerTest, LoadModel) {
    EXPECT_TRUE(manager_->load_model(model_path_, "dummy"));
}

TEST_F(InferenceManagerTest, OptimizeModel) {
    ASSERT_TRUE(manager_->load_model(model_path_, "dummy"));
    
    std::map<std::string, std::string> config = {
        {"quantization", "8bit"},
        {"pruning", "structured"},
        {"target_sparsity", "0.3"}
    };
    
    EXPECT_TRUE(manager_->optimize_model(config));
}

TEST_F(InferenceManagerTest, RunInference) {
    ASSERT_TRUE(manager_->load_model(model_path_, "dummy"));
    
    auto input = torch::randn({1, 10}).to(torch::kCUDA);
    auto output = manager_->run_inference(input);
    
    EXPECT_TRUE(output.defined());
    EXPECT_EQ(output.sizes(), std::vector<int64_t>{1, 10});
}

TEST_F(InferenceManagerTest, RunBatchInference) {
    ASSERT_TRUE(manager_->load_model(model_path_, "dummy"));
    
    std::vector<torch::Tensor> inputs;
    for (int i = 0; i < 3; ++i) {
        inputs.push_back(torch::randn({1, 10}).to(torch::kCUDA));
    }
    
    auto outputs = manager_->run_batch_inference(inputs);
    
    EXPECT_EQ(outputs.size(), inputs.size());
    for (const auto& output : outputs) {
        EXPECT_TRUE(output.defined());
        EXPECT_EQ(output.sizes(), std::vector<int64_t>{1, 10});
    }
}

TEST_F(InferenceManagerTest, PerformanceMonitoring) {
    ASSERT_TRUE(manager_->load_model(model_path_, "dummy"));
    
    manager_->start_monitoring();
    auto input = torch::randn({1, 10}).to(torch::kCUDA);
    manager_->run_inference(input);
    auto metrics = manager_->get_performance_metrics();
    manager_->stop_monitoring();
    
    EXPECT_GT(metrics["profiling_duration_ms"], 0.0f);
}

TEST_F(InferenceManagerTest, AutoOptimization) {
    ASSERT_TRUE(manager_->load_model(model_path_, "dummy"));
    EXPECT_TRUE(manager_->enable_auto_optimization());
}

TEST_F(InferenceManagerTest, SetBatchSize) {
    ASSERT_TRUE(manager_->load_model(model_path_, "dummy"));
    EXPECT_TRUE(manager_->set_batch_size(4));
    EXPECT_FALSE(manager_->set_batch_size(0));
}

TEST_F(InferenceManagerTest, SetPrecision) {
    ASSERT_TRUE(manager_->load_model(model_path_, "dummy"));
    EXPECT_TRUE(manager_->set_precision("fp16"));
    EXPECT_TRUE(manager_->set_precision("int8"));
    EXPECT_FALSE(manager_->set_precision("invalid"));
}

} // namespace
} // namespace cogniware 