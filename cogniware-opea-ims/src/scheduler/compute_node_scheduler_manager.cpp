#include "scheduler/compute_node_scheduler.h"
#include <spdlog/spdlog.h>
#include <algorithm>

namespace cogniware {
namespace scheduler {

ComputeNodeSchedulerManager::ComputeNodeSchedulerManager()
    : initialized_(false)
    , maxSchedulers_(10)
    , schedulingStrategy_("balanced")
    , loadBalancingStrategy_("round_robin")
    , systemProfilingEnabled_(false) {
    
    spdlog::info("ComputeNodeSchedulerManager initialized");
}

ComputeNodeSchedulerManager::~ComputeNodeSchedulerManager() {
    shutdown();
}

bool ComputeNodeSchedulerManager::initialize() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (initialized_) {
        spdlog::warn("Compute node scheduler manager already initialized");
        return true;
    }
    
    try {
        schedulers_.clear();
        taskToScheduler_.clear();
        taskStartTime_.clear();
        nodeToSchedulers_.clear();
        
        initialized_ = true;
        spdlog::info("ComputeNodeSchedulerManager initialized successfully");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize compute node scheduler manager: {}", e.what());
        return false;
    }
}

void ComputeNodeSchedulerManager::shutdown() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        return;
    }
    
    try {
        for (auto& scheduler : schedulers_) {
            if (scheduler.second) {
                scheduler.second->shutdown();
            }
        }
        schedulers_.clear();
        
        initialized_ = false;
        spdlog::info("ComputeNodeSchedulerManager shutdown completed");
        
    } catch (const std::exception& e) {
        spdlog::error("Error during compute node scheduler manager shutdown: {}", e.what());
    }
}

bool ComputeNodeSchedulerManager::isInitialized() const {
    return initialized_;
}

std::shared_ptr<ComputeNodeScheduler> ComputeNodeSchedulerManager::createScheduler(const SchedulerConfig& config) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return nullptr;
    }
    
    try {
        if (!validateSchedulerCreation(config)) {
            spdlog::error("Invalid scheduler configuration");
            return nullptr;
        }
        
        if (schedulers_.find(config.schedulerId) != schedulers_.end()) {
            spdlog::error("Compute node scheduler {} already exists", config.schedulerId);
            return nullptr;
        }
        
        if (static_cast<int>(schedulers_.size()) >= maxSchedulers_) {
            spdlog::error("Maximum number of schedulers ({}) reached", maxSchedulers_);
            return nullptr;
        }
        
        auto scheduler = std::make_shared<AdvancedComputeNodeScheduler>(config);
        if (!scheduler->initialize()) {
            spdlog::error("Failed to initialize compute node scheduler {}", config.schedulerId);
            return nullptr;
        }
        
        schedulers_[config.schedulerId] = scheduler;
        
        spdlog::info("Created compute node scheduler: {}", config.schedulerId);
        return scheduler;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to create compute node scheduler {}: {}", config.schedulerId, e.what());
        return nullptr;
    }
}

bool ComputeNodeSchedulerManager::destroyScheduler(const std::string& schedulerId) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        auto it = schedulers_.find(schedulerId);
        if (it == schedulers_.end()) {
            spdlog::error("Compute node scheduler {} not found", schedulerId);
            return false;
        }
        
        if (it->second) {
            it->second->shutdown();
        }
        
        schedulers_.erase(it);
        
        spdlog::info("Destroyed compute node scheduler: {}", schedulerId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to destroy compute node scheduler {}: {}", schedulerId, e.what());
        return false;
    }
}

std::shared_ptr<ComputeNodeScheduler> ComputeNodeSchedulerManager::getScheduler(const std::string& schedulerId) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    auto it = schedulers_.find(schedulerId);
    if (it != schedulers_.end()) {
        return it->second;
    }
    
    return nullptr;
}

std::vector<std::shared_ptr<ComputeNodeScheduler>> ComputeNodeSchedulerManager::getAllSchedulers() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    std::vector<std::shared_ptr<ComputeNodeScheduler>> allSchedulers;
    for (const auto& scheduler : schedulers_) {
        allSchedulers.push_back(scheduler.second);
    }
    return allSchedulers;
}

