#pragma once

#include <string>
#include <vector>
#include <map>
#include <memory>
#include <functional>
#include <chrono>

namespace cogniware {

// Model source types
enum class ModelSource {
    HUGGING_FACE,
    OLLAMA,
    LOCAL,
    CUSTOM
};

// Model types
enum class ModelType {
    INTERFACE_MODEL,    // For user interaction and chat
    KNOWLEDGE_MODEL,    // For knowledge retrieval and RAG
    EMBEDDING_MODEL,    // For text embeddings
    MULTIMODAL_MODEL,   // For multimodal tasks
    SPECIALIZED_MODEL   // For specific tasks
};

// Supported tasks
enum class SupportedTask {
    TEXT_GENERATION,
    TEXT_CLASSIFICATION,
    QUESTION_ANSWERING,
    SUMMARIZATION,
    TRANSLATION,
    EMBEDDING,
    IMAGE_CAPTIONING,
    IMAGE_GENERATION,
    AUDIO_TRANSCRIPTION,
    AUDIO_GENERATION,
    CODE_GENERATION,
    CODE_COMPLETION,
    CHAT,
    RAG,
    MULTIMODAL_REASONING
};

// Model metadata
struct ModelMetadata {
    std::string id;
    std::string name;
    std::string description;
    std::string author;
    std::string license;
    std::string version;
    std::string language;
    std::vector<std::string> tags;
    std::vector<SupportedTask> supportedTasks;
    ModelType modelType;
    ModelSource source;
    size_t parameterCount;
    size_t modelSize;  // in bytes
    std::string downloadUrl;
    std::string localPath;
    std::string configPath;
    std::string tokenizerPath;
    bool isDownloaded;
    bool isConfigured;
    std::chrono::system_clock::time_point lastUpdated;
    std::map<std::string, std::string> additionalInfo;
};

// Model configuration
struct ModelConfiguration {
    std::string modelId;
    ModelType modelType;
    std::vector<SupportedTask> enabledTasks;
    std::map<std::string, std::string> parameters;
    std::string systemPrompt;
    std::string userPrompt;
    std::string assistantPrompt;
    bool enableStreaming;
    bool enableCaching;
    size_t maxContextLength;
    size_t maxTokens;
    float temperature;
    float topP;
    size_t topK;
    bool useHalfPrecision;
    bool useQuantization;
    std::string quantizationType;
    std::map<std::string, std::string> customSettings;
};

// Download progress callback
using DownloadProgressCallback = std::function<void(const std::string& modelId, 
                                                   size_t downloaded, 
                                                   size_t total, 
                                                   const std::string& status)>;

// Model selector interface
class ModelSelector {
public:
    virtual ~ModelSelector() = default;

    // Model discovery
    virtual std::vector<ModelMetadata> searchModels(const std::string& query, 
                                                   ModelSource source = ModelSource::HUGGING_FACE) = 0;
    virtual std::vector<ModelMetadata> getPopularModels(ModelSource source = ModelSource::HUGGING_FACE) = 0;
    virtual std::vector<ModelMetadata> getModelsByTask(SupportedTask task, 
                                                      ModelSource source = ModelSource::HUGGING_FACE) = 0;
    virtual ModelMetadata getModelInfo(const std::string& modelId, 
                                      ModelSource source = ModelSource::HUGGING_FACE) = 0;

    // Model filtering
    virtual std::vector<ModelMetadata> filterBySize(size_t minSize, size_t maxSize) = 0;
    virtual std::vector<ModelMetadata> filterByParameterCount(size_t minParams, size_t maxParams) = 0;
    virtual std::vector<ModelMetadata> filterByLanguage(const std::string& language) = 0;
    virtual std::vector<ModelMetadata> filterByLicense(const std::string& license) = 0;
};

// Hugging Face model selector
class HuggingFaceModelSelector : public ModelSelector {
public:
    HuggingFaceModelSelector();
    ~HuggingFaceModelSelector() override = default;

