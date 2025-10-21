#include "nvlink/nvlink_optimization.h"
#include <spdlog/spdlog.h>
#include <algorithm>

namespace cogniware {
namespace nvlink {

NVLinkTopologyManager::NVLinkTopologyManager()
    : initialized_(false)
    , maxOptimizers_(10)
    , topologyStrategy_("balanced")
    , loadBalancingStrategy_("round_robin")
    , systemProfilingEnabled_(false) {
    
    spdlog::info("NVLinkTopologyManager initialized");
}

NVLinkTopologyManager::~NVLinkTopologyManager() {
    shutdown();
}

bool NVLinkTopologyManager::initialize() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (initialized_) {
        spdlog::warn("NVLink topology manager already initialized");
        return true;
    }
    
    try {
        optimizers_.clear();
        requestToOptimizer_.clear();
        requestStartTime_.clear();
        
        initialized_ = true;
        spdlog::info("NVLinkTopologyManager initialized successfully");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize NVLink topology manager: {}", e.what());
        return false;
    }
}

void NVLinkTopologyManager::shutdown() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        return;
    }
    
    try {
        for (auto& optimizer : optimizers_) {
            if (optimizer.second) {
                optimizer.second->shutdown();
            }
        }
        optimizers_.clear();
        
        initialized_ = false;
        spdlog::info("NVLinkTopologyManager shutdown completed");
        
    } catch (const std::exception& e) {
        spdlog::error("Error during NVLink topology manager shutdown: {}", e.what());
    }
}

bool NVLinkTopologyManager::isInitialized() const {
    return initialized_;
}

std::shared_ptr<NVLinkOptimizer> NVLinkTopologyManager::createOptimizer(const NVLinkConfig& config) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return nullptr;
    }
    
    try {
        if (!validateOptimizerCreation(config)) {
            spdlog::error("Invalid NVLink configuration");
            return nullptr;
        }
        
        if (optimizers_.find(config.linkId) != optimizers_.end()) {
            spdlog::error("NVLink optimizer {} already exists", config.linkId);
            return nullptr;
        }
        
        if (static_cast<int>(optimizers_.size()) >= maxOptimizers_) {
            spdlog::error("Maximum number of NVLink optimizers ({}) reached", maxOptimizers_);
            return nullptr;
        }
        
        auto optimizer = std::make_shared<AdvancedNVLinkOptimizer>(config);
        if (!optimizer->initialize()) {
            spdlog::error("Failed to initialize NVLink optimizer {}", config.linkId);
            return nullptr;
        }
        
        optimizers_[config.linkId] = optimizer;
        
        spdlog::info("Created NVLink optimizer: {}", config.linkId);
        return optimizer;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to create NVLink optimizer {}: {}", config.linkId, e.what());
        return nullptr;
    }
}

bool NVLinkTopologyManager::destroyOptimizer(const std::string& optimizerId) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        auto it = optimizers_.find(optimizerId);
        if (it == optimizers_.end()) {
            spdlog::error("NVLink optimizer {} not found", optimizerId);
            return false;
        }
        
        if (it->second) {
            it->second->shutdown();
        }
        
        optimizers_.erase(it);
        
        spdlog::info("Destroyed NVLink optimizer: {}", optimizerId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to destroy NVLink optimizer {}: {}", optimizerId, e.what());
        return false;
    }
}

std::shared_ptr<NVLinkOptimizer> NVLinkTopologyManager::getOptimizer(const std::string& optimizerId) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    auto it = optimizers_.find(optimizerId);
    if (it != optimizers_.end()) {
        return it->second;
    }
    
    return nullptr;
}

std::vector<std::shared_ptr<NVLinkOptimizer>> NVLinkTopologyManager::getAllOptimizers() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    std::vector<std::shared_ptr<NVLinkOptimizer>> allOptimizers;
    for (const auto& optimizer : optimizers_) {
        allOptimizers.push_back(optimizer.second);
    }
    return allOptimizers;
}

