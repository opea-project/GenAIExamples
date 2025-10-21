#pragma once

#include "llm_inference_core.h"
#include <string>
#include <unordered_map>
#include <memory>
#include <mutex>
#include <json/json.h>

namespace cogniware {

class ModelConfigManager {
public:
    static ModelConfigManager& get_instance() {
        static ModelConfigManager instance;
        return instance;
    }

    // Load model configuration from JSON file
    void load_config(const std::string& config_path);
    
    // Get model configuration by name
    LLMConfig get_config(const std::string& model_name) const;
    
    // Check if model configuration exists
    bool has_config(const std::string& model_name) const;
    
    // List available model configurations
    std::vector<std::string> list_models() const;
    
    // Update model configuration
    void update_config(const std::string& model_name, const LLMConfig& config);
    
    // Remove model configuration
    void remove_config(const std::string& model_name);

private:
    ModelConfigManager() = default;
    ~ModelConfigManager() = default;
    
    // Prevent copying
    ModelConfigManager(const ModelConfigManager&) = delete;
    ModelConfigManager& operator=(const ModelConfigManager&) = delete;
    
    // Parse JSON configuration
    LLMConfig parse_config(const Json::Value& json_config) const;
    
    // Save configurations to file
    void save_configs() const;
    
    // Model configurations
    std::unordered_map<std::string, LLMConfig> configs_;
    mutable std::mutex mutex_;
    std::string config_file_path_;
};

} // namespace cogniware 