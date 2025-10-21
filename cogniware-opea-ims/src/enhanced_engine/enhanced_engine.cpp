#include "enhanced_engine.h"
#include <iostream>
#include <fstream>
#include <chrono>
#include <random>
#include <algorithm>
#include <sstream>
#include <spdlog/spdlog.h>

namespace cognisynapse {

// VirtualComputeNode Implementation
VirtualComputeNode::VirtualComputeNode(const VirtualNodeConfig& config)
    : config_(config)
    , streams_(nullptr)
    , running_(false)
    , total_requests_processed_(0)
    , total_processing_time_ms_(0.0f) {
}

VirtualComputeNode::~VirtualComputeNode() {
    shutdown();
}

bool VirtualComputeNode::initialize() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    try {
        // Set CUDA device
        cudaError_t cuda_error = cudaSetDevice(config_.device_id);
        if (cuda_error != cudaSuccess) {
            spdlog::error("Failed to set CUDA device {}: {}", config_.device_id, cudaGetErrorString(cuda_error));
            return false;
        }

        // Create CUDA streams
        streams_ = new cudaStream_t[config_.num_streams];
        for (int i = 0; i < config_.num_streams; ++i) {
            cuda_error = cudaStreamCreate(&streams_[i]);
            if (cuda_error != cudaSuccess) {
                spdlog::error("Failed to create CUDA stream {}: {}", i, cudaGetErrorString(cuda_error));
                return false;
            }
        }

        // Initialize cuBLAS
        cublasStatus_t cublas_status = cublasCreate(&cublas_handle_);
        if (cublas_status != CUBLAS_STATUS_SUCCESS) {
            spdlog::error("Failed to initialize cuBLAS for node {}", config_.node_id);
            return false;
        }

        // Initialize cuDNN
        cudnnStatus_t cudnn_status = cudnnCreate(&cudnn_handle_);
        if (cudnn_status != CUDNN_STATUS_SUCCESS) {
            spdlog::error("Failed to initialize cuDNN for node {}", config_.node_id);
            return false;
        }

        // Start worker threads
        running_ = true;
        worker_threads_.reserve(config_.num_streams);
        for (int i = 0; i < config_.num_streams; ++i) {
            worker_threads_.emplace_back(&VirtualComputeNode::workerLoop, this, i);
        }

        spdlog::info("Virtual compute node {} initialized successfully", config_.node_id);
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize virtual compute node {}: {}", config_.node_id, e.what());
        return false;
    }
}

void VirtualComputeNode::shutdown() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!running_) {
        return;
    }
    
    running_ = false;
    
    // Wait for worker threads
    for (auto& thread : worker_threads_) {
        if (thread.joinable()) {
            thread.join();
        }
    }
    worker_threads_.clear();
    
    // Cleanup CUDA resources
    if (streams_) {
        for (int i = 0; i < config_.num_streams; ++i) {
            cudaStreamDestroy(streams_[i]);
        }
        delete[] streams_;
        streams_ = nullptr;
    }
    
    cublasDestroy(cublas_handle_);
    cudnnDestroy(cudnn_handle_);
    
    // Free model memory
    for (auto& pair : model_weights_) {
        freeModelMemory(pair.second);
    }
    model_weights_.clear();
    loaded_models_.clear();
    
    spdlog::info("Virtual compute node {} shutdown complete", config_.node_id);
}