    // Model discovery
    std::vector<ModelMetadata> searchModels(const std::string& query, 
                                           ModelSource source = ModelSource::HUGGING_FACE) override;
    std::vector<ModelMetadata> getPopularModels(ModelSource source = ModelSource::HUGGING_FACE) override;
    std::vector<ModelMetadata> getModelsByTask(SupportedTask task, 
                                              ModelSource source = ModelSource::HUGGING_FACE) override;
    ModelMetadata getModelInfo(const std::string& modelId, 
                              ModelSource source = ModelSource::HUGGING_FACE) override;

    // Model filtering
    std::vector<ModelMetadata> filterBySize(size_t minSize, size_t maxSize) override;
    std::vector<ModelMetadata> filterByParameterCount(size_t minParams, size_t maxParams) override;
    std::vector<ModelMetadata> filterByLanguage(const std::string& language) override;
    std::vector<ModelMetadata> filterByLicense(const std::string& license) override;

    // Hugging Face specific methods
    std::vector<ModelMetadata> getTrendingModels();
    std::vector<ModelMetadata> getModelsByAuthor(const std::string& author);
    std::vector<ModelMetadata> getModelsByTag(const std::string& tag);

private:
    std::string apiBaseUrl_;
    std::string apiToken_;
    std::vector<ModelMetadata> cachedModels_;
    std::chrono::system_clock::time_point lastCacheUpdate_;
    
    // Helper methods
    std::vector<ModelMetadata> fetchModelsFromAPI(const std::string& endpoint);
    ModelMetadata parseModelMetadata(const std::string& jsonData);
    std::vector<SupportedTask> identifySupportedTasks(const std::string& modelId, 
                                                     const std::string& modelType);
    ModelType determineModelType(const std::string& modelId, 
                                const std::vector<SupportedTask>& tasks);
};

// Ollama model selector
class OllamaModelSelector : public ModelSelector {
public:
    OllamaModelSelector();
    ~OllamaModelSelector() override = default;

    // Model discovery
    std::vector<ModelMetadata> searchModels(const std::string& query, 
                                           ModelSource source = ModelSource::OLLAMA) override;
    std::vector<ModelMetadata> getPopularModels(ModelSource source = ModelSource::OLLAMA) override;
    std::vector<ModelMetadata> getModelsByTask(SupportedTask task, 
                                              ModelSource source = ModelSource::OLLAMA) override;
    ModelMetadata getModelInfo(const std::string& modelId, 
                              ModelSource source = ModelSource::OLLAMA) override;

    // Model filtering
    std::vector<ModelMetadata> filterBySize(size_t minSize, size_t maxSize) override;
    std::vector<ModelMetadata> filterByParameterCount(size_t minParams, size_t maxParams) override;
    std::vector<ModelMetadata> filterByLanguage(const std::string& language) override;
    std::vector<ModelMetadata> filterByLicense(const std::string& license) override;

    // Ollama specific methods
    std::vector<ModelMetadata> getLocalModels();
    std::vector<ModelMetadata> getAvailableModels();
    bool isOllamaRunning();

private:
    std::string ollamaBaseUrl_;
    std::vector<ModelMetadata> localModels_;
    std::vector<ModelMetadata> availableModels_;
    
    // Helper methods
    std::vector<ModelMetadata> fetchModelsFromOllama(const std::string& endpoint);
    ModelMetadata parseOllamaModelInfo(const std::string& jsonData);
    std::vector<SupportedTask> identifyOllamaTasks(const std::string& modelId);
};

// Model selector factory
class ModelSelectorFactory {
public:
    static std::unique_ptr<ModelSelector> createSelector(ModelSource source);
    static std::vector<ModelMetadata> searchAllSources(const std::string& query);
    static std::vector<ModelMetadata> getPopularModelsFromAllSources();
};

} // namespace cogniware
