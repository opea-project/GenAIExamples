#include "llm_inference/inference_engine.h"
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

InferenceEngine::InferenceEngine(const InferenceEngineConfig& config)
    : config_(config), is_model_loaded_(false) {
    try {
        initialize_cuda();
        initialize_tensorrt();
        initialize_onnx();
        validate_config();

        ModelCacheConfig cache_config;
        cache_config.max_cache_size = config.cache_size;
        cache_config.max_models = 1; // Only cache the current model
        cache_config.enable_quantization = config.use_fp16 || config.use_int8;
        cache_config.quantization_type = config.use_fp16 ? "fp16" : (config.use_int8 ? "int8" : "");
        cache_config.enable_fp16 = config.use_fp16;
        cache_config.enable_int8 = config.use_int8;
        cache_config.enable_dynamic_shapes = config.use_dynamic_shapes;
        cache_config.enable_optimized_kernels = config.use_optimized_kernels;
        cache_config.enable_custom_kernels = config.use_custom_kernels;
        cache_config.enable_fused_operations = config.use_fused_operations;
        cache_config.enable_attention_cache = config.enable_attention_cache;
        cache_config.enable_kv_cache = config.enable_kv_cache;
        cache_config.num_attention_heads = config.num_attention_heads;
        cache_config.hidden_size = config.hidden_size;
        cache_config.num_layers = config.num_layers;
        cache_config.dropout = config.dropout;

        model_cache_ = std::make_unique<ModelCache>(cache_config);
        spdlog::info("InferenceEngine initialized successfully");
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize InferenceEngine: {}", e.what());
        throw;
    }
}

InferenceEngine::~InferenceEngine() {
    try {
        cleanup();
    } catch (const std::exception& e) {
        spdlog::error("Error during InferenceEngine destruction: {}", e.what());
    }
}

void InferenceEngine::load_model(const std::string& model_path) {
    try {
        std::lock_guard<std::mutex> lock(mutex_);

        if (is_model_loaded_) {
            spdlog::warn("Model already loaded");
            return;
        }

        // Determine model type from file extension
        std::string model_type;
        if (model_path.ends_with(".engine")) {
            model_type = "tensorrt";
        } else if (model_path.ends_with(".onnx")) {
            model_type = "onnx";
        } else {
            throw std::runtime_error("Unsupported model format: " + model_path);
        }

        // Load model into cache
        model_cache_->load_model(model_path, model_type);
        current_model_path_ = model_path;
        is_model_loaded_ = true;

        spdlog::info("Model loaded successfully: {}", model_path);
    } catch (const std::exception& e) {
        spdlog::error("Failed to load model: {}", e.what());
        throw;
    }
}

void InferenceEngine::unload_model() {
    try {
        std::lock_guard<std::mutex> lock(mutex_);

        if (!is_model_loaded_) {
            return;
        }

        model_cache_->unload_model(current_model_path_);
        current_model_path_.clear();
        is_model_loaded_ = false;

        spdlog::info("Model unloaded successfully");
    } catch (const std::exception& e) {
        spdlog::error("Failed to unload model: {}", e.what());
        throw;
    }
}

bool InferenceEngine::is_model_loaded() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return is_model_loaded_;
}

std::vector<float> InferenceEngine::run_inference(
    const std::vector<int>& input_tokens,
    const std::unordered_map<std::string, std::string>& parameters) {
    try {
        std::lock_guard<std::mutex> lock(mutex_);

        if (!is_model_loaded_) {
            throw std::runtime_error("Model not loaded");
        }

        // Prepare input tensors
        prepare_input_tensors(input_tokens);

        // Run inference
        auto* model = model_cache_->get_model(current_model_path_);
        if (!model) {
            throw std::runtime_error("Model not found in cache");
        }

        if (model->model_type == "tensorrt") {
            run_tensorrt_inference();
        } else if (model->model_type == "onnx") {
            run_onnx_inference();
        }

        // Process output tensors
        process_output_tensors();

        return std::vector<float>(); // Placeholder for actual output
    } catch (const std::exception& e) {
        spdlog::error("Inference failed: {}", e.what());
        throw;
    }
}

