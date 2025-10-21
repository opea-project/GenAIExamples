#include <gtest/gtest.h>
#include <spdlog/spdlog.h>
#include "memory/memory_partitioning.h"
#include <chrono>
#include <thread>

using namespace cogniware::memory;

class MemoryPartitioningSystemTest : public ::testing::Test {
protected:
    void SetUp() override {
        spdlog::set_level(spdlog::level::debug);
        
        // Initialize the global system
        auto& system = GlobalMemoryPartitioningSystem::getInstance();
        ASSERT_TRUE(system.initialize()) << "Failed to initialize global memory partitioning system";
    }
    
    void TearDown() override {
        // Shutdown the global system
        auto& system = GlobalMemoryPartitioningSystem::getInstance();
        system.shutdown();
    }
};

TEST_F(MemoryPartitioningSystemTest, TestSystemInitialization) {
    auto& system = GlobalMemoryPartitioningSystem::getInstance();
    
    EXPECT_TRUE(system.isInitialized()) << "System should be initialized";
    
    // Test component access
    auto partitioningManager = system.getPartitioningManager();
    EXPECT_NE(partitioningManager, nullptr) << "Partitioning manager should not be null";
}

TEST_F(MemoryPartitioningSystemTest, TestMemoryPartitionCreation) {
    auto& system = GlobalMemoryPartitioningSystem::getInstance();
    
    // Create memory partition configuration
    MemoryPartitionConfig config;
    config.partitionId = "test_partition_1";
    config.type = MemoryPartitionType::GLOBAL_MEMORY;
    config.size = 1024 * 1024 * 1024; // 1GB
    config.alignment = 256;
    config.offset = 0;
    config.baseAddress = nullptr;
    config.devicePtr = nullptr;
    config.hostPtr = nullptr;
    config.ownerLLM = "test_llm";
    config.priority = 0.8f;
    config.accessPattern = MemoryAccessPattern::SEQUENTIAL;
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    // Create partition
    auto partition = system.createPartition(config);
    EXPECT_NE(partition, nullptr) << "Partition should be created";
    
    if (partition) {
        EXPECT_EQ(partition->getPartitionId(), config.partitionId) << "Partition ID should match";
        EXPECT_EQ(partition->getPartitionType(), config.type) << "Partition type should match";
        EXPECT_TRUE(partition->isInitialized()) << "Partition should be initialized";
    }
}

TEST_F(MemoryPartitioningSystemTest, TestMemoryAllocation) {
    auto& system = GlobalMemoryPartitioningSystem::getInstance();
    
    // Create partition first
    MemoryPartitionConfig config;
    config.partitionId = "test_partition_2";
    config.type = MemoryPartitionType::GLOBAL_MEMORY;
    config.size = 2048 * 1024 * 1024; // 2GB
    config.alignment = 256;
    config.offset = 0;
    config.baseAddress = nullptr;
    config.devicePtr = nullptr;
    config.hostPtr = nullptr;
    config.ownerLLM = "test_llm";
    config.priority = 0.9f;
    config.accessPattern = MemoryAccessPattern::COALESCED;
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto partition = system.createPartition(config);
    ASSERT_NE(partition, nullptr) << "Partition should be created";
    
    // Allocate memory
    size_t allocationSize = 512 * 1024 * 1024; // 512MB
    bool allocated = partition->allocateMemory(allocationSize);
    EXPECT_TRUE(allocated) << "Memory allocation should succeed";
    
    if (allocated) {
        EXPECT_TRUE(partition->isMemoryAllocated()) << "Partition should have memory allocated";
        EXPECT_EQ(partition->getMemorySize(), allocationSize) << "Allocated memory size should match";
        EXPECT_EQ(partition->getAvailableMemory(), config.size - allocationSize) << "Available memory should be reduced";
    }
}

