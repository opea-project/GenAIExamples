#pragma once

#include "model_selector.h"
#include "model_downloader.h"
#include "model_configurator.h"
#include "model_registry.h"
#include <string>
#include <vector>
#include <memory>
#include <functional>
#include <mutex>

namespace cogniware {

// Model management system interface
class ModelManagerSystem {
public:
    virtual ~ModelManagerSystem() = default;

    // System initialization
    virtual bool initialize() = 0;
    virtual void shutdown() = 0;

    // Model discovery and selection
    virtual std::vector<ModelMetadata> searchModels(const std::string& query, 
                                                  ModelSource source = ModelSource::HUGGING_FACE) = 0;
    virtual std::vector<ModelMetadata> getPopularModels(ModelSource source = ModelSource::HUGGING_FACE) = 0;
    virtual std::vector<ModelMetadata> getModelsByTask(SupportedTask task, 
                                                     ModelSource source = ModelSource::HUGGING_FACE) = 0;
    virtual ModelMetadata getModelInfo(const std::string& modelId, 
                                     ModelSource source = ModelSource::HUGGING_FACE) = 0;

    // Model downloading
    virtual std::string downloadModel(const ModelMetadata& model, 
                                    const std::string& downloadPath,
                                    DownloadProgressCallback callback = nullptr) = 0;
    virtual bool cancelDownload(const std::string& taskId) = 0;
    virtual DownloadProgress getDownloadProgress(const std::string& taskId) = 0;
    virtual std::vector<DownloadProgress> getAllDownloadProgress() = 0;

    // Model configuration
    virtual bool configureModel(const ModelMetadata& model, 
                              const ModelConfiguration& config) = 0;
    virtual ModelConfiguration getModelConfiguration(const std::string& modelId) = 0;
    virtual bool updateModelConfiguration(const std::string& modelId, 
                                        const ModelConfiguration& config) = 0;
    virtual ModelConfiguration autoConfigureModel(const ModelMetadata& model) = 0;

    // Model registry management
    virtual bool registerModel(const ModelMetadata& metadata) = 0;
    virtual bool unregisterModel(const std::string& modelId) = 0;
    virtual ModelRegistryEntry getModelEntry(const std::string& modelId) = 0;
    virtual std::vector<ModelRegistryEntry> getAllModels() = 0;
    virtual std::vector<ModelRegistryEntry> getAvailableModels() = 0;
    virtual std::vector<ModelRegistryEntry> getActiveModels() = 0;

    // Model lifecycle management
    virtual bool activateModel(const std::string& modelId) = 0;
    virtual bool deactivateModel(const std::string& modelId) = 0;
    virtual bool isModelAvailable(const std::string& modelId) = 0;
    virtual bool isModelActive(const std::string& modelId) = 0;

    // Model utilities
    virtual bool verifyModel(const std::string& modelId) = 0;
    virtual bool cleanupModel(const std::string& modelId) = 0;
    virtual std::vector<std::string> getModelDependencies(const std::string& modelId) = 0;
    virtual std::map<std::string, std::string> getModelStats(const std::string& modelId) = 0;
};

// Comprehensive model management system
class ComprehensiveModelManagerSystem : public ModelManagerSystem {
public:
    ComprehensiveModelManagerSystem();
    ~ComprehensiveModelManagerSystem() override;

    // System initialization
    bool initialize() override;
    void shutdown() override;

    // Model discovery and selection
    std::vector<ModelMetadata> searchModels(const std::string& query, 
                                          ModelSource source = ModelSource::HUGGING_FACE) override;
    std::vector<ModelMetadata> getPopularModels(ModelSource source = ModelSource::HUGGING_FACE) override;
    std::vector<ModelMetadata> getModelsByTask(SupportedTask task, 
                                             ModelSource source = ModelSource::HUGGING_FACE) override;
    ModelMetadata getModelInfo(const std::string& modelId, 
                             ModelSource source = ModelSource::HUGGING_FACE) override;

    // Model downloading
    std::string downloadModel(const ModelMetadata& model, 
                            const std::string& downloadPath,
                            DownloadProgressCallback callback = nullptr) override;
    bool cancelDownload(const std::string& taskId) override;
    DownloadProgress getDownloadProgress(const std::string& taskId) override;
    std::vector<DownloadProgress> getAllDownloadProgress() override;

    // Model configuration
    bool configureModel(const ModelMetadata& model, 
                       const ModelConfiguration& config) override;
    ModelConfiguration getModelConfiguration(const std::string& modelId) override;
    bool updateModelConfiguration(const std::string& modelId, 
                                 const ModelConfiguration& config) override;
    ModelConfiguration autoConfigureModel(const ModelMetadata& model) override;

    // Model registry management
    bool registerModel(const ModelMetadata& metadata) override;
    bool unregisterModel(const std::string& modelId) override;
    ModelRegistryEntry getModelEntry(const std::string& modelId) override;
    std::vector<ModelRegistryEntry> getAllModels() override;
    std::vector<ModelRegistryEntry> getAvailableModels() override;
    std::vector<ModelRegistryEntry> getActiveModels() override;

