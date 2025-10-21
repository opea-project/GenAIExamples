#include "llm_inference_core/model/model_selector.h"
#include <spdlog/spdlog.h>
#include <nlohmann/json.hpp>
#include <curl/curl.h>
#include <sstream>
#include <algorithm>
#include <regex>

namespace cogniware {

HuggingFaceModelSelector::HuggingFaceModelSelector()
    : apiBaseUrl_("https://huggingface.co/api")
    , lastCacheUpdate_(std::chrono::system_clock::now()) {
    
    // Initialize curl
    curl_global_init(CURL_GLOBAL_DEFAULT);
    
    spdlog::info("HuggingFace model selector initialized");
}

std::vector<ModelMetadata> HuggingFaceModelSelector::searchModels(const std::string& query, 
                                                                ModelSource source) {
    if (source != ModelSource::HUGGING_FACE) {
        spdlog::warn("HuggingFace selector called with non-HuggingFace source");
        return {};
    }
    
    try {
        std::string endpoint = apiBaseUrl_ + "/models?search=" + query + "&limit=50";
        return fetchModelsFromAPI(endpoint);
    } catch (const std::exception& e) {
        spdlog::error("Failed to search models: {}", e.what());
        return {};
    }
}

std::vector<ModelMetadata> HuggingFaceModelSelector::getPopularModels(ModelSource source) {
    if (source != ModelSource::HUGGING_FACE) {
        spdlog::warn("HuggingFace selector called with non-HuggingFace source");
        return {};
    }
    
    try {
        std::string endpoint = apiBaseUrl_ + "/models?sort=downloads&direction=-1&limit=50";
        return fetchModelsFromAPI(endpoint);
    } catch (const std::exception& e) {
        spdlog::error("Failed to get popular models: {}", e.what());
        return {};
    }
}

std::vector<ModelMetadata> HuggingFaceModelSelector::getModelsByTask(SupportedTask task, 
                                                                   ModelSource source) {
    if (source != ModelSource::HUGGING_FACE) {
        spdlog::warn("HuggingFace selector called with non-HuggingFace source");
        return {};
    }
    
    try {
        std::string taskTag = getTaskTag(task);
        if (taskTag.empty()) {
            spdlog::warn("Unknown task type: {}", static_cast<int>(task));
            return {};
        }
        
        std::string endpoint = apiBaseUrl_ + "/models?filter=" + taskTag + "&limit=50";
        return fetchModelsFromAPI(endpoint);
    } catch (const std::exception& e) {
        spdlog::error("Failed to get models by task: {}", e.what());
        return {};
    }
}

ModelMetadata HuggingFaceModelSelector::getModelInfo(const std::string& modelId, 
                                                    ModelSource source) {
    if (source != ModelSource::HUGGING_FACE) {
        spdlog::warn("HuggingFace selector called with non-HuggingFace source");
        return {};
    }
    
    try {
        std::string endpoint = apiBaseUrl_ + "/models/" + modelId;
        auto models = fetchModelsFromAPI(endpoint);
        return models.empty() ? ModelMetadata{} : models[0];
    } catch (const std::exception& e) {
        spdlog::error("Failed to get model info for {}: {}", modelId, e.what());
        return {};
    }
}

std::vector<ModelMetadata> HuggingFaceModelSelector::filterBySize(size_t minSize, size_t maxSize) {
    std::vector<ModelMetadata> filtered;
    for (const auto& model : cachedModels_) {
        if (model.modelSize >= minSize && model.modelSize <= maxSize) {
            filtered.push_back(model);
        }
    }
    return filtered;
}

std::vector<ModelMetadata> HuggingFaceModelSelector::filterByParameterCount(size_t minParams, size_t maxParams) {
    std::vector<ModelMetadata> filtered;
    for (const auto& model : cachedModels_) {
        if (model.parameterCount >= minParams && model.parameterCount <= maxParams) {
            filtered.push_back(model);
        }
    }
    return filtered;
}

std::vector<ModelMetadata> HuggingFaceModelSelector::filterByLanguage(const std::string& language) {
    std::vector<ModelMetadata> filtered;
    for (const auto& model : cachedModels_) {
        if (model.language == language) {
            filtered.push_back(model);
        }
    }
    return filtered;
}

std::vector<ModelMetadata> HuggingFaceModelSelector::filterByLicense(const std::string& license) {
    std::vector<ModelMetadata> filtered;
    for (const auto& model : cachedModels_) {
        if (model.license == license) {
            filtered.push_back(model);
        }
    }
    return filtered;
}

std::vector<ModelMetadata> HuggingFaceModelSelector::getTrendingModels() {
    try {
        std::string endpoint = apiBaseUrl_ + "/models?sort=likes&direction=-1&limit=50";
        return fetchModelsFromAPI(endpoint);
    } catch (const std::exception& e) {
        spdlog::error("Failed to get trending models: {}", e.what());
        return {};
    }
}

std::vector<ModelMetadata> HuggingFaceModelSelector::getModelsByAuthor(const std::string& author) {
    try {
        std::string endpoint = apiBaseUrl_ + "/models?author=" + author + "&limit=50";
        return fetchModelsFromAPI(endpoint);
    } catch (const std::exception& e) {
        spdlog::error("Failed to get models by author {}: {}", author, e.what());
        return {};
    }
}

std::vector<ModelMetadata> HuggingFaceModelSelector::getModelsByTag(const std::string& tag) {
    try {
        std::string endpoint = apiBaseUrl_ + "/models?filter=" + tag + "&limit=50";
        return fetchModelsFromAPI(endpoint);
    } catch (const std::exception& e) {
        spdlog::error("Failed to get models by tag {}: {}", tag, e.what());
        return {};
    }
}

std::vector<ModelMetadata> HuggingFaceModelSelector::fetchModelsFromAPI(const std::string& endpoint) {
    std::vector<ModelMetadata> models;
    
    CURL* curl = curl_easy_init();
    if (!curl) {
        spdlog::error("Failed to initialize curl");
        return models;
    }
    
    std::string response;
    
    curl_easy_setopt(curl, CURLOPT_URL, endpoint.c_str());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, [](char* ptr, size_t size, size_t nmemb, std::string* data) {
        data->append(ptr, size * nmemb);
        return size * nmemb;
    });
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
    curl_easy_setopt(curl, CURLOPT_USERAGENT, "CogniWare-ModelSelector/1.0");
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 30L);
    
    CURLcode res = curl_easy_perform(curl);
    if (res != CURLE_OK) {
        spdlog::error("Failed to fetch from API: {}", curl_easy_strerror(res));
        curl_easy_cleanup(curl);
        return models;
    }
    
    curl_easy_cleanup(curl);
    
    try {
        nlohmann::json jsonData = nlohmann::json::parse(response);
        
        if (jsonData.is_array()) {
            for (const auto& item : jsonData) {
                ModelMetadata metadata = parseModelMetadata(item.dump());
                if (!metadata.id.empty()) {
                    models.push_back(metadata);
                }
            }
        } else if (jsonData.is_object()) {
            ModelMetadata metadata = parseModelMetadata(jsonData.dump());
            if (!metadata.id.empty()) {
                models.push_back(metadata);
            }
        }
        
        // Update cache
        cachedModels_.insert(cachedModels_.end(), models.begin(), models.end());
        lastCacheUpdate_ = std::chrono::system_clock::now();
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to parse API response: {}", e.what());
    }
    
    return models;
}