std::vector<std::shared_ptr<ComputeNodeScheduler>> ComputeNodeSchedulerManager::getSchedulersByType(SchedulerType type) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    std::vector<std::shared_ptr<ComputeNodeScheduler>> schedulersByType;
    for (const auto& scheduler : schedulers_) {
        if (scheduler.second && scheduler.second->getSchedulerType() == type) {
            schedulersByType.push_back(scheduler.second);
        }
    }
    return schedulersByType;
}

std::future<TaskExecutionResult> ComputeNodeSchedulerManager::submitTaskAsync(const TaskExecutionRequest& request) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return std::async(std::launch::deferred, []() {
            TaskExecutionResult result;
            result.success = false;
            result.error = "Manager not initialized";
            return result;
        });
    }
    
    try {
        if (!validateTaskSubmission(request)) {
            spdlog::error("Invalid task submission");
            return std::async(std::launch::deferred, []() {
                TaskExecutionResult result;
                result.success = false;
                result.error = "Invalid task submission";
                return result;
            });
        }
        
        std::string bestSchedulerId;
        if (!findBestScheduler(request, bestSchedulerId)) {
            spdlog::error("No suitable scheduler found for task {}", request.taskId);
            return std::async(std::launch::deferred, []() {
                TaskExecutionResult result;
                result.success = false;
                result.error = "No suitable scheduler found";
                return result;
            });
        }
        
        auto scheduler = getScheduler(bestSchedulerId);
        if (!scheduler) {
            spdlog::error("Scheduler {} not found", bestSchedulerId);
            return std::async(std::launch::deferred, []() {
                TaskExecutionResult result;
                result.success = false;
                result.error = "Scheduler not found";
                return result;
            });
        }
        
        taskToScheduler_[request.taskId] = bestSchedulerId;
        taskStartTime_[request.taskId] = std::chrono::system_clock::now();
        
        auto future = scheduler->submitTaskAsync(request);
        
        spdlog::info("Async task submission started for task {} on scheduler {}", request.taskId, bestSchedulerId);
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

TaskExecutionResult ComputeNodeSchedulerManager::submitTask(const TaskExecutionRequest& request) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        TaskExecutionResult result;
        result.success = false;
        result.error = "Manager not initialized";
        return result;
    }
    
    try {
        if (!validateTaskSubmission(request)) {
            spdlog::error("Invalid task submission");
            TaskExecutionResult result;
            result.success = false;
            result.error = "Invalid task submission";
            return result;
        }
        
        std::string bestSchedulerId;
        if (!findBestScheduler(request, bestSchedulerId)) {
            spdlog::error("No suitable scheduler found for task {}", request.taskId);
            TaskExecutionResult result;
            result.success = false;
            result.error = "No suitable scheduler found";
            return result;
        }
        
        auto scheduler = getScheduler(bestSchedulerId);
        if (!scheduler) {
            spdlog::error("Scheduler {} not found", bestSchedulerId);
            TaskExecutionResult result;
            result.success = false;
            result.error = "Scheduler not found";
            return result;
        }
        
        taskToScheduler_[request.taskId] = bestSchedulerId;
        taskStartTime_[request.taskId] = std::chrono::system_clock::now();
        
        auto result = scheduler->submitTask(request);
        
        spdlog::info("Task submission completed for task {} on scheduler {}", request.taskId, bestSchedulerId);
        return result;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to submit task {}: {}", request.taskId, e.what());
        TaskExecutionResult result;
        result.success = false;
        result.error = "Task submission failed: " + std::string(e.what());
        return result;
    }
}

bool ComputeNodeSchedulerManager::cancelTask(const std::string& taskId) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        auto it = taskToScheduler_.find(taskId);
        if (it == taskToScheduler_.end()) {
            spdlog::error("Task {} not found", taskId);
            return false;
        }
        
        auto scheduler = getScheduler(it->second);
        if (!scheduler) {
            spdlog::error("Scheduler {} not found for task {}", it->second, taskId);
            return false;
        }
        
        bool cancelled = scheduler->cancelTask(taskId);
        
        if (cancelled) {
            taskToScheduler_.erase(it);
            taskStartTime_.erase(taskId);
            spdlog::info("Task {} cancelled", taskId);
        }
        
        return cancelled;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cancel task {}: {}", taskId, e.what());
        return false;
    }
}

bool ComputeNodeSchedulerManager::cancelAllTasks() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        for (const auto& scheduler : schedulers_) {
            if (scheduler.second) {
                auto activeTasks = scheduler.second->getActiveTasks();
                for (const auto& taskId : activeTasks) {
                    scheduler.second->cancelTask(taskId);
                }
            }
        }
        
        taskToScheduler_.clear();
        taskStartTime_.clear();
        
        spdlog::info("All tasks cancelled");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cancel all tasks: {}", e.what());
        return false;
    }
}

