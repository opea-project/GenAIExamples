#include "orchestration/multi_llm_orchestrator.h"
#include <spdlog/spdlog.h>
#include <algorithm>

namespace cogniware {
namespace orchestration {

MultiLLMOrchestratorManager::MultiLLMOrchestratorManager()
    : initialized_(false)
    , maxOrchestrators_(10)
    , orchestrationStrategy_("parallel")
    , loadBalancingStrategy_("round_robin")
    , systemProfilingEnabled_(false) {
    
    spdlog::info("MultiLLMOrchestratorManager initialized");
}

MultiLLMOrchestratorManager::~MultiLLMOrchestratorManager() {
    shutdown();
}

bool MultiLLMOrchestratorManager::initialize() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (initialized_) {
        spdlog::warn("Multi-LLM orchestrator manager already initialized");
        return true;
    }
    
    try {
        orchestrators_.clear();
        requestToOrchestrator_.clear();
        requestStartTime_.clear();
        llmToOrchestrators_.clear();
        
        initialized_ = true;
        spdlog::info("MultiLLMOrchestratorManager initialized successfully");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize multi-LLM orchestrator manager: {}", e.what());
        return false;
    }
}

void MultiLLMOrchestratorManager::shutdown() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        return;
    }
    
    try {
        for (auto& orchestrator : orchestrators_) {
            if (orchestrator.second) {
                orchestrator.second->shutdown();
            }
        }
        orchestrators_.clear();
        
        initialized_ = false;
        spdlog::info("MultiLLMOrchestratorManager shutdown completed");
        
    } catch (const std::exception& e) {
        spdlog::error("Error during multi-LLM orchestrator manager shutdown: {}", e.what());
    }
}

bool MultiLLMOrchestratorManager::isInitialized() const {
    return initialized_;
}

std::shared_ptr<MultiLLMOrchestrator> MultiLLMOrchestratorManager::createOrchestrator(const OrchestrationConfig& config) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return nullptr;
    }
    
    try {
        if (!validateOrchestratorCreation(config)) {
            spdlog::error("Invalid orchestrator configuration");
            return nullptr;
        }
        
        if (orchestrators_.find(config.orchestratorId) != orchestrators_.end()) {
            spdlog::error("Multi-LLM orchestrator {} already exists", config.orchestratorId);
            return nullptr;
        }
        
        if (static_cast<int>(orchestrators_.size()) >= maxOrchestrators_) {
            spdlog::error("Maximum number of orchestrators ({}) reached", maxOrchestrators_);
            return nullptr;
        }
        
        auto orchestrator = std::make_shared<AdvancedMultiLLMOrchestrator>(config);
        if (!orchestrator->initialize()) {
            spdlog::error("Failed to initialize multi-LLM orchestrator {}", config.orchestratorId);
            return nullptr;
        }
        
        orchestrators_[config.orchestratorId] = orchestrator;
        
        spdlog::info("Created multi-LLM orchestrator: {}", config.orchestratorId);
        return orchestrator;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to create multi-LLM orchestrator {}: {}", config.orchestratorId, e.what());
        return nullptr;
    }
}

bool MultiLLMOrchestratorManager::destroyOrchestrator(const std::string& orchestratorId) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        auto it = orchestrators_.find(orchestratorId);
        if (it == orchestrators_.end()) {
            spdlog::error("Multi-LLM orchestrator {} not found", orchestratorId);
            return false;
        }
        
        if (it->second) {
            it->second->shutdown();
        }
        
        orchestrators_.erase(it);
        
        spdlog::info("Destroyed multi-LLM orchestrator: {}", orchestratorId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to destroy multi-LLM orchestrator {}: {}", orchestratorId, e.what());
        return false;
    }
}

std::shared_ptr<MultiLLMOrchestrator> MultiLLMOrchestratorManager::getOrchestrator(const std::string& orchestratorId) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    auto it = orchestrators_.find(orchestratorId);
    if (it != orchestrators_.end()) {
        return it->second;
    }
    
    return nullptr;
}

std::vector<std::shared_ptr<MultiLLMOrchestrator>> MultiLLMOrchestratorManager::getAllOrchestrators() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    std::vector<std::shared_ptr<MultiLLMOrchestrator>> allOrchestrators;
    for (const auto& orchestrator : orchestrators_) {
        allOrchestrators.push_back(orchestrator.second);
    }
    return allOrchestrators;
}

