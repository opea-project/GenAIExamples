#include "inference/inference_sharing.h"
#include <algorithm>
#include <numeric>
#include <cmath>
#include <sstream>
#include <queue>
#include <set>

namespace cogniware {
namespace inference {

// AdvancedInferenceSharing Implementation
class AdvancedInferenceSharing::Impl {
public:
    explicit Impl(const InferenceSharingConfig& cfg)
        : config(cfg)
        , total_knowledge_transfers(0)
        , total_cross_validations(0)
        , total_collaborative_inferences(0)
        , successful_transfers(0)
        , successful_validations(0)
        , successful_collaborations(0)
        , knowledge_cache_hits(0)
        , knowledge_cache_misses(0) {}

    InferenceSharingConfig config;
    std::unordered_map<std::string, std::vector<std::shared_ptr<Knowledge>>> knowledge_cache;
    std::unordered_map<std::string, std::vector<InferenceResult>> inference_history;
    std::unordered_map<std::string, float> model_contribution_weights;
    mutable std::mutex cache_mutex;
    mutable std::mutex history_mutex;
    mutable std::mutex weights_mutex;

    // Metrics
    size_t total_knowledge_transfers;
    size_t total_cross_validations;
    size_t total_collaborative_inferences;
    size_t successful_transfers;
    size_t successful_validations;
    size_t successful_collaborations;
    size_t knowledge_cache_hits;
    size_t knowledge_cache_misses;
    std::vector<double> transfer_times;
    std::vector<double> validation_times;
    std::vector<double> collaboration_times;

    float calculateEmbeddingSimilarity(
        const std::vector<float>& emb1,
        const std::vector<float>& emb2) {
        if (emb1.size() != emb2.size() || emb1.empty()) {
            return 0.0f;
        }

        float dot_product = 0.0f;
        float norm1 = 0.0f;
        float norm2 = 0.0f;

        for (size_t i = 0; i < emb1.size(); ++i) {
            dot_product += emb1[i] * emb2[i];
            norm1 += emb1[i] * emb1[i];
            norm2 += emb2[i] * emb2[i];
        }

        if (norm1 == 0.0f || norm2 == 0.0f) {
            return 0.0f;
        }

        return dot_product / (std::sqrt(norm1) * std::sqrt(norm2));
    }

    float calculateTextSimilarity(const std::string& text1, const std::string& text2) {
        if (text1.empty() || text2.empty()) {
            return 0.0f;
        }

        // Simple word-based similarity (can be enhanced with proper NLP)
        std::set<std::string> words1, words2;
        std::istringstream iss1(text1), iss2(text2);
        std::string word;

        while (iss1 >> word) words1.insert(word);
        while (iss2 >> word) words2.insert(word);

        size_t intersection = 0;
        for (const auto& w : words1) {
            if (words2.count(w)) {
                ++intersection;
            }
        }

        size_t union_size = words1.size() + words2.size() - intersection;
        return union_size > 0 ? static_cast<float>(intersection) / union_size : 0.0f;
    }
};

AdvancedInferenceSharing::AdvancedInferenceSharing(const InferenceSharingConfig& config)
    : pImpl(std::make_unique<Impl>(config)) {}

AdvancedInferenceSharing::~AdvancedInferenceSharing() = default;

KnowledgeTransferResult AdvancedInferenceSharing::transferKnowledge(
    const std::string& source_model,
    const std::string& target_model,
    const std::vector<std::string>& domains) {
    
    auto start_time = std::chrono::high_resolution_clock::now();
    
    KnowledgeTransferResult result;
    result.source_model = source_model;
    result.target_model = target_model;
    result.transfer_count = 0;
    result.transfer_quality = 0.0f;
    result.success = false;

    if (!pImpl->config.enable_knowledge_transfer) {
        result.transfer_time = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::high_resolution_clock::now() - start_time);
        return result;
    }

    std::lock_guard<std::mutex> lock(pImpl->cache_mutex);
    
    std::vector<float> quality_scores;

    for (const auto& domain : domains) {
        auto it = pImpl->knowledge_cache.find(domain);
        if (it != pImpl->knowledge_cache.end()) {
            for (const auto& knowledge : it->second) {
                if (knowledge->source_model == source_model &&
                    knowledge->confidence >= pImpl->config.confidence_threshold) {
                    
                    // Transfer knowledge by creating a copy for target model
                    auto transferred = std::make_shared<Knowledge>(*knowledge);
                    transferred->source_model = target_model;
                    transferred->metadata["original_source"] = source_model;
                    transferred->metadata["transfer_time"] = 
                        std::to_string(std::chrono::system_clock::now().time_since_epoch().count());
                    
                    result.transferred_knowledge.push_back(transferred);
                    result.transfer_count++;
                    quality_scores.push_back(knowledge->confidence);
                }
            }
        }
    }

