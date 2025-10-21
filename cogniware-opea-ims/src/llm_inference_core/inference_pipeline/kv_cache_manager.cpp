#include "kv_cache_manager.h"
#include "../cuda_runtime/cuda_utils.h"
#include <spdlog/spdlog.h>

namespace cogniware {
namespace llm_inference {

// Internal implementation
struct KVCacheManager::Impl {
    KVCacheConfig config;
    std::unordered_map<int, KVCacheEntry> cache_entries;
    std::mutex mutex;
    size_t total_cache_size;
    size_t peak_cache_size;

    Impl(const KVCacheConfig& cfg) : config(cfg), total_cache_size(0), peak_cache_size(0) {
        validateConfig(cfg);
    }

    ~Impl() {
        cleanup();
    }

    void validateConfig(const KVCacheConfig& cfg) {
        if (cfg.max_batch_size == 0) {
            throw std::invalid_argument("max_batch_size must be greater than 0");
        }
        if (cfg.max_sequence_length == 0) {
            throw std::invalid_argument("max_sequence_length must be greater than 0");
        }
        if (cfg.num_attention_heads == 0) {
            throw std::invalid_argument("num_attention_heads must be greater than 0");
        }
        if (cfg.head_dim == 0) {
            throw std::invalid_argument("head_dim must be greater than 0");
        }
        if (cfg.num_layers == 0) {
            throw std::invalid_argument("num_layers must be greater than 0");
        }
    }

    void cleanup() {
        std::lock_guard<std::mutex> lock(mutex);
        for (auto& entry : cache_entries) {
            if (entry.second.key_cache) {
                CUDA_CHECK(cudaFree(entry.second.key_cache));
            }
            if (entry.second.value_cache) {
                CUDA_CHECK(cudaFree(entry.second.value_cache));
            }
        }
        cache_entries.clear();
        total_cache_size = 0;
    }

    size_t calculateCacheSize(size_t batch_size, size_t sequence_length) const {
        const size_t element_size = config.use_fp16 ? sizeof(half) : sizeof(float);
        const size_t cache_size_per_layer = batch_size * sequence_length * config.num_attention_heads * config.head_dim * element_size;
        return cache_size_per_layer * config.num_layers * 2;  // *2 for key and value
    }
};

// Constructor and destructor
KVCacheManager::KVCacheManager(const KVCacheConfig& config)
    : pimpl(std::make_unique<Impl>(config)) {}

KVCacheManager::~KVCacheManager() = default;

// Singleton access
KVCacheManager& KVCacheManager::getInstance() {
    static KVCacheManager instance(KVCacheConfig{});
    return instance;
}

// Cache management
KVCacheEntry KVCacheManager::allocateCache(
    int layer_id,
    size_t batch_size,
    size_t sequence_length,
    cudaStream_t stream
) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);

    // Check if cache already exists
    auto it = pimpl->cache_entries.find(layer_id);
    if (it != pimpl->cache_entries.end()) {
        // Check if existing cache is sufficient
        if (it->second.batch_size >= batch_size && it->second.sequence_length >= sequence_length) {
            it->second.is_active = true;
            return it->second;
        }
        // Free existing cache if insufficient
        if (it->second.key_cache) {
            CUDA_CHECK(cudaFree(it->second.key_cache));
        }
        if (it->second.value_cache) {
            CUDA_CHECK(cudaFree(it->second.value_cache));
        }
        pimpl->total_cache_size -= calculateCacheSize(it->second.batch_size, it->second.sequence_length);
    }

    // Calculate cache size
    const size_t cache_size = calculateCacheSize(batch_size, sequence_length);
    const size_t element_size = pimpl->config.use_fp16 ? sizeof(half) : sizeof(float);
    const size_t cache_size_per_layer = cache_size / (pimpl->config.num_layers * 2);

    // Allocate new cache
    KVCacheEntry entry;
    entry.batch_size = batch_size;
    entry.sequence_length = sequence_length;
    entry.is_active = true;