std::vector<std::shared_ptr<MultiLLMOrchestrator>> MultiLLMOrchestratorManager::getOrchestratorsByType(OrchestrationType type) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    std::vector<std::shared_ptr<MultiLLMOrchestrator>> orchestratorsByType;
    for (const auto& orchestrator : orchestrators_) {
        if (orchestrator.second && orchestrator.second->getOrchestrationType() == type) {
            orchestratorsByType.push_back(orchestrator.second);
        }
    }
    return orchestratorsByType;
}

std::future<AggregatedResult> MultiLLMOrchestratorManager::processRequestAsync(const std::string& requestId, const std::string& prompt, const std::map<std::string, std::string>& parameters) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return std::async(std::launch::deferred, []() {
            AggregatedResult result;
            result.requestId = "";
            result.confidence = 0.0f;
            return result;
        });
    }
    
    try {
        if (!validateRequestParameters(parameters)) {
            spdlog::error("Invalid request parameters");
            return std::async(std::launch::deferred, []() {
                AggregatedResult result;
                result.requestId = "";
                result.confidence = 0.0f;
                return result;
            });
        }
        
        std::string bestOrchestratorId;
        if (!findBestOrchestrator(prompt, parameters, bestOrchestratorId)) {
            spdlog::error("No suitable orchestrator found for request {}", requestId);
            return std::async(std::launch::deferred, []() {
                AggregatedResult result;
                result.requestId = "";
                result.confidence = 0.0f;
                return result;
            });
        }
        
        auto orchestrator = getOrchestrator(bestOrchestratorId);
        if (!orchestrator) {
            spdlog::error("Orchestrator {} not found for request {}", bestOrchestratorId, requestId);
            return std::async(std::launch::deferred, []() {
                AggregatedResult result;
                result.requestId = "";
                result.confidence = 0.0f;
                return result;
            });
        }
        
        // Track request
        requestToOrchestrator_[requestId] = bestOrchestratorId;
        requestStartTime_[requestId] = std::chrono::system_clock::now();
        
        // Process request
        auto future = orchestrator->processRequestAsync(requestId, prompt, parameters);
        
        spdlog::info("Request {} assigned to orchestrator {}", requestId, bestOrchestratorId);
        return future;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to process async request {}: {}", requestId, e.what());
        return std::async(std::launch::deferred, []() {
            AggregatedResult result;
            result.requestId = "";
            result.confidence = 0.0f;
            return result;
        });
    }
}

AggregatedResult MultiLLMOrchestratorManager::processRequest(const std::string& requestId, const std::string& prompt, const std::map<std::string, std::string>& parameters) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        AggregatedResult result;
        result.requestId = requestId;
        result.confidence = 0.0f;
        return result;
    }
    
    try {
        if (!validateRequestParameters(parameters)) {
            spdlog::error("Invalid request parameters");
            AggregatedResult result;
            result.requestId = requestId;
            result.confidence = 0.0f;
            return result;
        }
        
        std::string bestOrchestratorId;
        if (!findBestOrchestrator(prompt, parameters, bestOrchestratorId)) {
            spdlog::error("No suitable orchestrator found for request {}", requestId);
            AggregatedResult result;
            result.requestId = requestId;
            result.confidence = 0.0f;
            return result;
        }
        
        auto orchestrator = getOrchestrator(bestOrchestratorId);
        if (!orchestrator) {
            spdlog::error("Orchestrator {} not found for request {}", bestOrchestratorId, requestId);
            AggregatedResult result;
            result.requestId = requestId;
            result.confidence = 0.0f;
            return result;
        }
        
        // Track request
        requestToOrchestrator_[requestId] = bestOrchestratorId;
        requestStartTime_[requestId] = std::chrono::system_clock::now();
        
        // Process request
        auto result = orchestrator->processRequest(requestId, prompt, parameters);
        
        spdlog::info("Request {} processed by orchestrator {}", requestId, bestOrchestratorId);
        return result;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to process request {}: {}", requestId, e.what());
        AggregatedResult result;
        result.requestId = requestId;
        result.confidence = 0.0f;
        return result;
    }
}

