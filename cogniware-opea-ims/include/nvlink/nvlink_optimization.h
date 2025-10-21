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
namespace nvlink {

// NVLink topology types
enum class NVLinkTopology {
    RING,                   // Ring topology
    MESH,                   // Mesh topology
    TREE,                   // Tree topology
    STAR,                   // Star topology
    CUSTOM                  // Custom topology
};

// NVLink communication patterns
enum class NVLinkPattern {
    POINT_TO_POINT,         // Point-to-point communication
    BROADCAST,              // Broadcast communication
    REDUCE,                 // Reduce communication
    ALL_REDUCE,             // All-reduce communication
    SCATTER,                // Scatter communication
    GATHER,                 // Gather communication
    ALL_GATHER              // All-gather communication
};

// NVLink optimization strategies
enum class NVLinkOptimizationStrategy {
    BANDWIDTH_OPTIMIZATION,  // Optimize for bandwidth
    LATENCY_OPTIMIZATION,    // Optimize for latency
    THROUGHPUT_OPTIMIZATION, // Optimize for throughput
    BALANCED_OPTIMIZATION,   // Balanced optimization
    CUSTOM_OPTIMIZATION      // Custom optimization
};

// NVLink link configuration
struct NVLinkConfig {
    std::string linkId;                     // Link identifier
    int sourceGPU;                          // Source GPU ID
    int destinationGPU;                     // Destination GPU ID
    int linkWidth;                          // Link width (lanes)
    float linkSpeed;                        // Link speed (GB/s)
    float bandwidth;                        // Available bandwidth
    float latency;                          // Link latency (ns)
    bool isActive;                          // Link active status
    NVLinkTopology topology;                // Topology type
    std::map<std::string, std::string> parameters; // Custom parameters
    std::chrono::system_clock::time_point createdAt; // Creation time
    std::chrono::system_clock::time_point lastUsed;  // Last usage time
};

// NVLink communication request
struct NVLinkRequest {
    std::string requestId;                  // Request identifier
    int sourceGPU;                          // Source GPU ID
    int destinationGPU;                     // Destination GPU ID
    void* sourcePtr;                        // Source memory pointer
    void* destinationPtr;                   // Destination memory pointer
    size_t size;                           // Transfer size
    NVLinkPattern pattern;                  // Communication pattern
    float priority;                         // Request priority
    std::chrono::milliseconds timeout;     // Request timeout
    std::map<std::string, std::string> parameters; // Custom parameters
    std::chrono::system_clock::time_point createdAt; // Creation time
};

// NVLink communication response
struct NVLinkResponse {
    std::string requestId;                  // Request identifier
    bool success;                           // Communication success
    float bandwidth;                        // Achieved bandwidth (GB/s)
    float latency;                          // Achieved latency (ns)
    float throughput;                       // Achieved throughput (GB/s)
    std::string error;                      // Error message if failed
    std::chrono::system_clock::time_point completedAt; // Completion time
};

// NVLink optimization interface
class NVLinkOptimizer {
public:
    virtual ~NVLinkOptimizer() = default;

    // Optimizer lifecycle
    virtual bool initialize() = 0;
    virtual void shutdown() = 0;
    virtual bool isInitialized() const = 0;

    // Link management
    virtual std::string getOptimizerId() const = 0;
    virtual NVLinkConfig getConfig() const = 0;
    virtual bool updateConfig(const NVLinkConfig& config) = 0;

    // Communication operations
    virtual std::future<NVLinkResponse> communicateAsync(const NVLinkRequest& request) = 0;
    virtual NVLinkResponse communicate(const NVLinkRequest& request) = 0;
    virtual bool cancelCommunication(const std::string& requestId) = 0;
    virtual std::vector<std::string> getActiveRequests() const = 0;
    virtual bool isRequestActive(const std::string& requestId) const = 0;

    // Optimization operations
    virtual bool optimizeBandwidth() = 0;
    virtual bool optimizeLatency() = 0;
    virtual bool optimizeThroughput() = 0;
    virtual bool optimizeBalanced() = 0;
    virtual bool optimizeCustom(const std::map<std::string, std::string>& params) = 0;

