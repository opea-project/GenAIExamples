#include "multimodal/multimodal_processor.h"
#include <algorithm>
#include <cmath>

namespace cogniware {
namespace multimodal {

// GlobalMultimodalSystem Implementation
class GlobalMultimodalSystem::GlobalImpl {
public:
    bool initialized;
    MultimodalConfig default_config;
    
    // Model registry
    struct ModelInfo {
        std::string model_id;
        ModalityType modality;
        std::string model_path;
    };
    
    std::unordered_map<std::string, ModelInfo> registered_models;
    mutable std::mutex models_mutex;
    
    // System metrics
    size_t total_inputs_processed;
    size_t total_gpu_memory_allocated;
    std::vector<double> throughput_samples;
    std::vector<double> latency_samples;
    mutable std::mutex metrics_mutex;
    
    GlobalImpl() 
        : initialized(false)
        , total_inputs_processed(0)
        , total_gpu_memory_allocated(0) {}

    float cosineSimilarity(const std::vector<float>& v1, const std::vector<float>& v2) {
        if (v1.size() != v2.size() || v1.empty()) {
            return 0.0f;
        }

        float dot = 0.0f;
        float norm1 = 0.0f;
        float norm2 = 0.0f;

        for (size_t i = 0; i < v1.size(); ++i) {
            dot += v1[i] * v2[i];
            norm1 += v1[i] * v1[i];
            norm2 += v2[i] * v2[i];
        }

        if (norm1 < 1e-6f || norm2 < 1e-6f) {
            return 0.0f;
        }

        return dot / (std::sqrt(norm1) * std::sqrt(norm2));
    }
};

GlobalMultimodalSystem::GlobalMultimodalSystem()
    : pImpl(std::make_unique<GlobalImpl>()) {}

GlobalMultimodalSystem::~GlobalMultimodalSystem() = default;

GlobalMultimodalSystem& GlobalMultimodalSystem::getInstance() {
    static GlobalMultimodalSystem instance;
    return instance;
}

bool GlobalMultimodalSystem::initialize(const MultimodalConfig& default_config) {
    if (pImpl->initialized) {
        return false;
    }

    pImpl->default_config = default_config;
    pImpl->initialized = true;
    
    return true;
}

bool GlobalMultimodalSystem::shutdown() {
    if (!pImpl->initialized) {
        return false;
    }

    std::lock_guard<std::mutex> lock(pImpl->models_mutex);
    pImpl->registered_models.clear();
    pImpl->initialized = false;
    
    return true;
}

bool GlobalMultimodalSystem::isInitialized() const {
    return pImpl->initialized;
}

bool GlobalMultimodalSystem::registerModel(
    const std::string& model_id,
    ModalityType modality,
    const std::string& model_path) {
    
    if (!pImpl->initialized) {
        return false;
    }

    std::lock_guard<std::mutex> lock(pImpl->models_mutex);
    
    if (pImpl->registered_models.find(model_id) != pImpl->registered_models.end()) {
        return false;
    }

    GlobalImpl::ModelInfo info;
    info.model_id = model_id;
    info.modality = modality;
    info.model_path = model_path;
    
    pImpl->registered_models[model_id] = info;
    
    return true;
}

bool GlobalMultimodalSystem::unregisterModel(const std::string& model_id) {
    if (!pImpl->initialized) {
        return false;
    }

    std::lock_guard<std::mutex> lock(pImpl->models_mutex);
    return pImpl->registered_models.erase(model_id) > 0;
}

std::vector<std::string> GlobalMultimodalSystem::getRegisteredModels(
    ModalityType modality) const {
    
    if (!pImpl->initialized) {
        return {};
    }

    std::lock_guard<std::mutex> lock(pImpl->models_mutex);
    
    std::vector<std::string> model_ids;
    for (const auto& [id, info] : pImpl->registered_models) {
        if (info.modality == modality) {
            model_ids.push_back(id);
        }
    }
    
    return model_ids;
}

float GlobalMultimodalSystem::calculateCrossModalSimilarity(
    const ModalityResult& result1,
    const ModalityResult& result2) {
    
    return pImpl->cosineSimilarity(result1.embeddings, result2.embeddings);
}

std::vector<float> GlobalMultimodalSystem::alignModalities(
    const std::vector<ModalityResult>& results) {
    
    if (results.empty()) {
        return {};
    }

    // Find the reference embedding size
    size_t max_embedding_size = 0;
    for (const auto& result : results) {
        max_embedding_size = std::max(max_embedding_size, result.embeddings.size());
    }

    if (max_embedding_size == 0) {
        return {};
    }

    // Align all embeddings to the same size
    std::vector<float> aligned(max_embedding_size, 0.0f);
    float total_weight = 0.0f;

    for (const auto& result : results) {
        float weight = result.scores.count("confidence") ? 
                      result.scores.at("confidence") : 1.0f;
        total_weight += weight;

        // Pad or truncate as needed
        for (size_t i = 0; i < std::min(max_embedding_size, result.embeddings.size()); ++i) {
            aligned[i] += result.embeddings[i] * weight;
        }
    }

    // Normalize
    if (total_weight > 0.0f) {
        for (float& val : aligned) {
            val /= total_weight;
        }
    }

    // L2 normalization
    float norm = 0.0f;
    for (float val : aligned) {
        norm += val * val;
    }
    norm = std::sqrt(norm);

    if (norm > 1e-6f) {
        for (float& val : aligned) {
            val /= norm;
        }
    }

    return aligned;
}

GlobalMultimodalSystem::SystemMetrics 
GlobalMultimodalSystem::getSystemMetrics() const {
    SystemMetrics metrics;
    
    auto& manager = MultimodalProcessorManager::getInstance();
    metrics.total_processors = manager.getActiveProcessorCount();
    
    {
        std::lock_guard<std::mutex> lock(pImpl->models_mutex);
        metrics.total_models_registered = pImpl->registered_models.size();
    }
    
    {
        std::lock_guard<std::mutex> lock(pImpl->metrics_mutex);
        metrics.total_inputs_processed = pImpl->total_inputs_processed;
        metrics.total_gpu_memory_allocated = pImpl->total_gpu_memory_allocated;
        
        metrics.avg_throughput_inputs_per_sec = pImpl->throughput_samples.empty() ? 0.0 :
            std::accumulate(pImpl->throughput_samples.begin(),
                           pImpl->throughput_samples.end(), 0.0)
            / pImpl->throughput_samples.size();
        
        metrics.avg_latency_ms = pImpl->latency_samples.empty() ? 0.0 :
            std::accumulate(pImpl->latency_samples.begin(),
                           pImpl->latency_samples.end(), 0.0)
            / pImpl->latency_samples.size();
    }
    
    return metrics;
}

} // namespace multimodal
} // namespace cogniware

