#include "model_config_manager.h"
#include <spdlog/spdlog.h>
#include <fstream>
#include <nlohmann/json.hpp>
#include <chrono>
#include <thread>

namespace cogniware {

ModelConfigManager& ModelConfigManager::getInstance() {
    static ModelConfigManager instance;
    return instance;
}

bool ModelConfigManager::initialize() {
    std::lock_guard<std::mutex> lock(mutex_);
    running_ = true;
    return true;
}

void ModelConfigManager::shutdown() {
    std::lock_guard<std::mutex> lock(mutex_);
    running_ = false;
    
    // Clean up resources
    for (const auto& [modelId, model] : models_) {
        model->shutdown();
    }
    models_.clear();
    configs_.clear();
    factories_.clear();
    modelStatus_.clear();
}

bool ModelConfigManager::loadConfig(const std::string& configPath) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    try {
        std::ifstream file(configPath);
        if (!file.is_open()) {
            spdlog::error("Failed to open config file: {}", configPath);
            return false;
        }
        
        nlohmann::json json;
        file >> json;
        
        for (const auto& [modelId, configJson] : json.items()) {
            ModelConfig config;
            config.modelId = modelId;
            config.modelType = configJson["modelType"];
            config.modelPath = configJson["modelPath"];
            config.enableGpu = configJson["enableGpu"];
            config.maxBatchSize = configJson["maxBatchSize"];
            config.memoryLimit = configJson["memoryLimit"];
            config.quantizationType = configJson["quantizationType"];
            config.enableDynamicBatching = configJson["enableDynamicBatching"];
            
            // Load parameters
            for (const auto& [key, value] : configJson["parameters"].items()) {
                config.parameters[key] = value;
            }
            
            // Load resource limits
            for (const auto& [key, value] : configJson["resourceLimits"].items()) {
                config.resourceLimits[key] = value;
            }
            
            if (!validateConfig(config)) {
                spdlog::error("Invalid config for model: {}", modelId);
                continue;
            }
            
            configs_[modelId] = config;
        }
        
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Error loading config: {}", e.what());
        return false;
    }
}

bool ModelConfigManager::saveConfig(const std::string& configPath) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    try {
        nlohmann::json json;
        
        for (const auto& [modelId, config] : configs_) {
            nlohmann::json configJson;
            configJson["modelType"] = config.modelType;
            configJson["modelPath"] = config.modelPath;
            configJson["enableGpu"] = config.enableGpu;
            configJson["maxBatchSize"] = config.maxBatchSize;
            configJson["memoryLimit"] = config.memoryLimit;
            configJson["quantizationType"] = config.quantizationType;
            configJson["enableDynamicBatching"] = config.enableDynamicBatching;
            
            // Save parameters
            for (const auto& [key, value] : config.parameters) {
                configJson["parameters"][key] = value;
            }
            
            // Save resource limits
            for (const auto& [key, value] : config.resourceLimits) {
                configJson["resourceLimits"][key] = value;
            }
            
            json[modelId] = configJson;
        }
        
        std::ofstream file(configPath);
        if (!file.is_open()) {
            spdlog::error("Failed to open config file for writing: {}", configPath);
            return false;
        }
        
        file << json.dump(4);
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Error saving config: {}", e.what());
        return false;
    }
}

bool ModelConfigManager::updateConfig(const ModelConfig& config) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!validateConfig(config)) {
        return false;
    }
    
    configs_[config.modelId] = config;
    
    // Update existing model if it exists
    auto it = models_.find(config.modelId);
    if (it != models_.end()) {
        return it->second->updateConfig(config);
    }
    
    return true;
}

bool ModelConfigManager::removeConfig(const std::string& modelId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Destroy model if it exists
    auto modelIt = models_.find(modelId);
    if (modelIt != models_.end()) {
        modelIt->second->shutdown();
        models_.erase(modelIt);
    }
    
    // Remove config
    configs_.erase(modelId);
    modelStatus_.erase(modelId);
    
    return true;
}

ModelConfig ModelConfigManager::getConfig(const std::string& modelId) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = configs_.find(modelId);
    if (it == configs_.end()) {
        return ModelConfig();
    }
    
    return it->second;
}

bool ModelConfigManager::registerModelType(const std::string& type,
                                         std::function<std::shared_ptr<IModelInterface>(const ModelConfig&)> factory) {
    std::lock_guard<std::mutex> lock(mutex_);
    factories_[type] = factory;
    return true;
}

bool ModelConfigManager::unregisterModelType(const std::string& type) {
    std::lock_guard<std::mutex> lock(mutex_);
    return factories_.erase(type) > 0;
}

std::vector<std::string> ModelConfigManager::getRegisteredModelTypes() const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    std::vector<std::string> types;
    types.reserve(factories_.size());
    
    for (const auto& [type, _] : factories_) {
        types.push_back(type);
    }
    
    return types;
}

