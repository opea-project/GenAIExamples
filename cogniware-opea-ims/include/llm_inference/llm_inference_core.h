#pragma once

#include <cuda_runtime.h>
#include <NvInfer.h>
#include <onnxruntime_cxx_api.h>
#include <memory>
#include <string>
#include <vector>
#include <unordered_map>
#include <mutex>
#include <atomic>
#include <chrono>
#include <functional>
#include <deque>
#include <optional>

namespace cogniware {
namespace llm_inference {

// Forward declarations
class ModelCache;
class Tokenizer;
class InferenceEngine;

struct InferenceConfig {
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

struct TokenizerConfig {
    std::string vocab_file;
    std::string merges_file;
    std::string special_tokens_file;
    int pad_token_id;
    int bos_token_id;
    int eos_token_id;
    int unk_token_id;
    int mask_token_id;
    int sep_token_id;
    int cls_token_id;
    bool add_special_tokens;
    bool add_bos_token;
    bool add_eos_token;
    bool add_sep_token;
    bool add_cls_token;
    bool add_mask_token;
    bool add_unk_token;
    bool add_pad_token;
    bool do_lower_case;
    bool strip_accents;
    bool clean_up_tokenization_spaces;
    bool use_fast;
    bool use_slow;
    bool use_regex;
    bool use_byte_level;
    bool use_word_level;
    bool use_char_level;
    bool use_subword_level;
    bool use_bpe;
    bool use_wordpiece;
    bool use_unigram;
    bool use_sentencepiece;
    bool use_bert;
    bool use_gpt2;
    bool use_roberta;
    bool use_t5;
    bool use_bart;
    bool use_marian;
    bool use_mbart;
    bool use_pegasus;
    bool use_mt5;
    bool use_led;
    bool use_longformer;
    bool use_bigbird;
    bool use_reformer;
    bool use_performer;
    bool use_linformer;
    bool use_nystromformer;
    bool use_fnet;
    bool use_funnel;
    bool use_convbert;
    bool use_electra;
    bool use_deberta;
    bool use_debertav2;
    bool use_mobilebert;
    bool use_mpnet;
    bool use_retribert;
    bool use_tapas;
    bool use_transfoxl;
    bool use_xlm;
    bool use_xlmroberta;
    bool use_flaubert;
    bool use_camembert;
    bool use_distilbert;
    bool use_albert;
    bool use_tinybert;
    bool use_bertweet;
    bool use_bertweetcnn;
    bool use_bertweetlstm;
    bool use_bertweetgru;
    bool use_bertweetbilstm;
    bool use_bertweetbigru;
    bool use_bertweetcnnlstm;
    bool use_bertweetcnngru;
    bool use_bertweetlstmcnn;
    bool use_bertweetgrucnn;
    bool use_bertweetbilstmcnn;
    bool use_bertweetbigrucnn;
    bool use_bertweetcnnbilstm;
    bool use_bertweetcnnbigru;
    bool use_bertweetlstmbilstm;
    bool use_bertweetgrubigru;
    bool use_bertweetbilstmbilstm;
    bool use_bertweetbigrubigru;
    bool use_bertweetcnnbilstmbilstm;
    bool use_bertweetcnnbigrubigru;
    bool use_bertweetlstmbilstmbilstm;
    bool use_bertweetgrubigrubigru;
    bool use_bertweetbilstmbilstmbilstmbilstm;
    bool use_bertweetbigrubigrubigru;
    bool use_bertweetcnnbilstmbilstmbilstmbilstm;
    bool use_bertweetcnnbigrubigrubigrubigru;
    bool use_bertweetlstmbilstmbilstmbilstmbilstm;
    bool use_bertweetgrubigrubigrubigrubigru;
    bool use_bertweetbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetbigrubigrubigrubigrubigru;
    bool use_bertweetcnnbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetcnnbigrubigrubigrubigrubigru;
    bool use_bertweetlstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetgrubigrubigrubigrubigrubigru;
    bool use_bertweetbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetbigrubigrubigrubigrubigru;
    bool use_bertweetcnnbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetcnnbigrubigrubigrubigrubigru;
    bool use_bertweetlstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetgrubigrubigrubigrubigrubigru;
    bool use_bertweetbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetbigrubigrubigrubigrubigru;
    bool use_bertweetcnnbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetcnnbigrubigrubigrubigrubigru;
    bool use_bertweetlstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetgrubigrubigrubigrubigrubigru;
    bool use_bertweetbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetbigrubigrubigrubigrubigru;
    bool use_bertweetcnnbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetcnnbigrubigrubigrubigrubigru;
    bool use_bertweetlstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetgrubigrubigrubigrubigrubigru;
    bool use_bertweetbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetbigrubigrubigrubigrubigru;
    bool use_bertweetcnnbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetcnnbigrubigrubigrubigrubigru;
    bool use_bertweetlstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetgrubigrubigrubigrubigrubigru;
    bool use_bertweetbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetbigrubigrubigrubigrubigru;
    bool use_bertweetcnnbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetcnnbigrubigrubigrubigrubigru;
    bool use_bertweetlstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetgrubigrubigrubigrubigrubigru;
    bool use_bertweetbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetbigrubigrubigrubigrubigru;
    bool use_bertweetcnnbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetcnnbigrubigrubigrubigrubigru;
    bool use_bertweetlstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetgrubigrubigrubigrubigrubigru;
    bool use_bertweetbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetbigrubigrubigrubigrubigru;
    bool use_bertweetcnnbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetcnnbigrubigrubigrubigrubigru;
    bool use_bertweetlstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetgrubigrubigrubigrubigrubigru;
    bool use_bertweetbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetbigrubigrubigrubigrubigru;
    bool use_bertweetcnnbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetcnnbigrubigrubigrubigrubigru;
    bool use_bertweetlstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetgrubigrubigrubigrubigrubigru;
    bool use_bertweetbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetbigrubigrubigrubigrubigru;
    bool use_bertweetcnnbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetcnnbigrubigrubigrubigrubigru;
    bool use_bertweetlstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetgrubigrubigrubigrubigrubigru;
    bool use_bertweetbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetbigrubigrubigrubigrubigru;
    bool use_bertweetcnnbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetcnnbigrubigrubigrubigrubigru;
    bool use_bertweetlstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetgrubigrubigrubigrubigrubigru;
    bool use_bertweetbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetbigrubigrubigrubigrubigru;
    bool use_bertweetcnnbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetcnnbigrubigrubigrubigrubigru;
    bool use_bertweetlstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetgrubigrubigrubigrubigrubigru;
    bool use_bertweetbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetbigrubigrubigrubigrubigru;
    bool use_bertweetcnnbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstmbilstm;
    bool use_bertweetcnnbigrubigrubigrubigrubigru;
};

struct ModelConfig {
    std::string model_path;
    std::string model_type;
    int hidden_size;
    int num_layers;
    int num_attention_heads;
    int intermediate_size;
    int vocab_size;
    int max_position_embeddings;
    float dropout;
    float attention_dropout;
    float hidden_dropout;
    float layer_norm_eps;
    bool use_cache;
    bool use_attention_cache;
    bool use_kv_cache;
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

class LLMInferenceCore {
public:
    static LLMInferenceCore& get_instance();

