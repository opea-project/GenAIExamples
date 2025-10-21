/**
 * @file model_config_manager.hpp
 * @brief Model configuration manager for the cogniware engine
 */

#ifndef MSMARTCOMPUTE_MODEL_CONFIG_MANAGER_HPP
#define MSMARTCOMPUTE_MODEL_CONFIG_MANAGER_HPP

#include <string>
#include <unordered_map>
#include <memory>
#include <mutex>
#include <nlohmann/json.hpp>

namespace cogniware {

/**
 * @brief Structure representing a model configuration
 */
struct ModelConfig {
    std::string model_id;
    std::string model_type;
    nlohmann::json model_config;
};

/**
 * @brief Class for managing model configurations
 */
class ModelConfigManager {
public:
    /**
     * @brief Get the singleton instance
     * @return Reference to the singleton instance
     */
    static ModelConfigManager& getInstance();

    /**
     * @brief Initialize the configuration manager
     * @param config_path Path to the configuration directory
     * @return true if initialization successful, false otherwise
     */
    bool initialize(const std::string& config_path);

    /**
     * @brief Register a new model configuration
     * @param config Model configuration to register
     * @return true if registration successful, false otherwise
     */
    bool registerModel(const ModelConfig& config);

    /**
     * @brief Get model configuration by ID
     * @param model_id ID of the model
     * @return Pointer to the model configuration, nullptr if not found
     */
    std::shared_ptr<ModelConfig> getModelConfig(const std::string& model_id);

    /**
     * @brief Update an existing model configuration
     * @param model_id ID of the model to update
     * @param updates JSON object containing updates
     * @return true if update successful, false otherwise
     */
    bool updateModelConfig(const std::string& model_id, const nlohmann::json& updates);

    /**
     * @brief List all registered model IDs
     * @return Vector of model IDs
     */
    std::vector<std::string> listModels();

    /**
     * @brief Get model type by ID
     * @param model_id ID of the model
     * @return Model type string, empty if not found
     */
    std::string getModelType(const std::string& model_id);

    /**
     * @brief Get model architecture by ID
     * @param model_id ID of the model
     * @return JSON object containing architecture config, empty if not found
     */
    nlohmann::json getModelArchitecture(const std::string& model_id);

    /**
     * @brief Get model parameters by ID
     * @param model_id ID of the model
     * @return JSON object containing parameters, empty if not found
     */
    nlohmann::json getModelParameters(const std::string& model_id);

    /**
     * @brief Get tokenizer configuration by ID
     * @param model_id ID of the model
     * @return JSON object containing tokenizer config, empty if not found
     */
    nlohmann::json getTokenizerConfig(const std::string& model_id);

    /**
     * @brief Get generation configuration by ID
     * @param model_id ID of the model
     * @return JSON object containing generation config, empty if not found
     */
    nlohmann::json getGenerationConfig(const std::string& model_id);

    /**
     * @brief Get quantization configuration by ID
     * @param model_id ID of the model
     * @return JSON object containing quantization config, empty if not found
     */
    nlohmann::json getQuantizationConfig(const std::string& model_id);

    /**
     * @brief Get optimization configuration by ID
     * @param model_id ID of the model
     * @return JSON object containing optimization config, empty if not found
     */
    nlohmann::json getOptimizationConfig(const std::string& model_id);

    /**
     * @brief Get model metadata by ID
     * @param model_id ID of the model
     * @return JSON object containing metadata, empty if not found
     */
    nlohmann::json getModelMetadata(const std::string& model_id);

public:
    ModelConfigManager() = default;
    ~ModelConfigManager() = default;
private:
    ModelConfigManager(const ModelConfigManager&) = delete;
    ModelConfigManager& operator=(const ModelConfigManager&) = delete;

    /**
     * @brief Load schema from file
     * @param schema_file Path to schema file
     * @return true if loading successful, false otherwise
     */
    bool loadSchema(const std::string& schema_file);

    /**
     * @brief Load configurations from directory
     * @return true if loading successful, false otherwise
     */
    bool loadConfigurations();

    /**
     * @brief Validate configuration against schema
     * @param config Configuration to validate
     * @return true if valid, false otherwise
     */
    bool validateConfig(const nlohmann::json& config);

    /**
     * @brief Save configuration to file
     * @param model_id ID of the model
     * @param config Configuration to save
     * @return true if saving successful, false otherwise
     */
    bool saveConfig(const std::string& model_id, const nlohmann::json& config);

    std::string config_path_;
    std::string schema_path_;
    std::string models_path_;
    nlohmann::json schema_;
    std::unordered_map<std::string, std::shared_ptr<ModelConfig>> registry_;
    std::mutex mutex_;
};

} // namespace cogniware

#endif // MSMARTCOMPUTE_MODEL_CONFIG_MANAGER_HPP 