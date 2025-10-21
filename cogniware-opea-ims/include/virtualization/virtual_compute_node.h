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
namespace virtualization {

// Virtual compute node types
enum class VirtualNodeType {
    TENSOR_CORE_NODE,      // Tensor core virtual node
    CUDA_CORE_NODE,        // CUDA core virtual node
    MEMORY_NODE,           // Memory virtual node
    MIXED_NODE,            // Mixed resource virtual node
    DEDICATED_NODE,        // Dedicated resource virtual node
    SHARED_NODE            // Shared resource virtual node
};

// Node status
enum class NodeStatus {
    CREATING,              // Node is being created
    ACTIVE,                // Node is active and running
    IDLE,                  // Node is idle but available
    SUSPENDED,             // Node is suspended
    DESTROYING,            // Node is being destroyed
    DESTROYED,             // Node has been destroyed
    ERROR                  // Node is in error state
};

// Resource allocation strategy
enum class AllocationStrategy {
    STATIC,                // Static allocation
    DYNAMIC,               // Dynamic allocation
    ADAPTIVE,              // Adaptive allocation
    PREDICTIVE,            // Predictive allocation
    ON_DEMAND              // On-demand allocation
};

// Virtual compute node configuration
struct VirtualNodeConfig {
    std::string nodeId;                    // Unique node identifier
    VirtualNodeType type;                  // Node type
    size_t memorySize;                     // Memory size in bytes
    size_t computeCores;                   // Number of compute cores
    size_t tensorCores;                    // Number of tensor cores
    float priority;                         // Node priority (0.0 - 1.0)
    std::string ownerLLM;                  // Owner LLM ID
    std::map<std::string, std::string> parameters; // Custom parameters
    std::chrono::system_clock::time_point createdAt; // Creation time
    std::chrono::system_clock::time_point lastUsed;  // Last usage time
};

// Resource allocation request
struct ResourceAllocationRequest {
    std::string requestId;                 // Request identifier
    std::string llmId;                     // Requesting LLM ID
    size_t requestedMemory;                // Requested memory size
    size_t requestedCores;                 // Requested compute cores
    size_t requestedTensorCores;           // Requested tensor cores
    float priority;                        // Request priority
    std::chrono::milliseconds timeout;    // Request timeout
    std::map<std::string, std::string> requirements; // Additional requirements
};

// Resource allocation response
struct ResourceAllocationResponse {
    std::string requestId;                 // Request identifier
    bool success;                          // Allocation success
    std::string nodeId;                    // Allocated node ID
    size_t allocatedMemory;                // Allocated memory size
    size_t allocatedCores;                 // Allocated compute cores
    size_t allocatedTensorCores;           // Allocated tensor cores
    std::string error;                     // Error message if failed
    std::chrono::system_clock::time_point allocatedAt; // Allocation time
};

// Virtual compute node interface
class VirtualComputeNode {
public:
    virtual ~VirtualComputeNode() = default;

    // Node lifecycle
    virtual bool initialize() = 0;
    virtual void shutdown() = 0;
    virtual bool isInitialized() const = 0;

    // Node management
    virtual std::string getNodeId() const = 0;
    virtual VirtualNodeType getNodeType() const = 0;
    virtual NodeStatus getStatus() const = 0;
    virtual VirtualNodeConfig getConfig() const = 0;

    // Resource management
    virtual bool allocateResources(const ResourceAllocationRequest& request) = 0;
    virtual bool deallocateResources() = 0;
    virtual bool isResourceAllocated() const = 0;
    virtual size_t getAvailableMemory() const = 0;
    virtual size_t getAvailableCores() const = 0;
    virtual size_t getAvailableTensorCores() const = 0;

    // Task management
    virtual bool executeTask(const std::string& taskId, const std::function<void()>& task) = 0;
    virtual bool cancelTask(const std::string& taskId) = 0;
    virtual std::vector<std::string> getActiveTasks() const = 0;
    virtual bool isTaskRunning(const std::string& taskId) const = 0;

