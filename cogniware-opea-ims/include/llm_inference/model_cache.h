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

namespace cogniware {
namespace llm_inference {

struct ModelCacheConfig {
    size_t max_cache_size;
    size_t max_models;
    bool enable_quantization;
    std::string quantization_type;
    bool enable_fp16;
    bool enable_int8;
    bool enable_dynamic_shapes;
    bool enable_optimized_kernels;
    bool enable_custom_kernels;
    bool enable_fused_operations;
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
};

struct CachedModel {
    std::string model_path;
    std::string model_type;
    std::chrono::system_clock::time_point last_accessed;
    size_t memory_usage;
    std::unique_ptr<nvinfer1::ICudaEngine> trt_engine;
    std::unique_ptr<Ort::Session> onnx_session;
    bool is_quantized;
    std::string quantization_type;
    bool is_optimized;
    std::vector<std::string> optimization_flags;
};

class ModelCache {
public:
    explicit ModelCache(const ModelCacheConfig& config);
    ~ModelCache();

    // Model management
    void load_model(const std::string& model_path, const std::string& model_type);
    void unload_model(const std::string& model_path);
    bool is_model_cached(const std::string& model_path) const;
    CachedModel* get_model(const std::string& model_path);

    // Cache management
    void set_max_cache_size(size_t size);
    void set_max_models(size_t num);
    size_t get_current_cache_size() const;
    size_t get_num_cached_models() const;
    void clear_cache();

    // Optimization
    void enable_quantization(bool enable);
    void set_quantization_type(const std::string& type);
    void enable_fp16(bool enable);
    void enable_int8(bool enable);
    void enable_dynamic_shapes(bool enable);
    void enable_optimized_kernels(bool enable);
    void enable_custom_kernels(bool enable);
    void enable_fused_operations(bool enable);
    void enable_attention_cache(bool enable);
    void enable_kv_cache(bool enable);

private:
    // Configuration and state
    ModelCacheConfig config_;
    std::unordered_map<std::string, CachedModel> cached_models_;
    mutable std::mutex mutex_;
    size_t current_cache_size_;

    // Helper methods
    void initialize_cuda();
    void initialize_tensorrt();
    void initialize_onnx();
    void load_tensorrt_model(const std::string& model_path, CachedModel& model);
    void load_onnx_model(const std::string& model_path, CachedModel& model);
    void optimize_model(CachedModel& model);
    void quantize_model(CachedModel& model);
    void cleanup_old_models();
    size_t calculate_model_size(const CachedModel& model) const;
    void update_model_access_time(CachedModel& model);
    bool should_evict_model(const CachedModel& model) const;
    void evict_model(const std::string& model_path);
};

} // namespace llm_inference
} // namespace cogniware 