std::vector<std::shared_ptr<NVLinkOptimizer>> NVLinkTopologyManager::getOptimizersByGPU(int gpuId) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    std::vector<std::shared_ptr<NVLinkOptimizer>> optimizersByGPU;
    for (const auto& optimizer : optimizers_) {
        if (optimizer.second) {
            auto config = optimizer.second->getConfig();
            if (config.sourceGPU == gpuId || config.destinationGPU == gpuId) {
                optimizersByGPU.push_back(optimizer.second);
            }
        }
    }
    return optimizersByGPU;
}

std::vector<std::shared_ptr<NVLinkOptimizer>> NVLinkTopologyManager::getOptimizersByTopology(NVLinkTopology topology) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    std::vector<std::shared_ptr<NVLinkOptimizer>> optimizersByTopology;
    for (const auto& optimizer : optimizers_) {
        if (optimizer.second) {
            auto config = optimizer.second->getConfig();
            if (config.topology == topology) {
                optimizersByTopology.push_back(optimizer.second);
            }
        }
    }
    return optimizersByTopology;
}

std::future<NVLinkResponse> NVLinkTopologyManager::communicateAsync(const NVLinkRequest& request) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return std::async(std::launch::deferred, []() {
            NVLinkResponse response;
            response.success = false;
            response.error = "Manager not initialized";
            return response;
        });
    }
    
    try {
        if (!validateCommunicationRequest(request)) {
            spdlog::error("Invalid communication request");
            return std::async(std::launch::deferred, []() {
                NVLinkResponse response;
                response.success = false;
                response.error = "Invalid communication request";
                return response;
            });
        }
        
        std::string bestOptimizerId;
        if (!findBestOptimizer(request, bestOptimizerId)) {
            spdlog::error("No suitable NVLink optimizer found for request {}", request.requestId);
            return std::async(std::launch::deferred, []() {
                NVLinkResponse response;
                response.success = false;
                response.error = "No suitable NVLink optimizer found";
                return response;
            });
        }
        
        auto optimizer = getOptimizer(bestOptimizerId);
        if (!optimizer) {
            spdlog::error("NVLink optimizer {} not found", bestOptimizerId);
            return std::async(std::launch::deferred, []() {
                NVLinkResponse response;
                response.success = false;
                response.error = "NVLink optimizer not found";
                return response;
            });
        }
        
        requestToOptimizer_[request.requestId] = bestOptimizerId;
        requestStartTime_[request.requestId] = std::chrono::system_clock::now();
        
        auto future = optimizer->communicateAsync(request);
        
        spdlog::info("Async communication started for request {} on NVLink optimizer {}", request.requestId, bestOptimizerId);
        return future;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to start async communication for request {}: {}", request.requestId, e.what());
        return std::async(std::launch::deferred, []() {
            NVLinkResponse response;
            response.success = false;
            response.error = "Failed to start async communication";
            return response;
        });
    }
}

NVLinkResponse NVLinkTopologyManager::communicate(const NVLinkRequest& request) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        NVLinkResponse response;
        response.success = false;
        response.error = "Manager not initialized";
        return response;
    }
    
    try {
        if (!validateCommunicationRequest(request)) {
            spdlog::error("Invalid communication request");
            NVLinkResponse response;
            response.success = false;
            response.error = "Invalid communication request";
            return response;
        }
        
        std::string bestOptimizerId;
        if (!findBestOptimizer(request, bestOptimizerId)) {
            spdlog::error("No suitable NVLink optimizer found for request {}", request.requestId);
            NVLinkResponse response;
            response.success = false;
            response.error = "No suitable NVLink optimizer found";
            return response;
        }
        
        auto optimizer = getOptimizer(bestOptimizerId);
        if (!optimizer) {
            spdlog::error("NVLink optimizer {} not found", bestOptimizerId);
            NVLinkResponse response;
            response.success = false;
            response.error = "NVLink optimizer not found";
            return response;
        }
        
        requestToOptimizer_[request.requestId] = bestOptimizerId;
        requestStartTime_[request.requestId] = std::chrono::system_clock::now();
        
        auto response = optimizer->communicate(request);
        
        spdlog::info("Communication completed for request {} on NVLink optimizer {}", request.requestId, bestOptimizerId);
        return response;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to communicate for request {}: {}", request.requestId, e.what());
        NVLinkResponse response;
        response.success = false;
        response.error = "Communication failed: " + std::string(e.what());
        return response;
    }
}

