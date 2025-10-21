#include "memory/memory_partitioning.h"
#include <spdlog/spdlog.h>
#include <algorithm>
#include <random>
#include <sstream>

namespace cogniware {
namespace memory {

MemoryPartitioningManager::MemoryPartitioningManager()
    : initialized_(false)
    , maxGlobalMemory_(16 * 1024 * 1024 * 1024) // 16GB
    , maxSharedMemory_(48 * 1024) // 48KB
    , maxConstantMemory_(64 * 1024) // 64KB
    , dmaPolicy_("default")
    , memoryAlignment_(256)
    , totalAllocatedMemory_(0)
    , totalGlobalMemory_(0)
    , totalSharedMemory_(0)
    , totalConstantMemory_(0)
    , systemProfilingEnabled_(false) {
    
    spdlog::info("MemoryPartitioningManager initialized");
}

MemoryPartitioningManager::~MemoryPartitioningManager() {
    shutdown();
}

bool MemoryPartitioningManager::initialize() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (initialized_) {
        spdlog::warn("Memory partitioning manager already initialized");
        return true;
    }
    
    try {
        // Initialize system
        partitions_.clear();
        totalAllocatedMemory_ = 0;
        totalGlobalMemory_ = 0;
        totalSharedMemory_ = 0;
        totalConstantMemory_ = 0;
        
        initialized_ = true;
        spdlog::info("MemoryPartitioningManager initialized successfully");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize memory partitioning manager: {}", e.what());
        return false;
    }
}

void MemoryPartitioningManager::shutdown() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        return;
    }
    
    try {
        // Destroy all partitions
        for (auto& partition : partitions_) {
            if (partition.second) {
                partition.second->shutdown();
            }
        }
        partitions_.clear();
        
        initialized_ = false;
        spdlog::info("MemoryPartitioningManager shutdown completed");
        
    } catch (const std::exception& e) {
        spdlog::error("Error during memory partitioning manager shutdown: {}", e.what());
    }
}

bool MemoryPartitioningManager::isInitialized() const {
    return initialized_;
}

std::shared_ptr<MemoryPartition> MemoryPartitioningManager::createPartition(const MemoryPartitionConfig& config) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return nullptr;
    }
    
    try {
        // Validate partition creation
        if (!validatePartitionCreation(config)) {
            spdlog::error("Invalid partition configuration");
            return nullptr;
        }
        
        // Check if partition already exists
        if (partitions_.find(config.partitionId) != partitions_.end()) {
            spdlog::error("Partition {} already exists", config.partitionId);
            return nullptr;
        }
        
        // Check memory limits
        if (!isMemoryAvailable(config.size, config.type)) {
            spdlog::error("Insufficient memory for partition {}", config.partitionId);
            return nullptr;
        }
        
        // Create partition
        auto partition = std::make_shared<AdvancedMemoryPartition>(config);
        if (!partition->initialize()) {
            spdlog::error("Failed to initialize partition {}", config.partitionId);
            return nullptr;
        }
        
        // Add to manager
        partitions_[config.partitionId] = partition;
        
        // Update memory tracking
        switch (config.type) {
            case MemoryPartitionType::GLOBAL_MEMORY:
                totalGlobalMemory_ += config.size;
                break;
            case MemoryPartitionType::SHARED_MEMORY:
                totalSharedMemory_ += config.size;
                break;
            case MemoryPartitionType::CONSTANT_MEMORY:
                totalConstantMemory_ += config.size;
                break;
            default:
                break;
        }
        totalAllocatedMemory_ += config.size;
        
        spdlog::info("Created memory partition: {}", config.partitionId);
        return partition;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to create partition {}: {}", config.partitionId, e.what());
        return nullptr;
    }
}

