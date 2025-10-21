#include "core/customized_kernel.h"
#include "core/python_cpp_bridge.h"
#include <iostream>
#include <cassert>
#include <chrono>
#include <thread>
#include <vector>

using namespace cogniware::core;

void testCustomizedKernel() {
    std::cout << "Testing customized kernel..." << std::endl;
    
    auto kernel = std::make_shared<AdvancedCustomizedKernel>();
    
    // Test initialization
    bool initialized = kernel->initialize();
    assert(initialized && "Failed to initialize kernel");
    std::cout << "✓ Kernel initialized successfully" << std::endl;
    
    // Test device management
    auto devices = kernel->getAvailableDevices();
    assert(!devices.empty() && "No devices available");
    std::cout << "✓ Found " << devices.size() << " GPU devices" << std::endl;
    
    for (const auto& device : devices) {
        std::cout << "  Device " << device.deviceId << ": " << device.name 
                  << " (Compute " << device.computeCapability << ")" << std::endl;
        std::cout << "    Memory: " << device.totalMemory / (1024*1024*1024) << " GB total, "
                  << device.freeMemory / (1024*1024*1024) << " GB free" << std::endl;
        std::cout << "    Tensor Cores: " << device.tensorCoreCount << std::endl;
        std::cout << "    CUDA Cores: " << device.cudaCoreCount << std::endl;
    }
    
    // Test device selection
    bool deviceSelected = kernel->selectDevice(0);
    assert(deviceSelected && "Failed to select device 0");
    std::cout << "✓ Selected device 0" << std::endl;
    
    auto currentDevice = kernel->getCurrentDevice();
    std::cout << "  Current device: " << currentDevice.name << std::endl;
    
    // Test compute node management
    auto computeNodes = kernel->getAvailableComputeNodes();
    assert(!computeNodes.empty() && "No compute nodes available");
    std::cout << "✓ Found " << computeNodes.size() << " compute nodes" << std::endl;
    
    // Test compute node allocation
    bool allocated = kernel->allocateComputeNode(0, "test_llm");
    assert(allocated && "Failed to allocate compute node");
    std::cout << "✓ Allocated compute node 0 for test_llm" << std::endl;
    
    auto node = kernel->getComputeNode(0);
    assert(node.isAllocated && "Compute node not allocated");
    std::cout << "  Node 0: " << node.memorySize << " bytes, " 
              << node.computeCapability << " cores" << std::endl;
    
    // Test memory partitioning
    auto memoryPartitions = kernel->getMemoryPartitions();
    assert(!memoryPartitions.empty() && "No memory partitions available");
    std::cout << "✓ Found " << memoryPartitions.size() << " memory partitions" << std::endl;
    
    // Test memory allocation
    void* testMemory = kernel->allocateMemory(1024 * 1024, "test_llm"); // 1MB
    assert(testMemory != nullptr && "Failed to allocate memory");
    std::cout << "✓ Allocated 1MB memory for test_llm" << std::endl;
    
    // Test memory deallocation
    bool deallocated = kernel->deallocateMemory(testMemory);
    assert(deallocated && "Failed to deallocate memory");
    std::cout << "✓ Deallocated memory" << std::endl;
    
    // Test CUDA stream management
    cudaStream_t stream = kernel->createStream("test_llm");
    assert(stream != nullptr && "Failed to create CUDA stream");
    std::cout << "✓ Created CUDA stream for test_llm" << std::endl;
    
    auto streams = kernel->getStreamsForLLM("test_llm");
    assert(!streams.empty() && "No streams found for test_llm");
    std::cout << "✓ Found " << streams.size() << " streams for test_llm" << std::endl;
    
    // Test stream synchronization
    bool synchronized = kernel->synchronizeStream(stream);
    assert(synchronized && "Failed to synchronize stream");
    std::cout << "✓ Synchronized CUDA stream" << std::endl;
    
    // Test stream destruction
    bool destroyed = kernel->destroyStream(stream);
    assert(destroyed && "Failed to destroy CUDA stream");
    std::cout << "✓ Destroyed CUDA stream" << std::endl;
    
    // Test task scheduling
    ComputeTask task;
    task.taskId = "test_task";
    task.llmId = "test_llm";
    task.priority = TaskPriority::NORMAL;
    task.requiredMemory = 1024 * 1024;
    task.requiredCores = 1;
    task.taskFunction = []() {
        std::cout << "    Executing test task..." << std::endl;
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    };
    
    std::string taskId = kernel->scheduleTask(task);
    assert(!taskId.empty() && "Failed to schedule task");
    std::cout << "✓ Scheduled task: " << taskId << std::endl;
    
    // Wait for task completion
    std::this_thread::sleep_for(std::chrono::milliseconds(200));
    
    auto taskStatus = kernel->getTaskStatus(taskId);
    std::cout << "  Task status: " << (taskStatus.isCompleted ? "completed" : "running") << std::endl;
    
    // Test performance metrics
    auto metrics = kernel->getPerformanceMetrics();
    assert(!metrics.empty() && "No performance metrics available");
    std::cout << "✓ Retrieved performance metrics:" << std::endl;
    for (const auto& metric : metrics) {
        std::cout << "  " << metric.first << ": " << metric.second << std::endl;
    }
    
    // Test resource usage
    auto usage = kernel->getResourceUsage();
    assert(!usage.empty() && "No resource usage data available");
    std::cout << "✓ Retrieved resource usage:" << std::endl;
    for (const auto& resource : usage) {
        std::cout << "  " << resource.first << ": " << resource.second << std::endl;
    }
    
    // Test compute node deallocation
    bool deallocatedNode = kernel->deallocateComputeNode(0);
    assert(deallocatedNode && "Failed to deallocate compute node");
    std::cout << "✓ Deallocated compute node 0" << std::endl;
    
    // Test shutdown
    kernel->shutdown();
    std::cout << "✓ Kernel shutdown completed" << std::endl;
}