    if (!quality_scores.empty()) {
        result.transfer_quality = std::accumulate(quality_scores.begin(), quality_scores.end(), 0.0f) 
                                 / quality_scores.size();
        result.success = true;
        pImpl->successful_transfers++;
    }

    pImpl->total_knowledge_transfers++;
    
    auto end_time = std::chrono::high_resolution_clock::now();
    result.transfer_time = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
    pImpl->transfer_times.push_back(result.transfer_time.count());

    return result;
}

bool AdvancedInferenceSharing::cacheKnowledge(const std::shared_ptr<Knowledge>& knowledge) {
    if (!knowledge) {
        return false;
    }

    std::lock_guard<std::mutex> lock(pImpl->cache_mutex);
    
    auto& domain_cache = pImpl->knowledge_cache[knowledge->domain];
    
    // Check cache size limit
    size_t total_size = 0;
    for (const auto& [domain, cache] : pImpl->knowledge_cache) {
        total_size += cache.size() * sizeof(Knowledge);
    }

    if (total_size >= pImpl->config.max_knowledge_cache_size) {
        // Simple LRU: remove oldest knowledge from largest cache
        auto largest = std::max_element(
            pImpl->knowledge_cache.begin(),
            pImpl->knowledge_cache.end(),
            [](const auto& a, const auto& b) {
                return a.second.size() < b.second.size();
            });
        
        if (largest != pImpl->knowledge_cache.end() && !largest->second.empty()) {
            largest->second.erase(largest->second.begin());
        }
    }

    domain_cache.push_back(knowledge);
    return true;
}

std::vector<std::shared_ptr<Knowledge>> AdvancedInferenceSharing::retrieveKnowledge(
    const std::string& domain,
    size_t max_results) {
    
    std::lock_guard<std::mutex> lock(pImpl->cache_mutex);
    
    auto it = pImpl->knowledge_cache.find(domain);
    if (it == pImpl->knowledge_cache.end()) {
        pImpl->knowledge_cache_misses++;
        return {};
    }

    pImpl->knowledge_cache_hits++;
    
    std::vector<std::shared_ptr<Knowledge>> results;
    auto& cache = it->second;
    
    // Sort by confidence and usage
    std::vector<std::shared_ptr<Knowledge>> sorted_cache = cache;
    std::sort(sorted_cache.begin(), sorted_cache.end(),
        [](const auto& a, const auto& b) {
            return (a->confidence * std::log(a->usage_count + 1)) >
                   (b->confidence * std::log(b->usage_count + 1));
        });

    size_t count = std::min(max_results, sorted_cache.size());
    for (size_t i = 0; i < count; ++i) {
        results.push_back(sorted_cache[i]);
        sorted_cache[i]->usage_count++;
    }

    return results;
}

void AdvancedInferenceSharing::clearKnowledgeCache() {
    std::lock_guard<std::mutex> lock(pImpl->cache_mutex);
    pImpl->knowledge_cache.clear();
}

size_t AdvancedInferenceSharing::getKnowledgeCacheSize() const {
    std::lock_guard<std::mutex> lock(pImpl->cache_mutex);
    size_t total = 0;
    for (const auto& [domain, cache] : pImpl->knowledge_cache) {
        total += cache.size();
    }
    return total;
}

CrossValidationResult AdvancedInferenceSharing::validateInference(
    const std::string& input,
    const std::vector<std::string>& model_ids) {
    
    auto start_time = std::chrono::high_resolution_clock::now();
    
    CrossValidationResult result;
    result.validation_passed = false;

    if (!pImpl->config.enable_cross_validation ||
        model_ids.size() < pImpl->config.min_validation_models) {
        result.validation_time = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::high_resolution_clock::now() - start_time);
        return result;
    }

    result.model_ids = model_ids;

    // Simulate inference results (in real implementation, would call actual models)
    for (const auto& model_id : model_ids) {
        InferenceResult inference;
        inference.model_id = model_id;
        inference.input = input;
        inference.output = "Model " + model_id + " output for: " + input;
        inference.confidence = 0.8f + (std::rand() % 20) / 100.0f;
        inference.latency = std::chrono::milliseconds(50 + std::rand() % 100);
        
        result.individual_results.push_back(inference);
    }

    // Calculate agreement scores
    for (size_t i = 0; i < result.individual_results.size(); ++i) {
        for (size_t j = i + 1; j < result.individual_results.size(); ++j) {
            float agreement = calculateAgreementScore(
                result.individual_results[i],
                result.individual_results[j]);
            result.agreement_scores.push_back(agreement);
        }
    }

