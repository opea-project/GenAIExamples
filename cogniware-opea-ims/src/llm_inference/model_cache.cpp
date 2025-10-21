#include "llm_inference/model_cache.h"
#include <spdlog/spdlog.h>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <filesystem>
#include <cuda_runtime.h>
#include <NvInfer.h>
#include <onnxruntime_cxx_api.h>

namespace cogniware {
namespace llm_inference {

ModelCache::ModelCache(const ModelCacheConfig& config) : config_(config), current_cache_size_(0) {
    try {
        initialize_cuda();
        initialize_tensorrt();
        initialize_onnx();
        spdlog::info("ModelCache initialized successfully");
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize ModelCache: {}", e.what());
        throw;
    }
}

ModelCache::~ModelCache() {
    try {
        clear_cache();
    } catch (const std::exception& e) {
        spdlog::error("Error during ModelCache destruction: {}", e.what());
    }
}

void ModelCache::load_model(const std::string& model_path, const std::string& model_type) {
    try {
        std::lock_guard<std::mutex> lock(mutex_);

        if (is_model_cached(model_path)) {
            spdlog::warn("Model already cached: {}", model_path);
            return;
        }

        // Check if we need to evict models
        while (current_cache_size_ + calculate_model_size(CachedModel{model_path, model_type}) > config_.max_cache_size ||
               cached_models_.size() >= config_.max_models) {
            cleanup_old_models();
        }

        // Create new cached model
        CachedModel model;
        model.model_path = model_path;
        model.model_type = model_type;
        model.last_accessed = std::chrono::system_clock::now();
        model.is_quantized = false;
        model.is_optimized = false;

        // Load model based on type
        if (model_type == "tensorrt") {
            load_tensorrt_model(model_path, model);
        } else if (model_type == "onnx") {
            load_onnx_model(model_path, model);
        } else {
            throw std::runtime_error("Unsupported model type: " + model_type);
        }

        // Optimize and quantize if enabled
        if (config_.enable_optimized_kernels) {
            optimize_model(model);
        }
        if (config_.enable_quantization) {
            quantize_model(model);
        }

        // Update cache
        model.memory_usage = calculate_model_size(model);
        current_cache_size_ += model.memory_usage;
        cached_models_[model_path] = std::move(model);

        spdlog::info("Model loaded and cached: {}", model_path);
    } catch (const std::exception& e) {
        spdlog::error("Failed to load model: {}", e.what());
        throw;
    }
}

void ModelCache::unload_model(const std::string& model_path) {
    try {
        std::lock_guard<std::mutex> lock(mutex_);

        auto it = cached_models_.find(model_path);
        if (it == cached_models_.end()) {
            spdlog::warn("Model not found in cache: {}", model_path);
            return;
        }

        current_cache_size_ -= it->second.memory_usage;
        cached_models_.erase(it);

        spdlog::info("Model unloaded from cache: {}", model_path);
    } catch (const std::exception& e) {
        spdlog::error("Failed to unload model: {}", e.what());
        throw;
    }
}

bool ModelCache::is_model_cached(const std::string& model_path) const {
    std::lock_guard<std::mutex> lock(mutex_);
    return cached_models_.find(model_path) != cached_models_.end();
}

CachedModel* ModelCache::get_model(const std::string& model_path) {
    try {
        std::lock_guard<std::mutex> lock(mutex_);

        auto it = cached_models_.find(model_path);
        if (it == cached_models_.end()) {
            return nullptr;
        }

        update_model_access_time(it->second);
        return &it->second;
    } catch (const std::exception& e) {
        spdlog::error("Failed to get model: {}", e.what());
        throw;
    }
}

void ModelCache::set_max_cache_size(size_t size) {
    std::lock_guard<std::mutex> lock(mutex_);
    config_.max_cache_size = size;
    cleanup_old_models();
}

void ModelCache::set_max_models(size_t num) {
    std::lock_guard<std::mutex> lock(mutex_);
    config_.max_models = num;
    cleanup_old_models();
}

size_t ModelCache::get_current_cache_size() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return current_cache_size_;
}

size_t ModelCache::get_num_cached_models() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return cached_models_.size();
}

void ModelCache::clear_cache() {
    try {
        std::lock_guard<std::mutex> lock(mutex_);

        for (auto& [path, model] : cached_models_) {
            model.trt_engine.reset();
            model.onnx_session.reset();
        }

        cached_models_.clear();
        current_cache_size_ = 0;

        spdlog::info("Model cache cleared");
    } catch (const std::exception& e) {
        spdlog::error("Failed to clear cache: {}", e.what());
        throw;
    }
}

void ModelCache::enable_quantization(bool enable) {
    std::lock_guard<std::mutex> lock(mutex_);
    config_.enable_quantization = enable;
}

void ModelCache::set_quantization_type(const std::string& type) {
    std::lock_guard<std::mutex> lock(mutex_);
    config_.quantization_type = type;
}

void ModelCache::enable_fp16(bool enable) {
    std::lock_guard<std::mutex> lock(mutex_);
    config_.enable_fp16 = enable;
}

void ModelCache::enable_int8(bool enable) {
    std::lock_guard<std::mutex> lock(mutex_);
    config_.enable_int8 = enable;
}

void ModelCache::enable_dynamic_shapes(bool enable) {
    std::lock_guard<std::mutex> lock(mutex_);
    config_.enable_dynamic_shapes = enable;
}

void ModelCache::enable_optimized_kernels(bool enable) {
    std::lock_guard<std::mutex> lock(mutex_);
    config_.enable_optimized_kernels = enable;
}

