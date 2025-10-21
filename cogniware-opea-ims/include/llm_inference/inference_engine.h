#pragma once

#include <string>
#include <vector>
#include <unordered_map>
#include <mutex>
#include <memory>
#include <chrono>
#include <cuda_runtime.h>
#include <NvInfer.h>
#include <onnxruntime_cxx_api.h>
#include "model_cache.h"

namespace cogniware {
namespace llm_inference {

struct InferenceEngineConfig {
    int max_batch_size;
    int max_sequence_length;
    float temperature;
    float top_p;
    int top_k;
    bool use_fp16;
    bool use_int8;
    int num_beams;
    float length_penalty;
    float repetition_penalty;
    bool do_sample;
    int num_return_sequences;
    std::string device;
    std::string precision;
    bool enable_cache;
    size_t cache_size;
    bool enable_attention_cache;
    bool enable_kv_cache;
    int num_attention_heads;
    int hidden_size;
    int num_layers;
    float dropout;
    bool use_gradient_checkpointing;
    bool use_flash_attention;
    bool use_sdpa;
    bool use_multi_query_attention;
    bool use_grouped_query_attention;
    bool use_sliding_window_attention;
    int sliding_window_size;
    bool use_rotary_embeddings;
    bool use_alibi_embeddings;
    bool use_relative_position_embeddings;
    int max_position_embeddings;
    bool use_layer_norm;
    bool use_rms_norm;
    bool use_parallel_attention;
    bool use_parallel_ffn;
    bool use_activation_checkpointing;
    bool use_selective_checkpointing;
    bool use_recompute;
    bool use_activation_recompute;
    bool use_selective_recompute;
    bool use_gradient_accumulation;
    int gradient_accumulation_steps;
    bool use_mixed_precision;
    bool use_amp;
    bool use_bf16;
    bool use_fp8;
    bool use_dynamic_shapes;
    bool use_static_shapes;
    bool use_optimized_kernels;
    bool use_custom_kernels;
    bool use_fused_operations;
    bool use_fused_layernorm;
    bool use_fused_attention;
    bool use_fused_ffn;
    bool use_fused_activation;
    bool use_fused_dropout;
    bool use_fused_bias;
    bool use_fused_residual;
    bool use_fused_scale;
    bool use_fused_softmax;
    bool use_fused_gelu;
    bool use_fused_silu;
    bool use_fused_mish;
    bool use_fused_relu;
    bool use_fused_tanh;
    bool use_fused_sigmoid;
    bool use_fused_elu;
    bool use_fused_leaky_relu;
    bool use_fused_prelu;
    bool use_fused_selu;
    bool use_fused_softplus;
    bool use_fused_softsign;
    bool use_fused_hardtanh;
    bool use_fused_hardsigmoid;
    bool use_fused_hardswish;
    bool use_fused_mish;
    bool use_fused_swish;
    bool use_fused_gelu_approximate;
    bool use_fused_silu_approximate;
    bool use_fused_mish_approximate;
    bool use_fused_swish_approximate;
    bool use_fused_gelu_fast;
    bool use_fused_silu_fast;
    bool use_fused_mish_fast;
    bool use_fused_swish_fast;
    bool use_fused_gelu_accurate;
    bool use_fused_silu_accurate;
    bool use_fused_mish_accurate;
    bool use_fused_swish_accurate;
    bool use_fused_gelu_optimized;
    bool use_fused_silu_optimized;
    bool use_fused_mish_optimized;
    bool use_fused_swish_optimized;
    bool use_fused_gelu_custom;
    bool use_fused_silu_custom;
    bool use_fused_mish_custom;
    bool use_fused_swish_custom;
};

class InferenceEngine {
public:
    explicit InferenceEngine(const InferenceEngineConfig& config);
    ~InferenceEngine();

    // Model management
    void load_model(const std::string& model_path);
    void unload_model();
    bool is_model_loaded() const;

    // Inference operations
    std::vector<float> run_inference(
        const std::vector<int>& input_tokens,
        const std::unordered_map<std::string, std::string>& parameters);
    std::vector<std::vector<float>> batch_inference(
        const std::vector<std::vector<int>>& batch_tokens,
        const std::unordered_map<std::string, std::string>& parameters);

    // Memory management
    void set_memory_limit(size_t limit);
    size_t get_available_memory() const;
    void allocate_memory(size_t size);
    void deallocate_memory(size_t size);