bool VirtualComputeNode::loadModel(const std::string& model_id, const std::string& model_path) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (loaded_models_.find(model_id) != loaded_models_.end()) {
        spdlog::info("Model {} already loaded on node {}", model_id, config_.node_id);
        return true;
    }
    
    auto start_time = std::chrono::high_resolution_clock::now();
    
    try {
        // Simulate model loading (in real implementation, load actual model weights)
        EnhancedModelInfo model_info;
        model_info.id = model_id;
        model_info.name = "Model_" + model_id;
        model_info.type = "text-generation";
        model_info.path = model_path;
        model_info.memory_usage_mb = 1024 + (std::hash<std::string>{}(model_id) % 2048); // Simulate variable memory usage
        model_info.loaded = true;
        model_info.status = "loaded";
        model_info.compute_node_id = config_.node_id;
        model_info.parameter_count = 7000000000; // 7B parameters
        model_info.max_sequence_length = 2048;
        model_info.supports_tensor_cores = config_.use_tensor_cores;
        model_info.supports_mixed_precision = config_.use_mixed_precision;
        
        // Allocate GPU memory for model weights
        void* model_weights = allocateModelMemory(model_info.memory_usage_mb * 1024 * 1024);
        if (!model_weights) {
            spdlog::error("Failed to allocate memory for model {} on node {}", model_id, config_.node_id);
            return false;
        }
        
        auto end_time = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
        model_info.loading_time_ms = static_cast<float>(duration.count());
        
        loaded_models_[model_id] = model_info;
        model_weights_[model_id] = model_weights;
        
        spdlog::info("Model {} loaded successfully on node {} ({} MB, {} ms)", 
                    model_id, config_.node_id, model_info.memory_usage_mb, model_info.loading_time_ms);
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Failed to load model {} on node {}: {}", model_id, config_.node_id, e.what());
        return false;
    }
}

bool VirtualComputeNode::unloadModel(const std::string& model_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto model_it = loaded_models_.find(model_id);
    if (model_it == loaded_models_.end()) {
        spdlog::warn("Model {} not found on node {}", model_id, config_.node_id);
        return false;
    }
    
    auto weights_it = model_weights_.find(model_id);
    if (weights_it != model_weights_.end()) {
        freeModelMemory(weights_it->second);
        model_weights_.erase(weights_it);
    }
    
    loaded_models_.erase(model_it);
    
    spdlog::info("Model {} unloaded from node {}", model_id, config_.node_id);
    return true;
}

std::future<EnhancedInferenceResponse> VirtualComputeNode::processInferenceAsync(const EnhancedInferenceRequest& request) {
    return std::async(std::launch::async, [this, request]() {
        return processInference(request);
    });
}

EnhancedInferenceResponse VirtualComputeNode::processInference(const EnhancedInferenceRequest& request) {
    auto start_time = std::chrono::high_resolution_clock::now();
    
    // Check if model is loaded
    {
        std::lock_guard<std::mutex> lock(mutex_);
        if (loaded_models_.find(request.model_id) == loaded_models_.end()) {
            EnhancedInferenceResponse response;
            response.id = request.id;
            response.model_id = request.model_id;
            response.success = false;
            response.error_message = "Model not loaded on node " + config_.node_id;
            response.timestamp = std::chrono::duration_cast<std::chrono::milliseconds>(
                std::chrono::system_clock::now().time_since_epoch()).count();
            response.compute_node_id = config_.node_id;
            return response;
        }
    }
    
    // Process the request
    auto response = processRequestInternal(request);
    
    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
    response.processing_time_ms = static_cast<float>(duration.count());
    
    updateStatistics(response.processing_time_ms);
    
    return response;
}

VirtualNodeStatus VirtualComputeNode::getStatus() const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    VirtualNodeStatus status;
    status.node_id = config_.node_id;
    status.active = running_;
    status.active_models = static_cast<int>(loaded_models_.size());
    status.queued_requests = static_cast<int>(request_queue_.size());
    status.total_requests_processed = total_requests_processed_.load();
    
    // Calculate memory usage
    size_t total_memory_used = 0;
    for (const auto& model : loaded_models_) {
        total_memory_used += model.second.memory_usage_mb;
    }
    status.used_memory_mb = total_memory_used;
    status.available_memory_mb = config_.memory_limit_mb - total_memory_used;
    status.memory_utilization = static_cast<float>(total_memory_used) / config_.memory_limit_mb;
    
    // Simulate GPU utilization
    status.gpu_utilization = std::min(1.0f, static_cast<float>(status.active_models) / config_.max_concurrent_models);
    
    // Get loaded model IDs
    for (const auto& model : loaded_models_) {
        status.loaded_models.push_back(model.first);
    }
    
    // Calculate average processing time
    if (total_requests_processed_ > 0) {
        status.average_processing_time_ms = total_processing_time_ms_.load() / total_requests_processed_;
    }
    
    return status;
}