std::vector<std::vector<float>> InferenceEngine::batch_inference(
    const std::vector<std::vector<int>>& batch_tokens,
    const std::unordered_map<std::string, std::string>& parameters) {
    try {
        std::lock_guard<std::mutex> lock(mutex_);

        if (!is_model_loaded_) {
            throw std::runtime_error("Model not loaded");
        }

        if (batch_tokens.size() > config_.max_batch_size) {
            throw std::runtime_error("Batch size exceeds maximum allowed");
        }

        // Prepare batch input tensors
        prepare_batch_input_tensors(batch_tokens);

        // Run batch inference
        auto* model = model_cache_->get_model(current_model_path_);
        if (!model) {
            throw std::runtime_error("Model not found in cache");
        }

        if (model->model_type == "tensorrt") {
            run_tensorrt_inference();
        } else if (model->model_type == "onnx") {
            run_onnx_inference();
        }

        // Process batch output tensors
        process_batch_output_tensors();

        return std::vector<std::vector<float>>(); // Placeholder for actual output
    } catch (const std::exception& e) {
        spdlog::error("Batch inference failed: {}", e.what());
        throw;
    }
}

void InferenceEngine::set_memory_limit(size_t limit) {
    std::lock_guard<std::mutex> lock(mutex_);
    model_cache_->set_max_cache_size(limit);
}

size_t InferenceEngine::get_available_memory() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return model_cache_->get_current_cache_size();
}

void InferenceEngine::allocate_memory(size_t size) {
    try {
        std::lock_guard<std::mutex> lock(mutex_);
        
        // Check if we have enough memory
        size_t available = get_available_memory();
        if (available < size) {
            throw std::runtime_error("Not enough memory available");
        }

        // Allocate GPU memory
        void* gpu_memory;
        cudaError_t error = cudaMalloc(&gpu_memory, size);
        if (error != cudaSuccess) {
            throw std::runtime_error("Failed to allocate GPU memory: " + std::string(cudaGetErrorString(error)));
        }

        // Track allocation
        allocated_memory_.push_back({gpu_memory, size});
        spdlog::info("Allocated {} bytes of GPU memory", size);
    } catch (const std::exception& e) {
        spdlog::error("Memory allocation failed: {}", e.what());
        throw;
    }
}

void InferenceEngine::deallocate_memory(size_t size) {
    try {
        std::lock_guard<std::mutex> lock(mutex_);
        
        // Find and deallocate the most recently allocated memory of the requested size
        auto it = std::find_if(allocated_memory_.rbegin(), allocated_memory_.rend(),
            [size](const auto& mem) { return mem.second == size; });
            
        if (it != allocated_memory_.rend()) {
            cudaError_t error = cudaFree(it->first);
            if (error != cudaSuccess) {
                throw std::runtime_error("Failed to deallocate GPU memory: " + std::string(cudaGetErrorString(error)));
            }
            
            allocated_memory_.erase(std::next(it).base());
            spdlog::info("Deallocated {} bytes of GPU memory", size);
        } else {
            throw std::runtime_error("No memory block of size " + std::to_string(size) + " found to deallocate");
        }
    } catch (const std::exception& e) {
        spdlog::error("Memory deallocation failed: {}", e.what());
        throw;
    }
}

// Performance optimization methods

void InferenceEngine::set_batch_size(int size) {
    std::lock_guard<std::mutex> lock(mutex_);
    config_.max_batch_size = size;
}

void InferenceEngine::set_sequence_length(int length) {
    std::lock_guard<std::mutex> lock(mutex_);
    config_.max_sequence_length = length;
}

void InferenceEngine::enable_quantization(bool enable) {
    std::lock_guard<std::mutex> lock(mutex_);
    config_.use_fp16 = enable;
    config_.use_int8 = false;
    model_cache_->enable_quantization(enable);
}