void testCustomizedDriver() {
    std::cout << "Testing customized driver..." << std::endl;
    
    auto driver = std::make_shared<AdvancedCustomizedDriver>();
    
    // Test initialization
    bool initialized = driver->initialize();
    assert(initialized && "Failed to initialize driver");
    std::cout << "✓ Driver initialized successfully" << std::endl;
    
    // Test kernel access
    auto kernel = driver->getKernel();
    assert(kernel != nullptr && "Failed to get kernel from driver");
    std::cout << "✓ Retrieved kernel from driver" << std::endl;
    
    // Test driver info
    auto driverInfo = driver->getDriverInfo();
    assert(!driverInfo.empty() && "No driver info available");
    std::cout << "✓ Retrieved driver info:" << std::endl;
    for (const auto& info : driverInfo) {
        std::cout << "  " << info.first << ": " << info.second << std::endl;
    }
    
    // Test performance stats
    auto performanceStats = driver->getPerformanceStats();
    assert(!performanceStats.empty() && "No performance stats available");
    std::cout << "✓ Retrieved performance stats:" << std::endl;
    for (const auto& stat : performanceStats) {
        std::cout << "  " << stat.first << ": " << stat.second << std::endl;
    }
    
    // Test supported GPUs
    auto supportedGPUs = driver->getSupportedGPUs();
    assert(!supportedGPUs.empty() && "No supported GPUs listed");
    std::cout << "✓ Supported GPUs:" << std::endl;
    for (const auto& gpu : supportedGPUs) {
        std::cout << "  " << gpu << std::endl;
    }
    
    // Test diagnostics
    bool diagnosticsPassed = driver->runDiagnostics();
    assert(diagnosticsPassed && "Driver diagnostics failed");
    std::cout << "✓ Driver diagnostics passed" << std::endl;
    
    // Test optimization features
    bool optimized = driver->optimizeForMultipleLLMs();
    assert(optimized && "Failed to optimize for multiple LLMs");
    std::cout << "✓ Optimized driver for multiple LLMs" << std::endl;
    
    bool tensorOptimized = driver->enableTensorCoreOptimization();
    assert(tensorOptimized && "Failed to enable tensor core optimization");
    std::cout << "✓ Enabled tensor core optimization" << std::endl;
    
    bool memoryOptimized = driver->enableMemoryOptimization();
    assert(memoryOptimized && "Failed to enable memory optimization");
    std::cout << "✓ Enabled memory optimization" << std::endl;
    
    // Test shutdown
    driver->shutdown();
    std::cout << "✓ Driver shutdown completed" << std::endl;
}

