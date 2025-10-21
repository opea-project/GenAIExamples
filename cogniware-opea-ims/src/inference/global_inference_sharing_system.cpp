#include "inference/inference_sharing.h"
#include <algorithm>
#include <queue>

namespace cogniware {
namespace inference {

// GlobalInferenceSharingSystem Implementation
class GlobalInferenceSharingSystem::GlobalImpl {
public:
    bool initialized;
    InferenceSharingConfig default_config;
    
    // Knowledge graph representation
    struct KnowledgeNode {
        std::shared_ptr<Knowledge> knowledge;
        std::unordered_map<std::string, float> relations;  // Related knowledge ID -> strength
    };
    
    std::unordered_map<std::string, KnowledgeNode> knowledge_graph;
    mutable std::mutex graph_mutex;
    
    // System metrics
    size_t total_inferences;
    size_t total_validations;
    size_t total_collaborations;
    std::vector<float> validation_accuracies;
    std::vector<float> collaboration_qualities;
    
    GlobalImpl() 
        : initialized(false)
        , total_inferences(0)
        , total_validations(0)
        , total_collaborations(0) {}
};

GlobalInferenceSharingSystem::GlobalInferenceSharingSystem()
    : pImpl(std::make_unique<GlobalImpl>()) {}

GlobalInferenceSharingSystem::~GlobalInferenceSharingSystem() = default;

GlobalInferenceSharingSystem& GlobalInferenceSharingSystem::getInstance() {
    static GlobalInferenceSharingSystem instance;
    return instance;
}

bool GlobalInferenceSharingSystem::initialize(const InferenceSharingConfig& default_config) {
    if (pImpl->initialized) {
        return false;
    }

    pImpl->default_config = default_config;
    pImpl->initialized = true;
    
    return true;
}

bool GlobalInferenceSharingSystem::shutdown() {
    if (!pImpl->initialized) {
        return false;
    }

    std::lock_guard<std::mutex> lock(pImpl->graph_mutex);
    pImpl->knowledge_graph.clear();
    pImpl->initialized = false;
    
    return true;
}

bool GlobalInferenceSharingSystem::isInitialized() const {
    return pImpl->initialized;
}

bool GlobalInferenceSharingSystem::buildKnowledgeGraph(
    const std::vector<std::shared_ptr<Knowledge>>& knowledge) {
    
    if (!pImpl->initialized) {
        return false;
    }

    std::lock_guard<std::mutex> lock(pImpl->graph_mutex);
    
    // Add all knowledge as nodes
    for (const auto& k : knowledge) {
        if (k) {
            GlobalImpl::KnowledgeNode node;
            node.knowledge = k;
            pImpl->knowledge_graph[k->id] = node;
        }
    }

    // Build relations based on domain similarity and embedding similarity
    for (auto& [id1, node1] : pImpl->knowledge_graph) {
        for (auto& [id2, node2] : pImpl->knowledge_graph) {
            if (id1 >= id2) continue;  // Avoid duplicates and self-relations

            float relation_strength = 0.0f;

            // Domain similarity
            if (node1.knowledge->domain == node2.knowledge->domain) {
                relation_strength += 0.3f;
            }

            // Embedding similarity (if available)
            if (!node1.knowledge->embedding.empty() && 
                !node2.knowledge->embedding.empty() &&
                node1.knowledge->embedding.size() == node2.knowledge->embedding.size()) {
                
                // Simple cosine similarity
                float dot = 0.0f, norm1 = 0.0f, norm2 = 0.0f;
                for (size_t i = 0; i < node1.knowledge->embedding.size(); ++i) {
                    dot += node1.knowledge->embedding[i] * node2.knowledge->embedding[i];
                    norm1 += node1.knowledge->embedding[i] * node1.knowledge->embedding[i];
                    norm2 += node2.knowledge->embedding[i] * node2.knowledge->embedding[i];
                }
                
                if (norm1 > 0.0f && norm2 > 0.0f) {
                    float similarity = dot / (std::sqrt(norm1) * std::sqrt(norm2));
                    relation_strength += 0.7f * std::max(0.0f, similarity);
                }
            }

            // Add bidirectional relations if strength is significant
            if (relation_strength > 0.2f) {
                node1.relations[id2] = relation_strength;
                node2.relations[id1] = relation_strength;
            }
        }
    }

    return true;
}

std::vector<std::shared_ptr<Knowledge>> GlobalInferenceSharingSystem::queryKnowledgeGraph(
    const std::string& query,
    size_t max_results) {
    
    if (!pImpl->initialized) {
        return {};
    }

    std::lock_guard<std::mutex> lock(pImpl->graph_mutex);
    
    // Simple query matching based on domain
    std::vector<std::pair<std::shared_ptr<Knowledge>, float>> scored_knowledge;
    
    for (const auto& [id, node] : pImpl->knowledge_graph) {
        float score = 0.0f;
        
        // Domain match
        if (node.knowledge->domain.find(query) != std::string::npos) {
            score += 0.5f;
        }
        
        // Confidence contribution
        score += 0.3f * node.knowledge->confidence;
        
        // Usage count contribution
        score += 0.2f * std::min(1.0f, node.knowledge->usage_count / 100.0f);
        
        scored_knowledge.push_back({node.knowledge, score});
    }

    // Sort by score
    std::sort(scored_knowledge.begin(), scored_knowledge.end(),
        [](const auto& a, const auto& b) {
            return a.second > b.second;
        });

    // Return top results
    std::vector<std::shared_ptr<Knowledge>> results;
    size_t count = std::min(max_results, scored_knowledge.size());
    for (size_t i = 0; i < count; ++i) {
        results.push_back(scored_knowledge[i].first);
    }

    return results;
}

void GlobalInferenceSharingSystem::updateKnowledgeRelations(
    const std::string& knowledge_id1,
    const std::string& knowledge_id2,
    float relation_strength) {
    
    if (!pImpl->initialized) {
        return;
    }

    std::lock_guard<std::mutex> lock(pImpl->graph_mutex);
    
    auto it1 = pImpl->knowledge_graph.find(knowledge_id1);
    auto it2 = pImpl->knowledge_graph.find(knowledge_id2);
    
    if (it1 != pImpl->knowledge_graph.end() && 
        it2 != pImpl->knowledge_graph.end()) {
        
        it1->second.relations[knowledge_id2] = relation_strength;
        it2->second.relations[knowledge_id1] = relation_strength;
    }
}

CollaborativeInferenceResult GlobalInferenceSharingSystem::coordinateMultiModelInference(
    const std::string& input,
    const std::vector<std::string>& model_ids,
    const std::string& strategy) {
    
    CollaborativeInferenceResult result;
    result.participating_models = model_ids;
    result.success = false;

    if (!pImpl->initialized || model_ids.empty()) {
        return result;
    }

    auto& manager = InferenceSharingManager::getInstance();
    
    // Coordinate inference across multiple sharing systems
    std::vector<InferenceResult> all_results;
    
    for (const auto& model_id : model_ids) {
        auto system = manager.getSharingSystem(model_id);
        if (system) {
            // Perform collaborative inference
            auto collab_result = system->collaborativeInference(
                input, {model_id}, strategy);
            
            if (collab_result.success) {
                result.partial_results.insert(
                    result.partial_results.end(),
                    collab_result.partial_results.begin(),
                    collab_result.partial_results.end());
            }
        }
    }

    // Aggregate results
    if (!result.partial_results.empty()) {
        float total_confidence = 0.0f;
        std::string combined_output;
        
        for (const auto& partial : result.partial_results) {
            combined_output += partial.output + " ";
            total_confidence += partial.confidence;
            result.contribution_weights[partial.model_id] = partial.confidence;
        }
        
        result.final_output = combined_output;
        result.combined_confidence = total_confidence / result.partial_results.size();
        result.success = true;
        
        pImpl->total_collaborations++;
        pImpl->collaboration_qualities.push_back(result.combined_confidence);
    }

    pImpl->total_inferences++;
    
    return result;
}

GlobalInferenceSharingSystem::SystemMetrics 
GlobalInferenceSharingSystem::getSystemMetrics() const {
    SystemMetrics metrics;
    
    auto& manager = InferenceSharingManager::getInstance();
    
    metrics.total_sharing_systems = manager.getActiveSharingSystemCount();
    metrics.total_knowledge_entries = manager.getTotalKnowledgeCount();
    metrics.total_inferences = pImpl->total_inferences;
    metrics.total_validations = pImpl->total_validations;
    metrics.total_collaborations = pImpl->total_collaborations;
    
    metrics.avg_validation_accuracy = pImpl->validation_accuracies.empty() ? 0.0 :
        std::accumulate(pImpl->validation_accuracies.begin(), 
                       pImpl->validation_accuracies.end(), 0.0) 
        / pImpl->validation_accuracies.size();
    
    metrics.avg_collaboration_quality = pImpl->collaboration_qualities.empty() ? 0.0 :
        std::accumulate(pImpl->collaboration_qualities.begin(),
                       pImpl->collaboration_qualities.end(), 0.0)
        / pImpl->collaboration_qualities.size();
    
    std::lock_guard<std::mutex> lock(pImpl->graph_mutex);
    metrics.knowledge_graph_nodes = pImpl->knowledge_graph.size();
    
    size_t total_edges = 0;
    for (const auto& [id, node] : pImpl->knowledge_graph) {
        total_edges += node.relations.size();
    }
    metrics.knowledge_graph_edges = total_edges / 2;  // Bidirectional edges counted once
    
    return metrics;
}

} // namespace inference
} // namespace cogniware

