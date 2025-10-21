#include "memory/memory_partitioning.h"
#include <spdlog/spdlog.h>

namespace cogniware {
namespace memory {

GlobalMemoryPartitioningSystem& GlobalMemoryPartitioningSystem::getInstance() {
    static GlobalMemoryPartitioningSystem instance;
    return instance;
}

GlobalMemoryPartitioningSystem::GlobalMemoryPartitioningSystem()
    : initialized_(false) {
    
    spdlog::info("GlobalMemoryPartitioningSystem singleton created");
}

GlobalMemoryPartitioningSystem::~GlobalMemoryPartitioningSystem() {
    shutdown();
}

bool GlobalMemoryPartitioningSystem::initialize() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (initialized_) {
        spdlog::warn("Global memory partitioning system already initialized");
        return true;
    }
    
    try {
        // Initialize partitioning manager
        partitioningManager_ = std::make_shared<MemoryPartitioningManager>();
        if (!partitioningManager_->initialize()) {
            spdlog::error("Failed to initialize memory partitioning manager");
            return false;
        }
        
        // Set default configuration
        configuration_["max_global_memory"] = "17179869184"; // 16GB
        configuration_["max_shared_memory"] = "49152"; // 48KB
        configuration_["max_constant_memory"] = "65536"; // 64KB
        configuration_["dma_policy"] = "default";
        configuration_["memory_alignment"] = "256";
        configuration_["auto_cleanup"] = "enabled";
        configuration_["memory_optimization"] = "enabled";
        configuration_["profiling"] = "disabled";
        
        initialized_ = true;
        spdlog::info("GlobalMemoryPartitioningSystem initialized successfully");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize global memory partitioning system: {}", e.what());
        return false;
    }
}

void GlobalMemoryPartitioningSystem::shutdown() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_) {
        return;
    }
    
    try {
        // Shutdown partitioning manager
        if (partitioningManager_) {
            partitioningManager_->shutdown();
            partitioningManager_.reset();
        }
        
        initialized_ = false;
        spdlog::info("GlobalMemoryPartitioningSystem shutdown completed");
        
    } catch (const std::exception& e) {
        spdlog::error("Error during global memory partitioning system shutdown: {}", e.what());
    }
}

bool GlobalMemoryPartitioningSystem::isInitialized() const {
    return initialized_;
}

std::shared_ptr<MemoryPartitioningManager> GlobalMemoryPartitioningSystem::getPartitioningManager() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    return partitioningManager_;
}

std::shared_ptr<MemoryPartition> GlobalMemoryPartitioningSystem::createPartition(const MemoryPartitionConfig& config) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !partitioningManager_) {
        spdlog::error("System not initialized");
        return nullptr;
    }
    
    try {
        // Create partition
        auto partition = partitioningManager_->createPartition(config);
        
        if (partition) {
            spdlog::info("Created memory partition: {}", config.partitionId);
        } else {
            spdlog::error("Failed to create memory partition: {}", config.partitionId);
        }
        
        return partition;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to create partition {}: {}", config.partitionId, e.what());
        return nullptr;
    }
}

bool GlobalMemoryPartitioningSystem::destroyPartition(const std::string& partitionId) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !partitioningManager_) {
        spdlog::error("System not initialized");
        return false;
    }
    
    try {
        // Destroy partition
        bool success = partitioningManager_->destroyPartition(partitionId);
        
        if (success) {
            spdlog::info("Destroyed memory partition: {}", partitionId);
        } else {
            spdlog::error("Failed to destroy memory partition: {}", partitionId);
        }
        
        return success;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to destroy partition {}: {}", partitionId, e.what());
        return false;
    }
}

std::shared_ptr<MemoryPartition> GlobalMemoryPartitioningSystem::getPartition(const std::string& partitionId) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !partitioningManager_) {
        spdlog::error("System not initialized");
        return nullptr;
    }
    
    return partitioningManager_->getPartition(partitionId);
}

bool GlobalMemoryPartitioningSystem::dmaTransfer(const DMATransferConfig& config) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !partitioningManager_) {
        spdlog::error("System not initialized");
        return false;
    }
    
    try {
        // Execute DMA transfer
        bool success = partitioningManager_->dmaTransfer(config);
        
        if (success) {
            spdlog::info("DMA transfer {} completed", config.transferId);
        } else {
            spdlog::error("DMA transfer {} failed", config.transferId);
        }
        
        return success;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to execute DMA transfer {}: {}", config.transferId, e.what());
        return false;
    }
}

bool GlobalMemoryPartitioningSystem::dmaTransferAsync(const DMATransferConfig& config) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !partitioningManager_) {
        spdlog::error("System not initialized");
        return false;
    }
    
    try {
        // Execute async DMA transfer
        bool success = partitioningManager_->dmaTransferAsync(config);
        
        if (success) {
            spdlog::info("Async DMA transfer {} started", config.transferId);
        } else {
            spdlog::error("Async DMA transfer {} failed", config.transferId);
        }
        
        return success;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to execute async DMA transfer {}: {}", config.transferId, e.what());
        return false;
    }
}

std::vector<std::shared_ptr<MemoryPartition>> GlobalMemoryPartitioningSystem::getAllPartitions() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !partitioningManager_) {
        spdlog::error("System not initialized");
        return std::vector<std::shared_ptr<MemoryPartition>>();
    }
    
    return partitioningManager_->getAllPartitions();
}

std::map<std::string, double> GlobalMemoryPartitioningSystem::getSystemMetrics() {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    if (!initialized_ || !partitioningManager_) {
        spdlog::error("System not initialized");
        return std::map<std::string, double>();
    }
    
    try {
        // Get system metrics
        auto metrics = partitioningManager_->getSystemMetrics();
        
        // Add system-specific metrics
        metrics["system_initialized"] = initialized_ ? 1.0 : 0.0;
        metrics["configuration_items"] = static_cast<double>(configuration_.size());
        
        return metrics;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get system metrics: {}", e.what());
        return std::map<std::string, double>();
    }
}

void GlobalMemoryPartitioningSystem::setSystemConfiguration(const std::map<std::string, std::string>& config) {
    std::lock_guard<std::mutex> lock(systemMutex_);
    
    configuration_ = config;
    spdlog::info("System configuration updated with {} items", config.size());
    
    // Apply configuration to partitioning manager
    if (partitioningManager_) {
        try {
            // Parse and apply configuration
            if (config.find("max_global_memory") != config.end() && 
                config.find("max_shared_memory") != config.end() && 
                config.find("max_constant_memory") != config.end()) {
                size_t maxGlobalMemory = std::stoull(config.at("max_global_memory"));
                size_t maxSharedMemory = std::stoull(config.at("max_shared_memory"));
                size_t maxConstantMemory = std::stoull(config.at("max_constant_memory"));
                partitioningManager_->setMemoryLimits(maxGlobalMemory, maxSharedMemory, maxConstantMemory);
            }
            
            if (config.find("dma_policy") != config.end()) {
                std::string dmaPolicy = config.at("dma_policy");
                partitioningManager_->setDMAPolicy(dmaPolicy);
            }
            
            if (config.find("memory_alignment") != config.end()) {
                size_t alignment = std::stoull(config.at("memory_alignment"));
                partitioningManager_->setMemoryAlignment(alignment);
            }
            
        } catch (const std::exception& e) {
            spdlog::error("Failed to apply configuration: {}", e.what());
        }
    }
}

std::map<std::string, std::string> GlobalMemoryPartitioningSystem::getSystemConfiguration() const {
    std::lock_guard<std::mutex> lock(systemMutex_);
    return configuration_;
}

} // namespace memory
} // namespace cogniware
