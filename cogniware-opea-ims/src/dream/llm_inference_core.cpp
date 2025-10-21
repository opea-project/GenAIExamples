#include "dream/llm_inference_core.h"
#include <spdlog/spdlog.h>
#include <fstream>
#include <sstream>
#include <chrono>
#include <thread>
#include <mutex>
#include <cuda_runtime.h>
#include <cublas_v2.h>
#include <cudnn.h>
#include <tensorrt/NvInfer.h>
#include <onnxruntime_cxx_api.h>
#include <json/json.h>

namespace cogniware {
namespace dream {

LLMInferenceCore& LLMInferenceCore::get_instance() {
    static LLMInferenceCore instance;
    return instance;
}

void LLMInferenceCore::initialize(const ModelConfig& model_config,
                                const TokenizerConfig& tokenizer_config,
                                const InferenceConfig& inference_config) {
    try {
        if (is_initialized_) {
            spdlog::warn("LLMInferenceCore already initialized");
            return;
        }

        model_config_ = model_config;
        tokenizer_config_ = tokenizer_config;
        inference_config_ = inference_config;

        validate_configs();
        initialize_cuda();
        initialize_tensorrt();
        initialize_onnx();
        initialize_tokenizer();

        is_initialized_ = true;
        spdlog::info("LLMInferenceCore initialized successfully");
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize LLMInferenceCore: {}", e.what());
        throw;
    }
}

void LLMInferenceCore::configure(const InferenceConfig& config) {
    try {
        inference_config_ = config;
        validate_configs();

        if (is_model_loaded_) {
            // Reconfigure loaded model
            if (trt_engine_) {
                trt_context_.reset(trt_engine_->createExecutionContext());
                trt_context_->setOptimizationProfile(0);
            }
            if (onnx_session_) {
                onnx_session_->SetGraphOptimizationLevel(
                    config.use_fp16 ? ORT_ENABLE_ALL : ORT_ENABLE_BASIC);
            }
        }

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

        unload_model();
        free_memory();

        if (trt_context_) trt_context_.reset();
        if (trt_engine_) trt_engine_.reset();
        if (trt_runtime_) trt_runtime_.reset();
        if (onnx_session_) onnx_session_.reset();
        if (memory_info_) memory_info_.reset();

        cublasDestroy(cublas_handle_);
        cudnnDestroy(cudnn_handle_);

        is_initialized_ = false;
        spdlog::info("LLMInferenceCore shut down");
    } catch (const std::exception& e) {
        spdlog::error("Error during LLMInferenceCore shutdown: {}", e.what());
        throw;
    }
}

void LLMInferenceCore::load_model(const std::string& model_path) {
    try {
        if (!is_initialized_) {
            throw std::runtime_error("LLMInferenceCore not initialized");
        }

        if (is_model_loaded_) {
            unload_model();
        }

        // Load model based on file extension
        std::string extension = model_path.substr(model_path.find_last_of(".") + 1);
        if (extension == "engine") {
            load_tensorrt_model(model_path);
        } else if (extension == "onnx") {
            load_onnx_model(model_path);
        } else {
            throw std::runtime_error("Unsupported model format: " + extension);
        }

        is_model_loaded_ = true;
        spdlog::info("Model loaded successfully: {}", model_path);
    } catch (const std::exception& e) {
        spdlog::error("Failed to load model: {}", e.what());
        throw;
    }
}

void LLMInferenceCore::unload_model() {
    try {
        if (!is_model_loaded_) {
            return;
        }

        if (trt_context_) trt_context_.reset();
        if (trt_engine_) trt_engine_.reset();
        if (onnx_session_) onnx_session_.reset();

        is_model_loaded_ = false;
        spdlog::info("Model unloaded");
    } catch (const std::exception& e) {
        spdlog::error("Error during model unload: {}", e.what());
        throw;
    }
}

bool LLMInferenceCore::is_model_loaded() const {
    return is_model_loaded_;
}

std::vector<int> LLMInferenceCore::tokenize(const std::string& text) {
    try {
        if (!is_initialized_) {
            throw std::runtime_error("LLMInferenceCore not initialized");
        }

        // Implement tokenization based on model type
        std::vector<int> tokens;
        if (model_config_.model_type == "gpt2") {
            // GPT-2 tokenization
            tokens = tokenize_gpt2(text);
        } else if (model_config_.model_type == "llama") {
            // LLaMA tokenization
            tokens = tokenize_llama(text);
        } else {
            throw std::runtime_error("Unsupported model type: " + model_config_.model_type);
        }

        // Add special tokens if configured
        if (tokenizer_config_.add_bos_token) {
            tokens.insert(tokens.begin(), tokenizer_config_.bos_token_id);
        }
        if (tokenizer_config_.add_eos_token) {
            tokens.push_back(tokenizer_config_.eos_token_id);
        }

        return tokens;
    } catch (const std::exception& e) {
        spdlog::error("Tokenization failed: {}", e.what());
        throw;
    }
}

std::string LLMInferenceCore::detokenize(const std::vector<int>& tokens) {
    try {
        if (!is_initialized_) {
            throw std::runtime_error("LLMInferenceCore not initialized");
        }

        // Remove special tokens
        std::vector<int> clean_tokens = tokens;
        if (tokenizer_config_.add_bos_token && !clean_tokens.empty() &&
            clean_tokens.front() == tokenizer_config_.bos_token_id) {
            clean_tokens.erase(clean_tokens.begin());
        }
        if (tokenizer_config_.add_eos_token && !clean_tokens.empty() &&
            clean_tokens.back() == tokenizer_config_.eos_token_id) {
            clean_tokens.pop_back();
        }

        // Implement detokenization based on model type
        if (model_config_.model_type == "gpt2") {
            return detokenize_gpt2(clean_tokens);
        } else if (model_config_.model_type == "llama") {
            return detokenize_llama(clean_tokens);
        } else {
            throw std::runtime_error("Unsupported model type: " + model_config_.model_type);
        }
    } catch (const std::exception& e) {
        spdlog::error("Detokenization failed: {}", e.what());
        throw;
    }
}

std::vector<float> LLMInferenceCore::run_inference(
    const std::vector<int>& input_tokens,
    const std::unordered_map<std::string, std::string>& parameters) {
    try {
        if (!is_model_loaded_) {
            throw std::runtime_error("Model not loaded");
        }

        auto start_time = std::chrono::high_resolution_clock::now();

        // Check cache if enabled
        if (cache_enabled_) {
            std::string cache_key = generate_cache_key(input_tokens);
            auto it = inference_cache_.find(cache_key);
            if (it != inference_cache_.end()) {
                update_metrics({0.0f, 0.0f, 0, 0.0f, 1, input_tokens.size(), 1.0f});
                return it->second.output_logits;
            }
        }

        // Prepare input
        std::vector<float> input_embeddings = prepare_input_embeddings(input_tokens);

        // Run inference
        std::vector<float> output_logits;
        if (trt_engine_) {
            output_logits = run_tensorrt_inference(input_embeddings);
        } else if (onnx_session_) {
            output_logits = run_onnx_inference(input_embeddings);
        }

        // Update cache if enabled
        if (cache_enabled_) {
            CacheEntry entry{
                input_tokens,
                output_logits,
                std::chrono::system_clock::now()
            };
            inference_cache_[generate_cache_key(input_tokens)] = entry;
            cleanup_cache();
        }

        // Update metrics
        auto end_time = std::chrono::high_resolution_clock::now();
        float latency = std::chrono::duration<float>(end_time - start_time).count();
        update_metrics({latency, 1.0f/latency, 0, 0.0f, 1, input_tokens.size(), 0.0f});

        return output_logits;
    } catch (const std::exception& e) {
        spdlog::error("Inference failed: {}", e.what());
        throw;
    }
}

std::vector<float> LLMInferenceCore::generate(
    const std::string& prompt,
    const std::unordered_map<std::string, std::string>& parameters) {
    try {
        // Tokenize input
        std::vector<int> input_tokens = tokenize(prompt);

        // Run inference
        std::vector<float> logits = run_inference(input_tokens, parameters);

        // Apply generation parameters
        float temperature = inference_config_.temperature;
        float top_p = inference_config_.top_p;
        int top_k = inference_config_.top_k;

        // Sample next token
        int next_token = sample_next_token(logits, temperature, top_p, top_k);

        // Add to output
        std::vector<int> output_tokens = input_tokens;
        output_tokens.push_back(next_token);

        // Continue generation until EOS or max length
        while (output_tokens.size() < inference_config_.max_sequence_length) {
            logits = run_inference(output_tokens, parameters);
            next_token = sample_next_token(logits, temperature, top_p, top_k);
            
            if (next_token == tokenizer_config_.eos_token_id) {
                break;
            }
            
            output_tokens.push_back(next_token);
        }

        // Convert to embeddings
        return prepare_input_embeddings(output_tokens);
    } catch (const std::exception& e) {
        spdlog::error("Generation failed: {}", e.what());
        throw;
    }
}

std::vector<std::vector<float>> LLMInferenceCore::batch_inference(
    const std::vector<std::vector<int>>& batch_tokens,
    const std::unordered_map<std::string, std::string>& parameters) {
    try {
        if (batch_tokens.empty()) {
            return {};
        }

        // Pad sequences to max length in batch
        size_t max_length = 0;
        for (const auto& tokens : batch_tokens) {
            max_length = std::max(max_length, tokens.size());
        }

        std::vector<std::vector<int>> padded_batch;
        for (const auto& tokens : batch_tokens) {
            std::vector<int> padded = tokens;
            padded.resize(max_length, tokenizer_config_.pad_token_id);
            padded_batch.push_back(padded);
        }

        // Run batch inference
        std::vector<std::vector<float>> results;
        for (const auto& tokens : padded_batch) {
            results.push_back(run_inference(tokens, parameters));
        }

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
        std::vector<std::string> results;
        for (const auto& prompt : prompts) {
            std::vector<float> embeddings = generate(prompt, parameters);
            results.push_back(detokenize(embeddings_to_tokens(embeddings)));
        }
        return results;
    } catch (const std::exception& e) {
        spdlog::error("Batch generation failed: {}", e.what());
        throw;
    }
}

void LLMInferenceCore::allocate_memory(size_t size) {
    try {
        if (gpu_memory_) {
            free_memory();
        }

        cudaError_t error = cudaMalloc(&gpu_memory_, size);
        if (error != cudaSuccess) {
            throw std::runtime_error("Failed to allocate GPU memory: " +
                                   std::string(cudaGetErrorString(error)));
        }

        gpu_memory_size_ = size;
        spdlog::info("Allocated {} bytes of GPU memory", size);
    } catch (const std::exception& e) {
        spdlog::error("Memory allocation failed: {}", e.what());
        throw;
    }
}

void LLMInferenceCore::free_memory() {
    try {
        if (gpu_memory_) {
            cudaFree(gpu_memory_);
            gpu_memory_ = nullptr;
            gpu_memory_size_ = 0;
            spdlog::info("Freed GPU memory");
        }
    } catch (const std::exception& e) {
        spdlog::error("Memory free failed: {}", e.what());
        throw;
    }
}

size_t LLMInferenceCore::get_available_memory() const {
    try {
        size_t free, total;
        cudaError_t error = cudaMemGetInfo(&free, &total);
        if (error != cudaSuccess) {
            throw std::runtime_error("Failed to get GPU memory info: " +
                                   std::string(cudaGetErrorString(error)));
        }
        return free;
    } catch (const std::exception& e) {
        spdlog::error("Failed to get available memory: {}", e.what());
        throw;
    }
}

void LLMInferenceCore::set_memory_limit(size_t limit) {
    memory_limit_ = limit;
    check_memory_limits();
}

void LLMInferenceCore::enable_caching(bool enable) {
    cache_enabled_ = enable;
    if (!enable) {
        clear_cache();
    }
}

void LLMInferenceCore::clear_cache() {
    inference_cache_.clear();
}

void LLMInferenceCore::set_batch_size(int size) {
    inference_config_.max_batch_size = size;
    if (is_model_loaded_) {
        configure(inference_config_);
    }
}

void LLMInferenceCore::set_sequence_length(int length) {
    inference_config_.max_sequence_length = length;
    if (is_model_loaded_) {
        configure(inference_config_);
    }
}

void LLMInferenceCore::enable_quantization(bool enable) {
    inference_config_.enable_quantization = enable;
    if (is_model_loaded_) {
        configure(inference_config_);
    }
}

void LLMInferenceCore::set_quantization_type(const std::string& type) {
    inference_config_.quantization_type = type;
    if (is_model_loaded_) {
        configure(inference_config_);
    }
}

LLMInferenceCore::InferenceMetrics LLMInferenceCore::get_metrics() const {
    std::lock_guard<std::mutex> lock(metrics_mutex_);
    return metrics_;
}

void LLMInferenceCore::reset_metrics() {
    std::lock_guard<std::mutex> lock(metrics_mutex_);
    metrics_ = InferenceMetrics{};
}

// Private helper functions

void LLMInferenceCore::initialize_cuda() {
    try {
        cudaError_t error = cudaSetDevice(inference_config_.device_id);
        if (error != cudaSuccess) {
            throw std::runtime_error("Failed to set CUDA device: " +
                                   std::string(cudaGetErrorString(error)));
        }

        cublasStatus_t cublas_status = cublasCreate(&cublas_handle_);
        if (cublas_status != CUBLAS_STATUS_SUCCESS) {
            throw std::runtime_error("Failed to initialize cuBLAS");
        }

        cudnnStatus_t cudnn_status = cudnnCreate(&cudnn_handle_);
        if (cudnn_status != CUDNN_STATUS_SUCCESS) {
            throw std::runtime_error("Failed to initialize cuDNN");
        }

        spdlog::info("CUDA initialized successfully");
    } catch (const std::exception& e) {
        spdlog::error("CUDA initialization failed: {}", e.what());
        throw;
    }
}

void LLMInferenceCore::initialize_tensorrt() {
    try {
        trt_runtime_ = std::unique_ptr<nvinfer1::IRuntime>(
            nvinfer1::createInferRuntime(nullptr));
        if (!trt_runtime_) {
            throw std::runtime_error("Failed to create TensorRT runtime");
        }

        spdlog::info("TensorRT initialized successfully");
    } catch (const std::exception& e) {
        spdlog::error("TensorRT initialization failed: {}", e.what());
        throw;
    }
}

void LLMInferenceCore::initialize_onnx() {
    try {
        Ort::Env env(ORT_LOGGING_LEVEL_WARNING, "llm_inference");
        memory_info_ = std::make_unique<Ort::MemoryInfo>(
            Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault));

        spdlog::info("ONNX Runtime initialized successfully");
    } catch (const std::exception& e) {
        spdlog::error("ONNX Runtime initialization failed: {}", e.what());
        throw;
    }
}

void LLMInferenceCore::initialize_tokenizer() {
    try {
        // Load vocabulary
        std::ifstream vocab_file(tokenizer_config_.vocab_file);
        if (!vocab_file) {
            throw std::runtime_error("Failed to open vocabulary file: " +
                                   tokenizer_config_.vocab_file);
        }

        // Load merges if available
        if (!tokenizer_config_.merges_file.empty()) {
            std::ifstream merges_file(tokenizer_config_.merges_file);
            if (!merges_file) {
                throw std::runtime_error("Failed to open merges file: " +
                                       tokenizer_config_.merges_file);
            }
        }

        // Load special tokens if available
        if (!tokenizer_config_.special_tokens_file.empty()) {
            std::ifstream special_tokens_file(tokenizer_config_.special_tokens_file);
            if (!special_tokens_file) {
                throw std::runtime_error("Failed to open special tokens file: " +
                                       tokenizer_config_.special_tokens_file);
            }
        }

        spdlog::info("Tokenizer initialized successfully");
    } catch (const std::exception& e) {
        spdlog::error("Tokenizer initialization failed: {}", e.what());
        throw;
    }
}

void LLMInferenceCore::validate_configs() {
    if (model_config_.model_path.empty()) {
        throw std::runtime_error("Model path not specified");
    }

    if (model_config_.model_type.empty()) {
        throw std::runtime_error("Model type not specified");
    }

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

void LLMInferenceCore::update_metrics(const InferenceMetrics& new_metrics) {
    std::lock_guard<std::mutex> lock(metrics_mutex_);
    metrics_ = new_metrics;
}

std::string LLMInferenceCore::generate_cache_key(const std::vector<int>& tokens) {
    std::stringstream ss;
    for (int token : tokens) {
        ss << token << ",";
    }
    return ss.str();
}

void LLMInferenceCore::cleanup_cache() {
    if (inference_cache_.size() > max_cache_size_) {
        // Remove oldest entries
        auto now = std::chrono::system_clock::now();
        std::vector<std::string> keys_to_remove;
        
        for (const auto& [key, entry] : inference_cache_) {
            if (now - entry.timestamp > std::chrono::hours(1)) {
                keys_to_remove.push_back(key);
            }
        }

        for (const auto& key : keys_to_remove) {
            inference_cache_.erase(key);
        }
    }
}

void LLMInferenceCore::check_memory_limits() {
    if (memory_limit_ > 0) {
        size_t available = get_available_memory();
        if (available < memory_limit_) {
            spdlog::warn("Available memory ({}) below limit ({})",
                        available, memory_limit_);
        }
    }
}

} // namespace dream
} // namespace cogniware 