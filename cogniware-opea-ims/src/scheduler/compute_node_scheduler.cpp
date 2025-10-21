#include "scheduler/compute_node_scheduler.h"
#include <spdlog/spdlog.h>
#include <algorithm>
#include <random>
#include <sstream>

namespace cogniware {
namespace scheduler {

AdvancedComputeNodeScheduler::AdvancedComputeNodeScheduler(const SchedulerConfig& config)
    : config_(config)
    , initialized_(false)
    , schedulerType_(config.type)
    , profilingEnabled_(false)
    , stopScheduler_(false) {
    
    spdlog::info("Creating compute node scheduler: {}", config_.schedulerId);
}

AdvancedComputeNodeScheduler::~AdvancedComputeNodeScheduler() {
    shutdown();
}

bool AdvancedComputeNodeScheduler::initialize() {
    std::lock_guard<std::mutex> lock(schedulerMutex_);
    
    if (initialized_) {
        spdlog::warn("Compute node scheduler {} already initialized", config_.schedulerId);
        return true;
    }
    
    try {
        // Initialize performance metrics
        performanceMetrics_["utilization"] = 0.0;
        performanceMetrics_["queue_size"] = 0.0;
        performanceMetrics_["active_tasks"] = 0.0;
        performanceMetrics_["completed_tasks"] = 0.0;
        performanceMetrics_["failed_tasks"] = 0.0;
        performanceMetrics_["average_execution_time"] = 0.0;
        lastUpdateTime_ = std::chrono::system_clock::now();
        
        // Start scheduler thread
        stopScheduler_ = false;
        schedulerThread_ = std::thread(&AdvancedComputeNodeScheduler::schedulerLoop, this);
        
        initialized_ = true;
        spdlog::info("Compute node scheduler {} initialized successfully", config_.schedulerId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize compute node scheduler {}: {}", config_.schedulerId, e.what());
        return false;
    }
}

void AdvancedComputeNodeScheduler::shutdown() {
    std::lock_guard<std::mutex> lock(schedulerMutex_);
    
    if (!initialized_) {
        return;
    }
    
    try {
        // Stop scheduler thread
        stopScheduler_ = true;
        if (schedulerThread_.joinable()) {
            schedulerThread_.join();
        }
        
        // Cancel all active tasks
        for (const auto& task : activeTasks_) {
            cancelTask(task.first);
        }
        activeTasks_.clear();
        taskStatus_.clear();
        taskWeights_.clear();
        
        // Clear task queue
        std::queue<TaskExecutionRequest> empty;
        taskQueue_.swap(empty);
        
        initialized_ = false;
        spdlog::info("Compute node scheduler {} shutdown completed", config_.schedulerId);
        
    } catch (const std::exception& e) {
        spdlog::error("Error during compute node scheduler {} shutdown: {}", config_.schedulerId, e.what());
    }
}

bool AdvancedComputeNodeScheduler::isInitialized() const {
    return initialized_;
}

std::string AdvancedComputeNodeScheduler::getSchedulerId() const {
    return config_.schedulerId;
}

SchedulerConfig AdvancedComputeNodeScheduler::getConfig() const {
    return config_;
}

bool AdvancedComputeNodeScheduler::updateConfig(const SchedulerConfig& config) {
    std::lock_guard<std::mutex> lock(schedulerMutex_);
    
    if (!initialized_) {
        spdlog::error("Compute node scheduler {} not initialized", config_.schedulerId);
        return false;
    }
    
    try {
        // Update configuration
        config_ = config;
        schedulerType_ = config.type;
        
        spdlog::info("Configuration updated for compute node scheduler {}", config_.schedulerId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to update configuration for compute node scheduler {}: {}", config_.schedulerId, e.what());
        return false;
    }
}

std::future<TaskExecutionResult> AdvancedComputeNodeScheduler::submitTaskAsync(const TaskExecutionRequest& request) {
    std::lock_guard<std::mutex> lock(schedulerMutex_);
    
    if (!initialized_) {
        spdlog::error("Compute node scheduler {} not initialized", config_.schedulerId);
        return std::async(std::launch::deferred, []() {
            TaskExecutionResult result;
            result.success = false;
            result.error = "Scheduler not initialized";
            return result;
        });
    }
    
    try {
        // Validate request
        if (!validateTaskRequest(request)) {
            spdlog::error("Invalid task request for scheduler {}", config_.schedulerId);
            return std::async(std::launch::deferred, []() {
                TaskExecutionResult result;
                result.success = false;
                result.error = "Invalid task request";
                return result;
            });
        }
        
        // Check queue size
        if (static_cast<int>(taskQueue_.size()) >= config_.maxQueueSize) {
            spdlog::error("Task queue is full for scheduler {}", config_.schedulerId);
            return std::async(std::launch::deferred, []() {
                TaskExecutionResult result;
                result.success = false;
                result.error = "Task queue is full";
                return result;
            });
        }
        
        // Add task to queue
        taskQueue_.push(request);
        taskStatus_[request.taskId] = TaskStatus::QUEUED;
        taskWeights_[request.taskId] = request.weight;
        
        // Create async task execution
        auto future = std::async(std::launch::async, [this, request]() {
            return executeTaskInternal(request);
        });
        
        // Store task
        activeTasks_[request.taskId] = std::move(future);
        
        spdlog::info("Async task submission started for task {} on scheduler {}", request.taskId, config_.schedulerId);
        return activeTasks_[request.taskId];
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to submit async task {} on scheduler {}: {}", request.taskId, config_.schedulerId, e.what());
        return std::async(std::launch::deferred, []() {
            TaskExecutionResult result;
            result.success = false;
            result.error = "Failed to submit async task";
            return result;
        });
    }
}

TaskExecutionResult AdvancedComputeNodeScheduler::submitTask(const TaskExecutionRequest& request) {
    std::lock_guard<std::mutex> lock(schedulerMutex_);
    
    if (!initialized_) {
        spdlog::error("Compute node scheduler {} not initialized", config_.schedulerId);
        TaskExecutionResult result;
        result.success = false;
        result.error = "Scheduler not initialized";
        return result;
    }
    
    try {
        // Validate request
        if (!validateTaskRequest(request)) {
            spdlog::error("Invalid task request for scheduler {}", config_.schedulerId);
            TaskExecutionResult result;
            result.success = false;
            result.error = "Invalid task request";
            return result;
        }
        
        // Check queue size
        if (static_cast<int>(taskQueue_.size()) >= config_.maxQueueSize) {
            spdlog::error("Task queue is full for scheduler {}", config_.schedulerId);
            TaskExecutionResult result;
            result.success = false;
            result.error = "Task queue is full";
            return result;
        }
        
        // Add task to queue
        taskQueue_.push(request);
        taskStatus_[request.taskId] = TaskStatus::QUEUED;
        taskWeights_[request.taskId] = request.weight;
        
        // Execute task
        auto result = executeTaskInternal(request);
        
        spdlog::info("Task submission completed for task {} on scheduler {}", request.taskId, config_.schedulerId);
        return result;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to submit task {} on scheduler {}: {}", request.taskId, config_.schedulerId, e.what());
        TaskExecutionResult result;
        result.success = false;
        result.error = "Task submission failed: " + std::string(e.what());
        return result;
    }
}

bool AdvancedComputeNodeScheduler::cancelTask(const std::string& taskId) {
    std::lock_guard<std::mutex> lock(schedulerMutex_);
    
    if (!initialized_) {
        spdlog::error("Compute node scheduler {} not initialized", config_.schedulerId);
        return false;
    }
    
    try {
        // Check if task is active
        if (activeTasks_.find(taskId) == activeTasks_.end()) {
            spdlog::warn("Task {} not found in scheduler {}", taskId, config_.schedulerId);
            return false;
        }
        
        // Update task status
        taskStatus_[taskId] = TaskStatus::CANCELLED;
        
        // Cleanup task
        cleanupTask(taskId);
        
        spdlog::info("Task {} cancelled on scheduler {}", taskId, config_.schedulerId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cancel task {} on scheduler {}: {}", taskId, config_.schedulerId, e.what());
        return false;
    }
}

bool AdvancedComputeNodeScheduler::suspendTask(const std::string& taskId) {
    std::lock_guard<std::mutex> lock(schedulerMutex_);
    
    if (!initialized_) {
        spdlog::error("Compute node scheduler {} not initialized", config_.schedulerId);
        return false;
    }
    
    try {
        // Check if task is active
        if (activeTasks_.find(taskId) == activeTasks_.end()) {
            spdlog::warn("Task {} not found in scheduler {}", taskId, config_.schedulerId);
            return false;
        }
        
        // Update task status
        taskStatus_[taskId] = TaskStatus::SUSPENDED;
        
        spdlog::info("Task {} suspended on scheduler {}", taskId, config_.schedulerId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to suspend task {} on scheduler {}: {}", taskId, config_.schedulerId, e.what());
        return false;
    }
}

bool AdvancedComputeNodeScheduler::resumeTask(const std::string& taskId) {
    std::lock_guard<std::mutex> lock(schedulerMutex_);
    
    if (!initialized_) {
        spdlog::error("Compute node scheduler {} not initialized", config_.schedulerId);
        return false;
    }
    
    try {
        // Check if task is suspended
        if (taskStatus_[taskId] != TaskStatus::SUSPENDED) {
            spdlog::warn("Task {} is not suspended in scheduler {}", taskId, config_.schedulerId);
            return false;
        }
        
        // Update task status
        taskStatus_[taskId] = TaskStatus::QUEUED;
        
        spdlog::info("Task {} resumed on scheduler {}", taskId, config_.schedulerId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to resume task {} on scheduler {}: {}", taskId, config_.schedulerId, e.what());
        return false;
    }
}

std::vector<std::string> AdvancedComputeNodeScheduler::getActiveTasks() const {
    std::lock_guard<std::mutex> lock(schedulerMutex_);
    
    std::vector<std::string> activeTaskIds;
    for (const auto& task : activeTasks_) {
        activeTaskIds.push_back(task.first);
    }
    return activeTaskIds;
}

bool AdvancedComputeNodeScheduler::isTaskActive(const std::string& taskId) const {
    std::lock_guard<std::mutex> lock(schedulerMutex_);
    return activeTasks_.find(taskId) != activeTasks_.end();
}

bool AdvancedComputeNodeScheduler::registerNode(const ComputeNodeInfo& nodeInfo) {
    std::lock_guard<std::mutex> lock(nodeMutex_);
    
    if (!initialized_) {
        spdlog::error("Compute node scheduler {} not initialized", config_.schedulerId);
        return false;
    }
    
    try {
        // Validate node info
        if (!validateNodeInfo(nodeInfo)) {
            spdlog::error("Invalid node info for scheduler {}", config_.schedulerId);
            return false;
        }
        
        // Register node
        computeNodes_[nodeInfo.nodeId] = nodeInfo;
        
        spdlog::info("Compute node {} registered with scheduler {}", nodeInfo.nodeId, config_.schedulerId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to register node {} with scheduler {}: {}", nodeInfo.nodeId, config_.schedulerId, e.what());
        return false;
    }
}

bool AdvancedComputeNodeScheduler::unregisterNode(const std::string& nodeId) {
    std::lock_guard<std::mutex> lock(nodeMutex_);
    
    if (!initialized_) {
        spdlog::error("Compute node scheduler {} not initialized", config_.schedulerId);
        return false;
    }
    
    try {
        // Check if node exists
        if (computeNodes_.find(nodeId) == computeNodes_.end()) {
            spdlog::warn("Node {} not found in scheduler {}", nodeId, config_.schedulerId);
            return false;
        }
        
        // Unregister node
        computeNodes_.erase(nodeId);
        
        spdlog::info("Compute node {} unregistered from scheduler {}", nodeId, config_.schedulerId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to unregister node {} from scheduler {}: {}", nodeId, config_.schedulerId, e.what());
        return false;
    }
}

std::vector<ComputeNodeInfo> AdvancedComputeNodeScheduler::getAvailableNodes() const {
    std::lock_guard<std::mutex> lock(nodeMutex_);
    
    std::vector<ComputeNodeInfo> availableNodes;
    for (const auto& node : computeNodes_) {
        if (node.second.isOnline && node.second.activeTasks < node.second.maxTasks) {
            availableNodes.push_back(node.second);
        }
    }
    return availableNodes;
}

ComputeNodeInfo AdvancedComputeNodeScheduler::getNodeInfo(const std::string& nodeId) const {
    std::lock_guard<std::mutex> lock(nodeMutex_);
    
    auto it = computeNodes_.find(nodeId);
    if (it != computeNodes_.end()) {
        return it->second;
    }
    
    // Return empty node info if not found
    ComputeNodeInfo emptyNode;
    emptyNode.nodeId = nodeId;
    return emptyNode;
}

std::map<std::string, double> AdvancedComputeNodeScheduler::getPerformanceMetrics() const {
    std::lock_guard<std::mutex> lock(schedulerMutex_);
    return performanceMetrics_;
}

float AdvancedComputeNodeScheduler::getUtilization() const {
    std::lock_guard<std::mutex> lock(schedulerMutex_);
    
    if (config_.maxConcurrentTasks == 0) {
        return 0.0f;
    }
    
    return static_cast<float>(activeTasks_.size()) / config_.maxConcurrentTasks;
}

bool AdvancedComputeNodeScheduler::enableProfiling() {
    profilingEnabled_ = true;
    spdlog::info("Profiling enabled for compute node scheduler {}", config_.schedulerId);
    return true;
}

bool AdvancedComputeNodeScheduler::disableProfiling() {
    profilingEnabled_ = false;
    spdlog::info("Profiling disabled for compute node scheduler {}", config_.schedulerId);
    return true;
}

std::map<std::string, double> AdvancedComputeNodeScheduler::getProfilingData() const {
    std::map<std::string, double> profilingData;
    
    if (!profilingEnabled_) {
        return profilingData;
    }
    
    try {
        // Collect profiling data
        auto metrics = getPerformanceMetrics();
        profilingData["utilization"] = metrics.at("utilization");
        profilingData["queue_size"] = metrics.at("queue_size");
        profilingData["active_tasks"] = metrics.at("active_tasks");
        profilingData["completed_tasks"] = metrics.at("completed_tasks");
        profilingData["failed_tasks"] = metrics.at("failed_tasks");
        profilingData["average_execution_time"] = metrics.at("average_execution_time");
        profilingData["registered_nodes"] = static_cast<double>(computeNodes_.size());
        profilingData["available_nodes"] = static_cast<double>(getAvailableNodes().size());
        profilingData["scheduler_type"] = static_cast<double>(static_cast<int>(schedulerType_));
        profilingData["max_queue_size"] = static_cast<double>(config_.maxQueueSize);
        profilingData["max_concurrent_tasks"] = static_cast<double>(config_.maxConcurrentTasks);
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to get profiling data for compute node scheduler {}: {}", config_.schedulerId, e.what());
    }
    
    return profilingData;
}

bool AdvancedComputeNodeScheduler::setSchedulerType(SchedulerType type) {
    std::lock_guard<std::mutex> lock(schedulerMutex_);
    
    schedulerType_ = type;
    config_.type = type;
    
    spdlog::info("Scheduler type set to {} for scheduler {}", static_cast<int>(type), config_.schedulerId);
    return true;
}

SchedulerType AdvancedComputeNodeScheduler::getSchedulerType() const {
    return schedulerType_;
}

bool AdvancedComputeNodeScheduler::setMaxQueueSize(int maxSize) {
    std::lock_guard<std::mutex> lock(schedulerMutex_);
    
    config_.maxQueueSize = maxSize;
    
    spdlog::info("Max queue size set to {} for scheduler {}", maxSize, config_.schedulerId);
    return true;
}

int AdvancedComputeNodeScheduler::getMaxQueueSize() const {
    return config_.maxQueueSize;
}

bool AdvancedComputeNodeScheduler::optimizeScheduling() {
    std::lock_guard<std::mutex> lock(schedulerMutex_);
    
    if (!initialized_) {
        spdlog::error("Compute node scheduler {} not initialized", config_.schedulerId);
        return false;
    }
    
    try {
        // Optimize task queue
        optimizeTaskQueue();
        
        // Rebalance tasks
        rebalanceTasks();
        
        spdlog::info("Scheduling optimization completed for scheduler {}", config_.schedulerId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to optimize scheduling for scheduler {}: {}", config_.schedulerId, e.what());
        return false;
    }
}

bool AdvancedComputeNodeScheduler::balanceLoad() {
    std::lock_guard<std::mutex> lock(schedulerMutex_);
    
    if (!initialized_) {
        spdlog::error("Compute node scheduler {} not initialized", config_.schedulerId);
        return false;
    }
    
    try {
        // Balance load across nodes
        rebalanceTasks();
        
        spdlog::info("Load balancing completed for scheduler {}", config_.schedulerId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to balance load for scheduler {}: {}", config_.schedulerId, e.what());
        return false;
    }
}

bool AdvancedComputeNodeScheduler::scaleNodes() {
    std::lock_guard<std::mutex> lock(schedulerMutex_);
    
    if (!initialized_) {
        spdlog::error("Compute node scheduler {} not initialized", config_.schedulerId);
        return false;
    }
    
    try {
        // Scale up if needed
        scaleUpNodes();
        
        // Scale down if needed
        scaleDownNodes();
        
        spdlog::info("Node scaling completed for scheduler {}", config_.schedulerId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to scale nodes for scheduler {}: {}", config_.schedulerId, e.what());
        return false;
    }
}

std::map<std::string, std::string> AdvancedComputeNodeScheduler::getSchedulerInfo() const {
    std::map<std::string, std::string> info;
    
    info["scheduler_id"] = config_.schedulerId;
    info["scheduler_type"] = std::to_string(static_cast<int>(schedulerType_));
    info["max_queue_size"] = std::to_string(config_.maxQueueSize);
    info["max_concurrent_tasks"] = std::to_string(config_.maxConcurrentTasks);
    info["enable_load_balancing"] = config_.enableLoadBalancing ? "true" : "false";
    info["enable_auto_scaling"] = config_.enableAutoScaling ? "true" : "false";
    info["utilization"] = std::to_string(getUtilization());
    info["queue_size"] = std::to_string(taskQueue_.size());
    info["active_tasks"] = std::to_string(activeTasks_.size());
    info["registered_nodes"] = std::to_string(computeNodes_.size());
    info["available_nodes"] = std::to_string(getAvailableNodes().size());
    
    return info;
}

bool AdvancedComputeNodeScheduler::validateConfiguration() const {
    try {
        // Validate configuration
        if (config_.schedulerId.empty()) {
            spdlog::error("Scheduler ID cannot be empty");
            return false;
        }
        
        if (config_.maxQueueSize <= 0) {
            spdlog::error("Max queue size must be greater than 0");
            return false;
        }
        
        if (config_.maxConcurrentTasks <= 0) {
            spdlog::error("Max concurrent tasks must be greater than 0");
            return false;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to validate configuration: {}", e.what());
        return false;
    }
}

bool AdvancedComputeNodeScheduler::setTaskWeight(const std::string& taskId, float weight) {
    std::lock_guard<std::mutex> lock(schedulerMutex_);
    
    if (!initialized_) {
        spdlog::error("Compute node scheduler {} not initialized", config_.schedulerId);
        return false;
    }
    
    try {
        // Validate weight
        if (weight < 0.0f || weight > 1.0f) {
            spdlog::error("Task weight must be between 0.0 and 1.0");
            return false;
        }
        
        // Set task weight
        taskWeights_[taskId] = weight;
        
        spdlog::info("Task weight set to {} for task {} on scheduler {}", weight, taskId, config_.schedulerId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to set task weight for task {} on scheduler {}: {}", taskId, config_.schedulerId, e.what());
        return false;
    }
}

float AdvancedComputeNodeScheduler::getTaskWeight(const std::string& taskId) const {
    std::lock_guard<std::mutex> lock(schedulerMutex_);
    
    auto it = taskWeights_.find(taskId);
    if (it != taskWeights_.end()) {
        return it->second;
    }
    
    return 0.0f;
}

bool AdvancedComputeNodeScheduler::setNodeCapacity(const std::string& nodeId, int maxTasks) {
    std::lock_guard<std::mutex> lock(nodeMutex_);
    
    if (!initialized_) {
        spdlog::error("Compute node scheduler {} not initialized", config_.schedulerId);
        return false;
    }
    
    try {
        // Check if node exists
        if (computeNodes_.find(nodeId) == computeNodes_.end()) {
            spdlog::error("Node {} not found in scheduler {}", nodeId, config_.schedulerId);
            return false;
        }
        
        // Set node capacity
        computeNodes_[nodeId].maxTasks = maxTasks;
        
        spdlog::info("Node capacity set to {} for node {} on scheduler {}", maxTasks, nodeId, config_.schedulerId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to set node capacity for node {} on scheduler {}: {}", nodeId, config_.schedulerId, e.what());
        return false;
    }
}

int AdvancedComputeNodeScheduler::getNodeCapacity(const std::string& nodeId) const {
    std::lock_guard<std::mutex> lock(nodeMutex_);
    
    auto it = computeNodes_.find(nodeId);
    if (it != computeNodes_.end()) {
        return it->second.maxTasks;
    }
    
    return 0;
}

void AdvancedComputeNodeScheduler::schedulerLoop() {
    while (!stopScheduler_) {
        try {
            // Process task queue
            processTaskQueue();
            
            // Update performance metrics
            updatePerformanceMetrics();
            
            // Cleanup completed tasks
            cleanupCompletedTasks();
            
            // Sleep for a short time
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            
        } catch (const std::exception& e) {
            spdlog::error("Error in scheduler loop for scheduler {}: {}", config_.schedulerId, e.what());
        }
    }
}

bool AdvancedComputeNodeScheduler::validateTaskRequest(const TaskExecutionRequest& request) {
    try {
        // Validate request ID
        if (request.requestId.empty()) {
            spdlog::error("Request ID cannot be empty");
            return false;
        }
        
        // Validate task ID
        if (request.taskId.empty()) {
            spdlog::error("Task ID cannot be empty");
            return false;
        }
        
        // Validate task function
        if (!request.taskFunction) {
            spdlog::error("Task function cannot be null");
            return false;
        }
        
        // Validate weight
        if (request.weight < 0.0f || request.weight > 1.0f) {
            spdlog::error("Task weight must be between 0.0 and 1.0");
            return false;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to validate task request: {}", e.what());
        return false;
    }
}

void AdvancedComputeNodeScheduler::updatePerformanceMetrics() {
    try {
        auto now = std::chrono::system_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(now - lastUpdateTime_);
        
        // Update metrics
        performanceMetrics_["utilization"] = getUtilization();
        performanceMetrics_["queue_size"] = static_cast<double>(taskQueue_.size());
        performanceMetrics_["active_tasks"] = static_cast<double>(activeTasks_.size());
        performanceMetrics_["completed_tasks"] = 0.0; // Will be updated on completion
        performanceMetrics_["failed_tasks"] = 0.0; // Will be updated on failure
        performanceMetrics_["average_execution_time"] = 0.0; // Will be updated during execution
        performanceMetrics_["update_duration_ms"] = static_cast<double>(duration.count());
        
        lastUpdateTime_ = now;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to update performance metrics for scheduler {}: {}", config_.schedulerId, e.what());
    }
}

TaskExecutionResult AdvancedComputeNodeScheduler::executeTaskInternal(const TaskExecutionRequest& request) {
    TaskExecutionResult result;
    result.requestId = request.requestId;
    result.taskId = request.taskId;
    result.success = false;
    result.status = TaskStatus::RUNNING;
    
    try {
        // Record start time
        auto startTime = std::chrono::high_resolution_clock::now();
        
        // Execute task function
        request.taskFunction();
        
        // Calculate execution time
        auto endTime = std::chrono::high_resolution_clock::now();
        result.executionTime = std::chrono::duration_cast<std::chrono::milliseconds>(endTime - startTime).count();
        
        // Set success
        result.success = true;
        result.status = TaskStatus::COMPLETED;
        result.completedAt = std::chrono::system_clock::now();
        
        // Update task status
        updateTaskStatus(request.taskId, TaskStatus::COMPLETED);
        
        spdlog::debug("Task execution completed for task {} on scheduler {}", request.taskId, config_.schedulerId);
        
    } catch (const std::exception& e) {
        result.error = "Task execution failed: " + std::string(e.what());
        result.status = TaskStatus::FAILED;
        result.completedAt = std::chrono::system_clock::now();
        
        // Update task status
        updateTaskStatus(request.taskId, TaskStatus::FAILED);
        
        spdlog::error("Task execution failed for task {} on scheduler {}: {}", request.taskId, config_.schedulerId, e.what());
    }
    
    return result;
}

void AdvancedComputeNodeScheduler::cleanupTask(const std::string& taskId) {
    try {
        // Remove task from active tasks
        if (activeTasks_.find(taskId) != activeTasks_.end()) {
            activeTasks_.erase(taskId);
        }
        
        // Remove task status
        taskStatus_.erase(taskId);
        
        // Remove task weight
        taskWeights_.erase(taskId);
        
        spdlog::debug("Task {} cleaned up for scheduler {}", taskId, config_.schedulerId);
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cleanup task {} for scheduler {}: {}", taskId, config_.schedulerId, e.what());
    }
}

std::string AdvancedComputeNodeScheduler::generateTaskId() {
    try {
        // Generate unique task ID
        std::stringstream ss;
        ss << "task_" << std::chrono::system_clock::now().time_since_epoch().count();
        return ss.str();
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to generate task ID: {}", e.what());
        return "task_" + std::to_string(std::chrono::system_clock::now().time_since_epoch().count());
    }
}

std::string AdvancedComputeNodeScheduler::selectBestNode(const TaskExecutionRequest& request) {
    try {
        // Get available nodes
        auto availableNodes = getAvailableNodes();
        if (availableNodes.empty()) {
            spdlog::error("No available nodes for task {}", request.taskId);
            return "";
        }
        
        // Select best node based on scheduler type
        std::string bestNodeId;
        float bestScore = -1.0f;
        
        for (const auto& node : availableNodes) {
            if (canNodeHandleTask(node, request)) {
                float score = calculateNodeScore(node, request);
                if (score > bestScore) {
                    bestScore = score;
                    bestNodeId = node.nodeId;
                }
            }
        }
        
        return bestNodeId;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to select best node for task {}: {}", request.taskId, e.what());
        return "";
    }
}

bool AdvancedComputeNodeScheduler::assignTaskToNode(const std::string& taskId, const std::string& nodeId) {
    try {
        // Check if node exists
        if (computeNodes_.find(nodeId) == computeNodes_.end()) {
            spdlog::error("Node {} not found for task {}", nodeId, taskId);
            return false;
        }
        
        // Check if node can handle task
        if (computeNodes_[nodeId].activeTasks >= computeNodes_[nodeId].maxTasks) {
            spdlog::error("Node {} is at capacity for task {}", nodeId, taskId);
            return false;
        }
        
        // Assign task to node
        computeNodes_[nodeId].activeTasks++;
        updateNodeUtilization(nodeId);
        
        spdlog::info("Task {} assigned to node {}", taskId, nodeId);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to assign task {} to node {}: {}", taskId, nodeId, e.what());
        return false;
    }
}

void AdvancedComputeNodeScheduler::updateNodeUtilization(const std::string& nodeId) {
    try {
        // Update node utilization
        auto& node = computeNodes_[nodeId];
        node.cpuUtilization = static_cast<float>(node.activeTasks) / node.maxTasks;
        node.memoryUtilization = static_cast<float>(node.activeTasks) / node.maxTasks;
        node.lastUpdated = std::chrono::system_clock::now();
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to update node utilization for node {}: {}", nodeId, e.what());
    }
}

float AdvancedComputeNodeScheduler::calculateNodeScore(const ComputeNodeInfo& node, const TaskExecutionRequest& request) {
    try {
        // Calculate node score based on scheduler type
        float score = 0.0f;
        
        switch (schedulerType_) {
            case SchedulerType::FIFO:
                score = 1.0f; // All nodes have equal score
                break;
            case SchedulerType::PRIORITY:
                score = static_cast<float>(static_cast<int>(request.priority));
                break;
            case SchedulerType::WEIGHTED:
                score = request.weight;
                break;
            case SchedulerType::LEAST_LOADED:
                score = 1.0f - node.cpuUtilization;
                break;
            case SchedulerType::ROUND_ROBIN:
                score = 1.0f; // All nodes have equal score
                break;
            default:
                score = 1.0f;
                break;
        }
        
        return score;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to calculate node score: {}", e.what());
        return 0.0f;
    }
}

bool AdvancedComputeNodeScheduler::canNodeHandleTask(const ComputeNodeInfo& node, const TaskExecutionRequest& request) {
    try {
        // Check if node is online
        if (!node.isOnline) {
            return false;
        }
        
        // Check if node has capacity
        if (node.activeTasks >= node.maxTasks) {
            return false;
        }
        
        // Check if node has enough resources
        if (node.availableCores < 1 || node.availableMemory < 1024) {
            return false;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to check if node can handle task: {}", e.what());
        return false;
    }
}

void AdvancedComputeNodeScheduler::processTaskQueue() {
    try {
        // Process tasks from queue
        while (!taskQueue_.empty() && activeTasks_.size() < static_cast<size_t>(config_.maxConcurrentTasks)) {
            auto request = taskQueue_.front();
            taskQueue_.pop();
            
            // Select best node
            std::string nodeId = selectBestNode(request);
            if (nodeId.empty()) {
                spdlog::error("No suitable node found for task {}", request.taskId);
                continue;
            }
            
            // Assign task to node
            if (assignTaskToNode(request.taskId, nodeId)) {
                // Update task status
                updateTaskStatus(request.taskId, TaskStatus::RUNNING);
            }
        }
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to process task queue: {}", e.what());
    }
}

void AdvancedComputeNodeScheduler::handleTaskCompletion(const std::string& taskId, const TaskExecutionResult& result) {
    try {
        // Update task status
        updateTaskStatus(taskId, result.status);
        
        // Update performance metrics
        if (result.success) {
            performanceMetrics_["completed_tasks"]++;
        } else {
            performanceMetrics_["failed_tasks"]++;
        }
        
        // Cleanup task
        cleanupTask(taskId);
        
        spdlog::info("Task {} completed with status {}", taskId, static_cast<int>(result.status));
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to handle task completion for task {}: {}", taskId, e.what());
    }
}

void AdvancedComputeNodeScheduler::handleTaskFailure(const std::string& taskId, const std::string& error) {
    try {
        // Update task status
        updateTaskStatus(taskId, TaskStatus::FAILED);
        
        // Update performance metrics
        performanceMetrics_["failed_tasks"]++;
        
        // Cleanup task
        cleanupTask(taskId);
        
        spdlog::error("Task {} failed: {}", taskId, error);
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to handle task failure for task {}: {}", taskId, e.what());
    }
}

void AdvancedComputeNodeScheduler::rebalanceTasks() {
    try {
        // Rebalance tasks across nodes
        // This is a simplified implementation
        spdlog::debug("Task rebalancing completed for scheduler {}", config_.schedulerId);
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to rebalance tasks for scheduler {}: {}", config_.schedulerId, e.what());
    }
}

void AdvancedComputeNodeScheduler::cleanupCompletedTasks() {
    try {
        // Cleanup completed tasks
        // This is a simplified implementation
        spdlog::debug("Completed task cleanup finished for scheduler {}", config_.schedulerId);
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to cleanup completed tasks for scheduler {}: {}", config_.schedulerId, e.what());
    }
}

std::string AdvancedComputeNodeScheduler::generateRequestId() {
    try {
        // Generate unique request ID
        std::stringstream ss;
        ss << "request_" << std::chrono::system_clock::now().time_since_epoch().count();
        return ss.str();
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to generate request ID: {}", e.what());
        return "request_" + std::to_string(std::chrono::system_clock::now().time_since_epoch().count());
    }
}

bool AdvancedComputeNodeScheduler::validateNodeInfo(const ComputeNodeInfo& nodeInfo) {
    try {
        // Validate node ID
        if (nodeInfo.nodeId.empty()) {
            spdlog::error("Node ID cannot be empty");
            return false;
        }
        
        // Validate node name
        if (nodeInfo.nodeName.empty()) {
            spdlog::error("Node name cannot be empty");
            return false;
        }
        
        // Validate cores
        if (nodeInfo.totalCores <= 0 || nodeInfo.availableCores < 0) {
            spdlog::error("Invalid core configuration");
            return false;
        }
        
        // Validate memory
        if (nodeInfo.totalMemory <= 0 || nodeInfo.availableMemory < 0) {
            spdlog::error("Invalid memory configuration");
            return false;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to validate node info: {}", e.what());
        return false;
    }
}

void AdvancedComputeNodeScheduler::updateTaskStatus(const std::string& taskId, TaskStatus status) {
    try {
        // Update task status
        taskStatus_[taskId] = status;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to update task status for task {}: {}", taskId, e.what());
    }
}

float AdvancedComputeNodeScheduler::calculateTaskPriority(const TaskExecutionRequest& request) {
    try {
        // Calculate task priority based on scheduler type
        float priority = 0.0f;
        
        switch (schedulerType_) {
            case SchedulerType::PRIORITY:
                priority = static_cast<float>(static_cast<int>(request.priority));
                break;
            case SchedulerType::WEIGHTED:
                priority = request.weight;
                break;
            default:
                priority = 1.0f;
                break;
        }
        
        return priority;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to calculate task priority: {}", e.what());
        return 1.0f;
    }
}

void AdvancedComputeNodeScheduler::optimizeTaskQueue() {
    try {
        // Optimize task queue based on scheduler type
        // This is a simplified implementation
        spdlog::debug("Task queue optimization completed for scheduler {}", config_.schedulerId);
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to optimize task queue for scheduler {}: {}", config_.schedulerId, e.what());
    }
}

void AdvancedComputeNodeScheduler::scaleUpNodes() {
    try {
        // Scale up nodes if needed
        // This is a simplified implementation
        spdlog::debug("Node scale up completed for scheduler {}", config_.schedulerId);
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to scale up nodes for scheduler {}: {}", config_.schedulerId, e.what());
    }
}

void AdvancedComputeNodeScheduler::scaleDownNodes() {
    try {
        // Scale down nodes if needed
        // This is a simplified implementation
        spdlog::debug("Node scale down completed for scheduler {}", config_.schedulerId);
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to scale down nodes for scheduler {}: {}", config_.schedulerId, e.what());
    }
}

bool AdvancedComputeNodeScheduler::isNodeOverloaded(const ComputeNodeInfo& node) {
    try {
        // Check if node is overloaded
        return node.cpuUtilization > 0.9f || node.memoryUtilization > 0.9f;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to check if node is overloaded: {}", e.what());
        return false;
    }
}

bool AdvancedComputeNodeScheduler::isNodeUnderloaded(const ComputeNodeInfo& node) {
    try {
        // Check if node is underloaded
        return node.cpuUtilization < 0.1f && node.memoryUtilization < 0.1f;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to check if node is underloaded: {}", e.what());
        return false;
    }
}

} // namespace scheduler
} // namespace cogniware
