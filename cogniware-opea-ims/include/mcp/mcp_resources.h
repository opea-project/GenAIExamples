#pragma once

#include "mcp_core.h"
#include <string>
#include <vector>
#include <memory>
#include <unordered_map>
#include <chrono>
#include <functional>

namespace cogniware {
namespace mcp {
namespace resources {

// Forward declarations
class ResourceAllocator;
class ResourceMonitor;
class ResourcePool;
class ResourceQuota;

/**
 * @brief Resource types
 */
enum class ResourceType {
    MEMORY,
    CPU,
    GPU,
    DISK,
    NETWORK,
    THREAD,
    FILE_DESCRIPTOR,
    PROCESS,
    CUSTOM
};

/**
 * @brief Resource allocation strategy
 */
enum class AllocationStrategy {
    FIRST_FIT,
    BEST_FIT,
    WORST_FIT,
    ROUND_ROBIN,
    PRIORITY_BASED,
    LOAD_BALANCED
};

/**
 * @brief Resource state
 */
enum class ResourceState {
    AVAILABLE,
    ALLOCATED,
    RESERVED,
    EXHAUSTED,
    THROTTLED,
    ERROR
};

/**
 * @brief Resource allocation request
 */
struct AllocationRequest {
    std::string request_id;
    std::string requester_id;
    ResourceType type;
    uint64_t amount;
    uint32_t priority = 0;
    std::chrono::seconds timeout = std::chrono::seconds(30);
    bool exclusive = false;
    std::unordered_map<std::string, std::string> metadata;
};

/**
 * @brief Resource allocation
 */
struct ResourceAllocation {
    std::string allocation_id;
    std::string request_id;
    std::string requester_id;
    ResourceType type;
    uint64_t allocated_amount;
    uint64_t used_amount;
    std::chrono::system_clock::time_point allocated_at;
    std::chrono::system_clock::time_point expires_at;
    ResourceState state;
    void* resource_handle;
};

/**
 * @brief Resource limits
 */
struct ResourceLimits {
    uint64_t memory_bytes = 0;          // 0 = unlimited
    uint32_t cpu_percent = 100;
    uint32_t gpu_percent = 100;
    uint64_t disk_bytes = 0;
    uint64_t network_bandwidth_bps = 0;
    uint32_t max_threads = 0;
    uint32_t max_file_descriptors = 0;
    uint32_t max_processes = 0;
};

/**
 * @brief Resource usage statistics
 */
struct ResourceUsage {
    ResourceType type;
    uint64_t total_available;
    uint64_t total_allocated;
    uint64_t total_used;
    uint64_t total_reserved;
    double utilization_percent;
    uint32_t allocation_count;
    std::chrono::system_clock::time_point measured_at;
};

/**
 * @brief Memory allocation info
 */
struct MemoryInfo {
    uint64_t total_bytes;
    uint64_t free_bytes;
    uint64_t used_bytes;
    uint64_t cached_bytes;
    uint64_t swap_total_bytes;
    uint64_t swap_used_bytes;
    double usage_percent;
};

/**
 * @brief CPU allocation info
 */
struct CPUInfo {
    uint32_t num_cores;
    uint32_t num_threads;
    double usage_percent;
    double load_average_1min;
    double load_average_5min;
    double load_average_15min;
    std::vector<double> per_core_usage;
};

/**
 * @brief GPU allocation info
 */
struct GPUInfo {
    uint32_t device_id;
    std::string name;
    uint64_t total_memory_bytes;
    uint64_t free_memory_bytes;
    uint64_t used_memory_bytes;
    double utilization_percent;
    double memory_utilization_percent;
    double temperature;
    uint32_t power_usage_watts;
};

/**
 * @brief Network bandwidth info
 */
struct NetworkInfo {
    uint64_t rx_bytes_per_sec;
    uint64_t tx_bytes_per_sec;
    uint64_t rx_packets_per_sec;
    uint64_t tx_packets_per_sec;
    uint64_t rx_errors;
    uint64_t tx_errors;
    double bandwidth_usage_percent;
};

/**
 * @brief Resource quota definition
 */
struct QuotaDefinition {
    std::string quota_id;
    std::string name;
    std::string description;
    bool enabled = true;
    