    // Performance monitoring
    virtual std::map<std::string, double> getPerformanceMetrics() const = 0;
    virtual float getUtilization() const = 0;
    virtual bool enableProfiling() = 0;
    virtual bool disableProfiling() = 0;
    virtual std::map<std::string, double> getProfilingData() const = 0;

    // Configuration
    virtual bool updateConfig(const VirtualNodeConfig& config) = 0;
    virtual bool setPriority(float priority) = 0;
    virtual float getPriority() const = 0;
};

// Advanced virtual compute node implementation
class AdvancedVirtualComputeNode : public VirtualComputeNode {
public:
    AdvancedVirtualComputeNode(const VirtualNodeConfig& config);
    ~AdvancedVirtualComputeNode() override;

    // Node lifecycle
    bool initialize() override;
    void shutdown() override;
    bool isInitialized() const override;

    // Node management
    std::string getNodeId() const override;
    VirtualNodeType getNodeType() const override;
    NodeStatus getStatus() const override;
    VirtualNodeConfig getConfig() const override;

    // Resource management
    bool allocateResources(const ResourceAllocationRequest& request) override;
    bool deallocateResources() override;
    bool isResourceAllocated() const override;
    size_t getAvailableMemory() const override;
    size_t getAvailableCores() const override;
    size_t getAvailableTensorCores() const override;

    // Task management
    bool executeTask(const std::string& taskId, const std::function<void()>& task) override;
    bool cancelTask(const std::string& taskId) override;
    std::vector<std::string> getActiveTasks() const override;
    bool isTaskRunning(const std::string& taskId) const override;

    // Performance monitoring
    std::map<std::string, double> getPerformanceMetrics() const override;
    float getUtilization() const override;
    bool enableProfiling() override;
    bool disableProfiling() override;
    std::map<std::string, double> getProfilingData() const override;

    // Configuration
    bool updateConfig(const VirtualNodeConfig& config) override;
    bool setPriority(float priority) override;
    float getPriority() const override;

    // Advanced features
    bool suspend();
    bool resume();
    bool migrate(const std::string& targetNodeId);
    bool clone(const std::string& newNodeId);
    bool scale(size_t newMemorySize, size_t newCores, size_t newTensorCores);
    bool optimize();
    std::map<std::string, std::string> getResourceInfo() const;
    bool validateResources() const;

private:
    // Internal state
    VirtualNodeConfig config_;
    NodeStatus status_;
    bool initialized_;
    bool resourceAllocated_;
    float priority_;
    std::mutex nodeMutex_;
    std::atomic<bool> profilingEnabled_;

    // Resource tracking
    size_t allocatedMemory_;
    size_t allocatedCores_;
    size_t allocatedTensorCores_;
    std::string ownerLLM_;

    // Task management
    std::map<std::string, std::thread> activeTasks_;
    std::map<std::string, std::atomic<bool>> taskCancelled_;
    std::mutex taskMutex_;

    // Performance monitoring
    std::map<std::string, double> performanceMetrics_;
    std::chrono::system_clock::time_point lastUpdateTime_;

    // CUDA resources
    cudaStream_t nodeStream_;
    void* deviceMemory_;
    size_t deviceMemorySize_;

    // Helper methods
    bool initializeCUDA();
    void shutdownCUDA();
    bool allocateDeviceMemory(size_t size);
    void deallocateDeviceMemory();
    bool validateAllocation(const ResourceAllocationRequest& request);
    void updatePerformanceMetrics();
    bool executeTaskInternal(const std::string& taskId, const std::function<void()>& task);
    void cleanupTask(const std::string& taskId);
};

// Virtual compute node manager
class VirtualComputeNodeManager {
public:
    VirtualComputeNodeManager();
    ~VirtualComputeNodeManager();

    // Manager lifecycle
    bool initialize();
    void shutdown();
    bool isInitialized() const;

    // Node creation and management
    std::shared_ptr<VirtualComputeNode> createNode(const VirtualNodeConfig& config);
    bool destroyNode(const std::string& nodeId);
    std::shared_ptr<VirtualComputeNode> getNode(const std::string& nodeId);
    std::vector<std::shared_ptr<VirtualComputeNode>> getAllNodes();
    std::vector<std::shared_ptr<VirtualComputeNode>> getNodesByType(VirtualNodeType type);
    std::vector<std::shared_ptr<VirtualComputeNode>> getNodesByOwner(const std::string& llmId);

