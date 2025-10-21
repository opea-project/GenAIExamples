#ifndef INFERENCE_SHARING_H
#define INFERENCE_SHARING_H

#include <string>
#include <vector>
#include <memory>
#include <unordered_map>
#include <mutex>
#include <functional>
#include <chrono>

namespace cogniware {
namespace inference {

// Forward declarations
struct KnowledgeTransferResult;
struct CrossValidationResult;
struct CollaborativeInferenceResult;

// Inference sharing configuration
struct InferenceSharingConfig {
    size_t max_knowledge_cache_size;
    size_t max_inference_history;
    bool enable_cross_validation;
    bool enable_knowledge_transfer;
    bool enable_collaborative_inference;
    float confidence_threshold;
    size_t min_validation_models;
    size_t max_validation_models;
    bool use_gpu_acceleration;
    size_t gpu_device_id;
    
    InferenceSharingConfig()
        : max_knowledge_cache_size(1024 * 1024 * 1024)  // 1GB
        , max_inference_history(10000)
        , enable_cross_validation(true)
        , enable_knowledge_transfer(true)
        , enable_collaborative_inference(true)
        , confidence_threshold(0.75f)
        , min_validation_models(2)
        , max_validation_models(4)
        , use_gpu_acceleration(true)
        , gpu_device_id(0) {}
};

// Knowledge representation
struct Knowledge {
    std::string id;
    std::string source_model;
    std::string domain;
    std::vector<float> embedding;
    std::unordered_map<std::string, std::string> metadata;
    float confidence;
    std::chrono::system_clock::time_point timestamp;
    size_t usage_count;
};

// Inference result with metadata
struct InferenceResult {
    std::string model_id;
    std::string input;
    std::string output;
    std::vector<float> logits;
    float confidence;
    std::chrono::milliseconds latency;
    std::unordered_map<std::string, std::string> metadata;
};

// Knowledge transfer result
struct KnowledgeTransferResult {
    std::string source_model;
    std::string target_model;
    std::vector<std::shared_ptr<Knowledge>> transferred_knowledge;
    size_t transfer_count;
    float transfer_quality;
    std::chrono::milliseconds transfer_time;
    bool success;
};

// Cross-validation result
struct CrossValidationResult {
    std::vector<std::string> model_ids;
    std::vector<InferenceResult> individual_results;
    std::string consensus_output;
    float consensus_confidence;
    std::vector<float> agreement_scores;
    bool validation_passed;
    std::chrono::milliseconds validation_time;
};

// Collaborative inference result
struct CollaborativeInferenceResult {
    std::vector<std::string> participating_models;
    std::vector<InferenceResult> partial_results;
    std::string final_output;
    float combined_confidence;
    std::unordered_map<std::string, float> contribution_weights;
    std::chrono::milliseconds total_time;
    bool success;
};

// Advanced inference sharing system
class AdvancedInferenceSharing {
public:
    explicit AdvancedInferenceSharing(const InferenceSharingConfig& config);
    ~AdvancedInferenceSharing();

    // Knowledge transfer operations
    KnowledgeTransferResult transferKnowledge(
        const std::string& source_model,
        const std::string& target_model,
        const std::vector<std::string>& domains);
    
    bool cacheKnowledge(const std::shared_ptr<Knowledge>& knowledge);
    std::vector<std::shared_ptr<Knowledge>> retrieveKnowledge(
        const std::string& domain,
        size_t max_results);
    
    void clearKnowledgeCache();
    size_t getKnowledgeCacheSize() const;

    // Cross-validation operations
    CrossValidationResult validateInference(
        const std::string& input,
        const std::vector<std::string>& model_ids);
    
    float calculateAgreementScore(
        const InferenceResult& result1,
        const InferenceResult& result2);
    
    std::string determineConsensus(
        const std::vector<InferenceResult>& results);

    // Collaborative inference operations
    CollaborativeInferenceResult collaborativeInference(
        const std::string& input,
        const std::vector<std::string>& model_ids,
        const std::string& collaboration_strategy);
    
    void updateContributionWeights(
        const std::string& model_id,
        float performance_score);
    
