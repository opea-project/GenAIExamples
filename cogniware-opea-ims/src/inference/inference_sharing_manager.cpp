#include "inference/inference_sharing.h"
#include <algorithm>

namespace cogniware {
namespace inference {

// InferenceSharingManager Implementation
class InferenceSharingManager::ManagerImpl {
public:
    std::unordered_map<std::string, std::shared_ptr<AdvancedInferenceSharing>> sharing_systems;
    std::unordered_map<std::string, std::vector<std::shared_ptr<Knowledge>>> global_knowledge;
    mutable std::mutex systems_mutex;
    mutable std::mutex global_knowledge_mutex;
};

InferenceSharingManager::InferenceSharingManager()
    : pImpl(std::make_unique<ManagerImpl>()) {}

InferenceSharingManager::~InferenceSharingManager() = default;

InferenceSharingManager& InferenceSharingManager::getInstance() {
    static InferenceSharingManager instance;
    return instance;
}

bool InferenceSharingManager::createSharingSystem(
    const std::string& system_id,
    const InferenceSharingConfig& config) {
    
    std::lock_guard<std::mutex> lock(pImpl->systems_mutex);
    
    if (pImpl->sharing_systems.find(system_id) != pImpl->sharing_systems.end()) {
        return false;
    }

    pImpl->sharing_systems[system_id] = 
        std::make_shared<AdvancedInferenceSharing>(config);
    
    return true;
}

bool InferenceSharingManager::destroySharingSystem(const std::string& system_id) {
    std::lock_guard<std::mutex> lock(pImpl->systems_mutex);
    return pImpl->sharing_systems.erase(system_id) > 0;
}

std::shared_ptr<AdvancedInferenceSharing> InferenceSharingManager::getSharingSystem(
    const std::string& system_id) {
    
    std::lock_guard<std::mutex> lock(pImpl->systems_mutex);
    auto it = pImpl->sharing_systems.find(system_id);
    return (it != pImpl->sharing_systems.end()) ? it->second : nullptr;
}

bool InferenceSharingManager::shareKnowledgeGlobally(
    const std::shared_ptr<Knowledge>& knowledge) {
    
    if (!knowledge) {
        return false;
    }

    std::lock_guard<std::mutex> lock(pImpl->global_knowledge_mutex);
    pImpl->global_knowledge[knowledge->domain].push_back(knowledge);
    
    return true;
}

std::vector<std::shared_ptr<Knowledge>> InferenceSharingManager::queryGlobalKnowledge(
    const std::string& domain,
    size_t max_results) {
    
    std::lock_guard<std::mutex> lock(pImpl->global_knowledge_mutex);
    
    auto it = pImpl->global_knowledge.find(domain);
    if (it == pImpl->global_knowledge.end()) {
        return {};
    }

    const auto& knowledge_list = it->second;
    size_t count = std::min(max_results, knowledge_list.size());
    
    // Sort by confidence
    std::vector<std::shared_ptr<Knowledge>> sorted = knowledge_list;
    std::sort(sorted.begin(), sorted.end(),
        [](const auto& a, const auto& b) {
            return a->confidence > b->confidence;
        });

    return std::vector<std::shared_ptr<Knowledge>>(
        sorted.begin(), sorted.begin() + count);
}

CrossValidationResult InferenceSharingManager::validateAcrossSystems(
    const std::string& input,
    const std::vector<std::string>& system_ids) {
    
    CrossValidationResult result;
    result.validation_passed = false;

    if (system_ids.size() < 2) {
        return result;
    }

    std::lock_guard<std::mutex> lock(pImpl->systems_mutex);
    
    std::vector<InferenceResult> all_results;
    
    for (const auto& system_id : system_ids) {
        auto it = pImpl->sharing_systems.find(system_id);
        if (it != pImpl->sharing_systems.end()) {
            // Simulate inference from this system
            InferenceResult inference;
            inference.model_id = system_id;
            inference.input = input;
            inference.output = "System " + system_id + " result";
            inference.confidence = 0.8f;
            
            all_results.push_back(inference);
            result.model_ids.push_back(system_id);
        }
    }

    result.individual_results = all_results;
    
    // Calculate agreement
    if (all_results.size() >= 2) {
        float total_agreement = 0.0f;
        size_t comparisons = 0;
        
        for (size_t i = 0; i < all_results.size(); ++i) {
            for (size_t j = i + 1; j < all_results.size(); ++j) {
                // Simple similarity measure
                float agreement = (all_results[i].confidence + all_results[j].confidence) / 2.0f;
                result.agreement_scores.push_back(agreement);
                total_agreement += agreement;
                comparisons++;
            }
        }
        
        result.consensus_confidence = comparisons > 0 ? total_agreement / comparisons : 0.0f;
        result.validation_passed = result.consensus_confidence >= 0.75f;
        result.consensus_output = all_results[0].output;
    }

    return result;
}

size_t InferenceSharingManager::getActiveSharingSystemCount() const {
    std::lock_guard<std::mutex> lock(pImpl->systems_mutex);
    return pImpl->sharing_systems.size();
}

size_t InferenceSharingManager::getTotalKnowledgeCount() const {
    std::lock_guard<std::mutex> lock(pImpl->global_knowledge_mutex);
    size_t total = 0;
    for (const auto& [domain, knowledge_list] : pImpl->global_knowledge) {
        total += knowledge_list.size();
    }
    return total;
}

std::vector<std::string> InferenceSharingManager::getActiveSharingSystemIds() const {
    std::lock_guard<std::mutex> lock(pImpl->systems_mutex);
    std::vector<std::string> ids;
    for (const auto& [id, _] : pImpl->sharing_systems) {
        ids.push_back(id);
    }
    return ids;
}

} // namespace inference
} // namespace cogniware