    // Resource allocation
    ResourceAllocationResponse allocateResources(const ResourceAllocationRequest& request);
    bool deallocateResources(const std::string& nodeId);
    bool isResourceAvailable(const ResourceAllocationRequest& request);
    std::vector<std::string> findAvailableNodes(const ResourceAllocationRequest& request);

    // Node management
    bool suspendNode(const std::string& nodeId);
    bool resumeNode(const std::string& nodeId);
    bool migrateNode(const std::string& nodeId, const std::string& targetNodeId);
    bool cloneNode(const std::string& nodeId, const std::string& newNodeId);
    bool scaleNode(const std::string& nodeId, size_t newMemorySize, size_t newCores, size_t newTensorCores);

    // System management
    bool optimizeSystem();
    bool balanceLoad();
    bool cleanupIdleNodes();
    bool validateSystem();

    // Monitoring and statistics
    std::map<std::string, double> getSystemMetrics();
    std::map<std::string, int> getNodeCounts();
    std::map<std::string, double> getResourceUtilization();
    bool enableSystemProfiling();
    bool disableSystemProfiling();
    std::map<std::string, double> getSystemProfilingData();

    // Configuration
    void setAllocationStrategy(AllocationStrategy strategy);
    AllocationStrategy getAllocationStrategy() const;
    void setMaxNodes(int maxNodes);
    int getMaxNodes() const;
    void setResourceLimits(size_t maxMemory, size_t maxCores, size_t maxTensorCores);
    std::map<std::string, size_t> getResourceLimits() const;

private:
    // Internal state
    bool initialized_;
    std::map<std::string, std::shared_ptr<VirtualComputeNode>> nodes_;
    std::mutex managerMutex_;
    std::atomic<bool> systemProfilingEnabled_;

    // Configuration
    AllocationStrategy allocationStrategy_;
    int maxNodes_;
    size_t maxMemory_;
    size_t maxCores_;
    size_t maxTensorCores_;

    // Resource tracking
    size_t totalAllocatedMemory_;
    size_t totalAllocatedCores_;
    size_t totalAllocatedTensorCores_;

    // Helper methods
    bool validateNodeCreation(const VirtualNodeConfig& config);
    bool validateResourceAllocation(const ResourceAllocationRequest& request);
    std::string generateNodeId();
    bool cleanupNode(const std::string& nodeId);
    void updateSystemMetrics();
    bool findBestNode(const ResourceAllocationRequest& request, std::string& bestNodeId);
    bool allocateResourcesToNode(const std::string& nodeId, const ResourceAllocationRequest& request);
};

// Global virtual compute node management system
class GlobalVirtualComputeNodeSystem {
public:
    static GlobalVirtualComputeNodeSystem& getInstance();

    // System management
    bool initialize();
    void shutdown();
    bool isInitialized() const;

    // Component access
    std::shared_ptr<VirtualComputeNodeManager> getNodeManager();
    std::shared_ptr<VirtualComputeNode> createNode(const VirtualNodeConfig& config);
    bool destroyNode(const std::string& nodeId);
    std::shared_ptr<VirtualComputeNode> getNode(const std::string& nodeId);

    // Quick access methods
    ResourceAllocationResponse allocateResources(const ResourceAllocationRequest& request);
    bool deallocateResources(const std::string& nodeId);
    std::vector<std::shared_ptr<VirtualComputeNode>> getAllNodes();
    std::map<std::string, double> getSystemMetrics();

    // Configuration
    void setSystemConfiguration(const std::map<std::string, std::string>& config);
    std::map<std::string, std::string> getSystemConfiguration() const;

private:
    GlobalVirtualComputeNodeSystem();
    ~GlobalVirtualComputeNodeSystem();

    std::shared_ptr<VirtualComputeNodeManager> nodeManager_;
    bool initialized_;
    std::map<std::string, std::string> configuration_;
    std::mutex systemMutex_;
};

} // namespace virtualization
} // namespace cogniware
