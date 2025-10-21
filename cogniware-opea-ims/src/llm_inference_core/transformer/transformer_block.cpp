#include "llm_inference_core/transformer/transformer_block.h"
#include <cuda_runtime.h>
#include <stdexcept>
#include <omp.h>
#include <random>

namespace cogniware {

TransformerBlock::TransformerBlock(const Config& config)
    : config_(config)
    , d_weights_(nullptr)
    , d_kv_cache_(nullptr) {
}

TransformerBlock::~TransformerBlock() {
    cleanup();
}

bool TransformerBlock::initialize(const std::vector<float>& weights) {
    if (weights.size() != getWeightSize()) {
        lastError_ = "Invalid weights size";
        return false;
    }
    
    weights_ = weights;
    return initializeWeights();
}

bool TransformerBlock::forward(const float* input,
                             float* output,
                             int batchSize,
                             int seqLength,
                             cudaStream_t stream) {
    if (!d_weights_ || !d_kv_cache_) {
        lastError_ = "Block not properly initialized";
        return false;
    }
    
    // Temporary buffers for intermediate results
    float* temp1 = nullptr;
    float* temp2 = nullptr;
    
    auto& memManager = GPUMemoryManager::getInstance();
    size_t bufferSize = batchSize * seqLength * config_.hiddenSize * sizeof(float);
    
    temp1 = static_cast<float*>(memManager.allocateFromPool(bufferSize));
    temp2 = static_cast<float*>(memManager.allocateFromPool(bufferSize));
    
    if (!temp1 || !temp2) {
        lastError_ = "Failed to allocate temporary buffers";
        memManager.returnToPool(temp1);
        memManager.returnToPool(temp2);
        return false;
    }
    
    // Layer normalization
    if (!launchLayerNormKernel(input, temp1, batchSize, seqLength, stream)) {
        memManager.returnToPool(temp1);
        memManager.returnToPool(temp2);
        return false;
    }
    
    // Self-attention
    if (!launchAttentionKernel(temp1, temp2, batchSize, seqLength, stream)) {
        memManager.returnToPool(temp1);
        memManager.returnToPool(temp2);
        return false;
    }
    
    // Residual connection
    // TODO: Implement residual connection kernel
    
    // Layer normalization
    if (!launchLayerNormKernel(temp2, temp1, batchSize, seqLength, stream)) {
        memManager.returnToPool(temp1);
        memManager.returnToPool(temp2);
        return false;
    }
    
    // Feed-forward network
    if (!launchFFNKernel(temp1, output, batchSize, seqLength, stream)) {
        memManager.returnToPool(temp1);
        memManager.returnToPool(temp2);
        return false;
    }
    
    // Cleanup
    memManager.returnToPool(temp1);
    memManager.returnToPool(temp2);
    
    return true;
}

bool TransformerBlock::allocateKVCache(int maxBatchSize, int maxSeqLength) {
    if (d_kv_cache_) {
        freeKVCache();
    }
    
    size_t cacheSize = getKVCacheSize();
    auto& memManager = GPUMemoryManager::getInstance();
    
    d_kv_cache_ = static_cast<float*>(memManager.allocate(cacheSize));
    if (!d_kv_cache_) {
        lastError_ = "Failed to allocate KV cache";
        return false;
    }
    
    return true;
}

void TransformerBlock::freeKVCache() {
    if (d_kv_cache_) {
        auto& memManager = GPUMemoryManager::getInstance();
        memManager.deallocate(d_kv_cache_);
        d_kv_cache_ = nullptr;
    }
}

size_t TransformerBlock::getWeightSize() const {
    // Calculate total number of weights
    size_t size = 0;
    
    // Self-attention weights
    size += config_.hiddenSize * config_.hiddenSize * 3;  // Q, K, V projections
    size += config_.hiddenSize * config_.hiddenSize;      // Output projection
    
    // Layer normalization weights
    if (config_.useLayerNorm) {
        size += config_.hiddenSize * 2;  // Scale and bias
    }
    
    // Feed-forward network weights
    size += config_.hiddenSize * config_.intermediateSize;  // First layer
    size += config_.intermediateSize * config_.hiddenSize;  // Second layer
    
    // Biases
    if (config_.useBias) {
        size += config_.hiddenSize * 4;  // Q, K, V, O projections
        size += config_.intermediateSize * 2;  // FFN layers
    }
    
    return size;
}

size_t TransformerBlock::getKVCacheSize() const {
    return config_.hiddenSize * config_.numHeads * 2;  // Key and Value cache
}

const char* TransformerBlock::getLastError() const {
    return lastError_.c_str();
}

void TransformerBlock::clearLastError() {
    lastError_.clear();
}

bool TransformerBlock::initializeWeights() {
    if (weights_.empty()) {
        lastError_ = "No weights provided";
        return false;
    }
    
    auto& memManager = GPUMemoryManager::getInstance();
    size_t weightSize = getWeightSize() * sizeof(float);
    
    d_weights_ = static_cast<float*>(memManager.allocate(weightSize));
    if (!d_weights_) {
        lastError_ = "Failed to allocate device weights";
        return false;
    }
    
    memManager.copyToDevice(d_weights_, weights_.data(), weightSize);
    return true;
}

bool TransformerBlock::initializeKVCache() {
    if (!d_kv_cache_) {
        lastError_ = "KV cache not allocated";
        return false;
    }
    
    // Initialize KV cache to zero
    size_t cacheSize = getKVCacheSize() * sizeof(float);
    cudaError_t error = cudaMemset(d_kv_cache_, 0, cacheSize);
    
    if (error != cudaSuccess) {
        lastError_ = cudaGetErrorString(error);
        return false;
    }
    
    return true;
}

void TransformerBlock::cleanup() {
    auto& memManager = GPUMemoryManager::getInstance();
    
    if (d_weights_) {
        memManager.deallocate(d_weights_);
        d_weights_ = nullptr;
    }
    
    freeKVCache();
}

void TransformerBlock::applyResidualConnection(float* output, const float* input, const float* residual, size_t size) {
    #pragma omp parallel for
    for (size_t i = 0; i < size; ++i) {
        output[i] = input[i] + residual[i];
    }
}

void TransformerBlock::applyResidualConnectionWithNorm(float* output, const float* input, const float* residual, 
                                                     const float* gamma, const float* beta, size_t size) {
    #pragma omp parallel for
    for (size_t i = 0; i < size; ++i) {
        // Add residual connection
        float x = input[i] + residual[i];
        
        // Apply layer normalization
        float mean = 0.0f;
        float variance = 0.0f;
        
        // Calculate mean
        for (size_t j = 0; j < size; ++j) {
            mean += x;
        }
        mean /= size;
        
        // Calculate variance
        for (size_t j = 0; j < size; ++j) {
            float diff = x - mean;
            variance += diff * diff;
        }
        variance /= size;
        
        // Normalize and scale
        float std_dev = std::sqrt(variance + 1e-5f);
        output[i] = gamma[i] * ((x - mean) / std_dev) + beta[i];
    }
}

void TransformerBlock::applyResidualConnectionWithDropout(float* output, const float* input, const float* residual,
                                                        float dropout_rate, size_t size) {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<float> dis(0.0f, 1.0f);
    
    #pragma omp parallel for
    for (size_t i = 0; i < size; ++i) {
        // Apply dropout mask
        float mask = (dis(gen) > dropout_rate) ? 1.0f : 0.0f;
        output[i] = (input[i] + residual[i]) * mask;
    }
}

} // namespace cogniware 