    // Performance monitoring
    virtual std::map<std::string, double> getPerformanceMetrics() const = 0;
    virtual float getUtilization() const = 0;
    virtual bool enableProfiling() = 0;
    virtual bool disableProfiling() = 0;
    virtual std::map<std::string, double> getProfilingData() const = 0;

    // Configuration
    virtual bool setOptimizationStrategy(NVLinkOptimizationStrategy strategy) = 0;
    virtual NVLinkOptimizationStrategy getOptimizationStrategy() const = 0;
};

// Advanced NVLink optimizer implementation
class AdvancedNVLinkOptimizer : public NVLinkOptimizer {
public:
    AdvancedNVLinkOptimizer(const NVLinkConfig& config);
    ~AdvancedNVLinkOptimizer() override;

    // Optimizer lifecycle
    bool initialize() override;
    void shutdown() override;
    bool isInitialized() const override;

    // Link management
    std::string getOptimizerId() const override;
    NVLinkConfig getConfig() const override;
    bool updateConfig(const NVLinkConfig& config) override;

    // Communication operations
    std::future<NVLinkResponse> communicateAsync(const NVLinkRequest& request) override;
    NVLinkResponse communicate(const NVLinkRequest& request) override;
    bool cancelCommunication(const std::string& requestId) override;
    std::vector<std::string> getActiveRequests() const override;
    bool isRequestActive(const std::string& requestId) const override;

    // Optimization operations
    bool optimizeBandwidth() override;
    bool optimizeLatency() override;
    bool optimizeThroughput() override;
    bool optimizeBalanced() override;
    bool optimizeCustom(const std::map<std::string, std::string>& params) override;

    // Performance monitoring
    std::map<std::string, double> getPerformanceMetrics() const override;
    float getUtilization() const override;
    bool enableProfiling() override;
    bool disableProfiling() override;
    std::map<std::string, double> getProfilingData() const override;

    // Configuration
    bool setOptimizationStrategy(NVLinkOptimizationStrategy strategy) override;
    NVLinkOptimizationStrategy getOptimizationStrategy() const override;

    // Advanced features
    bool analyzeTopology();
    bool optimizeTopology();
    bool balanceLoad();
    bool validateLinks();
    std::map<std::string, std::string> getTopologyInfo() const;
    bool setLinkPriority(int linkId, float priority);
    float getLinkPriority(int linkId) const;
    bool enableLink(int linkId);
    bool disableLink(int linkId);
    bool isLinkActive(int linkId) const;

private:
    // Internal state
    NVLinkConfig config_;
    bool initialized_;
    NVLinkOptimizationStrategy optimizationStrategy_;
    std::mutex optimizerMutex_;
    std::atomic<bool> profilingEnabled_;

    // Request tracking
    std::map<std::string, std::future<NVLinkResponse>> activeRequests_;
    std::map<std::string, std::atomic<bool>> requestCancelled_;
    std::mutex requestMutex_;

    // Performance monitoring
    std::map<std::string, double> performanceMetrics_;
    std::chrono::system_clock::time_point lastUpdateTime_;

    // CUDA resources
    cudaStream_t optimizerStream_;
    std::vector<cudaEvent_t> linkEvents_;

    // Helper methods
    bool initializeCUDA();
    void shutdownCUDA();
    bool validateRequest(const NVLinkRequest& request);
    void updatePerformanceMetrics();
    NVLinkResponse communicateInternal(const NVLinkRequest& request);
    void cleanupRequest(const std::string& requestId);
    std::string generateRequestId();
    bool validateLink(int linkId);
    float calculateBandwidth(const NVLinkRequest& request);
    float calculateLatency(const NVLinkRequest& request);
    bool executeCommunication(const NVLinkRequest& request);
};

// NVLink topology manager
class NVLinkTopologyManager {
public:
    NVLinkTopologyManager();
    ~NVLinkTopologyManager();

    // Manager lifecycle
    bool initialize();
    void shutdown();
    bool isInitialized() const;

    // Topology management
    std::shared_ptr<NVLinkOptimizer> createOptimizer(const NVLinkConfig& config);
    bool destroyOptimizer(const std::string& optimizerId);
    std::shared_ptr<NVLinkOptimizer> getOptimizer(const std::string& optimizerId);
    std::vector<std::shared_ptr<NVLinkOptimizer>> getAllOptimizers();
    std::vector<std::shared_ptr<NVLinkOptimizer>> getOptimizersByGPU(int gpuId);
    std::vector<std::shared_ptr<NVLinkOptimizer>> getOptimizersByTopology(NVLinkTopology topology);