    // Determine consensus
    result.consensus_output = determineConsensus(result.individual_results);
    
    // Calculate consensus confidence
    if (!result.agreement_scores.empty()) {
        result.consensus_confidence = std::accumulate(
            result.agreement_scores.begin(),
            result.agreement_scores.end(), 0.0f) / result.agreement_scores.size();
        
        result.validation_passed = result.consensus_confidence >= pImpl->config.confidence_threshold;
    }

    if (result.validation_passed) {
        pImpl->successful_validations++;
    }

    pImpl->total_cross_validations++;
    
    auto end_time = std::chrono::high_resolution_clock::now();
    result.validation_time = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
    pImpl->validation_times.push_back(result.validation_time.count());

    return result;
}

float AdvancedInferenceSharing::calculateAgreementScore(
    const InferenceResult& result1,
    const InferenceResult& result2) {
    
    return pImpl->calculateTextSimilarity(result1.output, result2.output);
}

std::string AdvancedInferenceSharing::determineConsensus(
    const std::vector<InferenceResult>& results) {
    
    if (results.empty()) {
        return "";
    }

    // Simple voting mechanism: find most similar outputs
    std::vector<float> similarity_scores(results.size(), 0.0f);
    
    for (size_t i = 0; i < results.size(); ++i) {
        for (size_t j = 0; j < results.size(); ++j) {
            if (i != j) {
                similarity_scores[i] += pImpl->calculateTextSimilarity(
                    results[i].output, results[j].output);
            }
        }
        similarity_scores[i] *= results[i].confidence;
    }

    size_t best_idx = std::distance(similarity_scores.begin(),
        std::max_element(similarity_scores.begin(), similarity_scores.end()));
    
    return results[best_idx].output;
}

CollaborativeInferenceResult AdvancedInferenceSharing::collaborativeInference(
    const std::string& input,
    const std::vector<std::string>& model_ids,
    const std::string& collaboration_strategy) {
    
    auto start_time = std::chrono::high_resolution_clock::now();
    
    CollaborativeInferenceResult result;
    result.participating_models = model_ids;
    result.success = false;

    if (!pImpl->config.enable_collaborative_inference || model_ids.empty()) {
        result.total_time = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::high_resolution_clock::now() - start_time);
        return result;
    }

    // Get contribution weights
    std::lock_guard<std::mutex> lock(pImpl->weights_mutex);
    
    for (const auto& model_id : model_ids) {
        InferenceResult partial;
        partial.model_id = model_id;
        partial.input = input;
        partial.output = "Partial output from " + model_id;
        partial.confidence = 0.75f + (std::rand() % 25) / 100.0f;
        partial.latency = std::chrono::milliseconds(30 + std::rand() % 70);
        
        result.partial_results.push_back(partial);

        // Get or initialize weight
        auto it = pImpl->model_contribution_weights.find(model_id);
        float weight = (it != pImpl->model_contribution_weights.end()) ? it->second : 1.0f;
        result.contribution_weights[model_id] = weight;
    }

    // Combine results based on strategy
    if (collaboration_strategy == "weighted_average") {
        // Weighted combination of outputs
        float total_weight = 0.0f;
        std::string combined;
        
        for (const auto& partial : result.partial_results) {
            float weight = result.contribution_weights[partial.model_id] * partial.confidence;
            total_weight += weight;
            combined += partial.output + " [w=" + std::to_string(weight) + "] ";
        }
        
        result.final_output = combined;
        result.combined_confidence = total_weight / result.partial_results.size();
        
    } else if (collaboration_strategy == "ensemble") {
        // Ensemble approach: combine all outputs
        std::string ensemble_output;
        float total_confidence = 0.0f;
        
        for (const auto& partial : result.partial_results) {
            ensemble_output += partial.output + " | ";
            total_confidence += partial.confidence;
        }
        
        result.final_output = ensemble_output;
        result.combined_confidence = total_confidence / result.partial_results.size();
        
    } else {
        // Default: highest confidence wins
        auto best = std::max_element(result.partial_results.begin(),
            result.partial_results.end(),
            [](const auto& a, const auto& b) {
                return a.confidence < b.confidence;
            });
        
        result.final_output = best->output;
        result.combined_confidence = best->confidence;
    }

    result.success = true;
    pImpl->successful_collaborations++;
    pImpl->total_collaborative_inferences++;
    
    auto end_time = std::chrono::high_resolution_clock::now();
    result.total_time = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
    pImpl->collaboration_times.push_back(result.total_time.count());

    return result;
}

