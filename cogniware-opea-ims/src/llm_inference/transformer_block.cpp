#include "../../include/transformer_block.h"
#include "../cuda_runtime/transformer_kernels.cu"
#include <cublas_v2.h>
#include <stdexcept>

namespace cogniware {

TransformerBlock::TransformerBlock(size_t hidden_size, size_t num_heads, size_t intermediate_size)
    : hidden_size_(hidden_size)
    , num_heads_(num_heads)
    , intermediate_size_(intermediate_size)
    , head_dim_(hidden_size / num_heads)
    , query_weight_(nullptr)
    , key_weight_(nullptr)
    , value_weight_(nullptr)
    , output_weight_(nullptr)
    , ffn_up_weight_(nullptr)
    , ffn_down_weight_(nullptr)
    , layer_norm1_weight_(nullptr)
    , layer_norm1_bias_(nullptr)
    , layer_norm2_weight_(nullptr)
    , layer_norm2_bias_(nullptr)
    , key_cache_(nullptr)
    , value_cache_(nullptr)
    , cache_batch_size_(0)
    , cache_seq_length_(0)
    , workspace_(nullptr)
    , workspace_size_(0)
{
    // Initialize cuBLAS handle
    cublasCreate(&cublas_handle_);
}

TransformerBlock::~TransformerBlock() {
    try {
        // Free GPU memory
        auto& memory_manager = GPUMemoryManager::getInstance();
        
        if (query_weight_) memory_manager.deallocate(query_weight_);
        if (key_weight_) memory_manager.deallocate(key_weight_);
        if (value_weight_) memory_manager.deallocate(value_weight_);
        if (output_weight_) memory_manager.deallocate(output_weight_);
        if (ffn_up_weight_) memory_manager.deallocate(ffn_up_weight_);
        if (ffn_down_weight_) memory_manager.deallocate(ffn_down_weight_);
        if (layer_norm1_weight_) memory_manager.deallocate(layer_norm1_weight_);
        if (layer_norm1_bias_) memory_manager.deallocate(layer_norm1_bias_);
        if (layer_norm2_weight_) memory_manager.deallocate(layer_norm2_weight_);
        if (layer_norm2_bias_) memory_manager.deallocate(layer_norm2_bias_);

        // Destroy CUDA streams
        if (attention_stream_) cudaStreamDestroy(attention_stream_);
        if (ffn_stream_) cudaStreamDestroy(ffn_stream_);
    } catch (const std::exception& e) {
        spdlog::error("Error during transformer block cleanup: {}", e.what());
    }

    // Destroy cuBLAS handle
    cublasDestroy(cublas_handle_);
}

bool TransformerBlock::initialize(const float* weights, size_t layer_idx) {
    try {
        // Calculate weight offsets
        const size_t layer_offset = layer_idx * (
            4 * hidden_size_ * hidden_size_ +  // Q, K, V, O weights
            2 * hidden_size_ * intermediate_size_ +  // FFN up/down weights
            4 * hidden_size_  // Layer norm weights and biases
        );

        // Allocate and copy weights
        auto& memory_manager = GPUMemoryManager::getInstance();
        
        // Query, Key, Value, Output weights
        query_weight_ = static_cast<float*>(memory_manager.allocate(hidden_size_ * hidden_size_ * sizeof(float)));
        key_weight_ = static_cast<float*>(memory_manager.allocate(hidden_size_ * hidden_size_ * sizeof(float)));
        value_weight_ = static_cast<float*>(memory_manager.allocate(hidden_size_ * hidden_size_ * sizeof(float)));
        output_weight_ = static_cast<float*>(memory_manager.allocate(hidden_size_ * hidden_size_ * sizeof(float)));

        // FFN weights
        ffn_up_weight_ = static_cast<float*>(memory_manager.allocate(hidden_size_ * intermediate_size_ * sizeof(float)));
        ffn_down_weight_ = static_cast<float*>(memory_manager.allocate(intermediate_size_ * hidden_size_ * sizeof(float)));

        // Layer norm weights and biases
        layer_norm1_weight_ = static_cast<float*>(memory_manager.allocate(hidden_size_ * sizeof(float)));
        layer_norm1_bias_ = static_cast<float*>(memory_manager.allocate(hidden_size_ * sizeof(float)));
        layer_norm2_weight_ = static_cast<float*>(memory_manager.allocate(hidden_size_ * sizeof(float)));
        layer_norm2_bias_ = static_cast<float*>(memory_manager.allocate(hidden_size_ * sizeof(float)));

        // Copy weights to GPU
        memory_manager.copyToDevice(query_weight_, weights + layer_offset, hidden_size_ * hidden_size_ * sizeof(float));
        memory_manager.copyToDevice(key_weight_, weights + layer_offset + hidden_size_ * hidden_size_, hidden_size_ * hidden_size_ * sizeof(float));
        memory_manager.copyToDevice(value_weight_, weights + layer_offset + 2 * hidden_size_ * hidden_size_, hidden_size_ * hidden_size_ * sizeof(float));
        memory_manager.copyToDevice(output_weight_, weights + layer_offset + 3 * hidden_size_ * hidden_size_, hidden_size_ * hidden_size_ * sizeof(float));

        memory_manager.copyToDevice(ffn_up_weight_, weights + layer_offset + 4 * hidden_size_ * hidden_size_, hidden_size_ * intermediate_size_ * sizeof(float));
        memory_manager.copyToDevice(ffn_down_weight_, weights + layer_offset + 4 * hidden_size_ * hidden_size_ + hidden_size_ * intermediate_size_, intermediate_size_ * hidden_size_ * sizeof(float));

        memory_manager.copyToDevice(layer_norm1_weight_, weights + layer_offset + 4 * hidden_size_ * hidden_size_ + 2 * hidden_size_ * intermediate_size_, hidden_size_ * sizeof(float));
        memory_manager.copyToDevice(layer_norm1_bias_, weights + layer_offset + 4 * hidden_size_ * hidden_size_ + 2 * hidden_size_ * intermediate_size_ + hidden_size_, hidden_size_ * sizeof(float));
        memory_manager.copyToDevice(layer_norm2_weight_, weights + layer_offset + 4 * hidden_size_ * hidden_size_ + 2 * hidden_size_ * intermediate_size_ + 2 * hidden_size_, hidden_size_ * sizeof(float));
        memory_manager.copyToDevice(layer_norm2_bias_, weights + layer_offset + 4 * hidden_size_ * hidden_size_ + 2 * hidden_size_ * intermediate_size_ + 3 * hidden_size_, hidden_size_ * sizeof(float));

        // Create CUDA streams for parallel operations
        cudaStreamCreate(&attention_stream_);
        cudaStreamCreate(&ffn_stream_);

        return true;
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize transformer block: {}", e.what());
        return false;
    }
}

bool TransformerBlock::forward(
    float* output,
    const float* input,
    size_t batch_size,
    size_t seq_length,
    cudaStream_t stream
) {
    // Allocate workspace if needed
    size_t required_workspace = getWorkspaceSize(batch_size, seq_length);
    if (required_workspace > workspace_size_) {
        if (workspace_) {
            cudaFree(workspace_);
        }
        workspace_ = static_cast<float*>(GPUMemoryManager::getInstance().allocate(required_workspace));
        workspace_size_ = required_workspace;
    }

    // Compute attention
    float* attention_output = workspace_;
    if (!computeAttention(attention_output, input, batch_size, seq_length, stream)) {
        return false;
    }

    // First layer norm
    float* norm1_output = attention_output + batch_size * seq_length * hidden_size_;
    if (!computeLayerNorm(norm1_output, attention_output, layer_norm1_weight_, layer_norm1_bias_, batch_size, seq_length, stream)) {
        return false;
    }

    // FFN
    float* ffn_output = norm1_output + batch_size * seq_length * hidden_size_;
    if (!computeFFN(ffn_output, norm1_output, batch_size, seq_length, stream)) {
        return false;
    }

    // Second layer norm
    if (!computeLayerNorm(output, ffn_output, layer_norm2_weight_, layer_norm2_bias_, batch_size, seq_length, stream)) {
        return false;
    }

    return true;
}

size_t TransformerBlock::getWorkspaceSize(size_t batch_size, size_t seq_length) const {
    return 3 * batch_size * seq_length * hidden_size_ * sizeof(float);  // For attention, norm1, and FFN outputs
}

size_t TransformerBlock::getKVCacheSize(size_t batch_size, size_t seq_length) const {
    return 2 * batch_size * seq_length * hidden_size_ * sizeof(float);  // For key and value caches
}

bool TransformerBlock::allocateKVCache(size_t batch_size, size_t seq_length) {
    if (batch_size == cache_batch_size_ && seq_length == cache_seq_length_) {
        return true;  // Cache already allocated with correct size
    }

    // Free existing cache if any
    if (key_cache_) cudaFree(key_cache_);
    if (value_cache_) cudaFree(value_cache_);

    // Allocate new cache
    size_t cache_size = getKVCacheSize(batch_size, seq_length);
    key_cache_ = static_cast<float*>(GPUMemoryManager::getInstance().allocate(cache_size / 2));
    value_cache_ = static_cast<float*>(GPUMemoryManager::getInstance().allocate(cache_size / 2));

    cache_batch_size_ = batch_size;
    cache_seq_length_ = seq_length;

    return true;
}

void TransformerBlock::freeKVCache() {
    if (key_cache_) {
        cudaFree(key_cache_);
        key_cache_ = nullptr;
    }
    if (value_cache_) {
        cudaFree(value_cache_);
        value_cache_ = nullptr;
    }
    cache_batch_size_ = 0;
    cache_seq_length_ = 0;
}

bool TransformerBlock::updateKVCache(size_t batch_size, size_t seq_length) {
    if (batch_size > cache_batch_size_ || seq_length > cache_seq_length_) {
        return allocateKVCache(batch_size, seq_length);
    }
    return true;
}

bool TransformerBlock::computeAttention(
    float* output,
    const float* input,
    size_t batch_size,
    size_t seq_length,
    cudaStream_t stream
) {
    // Project input to query, key, value
    float* query = workspace_ + 3 * batch_size * seq_length * hidden_size_;
    float* key = query + batch_size * seq_length * hidden_size_;
    float* value = key + batch_size * seq_length * hidden_size_;

    // Matrix multiplication using cuBLAS
    const float alpha = 1.0f;
    const float beta = 0.0f;

    // Q = input * query_weight_
    cublasSgemm(cublas_handle_, CUBLAS_OP_N, CUBLAS_OP_N,
        hidden_size_, batch_size * seq_length, hidden_size_,
        &alpha, query_weight_, hidden_size_,
        input, hidden_size_,
        &beta, query, hidden_size_);

    // K = input * key_weight_
    cublasSgemm(cublas_handle_, CUBLAS_OP_N, CUBLAS_OP_N,
        hidden_size_, batch_size * seq_length, hidden_size_,
        &alpha, key_weight_, hidden_size_,
        input, hidden_size_,
        &beta, key, hidden_size_);

    // V = input * value_weight_
    cublasSgemm(cublas_handle_, CUBLAS_OP_N, CUBLAS_OP_N,
        hidden_size_, batch_size * seq_length, hidden_size_,
        &alpha, value_weight_, hidden_size_,
        input, hidden_size_,
        &beta, value, hidden_size_);

    // Launch attention kernel
    float scale = 1.0f / std::sqrt(static_cast<float>(head_dim_));
    launchAttention(output, query, key, value, batch_size, seq_length, num_heads_, head_dim_, scale, stream);

    // Project output
    float* temp = value;  // Reuse value buffer
    cublasSgemm(cublas_handle_, CUBLAS_OP_N, CUBLAS_OP_N,
        hidden_size_, batch_size * seq_length, hidden_size_,
        &alpha, output_weight_, hidden_size_,
        output, hidden_size_,
        &beta, temp, hidden_size_);

    // Copy result back to output
    cudaMemcpyAsync(output, temp, batch_size * seq_length * hidden_size_ * sizeof(float),
        cudaMemcpyDeviceToDevice, stream);

    return true;
}

bool TransformerBlock::computeFFN(
    float* output,
    const float* input,
    size_t batch_size,
    size_t seq_length,
    cudaStream_t stream
) {
    // Launch FFN kernel
    launchFFN(output, input, ffn_up_weight_, ffn_down_weight_,
        batch_size, seq_length, hidden_size_, intermediate_size_, stream);
    return true;
}

bool TransformerBlock::computeLayerNorm(
    float* output,
    const float* input,
    const float* weight,
    const float* bias,
    size_t batch_size,
    size_t seq_length,
    cudaStream_t stream
) {
    // Launch layer norm kernel
    launchLayerNorm(output, input, weight, bias, batch_size, seq_length, hidden_size_, stream);
    return true;
}

} // namespace cogniware 