#include "parallel/parallel_llm_execution.h"
#include <spdlog/spdlog.h>

namespace cogniware {
namespace parallel {

GlobalParallelLLMExecutionSystem& GlobalParallelLLMExecutionSystem::getInstance() {
    static GlobalParallelLLMExecutionSystem instance;
    return instance;
}

GlobalParallelLLMExecutionSystem::GlobalParallelLLMExecutionSystem()
    : initialized_(false) {
    
    spdlog::info("GlobalParallelLLMExecutionSystem singleton created");
}

GlobalParallelLLMExecutionSystem::~GlobalParallelLLMExecutionSystem() {
    shutdown();
}

bool GlobalParallelLLMExecutionSystem::initialize() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (initialized_) {
        spdlog::warn("Global parallel LLM execution system already initialized");
        return true;
    }
    
    try {
        // Initialize execution manager
        executionManager_ = std::make_shared<ParallelLLMExecutionManager>();
        if (!executionManager_->initialize()) {
            spdlog::error("Failed to initialize parallel LLM execution manager");
            return false;
        }
        
        // Set default configuration
        configuration_["max_llms"] = "10";
        configuration_["execution_policy"] = "balanced";
        configuration_["load_balancing_strategy"] = "round_robin";
        configuration_["auto_cleanup"] = "enabled";
        configuration_["system_optimization"] = "enabled";
        configuration_["profiling"] = "disabled";
        
        initialized_ = true;
        spdlog::info("GlobalParallelLLMExecutionSystem initialized successfully");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize global parallel LLM execution system: {}", e.what());
        return false;
    }
}

void GlobalParallelLLMExecutionSystem::shutdown() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_) {
        return;
    }
    
    try {
        // Shutdown execution manager
        if (executionManager_) {
            executionManager_->shutdown();
            executionManager_.reset();
        }
        
        initialized_ = false;
        spdlog::info("GlobalParallelLLMExecutionSystem shutdown completed");
        
    } catch (const std::exception& e) {
        spdlog::error("Error during global parallel LLM execution system shutdown: {}", e.what());
    }
}

bool GlobalParallelLLMExecutionSystem::isInitialized() const {
    return initialized_;
}

std::shared_ptr<ParallelLLMExecutionManager> GlobalParallelLLMExecutionSystem::getExecutionManager() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    return executionManager_;
}

std::shared_ptr<LLMExecutor> GlobalParallelLLMExecutionSystem::createLLM(const LLMExecutionConfig& config) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !executionManager_) {
        spdlog::error("System not initialized");
        return nullptr;
    }
    
    try {
        // Create LLM
        auto llm = executionManager_->createLLM(config);
        
        if (llm) {
            spdlog::info("Created LLM executor: {}", config.llmId);
        } else {
            spdlog::error("Failed to create LLM executor: {}", config.llmId);
        }
        
        return llm;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to create LLM {}: {}", config.llmId, e.what());
        return nullptr;
    }
}

bool GlobalParallelLLMExecutionSystem::destroyLLM(const std::string& llmId) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !executionManager_) {
        spdlog::error("System not initialized");
        return false;
    }
    
    try {
        // Destroy LLM
        bool destroyed = executionManager_->destroyLLM(llmId);
        
        if (destroyed) {
            spdlog::info("Destroyed LLM executor: {}", llmId);
        } else {
            spdlog::error("Failed to destroy LLM executor: {}", llmId);
        }
        
        return destroyed;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to destroy LLM {}: {}", llmId, e.what());
        return false;
    }
}

std::shared_ptr<LLMExecutor> GlobalParallelLLMExecutionSystem::getLLM(const std::string& llmId) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !executionManager_) {
        spdlog::error("System not initialized");
        return nullptr;
    }
    
    return executionManager_->getLLM(llmId);
}