TEST_F(MemoryPartitioningSystemTest, TestMemoryOperations) {
    auto& system = GlobalMemoryPartitioningSystem::getInstance();
    
    // Create partition
    MemoryPartitionConfig config;
    config.partitionId = "test_partition_3";
    config.type = MemoryPartitionType::GLOBAL_MEMORY;
    config.size = 1024 * 1024 * 1024; // 1GB
    config.alignment = 256;
    config.offset = 0;
    config.baseAddress = nullptr;
    config.devicePtr = nullptr;
    config.hostPtr = nullptr;
    config.ownerLLM = "test_llm";
    config.priority = 0.8f;
    config.accessPattern = MemoryAccessPattern::SEQUENTIAL;
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto partition = system.createPartition(config);
    ASSERT_NE(partition, nullptr) << "Partition should be created";
    
    // Allocate memory
    size_t allocationSize = 256 * 1024 * 1024; // 256MB
    bool allocated = partition->allocateMemory(allocationSize);
    ASSERT_TRUE(allocated) << "Memory allocation should succeed";
    
    // Test memory operations
    size_t testSize = 1024; // 1KB
    size_t testOffset = 0;
    
    // Test memory write
    std::vector<int> testData(256, 42); // 256 integers with value 42
    bool written = partition->writeMemory(testData.data(), testOffset, testData.size() * sizeof(int));
    EXPECT_TRUE(written) << "Memory write should succeed";
    
    // Test memory read
    std::vector<int> readData(256);
    bool read = partition->readMemory(readData.data(), testOffset, readData.size() * sizeof(int));
    EXPECT_TRUE(read) << "Memory read should succeed";
    
    // Test memory copy
    std::vector<int> copyData(256);
    bool copied = partition->copyMemory(copyData.data(), testData.data(), testData.size() * sizeof(int));
    EXPECT_TRUE(copied) << "Memory copy should succeed";
    
    // Test memory fill
    bool filled = partition->fillMemory(0xFF, testOffset, testSize);
    EXPECT_TRUE(filled) << "Memory fill should succeed";
    
    // Test memory clear
    bool cleared = partition->clearMemory(testOffset, testSize);
    EXPECT_TRUE(cleared) << "Memory clear should succeed";
}

TEST_F(MemoryPartitioningSystemTest, TestDMATransfers) {
    auto& system = GlobalMemoryPartitioningSystem::getInstance();
    
    // Create source partition
    MemoryPartitionConfig sourceConfig;
    sourceConfig.partitionId = "source_partition";
    sourceConfig.type = MemoryPartitionType::GLOBAL_MEMORY;
    sourceConfig.size = 1024 * 1024 * 1024; // 1GB
    sourceConfig.alignment = 256;
    sourceConfig.offset = 0;
    sourceConfig.baseAddress = nullptr;
    sourceConfig.devicePtr = nullptr;
    sourceConfig.hostPtr = nullptr;
    sourceConfig.ownerLLM = "test_llm";
    sourceConfig.priority = 0.8f;
    sourceConfig.accessPattern = MemoryAccessPattern::SEQUENTIAL;
    sourceConfig.createdAt = std::chrono::system_clock::now();
    sourceConfig.lastUsed = std::chrono::system_clock::now();
    
    auto sourcePartition = system.createPartition(sourceConfig);
    ASSERT_NE(sourcePartition, nullptr) << "Source partition should be created";
    
    // Allocate memory in source partition
    size_t allocationSize = 256 * 1024 * 1024; // 256MB
    bool allocated = sourcePartition->allocateMemory(allocationSize);
    ASSERT_TRUE(allocated) << "Source partition memory allocation should succeed";
    
    // Create destination partition
    MemoryPartitionConfig destConfig;
    destConfig.partitionId = "dest_partition";
    destConfig.type = MemoryPartitionType::GLOBAL_MEMORY;
    destConfig.size = 1024 * 1024 * 1024; // 1GB
    destConfig.alignment = 256;
    destConfig.offset = 0;
    destConfig.baseAddress = nullptr;
    destConfig.devicePtr = nullptr;
    destConfig.hostPtr = nullptr;
    destConfig.ownerLLM = "test_llm";
    destConfig.priority = 0.8f;
    destConfig.accessPattern = MemoryAccessPattern::SEQUENTIAL;
    destConfig.createdAt = std::chrono::system_clock::now();
    destConfig.lastUsed = std::chrono::system_clock::now();
    
    auto destPartition = system.createPartition(destConfig);
    ASSERT_NE(destPartition, nullptr) << "Destination partition should be created";
    
    // Allocate memory in destination partition
    bool destAllocated = destPartition->allocateMemory(allocationSize);
    ASSERT_TRUE(destAllocated) << "Destination partition memory allocation should succeed";
    
    // Test synchronous DMA transfer
    DMATransferConfig transferConfig;
    transferConfig.transferId = "test_transfer_1";
    transferConfig.type = DMATransferType::DEVICE_TO_DEVICE;
    transferConfig.sourcePtr = sourcePartition->getDevicePtr();
    transferConfig.destinationPtr = destPartition->getDevicePtr();
    transferConfig.size = 1024 * 1024; // 1MB
    transferConfig.stream = nullptr;
    transferConfig.ownerLLM = "test_llm";
    transferConfig.priority = 0.7f;
    transferConfig.timeout = std::chrono::milliseconds(5000);
    
    bool transferred = system.dmaTransfer(transferConfig);
    EXPECT_TRUE(transferred) << "DMA transfer should succeed";
    
    // Test asynchronous DMA transfer
    transferConfig.transferId = "test_transfer_2";
    bool asyncTransferred = system.dmaTransferAsync(transferConfig);
    EXPECT_TRUE(asyncTransferred) << "Async DMA transfer should succeed";
    
    // Wait for async transfer to complete
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
}

