#pragma once

#include <cuda_runtime.h>
#include <vector>
#include <memory>
#include <mutex>
#include <atomic>
#include <map>
#include <string>
#include <chrono>
#include <functional>
#include <queue>
#include <thread>
#include <condition_variable>

namespace cogniware {
namespace memory {

// Memory partition types
enum class MemoryPartitionType {
    GLOBAL_MEMORY,          // Global GPU memory
    SHARED_MEMORY,          // Shared memory
    CONSTANT_MEMORY,        // Constant memory
    TEXTURE_MEMORY,         // Texture memory
    LOCAL_MEMORY,           // Local memory
    UNIFIED_MEMORY,         // Unified memory
    PINNED_MEMORY,          // Pinned host memory
    ZERO_COPY_MEMORY        // Zero-copy memory
};

// Memory access patterns
enum class MemoryAccessPattern {
    SEQUENTIAL,             // Sequential access
    RANDOM,                 // Random access
    STRIDED,                // Strided access
    COALESCED,              // Coalesced access
    CACHED,                 // Cached access
    PREFETCHED              // Prefetched access
};

// DMA transfer types
enum class DMATransferType {
    HOST_TO_DEVICE,         // Host to device transfer
    DEVICE_TO_HOST,         // Device to host transfer
    DEVICE_TO_DEVICE,       // Device to device transfer
    PEER_TO_PEER,           // Peer to peer transfer
    BIDIRECTIONAL           // Bidirectional transfer
};

// Memory partition configuration
struct MemoryPartitionConfig {
    std::string partitionId;                // Unique partition identifier
    MemoryPartitionType type;               // Partition type
    size_t size;                            // Partition size in bytes
    size_t alignment;                       // Memory alignment
    size_t offset;                          // Memory offset
    void* baseAddress;                      // Base memory address
    void* devicePtr;                        // Device pointer
    void* hostPtr;                          // Host pointer
    std::string ownerLLM;                   // Owner LLM ID
    float priority;                         // Partition priority
    MemoryAccessPattern accessPattern;       // Access pattern
    std::map<std::string, std::string> parameters; // Custom parameters
    std::chrono::system_clock::time_point createdAt; // Creation time
    std::chrono::system_clock::time_point lastUsed;  // Last usage time
};

// DMA transfer configuration
struct DMATransferConfig {
    std::string transferId;                 // Transfer identifier
    DMATransferType type;                   // Transfer type
    void* sourcePtr;                        // Source pointer
    void* destinationPtr;                   // Destination pointer
    size_t size;                           // Transfer size
    cudaStream_t stream;                    // CUDA stream
    std::string ownerLLM;                   // Owner LLM ID
    float priority;                         // Transfer priority
    std::chrono::milliseconds timeout;     // Transfer timeout
    std::map<std::string, std::string> parameters; // Custom parameters
};

// Memory partition interface
class MemoryPartition {
public:
    virtual ~MemoryPartition() = default;

    // Partition lifecycle
    virtual bool initialize() = 0;
    virtual void shutdown() = 0;
    virtual bool isInitialized() const = 0;

    // Partition management
    virtual std::string getPartitionId() const = 0;
    virtual MemoryPartitionType getPartitionType() const = 0;
    virtual MemoryPartitionConfig getConfig() const = 0;
    virtual bool updateConfig(const MemoryPartitionConfig& config) = 0;

    // Memory operations
    virtual bool allocateMemory(size_t size) = 0;
    virtual bool deallocateMemory() = 0;
    virtual bool isMemoryAllocated() const = 0;
    virtual size_t getMemorySize() const = 0;
    virtual size_t getAvailableMemory() const = 0;
    virtual void* getBaseAddress() const = 0;
    virtual void* getDevicePtr() const = 0;
    virtual void* getHostPtr() const = 0;

    // Memory access
    virtual bool readMemory(void* buffer, size_t offset, size_t size) = 0;
    virtual bool writeMemory(const void* buffer, size_t offset, size_t size) = 0;
    virtual bool copyMemory(void* destination, const void* source, size_t size) = 0;
    virtual bool fillMemory(int value, size_t offset, size_t size) = 0;
    virtual bool clearMemory(size_t offset, size_t size) = 0;

    // DMA operations
    virtual bool dmaTransfer(const DMATransferConfig& config) = 0;
    virtual bool dmaTransferAsync(const DMATransferConfig& config) = 0;
    virtual bool waitForTransfer(const std::string& transferId) = 0;
    virtual bool cancelTransfer(const std::string& transferId) = 0;
    virtual std::vector<std::string> getActiveTransfers() const = 0;