    // Initialization and configuration
    void initialize(const std::string& config_path);
    void configure(const std::unordered_map<std::string, std::string>& config);
    void shutdown();

    // Model management
    void load_model(const std::string& model_path);
    void unload_model();
    bool is_model_loaded() const;

    // Inference operations
    std::vector<float> run_inference(
        const std::vector<int>& input_tokens,
        const std::unordered_map<std::string, std::string>& parameters);
    std::vector<float> generate(
        const std::string& prompt,
        const std::unordered_map<std::string, std::string>& parameters);
    std::vector<std::vector<float>> batch_inference(
        const std::vector<std::vector<int>>& batch_tokens,
        const std::unordered_map<std::string, std::string>& parameters);
    std::vector<std::string> batch_generate(
        const std::vector<std::string>& prompts,
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
    LLMInferenceCore() = default;
    ~LLMInferenceCore() = default;
    LLMInferenceCore(const LLMInferenceCore&) = delete;
    LLMInferenceCore& operator=(const LLMInferenceCore&) = delete;

    // Core components
    std::unique_ptr<ModelCache> model_cache_;
    std::unique_ptr<Tokenizer> tokenizer_;
    std::unique_ptr<InferenceEngine> inference_engine_;

    // Configuration
    InferenceConfig inference_config_;
    TokenizerConfig tokenizer_config_;
    ModelConfig model_config_;

    // State
    std::atomic<bool> is_initialized_;
    std::atomic<bool> is_model_loaded_;
    std::mutex mutex_;

    // Helper functions
    void validate_config();
    void initialize_cuda();
    void initialize_tensorrt();
    void initialize_onnx();
    void initialize_tokenizer();
    void initialize_model_cache();
    void initialize_inference_engine();
    void cleanup();
};

} // namespace llm_inference
} // namespace cogniware 