    ResourceLimits limits;
    
    // Time-based limits
    std::chrono::seconds window_duration = std::chrono::hours(1);
    uint64_t requests_per_window = 0;
    
    // Enforcement
    bool hard_limit = true;
    bool notify_on_threshold = true;
    double threshold_percent = 80.0;
};

/**
 * @brief MCP Resource Management Tools
 * 
 * Provides resource allocation, monitoring, and management
 * for memory, CPU, GPU, network, and other system resources.
 */
class MCPResourceTools {
public:
    MCPResourceTools();
    ~MCPResourceTools();

    /**
     * @brief Register all resource management tools with MCP server
     * @param server MCP server instance
     */
    static void registerAllTools(AdvancedMCPServer& server);

    // Resource allocation
    static ResourceAllocation allocateResource(const AllocationRequest& request);
    static bool releaseResource(const std::string& allocation_id);
    static bool resizeAllocation(const std::string& allocation_id, uint64_t new_amount);
    static ResourceAllocation getAllocation(const std::string& allocation_id);
    static std::vector<ResourceAllocation> listAllocations(const std::string& requester_id = "");
    
    // Memory management
    static void* allocateMemory(size_t bytes);
    static void freeMemory(void* ptr);
    static MemoryInfo getMemoryInfo();
    static uint64_t getAvailableMemory();
    static bool setMemoryLimit(const std::string& target_id, uint64_t bytes);
    
    // CPU management
    static CPUInfo getCPUInfo();
    static double getCPUUsage();
    static bool setCPULimit(const std::string& target_id, uint32_t percent);
    static bool setCPUAffinity(const std::string& target_id, const std::vector<uint32_t>& cores);
    static bool setPriority(const std::string& target_id, int32_t priority);
    
    // GPU management
    static std::vector<GPUInfo> getGPUInfo();
    static GPUInfo getGPUInfo(uint32_t device_id);
    static bool allocateGPU(const std::string& target_id, uint32_t device_id);
    static bool releaseGPU(const std::string& target_id, uint32_t device_id);
    static bool setGPUMemoryLimit(uint32_t device_id, uint64_t bytes);
    
    // Network management
    static NetworkInfo getNetworkInfo();
    static bool setBandwidthLimit(const std::string& target_id, uint64_t bytes_per_sec);
    static bool setNetworkPriority(const std::string& target_id, uint32_t priority);
    
    // Resource limits & quotas
    static std::string createQuota(const QuotaDefinition& quota);
    static bool updateQuota(const std::string& quota_id, const QuotaDefinition& quota);
    static bool deleteQuota(const std::string& quota_id);
    static QuotaDefinition getQuota(const std::string& quota_id);
    static std::vector<QuotaDefinition> listQuotas();
    static bool applyQuota(const std::string& target_id, const std::string& quota_id);
    
    // Resource monitoring
    static ResourceUsage getResourceUsage(ResourceType type);
    static std::vector<ResourceUsage> getAllResourceUsage();
    static bool setUsageThreshold(ResourceType type, double threshold_percent,
                                  std::function<void(const ResourceUsage&)> callback);
    
    // Resource pooling
    static std::string createResourcePool(const std::string& name, ResourceType type,
                                         uint64_t size);
    static bool deleteResourcePool(const std::string& pool_id);
    static void* acquireFromPool(const std::string& pool_id);
    static bool releaseToPool(const std::string& pool_id, void* resource);
    
    // Resource reservation
    static std::string reserveResource(ResourceType type, uint64_t amount,
                                      std::chrono::seconds duration);
    static bool cancelReservation(const std::string& reservation_id);
    static std::vector<ResourceAllocation> listReservations();
    
