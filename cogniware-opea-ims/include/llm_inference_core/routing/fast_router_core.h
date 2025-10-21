#pragma once

#include <memory>
#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>

namespace cogniware {

struct ModelProfile {
    std::string modelId;
    std::vector<float> embedding;
    std::vector<std::string> keywords;
    float confidence;
    size_t memoryUsage;
    float averageLatency;
};

class FastRouterCore {
public:
    static FastRouterCore& getInstance();

    // Delete copy constructor and assignment operator
    FastRouterCore(const FastRouterCore&) = delete;
    FastRouterCore& operator=(const FastRouterCore&) = delete;

    // Initialization
    bool initialize(const std::vector<ModelProfile>& profiles);
    
    // Model profile management
    bool addModelProfile(const ModelProfile& profile);
    bool removeModelProfile(const std::string& modelId);
    bool updateModelProfile(const ModelProfile& profile);
    
    // Routing
    std::string routeQuery(const std::string& query);
    
    // Statistics
    size_t getTotalQueries() const;
    float getAverageConfidence() const;
    std::vector<std::string> getMostUsedModels(size_t count = 5) const;
    
    // Error handling
    const char* getLastError() const;
    void clearLastError();

private:
    FastRouterCore();
    ~FastRouterCore();

    // Helper methods
    std::vector<float> computeQueryEmbedding(const std::string& query);
    float computeSimilarity(const std::vector<float>& queryEmbedding,
                          const std::vector<float>& modelEmbedding);
    bool matchKeywords(const std::string& query,
                      const std::vector<std::string>& keywords);
    
    // Model profiles
    std::unordered_map<std::string, ModelProfile> profiles_;
    
    // Statistics
    size_t totalQueries_;
    float totalConfidence_;
    std::unordered_map<std::string, size_t> modelUsage_;
    
    // Thread safety
    mutable std::mutex mutex_;
    
    // Error handling
    std::string lastError_;
};

} // namespace cogniware 