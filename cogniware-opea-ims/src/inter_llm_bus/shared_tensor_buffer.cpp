#include "shared_tensor_buffer.h"
#include <algorithm>
#include <chrono>
#include <thread>
#include <cstring>

namespace cogniware {
namespace bus {

SharedTensorBuffer& SharedTensorBuffer::getInstance() {
    static SharedTensorBuffer instance;
    return instance;
}

SharedTensorBuffer::SharedTensorBuffer() :
    initialized_(false),
    total_memory_(0) {
}

SharedTensorBuffer::~SharedTensorBuffer() {
    shutdown();
}

bool SharedTensorBuffer::initialize(const SharedBufferConfig& config) {
    std::unique_lock<std::shared_mutex> lock(mutex_);
    
    if (initialized_) {
        LOG_WARN("Shared tensor buffer already initialized");
        return false;
    }

    if (!validateConfig(config)) {
        LOG_ERROR("Invalid buffer configuration");
        return false;
    }

    try {
        config_ = config;
        total_memory_ = 0;
        last_cleanup_ = std::chrono::system_clock::now();
        initialized_ = true;
        LOG_INFO("Shared tensor buffer initialized with {} MB max memory", config_.max_memory_mb);
        return true;
    } catch (const std::exception& e) {
        LOG_ERROR("Failed to initialize shared tensor buffer: {}", e.what());
        return false;
    }
}

void SharedTensorBuffer::shutdown() {
    std::unique_lock<std::shared_mutex> lock(mutex_);
    
    if (!initialized_) {
        return;
    }

    try {
        // Clean up all tensors
        for (auto& [name, tensor] : tensors_) {
            deallocateMemory(tensor.first, getTensorSize(tensor.second));
        }
        tensors_.clear();
        total_memory_ = 0;
        initialized_ = false;
        LOG_INFO("Shared tensor buffer shut down");
    } catch (const std::exception& e) {
        LOG_ERROR("Error during shared tensor buffer shutdown: {}", e.what());
    }
}

bool SharedTensorBuffer::isInitialized() const {
    std::shared_lock<std::shared_mutex> lock(mutex_);
    return initialized_;
}

bool SharedTensorBuffer::storeTensor(const std::string& name, const void* data, const TensorMetadata& metadata) {
    if (!initialized_) {
        LOG_ERROR("Shared tensor buffer not initialized");
        return false;
    }

    if (!validateTensor(metadata)) {
        LOG_ERROR("Invalid tensor metadata");
        return false;
    }

    std::unique_lock<std::shared_mutex> lock(mutex_);
    
    try {
        // Check if tensor already exists
        auto it = tensors_.find(name);
        if (it != tensors_.end()) {
            // Delete existing tensor
            deallocateMemory(it->second.first, getTensorSize(it->second.second));
            tensors_.erase(it);
        }

        // Calculate required memory
        size_t tensor_size = getTensorSize(metadata);
        if (tensor_size > config_.max_memory_mb * 1024 * 1024) {
            LOG_ERROR("Tensor size exceeds maximum memory limit");
            return false;
        }

        // Check available memory
        if (total_memory_ + tensor_size > config_.max_memory_mb * 1024 * 1024) {
            cleanupExpiredTensors();
            if (total_memory_ + tensor_size > config_.max_memory_mb * 1024 * 1024) {
                LOG_ERROR("Insufficient memory to store tensor");
                return false;
            }
        }

        // Allocate memory for tensor
        void* tensor_data = nullptr;
        if (!allocateMemory(tensor_size)) {
            LOG_ERROR("Failed to allocate memory for tensor");
            return false;
        }

        // Copy tensor data
        if (config_.enable_compression) {
            size_t compressed_size = tensor_size;
            if (!compressData(data, tensor_size, tensor_data, compressed_size)) {
                deallocateMemory(tensor_data, tensor_size);
                LOG_ERROR("Failed to compress tensor data");
                return false;
            }
            tensor_size = compressed_size;
        } else if (config_.enable_encryption) {
            size_t encrypted_size = tensor_size;
            if (!encryptData(data, tensor_size, tensor_data, encrypted_size)) {
                deallocateMemory(tensor_data, tensor_size);
                LOG_ERROR("Failed to encrypt tensor data");
                return false;
            }
            tensor_size = encrypted_size;
        } else {
            std::memcpy(tensor_data, data, tensor_size);
        }

        // Store tensor
        tensors_[name] = std::make_pair(tensor_data, metadata);
        total_memory_ += tensor_size;
        stats_.total_tensors++;
        stats_.active_tensors++;
        stats_.total_memory_bytes += tensor_size;
        stats_.peak_memory_bytes = std::max(stats_.peak_memory_bytes.load(), stats_.total_memory_bytes.load());
        stats_.tensor_type_usage[std::to_string(static_cast<int>(metadata.type))]++;
        stats_.operation_counts["store"]++;
        stats_.last_update = std::chrono::system_clock::now();

        LOG_INFO("Tensor '{}' stored successfully", name);
        return true;
    } catch (const std::exception& e) {
        LOG_ERROR("Error storing tensor: {}", e.what());
        stats_.failed_operations++;
        return false;
    }
}

bool SharedTensorBuffer::retrieveTensor(const std::string& name, void* data, TensorMetadata& metadata) {
    if (!initialized_) {
        LOG_ERROR("Shared tensor buffer not initialized");
        return false;
    }

    std::shared_lock<std::shared_mutex> lock(mutex_);
    
    try {
        auto it = tensors_.find(name);
        if (it == tensors_.end()) {
            LOG_ERROR("Tensor '{}' not found", name);
            return false;
        }

        // Get tensor data and metadata
        void* tensor_data = it->second.first;
        metadata = it->second.second;
        size_t tensor_size = getTensorSize(metadata);

        // Copy tensor data
        if (config_.enable_compression) {
            size_t decompressed_size = tensor_size;
            if (!decompressData(tensor_data, tensor_size, data, decompressed_size)) {
                LOG_ERROR("Failed to decompress tensor data");
                return false;
            }
        } else if (config_.enable_encryption) {
            size_t decrypted_size = tensor_size;
            if (!decryptData(tensor_data, tensor_size, data, decrypted_size)) {
                LOG_ERROR("Failed to decrypt tensor data");
                return false;
            }
        } else {
            std::memcpy(data, tensor_data, tensor_size);
        }

        stats_.operation_counts["retrieve"]++;
        stats_.last_update = std::chrono::system_clock::now();

        LOG_INFO("Tensor '{}' retrieved successfully", name);
        return true;
    } catch (const std::exception& e) {
        LOG_ERROR("Error retrieving tensor: {}", e.what());
        stats_.failed_operations++;
        return false;
    }
}

bool SharedTensorBuffer::deleteTensor(const std::string& name) {
    if (!initialized_) {
        LOG_ERROR("Shared tensor buffer not initialized");
        return false;
    }

    std::unique_lock<std::shared_mutex> lock(mutex_);
    
    try {
        auto it = tensors_.find(name);
        if (it == tensors_.end()) {
            LOG_ERROR("Tensor '{}' not found", name);
            return false;
        }

        // Deallocate memory
        deallocateMemory(it->second.first, getTensorSize(it->second.second));
        tensors_.erase(it);
        stats_.active_tensors--;
        stats_.operation_counts["delete"]++;
        stats_.last_update = std::chrono::system_clock::now();

        LOG_INFO("Tensor '{}' deleted successfully", name);
        return true;
    } catch (const std::exception& e) {
        LOG_ERROR("Error deleting tensor: {}", e.what());
        stats_.failed_operations++;
        return false;
    }
}

bool SharedTensorBuffer::tensorExists(const std::string& name) const {
    std::shared_lock<std::shared_mutex> lock(mutex_);
    return tensors_.find(name) != tensors_.end();
}

std::vector<std::string> SharedTensorBuffer::listTensors() const {
    std::shared_lock<std::shared_mutex> lock(mutex_);
    std::vector<std::string> names;
    names.reserve(tensors_.size());
    for (const auto& [name, _] : tensors_) {
        names.push_back(name);
    }
    return names;
}

TensorMetadata SharedTensorBuffer::getTensorMetadata(const std::string& name) const {
    std::shared_lock<std::shared_mutex> lock(mutex_);
    auto it = tensors_.find(name);
    if (it != tensors_.end()) {
        return it->second.second;
    }
    return TensorMetadata();
}

size_t SharedTensorBuffer::getTotalMemory() const {
    std::shared_lock<std::shared_mutex> lock(mutex_);
    return total_memory_;
}

size_t SharedTensorBuffer::getAvailableMemory() const {
    std::shared_lock<std::shared_mutex> lock(mutex_);
    return config_.max_memory_mb * 1024 * 1024 - total_memory_;
}

void SharedTensorBuffer::cleanup() {
    std::unique_lock<std::shared_mutex> lock(mutex_);
    cleanupExpiredTensors();
}

bool SharedTensorBuffer::resize(size_t new_size_mb) {
    std::unique_lock<std::shared_mutex> lock(mutex_);
    
    if (new_size_mb < total_memory_ / (1024 * 1024)) {
        LOG_ERROR("New size is smaller than current memory usage");
        return false;
    }

    config_.max_memory_mb = new_size_mb;
    LOG_INFO("Buffer resized to {} MB", new_size_mb);
    return true;
}

BufferStats SharedTensorBuffer::getStats() const {
    return stats_;
}

void SharedTensorBuffer::resetStats() {
    stats_ = BufferStats();
}

SharedBufferConfig SharedTensorBuffer::getConfig() const {
    std::shared_lock<std::shared_mutex> lock(mutex_);
    return config_;
}

bool SharedTensorBuffer::updateConfig(const SharedBufferConfig& config) {
    std::unique_lock<std::shared_mutex> lock(mutex_);
    
    if (!initialized_) {
        LOG_ERROR("Shared tensor buffer not initialized");
        return false;
    }

    if (!validateConfig(config)) {
        LOG_ERROR("Invalid buffer configuration");
        return false;
    }

    try {
        config_ = config;
        LOG_INFO("Buffer configuration updated");
        return true;
    } catch (const std::exception& e) {
        LOG_ERROR("Error updating buffer configuration: {}", e.what());
        return false;
    }
}

bool SharedTensorBuffer::allocateMemory(size_t size) {
    try {
        void* ptr = std::malloc(size);
        if (!ptr) {
            LOG_ERROR("Memory allocation failed");
            return false;
        }
        return true;
    } catch (const std::exception& e) {
        LOG_ERROR("Error allocating memory: {}", e.what());
        return false;
    }
}

void SharedTensorBuffer::deallocateMemory(void* ptr, size_t size) {
    if (ptr) {
        std::free(ptr);
    }
}

void SharedTensorBuffer::cleanupExpiredTensors() {
    auto now = std::chrono::system_clock::now();
    if (now - last_cleanup_ < config_.cleanup_interval) {
        return;
    }

    for (auto it = tensors_.begin(); it != tensors_.end();) {
        if (now - it->second.second.timestamp > config_.cleanup_interval) {
            deallocateMemory(it->second.first, getTensorSize(it->second.second));
            it = tensors_.erase(it);
            stats_.active_tensors--;
        } else {
            ++it;
        }
    }

    last_cleanup_ = now;
}

bool SharedTensorBuffer::compressData(const void* input, size_t input_size, void* output, size_t& output_size) {
    // TODO: Implement compression using zlib or similar
    return false;
}

bool SharedTensorBuffer::decompressData(const void* input, size_t input_size, void* output, size_t& output_size) {
    // TODO: Implement decompression using zlib or similar
    return false;
}

bool SharedTensorBuffer::encryptData(const void* input, size_t input_size, void* output, size_t& output_size) {
    // TODO: Implement encryption using OpenSSL or similar
    return false;
}

bool SharedTensorBuffer::decryptData(const void* input, size_t input_size, void* output, size_t& output_size) {
    // TODO: Implement decryption using OpenSSL or similar
    return false;
}

bool SharedTensorBuffer::validateTensor(const TensorMetadata& metadata) const {
    if (metadata.name.empty()) {
        LOG_ERROR("Tensor name cannot be empty");
        return false;
    }

    if (metadata.shape.dimensions.empty()) {
        LOG_ERROR("Tensor shape cannot be empty");
        return false;
    }

    if (metadata.shape.total_elements == 0) {
        LOG_ERROR("Tensor shape total elements cannot be zero");
        return false;
    }

    return true;
}

bool SharedTensorBuffer::validateConfig(const SharedBufferConfig& config) const {
    if (config.max_tensors == 0) {
        LOG_ERROR("Max tensors must be greater than 0");
        return false;
    }

    if (config.max_memory_mb == 0) {
        LOG_ERROR("Max memory must be greater than 0");
        return false;
    }

    if (config.cleanup_interval.count() <= 0) {
        LOG_ERROR("Cleanup interval must be greater than 0");
        return false;
    }

    if (config.enable_compression && config.compression_type.empty()) {
        LOG_ERROR("Compression type must be specified when compression is enabled");
        return false;
    }

    if (config.enable_encryption && config.encryption_key.empty()) {
        LOG_ERROR("Encryption key must be specified when encryption is enabled");
        return false;
    }

    return true;
}

size_t SharedTensorBuffer::getTensorSize(const TensorMetadata& metadata) const {
    size_t element_size = 0;
    switch (metadata.type) {
        case TensorType::FLOAT32:
            element_size = sizeof(float);
            break;
        case TensorType::FLOAT16:
            element_size = sizeof(uint16_t);
            break;
        case TensorType::INT32:
            element_size = sizeof(int32_t);
            break;
        case TensorType::INT64:
            element_size = sizeof(int64_t);
            break;
        case TensorType::UINT8:
            element_size = sizeof(uint8_t);
            break;
        case TensorType::BOOL:
            element_size = sizeof(bool);
            break;
        default:
            LOG_ERROR("Unsupported tensor type");
            return 0;
    }
    return metadata.shape.total_elements * element_size;
}

} // namespace bus
} // namespace cogniware