std::vector<std::string> ComputeNodeSchedulerManager::getActiveTasks() {
    std::vector<std::string> activeTasks;
    
    try {
        for (const auto& scheduler : schedulers_) {
            if (scheduler.second) {
                auto schedulerTasks = scheduler.second->getActiveTasks();
                activeTasks.insert(activeTasks.end(), schedulerTasks.begin(), schedulerTasks.end());
            }
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get active tasks: {}", e.what());
    }
    
    return activeTasks;
}

std::vector<std::string> ComputeNodeSchedulerManager::getActiveTasksByScheduler(const std::string& schedulerId) {
    std::vector<std::string> activeTasks;
    
    try {
        auto scheduler = getScheduler(schedulerId);
        if (scheduler) {
            activeTasks = scheduler->getActiveTasks();
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get active tasks for scheduler {}: {}", schedulerId, e.what());
    }
    
    return activeTasks;
}

bool ComputeNodeSchedulerManager::registerNode(const ComputeNodeInfo& nodeInfo) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        // Register node with all schedulers
        bool registered = true;
        for (const auto& scheduler : schedulers_) {
            if (scheduler.second) {
                if (!scheduler.second->registerNode(nodeInfo)) {
                    registered = false;
                }
            }
        }
        
        if (registered) {
            spdlog::info("Compute node {} registered with all schedulers", nodeInfo.nodeId);
        } else {
            spdlog::error("Failed to register compute node {} with some schedulers", nodeInfo.nodeId);
        }
        
        return registered;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to register compute node {}: {}", nodeInfo.nodeId, e.what());
        return false;
    }
}

bool ComputeNodeSchedulerManager::unregisterNode(const std::string& nodeId) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        // Unregister node from all schedulers
        bool unregistered = true;
        for (const auto& scheduler : schedulers_) {
            if (scheduler.second) {
                if (!scheduler.second->unregisterNode(nodeId)) {
                    unregistered = false;
                }
            }
        }
        
        if (unregistered) {
            spdlog::info("Compute node {} unregistered from all schedulers", nodeId);
        } else {
            spdlog::error("Failed to unregister compute node {} from some schedulers", nodeId);
        }
        
        return unregistered;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to unregister compute node {}: {}", nodeId, e.what());
        return false;
    }
}

std::vector<ComputeNodeInfo> ComputeNodeSchedulerManager::getAvailableNodes() {
    std::vector<ComputeNodeInfo> availableNodes;
    
    try {
        for (const auto& scheduler : schedulers_) {
            if (scheduler.second) {
                auto schedulerNodes = scheduler.second->getAvailableNodes();
                availableNodes.insert(availableNodes.end(), schedulerNodes.begin(), schedulerNodes.end());
            }
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get available nodes: {}", e.what());
    }
    
    return availableNodes;
}

ComputeNodeInfo ComputeNodeSchedulerManager::getNodeInfo(const std::string& nodeId) {
    ComputeNodeInfo nodeInfo;
    
    try {
        for (const auto& scheduler : schedulers_) {
            if (scheduler.second) {
                auto info = scheduler.second->getNodeInfo(nodeId);
                if (!info.nodeId.empty()) {
                    nodeInfo = info;
                    break;
                }
            }
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get node info for node {}: {}", nodeId, e.what());
    }
    
    return nodeInfo;
}

bool ComputeNodeSchedulerManager::optimizeSystem() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Optimizing compute node scheduler system");
        
        for (const auto& scheduler : schedulers_) {
            if (scheduler.second) {
                auto advancedScheduler = std::dynamic_pointer_cast<AdvancedComputeNodeScheduler>(scheduler.second);
                if (advancedScheduler) {
                    advancedScheduler->optimizeScheduling();
                }
            }
        }
        
        updateSystemMetrics();
        
        spdlog::info("System optimization completed");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to optimize system: {}", e.what());
        return false;
    }
}