    // Model lifecycle management
    bool activateModel(const std::string& modelId) override;
    bool deactivateModel(const std::string& modelId) override;
    bool isModelAvailable(const std::string& modelId) override;
    bool isModelActive(const std::string& modelId) override;

    // Model utilities
    bool verifyModel(const std::string& modelId) override;
    bool cleanupModel(const std::string& modelId) override;
    std::vector<std::string> getModelDependencies(const std::string& modelId) override;
    std::map<std::string, std::string> getModelStats(const std::string& modelId) override;

    // Advanced model management
    std::vector<ModelMetadata> searchAllSources(const std::string& query);
    std::vector<ModelMetadata> getRecommendedModels(SupportedTask task, 
                                                   ModelType type = ModelType::INTERFACE_MODEL);
    bool downloadAndConfigureModel(const std::string& modelId, 
                                 ModelSource source,
                                 const std::string& downloadPath,
                                 DownloadProgressCallback callback = nullptr);
    bool setupModelForTask(const std::string& modelId, SupportedTask task);
    bool optimizeModelConfiguration(const std::string& modelId, 
                                  const std::string& optimizationType = "performance");

    // Model analysis and recommendations
    std::vector<std::string> analyzeModelCompatibility(const std::string& modelId, 
                                                      SupportedTask task);
    std::vector<std::string> getModelRecommendations(SupportedTask task, 
                                                    ModelType type = ModelType::INTERFACE_MODEL);
    std::map<std::string, std::string> compareModels(const std::vector<std::string>& modelIds);

    // System configuration
    void setDownloadPath(const std::string& path);
    std::string getDownloadPath() const;
    void setConfigurationPath(const std::string& path);
    std::string getConfigurationPath() const;
    void setRegistryPath(const std::string& path);
    std::string getRegistryPath() const;
    void setMaxConcurrentDownloads(size_t max);
    size_t getMaxConcurrentDownloads() const;

    // System statistics
    std::map<std::string, std::string> getSystemStats();
    std::map<std::string, std::string> getDownloadStats();
    std::map<std::string, std::string> getConfigurationStats();
    std::map<std::string, std::string> getRegistryStats();

    // System maintenance
    bool cleanupSystem();
    bool backupSystem(const std::string& backupPath);
    bool restoreSystem(const std::string& backupPath);
    bool validateSystem();
    bool updateSystem();

private:
    // Component references
    std::unique_ptr<ModelSelectorFactory> selectorFactory_;
    std::unique_ptr<ModelDownloadManager> downloadManager_;
    std::unique_ptr<ModelConfigurationManager> configManager_;
    std::unique_ptr<ModelRegistryManager> registryManager_;

    // System state
    bool initialized_;
    std::string downloadPath_;
    std::string configurationPath_;
    std::string registryPath_;
    size_t maxConcurrentDownloads_;
    std::mutex systemMutex_;

    // Helper methods
    bool initializeComponents();
    void shutdownComponents();
    std::shared_ptr<ModelSelector> getSelector(ModelSource source);
    std::shared_ptr<ModelDownloader> getDownloader(ModelSource source);
    bool validateModelMetadata(const ModelMetadata& metadata);
    bool validateModelConfiguration(const ModelConfiguration& config);
    void updateModelUsage(const std::string& modelId);
    std::vector<SupportedTask> identifyModelTasks(const ModelMetadata& model);
    ModelType determineModelType(const ModelMetadata& model, 
                                const std::vector<SupportedTask>& tasks);
};

// Model management system factory
class ModelManagerSystemFactory {
public:
    static std::unique_ptr<ModelManagerSystem> createSystem();
    static std::unique_ptr<ComprehensiveModelManagerSystem> createComprehensiveSystem();
};

// Global model management system instance
class GlobalModelManagerSystem {
public:
    static GlobalModelManagerSystem& getInstance();

    // System access
    ModelManagerSystem& getSystem();
    ComprehensiveModelManagerSystem& getComprehensiveSystem();

    // System lifecycle
    bool initialize();
    void shutdown();
    bool isInitialized() const;

    // Quick access methods
    std::vector<ModelMetadata> searchModels(const std::string& query, 
                                          ModelSource source = ModelSource::HUGGING_FACE);
    std::string downloadModel(const ModelMetadata& model, 
                            const std::string& downloadPath,
                            DownloadProgressCallback callback = nullptr);
    bool configureModel(const ModelMetadata& model, 
                       const ModelConfiguration& config);
    ModelRegistryEntry getModelEntry(const std::string& modelId);
    std::vector<ModelRegistryEntry> getAvailableModels();

private:
    GlobalModelManagerSystem();
    ~GlobalModelManagerSystem();

    std::unique_ptr<ComprehensiveModelManagerSystem> system_;
    bool initialized_;
    std::mutex instanceMutex_;
};

} // namespace cogniware