    // Statistics & reporting
    struct ResourceStats {
        uint64_t total_allocations;
        uint64_t active_allocations;
        uint64_t failed_allocations;
        uint64_t peak_usage;
        double average_utilization;
        std::chrono::system_clock::time_point last_reset;
    };
    static ResourceStats getStats(ResourceType type);
    static std::string generateReport();
    static bool exportReport(const std::string& filepath);
    
    // Helper functions
    static std::string resourceTypeToString(ResourceType type);
    static ResourceType stringToResourceType(const std::string& type);
    static std::string formatResourceUsage(const ResourceUsage& usage);
    static std::string formatMemorySize(uint64_t bytes);

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
    
    static std::shared_ptr<ResourceAllocator> allocator_;
    static std::shared_ptr<ResourceMonitor> monitor_;
    static std::mutex mutex_;
};

/**
 * @brief Resource allocator
 */
class ResourceAllocator {
public:
    ResourceAllocator();
    ~ResourceAllocator();

    // Allocation
    ResourceAllocation allocate(const AllocationRequest& request);
    bool release(const std::string& allocation_id);
    bool resize(const std::string& allocation_id, uint64_t new_amount);
    
    // Queries
    ResourceAllocation getAllocation(const std::string& allocation_id);
    std::vector<ResourceAllocation> listAllocations(const std::string& requester_id = "");
    
    // Configuration
    void setAllocationStrategy(AllocationStrategy strategy);
    void setMaxAllocations(uint32_t max);
    void enableOvercommit(bool enabled);
    
    // Statistics
    uint64_t getTotalAllocations() const;
    uint64_t getActiveAllocations() const;
    uint64_t getFailedAllocations() const;

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

/**
 * @brief Resource monitor
 */
class ResourceMonitor {
public:
    ResourceMonitor();
    ~ResourceMonitor();

    // Monitoring control
    void start();
    void stop();
    bool isRunning() const;
    void setUpdateInterval(std::chrono::seconds interval);
    
    // Resource usage
    ResourceUsage getUsage(ResourceType type);
    std::vector<ResourceUsage> getAllUsage();
    MemoryInfo getMemoryInfo();
    CPUInfo getCPUInfo();
    std::vector<GPUInfo> getGPUInfo();
    NetworkInfo getNetworkInfo();
    
    // Thresholds & alerts
    using ThresholdCallback = std::function<void(const ResourceUsage&)>;
    void setThreshold(ResourceType type, double threshold_percent, ThresholdCallback callback);
    void removeThreshold(ResourceType type);
    
    // History
    std::vector<ResourceUsage> getHistory(ResourceType type,
                                         std::chrono::system_clock::time_point since,
                                         std::chrono::system_clock::time_point until);

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

/**
 * @brief Resource pool
 */
class ResourcePool {
public:
    ResourcePool(const std::string& name, ResourceType type, size_t size);
    ~ResourcePool();

    // Pool operations
    void* acquire();
    bool release(void* resource);
    bool contains(void* resource);
    
    // Pool management
    bool resize(size_t new_size);
    void clear();
    size_t size() const;
    size_t available() const;
    size_t inUse() const;
    
    // Configuration
    void setMaxWaitTime(std::chrono::milliseconds duration);
    void enableAutoGrow(bool enabled);
    void setGrowthIncrement(size_t increment);
    
    // Statistics
    struct PoolStats {
        size_t total_size;
        size_t available_count;
        size_t in_use_count;
        uint64_t total_acquires;
        uint64_t total_releases;
        uint64_t wait_timeouts;
    };
    PoolStats getStats() const;

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

/**
 * @brief Resource quota manager
 */
class ResourceQuota {
public:
    ResourceQuota();
    ~ResourceQuota();

