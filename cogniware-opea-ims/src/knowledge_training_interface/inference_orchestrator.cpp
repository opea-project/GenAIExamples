#include "inference_orchestrator.h"
#include <spdlog/spdlog.h>
#include <algorithm>
#include <chrono>
#include <numeric>
#include <cmath>

namespace cogniware {

InferenceOrchestrator& InferenceOrchestrator::getInstance() {
    static InferenceOrchestrator instance;
    return instance;
}

bool InferenceOrchestrator::initialize(const InferenceConfig& config) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    config_ = config;
    running_ = true;
    
    // Start inference thread
    inferenceThread_ = std::thread(&InferenceOrchestrator::inferenceLoop, this);
    
    return true;
}

void InferenceOrchestrator::shutdown() {
    {
        std::lock_guard<std::mutex> lock(mutex_);
        running_ = false;
    }
    
    if (inferenceThread_.joinable()) {
        inferenceThread_.join();
    }
    
    // Clean up resources
    results_.clear();
    sharedContext_.clear();
    sharedEmbeddings_.clear();
    callbacks_.clear();
}

bool InferenceOrchestrator::setConfig(const InferenceConfig& config) {
    std::lock_guard<std::mutex> lock(mutex_);
    config_ = config;
    return true;
}

bool InferenceOrchestrator::setKnowledgeSharingConfig(const KnowledgeSharingConfig& config) {
    std::lock_guard<std::mutex> lock(mutex_);
    sharingConfig_ = config;
    return true;
}

bool InferenceOrchestrator::startInference(const std::string& query, 
                                         std::function<void(const CollatedResult&)> callback) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Generate unique inference ID
    std::string inferenceId = std::to_string(std::chrono::system_clock::now().time_since_epoch().count());
    
    // Initialize result structure
    CollatedResult result;
    result.isComplete = false;
    result.overallConfidence = 0.0f;
    
    // Store callback
    callbacks_[inferenceId] = callback;
    
    // Add to inference queue
    inferenceQueue_.push(inferenceId);
    
    return true;
}

bool InferenceOrchestrator::stopInference(const std::string& inferenceId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = results_.find(inferenceId);
    if (it == results_.end()) {
        return false;
    }
    
    // Mark as complete
    it->second.isComplete = true;
    
    // Remove from queue if present
    std::queue<std::string> tempQueue;
    while (!inferenceQueue_.empty()) {
        std::string id = inferenceQueue_.front();
        inferenceQueue_.pop();
        if (id != inferenceId) {
            tempQueue.push(id);
        }
    }
    inferenceQueue_ = std::move(tempQueue);
    
    return true;
}

bool InferenceOrchestrator::pauseInference(const std::string& inferenceId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = results_.find(inferenceId);
    if (it == results_.end()) {
        return false;
    }
    
    // Mark as paused
    it->second.isComplete = false;
    
    return true;
}

bool InferenceOrchestrator::resumeInference(const std::string& inferenceId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = results_.find(inferenceId);
    if (it == results_.end()) {
        return false;
    }
    
    // Add back to queue
    inferenceQueue_.push(inferenceId);
    
    return true;
}

bool InferenceOrchestrator::shareKnowledge(const std::string& sourceModelId,
                                         const std::string& targetModelId,
                                         const std::vector<float>& embeddings) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!sharingConfig_.enableEmbeddingSharing) {
        return false;
    }
    
    // Store embeddings for sharing
    sharedEmbeddings_[sourceModelId] = embeddings;
    
    return true;
}

bool InferenceOrchestrator::updateSharedContext(const std::string& modelId,
                                              const std::vector<float>& context) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!sharingConfig_.enableResponseSharing) {
        return false;
    }
    
    // Update shared context
    sharedContext_[modelId] = context;
    
    // Trim context if exceeds maximum size
    if (context.size() > sharingConfig_.maxSharedContext) {
        sharedContext_[modelId].resize(sharingConfig_.maxSharedContext);
    }
    
    return true;
}

bool InferenceOrchestrator::validateSharedKnowledge(const std::string& modelId,
                                                  const std::vector<float>& knowledge) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!config_.enableCrossModelValidation) {
        return true;
    }
    
    // Compare with existing knowledge
    for (const auto& [otherModelId, otherKnowledge] : sharedEmbeddings_) {
        if (otherModelId == modelId) continue;
        
        // Calculate similarity
        float similarity = calculateCosineSimilarity(knowledge, otherKnowledge);
        
        if (similarity < sharingConfig_.similarityThreshold) {
            spdlog::warn("Knowledge validation failed for model {}: similarity {} < threshold {}",
                        modelId, similarity, sharingConfig_.similarityThreshold);
            return false;
        }
    }
    
    return true;
}

CollatedResult InferenceOrchestrator::getCollatedResult(const std::string& inferenceId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = results_.find(inferenceId);
    if (it == results_.end()) {
        return CollatedResult();
    }
    
    return it->second;
}

std::vector<InferenceResult> InferenceOrchestrator::getIndividualResults(const std::string& inferenceId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = results_.find(inferenceId);
    if (it == results_.end()) {
        return std::vector<InferenceResult>();
    }
    
    return it->second.individualResults;
}

bool InferenceOrchestrator::isInferenceComplete(const std::string& inferenceId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = results_.find(inferenceId);
    if (it == results_.end()) {
        return false;
    }
    
    return it->second.isComplete;
}

