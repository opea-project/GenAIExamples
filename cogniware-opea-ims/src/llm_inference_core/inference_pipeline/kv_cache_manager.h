#pragma once

#include <memory>
#include <vector>
#include <unordered_map>
#include <cuda_runtime.h>
#include "../cuda_runtime/gpu_memory_manager.h"

namespace cogniware {
namespace llm_inference {

// KV cache configuration
struct KVCacheConfig {
    size_t max_batch_size;
    size_t max_sequence_length;
    size_t num_attention_heads;
    size_t head_dim;
    size_t num_layers;
    bool use_fp16;
};

// KV cache entry
struct KVCacheEntry {
    void* key_cache;
    void* value_cache;
    size_t sequence_length;
    size_t batch_size;
    bool is_active;
};

class KVCacheManager {
public:
    static KVCacheManager& getInstance();

    // Prevent copying
    KVCacheManager(const KVCacheManager&) = delete;
    KVCacheManager& operator=(const KVCacheManager&) = delete;

    // Initialization and cleanup
    void initialize(const KVCacheConfig& config);
    void cleanup();

    // Cache management
    KVCacheEntry allocateCache(size_t batch_size, size_t sequence_length);
    void deallocateCache(const KVCacheEntry& entry);
    void clearCache();

    // Cache operations
    void updateCache(
        const KVCacheEntry& entry,
        const void* key,
        const void* value,
        size_t layer_idx,
        size_t position,
        cudaStream_t stream = nullptr
    );

    void getCache(
        void* key,
        void* value,
        const KVCacheEntry& entry,
        size_t layer_idx,
        size_t position,
        cudaStream_t stream = nullptr
    );

    // Cache information
    size_t getMaxBatchSize() const;
    size_t getMaxSequenceLength() const;
    size_t getNumLayers() const;
    size_t getHeadDim() const;
    bool isUsingFP16() const;

    // Memory management
    size_t getTotalCacheSize() const;
    size_t getFreeCacheSize() const;
    void setCacheSize(size_t size);
    size_t getCacheSize() const;

private:
    KVCacheManager();
    ~KVCacheManager();

    // Internal helper functions
    void initializeDevice();
    void cleanupDevice();
    size_t calculateCacheSize(size_t batch_size, size_t sequence_length) const;
    void validateConfig(const KVCacheConfig& config);

    // Internal state
    struct Impl;
    std::unique_ptr<Impl> pimpl;
};

// Helper functions
inline KVCacheManager& getKVCacheManager() {
    return KVCacheManager::getInstance();
}

inline void initializeKVCache(const KVCacheConfig& config) {
    getKVCacheManager().initialize(config);
}

inline void cleanupKVCache() {
    getKVCacheManager().cleanup();
}

inline KVCacheEntry allocateKVCache(size_t batch_size, size_t sequence_length) {
    return getKVCacheManager().allocateCache(batch_size, sequence_length);
}

inline void deallocateKVCache(const KVCacheEntry& entry) {
    getKVCacheManager().deallocateCache(entry);
}

inline void clearKVCache() {
    getKVCacheManager().clearCache();
}

} // namespace llm_inference
} // namespace cogniware
