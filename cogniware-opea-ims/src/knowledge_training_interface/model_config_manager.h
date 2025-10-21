#pragma once

#include "../common_interfaces/model_interface.h"
#include <string>
#include <vector>
#include <map>
#include <memory>
#include <mutex>
#include <atomic>
#include <functional>

namespace cogniware {

class ModelConfigManager {
public:
    static ModelConfigManager& getInstance();

    // Configuration management
    bool initialize();
    void shutdown();
    bool loadConfig(const std::string& configPath);
    bool saveConfig(const std::string& configPath);
    bool updateConfig(const ModelConfig& config);
    bool removeConfig(const std::string& modelId);
    ModelConfig getConfig(const std::string& modelId) const;

    // Model type management
    bool registerModelType(const std::string& type, 
                          std::function<std::shared_ptr<IModelInterface>(const ModelConfig&)> factory);
    bool unregisterModelType(const std::string& type);
    std::vector<std::string> getRegisteredModelTypes() const;

    // Model instance management
    std::shared_ptr<IModelInterface> createModel(const std::string& modelId);
    bool destroyModel(const std::string& modelId);
    std::shared_ptr<IModelInterface> getModel(const std::string& modelId);
    std::vector<std::string> getActiveModelIds() const;

    // Resource management
    bool allocateResources(const std::string& modelId);
    bool releaseResources(const std::string& modelId);
    bool optimizeResources(const std::string& modelId);
    std::map<std::string, float> getResourceUtilization(const std::string& modelId) const;

    // Monitoring and statistics
    void enableMonitoring(bool enable);
    void setStatusCallback(std::function<void(const std::string&, const ModelStatus&)> callback);
    void printStats() const;

private:
    ModelConfigManager() = default;
    ~ModelConfigManager() = default;
    ModelConfigManager(const ModelConfigManager&) = delete;
    ModelConfigManager& operator=(const ModelConfigManager&) = delete;

    // Internal methods
    bool validateConfig(const ModelConfig& config) const;
    bool checkResourceAvailability(const ModelConfig& config) const;
    void updateResourceMetrics(const std::string& modelId);
    void cleanupUnusedModels();

    // Member variables
    std::mutex mutex_;
    std::atomic<bool> running_{false};
    std::map<std::string, ModelConfig> configs_;
    std::map<std::string, std::shared_ptr<IModelInterface>> models_;
    std::map<std::string, std::function<std::shared_ptr<IModelInterface>(const ModelConfig&)>> factories_;
    std::map<std::string, ModelStatus> modelStatus_;
    std::atomic<bool> monitoringEnabled_{false};
    std::function<void(const std::string&, const ModelStatus&)> statusCallback_;
};

} // namespace cogniware 