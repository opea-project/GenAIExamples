#include "optimization/tensor_core_optimizer.h"
#include <spdlog/spdlog.h>

namespace cogniware {
namespace optimization {

TensorCoreOptimizationManager& TensorCoreOptimizationManager::getInstance() {
    static TensorCoreOptimizationManager instance;
    return instance;
}

TensorCoreOptimizationManager::TensorCoreOptimizationManager()
    : initialized_(false) {
    
    spdlog::info("TensorCoreOptimizationManager singleton created");
}

TensorCoreOptimizationManager::~TensorCoreOptimizationManager() {
    shutdown();
}

bool TensorCoreOptimizationManager::initialize() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (initialized_) {
        spdlog::warn("Tensor core optimization manager already initialized");
        return true;
    }
    
    try {
        // Initialize optimizer
        optimizer_ = std::make_shared<AdvancedTensorCoreOptimizer>();
        if (!optimizer_->initialize()) {
            spdlog::error("Failed to initialize tensor core optimizer");
            return false;
        }
        
        // Initialize workload balancer
        workloadBalancer_ = std::make_shared<TensorCoreWorkloadBalancer>();
        
        // Initialize memory optimizer
        memoryOptimizer_ = std::make_shared<TensorCoreMemoryOptimizer>();
        
        // Initialize precision optimizer
        precisionOptimizer_ = std::make_shared<TensorCorePrecisionOptimizer>();
        
        // Set default configuration
        configuration_["optimization_level"] = "high";
        configuration_["dormant_core_activation"] = "enabled";
        configuration_["workload_balancing"] = "enabled";
        configuration_["memory_optimization"] = "enabled";
        configuration_["precision_optimization"] = "enabled";
        
        initialized_ = true;
        spdlog::info("TensorCoreOptimizationManager initialized successfully");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize tensor core optimization manager: {}", e.what());
        return false;
    }
}

void TensorCoreOptimizationManager::shutdown() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        return;
    }
    
    try {
        // Shutdown components
        if (optimizer_) {
            optimizer_->shutdown();
            optimizer_.reset();
        }
        
        workloadBalancer_.reset();
        memoryOptimizer_.reset();
        precisionOptimizer_.reset();
        
        initialized_ = false;
        spdlog::info("TensorCoreOptimizationManager shutdown completed");
        
    } catch (const std::exception& e) {
        spdlog::error("Error during tensor core optimization manager shutdown: {}", e.what());
    }
}

bool TensorCoreOptimizationManager::isInitialized() const {
    return initialized_;
}

std::shared_ptr<TensorCoreOptimizer> TensorCoreOptimizationManager::getOptimizer() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    return optimizer_;
}

std::shared_ptr<TensorCoreWorkloadBalancer> TensorCoreOptimizationManager::getWorkloadBalancer() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    return workloadBalancer_;
}

std::shared_ptr<TensorCoreMemoryOptimizer> TensorCoreOptimizationManager::getMemoryOptimizer() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    return memoryOptimizer_;
}

std::shared_ptr<TensorCorePrecisionOptimizer> TensorCoreOptimizationManager::getPrecisionOptimizer() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    return precisionOptimizer_;
}

bool TensorCoreOptimizationManager::optimizeSystem() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Starting system-wide tensor core optimization");
        
        bool success = true;
        
        // Activate dormant cores
        if (configuration_["dormant_core_activation"] == "enabled") {
            if (!optimizer_->activateDormantCores()) {
                spdlog::warn("Failed to activate dormant cores");
                success = false;
            }
        }
        
        // Balance workload
        if (configuration_["workload_balancing"] == "enabled") {
            if (!optimizer_->balanceWorkload()) {
                spdlog::warn("Failed to balance workload");
                success = false;
            }
        }
        
        // Optimize memory
        if (configuration_["memory_optimization"] == "enabled") {
            if (!optimizer_->optimizeMemoryAccess()) {
                spdlog::warn("Failed to optimize memory access");
                success = false;
            }
        }
        
        // Optimize precision
        if (configuration_["precision_optimization"] == "enabled") {
            if (!optimizer_->optimizePrecision()) {
                spdlog::warn("Failed to optimize precision");
                success = false;
            }
        }
        
        if (success) {
            spdlog::info("System-wide tensor core optimization completed successfully");
        } else {
            spdlog::warn("System-wide tensor core optimization completed with warnings");
        }
        
        return success;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to optimize system: {}", e.what());
        return false;
    }
}