    // Performance optimization
    void set_batch_size(int size);
    void set_sequence_length(int length);
    void enable_quantization(bool enable);
    void set_quantization_type(const std::string& type);
    void enable_cache(bool enable);
    void set_cache_size(size_t size);
    void enable_attention_cache(bool enable);
    void enable_kv_cache(bool enable);
    void set_num_attention_heads(int num);
    void set_hidden_size(int size);
    void set_num_layers(int num);
    void set_dropout(float dropout);
    void enable_gradient_checkpointing(bool enable);
    void enable_flash_attention(bool enable);
    void enable_sdpa(bool enable);
    void enable_multi_query_attention(bool enable);
    void enable_grouped_query_attention(bool enable);
    void enable_sliding_window_attention(bool enable);
    void set_sliding_window_size(int size);
    void enable_rotary_embeddings(bool enable);
    void enable_alibi_embeddings(bool enable);
    void enable_relative_position_embeddings(bool enable);
    void enable_layer_norm(bool enable);
    void enable_rms_norm(bool enable);
    void enable_parallel_attention(bool enable);
    void enable_parallel_ffn(bool enable);
    void enable_activation_checkpointing(bool enable);
    void enable_selective_checkpointing(bool enable);
    void enable_recompute(bool enable);
    void enable_activation_recompute(bool enable);
    void enable_selective_recompute(bool enable);
    void enable_gradient_accumulation(bool enable);
    void set_gradient_accumulation_steps(int steps);
    void enable_mixed_precision(bool enable);
    void enable_amp(bool enable);
    void enable_bf16(bool enable);
    void enable_fp8(bool enable);
    void enable_dynamic_shapes(bool enable);
    void enable_static_shapes(bool enable);
    void enable_optimized_kernels(bool enable);
    void enable_custom_kernels(bool enable);
    void enable_fused_operations(bool enable);
    void enable_fused_layernorm(bool enable);
    void enable_fused_attention(bool enable);
    void enable_fused_ffn(bool enable);
    void enable_fused_activation(bool enable);
    void enable_fused_dropout(bool enable);
    void enable_fused_bias(bool enable);
    void enable_fused_residual(bool enable);
    void enable_fused_scale(bool enable);
    void enable_fused_softmax(bool enable);
    void enable_fused_gelu(bool enable);
    void enable_fused_silu(bool enable);
    void enable_fused_mish(bool enable);
    void enable_fused_relu(bool enable);
    void enable_fused_tanh(bool enable);
    void enable_fused_sigmoid(bool enable);
    void enable_fused_elu(bool enable);
    void enable_fused_leaky_relu(bool enable);
    void enable_fused_prelu(bool enable);
    void enable_fused_selu(bool enable);
    void enable_fused_softplus(bool enable);
    void enable_fused_softsign(bool enable);
    void enable_fused_hardtanh(bool enable);
    void enable_fused_hardsigmoid(bool enable);
    void enable_fused_hardswish(bool enable);
    void enable_fused_mish(bool enable);
    void enable_fused_swish(bool enable);
    void enable_fused_gelu_approximate(bool enable);
    void enable_fused_silu_approximate(bool enable);
    void enable_fused_mish_approximate(bool enable);
    void enable_fused_swish_approximate(bool enable);
    void enable_fused_gelu_fast(bool enable);
    void enable_fused_silu_fast(bool enable);
    void enable_fused_mish_fast(bool enable);
    void enable_fused_swish_fast(bool enable);
    void enable_fused_gelu_accurate(bool enable);
    void enable_fused_silu_accurate(bool enable);
    void enable_fused_mish_accurate(bool enable);
    void enable_fused_swish_accurate(bool enable);
    void enable_fused_gelu_optimized(bool enable);
    void enable_fused_silu_optimized(bool enable);
    void enable_fused_mish_optimized(bool enable);
    void enable_fused_swish_optimized(bool enable);
    void enable_fused_gelu_custom(bool enable);
    void enable_fused_silu_custom(bool enable);
    void enable_fused_mish_custom(bool enable);
    void enable_fused_swish_custom(bool enable);

private:
    // Configuration and state
    InferenceEngineConfig config_;
    std::unique_ptr<ModelCache> model_cache_;
    std::string current_model_path_;
    bool is_model_loaded_;
    mutable std::mutex mutex_;

    // Memory tracking
    struct MemoryBlock {
        void* ptr;
        size_t size;
    };
    std::vector<MemoryBlock> allocated_memory_;

    // Tensor storage
    struct TensorInfo {
        void* data;
        nvinfer1::Dims dims;
    };
    std::unordered_map<std::string, TensorInfo> input_tensors_;
    std::unordered_map<std::string, std::unique_ptr<float[]>> output_tensors_;
    std::unordered_map<std::string, Ort::Value> onnx_input_tensors_;
    std::unordered_map<std::string, Ort::Value> onnx_output_tensors_;
    std::vector<float> processed_output_;
    std::vector<std::vector<float>> processed_batch_output_;

    // Helper methods
    void initialize_cuda();
    void initialize_tensorrt();
    void initialize_onnx();
    void validate_config();
    void prepare_input_tensors(const std::vector<int>& input_tokens);
    void prepare_batch_input_tensors(const std::vector<std::vector<int>>& batch_tokens);
    void run_tensorrt_inference();
    void run_onnx_inference();
    void process_output_tensors();
    void process_batch_output_tensors();
    void cleanup();
};

} // namespace llm_inference
} // namespace cogniware 