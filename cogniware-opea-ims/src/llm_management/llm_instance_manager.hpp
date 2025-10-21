/**
 * @file llm_instance_manager.hpp
 * @brief LLM instance manager for the cogniware engine
 */

#ifndef MSMARTCOMPUTE_LLM_INSTANCE_MANAGER_HPP
#define MSMARTCOMPUTE_LLM_INSTANCE_MANAGER_HPP

#include <string>
#include <memory>
#include <unordered_map>
#include <mutex>
#include <vector>
#include <queue>
#include <condition_variable>
#include <atomic>
#include <thread>
#include <nlohmann/json.hpp>

namespace cogniware {

class LLMInstance;

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
 * @brief Class for managing LLM instances
 */
class LLMInstanceManager {
public:
    /**
     * @brief Get singleton instance
     * @return Reference to the singleton instance
     */
    static LLMInstanceManager& getInstance();

    /**
     * @brief Initialize the instance manager
     * @param config_path Path to configuration directory
     * @return true if initialization successful, false otherwise
     */
    bool initialize(const std::string& config_path);

    /**
     * @brief Create a new LLM instance
     * @param model_id Model identifier
     * @return true if creation successful, false otherwise
     */
    bool createInstance(const std::string& model_id);

    /**
     * @brief Destroy an LLM instance
     * @param model_id Model identifier
     * @return true if destruction successful, false otherwise
     */
    bool destroyInstance(const std::string& model_id);

    /**
     * @brief Submit an inference request
     * @param request Inference request
     * @param response Inference response
     * @return true if submission successful, false otherwise
     */
    bool submitInferenceRequest(
        const InferenceRequest& request,
        InferenceResponse& response
    );

    /**
     * @brief Get instance status
     * @param model_id Model identifier
     * @return JSON object containing status information
     */
    nlohmann::json getInstanceStatus(const std::string& model_id);

    /**
     * @brief Get resource usage statistics
     * @return JSON object containing resource usage information
     */
    nlohmann::json getResourceUsage();

    /**
     * @brief Set instance configuration
     * @param model_id Model identifier
     * @param config Configuration to apply
     * @return true if configuration successful, false otherwise
     */
    bool setInstanceConfig(
        const std::string& model_id,
        const nlohmann::json& config
    );

    /**
     * @brief Get instance configuration
     * @param model_id Model identifier
     * @return JSON object containing configuration
     */
    nlohmann::json getInstanceConfig(const std::string& model_id);

public:
    LLMInstanceManager() = default;
    ~LLMInstanceManager() = default;
private:
    LLMInstanceManager(const LLMInstanceManager&) = delete;
    LLMInstanceManager& operator=(const LLMInstanceManager&) = delete;

    /**
     * @brief Load instance configurations
     * @return true if loading successful, false otherwise
     */
    bool loadConfigurations();

    /**
     * @brief Save instance configurations
     * @return true if saving successful, false otherwise
     */
    bool saveConfigurations();

    /**
     * @brief Monitor resource usage
     */
    void monitorResources();

    std::string config_path_;
    std::unordered_map<std::string, std::shared_ptr<LLMInstance>> instances_;
    std::mutex mutex_;
    std::atomic<bool> running_;
    std::thread monitor_thread_;
};

} // namespace cogniware

#endif // MSMARTCOMPUTE_LLM_INSTANCE_MANAGER_HPP 