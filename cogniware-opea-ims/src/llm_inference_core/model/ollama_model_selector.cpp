#include "llm_inference_core/model/model_selector.h"
#include <spdlog/spdlog.h>
#include <nlohmann/json.hpp>
#include <curl/curl.h>
#include <sstream>
#include <algorithm>

namespace cogniware {

OllamaModelSelector::OllamaModelSelector()
    : ollamaBaseUrl_("http://localhost:11434") {
    
    // Initialize curl
    curl_global_init(CURL_GLOBAL_DEFAULT);
    
    spdlog::info("Ollama model selector initialized");
}

std::vector<ModelMetadata> OllamaModelSelector::searchModels(const std::string& query, 
                                                           ModelSource source) {
    if (source != ModelSource::OLLAMA) {
        spdlog::warn("Ollama selector called with non-Ollama source");
        return {};
    }
    
    try {
        // Get available models and filter by query
        auto models = getAvailableModels();
        std::vector<ModelMetadata> filtered;
        
        for (const auto& model : models) {
            if (model.name.find(query) != std::string::npos ||
                model.description.find(query) != std::string::npos) {
                filtered.push_back(model);
            }
        }
        
        return filtered;
    } catch (const std::exception& e) {
        spdlog::error("Failed to search models: {}", e.what());
        return {};
    }
}

std::vector<ModelMetadata> OllamaModelSelector::getPopularModels(ModelSource source) {
    if (source != ModelSource::OLLAMA) {
        spdlog::warn("Ollama selector called with non-Ollama source");
        return {};
    }
    
    try {
        // Get available models and sort by popularity (downloads)
        auto models = getAvailableModels();
        std::sort(models.begin(), models.end(), 
                 [](const ModelMetadata& a, const ModelMetadata& b) {
                     return a.parameterCount > b.parameterCount; // Use parameter count as popularity proxy
                 });
        
        // Return top 20 models
        if (models.size() > 20) {
            models.resize(20);
        }
        
        return models;
    } catch (const std::exception& e) {
        spdlog::error("Failed to get popular models: {}", e.what());
        return {};
    }
}

std::vector<ModelMetadata> OllamaModelSelector::getModelsByTask(SupportedTask task, 
                                                              ModelSource source) {
    if (source != ModelSource::OLLAMA) {
        spdlog::warn("Ollama selector called with non-Ollama source");
        return {};
    }
    
    try {
        auto models = getAvailableModels();
        std::vector<ModelMetadata> filtered;
        
        for (const auto& model : models) {
            if (std::find(model.supportedTasks.begin(), model.supportedTasks.end(), task) != model.supportedTasks.end()) {
                filtered.push_back(model);
            }
        }
        
        return filtered;
    } catch (const std::exception& e) {
        spdlog::error("Failed to get models by task: {}", e.what());
        return {};
    }
}

ModelMetadata OllamaModelSelector::getModelInfo(const std::string& modelId, 
                                              ModelSource source) {
    if (source != ModelSource::OLLAMA) {
        spdlog::warn("Ollama selector called with non-Ollama source");
        return {};
    }
    
    try {
        auto models = getAvailableModels();
        for (const auto& model : models) {
            if (model.id == modelId) {
                return model;
            }
        }
        
        return {};
    } catch (const std::exception& e) {
        spdlog::error("Failed to get model info for {}: {}", modelId, e.what());
        return {};
    }
}

std::vector<ModelMetadata> OllamaModelSelector::filterBySize(size_t minSize, size_t maxSize) {
    std::vector<ModelMetadata> filtered;
    for (const auto& model : availableModels_) {
        if (model.modelSize >= minSize && model.modelSize <= maxSize) {
            filtered.push_back(model);
        }
    }
    return filtered;
}

std::vector<ModelMetadata> OllamaModelSelector::filterByParameterCount(size_t minParams, size_t maxParams) {
    std::vector<ModelMetadata> filtered;
    for (const auto& model : availableModels_) {
        if (model.parameterCount >= minParams && model.parameterCount <= maxParams) {
            filtered.push_back(model);
        }
    }
    return filtered;
}

std::vector<ModelMetadata> OllamaModelSelector::filterByLanguage(const std::string& language) {
    std::vector<ModelMetadata> filtered;
    for (const auto& model : availableModels_) {
        if (model.language == language) {
            filtered.push_back(model);
        }
    }
    return filtered;
}

std::vector<ModelMetadata> OllamaModelSelector::filterByLicense(const std::string& license) {
    std::vector<ModelMetadata> filtered;
    for (const auto& model : availableModels_) {
        if (model.license == license) {
            filtered.push_back(model);
        }
    }
    return filtered;
}

std::vector<ModelMetadata> OllamaModelSelector::getLocalModels() {
    try {
        std::string endpoint = ollamaBaseUrl_ + "/api/tags";
        return fetchModelsFromOllama(endpoint);
    } catch (const std::exception& e) {
        spdlog::error("Failed to get local models: {}", e.what());
        return {};
    }
}

std::vector<ModelMetadata> OllamaModelSelector::getAvailableModels() {
    try {
        // Get both local and available models
        auto localModels = getLocalModels();
        auto availableModels = fetchModelsFromOllama(ollamaBaseUrl_ + "/api/library");
        
        // Combine and deduplicate
        std::vector<ModelMetadata> allModels = localModels;
        for (const auto& model : availableModels) {
            bool exists = false;
            for (const auto& local : localModels) {
                if (local.id == model.id) {
                    exists = true;
                    break;
                }
            }
            if (!exists) {
                allModels.push_back(model);
            }
        }
        
        availableModels_ = allModels;
        return allModels;
    } catch (const std::exception& e) {
        spdlog::error("Failed to get available models: {}", e.what());
        return {};
    }
}

bool OllamaModelSelector::isOllamaRunning() {
    CURL* curl = curl_easy_init();
    if (!curl) {
        return false;
    }
    
    std::string response;
    curl_easy_setopt(curl, CURLOPT_URL, (ollamaBaseUrl_ + "/api/version").c_str());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, [](char* ptr, size_t size, size_t nmemb, std::string* data) {
        data->append(ptr, size * nmemb);
        return size * nmemb;
    });
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 5L);
    
    CURLcode res = curl_easy_perform(curl);
    curl_easy_cleanup(curl);
    
    return res == CURLE_OK;
}