    // Communication management
    std::future<NVLinkResponse> communicateAsync(const NVLinkRequest& request);
    NVLinkResponse communicate(const NVLinkRequest& request);
    bool cancelCommunication(const std::string& requestId);
    bool cancelAllCommunications();
    std::vector<std::string> getActiveRequests();
    std::vector<std::string> getActiveRequestsByGPU(int gpuId);

    // Topology operations
    bool analyzeTopology();
    bool optimizeTopology();
    bool balanceLoad();
    bool validateTopology();
    std::map<std::string, std::string> getTopologyInfo() const;

    // System management
    bool optimizeSystem();
    bool balanceLoad();
    bool cleanupIdleOptimizers();
    bool validateSystem();

    // Monitoring and statistics
    std::map<std::string, double> getSystemMetrics();
    std::map<std::string, int> getOptimizerCounts();
    std::map<std::string, double> getCommunicationMetrics();
    bool enableSystemProfiling();
    bool disableSystemProfiling();
    std::map<std::string, double> getSystemProfilingData();

    // Configuration
    void setMaxOptimizers(int maxOptimizers);
    int getMaxOptimizers() const;
    void setTopologyStrategy(const std::string& strategy);
    std::string getTopologyStrategy() const;
    void setLoadBalancingStrategy(const std::string& strategy);
    std::string getLoadBalancingStrategy() const;

private:
    // Internal state
    bool initialized_;
    std::map<std::string, std::shared_ptr<NVLinkOptimizer>> optimizers_;
    std::mutex managerMutex_;
    std::atomic<bool> systemProfilingEnabled_;

    // Configuration
    int maxOptimizers_;
    std::string topologyStrategy_;
    std::string loadBalancingStrategy_;

    // Communication tracking
    std::map<std::string, std::string> requestToOptimizer_;
    std::map<std::string, std::chrono::system_clock::time_point> requestStartTime_;

    // Helper methods
    bool validateOptimizerCreation(const NVLinkConfig& config);
    bool validateCommunicationRequest(const NVLinkRequest& request);
    std::string generateOptimizerId();
    bool cleanupOptimizer(const std::string& optimizerId);
    void updateSystemMetrics();
    bool findBestOptimizer(const NVLinkRequest& request, std::string& bestOptimizerId);
    bool executeOnOptimizer(const std::string& optimizerId, const NVLinkRequest& request);
    std::vector<std::string> selectOptimizersForCommunication(const NVLinkRequest& request);
    bool validateTopologyConfiguration();
    bool optimizeTopologyConfiguration();
    bool balanceTopologyLoad();
};

// Global NVLink optimization system
class GlobalNVLinkOptimizationSystem {
public:
    static GlobalNVLinkOptimizationSystem& getInstance();

    // System management
    bool initialize();
    void shutdown();
    bool isInitialized() const;

    // Component access
    std::shared_ptr<NVLinkTopologyManager> getTopologyManager();
    std::shared_ptr<NVLinkOptimizer> createOptimizer(const NVLinkConfig& config);
    bool destroyOptimizer(const std::string& optimizerId);
    std::shared_ptr<NVLinkOptimizer> getOptimizer(const std::string& optimizerId);

    // Quick access methods
    std::future<NVLinkResponse> communicateAsync(const NVLinkRequest& request);
    NVLinkResponse communicate(const NVLinkRequest& request);
    std::vector<std::shared_ptr<NVLinkOptimizer>> getAllOptimizers();
    std::map<std::string, double> getSystemMetrics();

    // Configuration
    void setSystemConfiguration(const std::map<std::string, std::string>& config);
    std::map<std::string, std::string> getSystemConfiguration() const;

private:
    GlobalNVLinkOptimizationSystem();
    ~GlobalNVLinkOptimizationSystem();

    std::shared_ptr<NVLinkTopologyManager> topologyManager_;
    bool initialized_;
    std::map<std::string, std::string> configuration_;
    std::mutex systemMutex_;
};

} // namespace nvlink
} // namespace cogniware
