#pragma once

#include "model_selector.h"
#include <string>
#include <vector>
#include <map>
#include <memory>
#include <functional>

namespace cogniware {

// Configuration validation result
struct ConfigurationValidation {
    bool isValid;
    std::vector<std::string> errors;
    std::vector<std::string> warnings;
    std::map<std::string, std::string> suggestions;
};

// Model configuration template
struct ModelConfigTemplate {
    std::string templateId;
    std::string name;
    std::string description;
    ModelType modelType;
    std::vector<SupportedTask> supportedTasks;
    ModelConfiguration defaultConfig;
    std::map<std::string, std::string> requirements;
    std::vector<std::string> compatibleModels;
};

// Model configurator interface
class ModelConfigurator {
public:
    virtual ~ModelConfigurator() = default;

    // Configuration management
    virtual bool configureModel(const ModelMetadata& model, 
                              const ModelConfiguration& config) = 0;
    virtual ModelConfiguration getModelConfiguration(const std::string& modelId) = 0;
    virtual bool updateModelConfiguration(const std::string& modelId, 
                                        const ModelConfiguration& config) = 0;
    virtual bool deleteModelConfiguration(const std::string& modelId) = 0;

    // Configuration validation
    virtual ConfigurationValidation validateConfiguration(const ModelConfiguration& config) = 0;
    virtual ConfigurationValidation validateModelCompatibility(const ModelMetadata& model, 
                                                             const ModelConfiguration& config) = 0;

    // Template management
    virtual std::vector<ModelConfigTemplate> getAvailableTemplates() = 0;
    virtual ModelConfigTemplate getTemplate(const std::string& templateId) = 0;
    virtual ModelConfiguration createConfigurationFromTemplate(const std::string& templateId, 
                                                             const std::string& modelId) = 0;
};

// Advanced model configurator
class AdvancedModelConfigurator : public ModelConfigurator {
public:
    AdvancedModelConfigurator();
    ~AdvancedModelConfigurator() override = default;

    // Configuration management
    bool configureModel(const ModelMetadata& model, 
                       const ModelConfiguration& config) override;
    ModelConfiguration getModelConfiguration(const std::string& modelId) override;
    bool updateModelConfiguration(const std::string& modelId, 
                                 const ModelConfiguration& config) override;
    bool deleteModelConfiguration(const std::string& modelId) override;

    // Configuration validation
    ConfigurationValidation validateConfiguration(const ModelConfiguration& config) override;
    ConfigurationValidation validateModelCompatibility(const ModelMetadata& model, 
                                                      const ModelConfiguration& config) override;

    // Template management
    std::vector<ModelConfigTemplate> getAvailableTemplates() override;
    ModelConfigTemplate getTemplate(const std::string& templateId) override;
    ModelConfiguration createConfigurationFromTemplate(const std::string& templateId, 
                                                      const std::string& modelId) override;

    // Advanced configuration methods
    ModelConfiguration autoConfigureModel(const ModelMetadata& model);
    std::vector<SupportedTask> identifySupportedTasks(const ModelMetadata& model);
    ModelType determineOptimalModelType(const ModelMetadata& model, 
                                       const std::vector<SupportedTask>& tasks);
    std::map<std::string, std::string> generateOptimalParameters(const ModelMetadata& model, 
                                                               ModelType modelType);
    std::string generateSystemPrompt(ModelType modelType, 
                                   const std::vector<SupportedTask>& tasks);
    std::string generateUserPrompt(ModelType modelType, 
                                 const std::vector<SupportedTask>& tasks);
    std::string generateAssistantPrompt(ModelType modelType, 
                                      const std::vector<SupportedTask>& tasks);

    // Configuration optimization
    ModelConfiguration optimizeForTask(const ModelConfiguration& config, 
                                     SupportedTask task);
    ModelConfiguration optimizeForPerformance(const ModelConfiguration& config);
    ModelConfiguration optimizeForMemory(const ModelConfiguration& config);
    ModelConfiguration optimizeForQuality(const ModelConfiguration& config);

    // Configuration analysis
    std::map<std::string, std::string> analyzeConfiguration(const ModelConfiguration& config);
    std::vector<std::string> getConfigurationRecommendations(const ModelConfiguration& config);
    bool isConfigurationOptimal(const ModelConfiguration& config);

private:
    std::map<std::string, ModelConfiguration> configurations_;
    std::vector<ModelConfigTemplate> templates_;
    std::string configPath_;

    // Helper methods
    bool saveConfiguration(const std::string& modelId, const ModelConfiguration& config);
    bool loadConfiguration(const std::string& modelId, ModelConfiguration& config);
    void initializeTemplates();
    ModelConfigTemplate createTemplate(ModelType modelType, 
                                     const std::vector<SupportedTask>& tasks);
    std::vector<std::string> validateModelRequirements(const ModelMetadata& model, 
                                                      const ModelConfiguration& config);
    std::vector<std::string> validateParameterRanges(const ModelConfiguration& config);
    std::vector<std::string> validateTaskCompatibility(const ModelMetadata& model, 
                                                      const ModelConfiguration& config);
};

// Model configuration manager
class ModelConfigurationManager {
public:
    static ModelConfigurationManager& getInstance();

    // Configuration management
    bool configureModel(const ModelMetadata& model, 
                       const ModelConfiguration& config);
    ModelConfiguration getModelConfiguration(const std::string& modelId);
    bool updateModelConfiguration(const std::string& modelId, 
                                 const ModelConfiguration& config);
    bool deleteModelConfiguration(const std::string& modelId);
    std::vector<std::string> getConfiguredModels();

    // Auto-configuration
    ModelConfiguration autoConfigureModel(const ModelMetadata& model);
    bool autoConfigureAllModels();

    // Configuration validation
    ConfigurationValidation validateConfiguration(const ModelConfiguration& config);
    ConfigurationValidation validateModelCompatibility(const ModelMetadata& model, 
                                                      const ModelConfiguration& config);

    // Template management
    std::vector<ModelConfigTemplate> getAvailableTemplates();
    ModelConfigTemplate getTemplate(const std::string& templateId);
    ModelConfiguration createConfigurationFromTemplate(const std::string& templateId, 
                                                      const std::string& modelId);

    // Configuration optimization
    ModelConfiguration optimizeForTask(const std::string& modelId, SupportedTask task);
    ModelConfiguration optimizeForPerformance(const std::string& modelId);
    ModelConfiguration optimizeForMemory(const std::string& modelId);
    ModelConfiguration optimizeForQuality(const std::string& modelId);

    // Configuration analysis
    std::map<std::string, std::string> analyzeConfiguration(const std::string& modelId);
    std::vector<std::string> getConfigurationRecommendations(const std::string& modelId);
    bool isConfigurationOptimal(const std::string& modelId);

    // Configuration utilities
    void setConfigurationPath(const std::string& path);
    std::string getConfigurationPath() const;
    bool exportConfiguration(const std::string& modelId, const std::string& filePath);
    bool importConfiguration(const std::string& filePath);
    void cleanup();

private:
    ModelConfigurationManager();
    ~ModelConfigurationManager();

    std::unique_ptr<AdvancedModelConfigurator> configurator_;
    std::string configurationPath_;
    std::mutex managerMutex_;
};

} // namespace cogniware