bool TensorCoreOptimizationManager::optimizeForMultipleLLMs(const std::vector<std::string>& llmIds) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Optimizing for {} LLMs", llmIds.size());
        
        bool success = true;
        
        // Optimize for each LLM
        for (const auto& llmId : llmIds) {
            std::map<std::string, std::string> requirements = {
                {"precision", "mixed"},
                {"memory_bandwidth", "1.2"},
                {"compute_throughput", "1.1"}
            };
            
            if (!optimizer_->optimizeForLLM(llmId, requirements)) {
                spdlog::warn("Failed to optimize for LLM: {}", llmId);
                success = false;
            }
        }
        
        // Balance workload across LLMs
        if (workloadBalancer_) {
            if (!workloadBalancer_->balanceWorkload(llmIds)) {
                spdlog::warn("Failed to balance workload across LLMs");
                success = false;
            }
        }
        
        if (success) {
            spdlog::info("Multi-LLM optimization completed successfully");
        } else {
            spdlog::warn("Multi-LLM optimization completed with warnings");
        }
        
        return success;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to optimize for multiple LLMs: {}", e.what());
        return false;
    }
}

bool TensorCoreOptimizationManager::optimizeForWorkload(const std::string& workloadType) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Optimizing for workload type: {}", workloadType);
        
        std::map<std::string, std::string> parameters;
        
        if (workloadType == "inference") {
            parameters = {
                {"precision", "fp16"},
                {"memory_bandwidth", "1.5"},
                {"compute_throughput", "1.3"}
            };
        } else if (workloadType == "training") {
            parameters = {
                {"precision", "mixed"},
                {"memory_bandwidth", "1.2"},
                {"compute_throughput", "1.1"}
            };
        } else if (workloadType == "embedding") {
            parameters = {
                {"precision", "int8"},
                {"memory_bandwidth", "1.8"},
                {"compute_throughput", "1.6"}
            };
        } else {
            parameters = {
                {"precision", "mixed"},
                {"memory_bandwidth", "1.0"},
                {"compute_throughput", "1.0"}
            };
        }
        
        bool success = optimizer_->optimizeForWorkload(workloadType, parameters);
        
        if (success) {
            spdlog::info("Workload optimization completed for type: {}", workloadType);
        } else {
            spdlog::error("Failed to optimize for workload type: {}", workloadType);
        }
        
        return success;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to optimize for workload: {}", e.what());
        return false;
    }
}

bool TensorCoreOptimizationManager::runSystemOptimization() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Running comprehensive system optimization");
        
        bool success = true;
        
        // Run all optimization strategies
        std::vector<std::string> strategies = {
            "dormant_core_activation",
            "workload_balancing", 
            "memory_optimization",
            "precision_optimization",
            "parallel_execution",
            "cache_optimization",
            "pipeline_optimization"
        };
        
        for (const auto& strategy : strategies) {
            if (configuration_[strategy] == "enabled") {
                spdlog::info("Running optimization strategy: {}", strategy);
                
                if (strategy == "dormant_core_activation") {
                    if (!optimizer_->activateDormantCores()) {
                        spdlog::warn("Dormant core activation failed");
                        success = false;
                    }
                } else if (strategy == "workload_balancing") {
                    if (!optimizer_->balanceWorkload()) {
                        spdlog::warn("Workload balancing failed");
                        success = false;
                    }
                } else if (strategy == "memory_optimization") {
                    if (!optimizer_->optimizeMemoryAccess()) {
                        spdlog::warn("Memory optimization failed");
                        success = false;
                    }
                } else if (strategy == "precision_optimization") {
                    if (!optimizer_->optimizePrecision()) {
                        spdlog::warn("Precision optimization failed");
                        success = false;
                    }
                } else if (strategy == "parallel_execution") {
                    if (!optimizer_->optimizeParallelExecution()) {
                        spdlog::warn("Parallel execution optimization failed");
                        success = false;
                    }
                } else if (strategy == "cache_optimization") {
                    if (!optimizer_->optimizeCache()) {
                        spdlog::warn("Cache optimization failed");
                        success = false;
                    }
                } else if (strategy == "pipeline_optimization") {
                    if (!optimizer_->optimizePipeline()) {
                        spdlog::warn("Pipeline optimization failed");
                        success = false;
                    }
                }
            }
        }
        
        if (success) {
            spdlog::info("Comprehensive system optimization completed successfully");
        } else {
            spdlog::warn("Comprehensive system optimization completed with warnings");
        }
        
        return success;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to run system optimization: {}", e.what());
        return false;
    }
}