std::vector<EnhancedModelInfo> VirtualComputeNode::getLoadedModels() const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    std::vector<EnhancedModelInfo> models;
    for (const auto& pair : loaded_models_) {
        models.push_back(pair.second);
    }
    
    return models;
}

bool VirtualComputeNode::isHealthy() const {
    return running_ && cudaGetLastError() == cudaSuccess;
}

bool VirtualComputeNode::canHandleRequest(const EnhancedInferenceRequest& request) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Check if model is loaded
    if (loaded_models_.find(request.model_id) == loaded_models_.end()) {
        return false;
    }
    
    // Check memory availability
    size_t required_memory = request.memory_requirement > 0 ? request.memory_requirement : 512; // Default 512MB
    size_t available_memory = config_.memory_limit_mb - (getStatus().used_memory_mb);
    
    return available_memory >= required_memory && 
           static_cast<int>(loaded_models_.size()) < config_.max_concurrent_models;
}

void VirtualComputeNode::workerLoop(int thread_id) {
    while (running_) {
        // In a real implementation, this would process queued requests
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
}

EnhancedInferenceResponse VirtualComputeNode::processRequestInternal(const EnhancedInferenceRequest& request) {
    // Simulate inference processing with realistic timing
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(50, 200); // 50-200ms processing time
    int processing_time = dis(gen);
    
    // Simulate actual processing time
    std::this_thread::sleep_for(std::chrono::milliseconds(processing_time));
    
    EnhancedInferenceResponse response;
    response.id = request.id;
    response.model_id = request.model_id;
    response.generated_text = "Generated response for: " + request.prompt + " [Enhanced Engine - Node: " + config_.node_id + "]";
    response.tokens_generated = std::min(request.max_tokens, 50);
    response.success = true;
    response.timestamp = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::system_clock::now().time_since_epoch()).count();
    response.compute_node_id = config_.node_id;
    response.gpu_utilization = std::min(1.0f, static_cast<float>(loaded_models_.size()) / config_.max_concurrent_models);
    response.memory_utilization = getStatus().memory_utilization;
    
    return response;
}

void* VirtualComputeNode::allocateModelMemory(size_t size) {
    void* ptr = nullptr;
    cudaError_t error = cudaMalloc(&ptr, size);
    if (error != cudaSuccess) {
        spdlog::error("Failed to allocate {} bytes on GPU: {}", size, cudaGetErrorString(error));
        return nullptr;
    }
    return ptr;
}

void VirtualComputeNode::freeModelMemory(void* ptr) {
    if (ptr) {
        cudaFree(ptr);
    }
}

void VirtualComputeNode::updateStatistics(float processing_time_ms) {
    total_requests_processed_++;
    
    // Atomic float addition
    float current_total = total_processing_time_ms_.load();
    float new_total = current_total + processing_time_ms;
    while (!total_processing_time_ms_.compare_exchange_weak(current_total, new_total)) {
        new_total = current_total + processing_time_ms;
    }
}

// EnhancedEngine Implementation
EnhancedEngine::EnhancedEngine()
    : initialized_(false)
    , running_(false) {
}

EnhancedEngine::~EnhancedEngine() {
    shutdown();
}

bool EnhancedEngine::initialize(const std::string& config_path) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (initialized_) {
        return true;
    }
    
    try {
        // Initialize statistics
        stats_ = EnhancedEngineStats{};
        
        // Create default compute nodes
        VirtualNodeConfig node_config;
        node_config.node_id = "node_0";
        node_config.device_id = 0;
        node_config.memory_limit_mb = 8192; // 8GB
        node_config.max_concurrent_models = 4;
        node_config.use_tensor_cores = true;
        node_config.use_mixed_precision = true;
        node_config.num_streams = 4;
        
        if (!addComputeNode(node_config)) {
            spdlog::error("Failed to add default compute node");
            return false;
        }
        
        // Start load balancer thread
        running_ = true;
        load_balancer_thread_ = std::thread(&EnhancedEngine::loadBalancerLoop, this);
        
        // Initialize default models
        initializeDefaultModels();
        
        initialized_ = true;
        spdlog::info("Enhanced engine initialized successfully");
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize enhanced engine: {}", e.what());
        return false;
    }
}

