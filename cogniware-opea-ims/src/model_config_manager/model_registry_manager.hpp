/**
 * @file model_registry_manager.hpp
 * @brief Model registry manager for cogniware engine
 */

#ifndef MSMARTCOMPUTE_MODEL_REGISTRY_MANAGER_HPP
#define MSMARTCOMPUTE_MODEL_REGISTRY_MANAGER_HPP

#include <string>
#include <unordered_map>
#include <memory>
#include <mutex>
#include <nlohmann/json.hpp>

namespace cogniware {

/**
 * @brief Model registry entry structure
 */
struct ModelRegistryEntry {
    std::string model_id;
    std::string model_name;
    std::string model_family;
    std::string model_type;
    std::string version;
    std::string status;
    std::string path_to_model_files;
    int required_vram_mb;
    std::vector<std::string> supported_features;
    nlohmann::json model_parameters;
    nlohmann::json quantization;
    nlohmann::json performance_metrics;
    nlohmann::json dependencies;
    nlohmann::json metadata;
};

/**
 * @brief Model registry manager class
 */
class ModelRegistryManager {
public:
    /**
     * @brief Get singleton instance
     */
    static ModelRegistryManager& getInstance();

    /**
     * @brief Initialize the registry manager
     * @param config_path Path to configuration directory
     * @return true if initialization successful
     */
    bool initialize(const std::string& config_path);

    /**
     * @brief Register a new model
     * @param entry Model registry entry
     * @return true if registration successful
     */
    bool registerModel(const ModelRegistryEntry& entry);

    /**
     * @brief Get model entry by ID
     * @param model_id Model identifier
     * @return Pointer to model entry if found, nullptr otherwise
     */
    const ModelRegistryEntry* getModelEntry(const std::string& model_id) const;

    /**
     * @brief Update model entry
     * @param model_id Model identifier
     * @param updates JSON object with updates
     * @return true if update successful
     */
    bool updateModelEntry(const std::string& model_id, const nlohmann::json& updates);

    /**
     * @brief List all registered model IDs
     * @return Vector of model IDs
     */
    std::vector<std::string> listModels() const;

    /**
     * @brief Get model metadata
     * @param model_id Model identifier
     * @return JSON object with metadata
     */
    nlohmann::json getModelMetadata(const std::string& model_id) const;

    /**
     * @brief Get model performance metrics
     * @param model_id Model identifier
     * @return JSON object with performance metrics
     */
    nlohmann::json getModelPerformance(const std::string& model_id) const;

    /**
     * @brief Validate model entry against schema
     * @param entry Model registry entry
     * @return true if valid
     */
    bool validateModelEntry(const ModelRegistryEntry& entry) const;

public:
    ModelRegistryManager() = default;
    ~ModelRegistryManager() = default;
private:
    ModelRegistryManager(const ModelRegistryManager&) = delete;
    ModelRegistryManager& operator=(const ModelRegistryManager&) = delete;

    /**
     * @brief Load registry from file
     * @param file_path Path to registry file
     * @return true if load successful
     */
    bool loadRegistry(const std::string& file_path);

    /**
     * @brief Save registry to file
     * @param file_path Path to registry file
     * @return true if save successful
     */
    bool saveRegistry(const std::string& file_path) const;

    std::string config_path_;
    std::unordered_map<std::string, ModelRegistryEntry> registry_;
    mutable std::mutex mutex_;
    nlohmann::json schema_;
};

} // namespace cogniware

#endif // MSMARTCOMPUTE_MODEL_REGISTRY_MANAGER_HPP 