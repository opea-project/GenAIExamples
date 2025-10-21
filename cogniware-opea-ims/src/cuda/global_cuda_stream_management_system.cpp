#include "cuda/cuda_stream_management.h"
#include <spdlog/spdlog.h>

namespace cogniware {
namespace cuda {

GlobalCUDAStreamManagementSystem& GlobalCUDAStreamManagementSystem::getInstance() {
    static GlobalCUDAStreamManagementSystem instance;
    return instance;
}

GlobalCUDAStreamManagementSystem::GlobalCUDAStreamManagementSystem()
    : initialized_(false) {
    
    spdlog::info("GlobalCUDAStreamManagementSystem singleton created");
}

GlobalCUDAStreamManagementSystem::~GlobalCUDAStreamManagementSystem() {
    shutdown();
}

bool GlobalCUDAStreamManagementSystem::initialize() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (initialized_) {
        spdlog::warn("Global CUDA stream management system already initialized");
        return true;
    }
    
    try {
        // Initialize stream manager
        streamManager_ = std::make_shared<CUDAStreamManager>();
        if (!streamManager_->initialize()) {
            spdlog::error("Failed to initialize CUDA stream manager");
            return false;
        }
        
        // Set default configuration
        configuration_["max_streams"] = "10";
        configuration_["scheduling_strategy"] = "balanced";
        configuration_["load_balancing_strategy"] = "round_robin";
        configuration_["auto_cleanup"] = "enabled";
        configuration_["system_optimization"] = "enabled";
        configuration_["profiling"] = "disabled";
        
        initialized_ = true;
        spdlog::info("GlobalCUDAStreamManagementSystem initialized successfully");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize global CUDA stream management system: {}", e.what());
        return false;
    }
}

void GlobalCUDAStreamManagementSystem::shutdown() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_) {
        return;
    }
    
    try {
        // Shutdown stream manager
        if (streamManager_) {
            streamManager_->shutdown();
            streamManager_.reset();
        }
        
        initialized_ = false;
        spdlog::info("GlobalCUDAStreamManagementSystem shutdown completed");
        
    } catch (const std::exception& e) {
        spdlog::error("Error during global CUDA stream management system shutdown: {}", e.what());
    }
}

bool GlobalCUDAStreamManagementSystem::isInitialized() const {
    return initialized_;
}

std::shared_ptr<CUDAStreamManager> GlobalCUDAStreamManagementSystem::getStreamManager() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    return streamManager_;
}

std::shared_ptr<CUDAStream> GlobalCUDAStreamManagementSystem::createStream(const CUDAStreamConfig& config) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !streamManager_) {
        spdlog::error("System not initialized");
        return nullptr;
    }
    
    try {
        // Create stream
        auto stream = streamManager_->createStream(config);
        
        if (stream) {
            spdlog::info("Created CUDA stream: {}", config.streamId);
        } else {
            spdlog::error("Failed to create CUDA stream: {}", config.streamId);
        }
        
        return stream;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to create CUDA stream {}: {}", config.streamId, e.what());
        return nullptr;
    }
}

bool GlobalCUDAStreamManagementSystem::destroyStream(const std::string& streamId) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !streamManager_) {
        spdlog::error("System not initialized");
        return false;
    }
    
    try {
        // Destroy stream
        bool destroyed = streamManager_->destroyStream(streamId);
        
        if (destroyed) {
            spdlog::info("Destroyed CUDA stream: {}", streamId);
        } else {
            spdlog::error("Failed to destroy CUDA stream: {}", streamId);
        }
        
        return destroyed;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to destroy CUDA stream {}: {}", streamId, e.what());
        return false;
    }
}

std::shared_ptr<CUDAStream> GlobalCUDAStreamManagementSystem::getStream(const std::string& streamId) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !streamManager_) {
        spdlog::error("System not initialized");
        return nullptr;
    }
    
    return streamManager_->getStream(streamId);
}

std::future<CUDAStreamResult> GlobalCUDAStreamManagementSystem::executeTaskAsync(const CUDAStreamTask& task) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !streamManager_) {
        spdlog::error("System not initialized");
        return std::async(std::launch::deferred, []() {
            CUDAStreamResult result;
            result.success = false;
            result.error = "System not initialized";
            return result;
        });
    }
    
    try {
        // Execute async task
        auto future = streamManager_->executeTaskAsync(task);
        
        spdlog::info("Async task execution started for task {}", task.taskId);
        return future;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to start async task execution for task {}: {}", task.taskId, e.what());
        return std::async(std::launch::deferred, []() {
            CUDAStreamResult result;
            result.success = false;
            result.error = "Failed to start async task execution";
            return result;
        });
    }
}

CUDAStreamResult GlobalCUDAStreamManagementSystem::executeTask(const CUDAStreamTask& task) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !streamManager_) {
        spdlog::error("System not initialized");
        CUDAStreamResult result;
        result.success = false;
        result.error = "System not initialized";
        return result;
    }
    
    try {
        // Execute task
        auto result = streamManager_->executeTask(task);
        
        if (result.success) {
            spdlog::info("Task execution completed for task {}", task.taskId);
        } else {
            spdlog::error("Task execution failed for task {}: {}", task.taskId, result.error);
        }
        
        return result;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to execute task {}: {}", task.taskId, e.what());
        CUDAStreamResult result;
        result.success = false;
        result.error = "Task execution failed: " + std::string(e.what());
        return result;
    }
}

std::vector<std::shared_ptr<CUDAStream>> GlobalCUDAStreamManagementSystem::getAllStreams() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !streamManager_) {
        spdlog::error("System not initialized");
        return std::vector<std::shared_ptr<CUDAStream>>();
    }
    
    return streamManager_->getAllStreams();
}

std::map<std::string, double> GlobalCUDAStreamManagementSystem::getSystemMetrics() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !streamManager_) {
        spdlog::error("System not initialized");
        return std::map<std::string, double>();
    }
    
    try {
        // Get system metrics
        auto metrics = streamManager_->getSystemMetrics();
        
        // Add system-specific metrics
        metrics["system_initialized"] = initialized_ ? 1.0 : 0.0;
        metrics["configuration_items"] = static_cast<double>(configuration_.size());
        
        return metrics;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get system metrics: {}", e.what());
        return std::map<std::string, double>();
    }
}

void GlobalCUDAStreamManagementSystem::setSystemConfiguration(const std::map<std::string, std::string>& config) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    configuration_ = config;
    spdlog::info("System configuration updated with {} items", config.size());
    
    // Apply configuration to stream manager
    if (streamManager_) {
        try {
            // Parse and apply configuration
            if (config.find("max_streams") != config.end()) {
                int maxStreams = std::stoi(config.at("max_streams"));
                streamManager_->setMaxStreams(maxStreams);
            }
            
            if (config.find("scheduling_strategy") != config.end()) {
                std::string strategy = config.at("scheduling_strategy");
                streamManager_->setSchedulingStrategy(strategy);
            }
            
            if (config.find("load_balancing_strategy") != config.end()) {
                std::string strategy = config.at("load_balancing_strategy");
                streamManager_->setLoadBalancingStrategy(strategy);
            }
            
        } catch (const std::exception& e) {
            spdlog::error("Failed to apply configuration: {}", e.what());
        }
    }
}

std::map<std::string, std::string> GlobalCUDAStreamManagementSystem::getSystemConfiguration() const {
    std::lock_guard<std::mutex> lock(systemMutex_);
    return configuration_;
}

} // namespace cuda
} // namespace cogniware