void testKernelDriverManager() {
    std::cout << "Testing kernel driver manager..." << std::endl;
    
    auto& manager = KernelDriverManager::getInstance();
    
    // Test system initialization
    bool initialized = manager.initializeSystem();
    assert(initialized && "Failed to initialize system");
    std::cout << "✓ System initialized successfully" << std::endl;
    
    // Test system status
    bool isInitialized = manager.isSystemInitialized();
    assert(isInitialized && "System not initialized");
    std::cout << "✓ System status verified" << std::endl;
    
    // Test kernel access
    auto kernel = manager.getKernel();
    assert(kernel != nullptr && "Failed to get kernel from manager");
    std::cout << "✓ Retrieved kernel from manager" << std::endl;
    
    // Test driver access
    auto driver = manager.getDriver();
    assert(driver != nullptr && "Failed to get driver from manager");
    std::cout << "✓ Retrieved driver from manager" << std::endl;
    
    // Test performance metrics
    auto metrics = manager.getSystemPerformanceMetrics();
    assert(!metrics.empty() && "No system performance metrics available");
    std::cout << "✓ Retrieved system performance metrics:" << std::endl;
    for (const auto& metric : metrics) {
        std::cout << "  " << metric.first << ": " << metric.second << std::endl;
    }
    
    // Test resource usage
    auto usage = manager.getSystemResourceUsage();
    assert(!usage.empty() && "No system resource usage available");
    std::cout << "✓ Retrieved system resource usage:" << std::endl;
    for (const auto& resource : usage) {
        std::cout << "  " << resource.first << ": " << resource.second << std::endl;
    }
    
    // Test profiling
    bool profilingEnabled = manager.enableSystemProfiling();
    assert(profilingEnabled && "Failed to enable system profiling");
    std::cout << "✓ Enabled system profiling" << std::endl;
    
    bool profilingDisabled = manager.disableSystemProfiling();
    assert(profilingDisabled && "Failed to disable system profiling");
    std::cout << "✓ Disabled system profiling" << std::endl;
    
    // Test configuration
    std::map<std::string, std::string> kernelConfig = {
        {"max_memory", "8192"},
        {"max_cores", "100"},
        {"enable_profiling", "true"}
    };
    manager.setKernelConfiguration(kernelConfig);
    std::cout << "✓ Set kernel configuration" << std::endl;
    
    auto retrievedConfig = manager.getKernelConfiguration();
    assert(!retrievedConfig.empty() && "Failed to retrieve kernel configuration");
    std::cout << "✓ Retrieved kernel configuration" << std::endl;
    
    // Test system shutdown
    manager.shutdownSystem();
    std::cout << "✓ System shutdown completed" << std::endl;
}

