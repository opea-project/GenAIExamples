#pragma once

#include "dream/llm_inference_core.h"
#include <memory>
#include <string>
#include <vector>
#include <unordered_map>
#include <mutex>
#include <thread>
#include <atomic>
#include <chrono>
#include <functional>
#include <queue>
#include <condition_variable>

namespace cogniware {
namespace dream {

struct ModelMetadata {
    std::string model_id;
    std::string model_path;
    std::string model_type;
    std::string model_version;
    std::string model_architecture;
    size_t model_size;
    std::vector<std::string> supported_features;
    std::unordered_map<std::string, std::string> model_parameters;
    std::chrono::system_clock::time_point last_used;
    int usage_count;
    bool is_loaded;
    bool is_quantized;
    std::string quantization_type;
};

struct ModelLoadRequest {
    std::string model_id;
    std::string model_path;
    ModelConfig model_config;
    TokenizerConfig tokenizer_config;
    InferenceConfig inference_config;
    std::function<void(bool)> callback;
    int priority;
    std::chrono::system_clock::time_point request_time;
};

struct ModelUnloadRequest {
    std::string model_id;
    std::function<void(bool)> callback;
    bool force;
};

class LLMManager {
public:
    static LLMManager& get_instance();

    // Initialization and configuration
    void initialize(const std::string& config_path);
    void configure(const std::unordered_map<std::string, std::string>& config);
    void shutdown();

    // Model management
    void load_model(const std::string& model_id,
                   const std::string& model_path,
                   const ModelConfig& model_config,
                   const TokenizerConfig& tokenizer_config,
                   const InferenceConfig& inference_config,
                   std::function<void(bool)> callback = nullptr,
                   int priority = 0);
    void unload_model(const std::string& model_id,
                     std::function<void(bool)> callback = nullptr,
                     bool force = false);
    bool is_model_loaded(const std::string& model_id) const;
    std::vector<std::string> get_loaded_models() const;
    ModelMetadata get_model_metadata(const std::string& model_id) const;

    // Model operations
    std::vector<float> run_inference(const std::string& model_id,
                                   const std::vector<int>& input_tokens,
                                   const std::unordered_map<std::string, std::string>& parameters);
    std::vector<float> generate(const std::string& model_id,
                              const std::string& prompt,
                              const std::unordered_map<std::string, std::string>& parameters);
    std::vector<std::vector<float>> batch_inference(
        const std::string& model_id,
        const std::vector<std::vector<int>>& batch_tokens,
        const std::unordered_map<std::string, std::string>& parameters);
    std::vector<std::string> batch_generate(
        const std::string& model_id,
        const std::vector<std::string>& prompts,
        const std::unordered_map<std::string, std::string>& parameters);

    // Resource management
    void set_memory_limit(size_t limit);
    size_t get_available_memory() const;
    void set_max_loaded_models(int count);
    int get_max_loaded_models() const;
    void set_model_priority(const std::string& model_id, int priority);

    // Model optimization
    void optimize_model(const std::string& model_id,
                       const std::unordered_map<std::string, std::string>& optimization_params);
    void quantize_model(const std::string& model_id,
                       const std::string& quantization_type);
    void convert_model_format(const std::string& model_id,
                            const std::string& target_format);

    // Monitoring and metrics
    struct ModelMetrics {
        float load_time;
        float inference_time;
        float memory_usage;
        int inference_count;
        int error_count;
        std::chrono::system_clock::time_point last_inference;
    };
    ModelMetrics get_model_metrics(const std::string& model_id) const;
    void reset_model_metrics(const std::string& model_id);

private:
    LLMManager() = default;
    ~LLMManager() = default;
    LLMManager(const LLMManager&) = delete;
    LLMManager& operator=(const LLMManager&) = delete;

    // Core components
    std::unique_ptr<LLMInferenceCore> inference_core_;
    std::unordered_map<std::string, ModelMetadata> model_metadata_;
    std::unordered_map<std::string, ModelMetrics> model_metrics_;

    // Request queue
    std::priority_queue<ModelLoadRequest> load_queue_;
    std::queue<ModelUnloadRequest> unload_queue_;
    std::mutex queue_mutex_;
    std::condition_variable queue_cv_;

    // Resource limits
    size_t memory_limit_;
    int max_loaded_models_;
    std::atomic<bool> is_running_;

    // Worker thread
    std::thread worker_thread_;
    void worker_loop();
    void process_load_queue();
    void process_unload_queue();

    // Helper functions
    void load_model_internal(const ModelLoadRequest& request);
    void unload_model_internal(const ModelUnloadRequest& request);
    void update_model_metadata(const std::string& model_id, bool is_loaded);
    void update_model_metrics(const std::string& model_id, const ModelMetrics& metrics);
    bool check_memory_requirements(const ModelMetadata& metadata);
    void cleanup_unused_models();
    void validate_model_config(const ModelConfig& config);
    void validate_tokenizer_config(const TokenizerConfig& config);
    void validate_inference_config(const InferenceConfig& config);
};

} // namespace dream
} // namespace cogniware 