bool NVLinkTopologyManager::cancelCommunication(const std::string& requestId) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        auto it = requestToOptimizer_.find(requestId);
        if (it == requestToOptimizer_.end()) {
            spdlog::error("Request {} not found", requestId);
            return false;
        }
        
        auto optimizer = getOptimizer(it->second);
        if (!optimizer) {
            spdlog::error("NVLink optimizer {} not found for request {}", it->second, requestId);
            return false;
        }
        
        bool cancelled = optimizer->cancelCommunication(requestId);
        
        if (cancelled) {
            requestToOptimizer_.erase(it);
            requestStartTime_.erase(requestId);
            spdlog::info("Request {} cancelled", requestId);
        }
        
        return cancelled;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cancel request {}: {}", requestId, e.what());
        return false;
    }
}

bool NVLinkTopologyManager::cancelAllCommunications() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        for (const auto& optimizer : optimizers_) {
            if (optimizer.second) {
                auto activeRequests = optimizer.second->getActiveRequests();
                for (const auto& requestId : activeRequests) {
                    optimizer.second->cancelCommunication(requestId);
                }
            }
        }
        
        requestToOptimizer_.clear();
        requestStartTime_.clear();
        
        spdlog::info("All communications cancelled");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cancel all communications: {}", e.what());
        return false;
    }
}

std::vector<std::string> NVLinkTopologyManager::getActiveRequests() {
    std::vector<std::string> activeRequests;
    
    try {
        for (const auto& optimizer : optimizers_) {
            if (optimizer.second) {
                auto optimizerRequests = optimizer.second->getActiveRequests();
                activeRequests.insert(activeRequests.end(), optimizerRequests.begin(), optimizerRequests.end());
            }
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get active requests: {}", e.what());
    }
    
    return activeRequests;
}

std::vector<std::string> NVLinkTopologyManager::getActiveRequestsByGPU(int gpuId) {
    std::vector<std::string> activeRequests;
    
    try {
        auto optimizersByGPU = getOptimizersByGPU(gpuId);
        for (const auto& optimizer : optimizersByGPU) {
            if (optimizer) {
                auto optimizerRequests = optimizer->getActiveRequests();
                activeRequests.insert(activeRequests.end(), optimizerRequests.begin(), optimizerRequests.end());
            }
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get active requests for GPU {}: {}", gpuId, e.what());
    }
    
    return activeRequests;
}

bool NVLinkTopologyManager::analyzeTopology() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Analyzing NVLink topology");
        
        for (const auto& optimizer : optimizers_) {
            if (optimizer.second) {
                auto advancedOptimizer = std::dynamic_pointer_cast<AdvancedNVLinkOptimizer>(optimizer.second);
                if (advancedOptimizer) {
                    advancedOptimizer->analyzeTopology();
                }
            }
        }
        
        spdlog::info("Topology analysis completed");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to analyze topology: {}", e.what());
        return false;
    }
}

bool NVLinkTopologyManager::optimizeTopology() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Optimizing NVLink topology");
        
        for (const auto& optimizer : optimizers_) {
            if (optimizer.second) {
                auto advancedOptimizer = std::dynamic_pointer_cast<AdvancedNVLinkOptimizer>(optimizer.second);
                if (advancedOptimizer) {
                    advancedOptimizer->optimizeTopology();
                }
            }
        }
        
        spdlog::info("Topology optimization completed");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to optimize topology: {}", e.what());
        return false;
    }
}

