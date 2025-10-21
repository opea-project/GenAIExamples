#include "llm_inference_core/model/model_selector.h"
#include "llm_inference_core/model/huggingface_model_selector.cpp"
#include "llm_inference_core/model/ollama_model_selector.cpp"
#include <spdlog/spdlog.h>
#include <algorithm>

namespace cogniware {

std::unique_ptr<ModelSelector> ModelSelectorFactory::createSelector(ModelSource source) {
    switch (source) {
        case ModelSource::HUGGING_FACE:
            return std::make_unique<HuggingFaceModelSelector>();
        case ModelSource::OLLAMA:
            return std::make_unique<OllamaModelSelector>();
        case ModelSource::LOCAL:
            // For local models, we can use a generic selector or return null
            spdlog::warn("Local model selector not implemented yet");
            return nullptr;
        case ModelSource::CUSTOM:
            // For custom models, we can use a generic selector or return null
            spdlog::warn("Custom model selector not implemented yet");
            return nullptr;
        default:
            spdlog::error("Unknown model source: {}", static_cast<int>(source));
            return nullptr;
    }
}

std::vector<ModelMetadata> ModelSelectorFactory::searchAllSources(const std::string& query) {
    std::vector<ModelMetadata> allModels;
    
    // Search Hugging Face
    try {
        auto hfSelector = createSelector(ModelSource::HUGGING_FACE);
        if (hfSelector) {
            auto hfModels = hfSelector->searchModels(query, ModelSource::HUGGING_FACE);
            allModels.insert(allModels.end(), hfModels.begin(), hfModels.end());
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to search Hugging Face: {}", e.what());
    }
    
    // Search Ollama
    try {
        auto ollamaSelector = createSelector(ModelSource::OLLAMA);
        if (ollamaSelector) {
            auto ollamaModels = ollamaSelector->searchModels(query, ModelSource::OLLAMA);
            allModels.insert(allModels.end(), ollamaModels.begin(), ollamaModels.end());
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to search Ollama: {}", e.what());
    }
    
    // Remove duplicates based on model ID
    std::sort(allModels.begin(), allModels.end(), 
             [](const ModelMetadata& a, const ModelMetadata& b) {
                 return a.id < b.id;
             });
    
    allModels.erase(std::unique(allModels.begin(), allModels.end(),
                               [](const ModelMetadata& a, const ModelMetadata& b) {
                                   return a.id == b.id;
                               }), allModels.end());
    
    spdlog::info("Found {} models across all sources for query: {}", allModels.size(), query);
    return allModels;
}

std::vector<ModelMetadata> ModelSelectorFactory::getPopularModelsFromAllSources() {
    std::vector<ModelMetadata> allModels;
    
    // Get popular models from Hugging Face
    try {
        auto hfSelector = createSelector(ModelSource::HUGGING_FACE);
        if (hfSelector) {
            auto hfModels = hfSelector->getPopularModels(ModelSource::HUGGING_FACE);
            allModels.insert(allModels.end(), hfModels.begin(), hfModels.end());
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to get popular models from Hugging Face: {}", e.what());
    }
    
    // Get popular models from Ollama
    try {
        auto ollamaSelector = createSelector(ModelSource::OLLAMA);
        if (ollamaSelector) {
            auto ollamaModels = ollamaSelector->getPopularModels(ModelSource::OLLAMA);
            allModels.insert(allModels.end(), ollamaModels.begin(), ollamaModels.end());
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to get popular models from Ollama: {}", e.what());
    }
    
    // Sort by popularity (parameter count as proxy)
    std::sort(allModels.begin(), allModels.end(), 
             [](const ModelMetadata& a, const ModelMetadata& b) {
                 return a.parameterCount > b.parameterCount;
             });
    
    // Limit to top 50 models
    if (allModels.size() > 50) {
        allModels.resize(50);
    }
    
    spdlog::info("Retrieved {} popular models from all sources", allModels.size());
    return allModels;
}

} // namespace cogniware
