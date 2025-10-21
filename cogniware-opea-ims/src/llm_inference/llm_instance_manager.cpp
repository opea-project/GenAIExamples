#include "../../include/llm_inference/llm_instance_manager.h"
#include <spdlog/spdlog.h>
#include <algorithm>
#include <stdexcept>

namespace cogniware {
namespace llm_inference {

// LLMInstance implementation
LLMInstance::LLMInstance(const std::string& model_id)
    : model_id_(model_id)
    , is_loaded_(false)
    , input_embeddings_(nullptr)
    , output_embeddings_(nullptr)
    , workspace_(nullptr)
    , workspace_size_(0)
{
    cudaStreamCreate(&stream_);
}

LLMInstance::~LLMInstance() {
    if (input_embeddings_) cudaFree(input_embeddings_);
    if (output_embeddings_) cudaFree(output_embeddings_);
    if (workspace_) cudaFree(workspace_);
    cudaStreamDestroy(stream_);
}

bool LLMInstance::loadModel(const std::string& path, const std::string& format) {
    model_loader_ = createModelLoader(format);
    if (!model_loader_) {
        return false;
    }

    if (!model_loader_->loadFromFile(path)) {
        return false;
    }

    return initialize();
}

bool LLMInstance::initialize() {
    if (!model_loader_) {
        return false;
    }

    // Create transformer blocks
    size_t num_layers = model_loader_->getNumLayers();
    size_t hidden_size = model_loader_->getHiddenSize();
    size_t num_heads = model_loader_->getNumHeads();
    size_t intermediate_size = 4 * hidden_size;  // Standard FFN size

    transformer_blocks_.reserve(num_layers);
    for (size_t i = 0; i < num_layers; ++i) {
        auto block = std::make_unique<TransformerBlock>(hidden_size, num_heads, intermediate_size);
        if (!block->initialize(model_loader_->getLayerWeights(i), i)) {
            return false;
        }
        transformer_blocks_.push_back(std::move(block));
    }

    // Allocate embedding weights
    auto& memory_manager = GPUMemoryManager::getInstance();
    size_t vocab_size = model_loader_->getParameterCount() / (hidden_size * num_layers);
    
    input_embeddings_ = static_cast<float*>(memory_manager.allocate(vocab_size * hidden_size * sizeof(float)));
    output_embeddings_ = static_cast<float*>(memory_manager.allocate(vocab_size * hidden_size * sizeof(float)));

    // Copy embedding weights
    memory_manager.copyToDevice(input_embeddings_, model_loader_->getEmbeddingWeights(), 
        vocab_size * hidden_size * sizeof(float));
    memory_manager.copyToDevice(output_embeddings_, model_loader_->getOutputWeights(), 
        vocab_size * hidden_size * sizeof(float));

    is_loaded_ = true;
    return true;
}

bool LLMInstance::generate(
    const std::string& prompt,
    std::string& output,
    size_t max_tokens,
    float temperature,
    float top_p,
    int top_k
) {
    if (!is_loaded_) {
        return false;
    }

    // TODO: Implement tokenization
    std::vector<int> input_ids;
    // tokenizer_->encode(prompt, input_ids);

    // Allocate workspace
    size_t batch_size = 1;
    size_t seq_length = input_ids.size();
    size_t hidden_size = model_loader_->getHiddenSize();
    size_t required_workspace = (seq_length + max_tokens) * hidden_size * sizeof(float);
    
    if (required_workspace > workspace_size_) {
        if (workspace_) {
            cudaFree(workspace_);
        }
        workspace_ = static_cast<float*>(GPUMemoryManager::getInstance().allocate(required_workspace));
        workspace_size_ = required_workspace;
    }

    // Forward pass through transformer blocks
    float* hidden_states = workspace_;
    for (size_t i = 0; i < transformer_blocks_.size(); ++i) {
        if (!transformer_blocks_[i]->forward(hidden_states, hidden_states, batch_size, seq_length, stream_)) {
            return false;
        }
    }

    // TODO: Implement sampling and tokenization
    // output = tokenizer_->decode(output_ids);

    return true;
}

bool LLMInstance::isLoaded() const {
    return is_loaded_;
}

const std::string& LLMInstance::getModelId() const {
    return model_id_;
}

size_t LLMInstance::getContextLength() const {
    return model_loader_ ? model_loader_->getContextLength() : 0;
}

size_t LLMInstance::getParameterCount() const {
    return model_loader_ ? model_loader_->getParameterCount() : 0;
}

// LLMInstanceManager implementation
LLMInstanceManager& LLMInstanceManager::getInstance() {
    static LLMInstanceManager instance;
    return instance;
}

LLMInstanceManager::LLMInstanceManager()
    : max_instances_(4)
    , max_memory_per_instance_(1024 * 1024 * 1024) // 1GB default
{
    try {
        // Initialize CUDA
        cudaError_t error = cudaSetDevice(0);
        if (error != cudaSuccess) {
            throw std::runtime_error("Failed to initialize CUDA: " + std::string(cudaGetErrorString(error)));
        }

        // Initialize memory manager
        auto& memory_manager = GPUMemoryManager::getInstance();
        memory_manager.setMaxMemory(max_instances_ * max_memory_per_instance_);

        spdlog::info("LLM Instance Manager initialized with {} instances, {} MB per instance",
            max_instances_, max_memory_per_instance_ / (1024 * 1024));
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize LLM Instance Manager: {}", e.what());
        throw;
    }
}

LLMInstanceManager::~LLMInstanceManager() {
    try {
        // Clear all instances
        clearInstances();
        spdlog::info("LLM Instance Manager cleaned up");
    } catch (const std::exception& e) {
        spdlog::error("Error during LLM Instance Manager cleanup: {}", e.what());
    }
}

bool LLMInstanceManager::loadModel(const std::string& model_id, const std::string& model_path) {
    try {
        std::lock_guard<std::mutex> lock(mutex_);

        // Check if model is already loaded
        if (instances_.find(model_id) != instances_.end()) {
            spdlog::warn("Model {} is already loaded", model_id);
            return true;
        }

        // Check instance limit
        if (instances_.size() >= max_instances_) {
            spdlog::error("Maximum number of instances reached");
            return false;
        }

        // Create and initialize inference engine
        InferenceEngineConfig config;
        config.max_batch_size = 8;
        config.max_sequence_length = 2048;
        config.temperature = 1.0f;
        config.top_p = 0.9f;
        config.top_k = 50;
        config.use_fp16 = true;
        config.enable_cache = true;
        config.cache_size = max_memory_per_instance_ / 2;
        config.enable_attention_cache = true;
        config.enable_kv_cache = true;
        config.num_attention_heads = 32;
        config.hidden_size = 4096;
        config.num_layers = 32;
        config.dropout = 0.1f;

        auto engine = std::make_unique<InferenceEngine>(config);
        engine->load_model(model_path);

        // Store instance
        instances_[model_id] = std::move(engine);
        spdlog::info("Model {} loaded successfully", model_id);

        return true;
    } catch (const std::exception& e) {
        spdlog::error("Failed to load model {}: {}", model_id, e.what());
        return false;
    }
}

void LLMInstanceManager::unloadModel(const std::string& model_id) {
    try {
        std::lock_guard<std::mutex> lock(mutex_);

        auto it = instances_.find(model_id);
        if (it != instances_.end()) {
            it->second->unload_model();
            instances_.erase(it);
            spdlog::info("Model {} unloaded", model_id);
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to unload model {}: {}", model_id, e.what());
        throw;
    }
}

bool LLMInstanceManager::isModelLoaded(const std::string& model_id) const {
    std::lock_guard<std::mutex> lock(mutex_);
    return instances_.find(model_id) != instances_.end();
}

bool LLMInstanceManager::generate(
    const std::string& model_id,
    const std::string& prompt,
    const std::unordered_map<std::string, std::string>& parameters,
    std::string& output
) {
    try {
        std::lock_guard<std::mutex> lock(mutex_);

        auto it = instances_.find(model_id);
        if (it == instances_.end()) {
            spdlog::error("Model {} is not loaded", model_id);
            return false;
        }

        // Tokenize input
        std::vector<int> input_tokens;
        if (!tokenizer_.encode(prompt, input_tokens)) {
            spdlog::error("Failed to tokenize input");
            return false;
        }

        // Run inference
        auto logits = it->second->run_inference(input_tokens, parameters);
        if (logits.empty()) {
            spdlog::error("Inference failed");
            return false;
        }

        // Decode output
        if (!tokenizer_.decode(logits, output)) {
            spdlog::error("Failed to decode output");
            return false;
        }

        return true;
    } catch (const std::exception& e) {
        spdlog::error("Generation failed for model {}: {}", model_id, e.what());
        return false;
    }
}

bool LLMInstanceManager::batchGenerate(
    const std::string& model_id,
    const std::vector<std::string>& prompts,
    const std::vector<std::unordered_map<std::string, std::string>>& parameters,
    std::vector<std::string>& outputs
) {
    try {
        std::lock_guard<std::mutex> lock(mutex_);

        auto it = instances_.find(model_id);
        if (it == instances_.end()) {
            spdlog::error("Model {} is not loaded", model_id);
            return false;
        }

        // Tokenize inputs
        std::vector<std::vector<int>> batch_tokens;
        batch_tokens.reserve(prompts.size());
        for (const auto& prompt : prompts) {
            std::vector<int> tokens;
            if (!tokenizer_.encode(prompt, tokens)) {
                spdlog::error("Failed to tokenize input");
                return false;
            }
            batch_tokens.push_back(std::move(tokens));
        }

        // Run batch inference
        auto batch_logits = it->second->batch_inference(batch_tokens, parameters[0]);
        if (batch_logits.empty()) {
            spdlog::error("Batch inference failed");
            return false;
        }

        // Decode outputs
        outputs.clear();
        outputs.reserve(batch_logits.size());
        for (const auto& logits : batch_logits) {
            std::string output;
            if (!tokenizer_.decode(logits, output)) {
                spdlog::error("Failed to decode output");
                return false;
            }
            outputs.push_back(std::move(output));
        }

        return true;
    } catch (const std::exception& e) {
        spdlog::error("Batch generation failed for model {}: {}", model_id, e.what());
        return false;
    }
}

void LLMInstanceManager::setMaxInstances(size_t max_instances) {
    std::lock_guard<std::mutex> lock(mutex_);
    max_instances_ = max_instances;
    auto& memory_manager = GPUMemoryManager::getInstance();
    memory_manager.setMaxMemory(max_instances_ * max_memory_per_instance_);
    spdlog::info("Set maximum instances to {}", max_instances_);
}

void LLMInstanceManager::setMaxMemoryPerInstance(size_t max_memory) {
    std::lock_guard<std::mutex> lock(mutex_);
    max_memory_per_instance_ = max_memory;
    auto& memory_manager = GPUMemoryManager::getInstance();
    memory_manager.setMaxMemory(max_instances_ * max_memory_per_instance_);
    spdlog::info("Set maximum memory per instance to {} MB", max_memory_per_instance_ / (1024 * 1024));
}

size_t LLMInstanceManager::getMaxInstances() const {
    return max_instances_;
}

size_t LLMInstanceManager::getMaxMemoryPerInstance() const {
    return max_memory_per_instance_;
}

size_t LLMInstanceManager::getCurrentInstanceCount() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return instances_.size();
}

void LLMInstanceManager::clearInstances() {
    try {
        std::lock_guard<std::mutex> lock(mutex_);
        instances_.clear();
        auto& memory_manager = GPUMemoryManager::getInstance();
        memory_manager.reset();
        spdlog::info("Cleared all model instances");
    } catch (const std::exception& e) {
        spdlog::error("Failed to clear instances: {}", e.what());
        throw;
    }
}

} // namespace llm_inference
} // namespace cogniware 