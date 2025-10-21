#include "scheduler/compute_node_scheduler.h"
#include <spdlog/spdlog.h>

namespace cogniware {
namespace scheduler {

GlobalComputeNodeSchedulerSystem& GlobalComputeNodeSchedulerSystem::getInstance() {
    static GlobalComputeNodeSchedulerSystem instance;
    return instance;
}

GlobalComputeNodeSchedulerSystem::GlobalComputeNodeSchedulerSystem()
    : initialized_(false) {
    
    spdlog::info("GlobalComputeNodeSchedulerSystem singleton created");
}

GlobalComputeNodeSchedulerSystem::~GlobalComputeNodeSchedulerSystem() {
    shutdown();
}

bool GlobalComputeNodeSchedulerSystem::initialize() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (initialized_) {
        spdlog::warn("Global compute node scheduler system already initialized");
        return true;
    }
    
    try {
        // Initialize scheduler manager
        schedulerManager_ = std::make_shared<ComputeNodeSchedulerManager>();
        if (!schedulerManager_->initialize()) {
            spdlog::error("Failed to initialize compute node scheduler manager");
            return false;
        }
        
        // Set default configuration
        configuration_["max_schedulers"] = "10";
        configuration_["scheduling_strategy"] = "balanced";
        configuration_["load_balancing_strategy"] = "round_robin";
        configuration_["auto_cleanup"] = "enabled";
        configuration_["system_optimization"] = "enabled";
        configuration_["profiling"] = "disabled";
        
        initialized_ = true;
        spdlog::info("GlobalComputeNodeSchedulerSystem initialized successfully");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize global compute node scheduler system: {}", e.what());
        return false;
    }
}

void GlobalComputeNodeSchedulerSystem::shutdown() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_) {
        return;
    }
    
    try {
        // Shutdown scheduler manager
        if (schedulerManager_) {
            schedulerManager_->shutdown();
            schedulerManager_.reset();
        }
        
        initialized_ = false;
        spdlog::info("GlobalComputeNodeSchedulerSystem shutdown completed");
        
    } catch (const std::exception& e) {
        spdlog::error("Error during global compute node scheduler system shutdown: {}", e.what());
    }
}

bool GlobalComputeNodeSchedulerSystem::isInitialized() const {
    return initialized_;
}

std::shared_ptr<ComputeNodeSchedulerManager> GlobalComputeNodeSchedulerSystem::getSchedulerManager() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    return schedulerManager_;
}

std::shared_ptr<ComputeNodeScheduler> GlobalComputeNodeSchedulerSystem::createScheduler(const SchedulerConfig& config) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !schedulerManager_) {
        spdlog::error("System not initialized");
        return nullptr;
    }
    
    try {
        // Create scheduler
        auto scheduler = schedulerManager_->createScheduler(config);
        
        if (scheduler) {
            spdlog::info("Created compute node scheduler: {}", config.schedulerId);
        } else {
            spdlog::error("Failed to create compute node scheduler: {}", config.schedulerId);
        }
        
        return scheduler;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to create compute node scheduler {}: {}", config.schedulerId, e.what());
        return nullptr;
    }
}

bool GlobalComputeNodeSchedulerSystem::destroyScheduler(const std::string& schedulerId) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !schedulerManager_) {
        spdlog::error("System not initialized");
        return false;
    }
    
    try {
        // Destroy scheduler
        bool destroyed = schedulerManager_->destroyScheduler(schedulerId);
        
        if (destroyed) {
            spdlog::info("Destroyed compute node scheduler: {}", schedulerId);
        } else {
            spdlog::error("Failed to destroy compute node scheduler: {}", schedulerId);
        }
        
        return destroyed;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to destroy compute node scheduler {}: {}", schedulerId, e.what());
        return false;
    }
}

std::shared_ptr<ComputeNodeScheduler> GlobalComputeNodeSchedulerSystem::getScheduler(const std::string& schedulerId) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !schedulerManager_) {
        spdlog::error("System not initialized");
        return nullptr;
    }
    
    return schedulerManager_->getScheduler(schedulerId);
}

