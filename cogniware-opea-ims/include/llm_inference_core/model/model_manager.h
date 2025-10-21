#pragma once

#include <memory>
#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>

namespace cogniware {

struct ModelConfig {
    std::string modelId;
    std::string modelPath;
    std::string modelType;
    size_t maxBatchSize;
    size_t maxSequenceLength;
    bool useHalfPrecision;
    bool useQuantization;
    std::vector<std::string> supportedTasks;
};

struct ModelStats {
    size_t totalInferences;
    size_t totalTokens;
    float averageLatency;
    size_t peakMemoryUsage;
    size_t currentMemoryUsage;
};

class ModelManager {
public:
    static ModelManager& getInstance();

    // Delete copy constructor and assignment operator
    ModelManager(const ModelManager&) = delete;
    ModelManager& operator=(const ModelManager&) = delete;

    // Model lifecycle
    bool loadModel(const ModelConfig& config);
    bool unloadModel(const std::string& modelId);
    bool isModelLoaded(const std::string& modelId) const;
    
    // Model configuration
    bool updateModelConfig(const ModelConfig& config);
    ModelConfig getModelConfig(const std::string& modelId) const;
    
    // Model statistics
    ModelStats getModelStats(const std::string& modelId) const;
    void updateModelStats(const std::string& modelId,
                         size_t tokens,
                         float latency,
                         size_t memoryUsage);
    
    // Resource management
    size_t getTotalMemoryUsage() const;
    size_t getAvailableMemory() const;
    bool canLoadModel(const ModelConfig& config) const;
    
    // Error handling
    const char* getLastError() const;
    void clearLastError();

private:
    ModelManager();
    ~ModelManager();

    // Helper methods
    bool validateModelConfig(const ModelConfig& config);
    bool checkModelCompatibility(const ModelConfig& config);
    void cleanupModelResources(const std::string& modelId);
    size_t estimateModelMemoryUsage(const ModelConfig& config);
    
    // Model storage
    std::unordered_map<std::string, ModelConfig> modelConfigs_;
    std::unordered_map<std::string, ModelStats> modelStats_;
    
    // Resource tracking
    size_t totalMemoryUsage_;
    size_t availableMemory_;
    
    // Thread safety
    mutable std::mutex mutex_;
    
    // Error handling
    std::string lastError_;
};

} // namespace cogniware 