void InferenceEngine::set_quantization_type(const std::string& type) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (type == "fp16") {
        config_.use_fp16 = true;
        config_.use_int8 = false;
    } else if (type == "int8") {
        config_.use_fp16 = false;
        config_.use_int8 = true;
    }
    model_cache_->set_quantization_type(type);
}

void InferenceEngine::enable_cache(bool enable) {
    std::lock_guard<std::mutex> lock(mutex_);
    config_.enable_cache = enable;
}

void InferenceEngine::set_cache_size(size_t size) {
    std::lock_guard<std::mutex> lock(mutex_);
    config_.cache_size = size;
    model_cache_->set_max_cache_size(size);
}

void InferenceEngine::enable_attention_cache(bool enable) {
    std::lock_guard<std::mutex> lock(mutex_);
    config_.enable_attention_cache = enable;
    model_cache_->enable_attention_cache(enable);
}

void InferenceEngine::enable_kv_cache(bool enable) {
    std::lock_guard<std::mutex> lock(mutex_);
    config_.enable_kv_cache = enable;
    model_cache_->enable_kv_cache(enable);
}

// Private helper methods

void InferenceEngine::initialize_cuda() {
    cudaError_t error = cudaSetDevice(0);
    if (error != cudaSuccess) {
        throw std::runtime_error("Failed to initialize CUDA: " + std::string(cudaGetErrorString(error)));
    }
}

void InferenceEngine::initialize_tensorrt() {
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

void InferenceEngine::initialize_onnx() {
    Ort::Env env(ORT_LOGGING_LEVEL_WARNING, "inference_engine");
    Ort::SessionOptions session_options;
    session_options.SetIntraOpNumThreads(1);
    session_options.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_ALL);
}

void InferenceEngine::validate_config() {
    if (config_.max_batch_size <= 0) {
        throw std::runtime_error("Invalid batch size");
    }
    if (config_.max_sequence_length <= 0) {
        throw std::runtime_error("Invalid sequence length");
    }
    if (config_.temperature <= 0.0f) {
        throw std::runtime_error("Invalid temperature");
    }
    if (config_.top_p <= 0.0f || config_.top_p > 1.0f) {
        throw std::runtime_error("Invalid top_p value");
    }
    if (config_.top_k <= 0) {
        throw std::runtime_error("Invalid top_k value");
    }
}

void InferenceEngine::prepare_input_tensors(const std::vector<int>& input_tokens) {
    try {
        auto* model = model_cache_->get_model(current_model_path_);
        if (!model) {
            throw std::runtime_error("Model not found in cache");
        }

        if (model->model_type == "tensorrt") {
            // Prepare TensorRT input tensors
            nvinfer1::Dims dims;
            dims.nbDims = 2;
            dims.d[0] = 1; // batch size
            dims.d[1] = input_tokens.size();

            // Create input tensor
            auto input_tensor = std::make_unique<float[]>(input_tokens.size());
            for (size_t i = 0; i < input_tokens.size(); ++i) {
                input_tensor[i] = static_cast<float>(input_tokens[i]);
            }

            // Allocate GPU memory
            void* gpu_input;
            cudaMalloc(&gpu_input, input_tokens.size() * sizeof(float));
            cudaMemcpy(gpu_input, input_tensor.get(), input_tokens.size() * sizeof(float), cudaMemcpyHostToDevice);

            // Store tensor info for inference
            input_tensors_["input_ids"] = {gpu_input, dims};
        } else if (model->model_type == "onnx") {
            // Prepare ONNX input tensors
            std::vector<int64_t> shape = {1, static_cast<int64_t>(input_tokens.size())};
            auto memory_info = Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault);
            
            // Create input tensor
            auto input_tensor = Ort::Value::CreateTensor<int64_t>(
                memory_info,
                const_cast<int64_t*>(reinterpret_cast<const int64_t*>(input_tokens.data())),
                input_tokens.size(),
                shape.data(),
                shape.size()
            );

            // Store tensor info for inference
            onnx_input_tensors_["input_ids"] = std::move(input_tensor);
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to prepare input tensors: {}", e.what());
        throw;
    }
}