bool MemoryPartitioningManager::destroyPartition(const std::string& partitionId) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        // Find partition
        auto it = partitions_.find(partitionId);
        if (it == partitions_.end()) {
            spdlog::error("Partition {} not found", partitionId);
            return false;
        }
        
        // Update memory tracking
        auto config = it->second->getConfig();
        switch (config.type) {
            case MemoryPartitionType::GLOBAL_MEMORY:
                totalGlobalMemory_ -= config.size;
                break;
            case MemoryPartitionType::SHARED_MEMORY:
                totalSharedMemory_ -= config.size;
                break;
            case MemoryPartitionType::CONSTANT_MEMORY:
                totalConstantMemory_ -= config.size;
                break;
            default:
                break;
        }
        totalAllocatedMemory_ -= config.size;
        
        // Shutdown partition
        if (it->second) {
            it->second->shutdown();
        }
        
        // Remove from manager
        partitions_.erase(it);
        
        spdlog::info("Destroyed memory partition: {}", partitionId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to destroy partition {}: {}", partitionId, e.what());
        return false;
    }
}

std::shared_ptr<MemoryPartition> MemoryPartitioningManager::getPartition(const std::string& partitionId) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    auto it = partitions_.find(partitionId);
    if (it != partitions_.end()) {
        return it->second;
    }
    
    return nullptr;
}

std::vector<std::shared_ptr<MemoryPartition>> MemoryPartitioningManager::getAllPartitions() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    std::vector<std::shared_ptr<MemoryPartition>> allPartitions;
    for (const auto& partition : partitions_) {
        allPartitions.push_back(partition.second);
    }
    return allPartitions;
}

std::vector<std::shared_ptr<MemoryPartition>> MemoryPartitioningManager::getPartitionsByType(MemoryPartitionType type) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    std::vector<std::shared_ptr<MemoryPartition>> partitionsByType;
    for (const auto& partition : partitions_) {
        if (partition.second && partition.second->getPartitionType() == type) {
            partitionsByType.push_back(partition.second);
        }
    }
    return partitionsByType;
}

std::vector<std::shared_ptr<MemoryPartition>> MemoryPartitioningManager::getPartitionsByOwner(const std::string& llmId) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    std::vector<std::shared_ptr<MemoryPartition>> partitionsByOwner;
    for (const auto& partition : partitions_) {
        if (partition.second) {
            auto config = partition.second->getConfig();
            if (config.ownerLLM == llmId) {
                partitionsByOwner.push_back(partition.second);
            }
        }
    }
    return partitionsByOwner;
}

bool MemoryPartitioningManager::allocateMemory(const std::string& partitionId, size_t size) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        // Get partition
        auto partition = getPartition(partitionId);
        if (!partition) {
            spdlog::error("Partition {} not found", partitionId);
            return false;
        }
        
        // Allocate memory
        bool success = partition->allocateMemory(size);
        
        if (success) {
            spdlog::info("Allocated {}MB memory for partition {}", size / (1024 * 1024), partitionId);
        } else {
            spdlog::error("Failed to allocate memory for partition {}", partitionId);
        }
        
        return success;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to allocate memory for partition {}: {}", partitionId, e.what());
        return false;
    }
}

bool MemoryPartitioningManager::deallocateMemory(const std::string& partitionId) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        // Get partition
        auto partition = getPartition(partitionId);
        if (!partition) {
            spdlog::error("Partition {} not found", partitionId);
            return false;
        }
        
        // Deallocate memory
        bool success = partition->deallocateMemory();
        
        if (success) {
            spdlog::info("Deallocated memory for partition {}", partitionId);
        } else {
            spdlog::error("Failed to deallocate memory for partition {}", partitionId);
        }
        
        return success;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to deallocate memory for partition {}: {}", partitionId, e.what());
        return false;
    }
}