std::shared_ptr<IModelInterface> ModelConfigManager::createModel(const std::string& modelId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto configIt = configs_.find(modelId);
    if (configIt == configs_.end()) {
        spdlog::error("No config found for model: {}", modelId);
        return nullptr;
    }
    
    auto factoryIt = factories_.find(configIt->second.modelType);
    if (factoryIt == factories_.end()) {
        spdlog::error("No factory registered for model type: {}", configIt->second.modelType);
        return nullptr;
    }
    
    auto model = factoryIt->second(configIt->second);
    if (!model) {
        spdlog::error("Failed to create model: {}", modelId);
        return nullptr;
    }
    
    if (!model->initialize(configIt->second)) {
        spdlog::error("Failed to initialize model: {}", modelId);
        return nullptr;
    }
    
    models_[modelId] = model;
    modelStatus_[modelId] = ModelStatus();
    modelStatus_[modelId].modelId = modelId;
    modelStatus_[modelId].isLoaded = true;
    
    return model;
}

bool ModelConfigManager::destroyModel(const std::string& modelId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = models_.find(modelId);
    if (it == models_.end()) {
        return false;
    }
    
    it->second->shutdown();
    models_.erase(it);
    modelStatus_.erase(modelId);
    
    return true;
}

std::shared_ptr<IModelInterface> ModelConfigManager::getModel(const std::string& modelId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = models_.find(modelId);
    if (it == models_.end()) {
        return nullptr;
    }
    
    return it->second;
}

std::vector<std::string> ModelConfigManager::getActiveModelIds() const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    std::vector<std::string> ids;
    ids.reserve(models_.size());
    
    for (const auto& [id, _] : models_) {
        ids.push_back(id);
    }
    
    return ids;
}

bool ModelConfigManager::allocateResources(const std::string& modelId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = models_.find(modelId);
    if (it == models_.end()) {
        return false;
    }
    
    return it->second->allocateResources();
}

bool ModelConfigManager::releaseResources(const std::string& modelId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = models_.find(modelId);
    if (it == models_.end()) {
        return false;
    }
    
    return it->second->releaseResources();
}

bool ModelConfigManager::optimizeResources(const std::string& modelId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = models_.find(modelId);
    if (it == models_.end()) {
        return false;
    }
    
    return it->second->optimizeResources();
}

std::map<std::string, float> ModelConfigManager::getResourceUtilization(const std::string& modelId) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = modelStatus_.find(modelId);
    if (it == modelStatus_.end()) {
        return std::map<std::string, float>();
    }
    
    return it->second.resourceUtilization;
}

void ModelConfigManager::enableMonitoring(bool enable) {
    std::lock_guard<std::mutex> lock(mutex_);
    monitoringEnabled_ = enable;
}

void ModelConfigManager::setStatusCallback(std::function<void(const std::string&, const ModelStatus&)> callback) {
    std::lock_guard<std::mutex> lock(mutex_);
    statusCallback_ = callback;
}

void ModelConfigManager::printStats() const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    spdlog::info("Model Config Manager Stats:");
    spdlog::info("  Registered Model Types: {}", factories_.size());
    spdlog::info("  Active Models: {}", models_.size());
    spdlog::info("  Stored Configs: {}", configs_.size());
    
    for (const auto& [modelId, status] : modelStatus_) {
        spdlog::info("  Model {}: Loaded={}, Training={}, Memory={:.2f}%, GPU={:.2f}%",
                    modelId, status.isLoaded, status.isTraining,
                    status.memoryUsage * 100.0f, status.gpuUtilization * 100.0f);
    }
}

bool ModelConfigManager::validateConfig(const ModelConfig& config) const {
    if (config.modelId.empty() || config.modelType.empty() || config.modelPath.empty()) {
        return false;
    }
    
    if (config.maxBatchSize <= 0 || config.memoryLimit <= 0.0f) {
        return false;
    }
    
    return true;
}

bool ModelConfigManager::checkResourceAvailability(const ModelConfig& config) const {
    // Implement resource availability check logic
    return true;
}

void ModelConfigManager::updateResourceMetrics(const std::string& modelId) {
    auto it = models_.find(modelId);
    if (it == models_.end()) {
        return;
    }
    
    auto status = it->second->getStatus();
    modelStatus_[modelId] = status;
    
    if (statusCallback_) {
        statusCallback_(modelId, status);
    }
}

void ModelConfigManager::cleanupUnusedModels() {
    auto now = std::chrono::system_clock::now();
    
    for (auto it = models_.begin(); it != models_.end();) {
        auto status = it->second->getStatus();
        if (!status.isLoaded && !status.isTraining) {
            it->second->shutdown();
            it = models_.erase(it);
            modelStatus_.erase(it->first);
        } else {
            ++it;
        }
    }
}

} // namespace cogniware 