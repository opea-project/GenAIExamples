#include <gtest/gtest.h>
#include <spdlog/spdlog.h>
#include "cuda/cuda_stream_management.h"
#include <chrono>
#include <thread>

using namespace cogniware::cuda;

class CUDAStreamManagementSystemTest : public ::testing::Test {
protected:
    void SetUp() override {
        spdlog::set_level(spdlog::level::debug);
        
        // Initialize the global system
        auto& system = GlobalCUDAStreamManagementSystem::getInstance();
        ASSERT_TRUE(system.initialize()) << "Failed to initialize global CUDA stream management system";
    }
    
    void TearDown() override {
        // Shutdown the global system
        auto& system = GlobalCUDAStreamManagementSystem::getInstance();
        system.shutdown();
    }
};

TEST_F(CUDAStreamManagementSystemTest, TestSystemInitialization) {
    auto& system = GlobalCUDAStreamManagementSystem::getInstance();
    
    EXPECT_TRUE(system.isInitialized()) << "System should be initialized";
    
    // Test component access
    auto streamManager = system.getStreamManager();
    EXPECT_NE(streamManager, nullptr) << "Stream manager should not be null";
}

TEST_F(CUDAStreamManagementSystemTest, TestStreamCreation) {
    auto& system = GlobalCUDAStreamManagementSystem::getInstance();
    
    // Create CUDA stream configuration
    CUDAStreamConfig config;
    config.streamId = "cuda_stream_1";
    config.type = CUDAStreamType::COMPUTE_STREAM;
    config.priority = CUDAStreamPriority::NORMAL;
    config.deviceId = 0;
    config.isNonBlocking = true;
    config.enableProfiling = true;
    config.enableSynchronization = true;
    config.maxConcurrentKernels = 4;
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    // Create stream
    auto stream = system.createStream(config);
    EXPECT_NE(stream, nullptr) << "Stream should be created";
    
    if (stream) {
        EXPECT_EQ(stream->getStreamId(), config.streamId) << "Stream ID should match";
        EXPECT_TRUE(stream->isInitialized()) << "Stream should be initialized";
        EXPECT_EQ(stream->getType(), config.type) << "Stream type should match";
        EXPECT_EQ(stream->getPriority(), config.priority) << "Stream priority should match";
    }
}

TEST_F(CUDAStreamManagementSystemTest, TestTaskExecution) {
    auto& system = GlobalCUDAStreamManagementSystem::getInstance();
    
    // Create stream first
    CUDAStreamConfig config;
    config.streamId = "cuda_stream_2";
    config.type = CUDAStreamType::COMPUTE_STREAM;
    config.priority = CUDAStreamPriority::NORMAL;
    config.deviceId = 0;
    config.isNonBlocking = true;
    config.enableProfiling = true;
    config.enableSynchronization = true;
    config.maxConcurrentKernels = 4;
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto stream = system.createStream(config);
    ASSERT_NE(stream, nullptr) << "Stream should be created";
    
    // Create task
    CUDAStreamTask task;
    task.taskId = "task_1";
    task.streamId = config.streamId;
    task.kernelFunction = []() { /* Simulate kernel execution */ };
    task.inputPointers = {malloc(1024)};
    task.outputPointers = {malloc(1024)};
    task.inputSizes = {1024};
    task.outputSizes = {1024};
    task.gridDim = dim3(1, 1, 1);
    task.blockDim = dim3(1, 1, 1);
    task.sharedMemSize = 0;
    task.priority = CUDAStreamPriority::NORMAL;
    task.timeout = std::chrono::milliseconds(5000);
    task.createdAt = std::chrono::system_clock::now();
    
    // Execute task
    auto result = system.executeTask(task);
    EXPECT_TRUE(result.success) << "Task execution should succeed";
    EXPECT_EQ(result.taskId, task.taskId) << "Task ID should match";
    EXPECT_EQ(result.streamId, task.streamId) << "Stream ID should match";
    EXPECT_GT(result.executionTime, 0.0f) << "Execution time should be positive";
    EXPECT_GE(result.memoryBandwidth, 0.0f) << "Memory bandwidth should be non-negative";
    EXPECT_GE(result.computeThroughput, 0.0f) << "Compute throughput should be non-negative";
    
    // Cleanup
    free(task.inputPointers[0]);
    free(task.outputPointers[0]);
}