bool MultiLLMOrchestratorManager::cancelRequest(const std::string& requestId) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        auto it = requestToOrchestrator_.find(requestId);
        if (it == requestToOrchestrator_.end()) {
            spdlog::error("Request {} not found", requestId);
            return false;
        }
        
        auto orchestrator = getOrchestrator(it->second);
        if (!orchestrator) {
            spdlog::error("Orchestrator {} not found for request {}", it->second, requestId);
            return false;
        }
        
        bool cancelled = orchestrator->cancelRequest(requestId);
        
        if (cancelled) {
            requestToOrchestrator_.erase(it);
            requestStartTime_.erase(requestId);
            spdlog::info("Request {} cancelled", requestId);
        }
        
        return cancelled;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cancel request {}: {}", requestId, e.what());
        return false;
    }
}

bool MultiLLMOrchestratorManager::cancelAllRequests() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        bool allCancelled = true;
        
        for (const auto& request : requestToOrchestrator_) {
            auto orchestrator = getOrchestrator(request.second);
            if (orchestrator) {
                if (!orchestrator->cancelRequest(request.first)) {
                    allCancelled = false;
                }
            }
        }
        
        requestToOrchestrator_.clear();
        requestStartTime_.clear();
        
        spdlog::info("All requests cancelled");
        return allCancelled;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cancel all requests: {}", e.what());
        return false;
    }
}

std::vector<std::string> MultiLLMOrchestratorManager::getActiveRequests() {
    std::vector<std::string> activeRequestIds;
    
    try {
        for (const auto& orchestrator : orchestrators_) {
            if (orchestrator.second) {
                auto orchestratorRequests = orchestrator.second->getActiveRequests();
                activeRequestIds.insert(activeRequestIds.end(), orchestratorRequests.begin(), orchestratorRequests.end());
            }
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get active requests: {}", e.what());
    }
    
    return activeRequestIds;
}

std::vector<std::string> MultiLLMOrchestratorManager::getActiveRequestsByOrchestrator(const std::string& orchestratorId) {
    std::vector<std::string> activeRequestIds;
    
    try {
        auto orchestrator = getOrchestrator(orchestratorId);
        if (orchestrator) {
            activeRequestIds = orchestrator->getActiveRequests();
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get active requests for orchestrator {}: {}", orchestratorId, e.what());
    }
    
    return activeRequestIds;
}

bool MultiLLMOrchestratorManager::registerLLM(const LLMInstance& llmInstance) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        // Register LLM with all orchestrators
        bool registered = true;
        for (const auto& orchestrator : orchestrators_) {
            if (orchestrator.second) {
                if (!orchestrator.second->registerLLM(llmInstance)) {
                    registered = false;
                }
            }
        }
        
        if (registered) {
            spdlog::info("LLM {} registered with all orchestrators", llmInstance.llmId);
        } else {
            spdlog::warn("LLM {} registration failed on some orchestrators", llmInstance.llmId);
        }
        
        return registered;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to register LLM {}: {}", llmInstance.llmId, e.what());
        return false;
    }
}

bool MultiLLMOrchestratorManager::unregisterLLM(const std::string& llmId) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        // Unregister LLM from all orchestrators
        bool unregistered = true;
        for (const auto& orchestrator : orchestrators_) {
            if (orchestrator.second) {
                if (!orchestrator.second->unregisterLLM(llmId)) {
                    unregistered = false;
                }
            }
        }
        
        if (unregistered) {
            spdlog::info("LLM {} unregistered from all orchestrators", llmId);
        } else {
            spdlog::warn("LLM {} unregistration failed on some orchestrators", llmId);
        }
        
        return unregistered;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to unregister LLM {}: {}", llmId, e.what());
        return false;
    }
}