TEST_F(MemoryPartitioningSystemTest, TestPerformanceMonitoring) {
    auto& system = GlobalMemoryPartitioningSystem::getInstance();
    
    // Create partition
    MemoryPartitionConfig config;
    config.partitionId = "test_partition_4";
    config.type = MemoryPartitionType::GLOBAL_MEMORY;
    config.size = 1024 * 1024 * 1024; // 1GB
    config.alignment = 256;
    config.offset = 0;
    config.baseAddress = nullptr;
    config.devicePtr = nullptr;
    config.hostPtr = nullptr;
    config.ownerLLM = "test_llm";
    config.priority = 0.8f;
    config.accessPattern = MemoryAccessPattern::SEQUENTIAL;
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto partition = system.createPartition(config);
    ASSERT_NE(partition, nullptr) << "Partition should be created";
    
    // Allocate memory
    size_t allocationSize = 512 * 1024 * 1024; // 512MB
    bool allocated = partition->allocateMemory(allocationSize);
    ASSERT_TRUE(allocated) << "Memory allocation should succeed";
    
    // Enable profiling
    EXPECT_TRUE(partition->enableProfiling()) << "Profiling should be enabled";
    
    // Get performance metrics
    auto metrics = partition->getPerformanceMetrics();
    EXPECT_FALSE(metrics.empty()) << "Performance metrics should not be empty";
    EXPECT_GT(metrics["utilization"], 0.0) << "Utilization should be positive";
    EXPECT_GT(metrics["memory_usage"], 0.0) << "Memory usage should be positive";
    
    // Get profiling data
    auto profilingData = partition->getProfilingData();
    EXPECT_FALSE(profilingData.empty()) << "Profiling data should not be empty";
    EXPECT_GT(profilingData["utilization"], 0.0) << "Profiling utilization should be positive";
    EXPECT_GT(profilingData["allocated_size"], 0.0) << "Allocated size should be positive";
    EXPECT_GT(profilingData["available_memory"], 0.0) << "Available memory should be positive";
    
    // Get utilization
    float utilization = partition->getUtilization();
    EXPECT_GT(utilization, 0.0f) << "Utilization should be positive";
    EXPECT_LE(utilization, 1.0f) << "Utilization should not exceed 1.0";
    
    // Disable profiling
    EXPECT_TRUE(partition->disableProfiling()) << "Profiling should be disabled";
}