void InferenceEngine::prepare_batch_input_tensors(const std::vector<std::vector<int>>& batch_tokens) {
    try {
        auto* model = model_cache_->get_model(current_model_path_);
        if (!model) {
            throw std::runtime_error("Model not found in cache");
        }

        if (model->model_type == "tensorrt") {
            // Prepare TensorRT batch input tensors
            nvinfer1::Dims dims;
            dims.nbDims = 2;
            dims.d[0] = batch_tokens.size();
            dims.d[1] = config_.max_sequence_length;

            // Create padded input tensor
            auto input_tensor = std::make_unique<float[]>(batch_tokens.size() * config_.max_sequence_length);
            for (size_t i = 0; i < batch_tokens.size(); ++i) {
                for (size_t j = 0; j < batch_tokens[i].size() && j < config_.max_sequence_length; ++j) {
                    input_tensor[i * config_.max_sequence_length + j] = static_cast<float>(batch_tokens[i][j]);
                }
                // Pad remaining positions
                for (size_t j = batch_tokens[i].size(); j < config_.max_sequence_length; ++j) {
                    input_tensor[i * config_.max_sequence_length + j] = 0.0f;
                }
            }

            // Allocate GPU memory
            void* gpu_input;
            cudaMalloc(&gpu_input, batch_tokens.size() * config_.max_sequence_length * sizeof(float));
            cudaMemcpy(gpu_input, input_tensor.get(), 
                      batch_tokens.size() * config_.max_sequence_length * sizeof(float), 
                      cudaMemcpyHostToDevice);

            // Store tensor info for inference
            input_tensors_["input_ids"] = {gpu_input, dims};
        } else if (model->model_type == "onnx") {
            // Prepare ONNX batch input tensors
            std::vector<int64_t> shape = {static_cast<int64_t>(batch_tokens.size()), 
                                        static_cast<int64_t>(config_.max_sequence_length)};
            auto memory_info = Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault);
            
            // Create padded input tensor
            std::vector<int64_t> padded_tokens(batch_tokens.size() * config_.max_sequence_length);
            for (size_t i = 0; i < batch_tokens.size(); ++i) {
                for (size_t j = 0; j < batch_tokens[i].size() && j < config_.max_sequence_length; ++j) {
                    padded_tokens[i * config_.max_sequence_length + j] = batch_tokens[i][j];
                }
                // Pad remaining positions
                for (size_t j = batch_tokens[i].size(); j < config_.max_sequence_length; ++j) {
                    padded_tokens[i * config_.max_sequence_length + j] = 0;
                }
            }

            // Create input tensor
            auto input_tensor = Ort::Value::CreateTensor<int64_t>(
                memory_info,
                padded_tokens.data(),
                padded_tokens.size(),
                shape.data(),
                shape.size()
            );

            // Store tensor info for inference
            onnx_input_tensors_["input_ids"] = std::move(input_tensor);
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to prepare batch input tensors: {}", e.what());
        throw;
    }
}

void InferenceEngine::run_tensorrt_inference() {
    try {
        auto* model = model_cache_->get_model(current_model_path_);
        if (!model || !model->trt_engine) {
            throw std::runtime_error("Invalid TensorRT model");
        }

        // Create execution context
        auto context = model->trt_engine->createExecutionContext();
        if (!context) {
            throw std::runtime_error("Failed to create TensorRT execution context");
        }

        // Set input dimensions
        for (const auto& [name, tensor] : input_tensors_) {
            context->setBindingDimensions(0, tensor.dims);
        }

        // Prepare output buffer
        void* gpu_output;
        size_t output_size = config_.max_sequence_length * config_.hidden_size * sizeof(float);
        cudaMalloc(&gpu_output, output_size);

        // Run inference
        void* bindings[] = {input_tensors_["input_ids"].data, gpu_output};
        bool status = context->executeV2(bindings);
        if (!status) {
            throw std::runtime_error("TensorRT inference failed");
        }

        // Copy output to host
        auto host_output = std::make_unique<float[]>(output_size / sizeof(float));
        cudaMemcpy(host_output.get(), gpu_output, output_size, cudaMemcpyDeviceToHost);

        // Store output for processing
        output_tensors_["logits"] = std::move(host_output);

        // Cleanup
        cudaFree(gpu_output);
        context->destroy();
    } catch (const std::exception& e) {
        spdlog::error("TensorRT inference failed: {}", e.what());
        throw;
    }
}

