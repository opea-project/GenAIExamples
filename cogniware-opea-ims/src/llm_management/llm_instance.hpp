/**
 * @file llm_instance.hpp
 * @brief LLM instance class for the cogniware engine
 */

#ifndef MSMARTCOMPUTE_LLM_INSTANCE_HPP
#define MSMARTCOMPUTE_LLM_INSTANCE_HPP

#include <string>
#include <memory>
#include <mutex>
#include <queue>
#include <condition_variable>
#include <atomic>
#include <thread>
#include <nlohmann/json.hpp>

namespace cogniware {

// Forward declarations
class GGUFLoader;
class InferenceEngine;
class BPETokenizer;

/**
 * @brief Structure representing generation configuration
 */
struct GenerationConfig {
    int max_tokens;
    float temperature;
    int top_k;
    float top_p;
    int num_beams;
    int num_return_sequences;
    std::vector<std::string> stop_sequences;
};

/**
 * @brief Structure representing an inference request
 */
struct InferenceRequest {
    std::string model_id;
    std::string prompt;
    int max_tokens;
    float temperature;
    int top_k;
    float top_p;
    int num_beams;
    int num_return_sequences;
    std::vector<std::string> stop_sequences;
};

/**
 * @brief Structure representing an inference response
 */
struct InferenceResponse {
    std::string text;
    std::vector<float> logprobs;
    std::vector<int> token_ids;
    std::vector<float> token_logprobs;
};

/**
 * @brief Class representing a single LLM instance
 */
class LLMInstance {
public:
    /**
     * @brief Constructor
     * @param model_id Model identifier
     * @param config Model configuration
     */
    LLMInstance(const std::string& model_id, const nlohmann::json& config);
    
    /**
     * @brief Destructor
     */
    ~LLMInstance();
    
    /**
     * @brief Initialize the instance
     * @return true if initialization successful, false otherwise
     */
    bool initialize();
    
    /**
     * @brief Shutdown the instance
     */
    void shutdown();
    
    /**
     * @brief Perform inference
     * @param request Inference request
     * @param response Inference response
     * @return true if inference successful, false otherwise
     */
    bool infer(const InferenceRequest& request, InferenceResponse& response);
    
    /**
     * @brief Get instance status
     * @return JSON object containing status information
     */
    nlohmann::json getStatus() const;
    
    /**
     * @brief Get resource usage
     * @return JSON object containing resource usage information
     */
    nlohmann::json getResourceUsage() const;
    
    /**
     * @brief Set instance configuration
     * @param config Configuration to apply
     * @return true if configuration successful, false otherwise
     */
    bool setConfig(const nlohmann::json& config);
    
    /**
     * @brief Get instance configuration
     * @return JSON object containing configuration
     */
    nlohmann::json getConfig() const;
    
    /**
     * @brief Update resource usage statistics
     */
    void updateResourceUsage();

private:
    /**
     * @brief Load model
     * @return true if loading successful, false otherwise
     */
    bool loadModel();
    
    /**
     * @brief Unload model
     */
    void unloadModel();
    
    /**
     * @brief Process inference queue
     */
    void processQueue();
    
    /**
     * @brief Validate configuration
     * @param config Configuration to validate
     * @return true if configuration valid, false otherwise
     */
    bool validateConfig(const nlohmann::json& config) const;

    std::string model_id_;
    nlohmann::json config_;
    std::mutex mutex_;
    std::atomic<bool> running_;
    std::thread worker_thread_;
    std::queue<std::pair<InferenceRequest, InferenceResponse*>> request_queue_;
    std::condition_variable queue_cv_;
    
    // Model components
    std::unique_ptr<GGUFLoader> model_loader_;
    std::unique_ptr<InferenceEngine> inference_engine_;
    std::unique_ptr<BPETokenizer> tokenizer_;
    
    // Resource usage statistics
    struct {
        size_t vram_used;
        size_t vram_total;
        float gpu_utilization;
        float memory_utilization;
        size_t requests_processed;
        size_t tokens_generated;
        double average_latency;
    } resource_stats_;
};

} // namespace cogniware

#endif // MSMARTCOMPUTE_LLM_INSTANCE_HPP 