    // Performance monitoring
    virtual std::map<std::string, double> getPerformanceMetrics() const = 0;
    virtual float getUtilization() const = 0;
    virtual bool enableProfiling() = 0;
    virtual bool disableProfiling() = 0;
    virtual std::map<std::string, double> getProfilingData() const = 0;

    // Configuration
    virtual bool setPriority(float priority) = 0;
    virtual float getPriority() const = 0;
    virtual bool setAccessPattern(MemoryAccessPattern pattern) = 0;
    virtual MemoryAccessPattern getAccessPattern() const = 0;
};

// Advanced memory partition implementation
class AdvancedMemoryPartition : public MemoryPartition {
public:
    AdvancedMemoryPartition(const MemoryPartitionConfig& config);
    ~AdvancedMemoryPartition() override;

    // Partition lifecycle
    bool initialize() override;
    void shutdown() override;
    bool isInitialized() const override;

    // Partition management
    std::string getPartitionId() const override;
    MemoryPartitionType getPartitionType() const override;
    MemoryPartitionConfig getConfig() const override;
    bool updateConfig(const MemoryPartitionConfig& config) override;

    // Memory operations
    bool allocateMemory(size_t size) override;
    bool deallocateMemory() override;
    bool isMemoryAllocated() const override;
    size_t getMemorySize() const override;
    size_t getAvailableMemory() const override;
    void* getBaseAddress() const override;
    void* getDevicePtr() const override;
    void* getHostPtr() const override;

    // Memory access
    bool readMemory(void* buffer, size_t offset, size_t size) override;
    bool writeMemory(const void* buffer, size_t offset, size_t size) override;
    bool copyMemory(void* destination, const void* source, size_t size) override;
    bool fillMemory(int value, size_t offset, size_t size) override;
    bool clearMemory(size_t offset, size_t size) override;

    // DMA operations
    bool dmaTransfer(const DMATransferConfig& config) override;
    bool dmaTransferAsync(const DMATransferConfig& config) override;
    bool waitForTransfer(const std::string& transferId) override;
    bool cancelTransfer(const std::string& transferId) override;
    std::vector<std::string> getActiveTransfers() const override;

    // Performance monitoring
    std::map<std::string, double> getPerformanceMetrics() const override;
    float getUtilization() const override;
    bool enableProfiling() override;
    bool disableProfiling() override;
    std::map<std::string, double> getProfilingData() const override;

    // Configuration
    bool setPriority(float priority) override;
    float getPriority() const override;
    bool setAccessPattern(MemoryAccessPattern pattern) override;
    MemoryAccessPattern getAccessPattern() const override;

    // Advanced features
    bool optimizeMemoryLayout();
    bool prefetchMemory(size_t offset, size_t size);
    bool invalidateCache(size_t offset, size_t size);
    bool flushCache(size_t offset, size_t size);
    bool setMemoryProtection(size_t offset, size_t size, bool readOnly);
    bool getMemoryInfo(std::map<std::string, std::string>& info) const;
    bool validateMemoryIntegrity(size_t offset, size_t size);
    bool compressMemory(size_t offset, size_t size);
    bool decompressMemory(size_t offset, size_t size);

private:
    // Internal state
    MemoryPartitionConfig config_;
    bool initialized_;
    bool memoryAllocated_;
    size_t allocatedSize_;
    void* deviceMemory_;
    void* hostMemory_;
    std::mutex partitionMutex_;
    std::atomic<bool> profilingEnabled_;

    // DMA transfer tracking
    std::map<std::string, cudaEvent_t> activeTransfers_;
    std::map<std::string, DMATransferConfig> transferConfigs_;
    std::mutex transferMutex_;

    // Performance monitoring
    std::map<std::string, double> performanceMetrics_;
    std::chrono::system_clock::time_point lastUpdateTime_;

    // CUDA resources
    cudaStream_t partitionStream_;
    cudaEvent_t partitionEvent_;

    // Helper methods
    bool initializeCUDA();
    void shutdownCUDA();
    bool allocateDeviceMemory(size_t size);
    void deallocateDeviceMemory();
    bool allocateHostMemory(size_t size);
    void deallocateHostMemory();
    bool validateMemoryAccess(size_t offset, size_t size);
    void updatePerformanceMetrics();
    bool executeDMATransfer(const DMATransferConfig& config);
    bool executeDMATransferAsync(const DMATransferConfig& config);
    void cleanupTransfer(const std::string& transferId);
};

// Memory partitioning manager
class MemoryPartitioningManager {
public:
    MemoryPartitioningManager();
    ~MemoryPartitioningManager();

