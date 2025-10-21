/**
 * @file internal_types.h
 * @brief Internal C++ types used by the cogniware engine
 * 
 * This header defines the internal C++ types used within the cogniware engine.
 * These types are not exposed through the C API.
 */

#ifndef MSMARTCOMPUTE_INTERNAL_TYPES_H
#define MSMARTCOMPUTE_INTERNAL_TYPES_H

#include <string>
#include <vector>
#include <memory>
#include <unordered_map>
#include <cuda_runtime.h>

namespace cogniware {

/**
 * @brief Model types supported by the engine
 */
enum class ModelType {
    GGUF,
    SAFETENSORS,
    PYTORCH,
    UNKNOWN
};

/**
 * @brief Task states for async operations
 */
enum class TaskState {
    PENDING,
    RUNNING,
    COMPLETED,
    FAILED,
    CANCELLED
};

/**
 * @brief Configuration for a virtual compute node
 */
struct VirtualComputeNodeConfig {
    int gpu_id;                     ///< GPU device ID
    std::vector<int> core_indices;  ///< GPU core indices to use
    size_t vram_bytes;             ///< VRAM allocation in bytes
    size_t system_ram_bytes;       ///< System RAM allocation in bytes
    int priority;                  ///< Scheduling priority
    float memory_fraction;         ///< Fraction of GPU memory to use (0.0-1.0)
};

/**
 * @brief Task information
 */
struct Task {
    int task_id;                   ///< Unique task identifier
    TaskState state;               ///< Current task state
    std::string model_id;          ///< Associated model ID
    std::string input_json;        ///< Input JSON string
    std::string output_json;       ///< Output JSON string (when completed)
    int priority;                  ///< Task priority
    int timeout_ms;                ///< Timeout in milliseconds
    cudaStream_t stream;           ///< CUDA stream for this task
    std::chrono::steady_clock::time_point start_time; ///< Task start time
};

/**
 * @brief Model instance information
 */
struct ModelInstance {
    int handle;                    ///< Unique model handle
    std::string model_id;          ///< Model identifier
    ModelType type;                ///< Model type
    VirtualComputeNodeConfig vcn_config; ///< VCN configuration
    std::unordered_map<std::string, void*> weights; ///< Model weights on GPU
    std::unordered_map<std::string, void*> kv_cache; ///< KV cache tensors
    size_t context_length;         ///< Model context length
    int max_batch_size;            ///< Maximum batch size
    bool is_loaded;                ///< Whether model is loaded
};

/**
 * @brief Resource usage information
 */
struct ResourceUsage {
    size_t total_vram;            ///< Total VRAM on GPU
    size_t used_vram;             ///< Used VRAM on GPU
    size_t total_system_ram;      ///< Total system RAM
    size_t used_system_ram;       ///< Used system RAM
    float gpu_utilization;        ///< GPU utilization (0.0-1.0)
    std::vector<float> core_utilization; ///< Per-core utilization
};

/**
 * @brief Shared tensor information
 */
struct SharedTensor {
    std::string tensor_id;        ///< Unique tensor identifier
    void* data_ptr;               ///< Pointer to tensor data
    size_t data_size;             ///< Size of tensor data
    std::string dtype;            ///< Data type
    std::vector<int64_t> shape;   ///< Tensor shape
    bool is_device_memory;        ///< Whether data is on device
    std::chrono::steady_clock::time_point creation_time; ///< Creation time
};

/**
 * @brief Training buffer information
 */
struct TrainingBuffer {
    std::string buffer_id;        ///< Unique buffer identifier
    void* data_ptr;               ///< Pointer to buffer data
    size_t data_size;             ///< Size of buffer data
    std::string format;           ///< Data format
    int sequence_length;          ///< Sequence length
    bool is_training;             ///< Whether buffer is for training
};

} // namespace cogniware

#endif // MSMARTCOMPUTE_INTERNAL_TYPES_H