TEST_F(CUDAStreamManagementSystemTest, TestAsyncTaskExecution) {
    auto& system = GlobalCUDAStreamManagementSystem::getInstance();
    
    // Create stream first
    CUDAStreamConfig config;
    config.streamId = "cuda_stream_3";
    config.type = CUDAStreamType::COMPUTE_STREAM;
    config.priority = CUDAStreamPriority::NORMAL;
    config.deviceId = 0;
    config.isNonBlocking = true;
    config.enableProfiling = true;
    config.enableSynchronization = true;
    config.maxConcurrentKernels = 4;
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto stream = system.createStream(config);
    ASSERT_NE(stream, nullptr) << "Stream should be created";
    
    // Create task
    CUDAStreamTask task;
    task.taskId = "task_2";
    task.streamId = config.streamId;
    task.kernelFunction = []() { /* Simulate kernel execution */ };
    task.inputPointers = {malloc(1024)};
    task.outputPointers = {malloc(1024)};
    task.inputSizes = {1024};
    task.outputSizes = {1024};
    task.gridDim = dim3(1, 1, 1);
    task.blockDim = dim3(1, 1, 1);
    task.sharedMemSize = 0;
    task.priority = CUDAStreamPriority::NORMAL;
    task.timeout = std::chrono::milliseconds(5000);
    task.createdAt = std::chrono::system_clock::now();
    
    // Execute async task
    auto future = system.executeTaskAsync(task);
    EXPECT_TRUE(future.valid()) << "Future should be valid";
    
    // Wait for completion
    auto result = future.get();
    EXPECT_TRUE(result.success) << "Async task execution should succeed";
    EXPECT_EQ(result.taskId, task.taskId) << "Task ID should match";
    EXPECT_EQ(result.streamId, task.streamId) << "Stream ID should match";
    EXPECT_GT(result.executionTime, 0.0f) << "Execution time should be positive";
    EXPECT_GE(result.memoryBandwidth, 0.0f) << "Memory bandwidth should be non-negative";
    EXPECT_GE(result.computeThroughput, 0.0f) << "Compute throughput should be non-negative";
    
    // Cleanup
    free(task.inputPointers[0]);
    free(task.outputPointers[0]);
}

TEST_F(CUDAStreamManagementSystemTest, TestStreamManagement) {
    auto& system = GlobalCUDAStreamManagementSystem::getInstance();
    
    // Create multiple streams
    std::vector<std::string> streamIds;
    for (int i = 0; i < 4; ++i) {
        CUDAStreamConfig config;
        config.streamId = "cuda_stream_" + std::to_string(i + 4);
        config.type = CUDAStreamType::COMPUTE_STREAM;
        config.priority = CUDAStreamPriority::NORMAL;
        config.deviceId = 0;
        config.isNonBlocking = true;
        config.enableProfiling = true;
        config.enableSynchronization = true;
        config.maxConcurrentKernels = 4;
        config.createdAt = std::chrono::system_clock::now();
        config.lastUsed = std::chrono::system_clock::now();
        
        auto stream = system.createStream(config);
        ASSERT_NE(stream, nullptr) << "Stream " << i << " should be created";
        streamIds.push_back(config.streamId);
    }
    
    // Test stream retrieval
    for (const auto& streamId : streamIds) {
        auto stream = system.getStream(streamId);
        EXPECT_NE(stream, nullptr) << "Stream " << streamId << " should be retrievable";
        EXPECT_EQ(stream->getStreamId(), streamId) << "Stream ID should match";
    }
    
    // Test getting all streams
    auto allStreams = system.getAllStreams();
    EXPECT_GE(allStreams.size(), 4) << "Should have at least 4 streams";
    
    // Test stream destruction
    for (const auto& streamId : streamIds) {
        bool destroyed = system.destroyStream(streamId);
        EXPECT_TRUE(destroyed) << "Stream " << streamId << " should be destroyed";
    }
}