    float getModelContributionWeight(const std::string& model_id) const;

    // Inference history management
    void recordInference(const InferenceResult& result);
    std::vector<InferenceResult> getInferenceHistory(
        const std::string& model_id,
        size_t max_results) const;
    
    void clearInferenceHistory();

    // Configuration management
    void updateConfig(const InferenceSharingConfig& config);
    InferenceSharingConfig getConfig() const;

    // Performance metrics
    struct PerformanceMetrics {
        size_t total_knowledge_transfers;
        size_t total_cross_validations;
        size_t total_collaborative_inferences;
        size_t successful_transfers;
        size_t successful_validations;
        size_t successful_collaborations;
        double avg_transfer_time_ms;
        double avg_validation_time_ms;
        double avg_collaboration_time_ms;
        size_t knowledge_cache_hits;
        size_t knowledge_cache_misses;
        double cache_hit_rate;
    };

    PerformanceMetrics getPerformanceMetrics() const;
    void resetMetrics();

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

// Inference sharing manager for system-wide coordination
class InferenceSharingManager {
public:
    static InferenceSharingManager& getInstance();

    // Sharing system management
    bool createSharingSystem(
        const std::string& system_id,
        const InferenceSharingConfig& config);
    
    bool destroySharingSystem(const std::string& system_id);
    
    std::shared_ptr<AdvancedInferenceSharing> getSharingSystem(
        const std::string& system_id);

    // Global knowledge operations
    bool shareKnowledgeGlobally(const std::shared_ptr<Knowledge>& knowledge);
    std::vector<std::shared_ptr<Knowledge>> queryGlobalKnowledge(
        const std::string& domain,
        size_t max_results);

    // System-wide validation
    CrossValidationResult validateAcrossSystems(
        const std::string& input,
        const std::vector<std::string>& system_ids);

    // Statistics
    size_t getActiveSharingSystemCount() const;
    size_t getTotalKnowledgeCount() const;
    std::vector<std::string> getActiveSharingSystemIds() const;

private:
    InferenceSharingManager();
    ~InferenceSharingManager();
    InferenceSharingManager(const InferenceSharingManager&) = delete;
    InferenceSharingManager& operator=(const InferenceSharingManager&) = delete;

    class ManagerImpl;
    std::unique_ptr<ManagerImpl> pImpl;
};

// Global inference sharing system for overall coordination
class GlobalInferenceSharingSystem {
public:
    static GlobalInferenceSharingSystem& getInstance();

    // System initialization
    bool initialize(const InferenceSharingConfig& default_config);
    bool shutdown();
    bool isInitialized() const;

    // Knowledge graph operations
    bool buildKnowledgeGraph(const std::vector<std::shared_ptr<Knowledge>>& knowledge);
    std::vector<std::shared_ptr<Knowledge>> queryKnowledgeGraph(
        const std::string& query,
        size_t max_results);
    
    void updateKnowledgeRelations(
        const std::string& knowledge_id1,
        const std::string& knowledge_id2,
        float relation_strength);

    // Multi-model coordination
    CollaborativeInferenceResult coordinateMultiModelInference(
        const std::string& input,
        const std::vector<std::string>& model_ids,
        const std::string& strategy);

    // System-wide metrics
    struct SystemMetrics {
        size_t total_sharing_systems;
        size_t total_knowledge_entries;
        size_t total_inferences;
        size_t total_validations;
        size_t total_collaborations;
        double avg_validation_accuracy;
        double avg_collaboration_quality;
        size_t knowledge_graph_nodes;
        size_t knowledge_graph_edges;
    };

    SystemMetrics getSystemMetrics() const;

private:
    GlobalInferenceSharingSystem();
    ~GlobalInferenceSharingSystem();
    GlobalInferenceSharingSystem(const GlobalInferenceSharingSystem&) = delete;
    GlobalInferenceSharingSystem& operator=(const GlobalInferenceSharingSystem&) = delete;

    class GlobalImpl;
    std::unique_ptr<GlobalImpl> pImpl;
};

} // namespace inference
} // namespace cogniware

#endif // INFERENCE_SHARING_H