TEST_F(MemoryPartitioningSystemTest, TestPartitionManagement) {
    auto& system = GlobalMemoryPartitioningSystem::getInstance();
    auto partitioningManager = system.getPartitioningManager();
    
    ASSERT_NE(partitioningManager, nullptr) << "Partitioning manager should not be null";
    
    // Create multiple partitions
    std::vector<std::string> partitionIds;
    for (int i = 0; i < 5; ++i) {
        MemoryPartitionConfig config;
        config.partitionId = "test_partition_" + std::to_string(i + 10);
        config.type = static_cast<MemoryPartitionType>(i % 6);
        config.size = 1024 * 1024 * 1024; // 1GB
        config.alignment = 256;
        config.offset = 0;
        config.baseAddress = nullptr;
        config.devicePtr = nullptr;
        config.hostPtr = nullptr;
        config.ownerLLM = "test_llm_" + std::to_string(i);
        config.priority = 0.5f + (i * 0.1f);
        config.accessPattern = static_cast<MemoryAccessPattern>(i % 6);
        config.createdAt = std::chrono::system_clock::now();
        config.lastUsed = std::chrono::system_clock::now();
        
        auto partition = system.createPartition(config);
        ASSERT_NE(partition, nullptr) << "Partition " << i << " should be created";
        partitionIds.push_back(config.partitionId);
    }
    
    // Test partition retrieval
    for (const auto& partitionId : partitionIds) {
        auto partition = system.getPartition(partitionId);
        EXPECT_NE(partition, nullptr) << "Partition " << partitionId << " should be retrievable";
    }
    
    // Test getting all partitions
    auto allPartitions = system.getAllPartitions();
    EXPECT_GE(allPartitions.size(), 5) << "Should have at least 5 partitions";
    
    // Test partition management operations
    auto partition = system.getPartition(partitionIds[0]);
    ASSERT_NE(partition, nullptr) << "Partition should be retrievable";
    
    // Test partition configuration update
    auto config = partition->getConfig();
    config.priority = 0.9f;
    EXPECT_TRUE(partition->updateConfig(config)) << "Config update should succeed";
    EXPECT_EQ(partition->getPriority(), 0.9f) << "Priority should be updated";
    
    // Test partition priority setting
    EXPECT_TRUE(partition->setPriority(0.7f)) << "Priority setting should succeed";
    EXPECT_EQ(partition->getPriority(), 0.7f) << "Priority should be set";
    
    // Test access pattern setting
    EXPECT_TRUE(partition->setAccessPattern(MemoryAccessPattern::COALESCED)) << "Access pattern setting should succeed";
    EXPECT_EQ(partition->getAccessPattern(), MemoryAccessPattern::COALESCED) << "Access pattern should be set";
}

TEST_F(MemoryPartitioningSystemTest, TestAdvancedPartitionFeatures) {
    auto& system = GlobalMemoryPartitioningSystem::getInstance();
    
    // Create partition
    MemoryPartitionConfig config;
    config.partitionId = "test_partition_5";
    config.type = MemoryPartitionType::GLOBAL_MEMORY;
    config.size = 2048 * 1024 * 1024; // 2GB
    config.alignment = 256;
    config.offset = 0;
    config.baseAddress = nullptr;
    config.devicePtr = nullptr;
    config.hostPtr = nullptr;
    config.ownerLLM = "test_llm";
    config.priority = 0.8f;
    config.accessPattern = MemoryAccessPattern::SEQUENTIAL;
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto partition = system.createPartition(config);
    ASSERT_NE(partition, nullptr) << "Partition should be created";
    
    // Cast to advanced partition
    auto advancedPartition = std::dynamic_pointer_cast<AdvancedMemoryPartition>(partition);
    ASSERT_NE(advancedPartition, nullptr) << "Partition should be an advanced partition";
    
    // Allocate memory
    size_t allocationSize = 1024 * 1024 * 1024; // 1GB
    bool allocated = advancedPartition->allocateMemory(allocationSize);
    ASSERT_TRUE(allocated) << "Memory allocation should succeed";
    
    // Test advanced features
    EXPECT_TRUE(advancedPartition->optimizeMemoryLayout()) << "Memory layout optimization should succeed";
    EXPECT_TRUE(advancedPartition->prefetchMemory(0, 1024 * 1024)) << "Memory prefetch should succeed";
    EXPECT_TRUE(advancedPartition->invalidateCache(0, 1024 * 1024)) << "Cache invalidation should succeed";
    EXPECT_TRUE(advancedPartition->flushCache(0, 1024 * 1024)) << "Cache flush should succeed";
    EXPECT_TRUE(advancedPartition->setMemoryProtection(0, 1024 * 1024, true)) << "Memory protection should succeed";
    
    // Test memory info
    std::map<std::string, std::string> memoryInfo;
    EXPECT_TRUE(advancedPartition->getMemoryInfo(memoryInfo)) << "Memory info should be retrieved";
    EXPECT_FALSE(memoryInfo.empty()) << "Memory info should not be empty";
    EXPECT_EQ(memoryInfo["partition_id"], config.partitionId) << "Partition ID should match";
    
    // Test memory validation
    EXPECT_TRUE(advancedPartition->validateMemoryIntegrity(0, 1024 * 1024)) << "Memory integrity validation should pass";
    
    // Test memory compression/decompression
    EXPECT_TRUE(advancedPartition->compressMemory(0, 1024 * 1024)) << "Memory compression should succeed";
    EXPECT_TRUE(advancedPartition->decompressMemory(0, 1024 * 1024)) << "Memory decompression should succeed";
}