std::future<TaskExecutionResult> GlobalComputeNodeSchedulerSystem::submitTaskAsync(const TaskExecutionRequest& request) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !schedulerManager_) {
        spdlog::error("System not initialized");
        return std::async(std::launch::deferred, []() {
            TaskExecutionResult result;
            result.success = false;
            result.error = "System not initialized";
            return result;
        });
    }
    
    try {
        // Submit async task
        auto future = schedulerManager_->submitTaskAsync(request);
        
        spdlog::info("Async task submission started for task {}", request.taskId);
        return future;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to submit async task {}: {}", request.taskId, e.what());
        return std::async(std::launch::deferred, []() {
            TaskExecutionResult result;
            result.success = false;
            result.error = "Failed to submit async task";
            return result;
        });
    }
}

TaskExecutionResult GlobalComputeNodeSchedulerSystem::submitTask(const TaskExecutionRequest& request) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !schedulerManager_) {
        spdlog::error("System not initialized");
        TaskExecutionResult result;
        result.success = false;
        result.error = "System not initialized";
        return result;
    }
    
    try {
        // Submit task
        auto result = schedulerManager_->submitTask(request);
        
        if (result.success) {
            spdlog::info("Task submission completed for task {}", request.taskId);
        } else {
            spdlog::error("Task submission failed for task {}: {}", request.taskId, result.error);
        }
        
        return result;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to submit task {}: {}", request.taskId, e.what());
        TaskExecutionResult result;
        result.success = false;
        result.error = "Task submission failed: " + std::string(e.what());
        return result;
    }
}

std::vector<std::shared_ptr<ComputeNodeScheduler>> GlobalComputeNodeSchedulerSystem::getAllSchedulers() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !schedulerManager_) {
        spdlog::error("System not initialized");
        return std::vector<std::shared_ptr<ComputeNodeScheduler>>();
    }
    
    return schedulerManager_->getAllSchedulers();
}

std::map<std::string, double> GlobalComputeNodeSchedulerSystem::getSystemMetrics() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !schedulerManager_) {
        spdlog::error("System not initialized");
        return std::map<std::string, double>();
    }
    
    try {
        // Get system metrics
        auto metrics = schedulerManager_->getSystemMetrics();
        
        // Add system-specific metrics
        metrics["system_initialized"] = initialized_ ? 1.0 : 0.0;
        metrics["configuration_items"] = static_cast<double>(configuration_.size());
        
        return metrics;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get system metrics: {}", e.what());
        return std::map<std::string, double>();
    }
}

void GlobalComputeNodeSchedulerSystem::setSystemConfiguration(const std::map<std::string, std::string>& config) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    configuration_ = config;
    spdlog::info("System configuration updated with {} items", config.size());
    
    // Apply configuration to scheduler manager
    if (schedulerManager_) {
        try {
            // Parse and apply configuration
            if (config.find("max_schedulers") != config.end()) {
                int maxSchedulers = std::stoi(config.at("max_schedulers"));
                schedulerManager_->setMaxSchedulers(maxSchedulers);
            }
            
            if (config.find("scheduling_strategy") != config.end()) {
                std::string strategy = config.at("scheduling_strategy");
                schedulerManager_->setSchedulingStrategy(strategy);
            }
            
            if (config.find("load_balancing_strategy") != config.end()) {
                std::string strategy = config.at("load_balancing_strategy");
                schedulerManager_->setLoadBalancingStrategy(strategy);
            }
            
        } catch (const std::exception& e) {
            spdlog::error("Failed to apply configuration: {}", e.what());
        }
    }
}

std::map<std::string, std::string> GlobalComputeNodeSchedulerSystem::getSystemConfiguration() const {
    std::lock_guard<std::mutex> lock(systemMutex_);
    return configuration_;
}

} // namespace scheduler
} // namespace cogniware