void testPythonCppBridge() {
    std::cout << "Testing Python-C++ bridge..." << std::endl;
    
    auto bridge = std::make_shared<AdvancedPythonCppBridge>();
    
    // Test initialization
    bool initialized = bridge->initialize();
    assert(initialized && "Failed to initialize bridge");
    std::cout << "✓ Bridge initialized successfully" << std::endl;
    
    // Test LLM registration
    std::map<std::string, std::string> llmConfig = {
        {"model_type", "gpt"},
        {"max_tokens", "100"},
        {"temperature", "0.7"}
    };
    bool registered = bridge->registerLLM("test_llm", llmConfig);
    assert(registered && "Failed to register LLM");
    std::cout << "✓ Registered test_llm" << std::endl;
    
    // Test LLM configuration retrieval
    auto config = bridge->getLLMConfig("test_llm");
    assert(!config.empty() && "Failed to retrieve LLM config");
    std::cout << "✓ Retrieved LLM configuration" << std::endl;
    
    // Test memory array allocation
    auto array = bridge->allocateMemoryArray(1000, "test_llm");
    assert(!array.empty() && "Failed to allocate memory array");
    std::cout << "✓ Allocated memory array for test_llm" << std::endl;
    
    // Test memory pointer access
    void* ptr = bridge->getMemoryPointer(array);
    assert(ptr != nullptr && "Failed to get memory pointer");
    std::cout << "✓ Retrieved memory pointer" << std::endl;
    
    // Test compute node allocation
    auto availableNodes = bridge->getAvailableComputeNodes();
    assert(!availableNodes.empty() && "No available compute nodes");
    std::cout << "✓ Found " << availableNodes.size() << " available compute nodes" << std::endl;
    
    bool nodeAllocated = bridge->allocateComputeNode(availableNodes[0], "test_llm");
    assert(nodeAllocated && "Failed to allocate compute node");
    std::cout << "✓ Allocated compute node " << availableNodes[0] << " for test_llm" << std::endl;
    
    // Test task scheduling
    std::map<std::string, std::string> taskParams = {
        {"task_type", "inference"},
        {"priority", "normal"}
    };
    std::string taskId = bridge->scheduleTask("test_llm", "inference", taskParams);
    assert(!taskId.empty() && "Failed to schedule task");
    std::cout << "✓ Scheduled task: " << taskId << std::endl;
    
    // Test task status
    auto taskStatus = bridge->getTaskStatus(taskId);
    assert(!taskStatus.empty() && "Failed to get task status");
    std::cout << "✓ Retrieved task status" << std::endl;
    
    // Test active tasks
    auto activeTasks = bridge->getActiveTasks("test_llm");
    assert(!activeTasks.empty() && "No active tasks found");
    std::cout << "✓ Found " << activeTasks.size() << " active tasks for test_llm" << std::endl;
    
    // Test resource usage
    auto resourceUsage = bridge->getResourceUsage("test_llm");
    assert(!resourceUsage.empty() && "No resource usage data");
    std::cout << "✓ Retrieved resource usage for test_llm" << std::endl;
    
    // Test memory usage
    auto memoryUsage = bridge->getMemoryUsage("test_llm");
    assert(!memoryUsage.empty() && "No memory usage data");
    std::cout << "✓ Retrieved memory usage for test_llm" << std::endl;
    
    // Test performance metrics
    auto metrics = bridge->getPerformanceMetrics();
    assert(!metrics.empty() && "No performance metrics");
    std::cout << "✓ Retrieved performance metrics" << std::endl;
    
    // Test profiling
    bool profilingEnabled = bridge->enableProfiling("test_llm");
    assert(profilingEnabled && "Failed to enable profiling");
    std::cout << "✓ Enabled profiling for test_llm" << std::endl;
    
    auto profilingData = bridge->getProfilingData("test_llm");
    assert(!profilingData.empty() && "No profiling data");
    std::cout << "✓ Retrieved profiling data for test_llm" << std::endl;
    
    bool profilingDisabled = bridge->disableProfiling("test_llm");
    assert(profilingDisabled && "Failed to disable profiling");
    std::cout << "✓ Disabled profiling for test_llm" << std::endl;
    
    // Test active LLMs
    auto activeLLMs = bridge->getActiveLLMs();
    assert(!activeLLMs.empty() && "No active LLMs");
    std::cout << "✓ Found " << activeLLMs.size() << " active LLMs" << std::endl;
    
    // Test LLM activity check
    bool isActive = bridge->isLLMActive("test_llm");
    assert(isActive && "test_llm not active");
    std::cout << "✓ Verified test_llm is active" << std::endl;
    
    // Test system info
    auto systemInfo = bridge->getSystemInfo();
    assert(!systemInfo.empty() && "No system info");
    std::cout << "✓ Retrieved system info" << std::endl;
    
    // Test diagnostics
    bool diagnosticsPassed = bridge->runDiagnostics();
    assert(diagnosticsPassed && "Bridge diagnostics failed");
    std::cout << "✓ Bridge diagnostics passed" << std::endl;
    
    auto diagnosticResults = bridge->getDiagnosticResults();
    assert(!diagnosticResults.empty() && "No diagnostic results");
    std::cout << "✓ Retrieved diagnostic results" << std::endl;
    
    // Test memory array deallocation
    bool deallocated = bridge->deallocateMemoryArray(array, "test_llm");
    assert(deallocated && "Failed to deallocate memory array");
    std::cout << "✓ Deallocated memory array" << std::endl;
    
    // Test compute node deallocation
    bool nodeDeallocated = bridge->deallocateComputeNode(availableNodes[0], "test_llm");
    assert(nodeDeallocated && "Failed to deallocate compute node");
    std::cout << "✓ Deallocated compute node" << std::endl;
    
    // Test LLM unregistration
    bool unregistered = bridge->unregisterLLM("test_llm");
    assert(unregistered && "Failed to unregister LLM");
    std::cout << "✓ Unregistered test_llm" << std::endl;
    
    // Test shutdown
    bridge->shutdown();
    std::cout << "✓ Bridge shutdown completed" << std::endl;
}