void InferenceOrchestrator::enableMonitoring(bool enable) {
    std::lock_guard<std::mutex> lock(mutex_);
    monitoringEnabled_ = enable;
}

void InferenceOrchestrator::setStatusCallback(std::function<void(const std::string&, float)> callback) {
    std::lock_guard<std::mutex> lock(mutex_);
    statusCallback_ = callback;
}

void InferenceOrchestrator::printStats() const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    spdlog::info("Inference Orchestrator Stats:");
    spdlog::info("  Active Inferences: {}", results_.size());
    spdlog::info("  Queued Inferences: {}", inferenceQueue_.size());
    spdlog::info("  Shared Contexts: {}", sharedContext_.size());
    spdlog::info("  Shared Embeddings: {}", sharedEmbeddings_.size());
}

void InferenceOrchestrator::inferenceLoop() {
    while (running_) {
        {
            std::lock_guard<std::mutex> lock(mutex_);
            processInferenceQueue();
            updateSharedKnowledge();
            cleanupCompletedInferences();
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
}

void InferenceOrchestrator::processInferenceQueue() {
    while (!inferenceQueue_.empty()) {
        std::string inferenceId = inferenceQueue_.front();
        inferenceQueue_.pop();
        
        // Process inference
        collateResults(inferenceId);
        validateResults(inferenceId);
        aggregateMetadata(inferenceId);
        
        // Check if complete
        auto it = results_.find(inferenceId);
        if (it != results_.end() && it->second.isComplete) {
            // Call callback
            auto callbackIt = callbacks_.find(inferenceId);
            if (callbackIt != callbacks_.end()) {
                callbackIt->second(it->second);
                callbacks_.erase(callbackIt);
            }
        }
    }
}

void InferenceOrchestrator::collateResults(const std::string& inferenceId) {
    auto it = results_.find(inferenceId);
    if (it == results_.end()) {
        return;
    }
    
    // Aggregate responses from individual models
    std::string finalResponse;
    float totalConfidence = 0.0f;
    int validResponses = 0;
    
    for (const auto& result : it->second.individualResults) {
        if (result.confidence >= config_.confidenceThreshold) {
            if (!finalResponse.empty()) {
                finalResponse += "\n";
            }
            finalResponse += result.response;
            totalConfidence += result.confidence;
            validResponses++;
        }
    }
    
    if (validResponses > 0) {
        it->second.finalResponse = finalResponse;
        it->second.overallConfidence = totalConfidence / validResponses;
    }
}

void InferenceOrchestrator::validateResults(const std::string& inferenceId) {
    if (!config_.enableCrossModelValidation) {
        return;
    }
    
    auto it = results_.find(inferenceId);
    if (it == results_.end()) {
        return;
    }
    
    // Validate results against each other
    for (size_t i = 0; i < it->second.individualResults.size(); ++i) {
        for (size_t j = i + 1; j < it->second.individualResults.size(); ++j) {
            float similarity = calculateCosineSimilarity(
                it->second.individualResults[i].embeddings,
                it->second.individualResults[j].embeddings
            );
            
            if (similarity < sharingConfig_.similarityThreshold) {
                spdlog::warn("Result validation failed: similarity {} < threshold {}",
                            similarity, sharingConfig_.similarityThreshold);
            }
        }
    }
}

void InferenceOrchestrator::aggregateMetadata(const std::string& inferenceId) {
    auto it = results_.find(inferenceId);
    if (it == results_.end()) {
        return;
    }
    
    // Aggregate metadata from individual results
    std::map<std::string, float> aggregatedMetadata;
    int count = 0;
    
    for (const auto& result : it->second.individualResults) {
        for (const auto& [key, value] : result.metadata) {
            aggregatedMetadata[key] += value;
        }
        count++;
    }
    
    // Calculate averages
    for (auto& [key, value] : aggregatedMetadata) {
        value /= count;
    }
    
    it->second.aggregatedMetadata = std::move(aggregatedMetadata);
}

void InferenceOrchestrator::updateSharedKnowledge() {
    if (!sharingConfig_.enableEmbeddingSharing) {
        return;
    }
    
    // Update shared knowledge based on recent results
    for (const auto& [inferenceId, result] : results_) {
        if (!result.isComplete) continue;
        
        for (const auto& individualResult : result.individualResults) {
            if (individualResult.confidence >= config_.confidenceThreshold) {
                sharedEmbeddings_[individualResult.modelId] = individualResult.embeddings;
            }
        }
    }
}

void InferenceOrchestrator::cleanupCompletedInferences() {
    // Remove completed inferences older than timeout
    auto now = std::chrono::system_clock::now();
    for (auto it = results_.begin(); it != results_.end();) {
        if (it->second.isComplete) {
            it = results_.erase(it);
        } else {
            ++it;
        }
    }
}

float InferenceOrchestrator::calculateCosineSimilarity(const std::vector<float>& a,
                                                     const std::vector<float>& b) {
    if (a.size() != b.size() || a.empty()) {
        return 0.0f;
    }
    
    float dotProduct = 0.0f;
    float normA = 0.0f;
    float normB = 0.0f;
    
    for (size_t i = 0; i < a.size(); ++i) {
        dotProduct += a[i] * b[i];
        normA += a[i] * a[i];
        normB += b[i] * b[i];
    }
    
    if (normA == 0.0f || normB == 0.0f) {
        return 0.0f;
    }
    
    return dotProduct / (std::sqrt(normA) * std::sqrt(normB));
}

} // namespace cogniware 