bool MemoryPartitioningManager::isMemoryAvailable(size_t size, MemoryPartitionType type) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        return false;
    }
    
    try {
        // Check memory limits based on type
        switch (type) {
            case MemoryPartitionType::GLOBAL_MEMORY:
                return (totalGlobalMemory_ + size) <= maxGlobalMemory_;
            case MemoryPartitionType::SHARED_MEMORY:
                return (totalSharedMemory_ + size) <= maxSharedMemory_;
            case MemoryPartitionType::CONSTANT_MEMORY:
                return (totalConstantMemory_ + size) <= maxConstantMemory_;
            default:
                return true; // Other types have no specific limits
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to check memory availability: {}", e.what());
        return false;
    }
}

std::vector<std::string> MemoryPartitioningManager::findAvailablePartitions(size_t size, MemoryPartitionType type) {
    std::vector<std::string> availablePartitions;
    
    try {
        for (const auto& partition : partitions_) {
            if (partition.second && partition.second->getPartitionType() == type) {
                if (partition.second->getAvailableMemory() >= size) {
                    availablePartitions.push_back(partition.first);
                }
            }
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to find available partitions: {}", e.what());
    }
    
    return availablePartitions;
}

bool MemoryPartitioningManager::dmaTransfer(const DMATransferConfig& config) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        // Validate DMA transfer
        if (!validateDMATransfer(config)) {
            spdlog::error("Invalid DMA transfer configuration");
            return false;
        }
        
        // Find source partition
        std::shared_ptr<MemoryPartition> sourcePartition = nullptr;
        for (const auto& partition : partitions_) {
            if (partition.second && partition.second->getDevicePtr() == config.sourcePtr) {
                sourcePartition = partition.second;
                break;
            }
        }
        
        if (!sourcePartition) {
            spdlog::error("Source partition not found for DMA transfer");
            return false;
        }
        
        // Execute DMA transfer
        bool success = sourcePartition->dmaTransfer(config);
        
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

bool MemoryPartitioningManager::dmaTransferAsync(const DMATransferConfig& config) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        // Validate DMA transfer
        if (!validateDMATransfer(config)) {
            spdlog::error("Invalid DMA transfer configuration");
            return false;
        }
        
        // Find source partition
        std::shared_ptr<MemoryPartition> sourcePartition = nullptr;
        for (const auto& partition : partitions_) {
            if (partition.second && partition.second->getDevicePtr() == config.sourcePtr) {
                sourcePartition = partition.second;
                break;
            }
        }
        
        if (!sourcePartition) {
            spdlog::error("Source partition not found for DMA transfer");
            return false;
        }
        
        // Execute async DMA transfer
        bool success = sourcePartition->dmaTransferAsync(config);
        
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

bool MemoryPartitioningManager::waitForAllTransfers() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        // Wait for all transfers in all partitions
        for (const auto& partition : partitions_) {
            if (partition.second) {
                auto activeTransfers = partition.second->getActiveTransfers();
                for (const auto& transferId : activeTransfers) {
                    partition.second->waitForTransfer(transferId);
                }
            }
        }
        
        spdlog::info("All DMA transfers completed");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to wait for all transfers: {}", e.what());
        return false;
    }
}

bool MemoryPartitioningManager::cancelAllTransfers() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        // Cancel all transfers in all partitions
        for (const auto& partition : partitions_) {
            if (partition.second) {
                auto activeTransfers = partition.second->getActiveTransfers();
                for (const auto& transferId : activeTransfers) {
                    partition.second->cancelTransfer(transferId);
                }
            }
        }
        
        spdlog::info("All DMA transfers cancelled");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cancel all transfers: {}", e.what());
        return false;
    }
}

std::vector<std::string> MemoryPartitioningManager::getActiveTransfers() {
    std::vector<std::string> activeTransfers;
    
    try {
        for (const auto& partition : partitions_) {
            if (partition.second) {
                auto partitionTransfers = partition.second->getActiveTransfers();
                activeTransfers.insert(activeTransfers.end(), partitionTransfers.begin(), partitionTransfers.end());
            }
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get active transfers: {}", e.what());
    }
    
    return activeTransfers;
}

bool MemoryPartitioningManager::optimizeMemoryLayout() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Optimizing memory layout across all partitions");
        
        // Optimize each partition
        for (const auto& partition : partitions_) {
            if (partition.second) {
                auto advancedPartition = std::dynamic_pointer_cast<AdvancedMemoryPartition>(partition.second);
                if (advancedPartition) {
                    advancedPartition->optimizeMemoryLayout();
                }
            }
        }
        
        // Update system metrics
        updateSystemMetrics();
        
        spdlog::info("Memory layout optimization completed");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to optimize memory layout: {}", e.what());
        return false;
    }
}