ModelMetadata HuggingFaceModelSelector::parseModelMetadata(const std::string& jsonData) {
    ModelMetadata metadata;
    
    try {
        nlohmann::json json = nlohmann::json::parse(jsonData);
        
        metadata.id = json.value("id", "");
        metadata.name = json.value("id", "");
        metadata.description = json.value("pipeline_tag", "");
        metadata.author = json.value("author", "");
        metadata.license = json.value("license", "");
        metadata.version = json.value("lastModified", "");
        metadata.language = json.value("language", "en");
        metadata.source = ModelSource::HUGGING_FACE;
        
        // Parse tags
        if (json.contains("tags") && json["tags"].is_array()) {
            for (const auto& tag : json["tags"]) {
                metadata.tags.push_back(tag.get<std::string>());
            }
        }
        
        // Parse downloads count as parameter count estimate
        metadata.parameterCount = json.value("downloads", 0);
        
        // Estimate model size (this is a rough estimate)
        metadata.modelSize = metadata.parameterCount * 4; // 4 bytes per parameter (FP32)
        
        // Set download URL
        metadata.downloadUrl = "https://huggingface.co/" + metadata.id;
        
        // Identify supported tasks
        metadata.supportedTasks = identifySupportedTasks(metadata.id, metadata.description);
        
        // Determine model type
        metadata.modelType = determineModelType(metadata.id, metadata.supportedTasks);
        
        metadata.isDownloaded = false;
        metadata.isConfigured = false;
        metadata.lastUpdated = std::chrono::system_clock::now();
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to parse model metadata: {}", e.what());
    }
    
    return metadata;
}