void EnhancedEngine::shutdown() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!initialized_) {
        return;
    }
    
    // Stop load balancer
    running_ = false;
    queue_cv_.notify_all();
    
    if (load_balancer_thread_.joinable()) {
        load_balancer_thread_.join();
    }
    
    // Shutdown compute nodes
    {
        std::lock_guard<std::mutex> nodes_lock(nodes_mutex_);
        for (auto& pair : compute_nodes_) {
            pair.second->shutdown();
        }
        compute_nodes_.clear();
    }
    
    initialized_ = false;
    spdlog::info("Enhanced engine shutdown complete");
}

bool EnhancedEngine::addComputeNode(const VirtualNodeConfig& config) {
    std::lock_guard<std::mutex> lock(nodes_mutex_);
    
    auto node = std::make_unique<VirtualComputeNode>(config);
    if (!node->initialize()) {
        spdlog::error("Failed to initialize compute node {}", config.node_id);
        return false;
    }
    
    compute_nodes_[config.node_id] = std::move(node);
    stats_.active_compute_nodes++;
    
    spdlog::info("Added compute node: {}", config.node_id);
    return true;
}

bool EnhancedEngine::removeComputeNode(const std::string& node_id) {
    std::lock_guard<std::mutex> lock(nodes_mutex_);
    
    auto it = compute_nodes_.find(node_id);
    if (it == compute_nodes_.end()) {
        spdlog::warn("Compute node {} not found", node_id);
        return false;
    }
    
    it->second->shutdown();
    compute_nodes_.erase(it);
    stats_.active_compute_nodes--;
    
    spdlog::info("Removed compute node: {}", node_id);
    return true;
}

std::vector<VirtualNodeStatus> EnhancedEngine::getComputeNodeStatus() const {
    std::lock_guard<std::mutex> lock(nodes_mutex_);
    
    std::vector<VirtualNodeStatus> statuses;
    for (const auto& pair : compute_nodes_) {
        statuses.push_back(pair.second->getStatus());
    }
    
    return statuses;
}

bool EnhancedEngine::loadModel(const std::string& model_id, const std::string& model_path) {
    std::lock_guard<std::mutex> lock(nodes_mutex_);
    
    // Find the best compute node for this model
    std::string best_node = selectBestComputeNode(EnhancedInferenceRequest{model_id: model_id});
    if (best_node.empty()) {
        spdlog::error("No available compute node for model {}", model_id);
        return false;
    }
    
    auto it = compute_nodes_.find(best_node);
    if (it == compute_nodes_.end()) {
        spdlog::error("Compute node {} not found", best_node);
        return false;
    }
    
    bool success = it->second->loadModel(model_id, model_path);
    if (success) {
        stats_.active_models++;
    }
    
    return success;
}

bool EnhancedEngine::unloadModel(const std::string& model_id) {
    std::lock_guard<std::mutex> lock(nodes_mutex_);
    
    for (auto& pair : compute_nodes_) {
        if (pair.second->unloadModel(model_id)) {
            stats_.active_models--;
            return true;
        }
    }
    
    spdlog::warn("Model {} not found on any compute node", model_id);
    return false;
}

std::vector<EnhancedModelInfo> EnhancedEngine::getLoadedModels() const {
    std::lock_guard<std::mutex> lock(nodes_mutex_);
    
    std::vector<EnhancedModelInfo> all_models;
    for (const auto& pair : compute_nodes_) {
        auto node_models = pair.second->getLoadedModels();
        all_models.insert(all_models.end(), node_models.begin(), node_models.end());
    }
    
    return all_models;
}

std::future<EnhancedInferenceResponse> EnhancedEngine::processInferenceAsync(const EnhancedInferenceRequest& request) {
    return std::async(std::launch::async, [this, request]() {
        return processInference(request);
    });
}

