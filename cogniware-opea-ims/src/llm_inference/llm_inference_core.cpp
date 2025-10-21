#include "llm_inference/llm_inference_core.h"
#include <spdlog/spdlog.h>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <json/json.h>
#include <filesystem>
#include <cuda_runtime.h>
#include <NvInfer.h>
#include <onnxruntime_cxx_api.h>

namespace cogniware {
namespace llm_inference {

LLMInferenceCore& LLMInferenceCore::get_instance() {
    static LLMInferenceCore instance;
    return instance;
}

void LLMInferenceCore::initialize(const std::string& config_path) {
    try {
        if (is_initialized_) {
            spdlog::warn("LLMInferenceCore already initialized");
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

        // Initialize components
        initialize_cuda();
        initialize_tensorrt();
        initialize_onnx();
        initialize_tokenizer();
        initialize_model_cache();
        initialize_inference_engine();

        is_initialized_ = true;
        spdlog::info("LLMInferenceCore initialized successfully");
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize LLMInferenceCore: {}", e.what());
        throw;
    }
}

void LLMInferenceCore::configure(const std::unordered_map<std::string, std::string>& config) {
    try {
        std::lock_guard<std::mutex> lock(mutex_);

        for (const auto& [key, value] : config) {
            if (key == "max_batch_size") {
                inference_config_.max_batch_size = std::stoi(value);
            } else if (key == "max_sequence_length") {
                inference_config_.max_sequence_length = std::stoi(value);
            } else if (key == "temperature") {
                inference_config_.temperature = std::stof(value);
            } else if (key == "top_p") {
                inference_config_.top_p = std::stof(value);
            } else if (key == "top_k") {
                inference_config_.top_k = std::stoi(value);
            } else if (key == "use_fp16") {
                inference_config_.use_fp16 = (value == "true");
            } else if (key == "use_int8") {
                inference_config_.use_int8 = (value == "true");
            }
            // Add more configuration options as needed
        }

        validate_config();
        spdlog::info("LLMInferenceCore reconfigured");
    } catch (const std::exception& e) {
        spdlog::error("Failed to configure LLMInferenceCore: {}", e.what());
        throw;
    }
}

void LLMInferenceCore::shutdown() {
    try {
        if (!is_initialized_) {
            return;
        }

        cleanup();
        is_initialized_ = false;
        spdlog::info("LLMInferenceCore shut down");
    } catch (const std::exception& e) {
        spdlog::error("Error during LLMInferenceCore shutdown: {}", e.what());
        throw;
    }
}

void LLMInferenceCore::load_model(const std::string& model_path) {
    try {
        std::lock_guard<std::mutex> lock(mutex_);

        if (!is_initialized_) {
            throw std::runtime_error("LLMInferenceCore not initialized");
        }

        if (is_model_loaded_) {
            spdlog::warn("Model already loaded");
            return;
        }

        // Load model into inference engine
        inference_engine_->load_model(model_path);
        is_model_loaded_ = true;

        spdlog::info("Model loaded successfully from: {}", model_path);
    } catch (const std::exception& e) {
        spdlog::error("Failed to load model: {}", e.what());
        throw;
    }
}

void LLMInferenceCore::unload_model() {
    try {
        std::lock_guard<std::mutex> lock(mutex_);

        if (!is_model_loaded_) {
            return;
        }

        // Unload model from inference engine
        inference_engine_->unload_model();
        is_model_loaded_ = false;

        spdlog::info("Model unloaded successfully");
    } catch (const std::exception& e) {
        spdlog::error("Failed to unload model: {}", e.what());
        throw;
    }
}

bool LLMInferenceCore::is_model_loaded() const {
    return is_model_loaded_;
}

std::vector<float> LLMInferenceCore::run_inference(
    const std::vector<int>& input_tokens,
    const std::unordered_map<std::string, std::string>& parameters) {
    try {
        std::lock_guard<std::mutex> lock(mutex_);

        if (!is_model_loaded_) {
            throw std::runtime_error("Model not loaded");
        }

        // Run inference
        auto result = inference_engine_->run_inference(input_tokens, parameters);
        return result;
    } catch (const std::exception& e) {
        spdlog::error("Inference failed: {}", e.what());
        throw;
    }
}

std::vector<float> LLMInferenceCore::generate(
    const std::string& prompt,
    const std::unordered_map<std::string, std::string>& parameters) {
    try {
        std::lock_guard<std::mutex> lock(mutex_);

        if (!is_model_loaded_) {
            throw std::runtime_error("Model not loaded");
        }

        // Tokenize input
        auto tokens = tokenizer_->encode(prompt);

        // Run inference
        auto result = inference_engine_->run_inference(tokens, parameters);

        // Decode output
        auto text = tokenizer_->decode(result);
        return result;
    } catch (const std::exception& e) {
        spdlog::error("Generation failed: {}", e.what());
        throw;
    }
}

std::vector<std::vector<float>> LLMInferenceCore::batch_inference(
    const std::vector<std::vector<int>>& batch_tokens,
    const std::unordered_map<std::string, std::string>& parameters) {
    try {
        std::lock_guard<std::mutex> lock(mutex_);

        if (!is_model_loaded_) {
            throw std::runtime_error("Model not loaded");
        }

        // Run batch inference
        auto results = inference_engine_->batch_inference(batch_tokens, parameters);
        return results;
    } catch (const std::exception& e) {
        spdlog::error("Batch inference failed: {}", e.what());
        throw;
    }
}

std::vector<std::string> LLMInferenceCore::batch_generate(
    const std::vector<std::string>& prompts,
    const std::unordered_map<std::string, std::string>& parameters) {
    try {
        std::lock_guard<std::mutex> lock(mutex_);

        if (!is_model_loaded_) {
            throw std::runtime_error("Model not loaded");
        }

        // Tokenize inputs
        std::vector<std::vector<int>> batch_tokens;
        for (const auto& prompt : prompts) {
            batch_tokens.push_back(tokenizer_->encode(prompt));
        }

        // Run batch inference
        auto results = inference_engine_->batch_inference(batch_tokens, parameters);

        // Decode outputs
        std::vector<std::string> texts;
        for (const auto& result : results) {
            texts.push_back(tokenizer_->decode(result));
        }

        return texts;
    } catch (const std::exception& e) {
        spdlog::error("Batch generation failed: {}", e.what());
        throw;
    }
}

void LLMInferenceCore::set_memory_limit(size_t limit) {
    try {
        std::lock_guard<std::mutex> lock(mutex_);
        inference_engine_->set_memory_limit(limit);
    } catch (const std::exception& e) {
        spdlog::error("Failed to set memory limit: {}", e.what());
        throw;
    }
}

size_t LLMInferenceCore::get_available_memory() const {
    try {
        std::lock_guard<std::mutex> lock(mutex_);
        return inference_engine_->get_available_memory();
    } catch (const std::exception& e) {
        spdlog::error("Failed to get available memory: {}", e.what());
        throw;
    }
}

void LLMInferenceCore::allocate_memory(size_t size) {
    try {
        std::lock_guard<std::mutex> lock(mutex_);
        inference_engine_->allocate_memory(size);
    } catch (const std::exception& e) {
        spdlog::error("Failed to allocate memory: {}", e.what());
        throw;
    }
}

void LLMInferenceCore::deallocate_memory(size_t size) {
    try {
        std::lock_guard<std::mutex> lock(mutex_);
        inference_engine_->deallocate_memory(size);
    } catch (const std::exception& e) {
        spdlog::error("Failed to deallocate memory: {}", e.what());
        throw;
    }
}

// Private helper functions

void LLMInferenceCore::validate_config() {
    if (inference_config_.max_batch_size <= 0) {
        throw std::runtime_error("Invalid batch size");
    }
    if (inference_config_.max_sequence_length <= 0) {
        throw std::runtime_error("Invalid sequence length");
    }
    if (inference_config_.temperature <= 0.0f) {
        throw std::runtime_error("Invalid temperature");
    }
    if (inference_config_.top_p <= 0.0f || inference_config_.top_p > 1.0f) {
        throw std::runtime_error("Invalid top_p value");
    }
    if (inference_config_.top_k <= 0) {
        throw std::runtime_error("Invalid top_k value");
    }
}

void LLMInferenceCore::initialize_cuda() {
    cudaError_t error = cudaSetDevice(0);
    if (error != cudaSuccess) {
        throw std::runtime_error("Failed to initialize CUDA: " + std::string(cudaGetErrorString(error)));
    }
}

void LLMInferenceCore::initialize_tensorrt() {
    // Initialize TensorRT logger
    class Logger : public nvinfer1::ILogger {
        void log(Severity severity, const char* msg) noexcept override {
            if (severity == Severity::kERROR) {
                spdlog::error("TensorRT: {}", msg);
            } else if (severity == Severity::kWARNING) {
                spdlog::warn("TensorRT: {}", msg);
            } else if (severity == Severity::kINFO) {
                spdlog::info("TensorRT: {}", msg);
            }
        }
    } logger;

    // Create TensorRT builder
    auto builder = nvinfer1::createInferBuilder(logger);
    if (!builder) {
        throw std::runtime_error("Failed to create TensorRT builder");
    }
}

void LLMInferenceCore::initialize_onnx() {
    Ort::Env env(ORT_LOGGING_LEVEL_WARNING, "llm_inference");
    Ort::SessionOptions session_options;
    session_options.SetIntraOpNumThreads(1);
    session_options.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_ALL);
}

void LLMInferenceCore::initialize_tokenizer() {
    tokenizer_ = std::make_unique<Tokenizer>(tokenizer_config_);
}

void LLMInferenceCore::initialize_model_cache() {
    model_cache_ = std::make_unique<ModelCache>(inference_config_.cache_size);
}

void LLMInferenceCore::initialize_inference_engine() {
    inference_engine_ = std::make_unique<InferenceEngine>(inference_config_);
}

void LLMInferenceCore::cleanup() {
    if (is_model_loaded_) {
        unload_model();
    }

    inference_engine_.reset();
    tokenizer_.reset();
    model_cache_.reset();
}

} // namespace llm_inference
} // namespace cogniware 