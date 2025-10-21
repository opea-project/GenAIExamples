/**
 * @file test_inference_engine.cpp
 * @brief Tests for the inference engine
 */

#include <gtest/gtest.h>
#include "llm_inference_core/inference_pipeline/inference_engine.hpp"
#include "llm_inference_core/model_loader/gguf_loader.hpp"
#include <fstream>
#include <filesystem>

namespace cogniware {
namespace test {

class InferenceEngineTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Create temporary model file
        model_path_ = std::filesystem::temp_directory_path() / "test_model.gguf";
        std::ofstream model_file(model_path_, std::ios::binary);
        
        // Write GGUF magic number
        model_file.write("GGUF", 4);
        
        // Write version (1)
        uint32_t version = 1;
        model_file.write(reinterpret_cast<char*>(&version), sizeof(version));
        
        // Write tensor count (1)
        uint64_t tensor_count = 1;
        model_file.write(reinterpret_cast<char*>(&tensor_count), sizeof(tensor_count));
        
        // Write metadata count (1)
        uint64_t metadata_count = 1;
        model_file.write(reinterpret_cast<char*>(&metadata_count), sizeof(metadata_count));
        
        // Write dummy tensor data
        std::vector<float> dummy_tensor(1000, 0.0f);
        model_file.write(reinterpret_cast<char*>(dummy_tensor.data()), dummy_tensor.size() * sizeof(float));
        
        model_file.close();

        // Create model loader
        model_loader_ = std::make_shared<GGUFLoader>(model_path_.string());
        ASSERT_TRUE(model_loader_->load());

        // Create inference engine
        engine_ = std::make_unique<InferenceEngine>(model_loader_);
        ASSERT_TRUE(engine_->initialize());
    }

    void TearDown() override {
        // Clean up temporary files
        std::filesystem::remove(model_path_);
    }

    std::filesystem::path model_path_;
    std::shared_ptr<GGUFLoader> model_loader_;
    std::unique_ptr<InferenceEngine> engine_;
};

TEST_F(InferenceEngineTest, Generate) {
    std::string prompt = "Hello, world!";
    std::string generated = engine_->generate(
        prompt,
        10,  // max_tokens
        0.7f,  // temperature
        50,  // top_k
        0.9f,  // top_p
        1,  // num_beams
        1,  // num_return_sequences
        {"</s>"}  // stop_sequences
    );

    // Since we're using dummy tensors, the output will be empty
    ASSERT_TRUE(generated.empty());
}

TEST_F(InferenceEngineTest, GetMetadata) {
    auto metadata = engine_->getMetadata();
    ASSERT_FALSE(metadata.empty());
}

TEST_F(InferenceEngineTest, GetParameters) {
    auto parameters = engine_->getParameters();
    ASSERT_FALSE(parameters.empty());
}

TEST_F(InferenceEngineTest, GetVocabulary) {
    auto vocabulary = engine_->getVocabulary();
    ASSERT_FALSE(vocabulary.empty());
}

TEST_F(InferenceEngineTest, GetArchitecture) {
    std::string architecture = engine_->getArchitecture();
    ASSERT_FALSE(architecture.empty());
}

TEST_F(InferenceEngineTest, GetContextSize) {
    size_t context_size = engine_->getContextSize();
    ASSERT_GT(context_size, 0);
}

TEST_F(InferenceEngineTest, GetEmbeddingDim) {
    size_t embedding_dim = engine_->getEmbeddingDim();
    ASSERT_GT(embedding_dim, 0);
}

TEST_F(InferenceEngineTest, GetNumLayers) {
    size_t num_layers = engine_->getNumLayers();
    ASSERT_GT(num_layers, 0);
}

TEST_F(InferenceEngineTest, GetNumHeads) {
    size_t num_heads = engine_->getNumHeads();
    ASSERT_GT(num_heads, 0);
}

TEST_F(InferenceEngineTest, GetNumKVHeads) {
    size_t num_kv_heads = engine_->getNumKVHeads();
    ASSERT_GT(num_kv_heads, 0);
}

TEST_F(InferenceEngineTest, GetIntermediateSize) {
    size_t intermediate_size = engine_->getIntermediateSize();
    ASSERT_GT(intermediate_size, 0);
}

TEST_F(InferenceEngineTest, GetRotaryDim) {
    size_t rotary_dim = engine_->getRotaryDim();
    ASSERT_GT(rotary_dim, 0);
}

TEST_F(InferenceEngineTest, GetQuantizationType) {
    std::string quantization_type = engine_->getQuantizationType();
    ASSERT_FALSE(quantization_type.empty());
}

TEST_F(InferenceEngineTest, GetMemoryUsage) {
    size_t memory_usage = engine_->getMemoryUsage();
    ASSERT_GT(memory_usage, 0);
}

TEST_F(InferenceEngineTest, IsInitialized) {
    ASSERT_TRUE(engine_->isInitialized());
}

TEST_F(InferenceEngineTest, Shutdown) {
    engine_->shutdown();
    ASSERT_FALSE(engine_->isInitialized());
}

} // namespace test
} // namespace cogniware 