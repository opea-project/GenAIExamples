#include "llm_inference_core/routing/fast_router_core.h"
#include <algorithm>
#include <cmath>
#include <sstream>
#include <unordered_set>

namespace cogniware {

FastRouterCore& FastRouterCore::getInstance() {
    static FastRouterCore instance;
    return instance;
}

FastRouterCore::FastRouterCore()
    : totalQueries_(0)
    , totalConfidence_(0.0f) {
}

FastRouterCore::~FastRouterCore() {
    std::lock_guard<std::mutex> lock(mutex_);
    profiles_.clear();
    modelUsage_.clear();
}

bool FastRouterCore::initialize(const std::vector<ModelProfile>& profiles) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    profiles_.clear();
    modelUsage_.clear();
    totalQueries_ = 0;
    totalConfidence_ = 0.0f;
    
    for (const auto& profile : profiles) {
        if (!addModelProfile(profile)) {
            return false;
        }
    }
    
    return true;
}

bool FastRouterCore::addModelProfile(const ModelProfile& profile) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (profiles_.find(profile.modelId) != profiles_.end()) {
        lastError_ = "Model profile already exists: " + profile.modelId;
        return false;
    }
    
    if (profile.embedding.empty()) {
        lastError_ = "Invalid model embedding";
        return false;
    }
    
    profiles_[profile.modelId] = profile;
    modelUsage_[profile.modelId] = 0;
    
    return true;
}

bool FastRouterCore::removeModelProfile(const std::string& modelId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (profiles_.find(modelId) == profiles_.end()) {
        lastError_ = "Model profile not found: " + modelId;
        return false;
    }
    
    profiles_.erase(modelId);
    modelUsage_.erase(modelId);
    
    return true;
}

bool FastRouterCore::updateModelProfile(const ModelProfile& profile) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (profiles_.find(profile.modelId) == profiles_.end()) {
        lastError_ = "Model profile not found: " + profile.modelId;
        return false;
    }
    
    if (profile.embedding.empty()) {
        lastError_ = "Invalid model embedding";
        return false;
    }
    
    profiles_[profile.modelId] = profile;
    return true;
}

std::string FastRouterCore::routeQuery(const std::string& query) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (profiles_.empty()) {
        lastError_ = "No model profiles available";
        return "";
    }
    
    // Compute query embedding
    std::vector<float> queryEmbedding = computeQueryEmbedding(query);
    if (queryEmbedding.empty()) {
        lastError_ = "Failed to compute query embedding";
        return "";
    }
    
    // Find best matching model
    std::string bestModelId;
    float bestScore = -1.0f;
    
    for (const auto& pair : profiles_) {
        const auto& profile = pair.second;
        
        // Compute similarity score
        float similarity = computeSimilarity(queryEmbedding, profile.embedding);
        
        // Check keyword matches
        bool hasKeywordMatch = matchKeywords(query, profile.keywords);
        
        // Combine scores
        float score = similarity;
        if (hasKeywordMatch) {
            score *= 1.2f;  // Boost score for keyword matches
        }
        
        // Apply confidence factor
        score *= profile.confidence;
        
        // Consider resource usage
        score *= (1.0f - (profile.memoryUsage / (1024.0f * 1024.0f * 1024.0f)));  // Normalize memory usage
        score *= (1.0f - (profile.averageLatency / 1000.0f));  // Normalize latency
        
        if (score > bestScore) {
            bestScore = score;
            bestModelId = profile.modelId;
        }
    }
    
    if (bestModelId.empty()) {
        lastError_ = "No suitable model found";
        return "";
    }
    
    // Update statistics
    totalQueries_++;
    totalConfidence_ += bestScore;
    modelUsage_[bestModelId]++;
    
    return bestModelId;
}

size_t FastRouterCore::getTotalQueries() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return totalQueries_;
}

float FastRouterCore::getAverageConfidence() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return totalQueries_ > 0 ? totalConfidence_ / totalQueries_ : 0.0f;
}

std::vector<std::string> FastRouterCore::getMostUsedModels(size_t count) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Create vector of model usage pairs
    std::vector<std::pair<std::string, size_t>> usagePairs;
    usagePairs.reserve(modelUsage_.size());
    
    for (const auto& pair : modelUsage_) {
        usagePairs.emplace_back(pair.first, pair.second);
    }
    
    // Sort by usage count
    std::sort(usagePairs.begin(), usagePairs.end(),
        [](const auto& a, const auto& b) {
            return a.second > b.second;
        });
    
    // Get top N models
    std::vector<std::string> result;
    result.reserve(std::min(count, usagePairs.size()));
    
    for (size_t i = 0; i < std::min(count, usagePairs.size()); ++i) {
        result.push_back(usagePairs[i].first);
    }
    
    return result;
}

const char* FastRouterCore::getLastError() const {
    return lastError_.c_str();
}

void FastRouterCore::clearLastError() {
    lastError_.clear();
}

std::vector<float> FastRouterCore::computeQueryEmbedding(const std::string& query) {
    // TODO: Implement proper embedding computation
    // This is a simple placeholder implementation
    
    std::vector<float> embedding(128, 0.0f);  // 128-dimensional embedding
    
    // Simple character-based embedding
    for (char c : query) {
        size_t index = static_cast<size_t>(c) % 128;
        embedding[index] += 1.0f;
    }
    
    // Normalize
    float norm = 0.0f;
    for (float value : embedding) {
        norm += value * value;
    }
    norm = std::sqrt(norm);
    
    if (norm > 0.0f) {
        for (float& value : embedding) {
            value /= norm;
        }
    }
    
    return embedding;
}

float FastRouterCore::computeSimilarity(const std::vector<float>& queryEmbedding,
                                      const std::vector<float>& modelEmbedding) {
    if (queryEmbedding.size() != modelEmbedding.size()) {
        return 0.0f;
    }
    
    // Compute cosine similarity
    float dotProduct = 0.0f;
    float queryNorm = 0.0f;
    float modelNorm = 0.0f;
    
    for (size_t i = 0; i < queryEmbedding.size(); ++i) {
        dotProduct += queryEmbedding[i] * modelEmbedding[i];
        queryNorm += queryEmbedding[i] * queryEmbedding[i];
        modelNorm += modelEmbedding[i] * modelEmbedding[i];
    }
    
    queryNorm = std::sqrt(queryNorm);
    modelNorm = std::sqrt(modelNorm);
    
    if (queryNorm == 0.0f || modelNorm == 0.0f) {
        return 0.0f;
    }
    
    return dotProduct / (queryNorm * modelNorm);
}

bool FastRouterCore::matchKeywords(const std::string& query,
                                 const std::vector<std::string>& keywords) {
    if (keywords.empty()) {
        return false;
    }
    
    // Convert query to lowercase
    std::string lowercaseQuery = query;
    std::transform(lowercaseQuery.begin(), lowercaseQuery.end(),
                  lowercaseQuery.begin(), ::tolower);
    
    // Check for keyword matches
    for (const auto& keyword : keywords) {
        std::string lowercaseKeyword = keyword;
        std::transform(lowercaseKeyword.begin(), lowercaseKeyword.end(),
                      lowercaseKeyword.begin(), ::tolower);
        
        if (lowercaseQuery.find(lowercaseKeyword) != std::string::npos) {
            return true;
        }
    }
    
    return false;
}

} // namespace cogniware 