bool ComputeNodeSchedulerManager::balanceLoad() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Balancing load across compute node schedulers");
        
        std::vector<std::shared_ptr<ComputeNodeScheduler>> activeSchedulers;
        for (const auto& scheduler : schedulers_) {
            if (scheduler.second && scheduler.second->isInitialized()) {
                activeSchedulers.push_back(scheduler.second);
            }
        }
        
        if (activeSchedulers.empty()) {
            spdlog::warn("No active schedulers found for load balancing");
            return true;
        }
        
        // Calculate average utilization
        float totalUtilization = 0.0f;
        for (const auto& scheduler : activeSchedulers) {
            totalUtilization += scheduler->getUtilization();
        }
        float averageUtilization = totalUtilization / activeSchedulers.size();
        
        // Balance load (simplified implementation)
        for (const auto& scheduler : activeSchedulers) {
            float utilization = scheduler->getUtilization();
            if (utilization > averageUtilization * 1.2f) {
                spdlog::debug("Scheduler {} is overloaded (utilization: {:.2f})", 
                            scheduler->getSchedulerId(), utilization);
            } else if (utilization < averageUtilization * 0.8f) {
                spdlog::debug("Scheduler {} is underloaded (utilization: {:.2f})", 
                            scheduler->getSchedulerId(), utilization);
            }
        }
        
        spdlog::info("Load balancing completed");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to balance load: {}", e.what());
        return false;
    }
}

bool ComputeNodeSchedulerManager::cleanupIdleSchedulers() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Cleaning up idle compute node schedulers");
        
        std::vector<std::string> idleSchedulers;
        for (const auto& scheduler : schedulers_) {
            if (scheduler.second && !scheduler.second->isInitialized()) {
                idleSchedulers.push_back(scheduler.first);
            }
        }
        
        for (const auto& schedulerId : idleSchedulers) {
            spdlog::info("Cleaning up idle scheduler: {}", schedulerId);
            cleanupScheduler(schedulerId);
        }
        
        spdlog::info("Cleaned up {} idle schedulers", idleSchedulers.size());
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cleanup idle schedulers: {}", e.what());
        return false;
    }
}

