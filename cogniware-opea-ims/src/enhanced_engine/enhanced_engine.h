#pragma once

#include <string>
#include <vector>
#include <memory>
#include <mutex>
#include <atomic>
#include <thread>
#include <condition_variable>
#include <queue>
#include <unordered_map>
#include <future>
#include <chrono>
#include <nlohmann/json.hpp>
#include <cuda_runtime.h>
#include <cublas_v2.h>
#include <cudnn.h>

namespace cognisynapse {

/**
 * @brief Enhanced inference request with priority and resource requirements
 */
struct EnhancedInferenceRequest {
    std::string id;
    std::string model_id;
    std::string prompt;
    int max_tokens = 100;
    float temperature = 0.7f;
    std::string user_id;
    uint64_t timestamp;
    int priority = 0;  // Higher number = higher priority
    size_t memory_requirement = 0;
    bool use_tensor_cores = true;
    bool use_mixed_precision = true;
    int batch_size = 1;
};

/**
 * @brief Enhanced inference response with detailed metrics
 */
struct EnhancedInferenceResponse {
    std::string id;
    std::string model_id;
    std::string generated_text;
    int tokens_generated = 0;
    float processing_time_ms = 0.0f;
    bool success = false;
    std::string error_message;
    uint64_t timestamp;
    std::string compute_node_id;
    float gpu_utilization = 0.0f;
    float memory_utilization = 0.0f;
    int queue_position = 0;
    float wait_time_ms = 0.0f;
};

/**
 * @brief Virtual compute node configuration
 */
struct VirtualNodeConfig {
    std::string node_id;
    int device_id = 0;
    size_t memory_limit_mb = 8192;  // 8GB default
    int max_concurrent_models = 4;
    bool use_tensor_cores = true;
    bool use_mixed_precision = true;
    float memory_utilization_target = 0.8f;
    int batch_size = 8;
    int num_streams = 4;
    int priority = 0;  // Higher number = higher priority
};

/**
 * @brief Virtual compute node status
 */
struct VirtualNodeStatus {
    std::string node_id;
    bool active = false;
    size_t used_memory_mb = 0;
    size_t available_memory_mb = 0;
    int active_models = 0;
    int queued_requests = 0;
    float gpu_utilization = 0.0f;
    float memory_utilization = 0.0f;
    std::vector<std::string> loaded_models;
    std::vector<std::string> running_requests;
    uint64_t total_requests_processed = 0;
    float average_processing_time_ms = 0.0f;
};

/**
 * @brief Model information with resource requirements
 */
struct EnhancedModelInfo {
    std::string id;
    std::string name;
    std::string type;
    std::string path;
    size_t memory_usage_mb = 0;
    bool loaded = false;
    std::string status;
    std::string compute_node_id;
    size_t parameter_count = 0;
    int max_sequence_length = 2048;
    bool supports_tensor_cores = true;
    bool supports_mixed_precision = true;
    float loading_time_ms = 0.0f;
    uint64_t last_used_timestamp = 0;
};

/**
 * @brief Enhanced engine statistics
 */
struct EnhancedEngineStats {
    uint64_t total_requests = 0;
    uint64_t successful_requests = 0;
    uint64_t failed_requests = 0;
    uint64_t queued_requests = 0;
    float average_processing_time_ms = 0.0f;
    float average_wait_time_ms = 0.0f;
    size_t total_memory_usage_mb = 0;
    int active_models = 0;
    int active_compute_nodes = 0;
    float overall_gpu_utilization = 0.0f;
    float overall_memory_utilization = 0.0f;
    std::unordered_map<std::string, uint64_t> requests_per_model;
    std::unordered_map<std::string, float> avg_processing_time_per_model;
};

/**
 * @brief Virtual compute node implementation
 */
class VirtualComputeNode {
public:
    VirtualComputeNode(const VirtualNodeConfig& config);
    ~VirtualComputeNode();

    bool initialize();
    void shutdown();
    
    bool loadModel(const std::string& model_id, const std::string& model_path);
    bool unloadModel(const std::string& model_id);
    
    std::future<EnhancedInferenceResponse> processInferenceAsync(const EnhancedInferenceRequest& request);
    EnhancedInferenceResponse processInference(const EnhancedInferenceRequest& request);
    
    VirtualNodeStatus getStatus() const;
    std::vector<EnhancedModelInfo> getLoadedModels() const;
    
    bool isHealthy() const;
    bool canHandleRequest(const EnhancedInferenceRequest& request) const;

private:
    VirtualNodeConfig config_;
    mutable std::mutex mutex_;
    
    // CUDA resources
    cudaStream_t* streams_;
    cublasHandle_t cublas_handle_;
    cudnnHandle_t cudnn_handle_;
    
    // Model management
    std::unordered_map<std::string, EnhancedModelInfo> loaded_models_;
    std::unordered_map<std::string, void*> model_weights_;  // GPU memory pointers
    
    // Request processing
    std::queue<EnhancedInferenceRequest> request_queue_;
    std::vector<std::thread> worker_threads_;
    std::atomic<bool> running_;
    
    // Statistics
    std::atomic<uint64_t> total_requests_processed_;
    std::atomic<float> total_processing_time_ms_;
    
    void workerLoop(int thread_id);
    EnhancedInferenceResponse processRequestInternal(const EnhancedInferenceRequest& request);
    void* allocateModelMemory(size_t size);
    void freeModelMemory(void* ptr);
    void updateStatistics(float processing_time_ms);
};

/**
 * @brief Enhanced CogniSynapse Engine with virtual compute nodes
 */
class EnhancedEngine {
public:
    EnhancedEngine();
    ~EnhancedEngine();

    bool initialize(const std::string& config_path = "");
    void shutdown();

    // Compute node management
    bool addComputeNode(const VirtualNodeConfig& config);
    bool removeComputeNode(const std::string& node_id);
    std::vector<VirtualNodeStatus> getComputeNodeStatus() const;

    // Model management
    bool loadModel(const std::string& model_id, const std::string& model_path);
    bool unloadModel(const std::string& model_id);
    std::vector<EnhancedModelInfo> getLoadedModels() const;

    // Inference processing
    std::future<EnhancedInferenceResponse> processInferenceAsync(const EnhancedInferenceRequest& request);
    EnhancedInferenceResponse processInference(const EnhancedInferenceRequest& request);

    // Statistics and monitoring
    EnhancedEngineStats getStats() const;
    bool isHealthy() const;
    nlohmann::json getStatus() const;

    // Load balancing
    std::string selectBestComputeNode(const EnhancedInferenceRequest& request) const;
    void rebalanceModels();

private:
    std::atomic<bool> initialized_;
    std::atomic<bool> running_;
    mutable std::mutex mutex_;
    
    // Compute nodes
    std::unordered_map<std::string, std::unique_ptr<VirtualComputeNode>> compute_nodes_;
    mutable std::mutex nodes_mutex_;
    
    // Global request queue for load balancing
    std::queue<EnhancedInferenceRequest> global_queue_;
    std::mutex queue_mutex_;
    std::condition_variable queue_cv_;
    std::thread load_balancer_thread_;
    
    // Statistics
    mutable EnhancedEngineStats stats_;
    mutable std::mutex stats_mutex_;
    
    void loadBalancerLoop();
    void updateGlobalStatistics();
    void initializeDefaultModels();
};

} // namespace cognisynapse
