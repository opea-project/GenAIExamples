#include "orchestration/multi_llm_orchestrator.h"
#include <spdlog/spdlog.h>

namespace cogniware {
namespace orchestration {

GlobalMultiLLMOrchestrationSystem& GlobalMultiLLMOrchestrationSystem::getInstance() {
    static GlobalMultiLLMOrchestrationSystem instance;
    return instance;
}

GlobalMultiLLMOrchestrationSystem::GlobalMultiLLMOrchestrationSystem()
    : initialized_(false) {
    
    spdlog::info("GlobalMultiLLMOrchestrationSystem singleton created");
}

GlobalMultiLLMOrchestrationSystem::~GlobalMultiLLMOrchestrationSystem() {
    shutdown();
}

bool GlobalMultiLLMOrchestrationSystem::initialize() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (initialized_) {
        spdlog::warn("Global multi-LLM orchestration system already initialized");
        return true;
    }
    
    try {
        // Initialize orchestrator manager
        orchestratorManager_ = std::make_shared<MultiLLMOrchestratorManager>();
        if (!orchestratorManager_->initialize()) {
            spdlog::error("Failed to initialize multi-LLM orchestrator manager");
            return false;
        }
        
        // Set default configuration
        configuration_["max_orchestrators"] = "10";
        configuration_["orchestration_strategy"] = "parallel";
        configuration_["load_balancing_strategy"] = "round_robin";
        configuration_["auto_cleanup"] = "enabled";
        configuration_["system_optimization"] = "enabled";
        configuration_["profiling"] = "disabled";
        
        initialized_ = true;
        spdlog::info("GlobalMultiLLMOrchestrationSystem initialized successfully");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize global multi-LLM orchestration system: {}", e.what());
        return false;
    }
}

void GlobalMultiLLMOrchestrationSystem::shutdown() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_) {
        return;
    }
    
    try {
        // Shutdown orchestrator manager
        if (orchestratorManager_) {
            orchestratorManager_->shutdown();
            orchestratorManager_.reset();
        }
        
        initialized_ = false;
        spdlog::info("GlobalMultiLLMOrchestrationSystem shutdown completed");
        
    } catch (const std::exception& e) {
        spdlog::error("Error during global multi-LLM orchestration system shutdown: {}", e.what());
    }
}

bool GlobalMultiLLMOrchestrationSystem::isInitialized() const {
    return initialized_;
}

std::shared_ptr<MultiLLMOrchestratorManager> GlobalMultiLLMOrchestrationSystem::getOrchestratorManager() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    return orchestratorManager_;
}

std::shared_ptr<MultiLLMOrchestrator> GlobalMultiLLMOrchestrationSystem::createOrchestrator(const OrchestrationConfig& config) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !orchestratorManager_) {
        spdlog::error("System not initialized");
        return nullptr;
    }
    
    try {
        // Create orchestrator
        auto orchestrator = orchestratorManager_->createOrchestrator(config);
        
        if (orchestrator) {
            spdlog::info("Created multi-LLM orchestrator: {}", config.orchestratorId);
        } else {
            spdlog::error("Failed to create multi-LLM orchestrator: {}", config.orchestratorId);
        }
        
        return orchestrator;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to create multi-LLM orchestrator {}: {}", config.orchestratorId, e.what());
        return nullptr;
    }
}

bool GlobalMultiLLMOrchestrationSystem::destroyOrchestrator(const std::string& orchestratorId) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !orchestratorManager_) {
        spdlog::error("System not initialized");
        return false;
    }
    
    try {
        // Destroy orchestrator
        bool destroyed = orchestratorManager_->destroyOrchestrator(orchestratorId);
        
        if (destroyed) {
            spdlog::info("Destroyed multi-LLM orchestrator: {}", orchestratorId);
        } else {
            spdlog::error("Failed to destroy multi-LLM orchestrator: {}", orchestratorId);
        }
        
        return destroyed;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to destroy multi-LLM orchestrator {}: {}", orchestratorId, e.what());
        return false;
    }
}