bool ComputeNodeSchedulerManager::validateSystem() {
    std::lock_guard<std::mutex> lock(managerMutex_);
    
    if (!initialized_) {
        spdlog::error("Manager not initialized");
        return false;
    }
    
    try {
        spdlog::info("Validating compute node scheduler system");
        
        bool isValid = true;
        
        for (const auto& scheduler : schedulers_) {
            if (scheduler.second) {
                auto advancedScheduler = std::dynamic_pointer_cast<AdvancedComputeNodeScheduler>(scheduler.second);
                if (advancedScheduler && !advancedScheduler->validateConfiguration()) {
                    spdlog::error("Scheduler {} failed validation", scheduler.first);
                    isValid = false;
                }
            }
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

std::map<std::string, double> ComputeNodeSchedulerManager::getSystemMetrics() {
    std::map<std::string, double> metrics;
    
    try {
        updateSystemMetrics();
        
        metrics["total_schedulers"] = static_cast<double>(schedulers_.size());
        metrics["active_tasks"] = static_cast<double>(taskToScheduler_.size());
        metrics["scheduling_strategy"] = static_cast<double>(schedulingStrategy_.length());
        metrics["load_balancing_strategy"] = static_cast<double>(loadBalancingStrategy_.length());
        
        // Calculate average utilization
        double totalUtilization = 0.0;
        int schedulerCount = 0;
        for (const auto& scheduler : schedulers_) {
            if (scheduler.second) {
                totalUtilization += scheduler.second->getUtilization();
                schedulerCount++;
            }
        }
        if (schedulerCount > 0) {
            metrics["average_utilization"] = totalUtilization / schedulerCount;
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get system metrics: {}", e.what());
    }
    
    return metrics;
}

std::map<std::string, int> ComputeNodeSchedulerManager::getSchedulerCounts() {
    std::map<std::string, int> counts;
    
    try {
        counts["total"] = static_cast<int>(schedulers_.size());
        counts["fifo"] = 0;
        counts["priority"] = 0;
        counts["weighted"] = 0;
        counts["round_robin"] = 0;
        counts["least_loaded"] = 0;
        counts["custom"] = 0;
        
        for (const auto& scheduler : schedulers_) {
            if (scheduler.second) {
                switch (scheduler.second->getSchedulerType()) {
                    case SchedulerType::FIFO:
                        counts["fifo"]++;
                        break;
                    case SchedulerType::PRIORITY:
                        counts["priority"]++;
                        break;
                    case SchedulerType::WEIGHTED:
                        counts["weighted"]++;
                        break;
                    case SchedulerType::ROUND_ROBIN:
                        counts["round_robin"]++;
                        break;
                    case SchedulerType::LEAST_LOADED:
                        counts["least_loaded"]++;
                        break;
                    case SchedulerType::CUSTOM:
                        counts["custom"]++;
                        break;
                    default:
                        break;
                }
            }
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get scheduler counts: {}", e.what());
    }
    
    return counts;
}

std::map<std::string, double> ComputeNodeSchedulerManager::getTaskMetrics() {
    std::map<std::string, double> metrics;
    
    try {
        // Calculate task metrics
        metrics["total_tasks"] = static_cast<double>(taskToScheduler_.size());
        metrics["active_tasks"] = static_cast<double>(taskToScheduler_.size());
        
        // Calculate average execution time and utilization
        double totalExecutionTime = 0.0;
        double totalUtilization = 0.0;
        int schedulerCount = 0;
        for (const auto& scheduler : schedulers_) {
            if (scheduler.second) {
                auto schedulerMetrics = scheduler.second->getPerformanceMetrics();
                totalExecutionTime += schedulerMetrics.at("average_execution_time");
                totalUtilization += scheduler.second->getUtilization();
                schedulerCount++;
            }
        }
        if (schedulerCount > 0) {
            metrics["average_execution_time"] = totalExecutionTime / schedulerCount;
            metrics["average_utilization"] = totalUtilization / schedulerCount;
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get task metrics: {}", e.what());
    }
    
    return metrics;
}

bool ComputeNodeSchedulerManager::enableSystemProfiling() {
    systemProfilingEnabled_ = true;
    spdlog::info("System profiling enabled");
    return true;
}

bool ComputeNodeSchedulerManager::disableSystemProfiling() {
    systemProfilingEnabled_ = false;
    spdlog::info("System profiling disabled");
    return true;
}

std::map<std::string, double> ComputeNodeSchedulerManager::getSystemProfilingData() {
    std::map<std::string, double> profilingData;
    
    if (!systemProfilingEnabled_) {
        return profilingData;
    }
    
    try {
        auto metrics = getSystemMetrics();
        auto taskMetrics = getTaskMetrics();
        
        profilingData.insert(metrics.begin(), metrics.end());
        profilingData.insert(taskMetrics.begin(), taskMetrics.end());
        
        profilingData["profiling_enabled"] = systemProfilingEnabled_ ? 1.0 : 0.0;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get system profiling data: {}", e.what());
    }
    
    return profilingData;
}

void ComputeNodeSchedulerManager::setMaxSchedulers(int maxSchedulers) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    maxSchedulers_ = maxSchedulers;
    spdlog::info("Set maximum schedulers to: {}", maxSchedulers);
}

int ComputeNodeSchedulerManager::getMaxSchedulers() const {
    return maxSchedulers_;
}

void ComputeNodeSchedulerManager::setSchedulingStrategy(const std::string& strategy) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    schedulingStrategy_ = strategy;
    spdlog::info("Set scheduling strategy to: {}", strategy);
}

std::string ComputeNodeSchedulerManager::getSchedulingStrategy() const {
    return schedulingStrategy_;
}

void ComputeNodeSchedulerManager::setLoadBalancingStrategy(const std::string& strategy) {
    std::lock_guard<std::mutex> lock(managerMutex_);
    loadBalancingStrategy_ = strategy;
    spdlog::info("Set load balancing strategy to: {}", strategy);
}

std::string ComputeNodeSchedulerManager::getLoadBalancingStrategy() const {
    return loadBalancingStrategy_;
}

bool ComputeNodeSchedulerManager::validateSchedulerCreation(const SchedulerConfig& config) {
    try {
        if (config.schedulerId.empty()) {
            spdlog::error("Scheduler ID cannot be empty");
            return false;
        }
        
        if (config.maxQueueSize <= 0) {
            spdlog::error("Max queue size must be greater than 0");
            return false;
        }
        
        if (config.maxConcurrentTasks <= 0) {
            spdlog::error("Max concurrent tasks must be greater than 0");
            return false;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to validate scheduler creation: {}", e.what());
        return false;
    }
}

bool ComputeNodeSchedulerManager::validateTaskSubmission(const TaskExecutionRequest& request) {
    try {
        if (request.requestId.empty()) {
            spdlog::error("Request ID cannot be empty");
            return false;
        }
        
        if (request.taskId.empty()) {
            spdlog::error("Task ID cannot be empty");
            return false;
        }
        
        if (!request.taskFunction) {
            spdlog::error("Task function cannot be null");
            return false;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to validate task submission: {}", e.what());
        return false;
    }
}

std::string ComputeNodeSchedulerManager::generateSchedulerId() {
    try {
        std::stringstream ss;
        ss << "scheduler_" << std::chrono::system_clock::now().time_since_epoch().count();
        return ss.str();
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to generate scheduler ID: {}", e.what());
        return "scheduler_" + std::to_string(std::chrono::system_clock::now().time_since_epoch().count());
    }
}

bool ComputeNodeSchedulerManager::cleanupScheduler(const std::string& schedulerId) {
    try {
        auto scheduler = getScheduler(schedulerId);
        if (!scheduler) {
            spdlog::error("Scheduler {} not found for cleanup", schedulerId);
            return false;
        }
        
        scheduler->shutdown();
        schedulers_.erase(schedulerId);
        
        spdlog::info("Cleaned up scheduler: {}", schedulerId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cleanup scheduler {}: {}", schedulerId, e.what());
        return false;
    }
}

void ComputeNodeSchedulerManager::updateSystemMetrics() {
    try {
        // Update system metrics
        // Implementation depends on specific metrics to track
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to update system metrics: {}", e.what());
    }
}

bool ComputeNodeSchedulerManager::findBestScheduler(const TaskExecutionRequest& request, std::string& bestSchedulerId) {
    try {
        // Find best scheduler based on load balancing strategy
        if (loadBalancingStrategy_ == "round_robin") {
            // Round-robin selection
            static size_t currentIndex = 0;
            auto schedulerList = getAllSchedulers();
            if (!schedulerList.empty()) {
                bestSchedulerId = schedulerList[currentIndex % schedulerList.size()]->getSchedulerId();
                currentIndex++;
                return true;
            }
        } else if (loadBalancingStrategy_ == "least_loaded") {
            // Least loaded selection
            auto schedulerList = getAllSchedulers();
            if (!schedulerList.empty()) {
                float minUtilization = 1.0f;
                for (const auto& scheduler : schedulerList) {
                    if (scheduler->getUtilization() < minUtilization) {
                        minUtilization = scheduler->getUtilization();
                        bestSchedulerId = scheduler->getSchedulerId();
                    }
                }
                return true;
            }
        }
        
        return false;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to find best scheduler: {}", e.what());
        return false;
    }
}

bool ComputeNodeSchedulerManager::executeOnScheduler(const std::string& schedulerId, const TaskExecutionRequest& request) {
    try {
        auto scheduler = getScheduler(schedulerId);
        if (!scheduler) {
            spdlog::error("Scheduler {} not found", schedulerId);
            return false;
        }
        
        auto result = scheduler->submitTask(request);
        return result.success;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to execute on scheduler {}: {}", schedulerId, e.what());
        return false;
    }
}

std::vector<std::string> ComputeNodeSchedulerManager::selectSchedulersForTask(const TaskExecutionRequest& request) {
    std::vector<std::string> selectedSchedulers;
    
    try {
        auto allSchedulers = getAllSchedulers();
        if (allSchedulers.empty()) {
            return selectedSchedulers;
        }
        
        // Select schedulers based on task requirements
        for (const auto& scheduler : allSchedulers) {
            if (scheduler) {
                // Simple selection based on scheduler type
                if (scheduler->getSchedulerType() == SchedulerType::FIFO || 
                    scheduler->getSchedulerType() == SchedulerType::PRIORITY) {
                    selectedSchedulers.push_back(scheduler->getSchedulerId());
                }
            }
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to select schedulers for task: {}", e.what());
    }
    
    return selectedSchedulers;
}

bool ComputeNodeSchedulerManager::validateSystemConfiguration() {
    try {
        // Validate system configuration
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to validate system configuration: {}", e.what());
        return false;
    }
}

bool ComputeNodeSchedulerManager::optimizeSystemConfiguration() {
    try {
        // Optimize system configuration
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to optimize system configuration: {}", e.what());
        return false;
    }
}

bool ComputeNodeSchedulerManager::balanceSystemLoad() {
    try {
        // Balance system load
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to balance system load: {}", e.what());
        return false;
    }
}

} // namespace scheduler
} // namespace cogniware