    if (pimpl->config.use_fp16) {
        CUDA_CHECK(cudaMalloc(&entry.key_cache, cache_size_per_layer));
        CUDA_CHECK(cudaMalloc(&entry.value_cache, cache_size_per_layer));
        CUDA_CHECK(cudaMemsetAsync(entry.key_cache, 0, cache_size_per_layer, stream));
        CUDA_CHECK(cudaMemsetAsync(entry.value_cache, 0, cache_size_per_layer, stream));
    } else {
        CUDA_CHECK(cudaMalloc(&entry.key_cache, cache_size_per_layer));
        CUDA_CHECK(cudaMalloc(&entry.value_cache, cache_size_per_layer));
        CUDA_CHECK(cudaMemsetAsync(entry.key_cache, 0, cache_size_per_layer, stream));
        CUDA_CHECK(cudaMemsetAsync(entry.value_cache, 0, cache_size_per_layer, stream));
    }

    // Update cache entries and size
    pimpl->cache_entries[layer_id] = entry;
    pimpl->total_cache_size += cache_size;
    pimpl->peak_cache_size = std::max(pimpl->peak_cache_size, pimpl->total_cache_size);

    return entry;
}

void KVCacheManager::deallocateCache(int layer_id) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);

    auto it = pimpl->cache_entries.find(layer_id);
    if (it != pimpl->cache_entries.end()) {
        if (it->second.key_cache) {
            CUDA_CHECK(cudaFree(it->second.key_cache));
        }
        if (it->second.value_cache) {
            CUDA_CHECK(cudaFree(it->second.value_cache));
        }
        pimpl->total_cache_size -= calculateCacheSize(it->second.batch_size, it->second.sequence_length);
        pimpl->cache_entries.erase(it);
    }
}

void KVCacheManager::clearCache(cudaStream_t stream) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);

    for (auto& entry : pimpl->cache_entries) {
        const size_t cache_size = calculateCacheSize(entry.second.batch_size, entry.second.sequence_length) / (pimpl->config.num_layers * 2);
        CUDA_CHECK(cudaMemsetAsync(entry.second.key_cache, 0, cache_size, stream));
        CUDA_CHECK(cudaMemsetAsync(entry.second.value_cache, 0, cache_size, stream));
    }
}

// Cache operations
void KVCacheManager::updateCache(
    int layer_id,
    const void* key,
    const void* value,
    size_t batch_size,
    size_t sequence_length,
    size_t offset,
    cudaStream_t stream
) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);

    auto it = pimpl->cache_entries.find(layer_id);
    if (it == pimpl->cache_entries.end()) {
        throw std::runtime_error("Cache not found for layer " + std::to_string(layer_id));
    }

    const size_t element_size = pimpl->config.use_fp16 ? sizeof(half) : sizeof(float);
    const size_t cache_size = batch_size * sequence_length * pimpl->config.num_attention_heads * pimpl->config.head_dim * element_size;
    const size_t offset_size = offset * pimpl->config.num_attention_heads * pimpl->config.head_dim * element_size;

    // Copy key and value to cache
    CUDA_CHECK(cudaMemcpyAsync(
        static_cast<char*>(it->second.key_cache) + offset_size,
        key,
        cache_size,
        cudaMemcpyDeviceToDevice,
        stream
    ));

    CUDA_CHECK(cudaMemcpyAsync(
        static_cast<char*>(it->second.value_cache) + offset_size,
        value,
        cache_size,
        cudaMemcpyDeviceToDevice,
        stream
    ));
}

KVCacheEntry KVCacheManager::getCache(int layer_id) const {
    std::lock_guard<std::mutex> lock(pimpl->mutex);

    auto it = pimpl->cache_entries.find(layer_id);
    if (it == pimpl->cache_entries.end()) {
        throw std::runtime_error("Cache not found for layer " + std::to_string(layer_id));
    }

    return it->second;
}

// Memory management
size_t KVCacheManager::getTotalCacheSize() const {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    return pimpl->total_cache_size;
}

size_t KVCacheManager::getPeakCacheSize() const {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    return pimpl->peak_cache_size;
}

size_t KVCacheManager::getFreeCacheSize() const {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    size_t used_size = 0;
    for (const auto& entry : pimpl->cache_entries) {
        if (entry.second.is_active) {
            used_size += calculateCacheSize(entry.second.batch_size, entry.second.sequence_length);
        }
    }
    return pimpl->total_cache_size - used_size;
}

// Helper functions
size_t KVCacheManager::calculateCacheSize(size_t batch_size, size_t sequence_length) const {
    return pimpl->calculateCacheSize(batch_size, sequence_length);
}

} // namespace llm_inference
} // namespace cogniware
