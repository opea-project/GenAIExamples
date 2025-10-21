#pragma once

#include <string>
#include <vector>
#include <memory>
#include <mutex>
#include <shared_mutex>
#include <atomic>
#include <chrono>
#include <functional>
#include "utils/error_handler_cpp.h"
#include "utils/logger_cpp.h"

namespace cogniware {
namespace bus {

// Tensor data type
enum class TensorType {
    FLOAT32,
    FLOAT16,
    INT32,
    INT64,
    UINT8,
    BOOL
};

// Tensor shape
struct TensorShape {
    std::vector<size_t> dimensions;
    size_t total_elements;

    TensorShape() : total_elements(0) {}
    explicit TensorShape(const std::vector<size_t>& dims) : dimensions(dims) {
        total_elements = 1;
        for (size_t dim : dimensions) {
            total_elements *= dim;
        }
    }
};

// Tensor metadata
struct TensorMetadata {
    std::string name;
    TensorType type;
    TensorShape shape;
    std::chrono::system_clock::time_point timestamp;
    std::unordered_map<std::string, std::string> attributes;

    TensorMetadata() : type(TensorType::FLOAT32) {}
};

// Shared tensor buffer configuration
struct SharedBufferConfig {
    size_t max_tensors;
    size_t max_memory_mb;
    bool enable_compression;
    std::string compression_type;
    size_t compression_level;
    bool enable_encryption;
    std::string encryption_key;
    std::chrono::milliseconds cleanup_interval;
    std::unordered_map<std::string, std::string> parameters;

    SharedBufferConfig() :
        max_tensors(1000),
        max_memory_mb(1024),
        enable_compression(false),
        compression_level(6),
        enable_encryption(false),
        cleanup_interval(std::chrono::minutes(5)) {}
};

// Shared tensor buffer statistics
struct BufferStats {
    std::atomic<size_t> total_tensors;
    std::atomic<size_t> active_tensors;
    std::atomic<size_t> total_memory_bytes;
    std::atomic<size_t> peak_memory_bytes;
    std::atomic<size_t> total_operations;
    std::atomic<size_t> failed_operations;
    std::chrono::system_clock::time_point last_update;
    std::unordered_map<std::string, size_t> tensor_type_usage;
    std::unordered_map<std::string, size_t> operation_counts;
};

// Shared tensor buffer class
class SharedTensorBuffer {
public:
    static SharedTensorBuffer& getInstance();

    // Prevent copying
    SharedTensorBuffer(const SharedTensorBuffer&) = delete;
    SharedTensorBuffer& operator=(const SharedTensorBuffer&) = delete;

    // Initialization
    bool initialize(const SharedBufferConfig& config);
    void shutdown();
    bool isInitialized() const;

    // Tensor operations
    bool storeTensor(const std::string& name, const void* data, const TensorMetadata& metadata);
    bool retrieveTensor(const std::string& name, void* data, TensorMetadata& metadata);
    bool deleteTensor(const std::string& name);
    bool tensorExists(const std::string& name) const;
    std::vector<std::string> listTensors() const;
    TensorMetadata getTensorMetadata(const std::string& name) const;

    // Memory management
    size_t getTotalMemory() const;
    size_t getAvailableMemory() const;
    void cleanup();
    bool resize(size_t new_size_mb);

    // Statistics and monitoring
    BufferStats getStats() const;
    void resetStats();

    // Configuration
    SharedBufferConfig getConfig() const;
    bool updateConfig(const SharedBufferConfig& config);

private:
    SharedTensorBuffer();
    ~SharedTensorBuffer();

    // Memory management
    bool allocateMemory(size_t size);
    void deallocateMemory(void* ptr, size_t size);
    void cleanupExpiredTensors();
    bool compressData(const void* input, size_t input_size, void* output, size_t& output_size);
    bool decompressData(const void* input, size_t input_size, void* output, size_t& output_size);
    bool encryptData(const void* input, size_t input_size, void* output, size_t& output_size);
    bool decryptData(const void* input, size_t input_size, void* output, size_t& output_size);

    // Validation
    bool validateTensor(const TensorMetadata& metadata) const;
    bool validateConfig(const SharedBufferConfig& config) const;
    size_t getTensorSize(const TensorMetadata& metadata) const;

    // Member variables
    SharedBufferConfig config_;
    bool initialized_;
    mutable std::shared_mutex mutex_;
    std::unordered_map<std::string, std::pair<void*, TensorMetadata>> tensors_;
    std::atomic<size_t> total_memory_;
    BufferStats stats_;
    std::chrono::system_clock::time_point last_cleanup_;
};

} // namespace bus
} // namespace cogniware
