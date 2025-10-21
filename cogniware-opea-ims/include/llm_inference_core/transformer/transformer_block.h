#pragma once

#include <cuda_runtime.h>
#include <memory>
#include <vector>
#include "llm_inference_core/cuda_runtime/gpu_memory_manager.h"

namespace cogniware {

class TransformerBlock {
public:
    struct Config {
        int hiddenSize;
        int numHeads;
        int intermediateSize;
        float dropout;
        bool useBias;
        bool useLayerNorm;
        std::string activationType;
    };

    TransformerBlock(const Config& config);
    ~TransformerBlock();

    // Initialize the block with weights
    bool initialize(const std::vector<float>& weights);
    
    // Forward pass
    bool forward(const float* input,
                float* output,
                int batchSize,
                int seqLength,
                cudaStream_t stream = nullptr);
    
    // KV Cache management
    bool allocateKVCache(int maxBatchSize, int maxSeqLength);
    void freeKVCache();
    
    // Get configuration
    const Config& getConfig() const { return config_; }
    
    // Get memory requirements
    size_t getWeightSize() const;
    size_t getKVCacheSize() const;
    
    // Error handling
    const char* getLastError() const;
    void clearLastError();

private:
    Config config_;
    std::vector<float> weights_;
    float* d_weights_;
    float* d_kv_cache_;
    std::string lastError_;
    
    // Helper methods
    bool initializeWeights();
    bool initializeKVCache();
    void cleanup();
    
    // CUDA kernels (to be implemented in .cu file)
    bool launchAttentionKernel(const float* input,
                             float* output,
                             int batchSize,
                             int seqLength,
                             cudaStream_t stream);
    
    bool launchFFNKernel(const float* input,
                        float* output,
                        int batchSize,
                        int seqLength,
                        cudaStream_t stream);
    
    bool launchLayerNormKernel(const float* input,
                              float* output,
                              int batchSize,
                              int seqLength,
                              cudaStream_t stream);
};

} // namespace cogniware 