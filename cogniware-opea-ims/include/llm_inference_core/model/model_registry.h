#pragma once

#include "model_selector.h"
#include "model_downloader.h"
#include "model_configurator.h"
#include <string>
#include <vector>
#include <map>
#include <memory>
#include <mutex>
#include <chrono>

namespace cogniware {

// Model registry entry
struct ModelRegistryEntry {
    ModelMetadata metadata;
    ModelConfiguration configuration;
    DownloadStatus downloadStatus;
    bool isAvailable;
    bool isActive;
    std::chrono::system_clock::time_point lastUsed;
    std::chrono::system_clock::time_point lastUpdated;
    std::map<std::string, std::string> usageStats;
    std::vector<std::string> dependencies;
    std::vector<std::string> dependents;
};

// Model registry interface
class ModelRegistry {
public:
    virtual ~ModelRegistry() = default;

    // Model registration
    virtual bool registerModel(const ModelMetadata& metadata) = 0;
    virtual bool unregisterModel(const std::string& modelId) = 0;
    virtual bool updateModelMetadata(const std::string& modelId, 
                                   const ModelMetadata& metadata) = 0;

    // Model querying
    virtual ModelRegistryEntry getModelEntry(const std::string& modelId) = 0;
    virtual std::vector<ModelRegistryEntry> getAllModels() = 0;
    virtual std::vector<ModelRegistryEntry> getModelsByType(ModelType type) = 0;
    virtual std::vector<ModelRegistryEntry> getModelsByTask(SupportedTask task) = 0;
    virtual std::vector<ModelRegistryEntry> getAvailableModels() = 0;
    virtual std::vector<ModelRegistryEntry> getActiveModels() = 0;

    // Model status management
    virtual bool setModelAvailable(const std::string& modelId, bool available) = 0;
    virtual bool setModelActive(const std::string& modelId, bool active) = 0;
    virtual bool updateModelUsage(const std::string& modelId) = 0;
    virtual bool updateDownloadStatus(const std::string& modelId, DownloadStatus status) = 0;

    // Model dependencies
    virtual bool addModelDependency(const std::string& modelId, const std::string& dependencyId) = 0;
    virtual bool removeModelDependency(const std::string& modelId, const std::string& dependencyId) = 0;
    virtual std::vector<std::string> getModelDependencies(const std::string& modelId) = 0;
    virtual std::vector<std::string> getModelDependents(const std::string& modelId) = 0;

    // Model statistics
    virtual std::map<std::string, std::string> getModelStats(const std::string& modelId) = 0;
    virtual std::map<std::string, std::string> getRegistryStats() = 0;
};

// Advanced model registry
class AdvancedModelRegistry : public ModelRegistry {
public:
    AdvancedModelRegistry();
    ~AdvancedModelRegistry() override = default;

    // Model registration
    bool registerModel(const ModelMetadata& metadata) override;
    bool unregisterModel(const std::string& modelId) override;
    bool updateModelMetadata(const std::string& modelId, 
                           const ModelMetadata& metadata) override;

    // Model querying
    ModelRegistryEntry getModelEntry(const std::string& modelId) override;
    std::vector<ModelRegistryEntry> getAllModels() override;
    std::vector<ModelRegistryEntry> getModelsByType(ModelType type) override;
    std::vector<ModelRegistryEntry> getModelsByTask(SupportedTask task) override;
    std::vector<ModelRegistryEntry> getAvailableModels() override;
    std::vector<ModelRegistryEntry> getActiveModels() override;

    // Model status management
    bool setModelAvailable(const std::string& modelId, bool available) override;
    bool setModelActive(const std::string& modelId, bool active) override;
    bool updateModelUsage(const std::string& modelId) override;
    bool updateDownloadStatus(const std::string& modelId, DownloadStatus status) override;

    // Model dependencies
    bool addModelDependency(const std::string& modelId, const std::string& dependencyId) override;
    bool removeModelDependency(const std::string& modelId, const std::string& dependencyId) override;
    std::vector<std::string> getModelDependencies(const std::string& modelId) override;
    std::vector<std::string> getModelDependents(const std::string& modelId) override;

    // Model statistics
    std::map<std::string, std::string> getModelStats(const std::string& modelId) override;
    std::map<std::string, std::string> getRegistryStats() override;

    // Advanced registry methods
    std::vector<ModelRegistryEntry> searchModels(const std::string& query);
    std::vector<ModelRegistryEntry> getModelsBySource(ModelSource source);
    std::vector<ModelRegistryEntry> getModelsByLicense(const std::string& license);
    std::vector<ModelRegistryEntry> getModelsByLanguage(const std::string& language);
    std::vector<ModelRegistryEntry> getRecentlyUsedModels(size_t count = 10);
    std::vector<ModelRegistryEntry> getPopularModels(size_t count = 10);