void InferenceEngine::run_onnx_inference() {
    try {
        auto* model = model_cache_->get_model(current_model_path_);
        if (!model || !model->onnx_session) {
            throw std::runtime_error("Invalid ONNX model");
        }

        // Prepare input names
        std::vector<const char*> input_names = {"input_ids"};
        std::vector<const char*> output_names = {"logits"};

        // Run inference
        auto output_tensors = model->onnx_session->Run(
            Ort::RunOptions{nullptr},
            input_names.data(),
            &onnx_input_tensors_["input_ids"],
            1,
            output_names.data(),
            1
        );

        // Store output for processing
        onnx_output_tensors_["logits"] = std::move(output_tensors[0]);
    } catch (const std::exception& e) {
        spdlog::error("ONNX inference failed: {}", e.what());
        throw;
    }
}

void InferenceEngine::process_output_tensors() {
    try {
        auto* model = model_cache_->get_model(current_model_path_);
        if (!model) {
            throw std::runtime_error("Model not found in cache");
        }

        if (model->model_type == "tensorrt") {
            // Process TensorRT output
            auto* logits = output_tensors_["logits"].get();
            size_t vocab_size = config_.hidden_size;
            size_t sequence_length = config_.max_sequence_length;

            // Apply temperature and top-k/top-p sampling
            std::vector<float> probs(vocab_size);
            for (size_t i = 0; i < vocab_size; ++i) {
                probs[i] = logits[i] / config_.temperature;
            }

            // Apply softmax
            float max_logit = *std::max_element(probs.begin(), probs.end());
            float sum_exp = 0.0f;
            for (float& prob : probs) {
                prob = std::exp(prob - max_logit);
                sum_exp += prob;
            }
            for (float& prob : probs) {
                prob /= sum_exp;
            }

            // Apply top-k
            if (config_.top_k > 0) {
                std::vector<std::pair<float, int>> prob_indices;
                for (size_t i = 0; i < vocab_size; ++i) {
                    prob_indices.emplace_back(probs[i], i);
                }
                std::partial_sort(prob_indices.begin(), 
                                prob_indices.begin() + config_.top_k,
                                prob_indices.end(),
                                std::greater<std::pair<float, int>>());
                
                for (size_t i = config_.top_k; i < vocab_size; ++i) {
                    probs[prob_indices[i].second] = 0.0f;
                }
            }

            // Apply top-p
            if (config_.top_p < 1.0f) {
                std::vector<std::pair<float, int>> prob_indices;
                for (size_t i = 0; i < vocab_size; ++i) {
                    prob_indices.emplace_back(probs[i], i);
                }
                std::sort(prob_indices.begin(), prob_indices.end(),
                         std::greater<std::pair<float, int>>());

                float cumsum = 0.0f;
                for (size_t i = 0; i < vocab_size; ++i) {
                    cumsum += prob_indices[i].first;
                    if (cumsum > config_.top_p) {
                        for (size_t j = i + 1; j < vocab_size; ++j) {
                            probs[prob_indices[j].second] = 0.0f;
                        }
                        break;
                    }
                }
            }

            // Store processed output
            processed_output_ = std::move(probs);
        } else if (model->model_type == "onnx") {
            // Process ONNX output
            auto& logits_tensor = onnx_output_tensors_["logits"];
            auto* logits = logits_tensor.GetTensorData<float>();
            size_t vocab_size = config_.hidden_size;

            // Apply temperature and sampling
            std::vector<float> probs(vocab_size);
            for (size_t i = 0; i < vocab_size; ++i) {
                probs[i] = logits[i] / config_.temperature;
            }

            // Apply softmax and sampling (same as TensorRT)
            float max_logit = *std::max_element(probs.begin(), probs.end());
            float sum_exp = 0.0f;
            for (float& prob : probs) {
                prob = std::exp(prob - max_logit);
                sum_exp += prob;
            }
            for (float& prob : probs) {
                prob /= sum_exp;
            }

            // Apply top-k and top-p (same as TensorRT)
            if (config_.top_k > 0) {
                std::vector<std::pair<float, int>> prob_indices;
                for (size_t i = 0; i < vocab_size; ++i) {
                    prob_indices.emplace_back(probs[i], i);
                }
                std::partial_sort(prob_indices.begin(), 
                                prob_indices.begin() + config_.top_k,
                                prob_indices.end(),
                                std::greater<std::pair<float, int>>());
                
                for (size_t i = config_.top_k; i < vocab_size; ++i) {
                    probs[prob_indices[i].second] = 0.0f;
                }
            }

            if (config_.top_p < 1.0f) {
                std::vector<std::pair<float, int>> prob_indices;
                for (size_t i = 0; i < vocab_size; ++i) {
                    prob_indices.emplace_back(probs[i], i);
                }
                std::sort(prob_indices.begin(), prob_indices.end(),
                         std::greater<std::pair<float, int>>());

                float cumsum = 0.0f;
                for (size_t i = 0; i < vocab_size; ++i) {
                    cumsum += prob_indices[i].first;
                    if (cumsum > config_.top_p) {
                        for (size_t j = i + 1; j < vocab_size; ++j) {
                            probs[prob_indices[j].second] = 0.0f;
                        }
                        break;
                    }
                }
            }

            // Store processed output
            processed_output_ = std::move(probs);
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to process output tensors: {}", e.what());
        throw;
    }
}

void InferenceEngine::process_batch_output_tensors() {
    try {
        auto* model = model_cache_->get_model(current_model_path_);
        if (!model) {
            throw std::runtime_error("Model not found in cache");
        }

        if (model->model_type == "tensorrt") {
            // Process TensorRT batch output
            auto* logits = output_tensors_["logits"].get();
            size_t batch_size = config_.max_batch_size;
            size_t vocab_size = config_.hidden_size;
            size_t sequence_length = config_.max_sequence_length;

            // Process each sequence in the batch
            std::vector<std::vector<float>> batch_probs(batch_size);
            for (size_t b = 0; b < batch_size; ++b) {
                std::vector<float> probs(vocab_size);
                for (size_t i = 0; i < vocab_size; ++i) {
                    probs[i] = logits[b * vocab_size + i] / config_.temperature;
                }

                // Apply softmax and sampling (same as single sequence)
                float max_logit = *std::max_element(probs.begin(), probs.end());
                float sum_exp = 0.0f;
                for (float& prob : probs) {
                    prob = std::exp(prob - max_logit);
                    sum_exp += prob;
                }
                for (float& prob : probs) {
                    prob /= sum_exp;
                }

                // Apply top-k and top-p
                if (config_.top_k > 0) {
                    std::vector<std::pair<float, int>> prob_indices;
                    for (size_t i = 0; i < vocab_size; ++i) {
                        prob_indices.emplace_back(probs[i], i);
                    }
                    std::partial_sort(prob_indices.begin(), 
                                    prob_indices.begin() + config_.top_k,
                                    prob_indices.end(),
                                    std::greater<std::pair<float, int>>());
                    
                    for (size_t i = config_.top_k; i < vocab_size; ++i) {
                        probs[prob_indices[i].second] = 0.0f;
                    }
                }

                if (config_.top_p < 1.0f) {
                    std::vector<std::pair<float, int>> prob_indices;
                    for (size_t i = 0; i < vocab_size; ++i) {
                        prob_indices.emplace_back(probs[i], i);
                    }
                    std::sort(prob_indices.begin(), prob_indices.end(),
                             std::greater<std::pair<float, int>>());

                    float cumsum = 0.0f;
                    for (size_t i = 0; i < vocab_size; ++i) {
                        cumsum += prob_indices[i].first;
                        if (cumsum > config_.top_p) {
                            for (size_t j = i + 1; j < vocab_size; ++j) {
                                probs[prob_indices[j].second] = 0.0f;
                            }
                            break;
                        }
                    }
                }

                batch_probs[b] = std::move(probs);
            }

            // Store processed batch output
            processed_batch_output_ = std::move(batch_probs);
        } else if (model->model_type == "onnx") {
            // Process ONNX batch output
            auto& logits_tensor = onnx_output_tensors_["logits"];
            auto* logits = logits_tensor.GetTensorData<float>();
            size_t batch_size = config_.max_batch_size;
            size_t vocab_size = config_.hidden_size;

            // Process each sequence in the batch (same as TensorRT)
            std::vector<std::vector<float>> batch_probs(batch_size);
            for (size_t b = 0; b < batch_size; ++b) {
                std::vector<float> probs(vocab_size);
                for (size_t i = 0; i < vocab_size; ++i) {
                    probs[i] = logits[b * vocab_size + i] / config_.temperature;
                }

                // Apply softmax and sampling
                float max_logit = *std::max_element(probs.begin(), probs.end());
                float sum_exp = 0.0f;
                for (float& prob : probs) {
                    prob = std::exp(prob - max_logit);
                    sum_exp += prob;
                }
                for (float& prob : probs) {
                    prob /= sum_exp;
                }

                // Apply top-k and top-p
                if (config_.top_k > 0) {
                    std::vector<std::pair<float, int>> prob_indices;
                    for (size_t i = 0; i < vocab_size; ++i) {
                        prob_indices.emplace_back(probs[i], i);
                    }
                    std::partial_sort(prob_indices.begin(), 
                                    prob_indices.begin() + config_.top_k,
                                    prob_indices.end(),
                                    std::greater<std::pair<float, int>>());
                    
                    for (size_t i = config_.top_k; i < vocab_size; ++i) {
                        probs[prob_indices[i].second] = 0.0f;
                    }
                }

                if (config_.top_p < 1.0f) {
                    std::vector<std::pair<float, int>> prob_indices;
                    for (size_t i = 0; i < vocab_size; ++i) {
                        prob_indices.emplace_back(probs[i], i);
                    }
                    std::sort(prob_indices.begin(), prob_indices.end(),
                             std::greater<std::pair<float, int>>());

                    float cumsum = 0.0f;
                    for (size_t i = 0; i < vocab_size; ++i) {
                        cumsum += prob_indices[i].first;
                        if (cumsum > config_.top_p) {
                            for (size_t j = i + 1; j < vocab_size; ++j) {
                                probs[prob_indices[j].second] = 0.0f;
                            }
                            break;
                        }
                    }
                }

                batch_probs[b] = std::move(probs);
            }

            // Store processed batch output
            processed_batch_output_ = std::move(batch_probs);
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to process batch output tensors: {}", e.what());
        throw;
    }
}

void InferenceEngine::cleanup() {
    try {
        std::lock_guard<std::mutex> lock(mutex_);

        // Deallocate all GPU memory
        for (const auto& [ptr, size] : allocated_memory_) {
            cudaFree(ptr);
        }
        allocated_memory_.clear();

        // Clear tensor storage
        for (const auto& [name, tensor] : input_tensors_) {
            cudaFree(tensor.data);
        }
        input_tensors_.clear();
        output_tensors_.clear();
        onnx_input_tensors_.clear();
        onnx_output_tensors_.clear();
        processed_output_.clear();
        processed_batch_output_.clear();

        // Unload model if loaded
        if (is_model_loaded_) {
            unload_model();
        }

        // Reset model cache
        model_cache_.reset();

        spdlog::info("InferenceEngine cleanup completed");
    } catch (const std::exception& e) {
        spdlog::error("Error during cleanup: {}", e.what());
        throw;
    }
}

} // namespace llm_inference
} // namespace cogniware 