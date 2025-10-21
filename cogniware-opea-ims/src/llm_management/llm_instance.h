#pragma once

#include <memory>
#include <string>
#include <vector>
#include <mutex>
#include <atomic>
#include <chrono>
#include <functional>

namespace cogniware {
namespace llm_management {

// Forward declarations
class ResourceMonitor;
class RequestQueue;
class ConcurrencyController;

// Model configuration
struct ModelConfig {
    std::string model_id;
    std::string model_path;
    std::string model_type;
    size_t max_sequence_length;
    size_t max_batch_size;
    bool use_fp16;
    bool use_quantization;
    std::string quantization_type;
    size_t num_gpu_layers;
    size_t num_cpu_layers;
    size_t num_threads;
    size_t context_size;
    size_t embedding_dim;
    size_t num_heads;
    size_t num_layers;
    size_t intermediate_size;
    float rope_theta;
    float rope_scaling;
    bool use_flash_attention;
    bool use_sliding_window;
    size_t sliding_window_size;

    ModelConfig() :
        max_sequence_length(2048),
        max_batch_size(32),
        use_fp16(true),
        use_quantization(false),
        num_gpu_layers(0),
        num_cpu_layers(0),
        num_threads(4),
        context_size(2048),
        embedding_dim(4096),
        num_heads(32),
        num_layers(32),
        intermediate_size(11008),
        rope_theta(10000.0f),
        rope_scaling(1.0f),
        use_flash_attention(true),
        use_sliding_window(false),
        sliding_window_size(4096) {}
};

// Instance status
enum class InstanceStatus {
    UNINITIALIZED,
    INITIALIZING,
    READY,
    BUSY,
    ERROR,
    SHUTTING_DOWN
};

// Instance statistics
struct InstanceStats {
    size_t total_requests;
    size_t successful_requests;
    size_t failed_requests;
    size_t current_batch_size;
    std::chrono::milliseconds average_latency;
    std::chrono::milliseconds p95_latency;
    std::chrono::milliseconds p99_latency;
    double gpu_memory_usage;
    double gpu_utilization;
    double cpu_memory_usage;
    double cpu_utilization;

    InstanceStats() :
        total_requests(0),
        successful_requests(0),
        failed_requests(0),
        current_batch_size(0),
        average_latency(std::chrono::milliseconds(0)),
        p95_latency(std::chrono::milliseconds(0)),
        p99_latency(std::chrono::milliseconds(0)),
        gpu_memory_usage(0.0),
        gpu_utilization(0.0),
        cpu_memory_usage(0.0),
        cpu_utilization(0.0) {}
};

// LLM instance class
class LLMInstance {
public:
    LLMInstance();
    ~LLMInstance();

    // Prevent copying
    LLMInstance(const LLMInstance&) = delete;
    LLMInstance& operator=(const LLMInstance&) = delete;

    // Initialization and cleanup
    bool initialize(const ModelConfig& config);
    void shutdown();
    bool isInitialized() const;
    InstanceStatus getStatus() const;

    // Configuration
    ModelConfig getConfig() const;
    void updateConfig(const ModelConfig& config);
    void setResourceMonitor(std::shared_ptr<ResourceMonitor> monitor);
    void setRequestQueue(std::shared_ptr<RequestQueue> queue);
    void setConcurrencyController(std::shared_ptr<ConcurrencyController> controller);

    // Request processing
    bool processRequest(const std::string& request_id, const std::string& input);
    bool processBatch(const std::vector<std::string>& request_ids, const std::vector<std::string>& inputs);
    bool cancelRequest(const std::string& request_id);
    bool cancelAllRequests();

    // Status and statistics
    InstanceStats getStats() const;
    void resetStats();
    std::string getStatusString() const;
    bool isReady() const;
    bool isBusy() const;
    bool hasError() const;

    // Resource management
    bool checkResources() const;
    void updateResourceUsage();
    size_t getAvailableBatchSize() const;
    bool canProcessBatch(size_t batch_size) const;

    // Error handling
    std::string getLastError() const;
    void clearError();
    bool recoverFromError();

private:
    // Internal implementation
    struct Impl;
    std::unique_ptr<Impl> pimpl;
};

} // namespace llm_management
} // namespace cogniware
