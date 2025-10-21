#pragma once

#include <memory>
#include <string>
#include <vector>
#include <unordered_map>
#include <cstdint>

namespace cogniware {
namespace llm_inference {

// Forward declarations
class ModelConfig;
class Tokenizer;

// GGUF tensor metadata
struct GGUFTensorMetadata {
    std::string name;
    std::vector<int64_t> shape;
    std::string dtype;
    size_t offset;
    size_t size;
    bool is_quantized;
    std::string quantization_type;
};

// GGUF model metadata
struct GGUFMetadata {
    std::string architecture;
    size_t context_size;
    size_t embedding_dim;
    size_t num_layers;
    size_t num_heads;
    size_t num_kv_heads;
    size_t intermediate_size;
    size_t rotary_dim;
    std::string quantization_type;
    size_t memory_usage;
    std::unordered_map<std::string, std::string> parameters;
};

class GGUFLoader {
public:
    static GGUFLoader& getInstance();

    // Prevent copying
    GGUFLoader(const GGUFLoader&) = delete;
    GGUFLoader& operator=(const GGUFLoader&) = delete;

    // Model loading and unloading
    bool loadModel(const std::string& path);
    void unloadModel();

    // Model information
    const GGUFMetadata& getMetadata() const;
    const std::vector<GGUFTensorMetadata>& getTensorMetadata() const;
    std::unordered_map<int, std::string> getVocabulary() const;
    size_t getVocabularySize() const;
    size_t getHiddenSize() const;

    // Tensor operations
    void* getTensor(const std::string& name);
    void* getTensor(size_t index);
    size_t getTensorSize(const std::string& name) const;
    size_t getTensorSize(size_t index) const;
    std::vector<int64_t> getTensorShape(const std::string& name) const;
    std::vector<int64_t> getTensorShape(size_t index) const;

    // Memory management
    size_t getTotalMemoryUsage() const;
    size_t getPeakMemoryUsage() const;
    void setMemoryLimit(size_t limit);
    size_t getMemoryLimit() const;

    // Model configuration
    std::shared_ptr<ModelConfig> getModelConfig() const;
    std::shared_ptr<Tokenizer> getTokenizer() const;

    // State
    bool isLoaded() const;
    std::string getModelPath() const;
    std::string getModelName() const;

private:
    GGUFLoader();
    ~GGUFLoader();

    // Internal helper functions
    bool parseHeader();
    bool parseTensors();
    bool parseMetadata();
    bool parseVocabulary();
    bool validateModel();
    void cleanup();

    // Internal state
    struct Impl;
    std::unique_ptr<Impl> pimpl;
};

// Helper functions
inline GGUFLoader& getGGUFLoader() {
    return GGUFLoader::getInstance();
}

inline bool loadGGUFModel(const std::string& path) {
    return getGGUFLoader().loadModel(path);
}

inline void unloadGGUFModel() {
    getGGUFLoader().unloadModel();
}

inline const GGUFMetadata& getGGUFMetadata() {
    return getGGUFLoader().getMetadata();
}

inline std::unordered_map<int, std::string> getGGUFVocabulary() {
    return getGGUFLoader().getVocabulary();
}

} // namespace llm_inference
} // namespace cogniware
