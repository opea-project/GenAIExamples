/**
 * @file test_gguf_loader.cpp
 * @brief Tests for the GGUF loader
 */

#include <gtest/gtest.h>
#include "llm_inference_core/model_loader/gguf_loader.hpp"
#include <fstream>
#include <filesystem>

namespace cogniware {
namespace test {

class GGUFLoaderTest : public ::testing::Test {
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

        // Create loader
        loader_ = std::make_unique<GGUFLoader>(model_path_.string());
    }

    void TearDown() override {
        // Clean up temporary files
        std::filesystem::remove(model_path_);
    }

    std::filesystem::path model_path_;
    std::unique_ptr<GGUFLoader> loader_;
};

TEST_F(GGUFLoaderTest, Load) {
    ASSERT_TRUE(loader_->load());
    ASSERT_TRUE(loader_->isLoaded());
}

TEST_F(GGUFLoaderTest, Unload) {
    ASSERT_TRUE(loader_->load());
    loader_->unload();
    ASSERT_FALSE(loader_->isLoaded());
}

TEST_F(GGUFLoaderTest, GetMetadata) {
    ASSERT_TRUE(loader_->load());
    auto metadata = loader_->getMetadata();
    ASSERT_FALSE(metadata.empty());
}

TEST_F(GGUFLoaderTest, GetParameters) {
    ASSERT_TRUE(loader_->load());
    auto parameters = loader_->getParameters();
    ASSERT_FALSE(parameters.empty());
}

TEST_F(GGUFLoaderTest, GetTensors) {
    ASSERT_TRUE(loader_->load());
    auto tensors = loader_->getTensors();
    ASSERT_FALSE(tensors.empty());
    ASSERT_EQ(tensors.size(), 1000);  // Size of our dummy tensor
}

TEST_F(GGUFLoaderTest, GetVocabulary) {
    ASSERT_TRUE(loader_->load());
    auto vocabulary = loader_->getVocabulary();
    ASSERT_FALSE(vocabulary.empty());
}

TEST_F(GGUFLoaderTest, GetArchitecture) {
    ASSERT_TRUE(loader_->load());
    std::string architecture = loader_->getArchitecture();
    ASSERT_FALSE(architecture.empty());
}

TEST_F(GGUFLoaderTest, GetContextSize) {
    ASSERT_TRUE(loader_->load());
    size_t context_size = loader_->getContextSize();
    ASSERT_GT(context_size, 0);
}

TEST_F(GGUFLoaderTest, GetEmbeddingDim) {
    ASSERT_TRUE(loader_->load());
    size_t embedding_dim = loader_->getEmbeddingDim();
    ASSERT_GT(embedding_dim, 0);
}

TEST_F(GGUFLoaderTest, GetNumLayers) {
    ASSERT_TRUE(loader_->load());
    size_t num_layers = loader_->getNumLayers();
    ASSERT_GT(num_layers, 0);
}

TEST_F(GGUFLoaderTest, GetNumHeads) {
    ASSERT_TRUE(loader_->load());
    size_t num_heads = loader_->getNumHeads();
    ASSERT_GT(num_heads, 0);
}

TEST_F(GGUFLoaderTest, GetNumKVHeads) {
    ASSERT_TRUE(loader_->load());
    size_t num_kv_heads = loader_->getNumKVHeads();
    ASSERT_GT(num_kv_heads, 0);
}

TEST_F(GGUFLoaderTest, GetIntermediateSize) {
    ASSERT_TRUE(loader_->load());
    size_t intermediate_size = loader_->getIntermediateSize();
    ASSERT_GT(intermediate_size, 0);
}

TEST_F(GGUFLoaderTest, GetRotaryDim) {
    ASSERT_TRUE(loader_->load());
    size_t rotary_dim = loader_->getRotaryDim();
    ASSERT_GT(rotary_dim, 0);
}

TEST_F(GGUFLoaderTest, GetQuantizationType) {
    ASSERT_TRUE(loader_->load());
    std::string quantization_type = loader_->getQuantizationType();
    ASSERT_FALSE(quantization_type.empty());
}

TEST_F(GGUFLoaderTest, GetFileSize) {
    ASSERT_TRUE(loader_->load());
    size_t file_size = loader_->getFileSize();
    ASSERT_GT(file_size, 0);
}

TEST_F(GGUFLoaderTest, GetMemoryUsage) {
    ASSERT_TRUE(loader_->load());
    size_t memory_usage = loader_->getMemoryUsage();
    ASSERT_GT(memory_usage, 0);
}

TEST_F(GGUFLoaderTest, InvalidFile) {
    // Create loader with non-existent file
    auto invalid_loader = std::make_unique<GGUFLoader>("nonexistent.gguf");
    ASSERT_FALSE(invalid_loader->load());
    ASSERT_FALSE(invalid_loader->isLoaded());
}

TEST_F(GGUFLoaderTest, InvalidMagic) {
    // Create temporary file with invalid magic number
    auto invalid_path = std::filesystem::temp_directory_path() / "invalid.gguf";
    std::ofstream invalid_file(invalid_path, std::ios::binary);
    invalid_file.write("INVALID", 7);
    invalid_file.close();

    auto invalid_loader = std::make_unique<GGUFLoader>(invalid_path.string());
    ASSERT_FALSE(invalid_loader->load());
    ASSERT_FALSE(invalid_loader->isLoaded());

    std::filesystem::remove(invalid_path);
}

} // namespace test
} // namespace cogniware 