bool MemoryPartitioningManager::balanceMemoryUsage() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Balancing memory usage across partitions");
        
        // Get all partitions
        std::vector<std::shared_ptr<MemoryPartition>> allPartitions;
        for (const auto& partition : partitions_) {
            if (partition.second) {
                allPartitions.push_back(partition.second);
            }
        }
        
        if (allPartitions.empty()) {
            spdlog::warn("No partitions found for memory balancing");
            return true;
        }
        
        // Calculate average utilization
        float totalUtilization = 0.0f;
        for (const auto& partition : allPartitions) {
            totalUtilization += partition->getUtilization();
        }
        float averageUtilization = totalUtilization / allPartitions.size();
        
        // Balance memory usage (simplified implementation)
        for (const auto& partition : allPartitions) {
            float utilization = partition->getUtilization();
            if (utilization > averageUtilization * 1.2f) {
                // Partition is overloaded, try to redistribute
                spdlog::debug("Partition {} is overloaded (utilization: {:.2f})", 
                            partition->getPartitionId(), utilization);
            } else if (utilization < averageUtilization * 0.8f) {
                // Partition is underloaded, can take more work
                spdlog::debug("Partition {} is underloaded (utilization: {:.2f})", 
                            partition->getPartitionId(), utilization);
            }
        }
        
        spdlog::info("Memory usage balancing completed");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to balance memory usage: {}", e.what());
        return false;
    }
}

bool MemoryPartitioningManager::cleanupUnusedPartitions() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Cleaning up unused memory partitions");
        
        // Find unused partitions
        std::vector<std::string> unusedPartitions;
        for (const auto& partition : partitions_) {
            if (partition.second && !partition.second->isMemoryAllocated()) {
                unusedPartitions.push_back(partition.first);
            }
        }
        
        // Cleanup unused partitions
        for (const auto& partitionId : unusedPartitions) {
            spdlog::info("Cleaning up unused partition: {}", partitionId);
            cleanupPartition(partitionId);
        }
        
        spdlog::info("Cleaned up {} unused partitions", unusedPartitions.size());
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cleanup unused partitions: {}", e.what());
        return false;
    }
}

