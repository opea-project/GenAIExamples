#include "dream/llm_management.h"
#include <spdlog/spdlog.h>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <json/json.h>
#include <filesystem>

namespace cogniware {
namespace dream {

LLMManager& LLMManager::get_instance() {
    static LLMManager instance;
    return instance;
}

void LLMManager::initialize(const std::string& config_path) {
    try {
        if (is_running_) {
            spdlog::warn("LLMManager already initialized");
            return;
        }

        // Load configuration
        std::ifstream config_file(config_path);
        if (!config_file) {
            throw std::runtime_error("Failed to open config file: " + config_path);
        }

        Json::Value root;
        Json::Reader reader;
        if (!reader.parse(config_file, root)) {
            throw std::runtime_error("Failed to parse config file: " + reader.getFormattedErrorMessages());
        }

        // Initialize core components
        inference_core_ = std::make_unique<LLMInferenceCore>();
        
        // Set resource limits
        memory_limit_ = root.get("memory_limit", 0).asUInt64();
        max_loaded_models_ = root.get("max_loaded_models", 1).asInt();

        // Start worker thread
        is_running_ = true;
        worker_thread_ = std::thread(&LLMManager::worker_loop, this);

        spdlog::info("LLMManager initialized successfully");
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize LLMManager: {}", e.what());
        throw;
    }
}

void LLMManager::configure(const std::unordered_map<std::string, std::string>& config) {
    try {
        for (const auto& [key, value] : config) {
            if (key == "memory_limit") {
                memory_limit_ = std::stoull(value);
            } else if (key == "max_loaded_models") {
                max_loaded_models_ = std::stoi(value);
            }
        }

        spdlog::info("LLMManager reconfigured");
    } catch (const std::exception& e) {
        spdlog::error("Failed to configure LLMManager: {}", e.what());
        throw;
    }
}

void LLMManager::shutdown() {
    try {
        if (!is_running_) {
            return;
        }

        is_running_ = false;
        queue_cv_.notify_all();

        if (worker_thread_.joinable()) {
            worker_thread_.join();
        }

        // Unload all models
        for (const auto& [model_id, metadata] : model_metadata_) {
            if (metadata.is_loaded) {
                unload_model(model_id, nullptr, true);
            }
        }

        inference_core_.reset();
        spdlog::info("LLMManager shut down");
    } catch (const std::exception& e) {
        spdlog::error("Error during LLMManager shutdown: {}", e.what());
        throw;
    }
}

void LLMManager::load_model(const std::string& model_id,
                          const std::string& model_path,
                          const ModelConfig& model_config,
                          const TokenizerConfig& tokenizer_config,
                          const InferenceConfig& inference_config,
                          std::function<void(bool)> callback,
                          int priority) {
    try {
        ModelLoadRequest request{
            model_id,
            model_path,
            model_config,
            tokenizer_config,
            inference_config,
            callback,
            priority,
            std::chrono::system_clock::now()
        };

        std::lock_guard<std::mutex> lock(queue_mutex_);
        load_queue_.push(request);
        queue_cv_.notify_one();
    } catch (const std::exception& e) {
        spdlog::error("Failed to queue model load request: {}", e.what());
        throw;
    }
}

void LLMManager::unload_model(const std::string& model_id,
                            std::function<void(bool)> callback,
                            bool force) {
    try {
        ModelUnloadRequest request{
            model_id,
            callback,
            force
        };

        std::lock_guard<std::mutex> lock(queue_mutex_);
        unload_queue_.push(request);
        queue_cv_.notify_one();
    } catch (const std::exception& e) {
        spdlog::error("Failed to queue model unload request: {}", e.what());
        throw;
    }
}

bool LLMManager::is_model_loaded(const std::string& model_id) const {
    auto it = model_metadata_.find(model_id);
    return it != model_metadata_.end() && it->second.is_loaded;
}

std::vector<std::string> LLMManager::get_loaded_models() const {
    std::vector<std::string> loaded_models;
    for (const auto& [model_id, metadata] : model_metadata_) {
        if (metadata.is_loaded) {
            loaded_models.push_back(model_id);
        }
    }
    return loaded_models;
}

ModelMetadata LLMManager::get_model_metadata(const std::string& model_id) const {
    auto it = model_metadata_.find(model_id);
    if (it == model_metadata_.end()) {
        throw std::runtime_error("Model not found: " + model_id);
    }
    return it->second;
}

std::vector<float> LLMManager::run_inference(
    const std::string& model_id,
    const std::vector<int>& input_tokens,
    const std::unordered_map<std::string, std::string>& parameters) {
    try {
        if (!is_model_loaded(model_id)) {
            throw std::runtime_error("Model not loaded: " + model_id);
        }

        auto start_time = std::chrono::high_resolution_clock::now();
        auto result = inference_core_->run_inference(input_tokens, parameters);
        auto end_time = std::chrono::high_resolution_clock::now();

        // Update metrics
        ModelMetrics metrics = model_metrics_[model_id];
        metrics.inference_time = std::chrono::duration<float>(end_time - start_time).count();
        metrics.inference_count++;
        metrics.last_inference = std::chrono::system_clock::now();
        update_model_metrics(model_id, metrics);

        // Update metadata
        auto& metadata = model_metadata_[model_id];
        metadata.last_used = std::chrono::system_clock::now();
        metadata.usage_count++;

        return result;
    } catch (const std::exception& e) {
        spdlog::error("Inference failed for model {}: {}", model_id, e.what());
        model_metrics_[model_id].error_count++;
        throw;
    }
}

std::vector<float> LLMManager::generate(
    const std::string& model_id,
    const std::string& prompt,
    const std::unordered_map<std::string, std::string>& parameters) {
    try {
        if (!is_model_loaded(model_id)) {
            throw std::runtime_error("Model not loaded: " + model_id);
        }

        auto start_time = std::chrono::high_resolution_clock::now();
        auto result = inference_core_->generate(prompt, parameters);
        auto end_time = std::chrono::high_resolution_clock::now();

        // Update metrics
        ModelMetrics metrics = model_metrics_[model_id];
        metrics.inference_time = std::chrono::duration<float>(end_time - start_time).count();
        metrics.inference_count++;
        metrics.last_inference = std::chrono::system_clock::now();
        update_model_metrics(model_id, metrics);

        // Update metadata
        auto& metadata = model_metadata_[model_id];
        metadata.last_used = std::chrono::system_clock::now();
        metadata.usage_count++;

        return result;
    } catch (const std::exception& e) {
        spdlog::error("Generation failed for model {}: {}", model_id, e.what());
        model_metrics_[model_id].error_count++;
        throw;
    }
}

std::vector<std::vector<float>> LLMManager::batch_inference(
    const std::string& model_id,
    const std::vector<std::vector<int>>& batch_tokens,
    const std::unordered_map<std::string, std::string>& parameters) {
    try {
        if (!is_model_loaded(model_id)) {
            throw std::runtime_error("Model not loaded: " + model_id);
        }

        auto start_time = std::chrono::high_resolution_clock::now();
        auto result = inference_core_->batch_inference(batch_tokens, parameters);
        auto end_time = std::chrono::high_resolution_clock::now();

        // Update metrics
        ModelMetrics metrics = model_metrics_[model_id];
        metrics.inference_time = std::chrono::duration<float>(end_time - start_time).count();
        metrics.inference_count++;
        metrics.last_inference = std::chrono::system_clock::now();
        update_model_metrics(model_id, metrics);

        // Update metadata
        auto& metadata = model_metadata_[model_id];
        metadata.last_used = std::chrono::system_clock::now();
        metadata.usage_count++;

        return result;
    } catch (const std::exception& e) {
        spdlog::error("Batch inference failed for model {}: {}", model_id, e.what());
        model_metrics_[model_id].error_count++;
        throw;
    }
}

std::vector<std::string> LLMManager::batch_generate(
    const std::string& model_id,
    const std::vector<std::string>& prompts,
    const std::unordered_map<std::string, std::string>& parameters) {
    try {
        if (!is_model_loaded(model_id)) {
            throw std::runtime_error("Model not loaded: " + model_id);
        }

        auto start_time = std::chrono::high_resolution_clock::now();
        auto result = inference_core_->batch_generate(prompts, parameters);
        auto end_time = std::chrono::high_resolution_clock::now();

        // Update metrics
        ModelMetrics metrics = model_metrics_[model_id];
        metrics.inference_time = std::chrono::duration<float>(end_time - start_time).count();
        metrics.inference_count++;
        metrics.last_inference = std::chrono::system_clock::now();
        update_model_metrics(model_id, metrics);

        // Update metadata
        auto& metadata = model_metadata_[model_id];
        metadata.last_used = std::chrono::system_clock::now();
        metadata.usage_count++;

        return result;
    } catch (const std::exception& e) {
        spdlog::error("Batch generation failed for model {}: {}", model_id, e.what());
        model_metrics_[model_id].error_count++;
        throw;
    }
}

void LLMManager::set_memory_limit(size_t limit) {
    memory_limit_ = limit;
}

size_t LLMManager::get_available_memory() const {
    return inference_core_->get_available_memory();
}

void LLMManager::set_max_loaded_models(int count) {
    max_loaded_models_ = count;
    cleanup_unused_models();
}

int LLMManager::get_max_loaded_models() const {
    return max_loaded_models_;
}

void LLMManager::set_model_priority(const std::string& model_id, int priority) {
    auto it = model_metadata_.find(model_id);
    if (it == model_metadata_.end()) {
        throw std::runtime_error("Model not found: " + model_id);
    }

    // Update priority in load queue
    std::lock_guard<std::mutex> lock(queue_mutex_);
    std::priority_queue<ModelLoadRequest> new_queue;
    while (!load_queue_.empty()) {
        auto request = load_queue_.top();
        load_queue_.pop();
        if (request.model_id == model_id) {
            request.priority = priority;
        }
        new_queue.push(request);
    }
    load_queue_ = std::move(new_queue);
}

void LLMManager::optimize_model(
    const std::string& model_id,
    const std::unordered_map<std::string, std::string>& optimization_params) {
    try {
        if (!is_model_loaded(model_id)) {
            throw std::runtime_error("Model not loaded: " + model_id);
        }

        // Apply optimization parameters
        for (const auto& [key, value] : optimization_params) {
            if (key == "batch_size") {
                inference_core_->set_batch_size(std::stoi(value));
            } else if (key == "sequence_length") {
                inference_core_->set_sequence_length(std::stoi(value));
            } else if (key == "quantization") {
                inference_core_->enable_quantization(value == "true");
            } else if (key == "quantization_type") {
                inference_core_->set_quantization_type(value);
            }
        }

        spdlog::info("Model {} optimized", model_id);
    } catch (const std::exception& e) {
        spdlog::error("Failed to optimize model {}: {}", model_id, e.what());
        throw;
    }
}

void LLMManager::quantize_model(const std::string& model_id,
                              const std::string& quantization_type) {
    try {
        if (!is_model_loaded(model_id)) {
            throw std::runtime_error("Model not loaded: " + model_id);
        }

        inference_core_->enable_quantization(true);
        inference_core_->set_quantization_type(quantization_type);

        auto& metadata = model_metadata_[model_id];
        metadata.is_quantized = true;
        metadata.quantization_type = quantization_type;

        spdlog::info("Model {} quantized with type {}", model_id, quantization_type);
    } catch (const std::exception& e) {
        spdlog::error("Failed to quantize model {}: {}", model_id, e.what());
        throw;
    }
}

void LLMManager::convert_model_format(const std::string& model_id,
                                    const std::string& target_format) {
    try {
        if (!is_model_loaded(model_id)) {
            throw std::runtime_error("Model not loaded: " + model_id);
        }

        // Implementation depends on the target format
        if (target_format == "onnx") {
            // Convert to ONNX format
        } else if (target_format == "engine") {
            // Convert to TensorRT format
        } else {
            throw std::runtime_error("Unsupported target format: " + target_format);
        }

        spdlog::info("Model {} converted to format {}", model_id, target_format);
    } catch (const std::exception& e) {
        spdlog::error("Failed to convert model {}: {}", model_id, e.what());
        throw;
    }
}

LLMManager::ModelMetrics LLMManager::get_model_metrics(const std::string& model_id) const {
    auto it = model_metrics_.find(model_id);
    if (it == model_metrics_.end()) {
        throw std::runtime_error("Model metrics not found: " + model_id);
    }
    return it->second;
}

void LLMManager::reset_model_metrics(const std::string& model_id) {
    model_metrics_[model_id] = ModelMetrics{};
}

// Private helper functions

void LLMManager::worker_loop() {
    while (is_running_) {
        std::unique_lock<std::mutex> lock(queue_mutex_);
        queue_cv_.wait(lock, [this] {
            return !is_running_ || !load_queue_.empty() || !unload_queue_.empty();
        });

        if (!is_running_) {
            break;
        }

        process_unload_queue();
        process_load_queue();
    }
}

void LLMManager::process_load_queue() {
    while (!load_queue_.empty()) {
        auto request = load_queue_.top();
        load_queue_.pop();

        try {
            load_model_internal(request);
            if (request.callback) {
                request.callback(true);
            }
        } catch (const std::exception& e) {
            spdlog::error("Failed to load model {}: {}", request.model_id, e.what());
            if (request.callback) {
                request.callback(false);
            }
        }
    }
}

void LLMManager::process_unload_queue() {
    while (!unload_queue_.empty()) {
        auto request = unload_queue_.front();
        unload_queue_.pop();

        try {
            unload_model_internal(request);
            if (request.callback) {
                request.callback(true);
            }
        } catch (const std::exception& e) {
            spdlog::error("Failed to unload model {}: {}", request.model_id, e.what());
            if (request.callback) {
                request.callback(false);
            }
        }
    }
}

void LLMManager::load_model_internal(const ModelLoadRequest& request) {
    // Check if model is already loaded
    if (is_model_loaded(request.model_id)) {
        spdlog::warn("Model {} already loaded", request.model_id);
        return;
    }

    // Check memory requirements
    ModelMetadata metadata{
        request.model_id,
        request.model_path,
        request.model_config.model_type,
        "",  // version
        "",  // architecture
        0,   // size
        {},  // features
        {},  // parameters
        std::chrono::system_clock::now(),
        0,   // usage_count
        false,
        false,
        ""   // quantization_type
    };

    if (!check_memory_requirements(metadata)) {
        cleanup_unused_models();
        if (!check_memory_requirements(metadata)) {
            throw std::runtime_error("Insufficient memory to load model");
        }
    }

    // Load model
    auto start_time = std::chrono::high_resolution_clock::now();
    inference_core_->load_model(request.model_path);
    auto end_time = std::chrono::high_resolution_clock::now();

    // Update metadata
    metadata.is_loaded = true;
    metadata.last_used = std::chrono::system_clock::now();
    model_metadata_[request.model_id] = metadata;

    // Update metrics
    ModelMetrics metrics{};
    metrics.load_time = std::chrono::duration<float>(end_time - start_time).count();
    model_metrics_[request.model_id] = metrics;

    spdlog::info("Model {} loaded successfully", request.model_id);
}

void LLMManager::unload_model_internal(const ModelUnloadRequest& request) {
    // Check if model is loaded
    if (!is_model_loaded(request.model_id)) {
        spdlog::warn("Model {} not loaded", request.model_id);
        return;
    }

    // Check if model is in use
    if (!request.force) {
        auto it = model_metadata_.find(request.model_id);
        if (it != model_metadata_.end() && it->second.usage_count > 0) {
            throw std::runtime_error("Model is in use");
        }
    }

    // Unload model
    inference_core_->unload_model();

    // Update metadata
    auto& metadata = model_metadata_[request.model_id];
    metadata.is_loaded = false;
    metadata.last_used = std::chrono::system_clock::now();

    spdlog::info("Model {} unloaded", request.model_id);
}

void LLMManager::update_model_metadata(const std::string& model_id, bool is_loaded) {
    auto it = model_metadata_.find(model_id);
    if (it != model_metadata_.end()) {
        it->second.is_loaded = is_loaded;
        it->second.last_used = std::chrono::system_clock::now();
    }
}

void LLMManager::update_model_metrics(const std::string& model_id,
                                    const ModelMetrics& metrics) {
    model_metrics_[model_id] = metrics;
}

bool LLMManager::check_memory_requirements(const ModelMetadata& metadata) {
    if (memory_limit_ == 0) {
        return true;
    }

    size_t available = get_available_memory();
    return available >= memory_limit_;
}

void LLMManager::cleanup_unused_models() {
    std::vector<std::pair<std::string, std::chrono::system_clock::time_point>> unused_models;
    for (const auto& [model_id, metadata] : model_metadata_) {
        if (metadata.is_loaded && metadata.usage_count == 0) {
            unused_models.emplace_back(model_id, metadata.last_used);
        }
    }

    // Sort by last used time
    std::sort(unused_models.begin(), unused_models.end(),
              [](const auto& a, const auto& b) {
                  return a.second < b.second;
              });

    // Unload models until we're under the limit
    int loaded_count = get_loaded_models().size();
    for (const auto& [model_id, _] : unused_models) {
        if (loaded_count <= max_loaded_models_) {
            break;
        }
        unload_model(model_id, nullptr, true);
        loaded_count--;
    }
}

void LLMManager::validate_model_config(const ModelConfig& config) {
    if (config.model_path.empty()) {
        throw std::runtime_error("Model path not specified");
    }
    if (config.model_type.empty()) {
        throw std::runtime_error("Model type not specified");
    }
}

void LLMManager::validate_tokenizer_config(const TokenizerConfig& config) {
    if (config.vocab_file.empty()) {
        throw std::runtime_error("Vocabulary file not specified");
    }
}

void LLMManager::validate_inference_config(const InferenceConfig& config) {
    if (config.max_batch_size <= 0) {
        throw std::runtime_error("Invalid batch size");
    }
    if (config.max_sequence_length <= 0) {
        throw std::runtime_error("Invalid sequence length");
    }
    if (config.temperature <= 0.0f) {
        throw std::runtime_error("Invalid temperature");
    }
    if (config.top_p <= 0.0f || config.top_p > 1.0f) {
        throw std::runtime_error("Invalid top_p value");
    }
    if (config.top_k <= 0) {
        throw std::runtime_error("Invalid top_k value");
    }
}

} // namespace dream
} // namespace cogniware 