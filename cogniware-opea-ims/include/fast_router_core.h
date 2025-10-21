#ifndef FAST_ROUTER_CORE_H
#define FAST_ROUTER_CORE_H

#include <string>
#include <vector>
#include <unordered_map>
#include <memory>
#include <cuda_runtime.h>
#include "gpu_memory_manager.h"

namespace cogniware {

struct ModelProfile {
    std::string model_id;
    std::vector<std::string> specialties;
    std::vector<std::string> roles;
    float base_confidence;
};

struct RoutingDecision {
    std::string model_id;
    float confidence;
    std::string reasoning;
    bool needs_system2;
};

class FastRouterCore {
public:
    static FastRouterCore& getInstance();

    // Initialization
    bool initialize(const std::vector<ModelProfile>& profiles);
    bool loadEmbeddings(const std::string& path);

    // Routing
    RoutingDecision routeQuery(
        const std::string& query,
        const std::vector<std::string>& context = {}
    );

    // Profile management
    bool addModelProfile(const ModelProfile& profile);
    bool removeModelProfile(const std::string& model_id);
    bool updateModelProfile(const ModelProfile& profile);

    // Statistics
    size_t getTotalQueries() const;
    float getAverageConfidence() const;
    std::vector<std::string> getMostUsedModels() const;

private:
    FastRouterCore();
    ~FastRouterCore();

    // Prevent copying
    FastRouterCore(const FastRouterCore&) = delete;
    FastRouterCore& operator=(const FastRouterCore&) = delete;

    // Internal routing logic
    bool computeQueryEmbedding(const std::string& query, float* embedding);
    bool computeSimilarity(const float* query_embedding, const float* model_embedding, float& similarity);
    bool matchKeywords(const std::string& query, const std::vector<std::string>& keywords, float& score);

    // Internal state
    std::unordered_map<std::string, ModelProfile> model_profiles_;
    float* model_embeddings_;
    size_t embedding_dim_;
    size_t total_queries_;
    float total_confidence_;

    // CUDA resources
    cudaStream_t stream_;
    float* d_query_embedding_;
    float* d_model_embedding_;
    float* d_similarity_;
};

} // namespace cogniware

#endif // FAST_ROUTER_CORE_H 