bool MemoryPartitioningManager::validateSystem() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Validating memory partitioning system");
        
        bool isValid = true;
        
        // Validate each partition
        for (const auto& partition : partitions_) {
            if (partition.second) {
                auto advancedPartition = std::dynamic_pointer_cast<AdvancedMemoryPartition>(partition.second);
                if (advancedPartition && !advancedPartition->validateMemoryIntegrity(0, advancedPartition->getMemorySize())) {
                    spdlog::error("Partition {} failed memory integrity validation", partition.first);
                    isValid = false;
                }
            }
        }
        
        // Validate memory limits
        if (totalGlobalMemory_ > maxGlobalMemory_) {
            spdlog::error("Total global memory exceeds limit");
            isValid = false;
        }
        
        if (totalSharedMemory_ > maxSharedMemory_) {
            spdlog::error("Total shared memory exceeds limit");
            isValid = false;
        }
        
        if (totalConstantMemory_ > maxConstantMemory_) {
            spdlog::error("Total constant memory exceeds limit");
            isValid = false;
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

std::map<std::string, double> MemoryPartitioningManager::getSystemMetrics() {
    std::map<std::string, double> metrics;
    
    try {
        // Update system metrics
        updateSystemMetrics();
        
        // Calculate system metrics
        metrics["total_partitions"] = static_cast<double>(partitions_.size());
        metrics["total_memory"] = static_cast<double>(totalAllocatedMemory_);
        metrics["global_memory"] = static_cast<double>(totalGlobalMemory_);
        metrics["shared_memory"] = static_cast<double>(totalSharedMemory_);
        metrics["constant_memory"] = static_cast<double>(totalConstantMemory_);
        metrics["max_global_memory"] = static_cast<double>(maxGlobalMemory_);
        metrics["max_shared_memory"] = static_cast<double>(maxSharedMemory_);
        metrics["max_constant_memory"] = static_cast<double>(maxConstantMemory_);
        
        // Calculate utilization percentages
        if (maxGlobalMemory_ > 0) {
            metrics["global_memory_utilization"] = static_cast<double>(totalGlobalMemory_) / maxGlobalMemory_;
        }
        if (maxSharedMemory_ > 0) {
            metrics["shared_memory_utilization"] = static_cast<double>(totalSharedMemory_) / maxSharedMemory_;
        }
        if (maxConstantMemory_ > 0) {
            metrics["constant_memory_utilization"] = static_cast<double>(totalConstantMemory_) / maxConstantMemory_;
        }
        
        // Calculate average partition utilization
        double totalUtilization = 0.0;
        int partitionCount = 0;
        for (const auto& partition : partitions_) {
            if (partition.second) {
                totalUtilization += partition.second->getUtilization();
                partitionCount++;
            }
        }
        if (partitionCount > 0) {
            metrics["average_partition_utilization"] = totalUtilization / partitionCount;
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get system metrics: {}", e.what());
    }
    
    return metrics;
}

std::map<std::string, int> MemoryPartitioningManager::getPartitionCounts() {
    std::map<std::string, int> counts;
    
    try {
        counts["total"] = static_cast<int>(partitions_.size());
        counts["global_memory"] = 0;
        counts["shared_memory"] = 0;
        counts["constant_memory"] = 0;
        counts["pinned_memory"] = 0;
        counts["zero_copy_memory"] = 0;
        counts["unified_memory"] = 0;
        
        for (const auto& partition : partitions_) {
            if (partition.second) {
                switch (partition.second->getPartitionType()) {
                    case MemoryPartitionType::GLOBAL_MEMORY:
                        counts["global_memory"]++;
                        break;
                    case MemoryPartitionType::SHARED_MEMORY:
                        counts["shared_memory"]++;
                        break;
                    case MemoryPartitionType::CONSTANT_MEMORY:
                        counts["constant_memory"]++;
                        break;
                    case MemoryPartitionType::PINNED_MEMORY:
                        counts["pinned_memory"]++;
                        break;
                    case MemoryPartitionType::ZERO_COPY_MEMORY:
                        counts["zero_copy_memory"]++;
                        break;
                    case MemoryPartitionType::UNIFIED_MEMORY:
                        counts["unified_memory"]++;
                        break;
                    default:
                        break;
                }
            }
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get partition counts: {}", e.what());
    }
    
    return counts;
}

std::map<std::string, double> MemoryPartitioningManager::getMemoryUtilization() {
    std::map<std::string, double> utilization;
    
    try {
        // Calculate memory utilization
        if (maxGlobalMemory_ > 0) {
            utilization["global_memory"] = static_cast<double>(totalGlobalMemory_) / maxGlobalMemory_;
        }
        if (maxSharedMemory_ > 0) {
            utilization["shared_memory"] = static_cast<double>(totalSharedMemory_) / maxSharedMemory_;
        }
        if (maxConstantMemory_ > 0) {
            utilization["constant_memory"] = static_cast<double>(totalConstantMemory_) / maxConstantMemory_;
        }
        
        // Calculate average partition utilization
        double totalUtilization = 0.0;
        int partitionCount = 0;
        for (const auto& partition : partitions_) {
            if (partition.second) {
                totalUtilization += partition.second->getUtilization();
                partitionCount++;
            }
        }
        if (partitionCount > 0) {
            utilization["average_partition"] = totalUtilization / partitionCount;
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get memory utilization: {}", e.what());
    }
    
    return utilization;
}

bool MemoryPartitioningManager::enableSystemProfiling() {
    systemProfilingEnabled_ = true;
    spdlog::info("System profiling enabled");
    return true;
}

bool MemoryPartitioningManager::disableSystemProfiling() {
    systemProfilingEnabled_ = false;
    spdlog::info("System profiling disabled");
    return true;
}

std::map<std::string, double> MemoryPartitioningManager::getSystemProfilingData() {
    std::map<std::string, double> profilingData;
    
    if (!systemProfilingEnabled_) {
        return profilingData;
    }
    
    try {
        // Get system metrics
        auto metrics = getSystemMetrics();
        auto utilization = getMemoryUtilization();
        
        // Combine metrics and utilization
        profilingData.insert(metrics.begin(), metrics.end());
        profilingData.insert(utilization.begin(), utilization.end());
        
        // Add profiling-specific data
        profilingData["profiling_enabled"] = systemProfilingEnabled_ ? 1.0 : 0.0;
        profilingData["dma_policy"] = static_cast<double>(dmaPolicy_.length());
        profilingData["memory_alignment"] = static_cast<double>(memoryAlignment_);
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get system profiling data: {}", e.what());
    }
    
    return profilingData;
}

void MemoryPartitioningManager::setMemoryLimits(size_t maxGlobalMemory, size_t maxSharedMemory, size_t maxConstantMemory) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    maxGlobalMemory_ = maxGlobalMemory;
    maxSharedMemory_ = maxSharedMemory;
    maxConstantMemory_ = maxConstantMemory;
    spdlog::info("Set memory limits: {}MB global, {}KB shared, {}KB constant", 
                maxGlobalMemory / (1024 * 1024), maxSharedMemory / 1024, maxConstantMemory / 1024);
}

std::map<std::string, size_t> MemoryPartitioningManager::getMemoryLimits() const {
    std::map<std::string, size_t> limits;
    limits["max_global_memory"] = maxGlobalMemory_;
    limits["max_shared_memory"] = maxSharedMemory_;
    limits["max_constant_memory"] = maxConstantMemory_;
    return limits;
}

void MemoryPartitioningManager::setDMAPolicy(const std::string& policy) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    dmaPolicy_ = policy;
    spdlog::info("Set DMA policy to: {}", policy);
}

std::string MemoryPartitioningManager::getDMAPolicy() const {
    return dmaPolicy_;
}

void MemoryPartitioningManager::setMemoryAlignment(size_t alignment) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    memoryAlignment_ = alignment;
    spdlog::info("Set memory alignment to: {}", alignment);
}

size_t MemoryPartitioningManager::getMemoryAlignment() const {
    return memoryAlignment_;
}

bool MemoryPartitioningManager::validatePartitionCreation(const MemoryPartitionConfig& config) {
    try {
        // Validate partition ID
        if (config.partitionId.empty()) {
            spdlog::error("Partition ID cannot be empty");
            return false;
        }
        
        // Validate memory size
        if (config.size == 0) {
            spdlog::error("Memory size must be greater than 0");
            return false;
        }
        
        // Validate alignment
        if (config.alignment == 0) {
            spdlog::error("Memory alignment must be greater than 0");
            return false;
        }
        
        // Validate priority
        if (config.priority < 0.0f || config.priority > 1.0f) {
            spdlog::error("Priority must be between 0.0 and 1.0");
            return false;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to validate partition creation: {}", e.what());
        return false;
    }
}

bool MemoryPartitioningManager::validateDMATransfer(const DMATransferConfig& config) {
    try {
        // Validate transfer ID
        if (config.transferId.empty()) {
            spdlog::error("Transfer ID cannot be empty");
            return false;
        }
        
        // Validate pointers
        if (config.sourcePtr == nullptr) {
            spdlog::error("Source pointer cannot be null");
            return false;
        }
        
        if (config.destinationPtr == nullptr) {
            spdlog::error("Destination pointer cannot be null");
            return false;
        }
        
        // Validate size
        if (config.size == 0) {
            spdlog::error("Transfer size must be greater than 0");
            return false;
        }
        
        // Validate priority
        if (config.priority < 0.0f || config.priority > 1.0f) {
            spdlog::error("Transfer priority must be between 0.0 and 1.0");
            return false;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to validate DMA transfer: {}", e.what());
        return false;
    }
}

std::string MemoryPartitioningManager::generatePartitionId() {
    try {
        // Generate unique partition ID
        std::stringstream ss;
        ss << "partition_" << std::chrono::system_clock::now().time_since_epoch().count();
        return ss.str();
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to generate partition ID: {}", e.what());
        return "partition_" + std::to_string(std::chrono::system_clock::now().time_since_epoch().count());
    }
}

bool MemoryPartitioningManager::cleanupPartition(const std::string& partitionId) {
    try {
        // Get partition
        auto partition = getPartition(partitionId);
        if (!partition) {
            spdlog::error("Partition {} not found for cleanup", partitionId);
            return false;
        }
        
        // Shutdown partition
        partition->shutdown();
        
        // Remove from manager
        partitions_.erase(partitionId);
        
        spdlog::info("Cleaned up partition: {}", partitionId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cleanup partition {}: {}", partitionId, e.what());
        return false;
    }
}

void MemoryPartitioningManager::updateSystemMetrics() {
    try {
        // Reset counters
        totalAllocatedMemory_ = 0;
        totalGlobalMemory_ = 0;
        totalSharedMemory_ = 0;
        totalConstantMemory_ = 0;
        
        // Update counters
        for (const auto& partition : partitions_) {
            if (partition.second && partition.second->isMemoryAllocated()) {
                auto config = partition.second->getConfig();
                totalAllocatedMemory_ += config.size;
                
                switch (config.type) {
                    case MemoryPartitionType::GLOBAL_MEMORY:
                        totalGlobalMemory_ += config.size;
                        break;
                    case MemoryPartitionType::SHARED_MEMORY:
                        totalSharedMemory_ += config.size;
                        break;
                    case MemoryPartitionType::CONSTANT_MEMORY:
                        totalConstantMemory_ += config.size;
                        break;
                    default:
                        break;
                }
            }
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to update system metrics: {}", e.what());
    }
}

bool MemoryPartitioningManager::findBestPartition(size_t size, MemoryPartitionType type, std::string& bestPartitionId) {
    try {
        // Find partitions that can satisfy the request
        std::vector<std::string> availablePartitions = findAvailablePartitions(size, type);
        
        if (availablePartitions.empty()) {
            spdlog::warn("No available partitions found for size {} and type {}", size, static_cast<int>(type));
            return false;
        }
        
        // Select best partition (simplified implementation)
        bestPartitionId = availablePartitions[0];
        
        spdlog::debug("Selected best partition {} for size {} and type {}", bestPartitionId, size, static_cast<int>(type));
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to find best partition: {}", e.what());
        return false;
    }
}

bool MemoryPartitioningManager::allocateMemoryToPartition(const std::string& partitionId, size_t size) {
    try {
        // Get partition
        auto partition = getPartition(partitionId);
        if (!partition) {
            spdlog::error("Partition {} not found for allocation", partitionId);
            return false;
        }
        
        // Allocate memory
        bool success = partition->allocateMemory(size);
        
        if (success) {
            spdlog::info("Allocated {}MB memory to partition {}", size / (1024 * 1024), partitionId);
        } else {
            spdlog::error("Failed to allocate memory to partition {}", partitionId);
        }
        
        return success;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to allocate memory to partition {}: {}", partitionId, e.what());
        return false;
    }
}

} // namespace memory
} // namespace cogniware
