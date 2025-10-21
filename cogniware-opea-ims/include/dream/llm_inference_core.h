#pragma once

#include <memory>
#include <string>
#include <vector>
#include <unordered_map>
#include <functional>
#include <cuda_runtime.h>
#include <cublas_v2.h>
#include <cudnn.h>
#include <tensorrt/NvInfer.h>
#include <onnxruntime_cxx_api.h>

namespace cogniware {
namespace dream {

struct InferenceConfig {
    int max_batch_size;
    int max_sequence_length;
    float temperature;
    float top_p;
    int top_k;
    bool use_fp16;
    bool use_int8;
    int num_beams;
    float repetition_penalty;
    std::string device_type;  // "cuda", "cpu", "auto"
    int device_id;
    bool enable_cache;
    size_t max_cache_size;
    bool enable_quantization;
    std::string quantization_type;  // "int8", "fp16", "none"
};

struct TokenizerConfig {
    std::string vocab_file;
    std::string merges_file;
    std::string special_tokens_file;
    bool add_bos_token;
    bool add_eos_token;
    bool add_padding_token;
    int pad_token_id;
    int bos_token_id;
    int eos_token_id;
    int unk_token_id;
    int mask_token_id;
};

struct ModelConfig {
    std::string model_path;
    std::string model_type;  // "gpt2", "llama", "falcon", etc.
    int hidden_size;
    int num_layers;
    int num_heads;
    int vocab_size;
    int max_position_embeddings;
    float layer_norm_eps;
    bool use_rotary_embeddings;
    bool use_alibi;
    std::string activation_function;  // "gelu", "relu", "silu", etc.
    bool use_bias;
    bool use_residual;
    bool use_layer_norm;
    bool use_dropout;
    float dropout_prob;
};

class LLMInferenceCore {
public:
    static LLMInferenceCore& get_instance();

    // Initialization and configuration
    void initialize(const ModelConfig& model_config,
                   const TokenizerConfig& tokenizer_config,
                   const InferenceConfig& inference_config);
    void configure(const InferenceConfig& config);
    void shutdown();

    // Model management
    void load_model(const std::string& model_path);
    void unload_model();
    bool is_model_loaded() const;

    // Inference operations
    std::vector<int> tokenize(const std::string& text);
    std::string detokenize(const std::vector<int>& tokens);
    std::vector<float> run_inference(const std::vector<int>& input_tokens,
                                   const std::unordered_map<std::string, std::string>& parameters);
    std::vector<float> generate(const std::string& prompt,
                              const std::unordered_map<std::string, std::string>& parameters);

    // Batch operations
    std::vector<std::vector<float>> batch_inference(
        const std::vector<std::vector<int>>& batch_tokens,
        const std::unordered_map<std::string, std::string>& parameters);
    std::vector<std::string> batch_generate(
        const std::vector<std::string>& prompts,
        const std::unordered_map<std::string, std::string>& parameters);

    // Memory management
    void allocate_memory(size_t size);
    void free_memory();
    size_t get_available_memory() const;
    void set_memory_limit(size_t limit);

    // Performance optimization
    void enable_caching(bool enable);
    void clear_cache();
    void set_batch_size(int size);
    void set_sequence_length(int length);
    void enable_quantization(bool enable);
    void set_quantization_type(const std::string& type);

    // Monitoring and metrics
    struct InferenceMetrics {
        float latency;
        float throughput;
        size_t memory_usage;
        float gpu_utilization;
        int batch_size;
        int sequence_length;
        float cache_hit_rate;
    };
    InferenceMetrics get_metrics() const;
    void reset_metrics();

private:
    LLMInferenceCore() = default;
    ~LLMInferenceCore() = default;
    LLMInferenceCore(const LLMInferenceCore&) = delete;
    LLMInferenceCore& operator=(const LLMInferenceCore&) = delete;

    // Core components
    std::unique_ptr<nvinfer1::IRuntime> trt_runtime_;
    std::unique_ptr<nvinfer1::ICudaEngine> trt_engine_;
    std::unique_ptr<nvinfer1::IExecutionContext> trt_context_;
    std::unique_ptr<Ort::Session> onnx_session_;
    std::unique_ptr<Ort::MemoryInfo> memory_info_;

    // CUDA resources
    cublasHandle_t cublas_handle_;
    cudnnHandle_t cudnn_handle_;
    void* gpu_memory_;
    size_t gpu_memory_size_;
    size_t memory_limit_;

    // Model state
    ModelConfig model_config_;
    TokenizerConfig tokenizer_config_;
    InferenceConfig inference_config_;
    bool is_initialized_;
    bool is_model_loaded_;

    // Performance optimization
    struct CacheEntry {
        std::vector<int> input_tokens;
        std::vector<float> output_logits;
        std::chrono::system_clock::time_point timestamp;
    };
    std::unordered_map<std::string, CacheEntry> inference_cache_;
    bool cache_enabled_;
    size_t max_cache_size_;

    // Metrics
    mutable InferenceMetrics metrics_;
    mutable std::mutex metrics_mutex_;

    // Helper functions
    void initialize_cuda();
    void initialize_tensorrt();
    void initialize_onnx();
    void initialize_tokenizer();
    void validate_configs();
    void update_metrics(const InferenceMetrics& new_metrics);
    std::string generate_cache_key(const std::vector<int>& tokens);
    void cleanup_cache();
    void check_memory_limits();
};

} // namespace dream
} // namespace cogniware 