TEST_F(MemoryPartitioningSystemTest, TestSystemManagement) {
    auto& system = GlobalMemoryPartitioningSystem::getInstance();
    auto partitioningManager = system.getPartitioningManager();
    
    ASSERT_NE(partitioningManager, nullptr) << "Partitioning manager should not be null";
    
    // Test system optimization
    EXPECT_TRUE(partitioningManager->optimizeMemoryLayout()) << "Memory layout optimization should succeed";
    
    // Test memory balancing
    EXPECT_TRUE(partitioningManager->balanceMemoryUsage()) << "Memory usage balancing should succeed";
    
    // Test system validation
    EXPECT_TRUE(partitioningManager->validateSystem()) << "System validation should pass";
    
    // Test system metrics
    auto systemMetrics = system.getSystemMetrics();
    EXPECT_FALSE(systemMetrics.empty()) << "System metrics should not be empty";
    EXPECT_GT(systemMetrics["total_partitions"], 0.0) << "Total partitions should be positive";
    EXPECT_GT(systemMetrics["total_memory"], 0.0) << "Total memory should be positive";
    
    // Test partition counts
    auto partitionCounts = partitioningManager->getPartitionCounts();
    EXPECT_FALSE(partitionCounts.empty()) << "Partition counts should not be empty";
    EXPECT_GT(partitionCounts["total"], 0) << "Total partition count should be positive";
    
    // Test memory utilization
    auto utilization = partitioningManager->getMemoryUtilization();
    EXPECT_FALSE(utilization.empty()) << "Memory utilization should not be empty";
    EXPECT_GE(utilization["global_memory"], 0.0) << "Global memory utilization should be non-negative";
    EXPECT_GE(utilization["shared_memory"], 0.0) << "Shared memory utilization should be non-negative";
    EXPECT_GE(utilization["constant_memory"], 0.0) << "Constant memory utilization should be non-negative";
}

TEST_F(MemoryPartitioningSystemTest, TestSystemProfiling) {
    auto& system = GlobalMemoryPartitioningSystem::getInstance();
    auto partitioningManager = system.getPartitioningManager();
    
    ASSERT_NE(partitioningManager, nullptr) << "Partitioning manager should not be null";
    
    // Enable system profiling
    EXPECT_TRUE(partitioningManager->enableSystemProfiling()) << "System profiling should be enabled";
    
    // Get system profiling data
    auto profilingData = partitioningManager->getSystemProfilingData();
    EXPECT_FALSE(profilingData.empty()) << "System profiling data should not be empty";
    EXPECT_GT(profilingData["total_partitions"], 0.0) << "Total partitions should be positive";
    EXPECT_GT(profilingData["total_memory"], 0.0) << "Total memory should be positive";
    EXPECT_EQ(profilingData["profiling_enabled"], 1.0) << "Profiling should be enabled";
    
    // Disable system profiling
    EXPECT_TRUE(partitioningManager->disableSystemProfiling()) << "System profiling should be disabled";
}