    // Model lifecycle management
    bool initializeModel(const std::string& modelId);
    bool activateModel(const std::string& modelId);
    bool deactivateModel(const std::string& modelId);
    bool cleanupModel(const std::string& modelId);

    // Registry maintenance
    bool cleanupUnusedModels();
    bool updateRegistryIndex();
    bool validateRegistry();
    bool backupRegistry(const std::string& backupPath);
    bool restoreRegistry(const std::string& backupPath);

    // Configuration
    void setRegistryPath(const std::string& path);
    std::string getRegistryPath() const;
    void setMaxModels(size_t max);
    size_t getMaxModels() const;

private:
    std::map<std::string, ModelRegistryEntry> models_;
    std::map<ModelType, std::vector<std::string>> modelsByType_;
    std::map<SupportedTask, std::vector<std::string>> modelsByTask_;
    std::map<ModelSource, std::vector<std::string>> modelsBySource_;
    std::string registryPath_;
    size_t maxModels_;
    std::mutex registryMutex_;

    // Helper methods
    bool saveRegistry();
    bool loadRegistry();
    void updateIndexes();
    void updateModelIndexes(const std::string& modelId, const ModelRegistryEntry& entry);
    void removeModelIndexes(const std::string& modelId);
    std::vector<std::string> searchInMetadata(const std::string& query, 
                                            const std::vector<std::string>& modelIds);
    bool validateModelEntry(const ModelRegistryEntry& entry);
    void cleanupExpiredEntries();
};

// Model registry manager
class ModelRegistryManager {
public:
    static ModelRegistryManager& getInstance();

    // Model registration
    bool registerModel(const ModelMetadata& metadata);
    bool unregisterModel(const std::string& modelId);
    bool updateModelMetadata(const std::string& modelId, const ModelMetadata& metadata);

    // Model querying
    ModelRegistryEntry getModelEntry(const std::string& modelId);
    std::vector<ModelRegistryEntry> getAllModels();
    std::vector<ModelRegistryEntry> getModelsByType(ModelType type);
    std::vector<ModelRegistryEntry> getModelsByTask(SupportedTask task);
    std::vector<ModelRegistryEntry> getAvailableModels();
    std::vector<ModelRegistryEntry> getActiveModels();

    // Model status management
    bool setModelAvailable(const std::string& modelId, bool available);
    bool setModelActive(const std::string& modelId, bool active);
    bool updateModelUsage(const std::string& modelId);
    bool updateDownloadStatus(const std::string& modelId, DownloadStatus status);

    // Model dependencies
    bool addModelDependency(const std::string& modelId, const std::string& dependencyId);
    bool removeModelDependency(const std::string& modelId, const std::string& dependencyId);
    std::vector<std::string> getModelDependencies(const std::string& modelId);
    std::vector<std::string> getModelDependents(const std::string& modelId);

    // Model statistics
    std::map<std::string, std::string> getModelStats(const std::string& modelId);
    std::map<std::string, std::string> getRegistryStats();

    // Advanced registry methods
    std::vector<ModelRegistryEntry> searchModels(const std::string& query);
    std::vector<ModelRegistryEntry> getModelsBySource(ModelSource source);
    std::vector<ModelRegistryEntry> getModelsByLicense(const std::string& license);
    std::vector<ModelRegistryEntry> getModelsByLanguage(const std::string& language);
    std::vector<ModelRegistryEntry> getRecentlyUsedModels(size_t count = 10);
    std::vector<ModelRegistryEntry> getPopularModels(size_t count = 10);

    // Model lifecycle management
    bool initializeModel(const std::string& modelId);
    bool activateModel(const std::string& modelId);
    bool deactivateModel(const std::string& modelId);
    bool cleanupModel(const std::string& modelId);

    // Registry maintenance
    bool cleanupUnusedModels();
    bool updateRegistryIndex();
    bool validateRegistry();
    bool backupRegistry(const std::string& backupPath);
    bool restoreRegistry(const std::string& backupPath);

    // Configuration
    void setRegistryPath(const std::string& path);
    std::string getRegistryPath() const;
    void setMaxModels(size_t max);
    size_t getMaxModels() const;

    // Integration with other components
    void setModelSelector(std::shared_ptr<ModelSelector> selector);
    void setModelDownloader(std::shared_ptr<ModelDownloader> downloader);
    void setModelConfigurator(std::shared_ptr<ModelConfigurator> configurator);

    // Cleanup
    void cleanup();

private:
    ModelRegistryManager();
    ~ModelRegistryManager();

    std::unique_ptr<AdvancedModelRegistry> registry_;
    std::shared_ptr<ModelSelector> modelSelector_;
    std::shared_ptr<ModelDownloader> modelDownloader_;
    std::shared_ptr<ModelConfigurator> modelConfigurator_;
    std::mutex managerMutex_;
};

} // namespace cogniware