    // Quota management
    std::string createQuota(const QuotaDefinition& quota);
    bool updateQuota(const std::string& quota_id, const QuotaDefinition& quota);
    bool deleteQuota(const std::string& quota_id);
    QuotaDefinition getQuota(const std::string& quota_id);
    std::vector<QuotaDefinition> listQuotas();
    
    // Quota application
    bool applyQuota(const std::string& target_id, const std::string& quota_id);
    bool removeQuota(const std::string& target_id);
    std::string getAppliedQuota(const std::string& target_id);
    
    // Quota enforcement
    bool checkQuota(const std::string& target_id, ResourceType type, uint64_t amount);
    bool consumeQuota(const std::string& target_id, ResourceType type, uint64_t amount);
    bool releaseQuota(const std::string& target_id, ResourceType type, uint64_t amount);
    
    // Quota tracking
    struct QuotaUsage {
        std::string quota_id;
        std::string target_id;
        ResourceLimits limits;
        ResourceLimits current_usage;
        double usage_percent;
    };
    QuotaUsage getQuotaUsage(const std::string& target_id);
    std::vector<QuotaUsage> listQuotaUsage();

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

/**
 * @brief Memory pool
 */
class MemoryPool {
public:
    MemoryPool(size_t block_size, size_t num_blocks);
    ~MemoryPool();

    // Allocation
    void* allocate();
    void deallocate(void* ptr);
    
    // Queries
    size_t getBlockSize() const;
    size_t getTotalBlocks() const;
    size_t getAvailableBlocks() const;
    size_t getUsedBlocks() const;
    
    // Management
    bool expand(size_t additional_blocks);
    void reset();

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

/**
 * @brief GPU memory manager
 */
class GPUMemoryManager {
public:
    explicit GPUMemoryManager(uint32_t device_id);
    ~GPUMemoryManager();

    // GPU memory allocation
    void* allocate(size_t bytes);
    void free(void* ptr);
    
    // GPU info
    uint64_t getTotalMemory() const;
    uint64_t getFreeMemory() const;
    uint64_t getUsedMemory() const;
    
    // Memory transfer
    bool copyToDevice(void* device_ptr, const void* host_ptr, size_t bytes);
    bool copyToHost(void* host_ptr, const void* device_ptr, size_t bytes);
    bool copyDeviceToDevice(void* dst_ptr, const void* src_ptr, size_t bytes);
    
    // Synchronization
    bool synchronize();
    bool setDevice();

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

/**
 * @brief Thread pool
 */
class ThreadPool {
public:
    explicit ThreadPool(size_t num_threads);
    ~ThreadPool();

    // Task submission
    template<typename F, typename... Args>
    auto submit(F&& f, Args&&... args) -> std::future<typename std::result_of<F(Args...)>::type>;
    
    // Pool management
    void resize(size_t new_size);
    void wait();
    void stop();
    
    // Queries
    size_t getThreadCount() const;
    size_t getQueuedTasks() const;
    size_t getActiveTasks() const;

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

/**
 * @brief Resource utilities
 */
class ResourceUtils {
public:
    // Memory utilities
    static uint64_t getPageSize();
    static uint64_t alignToPageSize(uint64_t size);
    static bool lockMemory(void* ptr, size_t size);
    static bool unlockMemory(void* ptr, size_t size);
    
    // CPU utilities
    static uint32_t getNumCPUs();
    static uint32_t getCurrentCPU();
    static bool pinToCPU(uint32_t cpu_id);
    static std::vector<uint32_t> getAvailableCPUs();
    
    // GPU utilities
    static uint32_t getNumGPUs();
    static std::vector<uint32_t> getAvailableGPUs();
    static bool setCurrentGPU(uint32_t device_id);
    static uint32_t getCurrentGPU();
    
    // Format utilities
    static std::string formatBytes(uint64_t bytes);
    static std::string formatBandwidth(uint64_t bytes_per_sec);
    static std::string formatPercent(double percent);
};

} // namespace resources
} // namespace mcp
} // namespace cogniware

