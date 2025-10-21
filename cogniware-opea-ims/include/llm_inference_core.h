#pragma once

#include <cuda_runtime.h>
#include <cublas_v2.h>
#include <cudnn.h>
#include <string>
#include <vector>
#include <memory>
#include <unordered_map>

namespace cogniware {

struct LLMConfig {
    int max_sequence_length;
    int vocab_size;
    int hidden_size;
    int num_layers;
    int num_heads;
    float dropout_rate;
    bool use_fp16;
};

class LLMInferenceCore {
public:
    LLMInferenceCore(const LLMConfig& config, int device_id);
    ~LLMInferenceCore();

    // Initialize CUDA resources and load model weights
    void initialize();
    
    // Process input tokens and generate output
    std::vector<int> process(const std::vector<int>& input_tokens);
    
    // Get model configuration
    const LLMConfig& get_config() const { return config_; }

private:
    LLMConfig config_;
    int device_id_;
    cublasHandle_t cublas_handle_;
    cudnnHandle_t cudnn_handle_;
    
    // Model weights and buffers
    struct ModelWeights {
        void* embedding_weights;
        void* attention_weights;
        void* feedforward_weights;
        void* layer_norm_weights;
    } weights_;
    
    // CUDA streams and events
    cudaStream_t stream_;
    cudaEvent_t start_event_, end_event_;
    
    // Helper methods
    void initialize_cuda();
    void load_weights();
    void free_weights();
    
    // CUDA kernels
    void compute_attention(const void* query, const void* key, const void* value,
                         void* output, int batch_size, int seq_length);
    void compute_feedforward(const void* input, void* output, int batch_size);
    void compute_layer_norm(const void* input, void* output, int batch_size);
};

} // namespace cogniware 