std::shared_ptr<MultiLLMOrchestrator> GlobalMultiLLMOrchestrationSystem::getOrchestrator(const std::string& orchestratorId) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !orchestratorManager_) {
        spdlog::error("System not initialized");
        return nullptr;
    }
    
    return orchestratorManager_->getOrchestrator(orchestratorId);
}

std::future<AggregatedResult> GlobalMultiLLMOrchestrationSystem::processRequestAsync(const std::string& requestId, const std::string& prompt, const std::map<std::string, std::string>& parameters) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !orchestratorManager_) {
        spdlog::error("System not initialized");
        return std::async(std::launch::deferred, []() {
            AggregatedResult result;
            result.requestId = "";
            result.confidence = 0.0f;
            return result;
        });
    }
    
    try {
        // Process request
        auto future = orchestratorManager_->processRequestAsync(requestId, prompt, parameters);
        
        spdlog::info("Async request processing started for request {}", requestId);
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

AggregatedResult GlobalMultiLLMOrchestrationSystem::processRequest(const std::string& requestId, const std::string& prompt, const std::map<std::string, std::string>& parameters) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !orchestratorManager_) {
        spdlog::error("System not initialized");
        AggregatedResult result;
        result.requestId = requestId;
        result.confidence = 0.0f;
        return result;
    }
    
    try {
        // Process request
        auto result = orchestratorManager_->processRequest(requestId, prompt, parameters);
        
        spdlog::info("Request processing completed for request {}", requestId);
        return result;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to process request {}: {}", requestId, e.what());
        AggregatedResult result;
        result.requestId = requestId;
        result.confidence = 0.0f;
        return result;
    }
}

std::vector<std::shared_ptr<MultiLLMOrchestrator>> GlobalMultiLLMOrchestrationSystem::getAllOrchestrators() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !orchestratorManager_) {
        spdlog::error("System not initialized");
        return std::vector<std::shared_ptr<MultiLLMOrchestrator>>();
    }
    
    return orchestratorManager_->getAllOrchestrators();
}

std::map<std::string, double> GlobalMultiLLMOrchestrationSystem::getSystemMetrics() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !orchestratorManager_) {
        spdlog::error("System not initialized");
        return std::map<std::string, double>();
    }
    
    try {
        // Get system metrics
        auto metrics = orchestratorManager_->getSystemMetrics();
        
        // Add system-specific metrics
        metrics["system_initialized"] = initialized_ ? 1.0 : 0.0;
        metrics["configuration_items"] = static_cast<double>(configuration_.size());
        
        return metrics;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get system metrics: {}", e.what());
        return std::map<std::string, double>();
    }
}

void GlobalMultiLLMOrchestrationSystem::setSystemConfiguration(const std::map<std::string, std::string>& config) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    configuration_ = config;
    spdlog::info("System configuration updated with {} items", config.size());
    
    // Apply configuration to orchestrator manager
    if (orchestratorManager_) {
        try {
            // Parse and apply configuration
            if (config.find("max_orchestrators") != config.end()) {
                int maxOrchestrators = std::stoi(config.at("max_orchestrators"));
                orchestratorManager_->setMaxOrchestrators(maxOrchestrators);
            }
            
            if (config.find("orchestration_strategy") != config.end()) {
                std::string strategy = config.at("orchestration_strategy");
                orchestratorManager_->setOrchestrationStrategy(strategy);
            }
            
            if (config.find("load_balancing_strategy") != config.end()) {
                std::string strategy = config.at("load_balancing_strategy");
                orchestratorManager_->setLoadBalancingStrategy(strategy);
            }
            
        } catch (const std::exception& e) {
            spdlog::error("Failed to apply configuration: {}", e.what());
        }
    }
}

std::map<std::string, std::string> GlobalMultiLLMOrchestrationSystem::getSystemConfiguration() const {
    std::lock_guard<std::mutex> lock(systemMutex_);
    return configuration_;
}

} // namespace orchestration
} // namespace cogniware
