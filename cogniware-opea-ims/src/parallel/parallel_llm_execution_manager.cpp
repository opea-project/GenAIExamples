#include "parallel/parallel_llm_execution.h"
#include <spdlog/spdlog.h>
#include <algorithm>

namespace cogniware {
namespace parallel {

ParallelLLMExecutionManager::ParallelLLMExecutionManager()
    : initialized_(false)
    , maxLLMs_(10)
    , executionPolicy_("balanced")
    , loadBalancingStrategy_("round_robin")
    , systemProfilingEnabled_(false) {
    
    spdlog::info("ParallelLLMExecutionManager initialized");
}

ParallelLLMExecutionManager::~ParallelLLMExecutionManager() {
    shutdown();
}

bool ParallelLLMExecutionManager::initialize() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (initialized_) {
        spdlog::warn("Parallel LLM execution manager already initialized");
        return true;
    }
    
    try {
        llms_.clear();
        requestToLLM_.clear();
        requestStartTime_.clear();
        
        initialized_ = true;
        spdlog::info("ParallelLLMExecutionManager initialized successfully");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize parallel LLM execution manager: {}", e.what());
        return false;
    }
}

void ParallelLLMExecutionManager::shutdown() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        return;
    }
    
    try {
        for (auto& llm : llms_) {
            if (llm.second) {
                llm.second->shutdown();
            }
        }
        llms_.clear();
        
        initialized_ = false;
        spdlog::info("ParallelLLMExecutionManager shutdown completed");
        
    } catch (const std::exception& e) {
        spdlog::error("Error during parallel LLM execution manager shutdown: {}", e.what());
    }
}

bool ParallelLLMExecutionManager::isInitialized() const {
    return initialized_;
}

std::shared_ptr<LLMExecutor> ParallelLLMExecutionManager::createLLM(const LLMExecutionConfig& config) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return nullptr;
    }
    
    try {
        if (!validateLLMCreation(config)) {
            spdlog::error("Invalid LLM configuration");
            return nullptr;
        }
        
        if (llms_.find(config.llmId) != llms_.end()) {
            spdlog::error("LLM {} already exists", config.llmId);
            return nullptr;
        }
        
        if (static_cast<int>(llms_.size()) >= maxLLMs_) {
            spdlog::error("Maximum number of LLMs ({}) reached", maxLLMs_);
            return nullptr;
        }
        
        auto llm = std::make_shared<AdvancedLLMExecutor>(config);
        if (!llm->initialize()) {
            spdlog::error("Failed to initialize LLM {}", config.llmId);
            return nullptr;
        }
        
        llms_[config.llmId] = llm;
        
        spdlog::info("Created LLM executor: {}", config.llmId);
        return llm;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to create LLM {}: {}", config.llmId, e.what());
        return nullptr;
    }
}

bool ParallelLLMExecutionManager::destroyLLM(const std::string& llmId) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        auto it = llms_.find(llmId);
        if (it == llms_.end()) {
            spdlog::error("LLM {} not found", llmId);
            return false;
        }
        
        if (it->second) {
            it->second->shutdown();
        }
        
        llms_.erase(it);
        
        spdlog::info("Destroyed LLM executor: {}", llmId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to destroy LLM {}: {}", llmId, e.what());
        return false;
    }
}

std::shared_ptr<LLMExecutor> ParallelLLMExecutionManager::getLLM(const std::string& llmId) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    auto it = llms_.find(llmId);
    if (it != llms_.end()) {
        return it->second;
    }
    
    return nullptr;
}

std::vector<std::shared_ptr<LLMExecutor>> ParallelLLMExecutionManager::getAllLLMs() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    std::vector<std::shared_ptr<LLMExecutor>> allLLMs;
    for (const auto& llm : llms_) {
        allLLMs.push_back(llm.second);
    }
    return allLLMs;
}

std::vector<std::shared_ptr<LLMExecutor>> ParallelLLMExecutionManager::getLLMsByPriority(LLMPriority priority) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    std::vector<std::shared_ptr<LLMExecutor>> llmsByPriority;
    for (const auto& llm : llms_) {
        if (llm.second && llm.second->getPriority() == priority) {
            llmsByPriority.push_back(llm.second);
        }
    }
    return llmsByPriority;
}