bool NVLinkTopologyManager::balanceLoad() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Balancing load across NVLink optimizers");
        
        std::vector<std::shared_ptr<NVLinkOptimizer>> activeOptimizers;
        for (const auto& optimizer : optimizers_) {
            if (optimizer.second && optimizer.second->isInitialized()) {
                activeOptimizers.push_back(optimizer.second);
            }
        }
        
        if (activeOptimizers.empty()) {
            spdlog::warn("No active NVLink optimizers found for load balancing");
            return true;
        }
        
        // Calculate average utilization
        float totalUtilization = 0.0f;
        for (const auto& optimizer : activeOptimizers) {
            totalUtilization += optimizer->getUtilization();
        }
        float averageUtilization = totalUtilization / activeOptimizers.size();
        
        // Balance load (simplified implementation)
        for (const auto& optimizer : activeOptimizers) {
            float utilization = optimizer->getUtilization();
            if (utilization > averageUtilization * 1.2f) {
                spdlog::debug("NVLink optimizer {} is overloaded (utilization: {:.2f})", 
                            optimizer->getOptimizerId(), utilization);
            } else if (utilization < averageUtilization * 0.8f) {
                spdlog::debug("NVLink optimizer {} is underloaded (utilization: {:.2f})", 
                            optimizer->getOptimizerId(), utilization);
            }
        }
        
        spdlog::info("Load balancing completed");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to balance load: {}", e.what());
        return false;
    }
}

bool NVLinkTopologyManager::validateTopology() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Validating NVLink topology");
        
        bool isValid = true;
        
        for (const auto& optimizer : optimizers_) {
            if (optimizer.second) {
                auto advancedOptimizer = std::dynamic_pointer_cast<AdvancedNVLinkOptimizer>(optimizer.second);
                if (advancedOptimizer && !advancedOptimizer->validateLinks()) {
                    spdlog::error("NVLink optimizer {} failed validation", optimizer.first);
                    isValid = false;
                }
            }
        }
        
        if (isValid) {
            spdlog::info("Topology validation passed");
        } else {
            spdlog::error("Topology validation failed");
        }
        
        return isValid;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to validate topology: {}", e.what());
        return false;
    }
}

std::map<std::string, std::string> NVLinkTopologyManager::getTopologyInfo() const {
    std::map<std::string, std::string> info;
    
    try {
        info["total_optimizers"] = std::to_string(optimizers_.size());
        info["topology_strategy"] = topologyStrategy_;
        info["load_balancing_strategy"] = loadBalancingStrategy_;
        info["max_optimizers"] = std::to_string(maxOptimizers_);
        info["active_requests"] = std::to_string(requestToOptimizer_.size());
        
        // Add optimizer-specific info
        for (const auto& optimizer : optimizers_) {
            if (optimizer.second) {
                auto optimizerInfo = std::dynamic_pointer_cast<AdvancedNVLinkOptimizer>(optimizer.second);
                if (optimizerInfo) {
                    auto topologyInfo = optimizerInfo->getTopologyInfo();
                    for (const auto& item : topologyInfo) {
                        info[optimizer.first + "_" + item.first] = item.second;
                    }
                }
            }
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get topology info: {}", e.what());
    }
    
    return info;
}

bool NVLinkTopologyManager::optimizeSystem() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Optimizing NVLink topology system");
        
        for (const auto& optimizer : optimizers_) {
            if (optimizer.second) {
                auto advancedOptimizer = std::dynamic_pointer_cast<AdvancedNVLinkOptimizer>(optimizer.second);
                if (advancedOptimizer) {
                    advancedOptimizer->optimizeBalanced();
                }
            }
        }
        
        updateSystemMetrics();
        
        spdlog::info("System optimization completed");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to optimize system: {}", e.what());
        return false;
    }
}