std::vector<ModelMetadata> OllamaModelSelector::fetchModelsFromOllama(const std::string& endpoint) {
    std::vector<ModelMetadata> models;
    
    if (!isOllamaRunning()) {
        spdlog::warn("Ollama is not running");
        return models;
    }
    
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
        spdlog::error("Failed to fetch from Ollama API: {}", curl_easy_strerror(res));
        curl_easy_cleanup(curl);
        return models;
    }
    
    curl_easy_cleanup(curl);
    
    try {
        nlohmann::json jsonData = nlohmann::json::parse(response);
        
        if (jsonData.contains("models") && jsonData["models"].is_array()) {
            for (const auto& item : jsonData["models"]) {
                ModelMetadata metadata = parseOllamaModelInfo(item.dump());
                if (!metadata.id.empty()) {
                    models.push_back(metadata);
                }
            }
        } else if (jsonData.is_array()) {
            for (const auto& item : jsonData) {
                ModelMetadata metadata = parseOllamaModelInfo(item.dump());
                if (!metadata.id.empty()) {
                    models.push_back(metadata);
                }
            }
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to parse Ollama API response: {}", e.what());
    }
    
    return models;
}

ModelMetadata OllamaModelSelector::parseOllamaModelInfo(const std::string& jsonData) {
    ModelMetadata metadata;
    
    try {
        nlohmann::json json = nlohmann::json::parse(jsonData);
        
        metadata.id = json.value("name", "");
        metadata.name = json.value("name", "");
        metadata.description = json.value("details", nlohmann::json::object()).value("format", "");
        metadata.author = "Ollama";
        metadata.license = "Various";
        metadata.version = json.value("modified_at", "");
        metadata.language = "en";
        metadata.source = ModelSource::OLLAMA;
        
        // Parse size
        if (json.contains("size")) {
            metadata.modelSize = json["size"].get<size_t>();
        }
        
        // Parse parameter count from details
        if (json.contains("details") && json["details"].contains("parameter_size")) {
            std::string paramSize = json["details"]["parameter_size"];
            // Parse parameter size string (e.g., "7B", "13B")
            if (paramSize.back() == 'B') {
                std::string numStr = paramSize.substr(0, paramSize.length() - 1);
                try {
                    float num = std::stof(numStr);
                    metadata.parameterCount = static_cast<size_t>(num * 1000000000); // Convert to actual count
                } catch (...) {
                    metadata.parameterCount = 0;
                }
            }
        }
        
        // Set download URL
        metadata.downloadUrl = "ollama://" + metadata.id;
        
        // Identify supported tasks
        metadata.supportedTasks = identifyOllamaTasks(metadata.id);
        
        // Determine model type
        if (std::find(metadata.supportedTasks.begin(), metadata.supportedTasks.end(), SupportedTask::EMBEDDING) != metadata.supportedTasks.end()) {
            metadata.modelType = ModelType::EMBEDDING_MODEL;
        } else if (std::find(metadata.supportedTasks.begin(), metadata.supportedTasks.end(), SupportedTask::CHAT) != metadata.supportedTasks.end()) {
            metadata.modelType = ModelType::INTERFACE_MODEL;
        } else {
            metadata.modelType = ModelType::INTERFACE_MODEL;
        }
        
        metadata.isDownloaded = json.value("size", 0) > 0; // If size > 0, model is downloaded
        metadata.isConfigured = false;
        metadata.lastUpdated = std::chrono::system_clock::now();
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to parse Ollama model info: {}", e.what());
    }
    
    return metadata;
}