void testPythonCppBridgeManager() {
    std::cout << "Testing Python-C++ bridge manager..." << std::endl;
    
    auto& manager = PythonCppBridgeManager::getInstance();
    
    // Test bridge initialization
    bool initialized = manager.initializeBridge();
    assert(initialized && "Failed to initialize bridge");
    std::cout << "✓ Bridge manager initialized successfully" << std::endl;
    
    // Test bridge status
    bool isInitialized = manager.isBridgeInitialized();
    assert(isInitialized && "Bridge not initialized");
    std::cout << "✓ Bridge status verified" << std::endl;
    
    // Test bridge access
    auto bridge = manager.getBridge();
    assert(bridge != nullptr && "Failed to get bridge from manager");
    std::cout << "✓ Retrieved bridge from manager" << std::endl;
    
    // Test quick access methods
    std::map<std::string, std::string> llmConfig = {
        {"model_type", "gpt"},
        {"max_tokens", "100"}
    };
    bool registered = manager.registerLLM("test_llm", llmConfig);
    assert(registered && "Failed to register LLM via manager");
    std::cout << "✓ Registered LLM via manager" << std::endl;
    
    auto array = manager.allocateMemoryArray(1000, "test_llm");
    assert(!array.empty() && "Failed to allocate memory array via manager");
    std::cout << "✓ Allocated memory array via manager" << std::endl;
    
    auto resourceUsage = manager.getResourceUsage("test_llm");
    assert(!resourceUsage.empty() && "No resource usage data via manager");
    std::cout << "✓ Retrieved resource usage via manager" << std::endl;
    
    auto activeLLMs = manager.getActiveLLMs();
    assert(!activeLLMs.empty() && "No active LLMs via manager");
    std::cout << "✓ Retrieved active LLMs via manager" << std::endl;
    
    // Test configuration
    std::map<std::string, std::string> bridgeConfig = {
        {"max_memory", "8192"},
        {"max_llms", "10"},
        {"enable_profiling", "true"}
    };
    manager.setBridgeConfiguration(bridgeConfig);
    std::cout << "✓ Set bridge configuration" << std::endl;
    
    auto retrievedConfig = manager.getBridgeConfiguration();
    assert(!retrievedConfig.empty() && "Failed to retrieve bridge configuration");
    std::cout << "✓ Retrieved bridge configuration" << std::endl;
    
    // Test cleanup
    bool deallocated = manager.deallocateMemoryArray(array, "test_llm");
    assert(deallocated && "Failed to deallocate memory array via manager");
    std::cout << "✓ Deallocated memory array via manager" << std::endl;
    
    bool unregistered = manager.unregisterLLM("test_llm");
    assert(unregistered && "Failed to unregister LLM via manager");
    std::cout << "✓ Unregistered LLM via manager" << std::endl;
    
    // Test shutdown
    manager.shutdownBridge();
    std::cout << "✓ Bridge manager shutdown completed" << std::endl;
}

