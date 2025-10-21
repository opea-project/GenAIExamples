#include "gguf_loader.h"
#include "model_parser_utils.h"
#include <spdlog/spdlog.h>
#include <fstream>
#include <cstring>
#include <algorithm>

namespace cogniware {
namespace llm_inference {

// Internal implementation
struct GGUFLoader::Impl {
    std::string model_path;
    std::string model_name;
    bool is_loaded;
    size_t memory_limit;
    size_t total_memory_usage;
    size_t peak_memory_usage;

    // File handle
    std::ifstream file;
    size_t file_size;

    // Model data
    GGUFMetadata metadata;
    std::vector<GGUFTensorMetadata> tensor_metadata;
    std::unordered_map<std::string, void*> tensor_data;
    std::unordered_map<int, std::string> vocabulary;
    std::shared_ptr<ModelConfig> model_config;
    std::shared_ptr<Tokenizer> tokenizer;

    Impl() : is_loaded(false), memory_limit(0), total_memory_usage(0), peak_memory_usage(0) {}

    ~Impl() {
        cleanup();
    }

    void cleanup() {
        if (is_loaded) {
            // Free tensor data
            for (auto& [name, data] : tensor_data) {
                if (data) {
                    free(data);
                }
            }
            tensor_data.clear();

            // Close file
            if (file.is_open()) {
                file.close();
            }

            // Reset state
            is_loaded = false;
            total_memory_usage = 0;
            peak_memory_usage = 0;
        }
    }
};

// Constructor and destructor
GGUFLoader::GGUFLoader() : pimpl(std::make_unique<Impl>()) {}

GGUFLoader::~GGUFLoader() = default;

// Singleton access
GGUFLoader& GGUFLoader::getInstance() {
    static GGUFLoader instance;
    return instance;
}

// Model loading and unloading
bool GGUFLoader::loadModel(const std::string& path) {
    if (pimpl->is_loaded) {
        spdlog::warn("Model already loaded, unloading first");
        unloadModel();
    }

    // Open file
    pimpl->file.open(path, std::ios::binary);
    if (!pimpl->file.is_open()) {
        spdlog::error("Failed to open model file: {}", path);
        return false;
    }

    // Get file size
    pimpl->file.seekg(0, std::ios::end);
    pimpl->file_size = pimpl->file.tellg();
    pimpl->file.seekg(0, std::ios::beg);

    // Parse header
    if (!parseHeader()) {
        spdlog::error("Failed to parse GGUF header");
        return false;
    }

    // Parse tensors
    if (!parseTensors()) {
        spdlog::error("Failed to parse GGUF tensors");
        return false;
    }

    // Parse metadata
    if (!parseMetadata()) {
        spdlog::error("Failed to parse GGUF metadata");
        return false;
    }

    // Parse vocabulary
    if (!parseVocabulary()) {
        spdlog::error("Failed to parse GGUF vocabulary");
        return false;
    }

    // Validate model
    if (!validateModel()) {
        spdlog::error("Model validation failed");
        return false;
    }

    // Set state
    pimpl->model_path = path;
    pimpl->model_name = path.substr(path.find_last_of("/\\") + 1);
    pimpl->is_loaded = true;

    spdlog::info("Successfully loaded GGUF model: {}", pimpl->model_name);
    return true;
}

void GGUFLoader::unloadModel() {
    pimpl->cleanup();
    spdlog::info("Unloaded GGUF model");
}

// Model information
const GGUFMetadata& GGUFLoader::getMetadata() const {
    return pimpl->metadata;
}

const std::vector<GGUFTensorMetadata>& GGUFLoader::getTensorMetadata() const {
    return pimpl->tensor_metadata;
}

std::unordered_map<int, std::string> GGUFLoader::getVocabulary() const {
    return pimpl->vocabulary;
}

size_t GGUFLoader::getVocabularySize() const {
    return pimpl->vocabulary.size();
}

size_t GGUFLoader::getHiddenSize() const {
    return pimpl->metadata.embedding_dim;
}

// Tensor operations
void* GGUFLoader::getTensor(const std::string& name) {
    auto it = pimpl->tensor_data.find(name);
    if (it == pimpl->tensor_data.end()) {
        return nullptr;
    }
    return it->second;
}

void* GGUFLoader::getTensor(size_t index) {
    if (index >= pimpl->tensor_metadata.size()) {
        return nullptr;
    }
    return getTensor(pimpl->tensor_metadata[index].name);
}

size_t GGUFLoader::getTensorSize(const std::string& name) const {
    auto it = std::find_if(pimpl->tensor_metadata.begin(), pimpl->tensor_metadata.end(),
        [&name](const GGUFTensorMetadata& meta) { return meta.name == name; });
    if (it == pimpl->tensor_metadata.end()) {
        return 0;
    }
    return it->size;
}

size_t GGUFLoader::getTensorSize(size_t index) const {
    if (index >= pimpl->tensor_metadata.size()) {
        return 0;
    }
    return pimpl->tensor_metadata[index].size;
}

std::vector<int64_t> GGUFLoader::getTensorShape(const std::string& name) const {
    auto it = std::find_if(pimpl->tensor_metadata.begin(), pimpl->tensor_metadata.end(),
        [&name](const GGUFTensorMetadata& meta) { return meta.name == name; });
    if (it == pimpl->tensor_metadata.end()) {
        return {};
    }
    return it->shape;
}

std::vector<int64_t> GGUFLoader::getTensorShape(size_t index) const {
    if (index >= pimpl->tensor_metadata.size()) {
        return {};
    }
    return pimpl->tensor_metadata[index].shape;
}

// Memory management
size_t GGUFLoader::getTotalMemoryUsage() const {
    return pimpl->total_memory_usage;
}

size_t GGUFLoader::getPeakMemoryUsage() const {
    return pimpl->peak_memory_usage;
}

void GGUFLoader::setMemoryLimit(size_t limit) {
    pimpl->memory_limit = limit;
}

size_t GGUFLoader::getMemoryLimit() const {
    return pimpl->memory_limit;
}

// Model configuration
std::shared_ptr<ModelConfig> GGUFLoader::getModelConfig() const {
    return pimpl->model_config;
}

std::shared_ptr<Tokenizer> GGUFLoader::getTokenizer() const {
    return pimpl->tokenizer;
}

// State
bool GGUFLoader::isLoaded() const {
    return pimpl->is_loaded;
}

std::string GGUFLoader::getModelPath() const {
    return pimpl->model_path;
}

std::string GGUFLoader::getModelName() const {
    return pimpl->model_name;
}

// Internal helper functions
bool GGUFLoader::parseHeader() {
    // Read magic number
    uint32_t magic;
    pimpl->file.read(reinterpret_cast<char*>(&magic), sizeof(magic));
    if (magic != GGUF_MAGIC) {
        spdlog::error("Invalid GGUF magic number: {:x}", magic);
        return false;
    }

    // Read version
    uint32_t version;
    pimpl->file.read(reinterpret_cast<char*>(&version), sizeof(version));
    if (version != GGUF_VERSION) {
        spdlog::error("Unsupported GGUF version: {}", version);
        return false;
    }

    // Read tensor count
    uint64_t tensor_count;
    pimpl->file.read(reinterpret_cast<char*>(&tensor_count), sizeof(tensor_count));
    pimpl->tensor_metadata.reserve(tensor_count);

    return true;
}

bool GGUFLoader::parseTensors() {
    for (const auto& meta : pimpl->tensor_metadata) {
        // Check memory limit
        if (pimpl->memory_limit > 0 && pimpl->total_memory_usage + meta.size > pimpl->memory_limit) {
            spdlog::error("Memory limit exceeded");
            return false;
        }

        // Allocate memory
        void* data = malloc(meta.size);
        if (!data) {
            spdlog::error("Failed to allocate memory for tensor: {}", meta.name);
            return false;
        }

        // Read tensor data
        pimpl->file.seekg(meta.offset, std::ios::beg);
        pimpl->file.read(static_cast<char*>(data), meta.size);

        // Store tensor data
        pimpl->tensor_data[meta.name] = data;
        pimpl->total_memory_usage += meta.size;
        pimpl->peak_memory_usage = std::max(pimpl->peak_memory_usage, pimpl->total_memory_usage);
    }

    return true;
}

bool GGUFLoader::parseMetadata() {
    // Read metadata size
    uint64_t metadata_size;
    pimpl->file.read(reinterpret_cast<char*>(&metadata_size), sizeof(metadata_size));

    // Read metadata
    std::vector<char> metadata_buffer(metadata_size);
    pimpl->file.read(metadata_buffer.data(), metadata_size);

    // Parse metadata
    // TODO: Implement metadata parsing
    return true;
}

bool GGUFLoader::parseVocabulary() {
    // Read vocabulary size
    uint64_t vocab_size;
    pimpl->file.read(reinterpret_cast<char*>(&vocab_size), sizeof(vocab_size));

    // Read vocabulary
    for (uint64_t i = 0; i < vocab_size; ++i) {
        // Read token length
        uint32_t token_length;
        pimpl->file.read(reinterpret_cast<char*>(&token_length), sizeof(token_length));

        // Read token
        std::string token(token_length, '\0');
        pimpl->file.read(&token[0], token_length);

        // Store token
        pimpl->vocabulary[i] = token;
    }

    return true;
}

bool GGUFLoader::validateModel() {
    // Check required tensors
    const std::vector<std::string> required_tensors = {
        "token_embd.weight",
        "layers.0.attention.wq.weight",
        "layers.0.attention.wk.weight",
        "layers.0.attention.wv.weight",
        "layers.0.attention.wo.weight",
        "layers.0.feed_forward.w1.weight",
        "layers.0.feed_forward.w2.weight",
        "layers.0.feed_forward.w3.weight",
        "layers.0.attention_norm.weight",
        "layers.0.ffn_norm.weight"
    };

    for (const auto& name : required_tensors) {
        if (getTensor(name) == nullptr) {
            spdlog::error("Required tensor not found: {}", name);
            return false;
        }
    }

    return true;
}

} // namespace llm_inference
} // namespace cogniware