std::vector<SupportedTask> OllamaModelSelector::identifyOllamaTasks(const std::string& modelId) {
    std::vector<SupportedTask> tasks;
    
    // Convert model ID to lowercase for comparison
    std::string lowerId = modelId;
    std::transform(lowerId.begin(), lowerId.end(), lowerId.begin(), ::tolower);
    
    // Most Ollama models support text generation and chat
    tasks.push_back(SupportedTask::TEXT_GENERATION);
    tasks.push_back(SupportedTask::CHAT);
    
    // Check for specific model types
    if (lowerId.find("embedding") != std::string::npos ||
        lowerId.find("embed") != std::string::npos) {
        tasks.push_back(SupportedTask::EMBEDDING);
    }
    
    if (lowerId.find("code") != std::string::npos) {
        tasks.push_back(SupportedTask::CODE_GENERATION);
        tasks.push_back(SupportedTask::CODE_COMPLETION);
    }
    
    if (lowerId.find("summarize") != std::string::npos ||
        lowerId.find("summarization") != std::string::npos) {
        tasks.push_back(SupportedTask::SUMMARIZATION);
    }
    
    if (lowerId.find("qa") != std::string::npos ||
        lowerId.find("question") != std::string::npos) {
        tasks.push_back(SupportedTask::QUESTION_ANSWERING);
        tasks.push_back(SupportedTask::RAG);
    }
    
    if (lowerId.find("translate") != std::string::npos ||
        lowerId.find("translation") != std::string::npos) {
        tasks.push_back(SupportedTask::TRANSLATION);
    }
    
    if (lowerId.find("classify") != std::string::npos ||
        lowerId.find("classification") != std::string::npos) {
        tasks.push_back(SupportedTask::TEXT_CLASSIFICATION);
    }
    
    return tasks;
}

} // namespace cogniware
