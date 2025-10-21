#pragma once

#include "customized_kernel.h"
#include <Python.h>
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <memory>
#include <string>
#include <vector>
#include <map>
#include <mutex>

namespace cogniware {
namespace core {

// Python-C++ bridge for direct memory access and resource monitoring
class PythonCppBridge {
public:
    virtual ~PythonCppBridge() = default;

    // Memory management
    virtual pybind11::array_t<float> allocateMemoryArray(size_t size, const std::string& llmId) = 0;
    virtual bool deallocateMemoryArray(pybind11::array_t<float> array, const std::string& llmId) = 0;
    virtual void* getMemoryPointer(pybind11::array_t<float> array) = 0;
    virtual bool copyToGPU(pybind11::array_t<float> array, void* gpuPtr) = 0;
    virtual bool copyFromGPU(void* gpuPtr, pybind11::array_t<float> array) = 0;

    // Resource monitoring
    virtual std::map<std::string, double> getResourceUsage(const std::string& llmId) = 0;
    virtual std::map<std::string, size_t> getMemoryUsage(const std::string& llmId) = 0;
    virtual std::vector<std::string> getActiveLLMs() = 0;
    virtual bool isLLMActive(const std::string& llmId) = 0;

    // Compute node management
    virtual std::vector<int> getAvailableComputeNodes() = 0;
    virtual bool allocateComputeNode(int nodeId, const std::string& llmId) = 0;
    virtual bool deallocateComputeNode(int nodeId, const std::string& llmId) = 0;
    virtual std::map<std::string, std::string> getComputeNodeInfo(int nodeId) = 0;

    // Task management
    virtual std::string scheduleTask(const std::string& llmId, const std::string& taskType, 
                                   const std::map<std::string, std::string>& parameters) = 0;
    virtual bool cancelTask(const std::string& taskId) = 0;
    virtual std::map<std::string, std::string> getTaskStatus(const std::string& taskId) = 0;
    virtual std::vector<std::string> getActiveTasks(const std::string& llmId) = 0;

    // Performance monitoring
    virtual std::map<std::string, double> getPerformanceMetrics() = 0;
    virtual bool enableProfiling(const std::string& llmId) = 0;
    virtual bool disableProfiling(const std::string& llmId) = 0;
    virtual std::map<std::string, double> getProfilingData(const std::string& llmId) = 0;
};

// Advanced Python-C++ bridge implementation
class AdvancedPythonCppBridge : public PythonCppBridge {
public:
    AdvancedPythonCppBridge();
    ~AdvancedPythonCppBridge() override;

    // Memory management
    pybind11::array_t<float> allocateMemoryArray(size_t size, const std::string& llmId) override;
    bool deallocateMemoryArray(pybind11::array_t<float> array, const std::string& llmId) override;
    void* getMemoryPointer(pybind11::array_t<float> array) override;
    bool copyToGPU(pybind11::array_t<float> array, void* gpuPtr) override;
    bool copyFromGPU(void* gpuPtr, pybind11::array_t<float> array) override;

    // Resource monitoring
    std::map<std::string, double> getResourceUsage(const std::string& llmId) override;
    std::map<std::string, size_t> getMemoryUsage(const std::string& llmId) override;
    std::vector<std::string> getActiveLLMs() override;
    bool isLLMActive(const std::string& llmId) override;

    // Compute node management
    std::vector<int> getAvailableComputeNodes() override;
    bool allocateComputeNode(int nodeId, const std::string& llmId) override;
    bool deallocateComputeNode(int nodeId, const std::string& llmId) override;
    std::map<std::string, std::string> getComputeNodeInfo(int nodeId) override;

    // Task management
    std::string scheduleTask(const std::string& llmId, const std::string& taskType, 
                           const std::map<std::string, std::string>& parameters) override;
    bool cancelTask(const std::string& taskId) override;
    std::map<std::string, std::string> getTaskStatus(const std::string& taskId) override;
    std::vector<std::string> getActiveTasks(const std::string& llmId) override;

    // Performance monitoring
    std::map<std::string, double> getPerformanceMetrics() override;
    bool enableProfiling(const std::string& llmId) override;
    bool disableProfiling(const std::string& llmId) override;
    std::map<std::string, double> getProfilingData(const std::string& llmId) override;

    // Advanced features
    bool initialize();
    void shutdown();
    bool isInitialized() const;
    
    // Direct memory access
    pybind11::array_t<float> createSharedMemoryArray(size_t size, const std::string& llmId);
    bool destroySharedMemoryArray(pybind11::array_t<float> array, const std::string& llmId);
    void* getSharedMemoryPointer(pybind11::array_t<float> array);
    
    // LLM lifecycle management
    bool registerLLM(const std::string& llmId, const std::map<std::string, std::string>& config);
    bool unregisterLLM(const std::string& llmId);
    std::map<std::string, std::string> getLLMConfig(const std::string& llmId);
    bool updateLLMConfig(const std::string& llmId, const std::map<std::string, std::string>& config);
    