void AdvancedInferenceSharing::updateContributionWeights(
    const std::string& model_id,
    float performance_score) {
    
    std::lock_guard<std::mutex> lock(pImpl->weights_mutex);
    
    // Exponential moving average
    auto it = pImpl->model_contribution_weights.find(model_id);
    if (it != pImpl->model_contribution_weights.end()) {
        it->second = 0.7f * it->second + 0.3f * performance_score;
    } else {
        pImpl->model_contribution_weights[model_id] = performance_score;
    }
}

float AdvancedInferenceSharing::getModelContributionWeight(const std::string& model_id) const {
    std::lock_guard<std::mutex> lock(pImpl->weights_mutex);
    auto it = pImpl->model_contribution_weights.find(model_id);
    return (it != pImpl->model_contribution_weights.end()) ? it->second : 1.0f;
}

void AdvancedInferenceSharing::recordInference(const InferenceResult& result) {
    std::lock_guard<std::mutex> lock(pImpl->history_mutex);
    
    auto& history = pImpl->inference_history[result.model_id];
    history.push_back(result);
    
    // Limit history size
    if (history.size() > pImpl->config.max_inference_history) {
        history.erase(history.begin());
    }
}

std::vector<InferenceResult> AdvancedInferenceSharing::getInferenceHistory(
    const std::string& model_id,
    size_t max_results) const {
    
    std::lock_guard<std::mutex> lock(pImpl->history_mutex);
    
    auto it = pImpl->inference_history.find(model_id);
    if (it == pImpl->inference_history.end()) {
        return {};
    }

    const auto& history = it->second;
    size_t count = std::min(max_results, history.size());
    
    return std::vector<InferenceResult>(
        history.end() - count, history.end());
}

void AdvancedInferenceSharing::clearInferenceHistory() {
    std::lock_guard<std::mutex> lock(pImpl->history_mutex);
    pImpl->inference_history.clear();
}

void AdvancedInferenceSharing::updateConfig(const InferenceSharingConfig& config) {
    pImpl->config = config;
}

InferenceSharingConfig AdvancedInferenceSharing::getConfig() const {
    return pImpl->config;
}

AdvancedInferenceSharing::PerformanceMetrics 
AdvancedInferenceSharing::getPerformanceMetrics() const {
    PerformanceMetrics metrics;
    
    metrics.total_knowledge_transfers = pImpl->total_knowledge_transfers;
    metrics.total_cross_validations = pImpl->total_cross_validations;
    metrics.total_collaborative_inferences = pImpl->total_collaborative_inferences;
    metrics.successful_transfers = pImpl->successful_transfers;
    metrics.successful_validations = pImpl->successful_validations;
    metrics.successful_collaborations = pImpl->successful_collaborations;
    metrics.knowledge_cache_hits = pImpl->knowledge_cache_hits;
    metrics.knowledge_cache_misses = pImpl->knowledge_cache_misses;
    
    metrics.avg_transfer_time_ms = pImpl->transfer_times.empty() ? 0.0 :
        std::accumulate(pImpl->transfer_times.begin(), pImpl->transfer_times.end(), 0.0) 
        / pImpl->transfer_times.size();
    
    metrics.avg_validation_time_ms = pImpl->validation_times.empty() ? 0.0 :
        std::accumulate(pImpl->validation_times.begin(), pImpl->validation_times.end(), 0.0)
        / pImpl->validation_times.size();
    
    metrics.avg_collaboration_time_ms = pImpl->collaboration_times.empty() ? 0.0 :
        std::accumulate(pImpl->collaboration_times.begin(), pImpl->collaboration_times.end(), 0.0)
        / pImpl->collaboration_times.size();
    
    size_t total_cache_accesses = metrics.knowledge_cache_hits + metrics.knowledge_cache_misses;
    metrics.cache_hit_rate = total_cache_accesses > 0 ?
        static_cast<double>(metrics.knowledge_cache_hits) / total_cache_accesses : 0.0;
    
    return metrics;
}

void AdvancedInferenceSharing::resetMetrics() {
    pImpl->total_knowledge_transfers = 0;
    pImpl->total_cross_validations = 0;
    pImpl->total_collaborative_inferences = 0;
    pImpl->successful_transfers = 0;
    pImpl->successful_validations = 0;
    pImpl->successful_collaborations = 0;
    pImpl->knowledge_cache_hits = 0;
    pImpl->knowledge_cache_misses = 0;
    pImpl->transfer_times.clear();
    pImpl->validation_times.clear();
    pImpl->collaboration_times.clear();
}

} // namespace inference
} // namespace cogniware