std::vector<std::shared_ptr<LLMExecutor>> ParallelLLMExecutionManager::getLLMsByMode(LLMExecutionMode mode) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    std::vector<std::shared_ptr<LLMExecutor>> llmsByMode;
    for (const auto& llm : llms_) {
        if (llm.second && llm.second->getExecutionMode() == mode) {
            llmsByMode.push_back(llm.second);
        }
    }
    return llmsByMode;
}

std::future<LLMExecutionResponse> ParallelLLMExecutionManager::executeAsync(const LLMExecutionRequest& request) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return std::async(std::launch::deferred, []() {
            LLMExecutionResponse response;
            response.success = false;
            response.error = "Manager not initialized";
            return response;
        });
    }
    
    try {
        if (!validateExecutionRequest(request)) {
            spdlog::error("Invalid execution request");
            return std::async(std::launch::deferred, []() {
                LLMExecutionResponse response;
                response.success = false;
                response.error = "Invalid execution request";
                return response;
            });
        }
        
        std::string bestLLMId;
        if (!findBestLLM(request, bestLLMId)) {
            spdlog::error("No suitable LLM found for request {}", request.requestId);
            return std::async(std::launch::deferred, []() {
                LLMExecutionResponse response;
                response.success = false;
                response.error = "No suitable LLM found";
                return response;
            });
        }
        
        auto llm = getLLM(bestLLMId);
        if (!llm) {
            spdlog::error("LLM {} not found", bestLLMId);
            return std::async(std::launch::deferred, []() {
                LLMExecutionResponse response;
                response.success = false;
                response.error = "LLM not found";
                return response;
            });
        }
        
        requestToLLM_[request.requestId] = bestLLMId;
        requestStartTime_[request.requestId] = std::chrono::system_clock::now();
        
        auto future = llm->executeAsync(request);
        
        spdlog::info("Async execution started for request {} on LLM {}", request.requestId, bestLLMId);
        return future;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to start async execution for request {}: {}", request.requestId, e.what());
        return std::async(std::launch::deferred, []() {
            LLMExecutionResponse response;
            response.success = false;
            response.error = "Failed to start async execution";
            return response;
        });
    }
}

LLMExecutionResponse ParallelLLMExecutionManager::execute(const LLMExecutionRequest& request) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        LLMExecutionResponse response;
        response.success = false;
        response.error = "Manager not initialized";
        return response;
    }
    
    try {
        if (!validateExecutionRequest(request)) {
            spdlog::error("Invalid execution request");
            LLMExecutionResponse response;
            response.success = false;
            response.error = "Invalid execution request";
            return response;
        }
        
        std::string bestLLMId;
        if (!findBestLLM(request, bestLLMId)) {
            spdlog::error("No suitable LLM found for request {}", request.requestId);
            LLMExecutionResponse response;
            response.success = false;
            response.error = "No suitable LLM found";
            return response;
        }
        
        auto llm = getLLM(bestLLMId);
        if (!llm) {
            spdlog::error("LLM {} not found", bestLLMId);
            LLMExecutionResponse response;
            response.success = false;
            response.error = "LLM not found";
            return response;
        }
        
        requestToLLM_[request.requestId] = bestLLMId;
        requestStartTime_[request.requestId] = std::chrono::system_clock::now();
        
        auto response = llm->execute(request);
        
        spdlog::info("Execution completed for request {} on LLM {}", request.requestId, bestLLMId);
        return response;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to execute request {}: {}", request.requestId, e.what());
        LLMExecutionResponse response;
        response.success = false;
        response.error = "Execution failed: " + std::string(e.what());
        return response;
    }
}