TEST_F(CUDAStreamManagementSystemTest, TestMemoryBarriers) {
    auto& system = GlobalCUDAStreamManagementSystem::getInstance();
    
    // Create stream first
    CUDAStreamConfig config;
    config.streamId = "cuda_stream_8";
    config.type = CUDAStreamType::MEMORY_STREAM;
    config.priority = CUDAStreamPriority::NORMAL;
    config.deviceId = 0;
    config.isNonBlocking = true;
    config.enableProfiling = true;
    config.enableSynchronization = true;
    config.maxConcurrentKernels = 4;
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto stream = system.createStream(config);
    ASSERT_NE(stream, nullptr) << "Stream should be created";
    
    // Create memory barrier
    CUDAMemoryBarrier barrier;
    barrier.barrierId = "barrier_1";
    barrier.type = CUDAMemoryBarrierType::GLOBAL_BARRIER;
    barrier.memoryPointers = {malloc(1024)};
    barrier.memorySizes = {1024};
    barrier.isActive = true;
    barrier.createdAt = std::chrono::system_clock::now();
    
    // Create barrier
    std::string barrierId = stream->createMemoryBarrier(barrier);
    EXPECT_FALSE(barrierId.empty()) << "Barrier ID should not be empty";
    
    // Test barrier operations
    EXPECT_TRUE(stream->isBarrierActive(barrierId)) << "Barrier should be active";
    
    // Synchronize barrier
    bool synchronized = stream->synchronizeMemoryBarrier(barrierId);
    EXPECT_TRUE(synchronized) << "Barrier synchronization should succeed";
    
    // Get active barriers
    auto activeBarriers = stream->getActiveBarriers();
    EXPECT_FALSE(activeBarriers.empty()) << "Should have active barriers";
    
    // Destroy barrier
    bool destroyed = stream->destroyMemoryBarrier(barrierId);
    EXPECT_TRUE(destroyed) << "Barrier should be destroyed";
    
    // Cleanup
    free(barrier.memoryPointers[0]);
}

TEST_F(CUDAStreamManagementSystemTest, TestPerformanceMonitoring) {
    auto& system = GlobalCUDAStreamManagementSystem::getInstance();
    
    // Create stream first
    CUDAStreamConfig config;
    config.streamId = "cuda_stream_9";
    config.type = CUDAStreamType::COMPUTE_STREAM;
    config.priority = CUDAStreamPriority::NORMAL;
    config.deviceId = 0;
    config.isNonBlocking = true;
    config.enableProfiling = true;
    config.enableSynchronization = true;
    config.maxConcurrentKernels = 4;
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto stream = system.createStream(config);
    ASSERT_NE(stream, nullptr) << "Stream should be created";
    
    // Enable profiling
    EXPECT_TRUE(stream->enableProfiling()) << "Profiling should be enabled";
    
    // Get performance metrics
    auto metrics = stream->getPerformanceMetrics();
    EXPECT_FALSE(metrics.empty()) << "Performance metrics should not be empty";
    EXPECT_GE(metrics["utilization"], 0.0) << "Utilization should be non-negative";
    EXPECT_GE(metrics["execution_time"], 0.0) << "Execution time should be non-negative";
    EXPECT_GE(metrics["memory_bandwidth"], 0.0) << "Memory bandwidth should be non-negative";
    EXPECT_GE(metrics["compute_throughput"], 0.0) << "Compute throughput should be non-negative";
    EXPECT_GE(metrics["task_count"], 0.0) << "Task count should be non-negative";
    EXPECT_GE(metrics["error_count"], 0.0) << "Error count should be non-negative";
    
    // Get profiling data
    auto profilingData = stream->getProfilingData();
    EXPECT_FALSE(profilingData.empty()) << "Profiling data should not be empty";
    EXPECT_GE(profilingData["utilization"], 0.0) << "Profiling utilization should be non-negative";
    EXPECT_GE(profilingData["execution_time"], 0.0) << "Profiling execution time should be non-negative";
    EXPECT_GE(profilingData["memory_bandwidth"], 0.0) << "Profiling memory bandwidth should be non-negative";
    EXPECT_GE(profilingData["compute_throughput"], 0.0) << "Profiling compute throughput should be non-negative";
    EXPECT_GE(profilingData["task_count"], 0.0) << "Profiling task count should be non-negative";
    EXPECT_GE(profilingData["error_count"], 0.0) << "Profiling error count should be non-negative";
    EXPECT_GE(profilingData["active_tasks"], 0.0) << "Active tasks should be non-negative";
    EXPECT_GE(profilingData["active_barriers"], 0.0) << "Active barriers should be non-negative";
    EXPECT_GE(profilingData["device_id"], 0.0) << "Device ID should be non-negative";
    EXPECT_GE(profilingData["priority"], 0.0) << "Priority should be non-negative";
    EXPECT_GE(profilingData["stream_type"], 0.0) << "Stream type should be non-negative";
    
    // Get utilization
    float utilization = stream->getUtilization();
    EXPECT_GE(utilization, 0.0f) << "Utilization should be non-negative";
    EXPECT_LE(utilization, 1.0f) << "Utilization should not exceed 1.0";
    
    // Disable profiling
    EXPECT_TRUE(stream->disableProfiling()) << "Profiling should be disabled";
}