    // Resource optimization
    bool optimizeForLLM(const std::string& llmId, const std::map<std::string, std::string>& requirements);
    bool createVirtualComputeNode(const std::string& llmId, size_t memorySize, size_t coreCount);
    bool destroyVirtualComputeNode(const std::string& llmId);
    
    // Monitoring and diagnostics
    std::map<std::string, std::string> getSystemInfo();
    bool runDiagnostics();
    std::vector<std::string> getDiagnosticResults();

private:
    // Internal state
    bool initialized_;
    std::shared_ptr<AdvancedCustomizedKernel> kernel_;
    std::map<std::string, pybind11::array_t<float>> llmMemoryArrays_;
    std::map<std::string, std::map<std::string, std::string>> llmConfigs_;
    std::map<std::string, std::vector<std::string>> llmTasks_;
    std::map<std::string, bool> llmProfiling_;
    std::mutex bridgeMutex_;

    // Helper methods
    bool validateLLM(const std::string& llmId);
    bool validateArray(pybind11::array_t<float> array);
    std::string generateTaskId();
    void updateLLMResourceUsage(const std::string& llmId);
    void cleanupLLMResources(const std::string& llmId);
};

// Global Python-C++ bridge manager
class PythonCppBridgeManager {
public:
    static PythonCppBridgeManager& getInstance();

    // Bridge management
    std::shared_ptr<PythonCppBridge> getBridge();
    bool initializeBridge();
    void shutdownBridge();
    bool isBridgeInitialized() const;

    // Quick access methods
    pybind11::array_t<float> allocateMemoryArray(size_t size, const std::string& llmId);
    bool deallocateMemoryArray(pybind11::array_t<float> array, const std::string& llmId);
    std::map<std::string, double> getResourceUsage(const std::string& llmId);
    std::vector<std::string> getActiveLLMs();
    bool registerLLM(const std::string& llmId, const std::map<std::string, std::string>& config);
    bool unregisterLLM(const std::string& llmId);

    // Configuration
    void setBridgeConfiguration(const std::map<std::string, std::string>& config);
    std::map<std::string, std::string> getBridgeConfiguration() const;

private:
    PythonCppBridgeManager();
    ~PythonCppBridgeManager();

    std::shared_ptr<AdvancedPythonCppBridge> bridge_;
    bool bridgeInitialized_;
    std::map<std::string, std::string> bridgeConfig_;
    std::mutex managerMutex_;
};

} // namespace core
} // namespace cogniware