OptimizationMetrics TensorCoreOptimizationManager::getSystemOptimizationMetrics() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_ || !optimizer_) {
        return OptimizationMetrics{};
    }
    
    return optimizer_->getOptimizationMetrics();
}

std::map<std::string, double> TensorCoreOptimizationManager::getSystemPerformanceMetrics() {
    std::map<std::string, double> metrics;
    
    try {
        if (optimizer_) {
            auto optimizationMetrics = optimizer_->getOptimizationMetrics();
            
            metrics["total_utilization"] = optimizationMetrics.totalUtilization;
            metrics["dormant_core_utilization"] = optimizationMetrics.dormantCoreUtilization;
            metrics["performance_improvement"] = optimizationMetrics.performanceImprovement;
            metrics["memory_bandwidth_used"] = static_cast<double>(optimizationMetrics.memoryBandwidthUsed);
            metrics["compute_throughput"] = static_cast<double>(optimizationMetrics.computeThroughput);
            metrics["execution_time_ms"] = static_cast<double>(optimizationMetrics.executionTime.count());
            metrics["cores_activated"] = static_cast<double>(optimizationMetrics.coresActivated);
            metrics["cores_optimized"] = static_cast<double>(optimizationMetrics.coresOptimized);
        }
        
        if (workloadBalancer_) {
            auto coreLoads = workloadBalancer_->getCoreLoads();
            metrics["load_imbalance"] = workloadBalancer_->getLoadImbalance();
            metrics["is_load_balanced"] = workloadBalancer_->isLoadBalanced() ? 1.0 : 0.0;
        }
        
        if (memoryOptimizer_) {
            metrics["memory_efficiency"] = memoryOptimizer_->getMemoryEfficiency();
            metrics["is_memory_optimized"] = memoryOptimizer_->isMemoryOptimized() ? 1.0 : 0.0;
        }
        
        if (precisionOptimizer_) {
            metrics["precision_efficiency"] = precisionOptimizer_->getPrecisionEfficiency();
            metrics["is_precision_optimized"] = precisionOptimizer_->isPrecisionOptimized() ? 1.0 : 0.0;
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get system performance metrics: {}", e.what());
    }
    
    return metrics;
}

bool TensorCoreOptimizationManager::enableSystemProfiling() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        bool success = true;
        
        if (optimizer_) {
            success &= optimizer_->enableProfiling();
        }
        
        if (success) {
            spdlog::info("System profiling enabled");
        } else {
            spdlog::error("Failed to enable system profiling");
        }
        
        return success;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to enable system profiling: {}", e.what());
        return false;
    }
}

bool TensorCoreOptimizationManager::disableSystemProfiling() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        bool success = true;
        
        if (optimizer_) {
            success &= optimizer_->disableProfiling();
        }
        
        if (success) {
            spdlog::info("System profiling disabled");
        } else {
            spdlog::error("Failed to disable system profiling");
        }
        
        return success;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to disable system profiling: {}", e.what());
        return false;
    }
}

void TensorCoreOptimizationManager::setOptimizationConfiguration(const std::map<std::string, std::string>& config) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    configuration_ = config;
    spdlog::info("Optimization configuration updated with {} settings", config.size());
}

std::map<std::string, std::string> TensorCoreOptimizationManager::getOptimizationConfiguration() const {
    std::lock_guard<std::mutex> lock(managerMutex_);
    return configuration_;
}

} // namespace optimization
} // namespace cogniware