TEST_F(MemoryPartitioningSystemTest, TestSystemConfiguration) {
    auto& system = GlobalMemoryPartitioningSystem::getInstance();
    
    // Test system configuration
    std::map<std::string, std::string> config = {
        {"max_global_memory", "34359738368"}, // 32GB
        {"max_shared_memory", "98304"}, // 96KB
        {"max_constant_memory", "131072"}, // 128KB
        {"dma_policy", "optimized"},
        {"memory_alignment", "512"},
        {"auto_cleanup", "enabled"},
        {"memory_optimization", "enabled"},
        {"profiling", "enabled"}
    };
    
    system.setSystemConfiguration(config);
    
    auto retrievedConfig = system.getSystemConfiguration();
    EXPECT_EQ(retrievedConfig.size(), config.size()) << "Configuration size should match";
    
    for (const auto& item : config) {
        EXPECT_EQ(retrievedConfig[item.first], item.second) 
            << "Configuration item " << item.first << " should match";
    }
}

TEST_F(MemoryPartitioningSystemTest, TestMemoryDeallocation) {
    auto& system = GlobalMemoryPartitioningSystem::getInstance();
    
    // Create partition
    MemoryPartitionConfig config;
    config.partitionId = "test_partition_6";
    config.type = MemoryPartitionType::GLOBAL_MEMORY;
    config.size = 1024 * 1024 * 1024; // 1GB
    config.alignment = 256;
    config.offset = 0;
    config.baseAddress = nullptr;
    config.devicePtr = nullptr;
    config.hostPtr = nullptr;
    config.ownerLLM = "test_llm";
    config.priority = 0.8f;
    config.accessPattern = MemoryAccessPattern::SEQUENTIAL;
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto partition = system.createPartition(config);
    ASSERT_NE(partition, nullptr) << "Partition should be created";
    
    // Allocate memory
    size_t allocationSize = 512 * 1024 * 1024; // 512MB
    bool allocated = partition->allocateMemory(allocationSize);
    ASSERT_TRUE(allocated) << "Memory allocation should succeed";
    EXPECT_TRUE(partition->isMemoryAllocated()) << "Partition should have memory allocated";
    
    // Deallocate memory
    bool deallocated = partition->deallocateMemory();
    EXPECT_TRUE(deallocated) << "Memory deallocation should succeed";
    EXPECT_FALSE(partition->isMemoryAllocated()) << "Partition should not have memory allocated";
    
    // Verify available memory is restored
    EXPECT_EQ(partition->getAvailableMemory(), config.size) << "Available memory should be restored";
}

TEST_F(MemoryPartitioningSystemTest, TestPartitionDestruction) {
    auto& system = GlobalMemoryPartitioningSystem::getInstance();
    
    // Create partition
    MemoryPartitionConfig config;
    config.partitionId = "test_partition_7";
    config.type = MemoryPartitionType::GLOBAL_MEMORY;
    config.size = 1024 * 1024 * 1024; // 1GB
    config.alignment = 256;
    config.offset = 0;
    config.baseAddress = nullptr;
    config.devicePtr = nullptr;
    config.hostPtr = nullptr;
    config.ownerLLM = "test_llm";
    config.priority = 0.8f;
    config.accessPattern = MemoryAccessPattern::SEQUENTIAL;
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto partition = system.createPartition(config);
    ASSERT_NE(partition, nullptr) << "Partition should be created";
    
    // Verify partition exists
    auto retrievedPartition = system.getPartition(config.partitionId);
    EXPECT_NE(retrievedPartition, nullptr) << "Partition should be retrievable";
    
    // Destroy partition
    bool destroyed = system.destroyPartition(config.partitionId);
    EXPECT_TRUE(destroyed) << "Partition destruction should succeed";
    
    // Verify partition no longer exists
    auto destroyedPartition = system.getPartition(config.partitionId);
    EXPECT_EQ(destroyedPartition, nullptr) << "Destroyed partition should not be retrievable";
}

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    
    // Set up logging
    spdlog::set_level(spdlog::level::info);
    
    return RUN_ALL_TESTS();
}