std::vector<SupportedTask> HuggingFaceModelSelector::identifySupportedTasks(const std::string& modelId, 
                                                                           const std::string& modelType) {
    std::vector<SupportedTask> tasks;
    
    // Convert model type to lowercase for comparison
    std::string lowerType = modelType;
    std::transform(lowerType.begin(), lowerType.end(), lowerType.begin(), ::tolower);
    
    // Map common model types to supported tasks
    if (lowerType.find("text-generation") != std::string::npos ||
        lowerType.find("gpt") != std::string::npos ||
        lowerType.find("llama") != std::string::npos) {
        tasks.push_back(SupportedTask::TEXT_GENERATION);
        tasks.push_back(SupportedTask::CHAT);
    }
    
    if (lowerType.find("text-classification") != std::string::npos ||
        lowerType.find("bert") != std::string::npos) {
        tasks.push_back(SupportedTask::TEXT_CLASSIFICATION);
    }
    
    if (lowerType.find("question-answering") != std::string::npos ||
        lowerType.find("qa") != std::string::npos) {
        tasks.push_back(SupportedTask::QUESTION_ANSWERING);
        tasks.push_back(SupportedTask::RAG);
    }
    
    if (lowerType.find("summarization") != std::string::npos ||
        lowerType.find("summarize") != std::string::npos) {
        tasks.push_back(SupportedTask::SUMMARIZATION);
    }
    
    if (lowerType.find("translation") != std::string::npos ||
        lowerType.find("translate") != std::string::npos) {
        tasks.push_back(SupportedTask::TRANSLATION);
    }
    
    if (lowerType.find("embedding") != std::string::npos ||
        lowerType.find("sentence-transformers") != std::string::npos) {
        tasks.push_back(SupportedTask::EMBEDDING);
    }
    
    if (lowerType.find("image-captioning") != std::string::npos ||
        lowerType.find("vision") != std::string::npos) {
        tasks.push_back(SupportedTask::IMAGE_CAPTIONING);
        tasks.push_back(SupportedTask::MULTIMODAL_REASONING);
    }
    
    if (lowerType.find("code") != std::string::npos) {
        tasks.push_back(SupportedTask::CODE_GENERATION);
        tasks.push_back(SupportedTask::CODE_COMPLETION);
    }
    
    // If no specific tasks identified, add generic text generation
    if (tasks.empty()) {
        tasks.push_back(SupportedTask::TEXT_GENERATION);
    }
    
    return tasks;
}

ModelType HuggingFaceModelSelector::determineModelType(const std::string& modelId, 
                                                      const std::vector<SupportedTask>& tasks) {
    // Check if it's an embedding model
    if (std::find(tasks.begin(), tasks.end(), SupportedTask::EMBEDDING) != tasks.end()) {
        return ModelType::EMBEDDING_MODEL;
    }
    
    // Check if it's a multimodal model
    if (std::find(tasks.begin(), tasks.end(), SupportedTask::IMAGE_CAPTIONING) != tasks.end() ||
        std::find(tasks.begin(), tasks.end(), SupportedTask::MULTIMODAL_REASONING) != tasks.end()) {
        return ModelType::MULTIMODAL_MODEL;
    }
    
    // Check if it's suitable for knowledge tasks
    if (std::find(tasks.begin(), tasks.end(), SupportedTask::QUESTION_ANSWERING) != tasks.end() ||
        std::find(tasks.begin(), tasks.end(), SupportedTask::RAG) != tasks.end() ||
        std::find(tasks.begin(), tasks.end(), SupportedTask::SUMMARIZATION) != tasks.end()) {
        return ModelType::KNOWLEDGE_MODEL;
    }
    
    // Check if it's suitable for interface tasks
    if (std::find(tasks.begin(), tasks.end(), SupportedTask::CHAT) != tasks.end() ||
        std::find(tasks.begin(), tasks.end(), SupportedTask::TEXT_GENERATION) != tasks.end()) {
        return ModelType::INTERFACE_MODEL;
    }
    
    // Default to interface model
    return ModelType::INTERFACE_MODEL;
}

std::string HuggingFaceModelSelector::getTaskTag(SupportedTask task) {
    switch (task) {
        case SupportedTask::TEXT_GENERATION:
            return "text-generation";
        case SupportedTask::TEXT_CLASSIFICATION:
            return "text-classification";
        case SupportedTask::QUESTION_ANSWERING:
            return "question-answering";
        case SupportedTask::SUMMARIZATION:
            return "summarization";
        case SupportedTask::TRANSLATION:
            return "translation";
        case SupportedTask::EMBEDDING:
            return "feature-extraction";
        case SupportedTask::IMAGE_CAPTIONING:
            return "image-to-text";
        case SupportedTask::CODE_GENERATION:
            return "text-generation";
        case SupportedTask::CHAT:
            return "text-generation";
        case SupportedTask::RAG:
            return "question-answering";
        default:
            return "";
    }
}

} // namespace cogniware