TEST_F(CUDAStreamManagementSystemTest, TestSystemMetrics) {
    auto& system = GlobalCUDAStreamManagementSystem::getInstance();
    
    // Get system metrics
    auto metrics = system.getSystemMetrics();
    EXPECT_FALSE(metrics.empty()) << "System metrics should not be empty";
    EXPECT_GT(metrics["total_streams"], 0.0) << "Total streams should be positive";
    EXPECT_GE(metrics["active_tasks"], 0.0) << "Active tasks should be non-negative";
    EXPECT_GE(metrics["average_utilization"], 0.0) << "Average utilization should be non-negative";
    EXPECT_EQ(metrics["system_initialized"], 1.0) << "System should be initialized";
    EXPECT_GT(metrics["configuration_items"], 0.0) << "Configuration items should be positive";
}

TEST_F(CUDAStreamManagementSystemTest, TestSystemConfiguration) {
    auto& system = GlobalCUDAStreamManagementSystem::getInstance();
    
    // Test system configuration
    std::map<std::string, std::string> config = {
        {"max_streams", "20"},
        {"scheduling_strategy", "optimized"},
        {"load_balancing_strategy", "least_loaded"},
        {"auto_cleanup", "enabled"},
        {"system_optimization", "enabled"},
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

TEST_F(CUDAStreamManagementSystemTest, TestAdvancedStreamFeatures) {
    auto& system = GlobalCUDAStreamManagementSystem::getInstance();
    
    // Create stream first
    CUDAStreamConfig config;
    config.streamId = "cuda_stream_10";
    config.type = CUDAStreamType::COMPUTE_STREAM;
    config.priority = CUDAStreamPriority::NORMAL;
    config.deviceId = 0;
    config.isNonBlocking = true;
    config.enableProfiling = true;
    config.enableSynchronization = true;
    config.maxConcurrentKernels = 4;
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto stream = system.createStream(config);
    ASSERT_NE(stream, nullptr) << "Stream should be created";
    
    // Cast to advanced stream
    auto advancedStream = std::dynamic_pointer_cast<AdvancedCUDAStream>(stream);
    ASSERT_NE(advancedStream, nullptr) << "Stream should be an advanced stream";
    
    // Test advanced features
    EXPECT_TRUE(advancedStream->synchronize()) << "Stream synchronization should succeed";
    EXPECT_TRUE(advancedStream->waitForCompletion()) << "Wait for completion should succeed";
    EXPECT_TRUE(advancedStream->pause()) << "Stream pause should succeed";
    EXPECT_TRUE(advancedStream->resume()) << "Stream resume should succeed";
    EXPECT_TRUE(advancedStream->optimize()) << "Stream optimization should succeed";
    
    // Test resource info
    auto resourceInfo = advancedStream->getResourceInfo();
    EXPECT_FALSE(resourceInfo.empty()) << "Resource info should not be empty";
    EXPECT_EQ(resourceInfo["stream_id"], config.streamId) << "Stream ID should match";
    EXPECT_EQ(resourceInfo["device_id"], std::to_string(config.deviceId)) << "Device ID should match";
    
    // Test resource validation
    EXPECT_TRUE(advancedStream->validateResources()) << "Resource validation should succeed";
    
    // Test configuration
    EXPECT_TRUE(advancedStream->setMaxConcurrentKernels(8)) << "Max concurrent kernels setting should succeed";
    EXPECT_EQ(advancedStream->getMaxConcurrentKernels(), 8) << "Max concurrent kernels should match";
    EXPECT_TRUE(advancedStream->setDevice(0)) << "Device setting should succeed";
    EXPECT_EQ(advancedStream->getDevice(), 0) << "Device should match";
}

TEST_F(CUDAStreamManagementSystemTest, TestStreamManagerFeatures) {
    auto& system = GlobalCUDAStreamManagementSystem::getInstance();
    
    auto streamManager = system.getStreamManager();
    ASSERT_NE(streamManager, nullptr) << "Stream manager should not be null";
    
    // Test stream manager operations
    EXPECT_TRUE(streamManager->optimizeSystem()) << "System optimization should succeed";
    EXPECT_TRUE(streamManager->balanceLoad()) << "Load balancing should succeed";
    EXPECT_TRUE(streamManager->cleanupIdleStreams()) << "Idle stream cleanup should succeed";
    EXPECT_TRUE(streamManager->validateSystem()) << "System validation should succeed";
    
    // Test system metrics
    auto systemMetrics = streamManager->getSystemMetrics();
    EXPECT_FALSE(systemMetrics.empty()) << "System metrics should not be empty";
    EXPECT_GT(systemMetrics["total_streams"], 0.0) << "Total streams should be positive";
    
    // Test stream counts
    auto streamCounts = streamManager->getStreamCounts();
    EXPECT_FALSE(streamCounts.empty()) << "Stream counts should not be empty";
    EXPECT_GT(streamCounts["total"], 0) << "Total stream count should be positive";
    
    // Test task metrics
    auto taskMetrics = streamManager->getTaskMetrics();
    EXPECT_FALSE(taskMetrics.empty()) << "Task metrics should not be empty";
    EXPECT_GE(taskMetrics["total_tasks"], 0.0) << "Total tasks should be non-negative";
    EXPECT_GE(taskMetrics["active_tasks"], 0.0) << "Active tasks should be non-negative";
    
    // Test system profiling
    EXPECT_TRUE(streamManager->enableSystemProfiling()) << "System profiling should be enabled";
    auto profilingData = streamManager->getSystemProfilingData();
    EXPECT_FALSE(profilingData.empty()) << "System profiling data should not be empty";
    EXPECT_TRUE(streamManager->disableSystemProfiling()) << "System profiling should be disabled";
}

TEST_F(CUDAStreamManagementSystemTest, TestStreamTypes) {
    auto& system = GlobalCUDAStreamManagementSystem::getInstance();
    
    // Test different stream types
    std::vector<CUDAStreamType> types = {
        CUDAStreamType::COMPUTE_STREAM,
        CUDAStreamType::MEMORY_STREAM,
        CUDAStreamType::KERNEL_STREAM,
        CUDAStreamType::COMMUNICATION_STREAM,
        CUDAStreamType::CUSTOM_STREAM
    };
    
    for (const auto& type : types) {
        CUDAStreamConfig config;
        config.streamId = "stream_type_test_" + std::to_string(static_cast<int>(type));
        config.type = type;
        config.priority = CUDAStreamPriority::NORMAL;
        config.deviceId = 0;
        config.isNonBlocking = true;
        config.enableProfiling = true;
        config.enableSynchronization = true;
        config.maxConcurrentKernels = 4;
        config.createdAt = std::chrono::system_clock::now();
        config.lastUsed = std::chrono::system_clock::now();
        
        auto stream = system.createStream(config);
        EXPECT_NE(stream, nullptr) << "Stream for type " << static_cast<int>(type) << " should be created";
        
        if (stream) {
            EXPECT_EQ(stream->getType(), type) << "Stream type should match";
        }
    }
}

TEST_F(CUDAStreamManagementSystemTest, TestStreamPriorities) {
    auto& system = GlobalCUDAStreamManagementSystem::getInstance();
    
    // Test different stream priorities
    std::vector<CUDAStreamPriority> priorities = {
        CUDAStreamPriority::LOW,
        CUDAStreamPriority::NORMAL,
        CUDAStreamPriority::HIGH,
        CUDAStreamPriority::CRITICAL
    };
    
    for (const auto& priority : priorities) {
        CUDAStreamConfig config;
        config.streamId = "stream_priority_test_" + std::to_string(static_cast<int>(priority));
        config.type = CUDAStreamType::COMPUTE_STREAM;
        config.priority = priority;
        config.deviceId = 0;
        config.isNonBlocking = true;
        config.enableProfiling = true;
        config.enableSynchronization = true;
        config.maxConcurrentKernels = 4;
        config.createdAt = std::chrono::system_clock::now();
        config.lastUsed = std::chrono::system_clock::now();
        
        auto stream = system.createStream(config);
        EXPECT_NE(stream, nullptr) << "Stream for priority " << static_cast<int>(priority) << " should be created";
        
        if (stream) {
            EXPECT_EQ(stream->getPriority(), priority) << "Stream priority should match";
        }
    }
}

TEST_F(CUDAStreamManagementSystemTest, TestMemoryBarrierTypes) {
    auto& system = GlobalCUDAStreamManagementSystem::getInstance();
    
    // Create stream first
    CUDAStreamConfig config;
    config.streamId = "cuda_stream_11";
    config.type = CUDAStreamType::MEMORY_STREAM;
    config.priority = CUDAStreamPriority::NORMAL;
    config.deviceId = 0;
    config.isNonBlocking = true;
    config.enableProfiling = true;
    config.enableSynchronization = true;
    config.maxConcurrentKernels = 4;
    config.createdAt = std::chrono::system_clock::now();
    config.lastUsed = std::chrono::system_clock::now();
    
    auto stream = system.createStream(config);
    ASSERT_NE(stream, nullptr) << "Stream should be created";
    
    // Test different memory barrier types
    std::vector<CUDAMemoryBarrierType> barrierTypes = {
        CUDAMemoryBarrierType::GLOBAL_BARRIER,
        CUDAMemoryBarrierType::SHARED_BARRIER,
        CUDAMemoryBarrierType::CONSTANT_BARRIER,
        CUDAMemoryBarrierType::TEXTURE_BARRIER,
        CUDAMemoryBarrierType::SURFACE_BARRIER,
        CUDAMemoryBarrierType::CUSTOM_BARRIER
    };
    
    for (const auto& barrierType : barrierTypes) {
        CUDAMemoryBarrier barrier;
        barrier.barrierId = "barrier_type_test_" + std::to_string(static_cast<int>(barrierType));
        barrier.type = barrierType;
        barrier.memoryPointers = {malloc(1024)};
        barrier.memorySizes = {1024};
        barrier.isActive = true;
        barrier.createdAt = std::chrono::system_clock::now();
        
        std::string barrierId = stream->createMemoryBarrier(barrier);
        EXPECT_FALSE(barrierId.empty()) << "Barrier for type " << static_cast<int>(barrierType) << " should be created";
        
        if (!barrierId.empty()) {
            EXPECT_TRUE(stream->isBarrierActive(barrierId)) << "Barrier should be active";
            EXPECT_TRUE(stream->synchronizeMemoryBarrier(barrierId)) << "Barrier synchronization should succeed";
            EXPECT_TRUE(stream->destroyMemoryBarrier(barrierId)) << "Barrier should be destroyed";
        }
        
        // Cleanup
        free(barrier.memoryPointers[0]);
    }
}

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    
    // Set up logging
    spdlog::set_level(spdlog::level::info);
    
    return RUN_ALL_TESTS();
}