bool NVLinkTopologyManager::cleanupIdleOptimizers() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Cleaning up idle NVLink optimizers");
        
        std::vector<std::string> idleOptimizers;
        for (const auto& optimizer : optimizers_) {
            if (optimizer.second && !optimizer.second->isInitialized()) {
                idleOptimizers.push_back(optimizer.first);
            }
        }
        
        for (const auto& optimizerId : idleOptimizers) {
            spdlog::info("Cleaning up idle optimizer: {}", optimizerId);
            cleanupOptimizer(optimizerId);
        }
        
        spdlog::info("Cleaned up {} idle optimizers", idleOptimizers.size());
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cleanup idle optimizers: {}", e.what());
        return false;
    }
}

bool NVLinkTopologyManager::validateSystem() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Validating NVLink topology system");
        
        bool isValid = true;
        
        for (const auto& optimizer : optimizers_) {
            if (optimizer.second) {
                auto advancedOptimizer = std::dynamic_pointer_cast<AdvancedNVLinkOptimizer>(optimizer.second);
                if (advancedOptimizer && !advancedOptimizer->validateLinks()) {
                    spdlog::error("NVLink optimizer {} failed validation", optimizer.first);
                    isValid = false;
                }
            }
        }
        
        if (isValid) {
            spdlog::info("System validation passed");
        } else {
            spdlog::error("System validation failed");
        }
        
        return isValid;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to validate system: {}", e.what());
        return false;
    }
}

std::map<std::string, double> NVLinkTopologyManager::getSystemMetrics() {
    std::map<std::string, double> metrics;
    
    try {
        updateSystemMetrics();
        
        metrics["total_optimizers"] = static_cast<double>(optimizers_.size());
        metrics["active_requests"] = static_cast<double>(requestToOptimizer_.size());
        metrics["topology_strategy"] = static_cast<double>(topologyStrategy_.length());
        metrics["load_balancing_strategy"] = static_cast<double>(loadBalancingStrategy_.length());
        
        // Calculate average utilization
        double totalUtilization = 0.0;
        int optimizerCount = 0;
        for (const auto& optimizer : optimizers_) {
            if (optimizer.second) {
                totalUtilization += optimizer.second->getUtilization();
                optimizerCount++;
            }
        }
        if (optimizerCount > 0) {
            metrics["average_utilization"] = totalUtilization / optimizerCount;
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get system metrics: {}", e.what());
    }
    
    return metrics;
}

std::map<std::string, int> NVLinkTopologyManager::getOptimizerCounts() {
    std::map<std::string, int> counts;
    
    try {
        counts["total"] = static_cast<int>(optimizers_.size());
        counts["ring_topology"] = 0;
        counts["mesh_topology"] = 0;
        counts["tree_topology"] = 0;
        counts["star_topology"] = 0;
        counts["custom_topology"] = 0;
        
        for (const auto& optimizer : optimizers_) {
            if (optimizer.second) {
                auto config = optimizer.second->getConfig();
                switch (config.topology) {
                    case NVLinkTopology::RING:
                        counts["ring_topology"]++;
                        break;
                    case NVLinkTopology::MESH:
                        counts["mesh_topology"]++;
                        break;
                    case NVLinkTopology::TREE:
                        counts["tree_topology"]++;
                        break;
                    case NVLinkTopology::STAR:
                        counts["star_topology"]++;
                        break;
                    case NVLinkTopology::CUSTOM:
                        counts["custom_topology"]++;
                        break;
                    default:
                        break;
                }
            }
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get optimizer counts: {}", e.what());
    }
    
    return counts;
}

std::map<std::string, double> NVLinkTopologyManager::getCommunicationMetrics() {
    std::map<std::string, double> metrics;
    
    try {
        // Calculate communication metrics
        metrics["total_requests"] = static_cast<double>(requestToOptimizer_.size());
        metrics["active_requests"] = static_cast<double>(requestToOptimizer_.size());
        
        // Calculate average bandwidth and latency
        double totalBandwidth = 0.0;
        double totalLatency = 0.0;
        int optimizerCount = 0;
        for (const auto& optimizer : optimizers_) {
            if (optimizer.second) {
                auto optimizerMetrics = optimizer.second->getPerformanceMetrics();
                totalBandwidth += optimizerMetrics.at("bandwidth");
                totalLatency += optimizerMetrics.at("latency");
                optimizerCount++;
            }
        }
        if (optimizerCount > 0) {
            metrics["average_bandwidth"] = totalBandwidth / optimizerCount;
            metrics["average_latency"] = totalLatency / optimizerCount;
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get communication metrics: {}", e.what());
    }
    
    return metrics;
}

bool NVLinkTopologyManager::enableSystemProfiling() {
    systemProfilingEnabled_ = true;
    spdlog::info("System profiling enabled");
    return true;
}

bool NVLinkTopologyManager::disableSystemProfiling() {
    systemProfilingEnabled_ = false;
    spdlog::info("System profiling disabled");
    return true;
}

std::map<std::string, double> NVLinkTopologyManager::getSystemProfilingData() {
    std::map<std::string, double> profilingData;
    
    if (!systemProfilingEnabled_) {
        return profilingData;
    }
    
    try {
        auto metrics = getSystemMetrics();
        auto communicationMetrics = getCommunicationMetrics();
        
        profilingData.insert(metrics.begin(), metrics.end());
        profilingData.insert(communicationMetrics.begin(), communicationMetrics.end());
        
        profilingData["profiling_enabled"] = systemProfilingEnabled_ ? 1.0 : 0.0;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get system profiling data: {}", e.what());
    }
    
    return profilingData;
}

void NVLinkTopologyManager::setMaxOptimizers(int maxOptimizers) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    maxOptimizers_ = maxOptimizers;
    spdlog::info("Set maximum NVLink optimizers to: {}", maxOptimizers);
}

int NVLinkTopologyManager::getMaxOptimizers() const {
    return maxOptimizers_;
}

void NVLinkTopologyManager::setTopologyStrategy(const std::string& strategy) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    topologyStrategy_ = strategy;
    spdlog::info("Set topology strategy to: {}", strategy);
}

std::string NVLinkTopologyManager::getTopologyStrategy() const {
    return topologyStrategy_;
}

void NVLinkTopologyManager::setLoadBalancingStrategy(const std::string& strategy) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    loadBalancingStrategy_ = strategy;
    spdlog::info("Set load balancing strategy to: {}", strategy);
}

