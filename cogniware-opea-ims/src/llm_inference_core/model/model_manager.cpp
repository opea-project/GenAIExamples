#include "llm_inference_core/model/model_manager.h"
#include <algorithm>
#include <filesystem>
#include <fstream>
#include <spdlog/spdlog.h>

namespace cogniware {

ModelManager& ModelManager::getInstance() {
    static ModelManager instance;
    return instance;
}

ModelManager::ModelManager()
    : totalMemoryUsage_(0)
    , availableMemory_(0) {
    // TODO: Initialize available memory based on system resources
    availableMemory_ = 16ULL * 1024 * 1024 * 1024;  // 16GB default
}

ModelManager::~ModelManager() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Unload all models
    for (const auto& pair : modelConfigs_) {
        cleanupModelResources(pair.first);
    }
    
    modelConfigs_.clear();
    modelStats_.clear();
}

void ModelManager::initialize() {
    // Initialize with default memory allocation
    availableMemory_ = 16ULL * 1024 * 1024 * 1024;  // 16GB default
    totalMemoryUsage_ = 0;
    
    spdlog::info("Model manager initialized with {} MB available memory", 
                 availableMemory_ / (1024 * 1024));
}

bool ModelManager::loadModel(const ModelConfig& config) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    try {
        // Validate configuration
        if (!validateModelConfig(config)) {
            return false;
        }
        
        // Check if model is already loaded
        if (isModelLoaded(config.modelId)) {
            lastError_ = "Model already loaded: " + config.modelId;
            return false;
        }
        
        // Check if we can load the model
        if (!canLoadModel(config)) {
            lastError_ = "Insufficient resources to load model: " + config.modelId;
            return false;
        }
        
        // Check if model file exists
        if (!std::filesystem::exists(config.modelPath)) {
            lastError_ = "Model file not found: " + config.modelPath;
            return false;
        }
        
        // Store model configuration
        modelConfigs_[config.modelId] = config;
        
        // Initialize model statistics
        ModelStats stats;
        stats.totalInferences = 0;
        stats.totalTokens = 0;
        stats.averageLatency = 0.0f;
        stats.peakMemoryUsage = 0;
        stats.currentMemoryUsage = estimateModelMemoryUsage(config);
        modelStats_[config.modelId] = stats;
        
        // Update total memory usage
        totalMemoryUsage_ += stats.currentMemoryUsage;
        
        spdlog::info("Model {} loaded successfully from {}", config.modelId, config.modelPath);
        return true;
        
    } catch (const std::exception& e) {
        lastError_ = "Failed to load model: " + std::string(e.what());
        spdlog::error("Failed to load model {}: {}", config.modelId, e.what());
        return false;
    }
}

size_t ModelManager::estimateModelMemoryUsage(const ModelConfig& config) {
    // Rough estimation of model memory usage
    // This is a simplified calculation - in practice, this would be more sophisticated
    
    size_t baseMemory = 100 * 1024 * 1024;  // 100MB base
    size_t batchMemory = config.maxBatchSize * config.maxSequenceLength * 4;  // 4 bytes per token
    size_t modelMemory = config.maxSequenceLength * 4;  // Model weights
    
    return baseMemory + batchMemory + modelMemory;
}

bool ModelManager::unloadModel(const std::string& modelId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!isModelLoaded(modelId)) {
        lastError_ = "Model not loaded: " + modelId;
        return false;
    }
    
    // Cleanup resources
    cleanupModelResources(modelId);
    
    // Remove model data
    modelConfigs_.erase(modelId);
    modelStats_.erase(modelId);
    
    return true;
}

bool ModelManager::isModelLoaded(const std::string& modelId) const {
    std::lock_guard<std::mutex> lock(mutex_);
    return modelConfigs_.find(modelId) != modelConfigs_.end();
}