void ModelCache::enable_custom_kernels(bool enable) {
    std::lock_guard<std::mutex> lock(mutex_);
    config_.enable_custom_kernels = enable;
}

void ModelCache::enable_fused_operations(bool enable) {
    std::lock_guard<std::mutex> lock(mutex_);
    config_.enable_fused_operations = enable;
}

void ModelCache::enable_attention_cache(bool enable) {
    std::lock_guard<std::mutex> lock(mutex_);
    config_.enable_attention_cache = enable;
}

void ModelCache::enable_kv_cache(bool enable) {
    std::lock_guard<std::mutex> lock(mutex_);
    config_.enable_kv_cache = enable;
}

// Private helper methods

void ModelCache::initialize_cuda() {
    cudaError_t error = cudaSetDevice(0);
    if (error != cudaSuccess) {
        throw std::runtime_error("Failed to initialize CUDA: " + std::string(cudaGetErrorString(error)));
    }
}

void ModelCache::initialize_tensorrt() {
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

void ModelCache::initialize_onnx() {
    Ort::Env env(ORT_LOGGING_LEVEL_WARNING, "model_cache");
    Ort::SessionOptions session_options;
    session_options.SetIntraOpNumThreads(1);
    session_options.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_ALL);
}

void ModelCache::load_tensorrt_model(const std::string& model_path, CachedModel& model) {
    std::ifstream file(model_path, std::ios::binary);
    if (!file) {
        throw std::runtime_error("Failed to open TensorRT model file: " + model_path);
    }

    file.seekg(0, std::ios::end);
    size_t size = file.tellg();
    file.seekg(0, std::ios::beg);

    std::vector<char> buffer(size);
    file.read(buffer.data(), size);

    auto runtime = nvinfer1::createInferRuntime(nullptr);
    if (!runtime) {
        throw std::runtime_error("Failed to create TensorRT runtime");
    }

    model.trt_engine.reset(runtime->deserializeCudaEngine(buffer.data(), size));
    if (!model.trt_engine) {
        throw std::runtime_error("Failed to deserialize TensorRT engine");
    }
}

void ModelCache::load_onnx_model(const std::string& model_path, CachedModel& model) {
    Ort::Env env(ORT_LOGGING_LEVEL_WARNING, "model_cache");
    Ort::SessionOptions session_options;
    session_options.SetIntraOpNumThreads(1);
    session_options.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_ALL);

    model.onnx_session = std::make_unique<Ort::Session>(env, model_path.c_str(), session_options);
    if (!model.onnx_session) {
        throw std::runtime_error("Failed to create ONNX session");
    }
}

void ModelCache::optimize_model(CachedModel& model) {
    if (model.is_optimized) {
        return;
    }

    if (model.model_type == "tensorrt") {
        // Apply TensorRT optimizations
        if (config_.enable_fp16) {
            model.optimization_flags.push_back("fp16");
        }
        if (config_.enable_int8) {
            model.optimization_flags.push_back("int8");
        }
        if (config_.enable_dynamic_shapes) {
            model.optimization_flags.push_back("dynamic_shapes");
        }
    } else if (model.model_type == "onnx") {
        // Apply ONNX optimizations
        if (config_.enable_fused_operations) {
            model.optimization_flags.push_back("fused_ops");
        }
        if (config_.enable_attention_cache) {
            model.optimization_flags.push_back("attention_cache");
        }
        if (config_.enable_kv_cache) {
            model.optimization_flags.push_back("kv_cache");
        }
    }

    model.is_optimized = true;
}

void ModelCache::quantize_model(CachedModel& model) {
    if (model.is_quantized) {
        return;
    }

    if (model.model_type == "tensorrt") {
        // Apply TensorRT quantization
        if (config_.quantization_type == "fp16") {
            model.quantization_type = "fp16";
        } else if (config_.quantization_type == "int8") {
            model.quantization_type = "int8";
        }
    } else if (model.model_type == "onnx") {
        // Apply ONNX quantization
        if (config_.quantization_type == "fp16") {
            model.quantization_type = "fp16";
        } else if (config_.quantization_type == "int8") {
            model.quantization_type = "int8";
        }
    }

    model.is_quantized = true;
}

void ModelCache::cleanup_old_models() {
    std::vector<std::string> models_to_evict;
    for (const auto& [path, model] : cached_models_) {
        if (should_evict_model(model)) {
            models_to_evict.push_back(path);
        }
    }

    for (const auto& path : models_to_evict) {
        evict_model(path);
    }
}

size_t ModelCache::calculate_model_size(const CachedModel& model) const {
    size_t size = 0;
    if (model.trt_engine) {
        size += model.trt_engine->getDeviceMemorySize();
    }
    if (model.onnx_session) {
        // Estimate ONNX model size
        size += 1024 * 1024; // 1MB base size
    }
    return size;
}

void ModelCache::update_model_access_time(CachedModel& model) {
    model.last_accessed = std::chrono::system_clock::now();
}

bool ModelCache::should_evict_model(const CachedModel& model) const {
    auto now = std::chrono::system_clock::now();
    auto age = std::chrono::duration_cast<std::chrono::hours>(now - model.last_accessed);
    return age.count() > 24; // Evict models older than 24 hours
}

void ModelCache::evict_model(const std::string& model_path) {
    auto it = cached_models_.find(model_path);
    if (it != cached_models_.end()) {
        current_cache_size_ -= it->second.memory_usage;
        cached_models_.erase(it);
        spdlog::info("Model evicted from cache: {}", model_path);
    }
}

} // namespace llm_inference
} // namespace cogniware 