// Python module definition
PYBIND11_MODULE(cogniware_core, m) {
    m.doc() = "CogniWare Core - Python-C++ Bridge for Direct Memory Access and Resource Monitoring";

    // Core classes
    pybind11::class_<cogniware::core::PythonCppBridge>(m, "PythonCppBridge")
        .def("allocate_memory_array", &cogniware::core::PythonCppBridge::allocateMemoryArray)
        .def("deallocate_memory_array", &cogniware::core::PythonCppBridge::deallocateMemoryArray)
        .def("get_memory_pointer", &cogniware::core::PythonCppBridge::getMemoryPointer)
        .def("copy_to_gpu", &cogniware::core::PythonCppBridge::copyToGPU)
        .def("copy_from_gpu", &cogniware::core::PythonCppBridge::copyFromGPU)
        .def("get_resource_usage", &cogniware::core::PythonCppBridge::getResourceUsage)
        .def("get_memory_usage", &cogniware::core::PythonCppBridge::getMemoryUsage)
        .def("get_active_llms", &cogniware::core::PythonCppBridge::getActiveLLMs)
        .def("is_llm_active", &cogniware::core::PythonCppBridge::isLLMActive)
        .def("get_available_compute_nodes", &cogniware::core::PythonCppBridge::getAvailableComputeNodes)
        .def("allocate_compute_node", &cogniware::core::PythonCppBridge::allocateComputeNode)
        .def("deallocate_compute_node", &cogniware::core::PythonCppBridge::deallocateComputeNode)
        .def("get_compute_node_info", &cogniware::core::PythonCppBridge::getComputeNodeInfo)
        .def("schedule_task", &cogniware::core::PythonCppBridge::scheduleTask)
        .def("cancel_task", &cogniware::core::PythonCppBridge::cancelTask)
        .def("get_task_status", &cogniware::core::PythonCppBridge::getTaskStatus)
        .def("get_active_tasks", &cogniware::core::PythonCppBridge::getActiveTasks)
        .def("get_performance_metrics", &cogniware::core::PythonCppBridge::getPerformanceMetrics)
        .def("enable_profiling", &cogniware::core::PythonCppBridge::enableProfiling)
        .def("disable_profiling", &cogniware::core::PythonCppBridge::disableProfiling)
        .def("get_profiling_data", &cogniware::core::PythonCppBridge::getProfilingData);

    pybind11::class_<cogniware::core::AdvancedPythonCppBridge, cogniware::core::PythonCppBridge>(m, "AdvancedPythonCppBridge")
        .def(pybind11::init<>())
        .def("initialize", &cogniware::core::AdvancedPythonCppBridge::initialize)
        .def("shutdown", &cogniware::core::AdvancedPythonCppBridge::shutdown)
        .def("is_initialized", &cogniware::core::AdvancedPythonCppBridge::isInitialized)
        .def("create_shared_memory_array", &cogniware::core::AdvancedPythonCppBridge::createSharedMemoryArray)
        .def("destroy_shared_memory_array", &cogniware::core::AdvancedPythonCppBridge::destroySharedMemoryArray)
        .def("get_shared_memory_pointer", &cogniware::core::AdvancedPythonCppBridge::getSharedMemoryPointer)
        .def("register_llm", &cogniware::core::AdvancedPythonCppBridge::registerLLM)
        .def("unregister_llm", &cogniware::core::AdvancedPythonCppBridge::unregisterLLM)
        .def("get_llm_config", &cogniware::core::AdvancedPythonCppBridge::getLLMConfig)
        .def("update_llm_config", &cogniware::core::AdvancedPythonCppBridge::updateLLMConfig)
        .def("optimize_for_llm", &cogniware::core::AdvancedPythonCppBridge::optimizeForLLM)
        .def("create_virtual_compute_node", &cogniware::core::AdvancedPythonCppBridge::createVirtualComputeNode)
        .def("destroy_virtual_compute_node", &cogniware::core::AdvancedPythonCppBridge::destroyVirtualComputeNode)
        .def("get_system_info", &cogniware::core::AdvancedPythonCppBridge::getSystemInfo)
        .def("run_diagnostics", &cogniware::core::AdvancedPythonCppBridge::runDiagnostics)
        .def("get_diagnostic_results", &cogniware::core::AdvancedPythonCppBridge::getDiagnosticResults);

    pybind11::class_<cogniware::core::PythonCppBridgeManager>(m, "PythonCppBridgeManager")
        .def_static("get_instance", &cogniware::core::PythonCppBridgeManager::getInstance, 
                   pybind11::return_value_policy::reference)
        .def("get_bridge", &cogniware::core::PythonCppBridgeManager::getBridge)
        .def("initialize_bridge", &cogniware::core::PythonCppBridgeManager::initializeBridge)
        .def("shutdown_bridge", &cogniware::core::PythonCppBridgeManager::shutdownBridge)
        .def("is_bridge_initialized", &cogniware::core::PythonCppBridgeManager::isBridgeInitialized)
        .def("allocate_memory_array", &cogniware::core::PythonCppBridgeManager::allocateMemoryArray)
        .def("deallocate_memory_array", &cogniware::core::PythonCppBridgeManager::deallocateMemoryArray)
        .def("get_resource_usage", &cogniware::core::PythonCppBridgeManager::getResourceUsage)
        .def("get_active_llms", &cogniware::core::PythonCppBridgeManager::getActiveLLMs)
        .def("register_llm", &cogniware::core::PythonCppBridgeManager::registerLLM)
        .def("unregister_llm", &cogniware::core::PythonCppBridgeManager::unregisterLLM)
        .def("set_bridge_configuration", &cogniware::core::PythonCppBridgeManager::setBridgeConfiguration)
        .def("get_bridge_configuration", &cogniware::core::PythonCppBridgeManager::getBridgeConfiguration);

    // Enums
    pybind11::enum_<cogniware::core::ComputeNodeType>(m, "ComputeNodeType")
        .value("TENSOR_CORE", cogniware::core::ComputeNodeType::TENSOR_CORE)
        .value("CUDA_CORE", cogniware::core::ComputeNodeType::CUDA_CORE)
        .value("MEMORY_BANK", cogniware::core::ComputeNodeType::MEMORY_BANK)
        .value("SHARED_MEMORY", cogniware::core::ComputeNodeType::SHARED_MEMORY)
        .value("L2_CACHE", cogniware::core::ComputeNodeType::L2_CACHE);

    pybind11::enum_<cogniware::core::MemoryPartitionType>(m, "MemoryPartitionType")
        .value("GLOBAL_MEMORY", cogniware::core::MemoryPartitionType::GLOBAL_MEMORY)
        .value("SHARED_MEMORY", cogniware::core::MemoryPartitionType::SHARED_MEMORY)
        .value("CONSTANT_MEMORY", cogniware::core::MemoryPartitionType::CONSTANT_MEMORY)
        .value("TEXTURE_MEMORY", cogniware::core::MemoryPartitionType::TEXTURE_MEMORY)
        .value("LOCAL_MEMORY", cogniware::core::MemoryPartitionType::LOCAL_MEMORY);

    pybind11::enum_<cogniware::core::TaskPriority>(m, "TaskPriority")
        .value("CRITICAL", cogniware::core::TaskPriority::CRITICAL)
        .value("HIGH", cogniware::core::TaskPriority::HIGH)
        .value("NORMAL", cogniware::core::TaskPriority::NORMAL)
        .value("LOW", cogniware::core::TaskPriority::LOW)
        .value("BACKGROUND", cogniware::core::TaskPriority::BACKGROUND);
}