void testPatentClaims() {
    std::cout << "Testing patent claims..." << std::endl;
    
    // Test 1: Multiple LLM execution capability
    std::cout << "Testing multiple LLM execution capability..." << std::endl;
    
    auto& kernelManager = KernelDriverManager::getInstance();
    kernelManager.initializeSystem();
    
    auto& bridgeManager = PythonCppBridgeManager::getInstance();
    bridgeManager.initializeBridge();
    
    // Register multiple LLMs
    std::vector<std::string> llmIds = {"llm1", "llm2", "llm3", "llm4"};
    for (const auto& llmId : llmIds) {
        std::map<std::string, std::string> config = {
            {"model_type", "gpt"},
            {"max_tokens", "100"},
            {"temperature", "0.7"}
        };
        bool registered = bridgeManager.registerLLM(llmId, config);
        assert(registered && "Failed to register LLM");
        
        // Allocate memory for each LLM
        auto array = bridgeManager.allocateMemoryArray(1000, llmId);
        assert(!array.empty() && "Failed to allocate memory for LLM");
    }
    
    std::cout << "✓ Registered " << llmIds.size() << " LLMs simultaneously" << std::endl;
    
    // Test 2: Parallel computing with custom kernel
    std::cout << "Testing parallel computing with custom kernel..." << std::endl;
    
    auto kernel = kernelManager.getKernel();
    assert(kernel != nullptr && "Failed to get kernel");
    
    // Test multiple compute nodes
    auto computeNodes = kernel->getAvailableComputeNodes();
    assert(!computeNodes.empty() && "No compute nodes available");
    
    // Allocate multiple compute nodes
    for (size_t i = 0; i < std::min(static_cast<size_t>(4), computeNodes.size()); ++i) {
        bool allocated = kernel->allocateComputeNode(computeNodes[i].nodeId, llmIds[i]);
        assert(allocated && "Failed to allocate compute node");
    }
    
    std::cout << "✓ Allocated " << std::min(static_cast<size_t>(4), computeNodes.size()) 
              << " compute nodes in parallel" << std::endl;
    
    // Test 3: Direct memory access
    std::cout << "Testing direct memory access..." << std::endl;
    
    auto bridge = bridgeManager.getBridge();
    assert(bridge != nullptr && "Failed to get bridge");
    
    // Test direct memory pointer access
    for (const auto& llmId : llmIds) {
        auto array = bridge->allocateMemoryArray(1000, llmId);
        void* ptr = bridge->getMemoryPointer(array);
        assert(ptr != nullptr && "Failed to get memory pointer");
    }
    
    std::cout << "✓ Direct memory access working for all LLMs" << std::endl;
    
    // Test 4: Resource monitoring
    std::cout << "Testing resource monitoring..." << std::endl;
    
    auto activeLLMs = bridgeManager.getActiveLLMs();
    assert(activeLLMs.size() == llmIds.size() && "Not all LLMs are active");
    
    for (const auto& llmId : llmIds) {
        auto resourceUsage = bridgeManager.getResourceUsage(llmId);
        assert(!resourceUsage.empty() && "No resource usage data");
    }
    
    std::cout << "✓ Resource monitoring working for all LLMs" << std::endl;
    
    // Test 5: Performance metrics
    std::cout << "Testing performance metrics..." << std::endl;
    
    auto systemMetrics = kernelManager.getSystemPerformanceMetrics();
    assert(!systemMetrics.empty() && "No system performance metrics");
    
    auto systemUsage = kernelManager.getSystemResourceUsage();
    assert(!systemUsage.empty() && "No system resource usage");
    
    std::cout << "✓ Performance metrics collection working" << std::endl;
    
    // Cleanup
    for (const auto& llmId : llmIds) {
        bridgeManager.unregisterLLM(llmId);
    }
    
    bridgeManager.shutdownBridge();
    kernelManager.shutdownSystem();
    
    std::cout << "✓ Patent claims test completed successfully" << std::endl;
}

int main() {
    std::cout << "=== CogniWare Customized Kernel and Driver Test ===" << std::endl;
    std::cout << std::endl;
    
    try {
        testCustomizedKernel();
        std::cout << std::endl;
        
        testCustomizedDriver();
        std::cout << std::endl;
        
        testKernelDriverManager();
        std::cout << std::endl;
        
        testPythonCppBridge();
        std::cout << std::endl;
        
        testPythonCppBridgeManager();
        std::cout << std::endl;
        
        testPatentClaims();
        std::cout << std::endl;
        
        std::cout << "=== All customized kernel and driver tests completed ===" << std::endl;
        
    } catch (const std::exception& e) {
        std::cerr << "Test failed with exception: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}