EnhancedInferenceResponse EnhancedEngine::processInference(const EnhancedInferenceRequest& request) {
    if (!initialized_) {
        EnhancedInferenceResponse response;
        response.id = request.id;
        response.model_id = request.model_id;
        response.success = false;
        response.error_message = "Engine not initialized";
        response.timestamp = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::system_clock::now().time_since_epoch()).count();
        return response;
    }
    
    // Select best compute node
    std::string best_node = selectBestComputeNode(request);
    if (best_node.empty()) {
        EnhancedInferenceResponse response;
        response.id = request.id;
        response.model_id = request.model_id;
        response.success = false;
        response.error_message = "No available compute node";
        response.timestamp = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::system_clock::now().time_since_epoch()).count();
        return response;
    }
    
    // Process on selected node
    std::lock_guard<std::mutex> lock(nodes_mutex_);
    auto it = compute_nodes_.find(best_node);
    if (it == compute_nodes_.end()) {
        EnhancedInferenceResponse response;
        response.id = request.id;
        response.model_id = request.model_id;
        response.success = false;
        response.error_message = "Selected compute node not found";
        response.timestamp = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::system_clock::now().time_since_epoch()).count();
        return response;
    }
    
    auto response = it->second->processInference(request);
    
    // Update global statistics
    {
        std::lock_guard<std::mutex> stats_lock(stats_mutex_);
        stats_.total_requests++;
        if (response.success) {
            stats_.successful_requests++;
        } else {
            stats_.failed_requests++;
        }
        
        // Update per-model statistics
        stats_.requests_per_model[request.model_id]++;
        stats_.avg_processing_time_per_model[request.model_id] = 
            (stats_.avg_processing_time_per_model[request.model_id] + response.processing_time_ms) / 2.0f;
    }
    
    return response;
}

EnhancedEngineStats EnhancedEngine::getStats() const {
    std::lock_guard<std::mutex> lock(stats_mutex_);
    return stats_;
}

bool EnhancedEngine::isHealthy() const {
    return initialized_ && running_;
}

nlohmann::json EnhancedEngine::getStatus() const {
    nlohmann::json status;
    
    status["initialized"] = initialized_.load();
    status["running"] = running_.load();
    status["healthy"] = isHealthy();
    
    // Add compute node information
    auto node_statuses = getComputeNodeStatus();
    status["compute_nodes"] = nlohmann::json::array();
    for (const auto& node_status : node_statuses) {
        nlohmann::json node_json;
        node_json["node_id"] = node_status.node_id;
        node_json["active"] = node_status.active;
        node_json["used_memory_mb"] = node_status.used_memory_mb;
        node_json["available_memory_mb"] = node_status.available_memory_mb;
        node_json["active_models"] = node_status.active_models;
        node_json["queued_requests"] = node_status.queued_requests;
        node_json["gpu_utilization"] = node_status.gpu_utilization;
        node_json["memory_utilization"] = node_status.memory_utilization;
        node_json["loaded_models"] = node_status.loaded_models;
        node_json["total_requests_processed"] = node_status.total_requests_processed;
        node_json["average_processing_time_ms"] = node_status.average_processing_time_ms;
        status["compute_nodes"].push_back(node_json);
    }
    
    // Add model information
    auto models = getLoadedModels();
    status["models"] = nlohmann::json::array();
    for (const auto& model : models) {
        nlohmann::json model_json;
        model_json["id"] = model.id;
        model_json["name"] = model.name;
        model_json["type"] = model.type;
        model_json["memory_usage_mb"] = model.memory_usage_mb;
        model_json["loaded"] = model.loaded;
        model_json["status"] = model.status;
        model_json["compute_node_id"] = model.compute_node_id;
        model_json["parameter_count"] = model.parameter_count;
        model_json["max_sequence_length"] = model.max_sequence_length;
        model_json["supports_tensor_cores"] = model.supports_tensor_cores;
        model_json["supports_mixed_precision"] = model.supports_mixed_precision;
        status["models"].push_back(model_json);
    }
    
    // Add statistics
    auto stats = getStats();
    status["stats"]["total_requests"] = stats.total_requests;
    status["stats"]["successful_requests"] = stats.successful_requests;
    status["stats"]["failed_requests"] = stats.failed_requests;
    status["stats"]["queued_requests"] = stats.queued_requests;
    status["stats"]["average_processing_time_ms"] = stats.average_processing_time_ms;
    status["stats"]["average_wait_time_ms"] = stats.average_wait_time_ms;
    status["stats"]["total_memory_usage_mb"] = stats.total_memory_usage_mb;
    status["stats"]["active_models"] = stats.active_models;
    status["stats"]["active_compute_nodes"] = stats.active_compute_nodes;
    status["stats"]["overall_gpu_utilization"] = stats.overall_gpu_utilization;
    status["stats"]["overall_memory_utilization"] = stats.overall_memory_utilization;
    
    return status;
}