std::vector<LLMInstance> MultiLLMOrchestratorManager::getRegisteredLLMs() {
    std::vector<LLMInstance> allLLMs;
    
    try {
        for (const auto& orchestrator : orchestrators_) {
            if (orchestrator.second) {
                auto orchestratorLLMs = orchestrator.second->getRegisteredLLMs();
                allLLMs.insert(allLLMs.end(), orchestratorLLMs.begin(), orchestratorLLMs.end());
            }
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get registered LLMs: {}", e.what());
    }
    
    return allLLMs;
}

LLMInstance MultiLLMOrchestratorManager::getLLMInstance(const std::string& llmId) {
    LLMInstance llmInstance;
    llmInstance.llmId = llmId;
    
    try {
        for (const auto& orchestrator : orchestrators_) {
            if (orchestrator.second) {
                auto instance = orchestrator.second->getLLMInstance(llmId);
                if (!instance.llmId.empty()) {
                    return instance;
                }
            }
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get LLM instance {}: {}", llmId, e.what());
    }
    
    return llmInstance;
}

bool MultiLLMOrchestratorManager::optimizeSystem() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Optimizing multi-LLM orchestration system");
        
        for (const auto& orchestrator : orchestrators_) {
            if (orchestrator.second) {
                auto advancedOrchestrator = std::dynamic_pointer_cast<AdvancedMultiLLMOrchestrator>(orchestrator.second);
                if (advancedOrchestrator) {
                    advancedOrchestrator->optimizeOrchestration();
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

bool MultiLLMOrchestratorManager::balanceLoad() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Balancing load across multi-LLM orchestrators");
        
        std::vector<std::shared_ptr<MultiLLMOrchestrator>> activeOrchestrators;
        for (const auto& orchestrator : orchestrators_) {
            if (orchestrator.second && orchestrator.second->isInitialized()) {
                activeOrchestrators.push_back(orchestrator.second);
            }
        }
        
        if (activeOrchestrators.empty()) {
            spdlog::warn("No active orchestrators found for load balancing");
            return true;
        }
        
        // Calculate average utilization
        float totalUtilization = 0.0f;
        for (const auto& orchestrator : activeOrchestrators) {
            totalUtilization += orchestrator->getUtilization();
        }
        float averageUtilization = totalUtilization / activeOrchestrators.size();
        
        // Balance load (simplified implementation)
        for (const auto& orchestrator : activeOrchestrators) {
            float utilization = orchestrator->getUtilization();
            if (utilization > averageUtilization * 1.2f) {
                spdlog::debug("Orchestrator {} is overloaded (utilization: {:.2f})", 
                            orchestrator->getOrchestratorId(), utilization);
            } else if (utilization < averageUtilization * 0.8f) {
                spdlog::debug("Orchestrator {} is underloaded (utilization: {:.2f})", 
                            orchestrator->getOrchestratorId(), utilization);
            }
        }
        
        spdlog::info("Load balancing completed");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to balance load: {}", e.what());
        return false;
    }
}

bool MultiLLMOrchestratorManager::cleanupIdleOrchestrators() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Cleaning up idle multi-LLM orchestrators");
        
        std::vector<std::string> idleOrchestrators;
        for (const auto& orchestrator : orchestrators_) {
            if (orchestrator.second && !orchestrator.second->isInitialized()) {
                idleOrchestrators.push_back(orchestrator.first);
            }
        }
        
        for (const auto& orchestratorId : idleOrchestrators) {
            spdlog::info("Cleaning up idle orchestrator: {}", orchestratorId);
            cleanupOrchestrator(orchestratorId);
        }
        
        spdlog::info("Cleaned up {} idle orchestrators", idleOrchestrators.size());
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cleanup idle orchestrators: {}", e.what());
        return false;
    }
}

bool MultiLLMOrchestratorManager::validateSystem() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Validating multi-LLM orchestration system");
        
        bool isValid = true;
        
        for (const auto& orchestrator : orchestrators_) {
            if (orchestrator.second) {
                auto advancedOrchestrator = std::dynamic_pointer_cast<AdvancedMultiLLMOrchestrator>(orchestrator.second);
                if (advancedOrchestrator && !advancedOrchestrator->validateConfiguration()) {
                    spdlog::error("Orchestrator {} failed validation", orchestrator.first);
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

std::map<std::string, double> MultiLLMOrchestratorManager::getSystemMetrics() {
    std::map<std::string, double> metrics;
    
    try {
        updateSystemMetrics();
        
        metrics["total_orchestrators"] = static_cast<double>(orchestrators_.size());
        metrics["active_requests"] = static_cast<double>(requestToOrchestrator_.size());
        metrics["registered_llms"] = static_cast<double>(getRegisteredLLMs().size());
        metrics["orchestration_strategy"] = static_cast<double>(orchestrationStrategy_.length());
        metrics["load_balancing_strategy"] = static_cast<double>(loadBalancingStrategy_.length());
        
        // Calculate average utilization
        double totalUtilization = 0.0;
        int orchestratorCount = 0;
        for (const auto& orchestrator : orchestrators_) {
            if (orchestrator.second) {
                totalUtilization += orchestrator.second->getUtilization();
                orchestratorCount++;
            }
        }
        if (orchestratorCount > 0) {
            metrics["average_utilization"] = totalUtilization / orchestratorCount;
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get system metrics: {}", e.what());
    }
    
    return metrics;
}

std::map<std::string, int> MultiLLMOrchestratorManager::getOrchestratorCounts() {
    std::map<std::string, int> counts;
    
    try {
        counts["total"] = static_cast<int>(orchestrators_.size());
        counts["parallel"] = 0;
        counts["sequential"] = 0;
        counts["pipeline"] = 0;
        counts["hybrid"] = 0;
        
        for (const auto& orchestrator : orchestrators_) {
            if (orchestrator.second) {
                switch (orchestrator.second->getOrchestrationType()) {
                    case OrchestrationType::PARALLEL:
                        counts["parallel"]++;
                        break;
                    case OrchestrationType::SEQUENTIAL:
                        counts["sequential"]++;
                        break;
                    case OrchestrationType::PIPELINE:
                        counts["pipeline"]++;
                        break;
                    case OrchestrationType::HYBRID:
                        counts["hybrid"]++;
                        break;
                    default:
                        break;
                }
            }
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get orchestrator counts: {}", e.what());
    }
    
    return counts;
}

std::map<std::string, double> MultiLLMOrchestratorManager::getRequestMetrics() {
    std::map<std::string, double> metrics;
    
    try {
        // Calculate request metrics
        metrics["total_requests"] = static_cast<double>(requestToOrchestrator_.size());
        metrics["active_requests"] = static_cast<double>(requestToOrchestrator_.size());
        
        // Calculate average request time
        double totalRequestTime = 0.0;
        int requestCount = 0;
        for (const auto& request : requestToOrchestrator_) {
            auto it = requestStartTime_.find(request.first);
            if (it != requestStartTime_.end()) {
                auto duration = std::chrono::system_clock::now() - it->second;
                totalRequestTime += std::chrono::duration_cast<std::chrono::milliseconds>(duration).count();
                requestCount++;
            }
        }
        if (requestCount > 0) {
            metrics["average_request_time_ms"] = totalRequestTime / requestCount;
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get request metrics: {}", e.what());
    }
    
    return metrics;
}

bool MultiLLMOrchestratorManager::enableSystemProfiling() {
    systemProfilingEnabled_ = true;
    spdlog::info("System profiling enabled");
    return true;
}

bool MultiLLMOrchestratorManager::disableSystemProfiling() {
    systemProfilingEnabled_ = false;
    spdlog::info("System profiling disabled");
    return true;
}

std::map<std::string, double> MultiLLMOrchestratorManager::getSystemProfilingData() {
    std::map<std::string, double> profilingData;
    
    if (!systemProfilingEnabled_) {
        return profilingData;
    }
    
    try {
        auto metrics = getSystemMetrics();
        auto requestMetrics = getRequestMetrics();
        
        profilingData.insert(metrics.begin(), metrics.end());
        profilingData.insert(requestMetrics.begin(), requestMetrics.end());
        
        profilingData["profiling_enabled"] = systemProfilingEnabled_ ? 1.0 : 0.0;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get system profiling data: {}", e.what());
    }
    
    return profilingData;
}

void MultiLLMOrchestratorManager::setMaxOrchestrators(int maxOrchestrators) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    maxOrchestrators_ = maxOrchestrators;
    spdlog::info("Set maximum orchestrators to: {}", maxOrchestrators);
}

int MultiLLMOrchestratorManager::getMaxOrchestrators() const {
    return maxOrchestrators_;
}

void MultiLLMOrchestratorManager::setOrchestrationStrategy(const std::string& strategy) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    orchestrationStrategy_ = strategy;
    spdlog::info("Set orchestration strategy to: {}", strategy);
}

std::string MultiLLMOrchestratorManager::getOrchestrationStrategy() const {
    return orchestrationStrategy_;
}

void MultiLLMOrchestratorManager::setLoadBalancingStrategy(const std::string& strategy) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    loadBalancingStrategy_ = strategy;
    spdlog::info("Set load balancing strategy to: {}", strategy);
}

std::string MultiLLMOrchestratorManager::getLoadBalancingStrategy() const {
    return loadBalancingStrategy_;
}

bool MultiLLMOrchestratorManager::validateOrchestratorCreation(const OrchestrationConfig& config) {
    try {
        if (config.orchestratorId.empty()) {
            spdlog::error("Orchestrator ID cannot be empty");
            return false;
        }
        
        if (config.maxConcurrentLLMs <= 0) {
            spdlog::error("Max concurrent LLMs must be greater than 0");
            return false;
        }
        
        if (config.maxQueueSize <= 0) {
            spdlog::error("Max queue size must be greater than 0");
            return false;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to validate orchestrator creation: {}", e.what());
        return false;
    }
}

bool MultiLLMOrchestratorManager::validateRequestParameters(const std::map<std::string, std::string>& parameters) {
    try {
        // Validate request parameters
        // This is a simplified implementation
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to validate request parameters: {}", e.what());
        return false;
    }
}

std::string MultiLLMOrchestratorManager::generateOrchestratorId() {
    try {
        std::stringstream ss;
        ss << "orchestrator_" << std::chrono::system_clock::now().time_since_epoch().count();
        return ss.str();
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to generate orchestrator ID: {}", e.what());
        return "orchestrator_" + std::to_string(std::chrono::system_clock::now().time_since_epoch().count());
    }
}

bool MultiLLMOrchestratorManager::cleanupOrchestrator(const std::string& orchestratorId) {
    try {
        auto orchestrator = getOrchestrator(orchestratorId);
        if (!orchestrator) {
            spdlog::error("Orchestrator {} not found for cleanup", orchestratorId);
            return false;
        }
        
        orchestrator->shutdown();
        orchestrators_.erase(orchestratorId);
        
        spdlog::info("Cleaned up orchestrator: {}", orchestratorId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cleanup orchestrator {}: {}", orchestratorId, e.what());
        return false;
    }
}

void MultiLLMOrchestratorManager::updateSystemMetrics() {
    try {
        // Update system metrics
        // Implementation depends on specific metrics to track
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to update system metrics: {}", e.what());
    }
}

bool MultiLLMOrchestratorManager::findBestOrchestrator(const std::string& prompt, const std::map<std::string, std::string>& parameters, std::string& bestOrchestratorId) {
    try {
        // Find best orchestrator based on prompt and parameters
        auto orchestratorsByType = getOrchestratorsByType(OrchestrationType::PARALLEL);
        if (orchestratorsByType.empty()) {
            spdlog::error("No orchestrators found for type {}", static_cast<int>(OrchestrationType::PARALLEL));
            return false;
        }
        
        // Select first available orchestrator
        bestOrchestratorId = orchestratorsByType[0]->getOrchestratorId();
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to find best orchestrator: {}", e.what());
        return false;
    }
}

bool MultiLLMOrchestratorManager::executeOnOrchestrator(const std::string& orchestratorId, const std::string& requestId, const std::string& prompt, const std::map<std::string, std::string>& parameters) {
    try {
        auto orchestrator = getOrchestrator(orchestratorId);
        if (!orchestrator) {
            spdlog::error("Orchestrator {} not found", orchestratorId);
            return false;
        }
        
        // Execute request on orchestrator
        // This is a simplified implementation
        spdlog::debug("Executing request {} on orchestrator {}", requestId, orchestratorId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to execute request {} on orchestrator {}: {}", requestId, orchestratorId, e.what());
        return false;
    }
}

std::vector<std::string> MultiLLMOrchestratorManager::selectOrchestratorsForRequest(const std::string& prompt, const std::map<std::string, std::string>& parameters) {
    std::vector<std::string> selectedOrchestrators;
    
    try {
        auto orchestratorsByType = getOrchestratorsByType(OrchestrationType::PARALLEL);
        if (orchestratorsByType.empty()) {
            return selectedOrchestrators;
        }
        
        // Select orchestrators based on type
        for (const auto& orchestrator : orchestratorsByType) {
            if (orchestrator) {
                selectedOrchestrators.push_back(orchestrator->getOrchestratorId());
            }
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to select orchestrators for request: {}", e.what());
    }
    
    return selectedOrchestrators;
}

bool MultiLLMOrchestratorManager::validateSystemConfiguration() {
    try {
        // Validate system configuration
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to validate system configuration: {}", e.what());
        return false;
    }
}

bool MultiLLMOrchestratorManager::optimizeSystemConfiguration() {
    try {
        // Optimize system configuration
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to optimize system configuration: {}", e.what());
        return false;
    }
}

bool MultiLLMOrchestratorManager::balanceSystemLoad() {
    try {
        // Balance system load
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to balance system load: {}", e.what());
        return false;
    }
}

} // namespace orchestration
} // namespace cogniware
