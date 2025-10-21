#include <gtest/gtest.h>
#include "llm_inference_core.h"
#include <vector>
#include <random>

namespace cogniware {
namespace test {

class LLMInferenceCoreTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Create a test configuration
        config_.max_sequence_length = 512;
        config_.vocab_size = 50000;
        config_.hidden_size = 768;
        config_.num_layers = 12;
        config_.num_heads = 12;
        config_.dropout_rate = 0.1f;
        config_.use_fp16 = false;
        
        // Initialize the core
        core_ = std::make_unique<LLMInferenceCore>(config_, 0);
    }
    
    void TearDown() override {
        core_.reset();
    }
    
    LLMConfig config_;
    std::unique_ptr<LLMInferenceCore> core_;
    
    // Helper function to generate random input tokens
    std::vector<int> generate_random_input(int length) {
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_int_distribution<> dis(0, config_.vocab_size - 1);
        
        std::vector<int> tokens(length);
        for (int i = 0; i < length; i++) {
            tokens[i] = dis(gen);
        }
        return tokens;
    }
};

TEST_F(LLMInferenceCoreTest, Initialization) {
    EXPECT_EQ(core_->get_config().max_sequence_length, config_.max_sequence_length);
    EXPECT_EQ(core_->get_config().vocab_size, config_.vocab_size);
    EXPECT_EQ(core_->get_config().hidden_size, config_.hidden_size);
    EXPECT_EQ(core_->get_config().num_layers, config_.num_layers);
    EXPECT_EQ(core_->get_config().num_heads, config_.num_heads);
}

TEST_F(LLMInferenceCoreTest, ProcessEmptyInput) {
    EXPECT_THROW(core_->process(std::vector<int>()), std::runtime_error);
}

TEST_F(LLMInferenceCoreTest, ProcessValidInput) {
    auto input = generate_random_input(10);
    auto output = core_->process(input);
    
    EXPECT_EQ(output.size(), input.size());
    for (size_t i = 0; i < output.size(); i++) {
        EXPECT_GE(output[i], 0);
        EXPECT_LT(output[i], config_.vocab_size);
    }
}

TEST_F(LLMInferenceCoreTest, ProcessLongInput) {
    auto input = generate_random_input(config_.max_sequence_length);
    auto output = core_->process(input);
    
    EXPECT_EQ(output.size(), input.size());
}

TEST_F(LLMInferenceCoreTest, ProcessInvalidInput) {
    std::vector<int> input(config_.max_sequence_length + 1, 0);
    EXPECT_THROW(core_->process(input), std::runtime_error);
}

TEST_F(LLMInferenceCoreTest, ProcessInvalidToken) {
    std::vector<int> input = {config_.vocab_size};
    EXPECT_THROW(core_->process(input), std::runtime_error);
}

TEST_F(LLMInferenceCoreTest, ProcessMultipleRequests) {
    auto input1 = generate_random_input(10);
    auto input2 = generate_random_input(20);
    
    auto output1 = core_->process(input1);
    auto output2 = core_->process(input2);
    
    EXPECT_EQ(output1.size(), input1.size());
    EXPECT_EQ(output2.size(), input2.size());
}

TEST_F(LLMInferenceCoreTest, ProcessConcurrentRequests) {
    const int num_threads = 4;
    const int input_length = 10;
    std::vector<std::thread> threads;
    std::vector<std::vector<int>> outputs(num_threads);
    
    for (int i = 0; i < num_threads; i++) {
        threads.emplace_back([this, i, input_length, &outputs]() {
            auto input = generate_random_input(input_length);
            outputs[i] = core_->process(input);
        });
    }
    
    for (auto& thread : threads) {
        thread.join();
    }
    
    for (const auto& output : outputs) {
        EXPECT_EQ(output.size(), input_length);
    }
}

} // namespace test
} // namespace cogniware 