std::string EnhancedEngine::selectBestComputeNode(const EnhancedInferenceRequest& request) const {
    std::lock_guard<std::mutex> lock(nodes_mutex_);
    
    std::string best_node;
    float best_score = -1.0f;
    
    for (const auto& pair : compute_nodes_) {
        if (!pair.second->canHandleRequest(request)) {
            continue;
        }
        
        auto status = pair.second->getStatus();
        
        // Calculate score based on available resources and load
        float memory_score = static_cast<float>(status.available_memory_mb) / 8192.0f; // Normalize to 8GB
        float load_score = 1.0f - status.gpu_utilization;
        float model_score = static_cast<float>(status.active_models) < pair.second->getStatus().active_models ? 1.0f : 0.5f;
        
        float total_score = memory_score * 0.4f + load_score * 0.4f + model_score * 0.2f;
        
        if (total_score > best_score) {
            best_score = total_score;
            best_node = pair.first;
        }
    }
    
    return best_node;
}

void EnhancedEngine::rebalanceModels() {
    // Implementation for model rebalancing across compute nodes
    spdlog::info("Rebalancing models across compute nodes");
}

void EnhancedEngine::loadBalancerLoop() {
    while (running_) {
        std::unique_lock<std::mutex> lock(queue_mutex_);
        queue_cv_.wait(lock, [this] { return !global_queue_.empty() || !running_; });
        
        if (!running_) {
            break;
        }
        
        while (!global_queue_.empty()) {
            auto request = global_queue_.front();
            global_queue_.pop();
            lock.unlock();
            
            // Process the request
            processInference(request);
            
            lock.lock();
        }
    }
}

void EnhancedEngine::updateGlobalStatistics() {
    std::lock_guard<std::mutex> lock(stats_mutex_);
    
    // Update overall statistics from compute nodes
    auto node_statuses = getComputeNodeStatus();
    
    stats_.total_memory_usage_mb = 0;
    stats_.overall_gpu_utilization = 0.0f;
    stats_.overall_memory_utilization = 0.0f;
    
    for (const auto& node_status : node_statuses) {
        stats_.total_memory_usage_mb += node_status.used_memory_mb;
        stats_.overall_gpu_utilization += node_status.gpu_utilization;
        stats_.overall_memory_utilization += node_status.memory_utilization;
    }
    
    if (!node_statuses.empty()) {
        stats_.overall_gpu_utilization /= node_statuses.size();
        stats_.overall_memory_utilization /= node_statuses.size();
    }
}

void EnhancedEngine::initializeDefaultModels() {
    // Load 5 default LLMs
    std::vector<std::pair<std::string, std::string>> default_models = {
        {"llama-7b", "/models/llama-7b"},
        {"gpt-3.5-turbo", "/models/gpt-3.5-turbo"},
        {"claude-3-sonnet", "/models/claude-3-sonnet"},
        {"mistral-7b", "/models/mistral-7b"},
        {"codellama-7b", "/models/codellama-7b"}
    };
    
    for (const auto& model : default_models) {
        if (loadModel(model.first, model.second)) {
            spdlog::info("Loaded default model: {}", model.first);
        } else {
            spdlog::warn("Failed to load default model: {}", model.first);
        }
    }
}

} // namespace cognisynapse
