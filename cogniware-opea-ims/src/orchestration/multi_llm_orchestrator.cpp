#include "orchestration/multi_llm_orchestrator.h"
#include <spdlog/spdlog.h>
#include <algorithm>
#include <random>
#include <sstream>

namespace cogniware {
namespace orchestration {

AdvancedMultiLLMOrchestrator::AdvancedMultiLLMOrchestrator(const OrchestrationConfig& config)
    : config_(config)
    , initialized_(false)
    , orchestrationType_(config.type)
    , profilingEnabled_(false)
    , stopOrchestrator_(false)
    , loadBalancingStrategy_("round_robin")
    , resultAggregationStrategy_("weighted_average") {
    
    spdlog::info("Creating multi-LLM orchestrator: {}", config_.orchestratorId);
}

AdvancedMultiLLMOrchestrator::~AdvancedMultiLLMOrchestrator() {
    shutdown();
}

bool AdvancedMultiLLMOrchestrator::initialize() {
    std::lock_guard<std::mutex> lock(orchestratorMutex_);
    
    if (initialized_) {
        spdlog::warn("Multi-LLM orchestrator {} already initialized", config_.orchestratorId);
        return true;
    }
    
    try {
        // Initialize performance metrics
        performanceMetrics_["utilization"] = 0.0;
        performanceMetrics_["active_requests"] = 0.0;
        performanceMetrics_["registered_llms"] = 0.0;
        performanceMetrics_["completed_requests"] = 0.0;
        performanceMetrics_["failed_requests"] = 0.0;
        performanceMetrics_["average_response_time"] = 0.0;
        lastUpdateTime_ = std::chrono::system_clock::now();
        
        // Start orchestrator thread
        stopOrchestrator_ = false;
        orchestratorThread_ = std::thread(&AdvancedMultiLLMOrchestrator::orchestratorLoop, this);
        
        initialized_ = true;
        spdlog::info("Multi-LLM orchestrator {} initialized successfully", config_.orchestratorId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize multi-LLM orchestrator {}: {}", config_.orchestratorId, e.what());
        return false;
    }
}

void AdvancedMultiLLMOrchestrator::shutdown() {
    std::lock_guard<std::mutex> lock(orchestratorMutex_);
    
    if (!initialized_) {
        return;
    }
    
    try {
        // Stop orchestrator thread
        stopOrchestrator_ = true;
        if (orchestratorThread_.joinable()) {
            orchestratorThread_.join();
        }
        
        // Cancel all active requests
        for (const auto& request : activeRequests_) {
            cancelRequest(request.first);
        }
        activeRequests_.clear();
        requestTasks_.clear();
        
        initialized_ = false;
        spdlog::info("Multi-LLM orchestrator {} shutdown completed", config_.orchestratorId);
        
    } catch (const std::exception& e) {
        spdlog::error("Error during multi-LLM orchestrator {} shutdown: {}", config_.orchestratorId, e.what());
    }
}

bool AdvancedMultiLLMOrchestrator::isInitialized() const {
    return initialized_;
}

std::string AdvancedMultiLLMOrchestrator::getOrchestratorId() const {
    return config_.orchestratorId;
}

OrchestrationConfig AdvancedMultiLLMOrchestrator::getConfig() const {
    return config_;
}

bool AdvancedMultiLLMOrchestrator::updateConfig(const OrchestrationConfig& config) {
    std::lock_guard<std::mutex> lock(orchestratorMutex_);
    
    if (!initialized_) {
        spdlog::error("Multi-LLM orchestrator {} not initialized", config_.orchestratorId);
        return false;
    }
    
    try {
        // Update configuration
        config_ = config;
        orchestrationType_ = config.type;
        
        spdlog::info("Configuration updated for multi-LLM orchestrator {}", config_.orchestratorId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to update configuration for multi-LLM orchestrator {}: {}", config_.orchestratorId, e.what());
        return false;
    }
}

bool AdvancedMultiLLMOrchestrator::registerLLM(const LLMInstance& llmInstance) {
    std::lock_guard<std::mutex> lock(llmMutex_);
    
    if (!initialized_) {
        spdlog::error("Multi-LLM orchestrator {} not initialized", config_.orchestratorId);
        return false;
    }
    
    try {
        // Validate LLM instance
        if (!validateLLMInstance(llmInstance)) {
            spdlog::error("Invalid LLM instance for orchestrator {}", config_.orchestratorId);
            return false;
        }
        
        // Register LLM
        registeredLLMs_[llmInstance.llmId] = llmInstance;
        
        spdlog::info("LLM {} registered with orchestrator {}", llmInstance.llmId, config_.orchestratorId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to register LLM {} with orchestrator {}: {}", llmInstance.llmId, config_.orchestratorId, e.what());
        return false;
    }
}

bool AdvancedMultiLLMOrchestrator::unregisterLLM(const std::string& llmId) {
    std::lock_guard<std::mutex> lock(llmMutex_);
    
    if (!initialized_) {
        spdlog::error("Multi-LLM orchestrator {} not initialized", config_.orchestratorId);
        return false;
    }
    
    try {
        // Check if LLM exists
        if (registeredLLMs_.find(llmId) == registeredLLMs_.end()) {
            spdlog::error("LLM {} not found in orchestrator {}", llmId, config_.orchestratorId);
            return false;
        }
        
        // Unregister LLM
        registeredLLMs_.erase(llmId);
        
        spdlog::info("LLM {} unregistered from orchestrator {}", llmId, config_.orchestratorId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to unregister LLM {} from orchestrator {}: {}", llmId, config_.orchestratorId, e.what());
        return false;
    }
}

std::vector<LLMInstance> AdvancedMultiLLMOrchestrator::getRegisteredLLMs() const {
    std::lock_guard<std::mutex> lock(llmMutex_);
    
    std::vector<LLMInstance> llms;
    for (const auto& llm : registeredLLMs_) {
        llms.push_back(llm.second);
    }
    return llms;
}

LLMInstance AdvancedMultiLLMOrchestrator::getLLMInstance(const std::string& llmId) const {
    std::lock_guard<std::mutex> lock(llmMutex_);
    
    auto it = registeredLLMs_.find(llmId);
    if (it != registeredLLMs_.end()) {
        return it->second;
    }
    
    // Return empty instance if not found
    LLMInstance emptyInstance;
    emptyInstance.llmId = llmId;
    return emptyInstance;
}

std::future<AggregatedResult> AdvancedMultiLLMOrchestrator::processRequestAsync(const std::string& requestId, const std::string& prompt, const std::map<std::string, std::string>& parameters) {
    std::lock_guard<std::mutex> lock(orchestratorMutex_);
    
    if (!initialized_) {
        spdlog::error("Multi-LLM orchestrator {} not initialized", config_.orchestratorId);
        return std::async(std::launch::deferred, []() {
            AggregatedResult result;
            result.requestId = "";
            result.confidence = 0.0f;
            return result;
        });
    }
    
    try {
        // Validate request parameters
        if (!validateRequestParameters(parameters)) {
            spdlog::error("Invalid request parameters for orchestrator {}", config_.orchestratorId);
            return std::async(std::launch::deferred, []() {
                AggregatedResult result;
                result.requestId = "";
                result.confidence = 0.0f;
                return result;
            });
        }
        
        // Check if request is already active
        if (activeRequests_.find(requestId) != activeRequests_.end()) {
            spdlog::error("Request {} is already active in orchestrator {}", requestId, config_.orchestratorId);
            return std::async(std::launch::deferred, []() {
                AggregatedResult result;
                result.requestId = "";
                result.confidence = 0.0f;
                return result;
            });
        }
        
        // Create async request processing
        auto future = std::async(std::launch::async, [this, requestId, prompt, parameters]() {
            return processRequestInternal(requestId, prompt, parameters);
        });
        
        // Store request
        activeRequests_[requestId] = std::move(future);
        
        spdlog::info("Async request processing started for request {} on orchestrator {}", requestId, config_.orchestratorId);
        return activeRequests_[requestId];
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to process async request {} on orchestrator {}: {}", requestId, config_.orchestratorId, e.what());
        return std::async(std::launch::deferred, []() {
            AggregatedResult result;
            result.requestId = "";
            result.confidence = 0.0f;
            return result;
        });
    }
}

AggregatedResult AdvancedMultiLLMOrchestrator::processRequest(const std::string& requestId, const std::string& prompt, const std::map<std::string, std::string>& parameters) {
    std::lock_guard<std::mutex> lock(orchestratorMutex_);
    
    if (!initialized_) {
        spdlog::error("Multi-LLM orchestrator {} not initialized", config_.orchestratorId);
        AggregatedResult result;
        result.requestId = requestId;
        result.confidence = 0.0f;
        return result;
    }
    
    try {
        // Validate request parameters
        if (!validateRequestParameters(parameters)) {
            spdlog::error("Invalid request parameters for orchestrator {}", config_.orchestratorId);
            AggregatedResult result;
            result.requestId = requestId;
            result.confidence = 0.0f;
            return result;
        }
        
        // Check if request is already active
        if (activeRequests_.find(requestId) != activeRequests_.end()) {
            spdlog::error("Request {} is already active in orchestrator {}", requestId, config_.orchestratorId);
            AggregatedResult result;
            result.requestId = requestId;
            result.confidence = 0.0f;
            return result;
        }
        
        // Process request
        auto result = processRequestInternal(requestId, prompt, parameters);
        
        spdlog::info("Request processing completed for request {} on orchestrator {}", requestId, config_.orchestratorId);
        return result;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to process request {} on orchestrator {}: {}", requestId, config_.orchestratorId, e.what());
        AggregatedResult result;
        result.requestId = requestId;
        result.confidence = 0.0f;
        return result;
    }
}

bool AdvancedMultiLLMOrchestrator::cancelRequest(const std::string& requestId) {
    std::lock_guard<std::mutex> lock(orchestratorMutex_);
    
    if (!initialized_) {
        spdlog::error("Multi-LLM orchestrator {} not initialized", config_.orchestratorId);
        return false;
    }
    
    try {
        // Check if request is active
        if (activeRequests_.find(requestId) == activeRequests_.end()) {
            spdlog::error("Request {} not found in orchestrator {}", requestId, config_.orchestratorId);
            return false;
        }
        
        // Cancel request
        cleanupRequest(requestId);
        
        spdlog::info("Request {} cancelled on orchestrator {}", requestId, config_.orchestratorId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cancel request {} on orchestrator {}: {}", requestId, config_.orchestratorId, e.what());
        return false;
    }
}

std::vector<std::string> AdvancedMultiLLMOrchestrator::getActiveRequests() const {
    std::lock_guard<std::mutex> lock(orchestratorMutex_);
    
    std::vector<std::string> activeRequestIds;
    for (const auto& request : activeRequests_) {
        activeRequestIds.push_back(request.first);
    }
    return activeRequestIds;
}

bool AdvancedMultiLLMOrchestrator::isRequestActive(const std::string& requestId) const {
    std::lock_guard<std::mutex> lock(orchestratorMutex_);
    return activeRequests_.find(requestId) != activeRequests_.end();
}

std::map<std::string, double> AdvancedMultiLLMOrchestrator::getPerformanceMetrics() const {
    std::lock_guard<std::mutex> lock(orchestratorMutex_);
    return performanceMetrics_;
}

float AdvancedMultiLLMOrchestrator::getUtilization() const {
    std::lock_guard<std::mutex> lock(orchestratorMutex_);
    
    if (config_.maxConcurrentLLMs == 0) {
        return 0.0f;
    }
    
    return static_cast<float>(activeRequests_.size()) / config_.maxConcurrentLLMs;
}

bool AdvancedMultiLLMOrchestrator::enableProfiling() {
    profilingEnabled_ = true;
    spdlog::info("Profiling enabled for multi-LLM orchestrator {}", config_.orchestratorId);
    return true;
}

bool AdvancedMultiLLMOrchestrator::disableProfiling() {
    profilingEnabled_ = false;
    spdlog::info("Profiling disabled for multi-LLM orchestrator {}", config_.orchestratorId);
    return true;
}

std::map<std::string, double> AdvancedMultiLLMOrchestrator::getProfilingData() const {
    std::map<std::string, double> profilingData;
    
    if (!profilingEnabled_) {
        return profilingData;
    }
    
    try {
        // Collect profiling data
        auto metrics = getPerformanceMetrics();
        profilingData["utilization"] = metrics.at("utilization");
        profilingData["active_requests"] = metrics.at("active_requests");
        profilingData["registered_llms"] = metrics.at("registered_llms");
        profilingData["completed_requests"] = metrics.at("completed_requests");
        profilingData["failed_requests"] = metrics.at("failed_requests");
        profilingData["average_response_time"] = metrics.at("average_response_time");
        profilingData["orchestration_type"] = static_cast<double>(static_cast<int>(orchestrationType_));
        profilingData["max_concurrent_llms"] = static_cast<double>(config_.maxConcurrentLLMs);
        profilingData["max_queue_size"] = static_cast<double>(config_.maxQueueSize);
        profilingData["enable_load_balancing"] = config_.enableLoadBalancing ? 1.0 : 0.0;
        profilingData["enable_result_aggregation"] = config_.enableResultAggregation ? 1.0 : 0.0;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get profiling data for multi-LLM orchestrator {}: {}", config_.orchestratorId, e.what());
    }
    
    return profilingData;
}

bool AdvancedMultiLLMOrchestrator::setOrchestrationType(OrchestrationType type) {
    std::lock_guard<std::mutex> lock(orchestratorMutex_);
    
    orchestrationType_ = type;
    config_.type = type;
    
    spdlog::info("Orchestration type set to {} for orchestrator {}", static_cast<int>(type), config_.orchestratorId);
    return true;
}

OrchestrationType AdvancedMultiLLMOrchestrator::getOrchestrationType() const {
    return orchestrationType_;
}

bool AdvancedMultiLLMOrchestrator::setMaxConcurrentLLMs(int maxLLMs) {
    std::lock_guard<std::mutex> lock(orchestratorMutex_);
    
    config_.maxConcurrentLLMs = maxLLMs;
    
    spdlog::info("Max concurrent LLMs set to {} for orchestrator {}", maxLLMs, config_.orchestratorId);
    return true;
}

int AdvancedMultiLLMOrchestrator::getMaxConcurrentLLMs() const {
    return config_.maxConcurrentLLMs;
}

bool AdvancedMultiLLMOrchestrator::optimizeOrchestration() {
    std::lock_guard<std::mutex> lock(orchestratorMutex_);
    
    if (!initialized_) {
        spdlog::error("Multi-LLM orchestrator {} not initialized", config_.orchestratorId);
        return false;
    }
    
    try {
        // Optimize request queue
        optimizeRequestQueue();
        
        // Rebalance LLMs
        rebalanceLLMs();
        
        spdlog::info("Orchestration optimization completed for orchestrator {}", config_.orchestratorId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to optimize orchestration for orchestrator {}: {}", config_.orchestratorId, e.what());
        return false;
    }
}

bool AdvancedMultiLLMOrchestrator::balanceLoad() {
    std::lock_guard<std::mutex> lock(orchestratorMutex_);
    
    if (!initialized_) {
        spdlog::error("Multi-LLM orchestrator {} not initialized", config_.orchestratorId);
        return false;
    }
    
    try {
        // Balance load across LLMs
        rebalanceLLMs();
        
        spdlog::info("Load balancing completed for orchestrator {}", config_.orchestratorId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to balance load for orchestrator {}: {}", config_.orchestratorId, e.what());
        return false;
    }
}

bool AdvancedMultiLLMOrchestrator::aggregateResults() {
    std::lock_guard<std::mutex> lock(orchestratorMutex_);
    
    if (!initialized_) {
        spdlog::error("Multi-LLM orchestrator {} not initialized", config_.orchestratorId);
        return false;
    }
    
    try {
        // Aggregate results from completed requests
        // This is a simplified implementation
        spdlog::info("Result aggregation completed for orchestrator {}", config_.orchestratorId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to aggregate results for orchestrator {}: {}", config_.orchestratorId, e.what());
        return false;
    }
}

std::map<std::string, std::string> AdvancedMultiLLMOrchestrator::getOrchestratorInfo() const {
    std::map<std::string, std::string> info;
    
    info["orchestrator_id"] = config_.orchestratorId;
    info["orchestration_type"] = std::to_string(static_cast<int>(orchestrationType_));
    info["max_concurrent_llms"] = std::to_string(config_.maxConcurrentLLMs);
    info["max_queue_size"] = std::to_string(config_.maxQueueSize);
    info["enable_load_balancing"] = config_.enableLoadBalancing ? "true" : "false";
    info["enable_result_aggregation"] = config_.enableResultAggregation ? "true" : "false";
    info["utilization"] = std::to_string(getUtilization());
    info["active_requests"] = std::to_string(activeRequests_.size());
    info["registered_llms"] = std::to_string(registeredLLMs_.size());
    info["load_balancing_strategy"] = loadBalancingStrategy_;
    info["result_aggregation_strategy"] = resultAggregationStrategy_;
    
    return info;
}

bool AdvancedMultiLLMOrchestrator::validateConfiguration() const {
    try {
        // Validate configuration
        if (config_.orchestratorId.empty()) {
            spdlog::error("Orchestrator ID cannot be empty");
            return false;
        }
        
        if (config_.maxConcurrentLLMs <= 0) {
            spdlog::error("Max concurrent LLMs must be greater than 0");
            return false;
        }
        
        if (config_.maxQueueSize <= 0) {
            spdlog::error("Max queue size must be greater than 0");
            return false;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to validate configuration: {}", e.what());
        return false;
    }
}

bool AdvancedMultiLLMOrchestrator::setLoadBalancingStrategy(const std::string& strategy) {
    std::lock_guard<std::mutex> lock(orchestratorMutex_);
    
    loadBalancingStrategy_ = strategy;
    
    spdlog::info("Load balancing strategy set to {} for orchestrator {}", strategy, config_.orchestratorId);
    return true;
}

std::string AdvancedMultiLLMOrchestrator::getLoadBalancingStrategy() const {
    return loadBalancingStrategy_;
}

bool AdvancedMultiLLMOrchestrator::setResultAggregationStrategy(const std::string& strategy) {
    std::lock_guard<std::mutex> lock(orchestratorMutex_);
    
    resultAggregationStrategy_ = strategy;
    
    spdlog::info("Result aggregation strategy set to {} for orchestrator {}", strategy, config_.orchestratorId);
    return true;
}

std::string AdvancedMultiLLMOrchestrator::getResultAggregationStrategy() const {
    return resultAggregationStrategy_;
}

void AdvancedMultiLLMOrchestrator::orchestratorLoop() {
    while (!stopOrchestrator_) {
        try {
            // Process request queue
            processRequestQueue();
            
            // Update performance metrics
            updatePerformanceMetrics();
            
            // Cleanup completed requests
            cleanupCompletedRequests();
            
            // Sleep for a short time
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            
        } catch (const std::exception& e) {
            spdlog::error("Error in orchestrator loop for orchestrator {}: {}", config_.orchestratorId, e.what());
        }
    }
}

bool AdvancedMultiLLMOrchestrator::validateLLMInstance(const LLMInstance& llmInstance) {
    try {
        // Validate LLM instance
        if (llmInstance.llmId.empty()) {
            spdlog::error("LLM ID cannot be empty");
            return false;
        }
        
        if (llmInstance.modelName.empty()) {
            spdlog::error("Model name cannot be empty");
            return false;
        }
        
        if (llmInstance.modelPath.empty()) {
            spdlog::error("Model path cannot be empty");
            return false;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to validate LLM instance: {}", e.what());
        return false;
    }
}

void AdvancedMultiLLMOrchestrator::updatePerformanceMetrics() {
    try {
        auto now = std::chrono::system_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(now - lastUpdateTime_);
        
        // Update metrics
        performanceMetrics_["utilization"] = getUtilization();
        performanceMetrics_["active_requests"] = static_cast<double>(activeRequests_.size());
        performanceMetrics_["registered_llms"] = static_cast<double>(registeredLLMs_.size());
        performanceMetrics_["completed_requests"] = 0.0; // Will be updated on completion
        performanceMetrics_["failed_requests"] = 0.0; // Will be updated on failure
        performanceMetrics_["average_response_time"] = 0.0; // Will be updated during processing
        performanceMetrics_["update_duration_ms"] = static_cast<double>(duration.count());
        
        lastUpdateTime_ = now;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to update performance metrics for orchestrator {}: {}", config_.orchestratorId, e.what());
    }
}

AggregatedResult AdvancedMultiLLMOrchestrator::processRequestInternal(const std::string& requestId, const std::string& prompt, const std::map<std::string, std::string>& parameters) {
    AggregatedResult result;
    result.requestId = requestId;
    result.confidence = 0.0f;
    
    try {
        // Record start time
        auto startTime = std::chrono::high_resolution_clock::now();
        
        // Select best LLM
        std::string bestLLMId = selectBestLLM(prompt, parameters);
        if (bestLLMId.empty()) {
            spdlog::error("No suitable LLM found for request {}", requestId);
            return result;
        }
        
        // Create task
        LLMTask task;
        task.taskId = generateTaskId();
        task.llmId = bestLLMId;
        task.prompt = prompt;
        task.priority = TaskPriority::NORMAL;
        task.timeout = config_.timeout;
        task.createdAt = std::chrono::system_clock::now();
        
        // Assign task to LLM
        if (!assignTaskToLLM(task.taskId, bestLLMId)) {
            spdlog::error("Failed to assign task to LLM {} for request {}", bestLLMId, requestId);
            return result;
        }
        
        // Simulate LLM processing
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        
        // Generate response
        std::string response = "Generated response for: " + prompt;
        result.responses.push_back(response);
        result.aggregatedResponse = response;
        result.confidence = 0.8f;
        result.aggregatedAt = std::chrono::system_clock::now();
        
        // Calculate processing time
        auto endTime = std::chrono::high_resolution_clock::now();
        auto processingTime = std::chrono::duration_cast<std::chrono::milliseconds>(endTime - startTime);
        
        // Update LLM utilization
        updateLLMUtilization(bestLLMId);
        
        spdlog::debug("Request processing completed for request {} on orchestrator {}", requestId, config_.orchestratorId);
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to process request {} on orchestrator {}: {}", requestId, config_.orchestratorId, e.what());
    }
    
    return result;
}

void AdvancedMultiLLMOrchestrator::cleanupRequest(const std::string& requestId) {
    try {
        // Remove request from active requests
        if (activeRequests_.find(requestId) != activeRequests_.end()) {
            activeRequests_.erase(requestId);
        }
        
        // Remove request tasks
        requestTasks_.erase(requestId);
        
        spdlog::debug("Request {} cleaned up for orchestrator {}", requestId, config_.orchestratorId);
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cleanup request {} for orchestrator {}: {}", requestId, config_.orchestratorId, e.what());
    }
}

std::string AdvancedMultiLLMOrchestrator::generateRequestId() {
    try {
        // Generate unique request ID
        std::stringstream ss;
        ss << "request_" << std::chrono::system_clock::now().time_since_epoch().count();
        return ss.str();
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to generate request ID: {}", e.what());
        return "request_" + std::to_string(std::chrono::system_clock::now().time_since_epoch().count());
    }
}

std::string AdvancedMultiLLMOrchestrator::selectBestLLM(const std::string& prompt, const std::map<std::string, std::string>& parameters) {
    try {
        // Get registered LLMs
        auto llms = getRegisteredLLMs();
        if (llms.empty()) {
            spdlog::error("No registered LLMs for orchestrator {}", config_.orchestratorId);
            return "";
        }
        
        // Select best LLM based on load balancing strategy
        std::string bestLLMId;
        float bestScore = -1.0f;
        
        for (const auto& llm : llms) {
            if (canLLMHandleTask(llm)) {
                float score = calculateLLMScore(llm, prompt);
                if (score > bestScore) {
                    bestScore = score;
                    bestLLMId = llm.llmId;
                }
            }
        }
        
        return bestLLMId;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to select best LLM: {}", e.what());
        return "";
    }
}

bool AdvancedMultiLLMOrchestrator::assignTaskToLLM(const std::string& taskId, const std::string& llmId) {
    try {
        // Check if LLM exists
        if (registeredLLMs_.find(llmId) == registeredLLMs_.end()) {
            spdlog::error("LLM {} not found for task {}", llmId, taskId);
            return false;
        }
        
        // Check if LLM can handle task
        if (registeredLLMs_[llmId].activeTasks >= registeredLLMs_[llmId].maxTasks) {
            spdlog::error("LLM {} is at capacity for task {}", llmId, taskId);
            return false;
        }
        
        // Assign task to LLM
        registeredLLMs_[llmId].activeTasks++;
        updateLLMUtilization(llmId);
        
        spdlog::info("Task {} assigned to LLM {}", taskId, llmId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to assign task {} to LLM {}: {}", taskId, llmId, e.what());
        return false;
    }
}

void AdvancedMultiLLMOrchestrator::updateLLMUtilization(const std::string& llmId) {
    try {
        // Update LLM utilization
        auto& llm = registeredLLMs_[llmId];
        llm.utilization = static_cast<float>(llm.activeTasks) / llm.maxTasks;
        llm.lastUpdated = std::chrono::system_clock::now();
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to update LLM utilization for LLM {}: {}", llmId, e.what());
    }
}

float AdvancedMultiLLMOrchestrator::calculateLLMScore(const LLMInstance& llm, const std::string& prompt) {
    try {
        // Calculate LLM score based on load balancing strategy
        float score = 0.0f;
        
        if (loadBalancingStrategy_ == "round_robin") {
            score = 1.0f; // All LLMs have equal score
        } else if (loadBalancingStrategy_ == "least_loaded") {
            score = 1.0f - llm.utilization;
        } else if (loadBalancingStrategy_ == "weighted") {
            score = llm.utilization;
        } else {
            score = 1.0f; // Default to equal score
        }
        
        return score;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to calculate LLM score: {}", e.what());
        return 0.0f;
    }
}

bool AdvancedMultiLLMOrchestrator::canLLMHandleTask(const LLMInstance& llm) {
    try {
        // Check if LLM is available
        if (llm.status != LLMStatus::READY) {
            return false;
        }
        
        // Check if LLM has capacity
        if (llm.activeTasks >= llm.maxTasks) {
            return false;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to check if LLM can handle task: {}", e.what());
        return false;
    }
}

void AdvancedMultiLLMOrchestrator::processRequestQueue() {
    try {
        // Process requests from queue
        // This is a simplified implementation
        spdlog::debug("Request queue processed for orchestrator {}", config_.orchestratorId);
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to process request queue: {}", e.what());
    }
}

void AdvancedMultiLLMOrchestrator::handleRequestCompletion(const std::string& requestId, const AggregatedResult& result) {
    try {
        // Handle request completion
        spdlog::info("Request {} completed on orchestrator {}", requestId, config_.orchestratorId);
        
        // Update performance metrics
        performanceMetrics_["completed_requests"]++;
        
        // Cleanup request
        cleanupRequest(requestId);
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to handle request completion for request {}: {}", requestId, e.what());
    }
}

void AdvancedMultiLLMOrchestrator::handleRequestFailure(const std::string& requestId, const std::string& error) {
    try {
        // Handle request failure
        spdlog::error("Request {} failed on orchestrator {}: {}", requestId, config_.orchestratorId, error);
        
        // Update performance metrics
        performanceMetrics_["failed_requests"]++;
        
        // Cleanup request
        cleanupRequest(requestId);
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to handle request failure for request {}: {}", requestId, e.what());
    }
}

void AdvancedMultiLLMOrchestrator::rebalanceLLMs() {
    try {
        // Rebalance LLMs
        // This is a simplified implementation
        spdlog::debug("LLM rebalancing completed for orchestrator {}", config_.orchestratorId);
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to rebalance LLMs for orchestrator {}: {}", config_.orchestratorId, e.what());
    }
}

void AdvancedMultiLLMOrchestrator::cleanupCompletedRequests() {
    try {
        // Cleanup completed requests
        // This is a simplified implementation
        spdlog::debug("Completed request cleanup finished for orchestrator {}", config_.orchestratorId);
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cleanup completed requests for orchestrator {}: {}", config_.orchestratorId, e.what());
    }
}

std::string AdvancedMultiLLMOrchestrator::generateTaskId() {
    try {
        // Generate unique task ID
        std::stringstream ss;
        ss << "task_" << std::chrono::system_clock::now().time_since_epoch().count();
        return ss.str();
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to generate task ID: {}", e.what());
        return "task_" + std::to_string(std::chrono::system_clock::now().time_since_epoch().count());
    }
}

bool AdvancedMultiLLMOrchestrator::validateRequestParameters(const std::map<std::string, std::string>& parameters) {
    try {
        // Validate request parameters
        // This is a simplified implementation
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to validate request parameters: {}", e.what());
        return false;
    }
}

void AdvancedMultiLLMOrchestrator::updateRequestStatus(const std::string& requestId, const std::string& status) {
    try {
        // Update request status
        spdlog::debug("Request {} status updated to {} for orchestrator {}", requestId, status, config_.orchestratorId);
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to update request status: {}", e.what());
    }
}

float AdvancedMultiLLMOrchestrator::calculateRequestPriority(const std::string& prompt, const std::map<std::string, std::string>& parameters) {
    try {
        // Calculate request priority
        // This is a simplified implementation
        return 0.5f;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to calculate request priority: {}", e.what());
        return 0.5f;
    }
}

void AdvancedMultiLLMOrchestrator::optimizeRequestQueue() {
    try {
        // Optimize request queue
        // This is a simplified implementation
        spdlog::debug("Request queue optimization completed for orchestrator {}", config_.orchestratorId);
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to optimize request queue for orchestrator {}: {}", config_.orchestratorId, e.what());
    }
}

void AdvancedMultiLLMOrchestrator::scaleUpLLMs() {
    try {
        // Scale up LLMs
        // This is a simplified implementation
        spdlog::debug("LLM scale up completed for orchestrator {}", config_.orchestratorId);
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to scale up LLMs for orchestrator {}: {}", config_.orchestratorId, e.what());
    }
}

void AdvancedMultiLLMOrchestrator::scaleDownLLMs() {
    try {
        // Scale down LLMs
        // This is a simplified implementation
        spdlog::debug("LLM scale down completed for orchestrator {}", config_.orchestratorId);
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to scale down LLMs for orchestrator {}: {}", config_.orchestratorId, e.what());
    }
}

bool AdvancedMultiLLMOrchestrator::isLLMOverloaded(const LLMInstance& llm) {
    try {
        // Check if LLM is overloaded
        return llm.utilization > 0.9f;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to check if LLM is overloaded: {}", e.what());
        return false;
    }
}

bool AdvancedMultiLLMOrchestrator::isLLMUnderloaded(const LLMInstance& llm) {
    try {
        // Check if LLM is underloaded
        return llm.utilization < 0.1f;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to check if LLM is underloaded: {}", e.what());
        return false;
    }
}

AggregatedResult AdvancedMultiLLMOrchestrator::aggregateResults(const std::vector<std::string>& responses) {
    AggregatedResult result;
    
    try {
        // Aggregate results based on strategy
        if (resultAggregationStrategy_ == "weighted_average") {
            result.aggregatedResponse = generateAggregatedResponse(responses);
        } else if (resultAggregationStrategy_ == "majority_vote") {
            result.aggregatedResponse = generateAggregatedResponse(responses);
        } else {
            result.aggregatedResponse = generateAggregatedResponse(responses);
        }
        
        result.responses = responses;
        result.confidence = calculateConfidence(responses);
        result.aggregatedAt = std::chrono::system_clock::now();
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to aggregate results: {}", e.what());
    }
    
    return result;
}

float AdvancedMultiLLMOrchestrator::calculateConfidence(const std::vector<std::string>& responses) {
    try {
        // Calculate confidence based on response similarity
        // This is a simplified implementation
        return 0.8f;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to calculate confidence: {}", e.what());
        return 0.0f;
    }
}

std::string AdvancedMultiLLMOrchestrator::generateAggregatedResponse(const std::vector<std::string>& responses) {
    try {
        // Generate aggregated response
        // This is a simplified implementation
        if (responses.empty()) {
            return "";
        }
        
        return responses[0]; // Return first response for now
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to generate aggregated response: {}", e.what());
        return "";
    }
}

} // namespace orchestration
} // namespace cogniware
