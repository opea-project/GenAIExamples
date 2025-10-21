#include <gtest/gtest.h>
#include "transformer_block.h"
#include "gpu_memory_manager.h"
#include <vector>
#include <random>

class TransformerBlockTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Initialize parameters
        hidden_size = 768;
        num_heads = 12;
        intermediate_size = 3072;
        
        // Create transformer block
        block = std::make_unique<TransformerBlock>(hidden_size, num_heads, intermediate_size);
        
        // Initialize weights with random values
        std::vector<float> weights(block->getWorkspaceSize() / sizeof(float));
        std::random_device rd;
        std::mt19937 gen(rd());
        std::normal_distribution<float> dist(0.0f, 0.02f);
        
        for (float& w : weights) {
            w = dist(gen);
        }
        
        // Copy weights to GPU
        auto& memory_manager = GPUMemoryManager::getInstance();
        void* d_weights = memory_manager.allocate(block->getWorkspaceSize());
        memory_manager.copyHostToDevice(d_weights, weights.data(), block->getWorkspaceSize());
        
        // Initialize transformer block
        block->initialize(d_weights);
        memory_manager.free(d_weights);
    }
    
    void TearDown() override {
        block.reset();
    }
    
    size_t hidden_size;
    size_t num_heads;
    size_t intermediate_size;
    std::unique_ptr<TransformerBlock> block;
};

TEST_F(TransformerBlockTest, Initialization) {
    EXPECT_EQ(block->getHiddenSize(), hidden_size);
    EXPECT_EQ(block->getNumHeads(), num_heads);
    EXPECT_EQ(block->getIntermediateSize(), intermediate_size);
    EXPECT_GT(block->getWorkspaceSize(), 0);
    EXPECT_GT(block->getKVCacheSize(), 0);
}

TEST_F(TransformerBlockTest, ForwardPass) {
    const size_t batch_size = 2;
    const size_t seq_length = 32;
    const size_t input_size = batch_size * seq_length * hidden_size;
    
    // Create input data
    std::vector<float> input_data(input_size);
    std::random_device rd;
    std::mt19937 gen(rd());
    std::normal_distribution<float> dist(0.0f, 1.0f);
    
    for (float& x : input_data) {
        x = dist(gen);
    }
    
    // Allocate GPU memory
    auto& memory_manager = GPUMemoryManager::getInstance();
    void* d_input = memory_manager.allocate(input_size * sizeof(float));
    void* d_output = memory_manager.allocate(input_size * sizeof(float));
    
    // Copy input to GPU
    memory_manager.copyHostToDevice(d_input, input_data.data(), input_size * sizeof(float));
    
    // Allocate KV cache
    void* kv_cache = block->allocateKVCache(batch_size, seq_length);
    
    // Create CUDA stream
    cudaStream_t stream = memory_manager.createStream();
    
    // Run forward pass
    block->forward(d_output, d_input, kv_cache, batch_size, seq_length, stream);
    
    // Synchronize
    memory_manager.synchronizeStream(stream);
    
    // Copy output back to host
    std::vector<float> output_data(input_size);
    memory_manager.copyDeviceToHost(output_data.data(), d_output, input_size * sizeof(float));
    
    // Verify output
    for (size_t i = 0; i < input_size; ++i) {
        EXPECT_NE(output_data[i], 0.0f);
    }
    
    // Clean up
    block->freeKVCache(kv_cache);
    memory_manager.free(d_input);
    memory_manager.free(d_output);
    memory_manager.destroyStream(stream);
}

TEST_F(TransformerBlockTest, KVCacheManagement) {
    const size_t batch_size = 2;
    const size_t seq_length = 32;
    
    // Allocate KV cache
    void* kv_cache = block->allocateKVCache(batch_size, seq_length);
    EXPECT_NE(kv_cache, nullptr);
    
    // Update KV cache
    const size_t input_size = batch_size * seq_length * hidden_size;
    std::vector<float> input_data(input_size, 1.0f);
    
    auto& memory_manager = GPUMemoryManager::getInstance();
    void* d_input = memory_manager.allocate(input_size * sizeof(float));
    memory_manager.copyHostToDevice(d_input, input_data.data(), input_size * sizeof(float));
    
    cudaStream_t stream = memory_manager.createStream();
    block->updateKVCache(kv_cache, d_input, batch_size, seq_length, stream);
    memory_manager.synchronizeStream(stream);
    
    // Free resources
    block->freeKVCache(kv_cache);
    memory_manager.free(d_input);
    memory_manager.destroyStream(stream);
}