bool ParallelLLMExecutionManager::cancelExecution(const std::string& requestId) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        auto it = requestToLLM_.find(requestId);
        if (it == requestToLLM_.end()) {
            spdlog::error("Request {} not found", requestId);
            return false;
        }
        
        auto llm = getLLM(it->second);
        if (!llm) {
            spdlog::error("LLM {} not found for request {}", it->second, requestId);
            return false;
        }
        
        bool cancelled = llm->cancelExecution(requestId);
        
        if (cancelled) {
            requestToLLM_.erase(it);
            requestStartTime_.erase(requestId);
            spdlog::info("Request {} cancelled", requestId);
        }
        
        return cancelled;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cancel request {}: {}", requestId, e.what());
        return false;
    }
}

bool ParallelLLMExecutionManager::cancelAllExecutions() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        for (const auto& llm : llms_) {
            if (llm.second) {
                auto activeRequests = llm.second->getActiveRequests();
                for (const auto& requestId : activeRequests) {
                    llm.second->cancelExecution(requestId);
                }
            }
        }
        
        requestToLLM_.clear();
        requestStartTime_.clear();
        
        spdlog::info("All executions cancelled");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cancel all executions: {}", e.what());
        return false;
    }
}

std::vector<std::string> ParallelLLMExecutionManager::getActiveRequests() {
    std::vector<std::string> activeRequests;
    
    try {
        for (const auto& llm : llms_) {
            if (llm.second) {
                auto llmRequests = llm.second->getActiveRequests();
                activeRequests.insert(activeRequests.end(), llmRequests.begin(), llmRequests.end());
            }
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get active requests: {}", e.what());
    }
    
    return activeRequests;
}

std::vector<std::string> ParallelLLMExecutionManager::getActiveRequestsByLLM(const std::string& llmId) {
    std::vector<std::string> activeRequests;
    
    try {
        auto llm = getLLM(llmId);
        if (llm) {
            activeRequests = llm->getActiveRequests();
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get active requests for LLM {}: {}", llmId, e.what());
    }
    
    return activeRequests;
}

std::vector<LLMExecutionResponse> ParallelLLMExecutionManager::executeParallel(const std::vector<LLMExecutionRequest>& requests) {
    std::vector<LLMExecutionResponse> responses;
    
    try {
        spdlog::info("Executing {} requests in parallel", requests.size());
        
        // Select LLMs for parallel execution
        auto selectedLLMs = selectLLMsForParallelExecution(requests);
        
        if (selectedLLMs.size() != requests.size()) {
            spdlog::error("Could not select enough LLMs for parallel execution");
            return responses;
        }
        
        // Execute requests in parallel
        std::vector<std::future<LLMExecutionResponse>> futures;
        for (size_t i = 0; i < requests.size(); ++i) {
            auto llm = getLLM(selectedLLMs[i]);
            if (llm) {
                futures.push_back(llm->executeAsync(requests[i]));
            }
        }
        
        // Collect results
        for (auto& future : futures) {
            responses.push_back(future.get());
        }
        
        spdlog::info("Parallel execution completed with {} responses", responses.size());
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to execute parallel requests: {}", e.what());
    }
    
    return responses;
}

std::vector<LLMExecutionResponse> ParallelLLMExecutionManager::executePipelined(const std::vector<LLMExecutionRequest>& requests) {
    std::vector<LLMExecutionResponse> responses;
    
    try {
        spdlog::info("Executing {} requests in pipelined mode", requests.size());
        
        // Select LLMs for pipelined execution
        auto selectedLLMs = selectLLMsForPipelinedExecution(requests);
        
        if (selectedLLMs.empty()) {
            spdlog::error("Could not select LLMs for pipelined execution");
            return responses;
        }
        
        // Execute requests in pipeline
        for (size_t i = 0; i < requests.size(); ++i) {
            auto llm = getLLM(selectedLLMs[i % selectedLLMs.size()]);
            if (llm) {
                responses.push_back(llm->execute(requests[i]));
            }
        }
        
        spdlog::info("Pipelined execution completed with {} responses", responses.size());
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to execute pipelined requests: {}", e.what());
    }
    
    return responses;
}

std::vector<LLMExecutionResponse> ParallelLLMExecutionManager::executeBatch(const std::vector<LLMExecutionRequest>& requests) {
    std::vector<LLMExecutionResponse> responses;
    
    try {
        spdlog::info("Executing {} requests in batch mode", requests.size());
        
        // Select LLMs for batch execution
        auto selectedLLMs = selectLLMsForBatchExecution(requests);
        
        if (selectedLLMs.empty()) {
            spdlog::error("Could not select LLMs for batch execution");
            return responses;
        }
        
        // Execute requests in batches
        size_t batchSize = requests.size() / selectedLLMs.size();
        for (size_t i = 0; i < selectedLLMs.size(); ++i) {
            auto llm = getLLM(selectedLLMs[i]);
            if (llm) {
                size_t startIdx = i * batchSize;
                size_t endIdx = (i + 1) * batchSize;
                if (i == selectedLLMs.size() - 1) {
                    endIdx = requests.size();
                }
                
                for (size_t j = startIdx; j < endIdx; ++j) {
                    responses.push_back(llm->execute(requests[j]));
                }
            }
        }
        
        spdlog::info("Batch execution completed with {} responses", responses.size());
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to execute batch requests: {}", e.what());
    }
    
    return responses;
}

std::vector<LLMExecutionResponse> ParallelLLMExecutionManager::executeHybrid(const std::vector<LLMExecutionRequest>& requests) {
    std::vector<LLMExecutionResponse> responses;
    
    try {
        spdlog::info("Executing {} requests in hybrid mode", requests.size());
        
        // Select LLMs for hybrid execution
        auto selectedLLMs = selectLLMsForHybridExecution(requests);
        
        if (selectedLLMs.empty()) {
            spdlog::error("Could not select LLMs for hybrid execution");
            return responses;
        }
        
        // Execute requests using hybrid strategy
        for (size_t i = 0; i < requests.size(); ++i) {
            auto llm = getLLM(selectedLLMs[i % selectedLLMs.size()]);
            if (llm) {
                responses.push_back(llm->execute(requests[i]));
            }
        }
        
        spdlog::info("Hybrid execution completed with {} responses", responses.size());
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to execute hybrid requests: {}", e.what());
    }
    
    return responses;
}

bool ParallelLLMExecutionManager::optimizeSystem() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Optimizing parallel LLM execution system");
        
        for (const auto& llm : llms_) {
            if (llm.second) {
                auto advancedLLM = std::dynamic_pointer_cast<AdvancedLLMExecutor>(llm.second);
                if (advancedLLM) {
                    advancedLLM->optimize();
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

bool ParallelLLMExecutionManager::balanceLoad() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Balancing load across LLM executors");
        
        std::vector<std::shared_ptr<LLMExecutor>> activeLLMs;
        for (const auto& llm : llms_) {
            if (llm.second && llm.second->getStatus() == LLMExecutionStatus::READY) {
                activeLLMs.push_back(llm.second);
            }
        }
        
        if (activeLLMs.empty()) {
            spdlog::warn("No active LLMs found for load balancing");
            return true;
        }
        
        // Calculate average utilization
        float totalUtilization = 0.0f;
        for (const auto& llm : activeLLMs) {
            totalUtilization += llm->getUtilization();
        }
        float averageUtilization = totalUtilization / activeLLMs.size();
        
        // Balance load (simplified implementation)
        for (const auto& llm : activeLLMs) {
            float utilization = llm->getUtilization();
            if (utilization > averageUtilization * 1.2f) {
                spdlog::debug("LLM {} is overloaded (utilization: {:.2f})", 
                            llm->getLLMId(), utilization);
            } else if (utilization < averageUtilization * 0.8f) {
                spdlog::debug("LLM {} is underloaded (utilization: {:.2f})", 
                            llm->getLLMId(), utilization);
            }
        }
        
        spdlog::info("Load balancing completed");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to balance load: {}", e.what());
        return false;
    }
}

bool ParallelLLMExecutionManager::cleanupIdleLLMs() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Cleaning up idle LLM executors");
        
        std::vector<std::string> idleLLMs;
        for (const auto& llm : llms_) {
            if (llm.second && llm.second->getStatus() == LLMExecutionStatus::IDLE) {
                idleLLMs.push_back(llm.first);
            }
        }
        
        for (const auto& llmId : idleLLMs) {
            spdlog::info("Cleaning up idle LLM: {}", llmId);
            cleanupLLM(llmId);
        }
        
        spdlog::info("Cleaned up {} idle LLMs", idleLLMs.size());
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cleanup idle LLMs: {}", e.what());
        return false;
    }
}

bool ParallelLLMExecutionManager::validateSystem() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Validating parallel LLM execution system");
        
        bool isValid = true;
        
        for (const auto& llm : llms_) {
            if (llm.second) {
                auto advancedLLM = std::dynamic_pointer_cast<AdvancedLLMExecutor>(llm.second);
                if (advancedLLM && !advancedLLM->validateResources()) {
                    spdlog::error("LLM {} failed validation", llm.first);
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

std::map<std::string, double> ParallelLLMExecutionManager::getSystemMetrics() {
    std::map<std::string, double> metrics;
    
    try {
        updateSystemMetrics();
        
        metrics["total_llms"] = static_cast<double>(llms_.size());
        metrics["active_requests"] = static_cast<double>(requestToLLM_.size());
        metrics["execution_policy"] = static_cast<double>(executionPolicy_.length());
        metrics["load_balancing_strategy"] = static_cast<double>(loadBalancingStrategy_.length());
        
        // Calculate average utilization
        double totalUtilization = 0.0;
        int llmCount = 0;
        for (const auto& llm : llms_) {
            if (llm.second) {
                totalUtilization += llm.second->getUtilization();
                llmCount++;
            }
        }
        if (llmCount > 0) {
            metrics["average_utilization"] = totalUtilization / llmCount;
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get system metrics: {}", e.what());
    }
    
    return metrics;
}

std::map<std::string, int> ParallelLLMExecutionManager::getLLMCounts() {
    std::map<std::string, int> counts;
    
    try {
        counts["total"] = static_cast<int>(llms_.size());
        counts["idle"] = 0;
        counts["ready"] = 0;
        counts["executing"] = 0;
        counts["error"] = 0;
        counts["suspended"] = 0;
        
        for (const auto& llm : llms_) {
            if (llm.second) {
                switch (llm.second->getStatus()) {
                    case LLMExecutionStatus::IDLE:
                        counts["idle"]++;
                        break;
                    case LLMExecutionStatus::READY:
                        counts["ready"]++;
                        break;
                    case LLMExecutionStatus::EXECUTING:
                        counts["executing"]++;
                        break;
                    case LLMExecutionStatus::ERROR:
                        counts["error"]++;
                        break;
                    case LLMExecutionStatus::SUSPENDED:
                        counts["suspended"]++;
                        break;
                    default:
                        break;
                }
            }
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get LLM counts: {}", e.what());
    }
    
    return counts;
}

std::map<std::string, double> ParallelLLMExecutionManager::getExecutionMetrics() {
    std::map<std::string, double> metrics;
    
    try {
        // Calculate execution metrics
        metrics["total_requests"] = static_cast<double>(requestToLLM_.size());
        metrics["active_requests"] = static_cast<double>(requestToLLM_.size());
        
        // Calculate average latency and throughput
        double totalLatency = 0.0;
        double totalThroughput = 0.0;
        int llmCount = 0;
        for (const auto& llm : llms_) {
            if (llm.second) {
                auto llmMetrics = llm.second->getPerformanceMetrics();
                totalLatency += llmMetrics.at("latency");
                totalThroughput += llmMetrics.at("throughput");
                llmCount++;
            }
        }
        if (llmCount > 0) {
            metrics["average_latency"] = totalLatency / llmCount;
            metrics["average_throughput"] = totalThroughput / llmCount;
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get execution metrics: {}", e.what());
    }
    
    return metrics;
}

bool ParallelLLMExecutionManager::enableSystemProfiling() {
    systemProfilingEnabled_ = true;
    spdlog::info("System profiling enabled");
    return true;
}

bool ParallelLLMExecutionManager::disableSystemProfiling() {
    systemProfilingEnabled_ = false;
    spdlog::info("System profiling disabled");
    return true;
}

std::map<std::string, double> ParallelLLMExecutionManager::getSystemProfilingData() {
    std::map<std::string, double> profilingData;
    
    if (!systemProfilingEnabled_) {
        return profilingData;
    }
    
    try {
        auto metrics = getSystemMetrics();
        auto executionMetrics = getExecutionMetrics();
        
        profilingData.insert(metrics.begin(), metrics.end());
        profilingData.insert(executionMetrics.begin(), executionMetrics.end());
        
        profilingData["profiling_enabled"] = systemProfilingEnabled_ ? 1.0 : 0.0;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get system profiling data: {}", e.what());
    }
    
    return profilingData;
}

void ParallelLLMExecutionManager::setMaxLLMs(int maxLLMs) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    maxLLMs_ = maxLLMs;
    spdlog::info("Set maximum LLMs to: {}", maxLLMs);
}

int ParallelLLMExecutionManager::getMaxLLMs() const {
    return maxLLMs_;
}

void ParallelLLMExecutionManager::setExecutionPolicy(const std::string& policy) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    executionPolicy_ = policy;
    spdlog::info("Set execution policy to: {}", policy);
}

std::string ParallelLLMExecutionManager::getExecutionPolicy() const {
    return executionPolicy_;
}

void ParallelLLMExecutionManager::setLoadBalancingStrategy(const std::string& strategy) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    loadBalancingStrategy_ = strategy;
    spdlog::info("Set load balancing strategy to: {}", strategy);
}

std::string ParallelLLMExecutionManager::getLoadBalancingStrategy() const {
    return loadBalancingStrategy_;
}

bool ParallelLLMExecutionManager::validateLLMCreation(const LLMExecutionConfig& config) {
    try {
        if (config.llmId.empty()) {
            spdlog::error("LLM ID cannot be empty");
            return false;
        }
        
        if (config.modelPath.empty()) {
            spdlog::error("Model path cannot be empty");
            return false;
        }
        
        if (config.batchSize == 0) {
            spdlog::error("Batch size must be greater than 0");
            return false;
        }
        
        if (config.maxSequenceLength == 0) {
            spdlog::error("Maximum sequence length must be greater than 0");
            return false;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to validate LLM creation: {}", e.what());
        return false;
    }
}

bool ParallelLLMExecutionManager::validateExecutionRequest(const LLMExecutionRequest& request) {
    try {
        if (request.requestId.empty()) {
            spdlog::error("Request ID cannot be empty");
            return false;
        }
        
        if (request.llmId.empty()) {
            spdlog::error("LLM ID cannot be empty");
            return false;
        }
        
        if (request.inputText.empty() && request.inputTokens.empty()) {
            spdlog::error("Request must have either input text or input tokens");
            return false;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to validate execution request: {}", e.what());
        return false;
    }
}

std::string ParallelLLMExecutionManager::generateLLMId() {
    try {
        std::stringstream ss;
        ss << "llm_" << std::chrono::system_clock::now().time_since_epoch().count();
        return ss.str();
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to generate LLM ID: {}", e.what());
        return "llm_" + std::to_string(std::chrono::system_clock::now().time_since_epoch().count());
    }
}

bool ParallelLLMExecutionManager::cleanupLLM(const std::string& llmId) {
    try {
        auto llm = getLLM(llmId);
        if (!llm) {
            spdlog::error("LLM {} not found for cleanup", llmId);
            return false;
        }
        
        llm->shutdown();
        llms_.erase(llmId);
        
        spdlog::info("Cleaned up LLM: {}", llmId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cleanup LLM {}: {}", llmId, e.what());
        return false;
    }
}

void ParallelLLMExecutionManager::updateSystemMetrics() {
    try {
        // Update system metrics
        // Implementation depends on specific metrics to track
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to update system metrics: {}", e.what());
    }
}

bool ParallelLLMExecutionManager::findBestLLM(const LLMExecutionRequest& request, std::string& bestLLMId) {
    try {
        // Find best LLM based on load balancing strategy
        if (loadBalancingStrategy_ == "round_robin") {
            // Round-robin selection
            static size_t currentIndex = 0;
            auto llmList = getAllLLMs();
            if (!llmList.empty()) {
                bestLLMId = llmList[currentIndex % llmList.size()]->getLLMId();
                currentIndex++;
                return true;
            }
        } else if (loadBalancingStrategy_ == "least_loaded") {
            // Least loaded selection
            auto llmList = getAllLLMs();
            if (!llmList.empty()) {
                float minUtilization = 1.0f;
                for (const auto& llm : llmList) {
                    if (llm->getUtilization() < minUtilization) {
                        minUtilization = llm->getUtilization();
                        bestLLMId = llm->getLLMId();
                    }
                }
                return true;
            }
        }
        
        return false;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to find best LLM: {}", e.what());
        return false;
    }
}

bool ParallelLLMExecutionManager::executeOnLLM(const std::string& llmId, const LLMExecutionRequest& request) {
    try {
        auto llm = getLLM(llmId);
        if (!llm) {
            spdlog::error("LLM {} not found", llmId);
            return false;
        }
        
        auto response = llm->execute(request);
        return response.success;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to execute on LLM {}: {}", llmId, e.what());
        return false;
    }
}

std::vector<std::string> ParallelLLMExecutionManager::selectLLMsForParallelExecution(const std::vector<LLMExecutionRequest>& requests) {
    std::vector<std::string> selectedLLMs;
    
    try {
        auto allLLMs = getAllLLMs();
        if (allLLMs.empty()) {
            return selectedLLMs;
        }
        
        // Select one LLM per request
        for (size_t i = 0; i < requests.size(); ++i) {
            selectedLLMs.push_back(allLLMs[i % allLLMs.size()]->getLLMId());
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to select LLMs for parallel execution: {}", e.what());
    }
    
    return selectedLLMs;
}

std::vector<std::string> ParallelLLMExecutionManager::selectLLMsForPipelinedExecution(const std::vector<LLMExecutionRequest>& requests) {
    std::vector<std::string> selectedLLMs;
    
    try {
        auto allLLMs = getAllLLMs();
        if (allLLMs.empty()) {
            return selectedLLMs;
        }
        
        // Select LLMs for pipelined execution
        size_t numLLMs = std::min(allLLMs.size(), requests.size());
        for (size_t i = 0; i < numLLMs; ++i) {
            selectedLLMs.push_back(allLLMs[i]->getLLMId());
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to select LLMs for pipelined execution: {}", e.what());
    }
    
    return selectedLLMs;
}

std::vector<std::string> ParallelLLMExecutionManager::selectLLMsForBatchExecution(const std::vector<LLMExecutionRequest>& requests) {
    std::vector<std::string> selectedLLMs;
    
    try {
        auto allLLMs = getAllLLMs();
        if (allLLMs.empty()) {
            return selectedLLMs;
        }
        
        // Select LLMs for batch execution
        size_t numLLMs = std::min(allLLMs.size(), requests.size());
        for (size_t i = 0; i < numLLMs; ++i) {
            selectedLLMs.push_back(allLLMs[i]->getLLMId());
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to select LLMs for batch execution: {}", e.what());
    }
    
    return selectedLLMs;
}

std::vector<std::string> ParallelLLMExecutionManager::selectLLMsForHybridExecution(const std::vector<LLMExecutionRequest>& requests) {
    std::vector<std::string> selectedLLMs;
    
    try {
        auto allLLMs = getAllLLMs();
        if (allLLMs.empty()) {
            return selectedLLMs;
        }
        
        // Select LLMs for hybrid execution
        size_t numLLMs = std::min(allLLMs.size(), requests.size());
        for (size_t i = 0; i < numLLMs; ++i) {
            selectedLLMs.push_back(allLLMs[i]->getLLMId());
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to select LLMs for hybrid execution: {}", e.what());
    }
    
    return selectedLLMs;
}

} // namespace parallel
} // namespace cogniware