    // Manager lifecycle
    bool initialize();
    void shutdown();
    bool isInitialized() const;

    // Partition management
    std::shared_ptr<MemoryPartition> createPartition(const MemoryPartitionConfig& config);
    bool destroyPartition(const std::string& partitionId);
    std::shared_ptr<MemoryPartition> getPartition(const std::string& partitionId);
    std::vector<std::shared_ptr<MemoryPartition>> getAllPartitions();
    std::vector<std::shared_ptr<MemoryPartition>> getPartitionsByType(MemoryPartitionType type);
    std::vector<std::shared_ptr<MemoryPartition>> getPartitionsByOwner(const std::string& llmId);

    // Memory operations
    bool allocateMemory(const std::string& partitionId, size_t size);
    bool deallocateMemory(const std::string& partitionId);
    bool isMemoryAvailable(size_t size, MemoryPartitionType type);
    std::vector<std::string> findAvailablePartitions(size_t size, MemoryPartitionType type);

    // DMA operations
    bool dmaTransfer(const DMATransferConfig& config);
    bool dmaTransferAsync(const DMATransferConfig& config);
    bool waitForAllTransfers();
    bool cancelAllTransfers();
    std::vector<std::string> getActiveTransfers();

    // System management
    bool optimizeMemoryLayout();
    bool balanceMemoryUsage();
    bool cleanupUnusedPartitions();
    bool validateSystem();

    // Monitoring and statistics
    std::map<std::string, double> getSystemMetrics();
    std::map<std::string, int> getPartitionCounts();
    std::map<std::string, double> getMemoryUtilization();
    bool enableSystemProfiling();
    bool disableSystemProfiling();
    std::map<std::string, double> getSystemProfilingData();

    // Configuration
    void setMemoryLimits(size_t maxGlobalMemory, size_t maxSharedMemory, size_t maxConstantMemory);
    std::map<std::string, size_t> getMemoryLimits() const;
    void setDMAPolicy(const std::string& policy);
    std::string getDMAPolicy() const;
    void setMemoryAlignment(size_t alignment);
    size_t getMemoryAlignment() const;

private:
    // Internal state
    bool initialized_;
    std::map<std::string, std::shared_ptr<MemoryPartition>> partitions_;
    std::mutex managerMutex_;
    std::atomic<bool> systemProfilingEnabled_;

    // Configuration
    size_t maxGlobalMemory_;
    size_t maxSharedMemory_;
    size_t maxConstantMemory_;
    std::string dmaPolicy_;
    size_t memoryAlignment_;

    // Memory tracking
    size_t totalAllocatedMemory_;
    size_t totalGlobalMemory_;
    size_t totalSharedMemory_;
    size_t totalConstantMemory_;

    // Helper methods
    bool validatePartitionCreation(const MemoryPartitionConfig& config);
    bool validateDMATransfer(const DMATransferConfig& config);
    std::string generatePartitionId();
    bool cleanupPartition(const std::string& partitionId);
    void updateSystemMetrics();
    bool findBestPartition(size_t size, MemoryPartitionType type, std::string& bestPartitionId);
    bool allocateMemoryToPartition(const std::string& partitionId, size_t size);
};

// Global memory partitioning system
class GlobalMemoryPartitioningSystem {
public:
    static GlobalMemoryPartitioningSystem& getInstance();

    // System management
    bool initialize();
    void shutdown();
    bool isInitialized() const;

    // Component access
    std::shared_ptr<MemoryPartitioningManager> getPartitioningManager();
    std::shared_ptr<MemoryPartition> createPartition(const MemoryPartitionConfig& config);
    bool destroyPartition(const std::string& partitionId);
    std::shared_ptr<MemoryPartition> getPartition(const std::string& partitionId);

    // Quick access methods
    bool dmaTransfer(const DMATransferConfig& config);
    bool dmaTransferAsync(const DMATransferConfig& config);
    std::vector<std::shared_ptr<MemoryPartition>> getAllPartitions();
    std::map<std::string, double> getSystemMetrics();

    // Configuration
    void setSystemConfiguration(const std::map<std::string, std::string>& config);
    std::map<std::string, std::string> getSystemConfiguration() const;

private:
    GlobalMemoryPartitioningSystem();
    ~GlobalMemoryPartitioningSystem();

    std::shared_ptr<MemoryPartitioningManager> partitioningManager_;
    bool initialized_;
    std::map<std::string, std::string> configuration_;
    std::mutex systemMutex_;
};

} // namespace memory
} // namespace cogniware