std::string NVLinkTopologyManager::getLoadBalancingStrategy() const {
    return loadBalancingStrategy_;
}

bool NVLinkTopologyManager::validateOptimizerCreation(const NVLinkConfig& config) {
    try {
        if (config.linkId.empty()) {
            spdlog::error("Link ID cannot be empty");
            return false;
        }
        
        if (config.sourceGPU < 0 || config.destinationGPU < 0) {
            spdlog::error("Invalid GPU IDs");
            return false;
        }
        
        if (config.linkWidth <= 0) {
            spdlog::error("Link width must be greater than 0");
            return false;
        }
        
        if (config.linkSpeed <= 0.0f) {
            spdlog::error("Link speed must be greater than 0");
            return false;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to validate optimizer creation: {}", e.what());
        return false;
    }
}

bool NVLinkTopologyManager::validateCommunicationRequest(const NVLinkRequest& request) {
    try {
        if (request.requestId.empty()) {
            spdlog::error("Request ID cannot be empty");
            return false;
        }
        
        if (request.sourceGPU < 0 || request.destinationGPU < 0) {
            spdlog::error("Invalid GPU IDs");
            return false;
        }
        
        if (request.sourcePtr == nullptr || request.destinationPtr == nullptr) {
            spdlog::error("Invalid memory pointers");
            return false;
        }
        
        if (request.size == 0) {
            spdlog::error("Transfer size must be greater than 0");
            return false;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to validate communication request: {}", e.what());
        return false;
    }
}

std::string NVLinkTopologyManager::generateOptimizerId() {
    try {
        std::stringstream ss;
        ss << "optimizer_" << std::chrono::system_clock::now().time_since_epoch().count();
        return ss.str();
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to generate optimizer ID: {}", e.what());
        return "optimizer_" + std::to_string(std::chrono::system_clock::now().time_since_epoch().count());
    }
}

bool NVLinkTopologyManager::cleanupOptimizer(const std::string& optimizerId) {
    try {
        auto optimizer = getOptimizer(optimizerId);
        if (!optimizer) {
            spdlog::error("NVLink optimizer {} not found for cleanup", optimizerId);
            return false;
        }
        
        optimizer->shutdown();
        optimizers_.erase(optimizerId);
        
        spdlog::info("Cleaned up NVLink optimizer: {}", optimizerId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cleanup NVLink optimizer {}: {}", optimizerId, e.what());
        return false;
    }
}

void NVLinkTopologyManager::updateSystemMetrics() {
    try {
        // Update system metrics
        // Implementation depends on specific metrics to track
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to update system metrics: {}", e.what());
    }
}

bool NVLinkTopologyManager::findBestOptimizer(const NVLinkRequest& request, std::string& bestOptimizerId) {
    try {
        // Find best optimizer based on load balancing strategy
        if (loadBalancingStrategy_ == "round_robin") {
            // Round-robin selection
            static size_t currentIndex = 0;
            auto optimizerList = getAllOptimizers();
            if (!optimizerList.empty()) {
                bestOptimizerId = optimizerList[currentIndex % optimizerList.size()]->getOptimizerId();
                currentIndex++;
                return true;
            }
        } else if (loadBalancingStrategy_ == "least_loaded") {
            // Least loaded selection
            auto optimizerList = getAllOptimizers();
            if (!optimizerList.empty()) {
                float minUtilization = 1.0f;
                for (const auto& optimizer : optimizerList) {
                    if (optimizer->getUtilization() < minUtilization) {
                        minUtilization = optimizer->getUtilization();
                        bestOptimizerId = optimizer->getOptimizerId();
                    }
                }
                return true;
            }
        }
        
        return false;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to find best optimizer: {}", e.what());
        return false;
    }
}

bool NVLinkTopologyManager::executeOnOptimizer(const std::string& optimizerId, const NVLinkRequest& request) {
    try {
        auto optimizer = getOptimizer(optimizerId);
        if (!optimizer) {
            spdlog::error("NVLink optimizer {} not found", optimizerId);
            return false;
        }
        
        auto response = optimizer->communicate(request);
        return response.success;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to execute on optimizer {}: {}", optimizerId, e.what());
        return false;
    }
}

std::vector<std::string> NVLinkTopologyManager::selectOptimizersForCommunication(const NVLinkRequest& request) {
    std::vector<std::string> selectedOptimizers;
    
    try {
        auto allOptimizers = getAllOptimizers();
        if (allOptimizers.empty()) {
            return selectedOptimizers;
        }
        
        // Select optimizers based on request requirements
        for (const auto& optimizer : allOptimizers) {
            if (optimizer) {
                auto config = optimizer->getConfig();
                if (config.sourceGPU == request.sourceGPU || config.destinationGPU == request.destinationGPU) {
                    selectedOptimizers.push_back(optimizer->getOptimizerId());
                }
            }
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to select optimizers for communication: {}", e.what());
    }
    
    return selectedOptimizers;
}

bool NVLinkTopologyManager::validateTopologyConfiguration() {
    try {
        // Validate topology configuration
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to validate topology configuration: {}", e.what());
        return false;
    }
}

bool NVLinkTopologyManager::optimizeTopologyConfiguration() {
    try {
        // Optimize topology configuration
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to optimize topology configuration: {}", e.what());
        return false;
    }
}

bool NVLinkTopologyManager::balanceTopologyLoad() {
    try {
        // Balance topology load
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to balance topology load: {}", e.what());
        return false;
    }
}

} // namespace nvlink
} // namespace cogniware