bool ModelManager::updateModelConfig(const ModelConfig& config) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!isModelLoaded(config.modelId)) {
        lastError_ = "Model not loaded: " + config.modelId;
        return false;
    }
    
    if (!validateModelConfig(config)) {
        return false;
    }
    
    // Update configuration
    modelConfigs_[config.modelId] = config;
    
    return true;
}

ModelConfig ModelManager::getModelConfig(const std::string& modelId) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = modelConfigs_.find(modelId);
    if (it == modelConfigs_.end()) {
        return ModelConfig{};
    }
    
    return it->second;
}

ModelStats ModelManager::getModelStats(const std::string& modelId) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = modelStats_.find(modelId);
    if (it == modelStats_.end()) {
        return ModelStats{};
    }
    
    return it->second;
}

void ModelManager::updateModelStats(const std::string& modelId,
                                  size_t tokens,
                                  float latency,
                                  size_t memoryUsage) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = modelStats_.find(modelId);
    if (it == modelStats_.end()) {
        return;
    }
    
    auto& stats = it->second;
    
    // Update statistics
    stats.totalInferences++;
    stats.totalTokens += tokens;
    
    // Update average latency using exponential moving average
    const float alpha = 0.1f;  // Smoothing factor
    stats.averageLatency = (1.0f - alpha) * stats.averageLatency + alpha * latency;
    
    // Update memory usage
    stats.currentMemoryUsage = memoryUsage;
    stats.peakMemoryUsage = std::max(stats.peakMemoryUsage, memoryUsage);
    
    // Update total memory usage
    totalMemoryUsage_ = 0;
    for (const auto& pair : modelStats_) {
        totalMemoryUsage_ += pair.second.currentMemoryUsage;
    }
}

size_t ModelManager::getTotalMemoryUsage() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return totalMemoryUsage_;
}

size_t ModelManager::getAvailableMemory() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return availableMemory_;
}

bool ModelManager::canLoadModel(const ModelConfig& config) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Estimate memory requirements
    size_t estimatedMemory = config.maxBatchSize * config.maxSequenceLength * 4;  // Rough estimate
    
    // Check if we have enough memory
    return (totalMemoryUsage_ + estimatedMemory) <= availableMemory_;
}

const char* ModelManager::getLastError() const {
    return lastError_.c_str();
}

void ModelManager::clearLastError() {
    lastError_.clear();
}

bool ModelManager::validateModelConfig(const ModelConfig& config) {
    if (config.modelId.empty()) {
        lastError_ = "Invalid model ID";
        return false;
    }
    
    if (config.modelPath.empty()) {
        lastError_ = "Invalid model path";
        return false;
    }
    
    if (!std::filesystem::exists(config.modelPath)) {
        lastError_ = "Model file not found: " + config.modelPath;
        return false;
    }
    
    if (config.modelType.empty()) {
        lastError_ = "Invalid model type";
        return false;
    }
    
    if (config.maxBatchSize == 0) {
        lastError_ = "Invalid batch size";
        return false;
    }
    
    if (config.maxSequenceLength == 0) {
        lastError_ = "Invalid sequence length";
        return false;
    }
    
    return true;
}

bool ModelManager::checkModelCompatibility(const ModelConfig& config) {
    // TODO: Implement model compatibility checks
    // This is a placeholder implementation
    
    // Check if model type is supported
    const std::vector<std::string> supportedTypes = {
        "gpt", "bert", "t5", "llama"
    };
    
    if (std::find(supportedTypes.begin(), supportedTypes.end(), config.modelType) == supportedTypes.end()) {
        lastError_ = "Unsupported model type: " + config.modelType;
        return false;
    }
    
    return true;
}

void ModelManager::cleanupModelResources(const std::string& modelId) {
    auto it = modelStats_.find(modelId);
    if (it != modelStats_.end()) {
        // Update total memory usage
        totalMemoryUsage_ -= it->second.currentMemoryUsage;
    }
}

} // namespace cogniware 