std::future<LLMExecutionResponse> GlobalParallelLLMExecutionSystem::executeAsync(const LLMExecutionRequest& request) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !executionManager_) {
        spdlog::error("System not initialized");
        return std::async(std::launch::deferred, []() {
            LLMExecutionResponse response;
            response.success = false;
            response.error = "System not initialized";
            return response;
        });
    }
    
    try {
        // Execute async request
        auto future = executionManager_->executeAsync(request);
        
        spdlog::info("Async execution started for request {}", request.requestId);
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

LLMExecutionResponse GlobalParallelLLMExecutionSystem::execute(const LLMExecutionRequest& request) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !executionManager_) {
        spdlog::error("System not initialized");
        LLMExecutionResponse response;
        response.success = false;
        response.error = "System not initialized";
        return response;
    }
    
    try {
        // Execute request
        auto response = executionManager_->execute(request);
        
        if (response.success) {
            spdlog::info("Execution completed for request {}", request.requestId);
        } else {
            spdlog::error("Execution failed for request {}: {}", request.requestId, response.error);
        }
        
        return response;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to execute request {}: {}", request.requestId, e.what());
        LLMExecutionResponse response;
        response.success = false;
        response.error = "Execution failed: " + std::string(e.what());
        return response;
    }
}

std::vector<LLMExecutionResponse> GlobalParallelLLMExecutionSystem::executeParallel(const std::vector<LLMExecutionRequest>& requests) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !executionManager_) {
        spdlog::error("System not initialized");
        return std::vector<LLMExecutionResponse>();
    }
    
    try {
        // Execute parallel requests
        auto responses = executionManager_->executeParallel(requests);
        
        spdlog::info("Parallel execution completed with {} responses", responses.size());
        return responses;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to execute parallel requests: {}", e.what());
        return std::vector<LLMExecutionResponse>();
    }
}

std::vector<std::shared_ptr<LLMExecutor>> GlobalParallelLLMExecutionSystem::getAllLLMs() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !executionManager_) {
        spdlog::error("System not initialized");
        return std::vector<std::shared_ptr<LLMExecutor>>();
    }
    
    return executionManager_->getAllLLMs();
}

std::map<std::string, double> GlobalParallelLLMExecutionSystem::getSystemMetrics() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !executionManager_) {
        spdlog::error("System not initialized");
        return std::map<std::string, double>();
    }
    
    try {
        // Get system metrics
        auto metrics = executionManager_->getSystemMetrics();
        
        // Add system-specific metrics
        metrics["system_initialized"] = initialized_ ? 1.0 : 0.0;
        metrics["configuration_items"] = static_cast<double>(configuration_.size());
        
        return metrics;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get system metrics: {}", e.what());
        return std::map<std::string, double>();
    }
}

void GlobalParallelLLMExecutionSystem::setSystemConfiguration(const std::map<std::string, std::string>& config) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    configuration_ = config;
    spdlog::info("System configuration updated with {} items", config.size());
    
    // Apply configuration to execution manager
    if (executionManager_) {
        try {
            // Parse and apply configuration
            if (config.find("max_llms") != config.end()) {
                int maxLLMs = std::stoi(config.at("max_llms"));
                executionManager_->setMaxLLMs(maxLLMs);
            }
            
            if (config.find("execution_policy") != config.end()) {
                std::string policy = config.at("execution_policy");
                executionManager_->setExecutionPolicy(policy);
            }
            
            if (config.find("load_balancing_strategy") != config.end()) {
                std::string strategy = config.at("load_balancing_strategy");
                executionManager_->setLoadBalancingStrategy(strategy);
            }
            
        } catch (const std::exception& e) {
            spdlog::error("Failed to apply configuration: {}", e.what());
        }
    }
}

std::map<std::string, std::string> GlobalParallelLLMExecutionSystem::getSystemConfiguration() const {
    std::lock_guard<std::mutex> lock(systemMutex_);
    return configuration_;
}

} // namespace parallel
} // namespace cogniware