TEST_F(TransformerBlockTest, AttentionComputation) {
    const size_t batch_size = 2;
    const size_t seq_length = 32;
    const size_t input_size = batch_size * seq_length * hidden_size;
    
    // Create input data
    std::vector<float> input_data(input_size);
    std::random_device rd;
    std::mt19937 gen(rd());
    std::normal_distribution<float> dist(0.0f, 1.0f);
    
    for (float& x : input_data) {
        x = dist(gen);
    }
    
    // Allocate GPU memory
    auto& memory_manager = GPUMemoryManager::getInstance();
    void* d_input = memory_manager.allocate(input_size * sizeof(float));
    void* d_output = memory_manager.allocate(input_size * sizeof(float));
    
    // Copy input to GPU
    memory_manager.copyHostToDevice(d_input, input_data.data(), input_size * sizeof(float));
    
    // Create CUDA stream
    cudaStream_t stream = memory_manager.createStream();
    
    // Compute attention
    block->computeAttention(d_output, d_input, batch_size, seq_length, stream);
    
    // Synchronize
    memory_manager.synchronizeStream(stream);
    
    // Copy output back to host
    std::vector<float> output_data(input_size);
    memory_manager.copyDeviceToHost(output_data.data(), d_output, input_size * sizeof(float));
    
    // Verify output
    for (size_t i = 0; i < input_size; ++i) {
        EXPECT_NE(output_data[i], 0.0f);
    }
    
    // Clean up
    memory_manager.free(d_input);
    memory_manager.free(d_output);
    memory_manager.destroyStream(stream);
}

TEST_F(TransformerBlockTest, FFNComputation) {
    const size_t batch_size = 2;
    const size_t seq_length = 32;
    const size_t input_size = batch_size * seq_length * hidden_size;
    
    // Create input data
    std::vector<float> input_data(input_size);
    std::random_device rd;
    std::mt19937 gen(rd());
    std::normal_distribution<float> dist(0.0f, 1.0f);
    
    for (float& x : input_data) {
        x = dist(gen);
    }
    
    // Allocate GPU memory
    auto& memory_manager = GPUMemoryManager::getInstance();
    void* d_input = memory_manager.allocate(input_size * sizeof(float));
    void* d_output = memory_manager.allocate(input_size * sizeof(float));
    
    // Copy input to GPU
    memory_manager.copyHostToDevice(d_input, input_data.data(), input_size * sizeof(float));
    
    // Create CUDA stream
    cudaStream_t stream = memory_manager.createStream();
    
    // Compute FFN
    block->computeFFN(d_output, d_input, batch_size, seq_length, stream);
    
    // Synchronize
    memory_manager.synchronizeStream(stream);
    
    // Copy output back to host
    std::vector<float> output_data(input_size);
    memory_manager.copyDeviceToHost(output_data.data(), d_output, input_size * sizeof(float));
    
    // Verify output
    for (size_t i = 0; i < input_size; ++i) {
        EXPECT_NE(output_data[i], 0.0f);
    }
    
    // Clean up
    memory_manager.free(d_input);
    memory_manager.free(d_output);
    memory_manager.destroyStream(stream);
}

TEST_F(TransformerBlockTest, LayerNormComputation) {
    const size_t batch_size = 2;
    const size_t seq_length = 32;
    const size_t input_size = batch_size * seq_length * hidden_size;
    
    // Create input data
    std::vector<float> input_data(input_size);
    std::random_device rd;
    std::mt19937 gen(rd());
    std::normal_distribution<float> dist(0.0f, 1.0f);
    
    for (float& x : input_data) {
        x = dist(gen);
    }
    
    // Allocate GPU memory
    auto& memory_manager = GPUMemoryManager::getInstance();
    void* d_input = memory_manager.allocate(input_size * sizeof(float));
    void* d_output = memory_manager.allocate(input_size * sizeof(float));
    
    // Copy input to GPU
    memory_manager.copyHostToDevice(d_input, input_data.data(), input_size * sizeof(float));
    
    // Create CUDA stream
    cudaStream_t stream = memory_manager.createStream();
    
    // Compute layer norm
    block->computeLayerNorm(d_output, d_input, batch_size, seq_length, stream);
    
    // Synchronize
    memory_manager.synchronizeStream(stream);
    
    // Copy output back to host
    std::vector<float> output_data(input_size);
    memory_manager.copyDeviceToHost(output_data.data(), d_output, input_size * sizeof(float));
    
    // Verify output
    for (size_t i = 0; i < input_size; ++i) {
        EXPECT_NE(output_data[i], 0.0f);
    }
    
    // Clean up
    memory_manager.free(d_input);
    memory_manager.free(d_output);
    memory_manager.destroyStream(stream);
}

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
} 