/**
 * @file cognidream_admin.hpp
 * @brief Admin interface for CogniDream
 */

#pragma once

#include <string>
#include <vector>
#include <memory>
#include <unordered_map>
#include <mutex>
#include <chrono>
#include <nlohmann/json.hpp>

namespace cognidream {

/**
 * @brief Structure representing a user session
 */
struct UserSession {
    std::string session_id;
    std::string user_id;
    std::string model_id;
    std::chrono::system_clock::time_point created_at;
    std::chrono::system_clock::time_point last_active;
    size_t requests_processed;
    size_t tokens_generated;
};

/**
 * @brief Structure representing system metrics
 */
struct SystemMetrics {
    size_t total_requests;
    size_t total_tokens;
    size_t active_sessions;
    size_t total_vram_used;
    size_t total_vram_available;
    float average_latency;
    std::vector<float> gpu_utilization;
    std::vector<float> memory_utilization;
};

/**
 * @brief Class for managing CogniDream admin interface
 */
class CogniDreamAdmin {
public:
    /**
     * @brief Get singleton instance
     * @return Reference to the singleton instance
     */
    static CogniDreamAdmin& getInstance();

    // Delete copy constructor and assignment operator
    CogniDreamAdmin(const CogniDreamAdmin&) = delete;
    CogniDreamAdmin& operator=(const CogniDreamAdmin&) = delete;

    // System management
    bool initialize(const std::string& config_path);
    bool shutdown();
    bool isInitialized() const;

    // Model management
    bool loadModel(const std::string& model_id, const std::string& model_path);
    bool unloadModel(const std::string& model_id);
    bool isModelLoaded(const std::string& model_id) const;
    std::vector<std::string> getLoadedModels() const;

    // Resource management
    bool setResourceLimits(const std::string& resource_type, const nlohmann::json& limits);
    nlohmann::json getResourceUsage() const;
    bool adjustResourceAllocation(const std::string& resource_type, const nlohmann::json& allocation);

    // Monitoring and metrics
    nlohmann::json getSystemMetrics() const;
    nlohmann::json getModelMetrics(const std::string& model_id) const;
    bool setMonitoringConfig(const nlohmann::json& config);

    // Security management
    bool updateSecurityConfig(const nlohmann::json& config);
    bool validateAccessToken(const std::string& token) const;
    std::string generateAccessToken(const std::string& user_id, const std::vector<std::string>& permissions);

    // User management
    std::string createSession(const std::string& user_id, const std::string& model_id);
    bool endSession(const std::string& session_id);
    UserSession getSessionInfo(const std::string& session_id);
    std::vector<UserSession> getActiveSessions();

    // Model statistics
    nlohmann::json getModelStats(const std::string& model_id);
    std::unordered_map<std::string, nlohmann::json> getAllModelStats();

    // User statistics
    nlohmann::json getUserStats(const std::string& user_id);
    std::unordered_map<std::string, nlohmann::json> getAllUserStats();

    // Update model configuration
    bool updateModelConfig(const std::string& model_id, const nlohmann::json& config);

private:
    CogniDreamAdmin() = default;
    ~CogniDreamAdmin() = default;

    // Internal state
    bool initialized_{false};
    std::mutex mutex_;
    std::unordered_map<std::string, std::shared_ptr<void>> loaded_models_;
    nlohmann::json config_;
    std::chrono::system_clock::time_point last_metrics_update_;

    // Internal helper methods
    bool validateConfig(const nlohmann::json& config) const;
    void updateMetrics();
    bool checkResourceAvailability(const std::string& resource_type, const nlohmann::json& requirements) const;

    // Additional member variables
    std::unordered_map<std::string, UserSession> sessions_;
    std::unordered_map<std::string, nlohmann::json> model_stats_;
    std::unordered_map<std::string, nlohmann::json> user_stats_;
    SystemMetrics current_metrics_;
};

} // namespace cognidream 