#include "dream/dream_agent.h"
#include <spdlog/spdlog.h>
#include <algorithm>
#include <chrono>
#include <thread>
#include <numeric>
#include <cmath>

namespace cogniware {
namespace dream {

DreamAgent::DreamAgent(const AgentConfig& config)
    : config_(config),
      allocated_memory_(0),
      active_tasks_(0),
      last_metrics_update_(std::chrono::system_clock::now()),
      last_load_balance_(std::chrono::system_clock::now()),
      current_load_factor_(0.0f) {
    
    metrics_ = AgentMetrics{};
    
    // Initialize task queue with priority comparison
    task_queue_ = std::priority_queue<std::string, std::vector<std::string>,
        std::function<bool(const std::string&, const std::string&)>>(
        [this](const std::string& a, const std::string& b) {
            return tasks_[a].priority > tasks_[b].priority;
        });
}

std::string DreamAgent::schedule_reasoning_task(
    const std::string& description,
    const std::vector<std::string>& input_tokens,
    const std::vector<TaskDependency>& dependencies,
    TaskPriority priority,
    std::function<void(const std::string&)> callback) {
    
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Check queue size limit
    if (task_queue_.size() >= config_.max_queue_size) {
        throw std::runtime_error("Task queue is full");
    }
    
    // Generate unique task ID
    std::string task_id = "task_" + std::to_string(
        std::chrono::system_clock::now().time_since_epoch().count());
    
    // Create task
    ReasoningTask task{
        task_id,
        description,
        input_tokens,
        dependencies,
        priority,
        callback,
        false,
        std::chrono::system_clock::now(),
        std::chrono::system_clock::time_point(),
        std::chrono::system_clock::time_point(),
        config_.resource_requirements,
        {}
    };
    
    // Store task
    tasks_[task_id] = task;
    
    // Track dependencies
    task_dependencies_[task_id] = dependencies;
    for (const auto& dep : dependencies) {
        dependent_tasks_[dep.task_id].push_back(task_id);
    }
    
    // Check resource availability
    if (!check_resource_availability(task.resource_requirements)) {
        spdlog::warn("Insufficient resources for task {}", task_id);
        metrics_.blocked_tasks++;
        return task_id;
    }
    
    // Add to queue if no dependencies
    if (dependencies.empty()) {
        task_queue_.push(task_id);
        cv_.notify_one();
    }
    
    metrics_.queued_tasks++;
    spdlog::info("Scheduled task {} with priority {}", task_id, 
                 static_cast<int>(priority));
    
    return task_id;
}

void DreamAgent::retry_task(const std::string& task_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = tasks_.find(task_id);
    if (it == tasks_.end()) {
        throw std::runtime_error("Task not found: " + task_id);
    }
    
    auto& task = it->second;
    task.completed = false;
    task.started_at = std::chrono::system_clock::time_point();
    task.completed_at = std::chrono::system_clock::time_point();
    
    // Update metrics
    auto& task_metric = task_metrics_[task_id];
    task_metric.retry_count++;
    
    // Add back to queue
    task_queue_.push(task_id);
    cv_.notify_one();
    
    spdlog::info("Retrying task {}", task_id);
}

bool DreamAgent::check_resource_availability(
    const std::vector<ResourceRequirement>& requirements) {
    
    for (const auto& req : requirements) {
        auto& metrics = resource_metrics_[req.type];
        if (metrics.utilization + (static_cast<float>(req.amount) / metrics.available) 
            > req.utilization_threshold) {
            return false;
        }
    }
    return true;
}

void DreamAgent::optimize_resource_allocation() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Optimize memory usage
    optimize_memory_usage();
    
    // Optimize compute usage
    optimize_compute_usage();
    
    // Optimize network usage
    optimize_network_usage();
    
    // Update resource metrics
    for (auto& [type, metrics] : resource_metrics_) {
        metrics.last_update = std::chrono::system_clock::now();
    }
}

void DreamAgent::balance_load() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto now = std::chrono::system_clock::now();
    if (now - last_load_balance_ < std::chrono::seconds(5)) {
        return;  // Balance load every 5 seconds
    }
    
    // Calculate current load factor
    float total_load = 0.0f;
    for (const auto& [type, metrics] : resource_metrics_) {
        total_load += metrics.utilization;
    }
    current_load_factor_ = total_load / resource_metrics_.size();
    
    // Check for overloaded resources
    overloaded_resources_.clear();
    for (const auto& [type, metrics] : resource_metrics_) {
        if (metrics.utilization > 0.8f) {  // 80% threshold
            overloaded_resources_.push_back(std::to_string(static_cast<int>(type)));
        }
    }
    
    if (!overloaded_resources_.empty()) {
        redistribute_tasks();
    }
    
    last_load_balance_ = now;
}

void DreamAgent::redistribute_tasks() {
    // Move tasks from overloaded resources to underloaded ones
    std::vector<std::string> tasks_to_move;
    
    for (const auto& [task_id, task] : tasks_) {
        if (task.completed || task.started_at != std::chrono::system_clock::time_point()) {
            continue;
        }
        
        bool should_move = false;
        for (const auto& req : task.resource_requirements) {
            auto& metrics = resource_metrics_[req.type];
            if (metrics.utilization > 0.8f) {
                should_move = true;
                break;
            }
        }
        
        if (should_move) {
            tasks_to_move.push_back(task_id);
        }
    }
    
    // Cancel and reschedule tasks
    for (const auto& task_id : tasks_to_move) {
        auto task = tasks_[task_id];
        cancel_task(task_id);
        
        // Reschedule with adjusted resource requirements
        for (auto& req : task.resource_requirements) {
            req.utilization_threshold *= 0.8f;  // Reduce threshold
        }
        
        schedule_reasoning_task(
            task.description,
            task.input_tokens,
            task.dependencies,
            task.priority,
            task.callback
        );
    }
}

void DreamAgent::adjust_resource_limits() {
    // Adjust resource limits based on historical usage
    for (auto& [type, metrics] : resource_metrics_) {
        if (metrics.peak_usage > metrics.allocated * 0.9f) {
            // Increase allocation if peak usage is close to current allocation
            metrics.allocated = static_cast<size_t>(metrics.peak_usage * 1.2f);
        } else if (metrics.peak_usage < metrics.allocated * 0.5f) {
            // Decrease allocation if peak usage is much lower than current allocation
            metrics.allocated = static_cast<size_t>(metrics.peak_usage * 1.5f);
        }
    }
}

void DreamAgent::resolve_dependencies(const std::string& task_id) {
    auto& task = tasks_[task_id];
    auto& deps = task_dependencies_[task_id];
    
    for (auto& dep : deps) {
        if (!dep.is_optional) {
            auto dep_task = tasks_.find(dep.task_id);
            if (dep_task == tasks_.end() || !dep_task->second.completed) {
                return;  // Wait for required dependency
            }
            
            // Check for timeout
            auto now = std::chrono::system_clock::now();
            if (now - dep_task->second.created_at > dep.timeout) {
                handle_dependency_failure(task_id, dep.task_id);
                return;
            }
        }
    }
    
    // All dependencies resolved
    task_queue_.push(task_id);
    cv_.notify_one();
}

void DreamAgent::handle_dependency_failure(
    const std::string& task_id,
    const std::string& dependency_id) {
    
    auto& task = tasks_[task_id];
    task.completed = true;  // Mark as completed to prevent further processing
    
    // Update metrics
    metrics_.failed_tasks++;
    metrics_.recent_errors.push_back(
        "Dependency " + dependency_id + " failed for task " + task_id);
    
    // Call failure handler
    handle_task_failure(task_id, "Dependency failed: " + dependency_id);
}

bool DreamAgent::check_dependency_health(const std::string& task_id) {
    auto& deps = task_dependencies_[task_id];
    for (const auto& dep : deps) {
        auto dep_task = tasks_.find(dep.task_id);
        if (dep_task == tasks_.end()) {
            return false;
        }
        
        // Check for timeout
        auto now = std::chrono::system_clock::now();
        if (now - dep_task->second.created_at > dep.timeout) {
            return false;
        }
    }
    return true;
}

void DreamAgent::update_metrics() {
    auto now = std::chrono::system_clock::now();
    auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(
        now - last_metrics_update_).count();
    
    if (elapsed >= 1) {  // Update every second
        // Update task metrics
        metrics_.active_tasks = active_tasks_;
        metrics_.queued_tasks = task_queue_.size();
        
        // Calculate success rate
        if (metrics_.completed_tasks + metrics_.failed_tasks > 0) {
            metrics_.task_success_rate = static_cast<float>(metrics_.completed_tasks) /
                (metrics_.completed_tasks + metrics_.failed_tasks);
        }
        
        // Calculate average processing time
        std::vector<float> processing_times;
        for (const auto& [task_id, task_metric] : task_metrics_) {
            processing_times.push_back(
                std::chrono::duration_cast<std::chrono::milliseconds>(
                    task_metric.processing_time).count());
        }
        
        if (!processing_times.empty()) {
            std::sort(processing_times.begin(), processing_times.end());
            metrics_.average_processing_time = std::accumulate(
                processing_times.begin(), processing_times.end(), 0.0f) / 
                processing_times.size();
            
            // Calculate percentiles
            size_t p95_idx = static_cast<size_t>(processing_times.size() * 0.95);
            size_t p99_idx = static_cast<size_t>(processing_times.size() * 0.99);
            metrics_.latency_p95 = processing_times[p95_idx];
            metrics_.latency_p99 = processing_times[p99_idx];
        }
        
        // Update resource metrics
        for (auto& [type, metrics] : resource_metrics_) {
            metrics.last_update = now;
            if (metrics.allocated > metrics.peak_usage) {
                metrics.peak_usage = metrics.allocated;
            }
        }
        
        // Calculate throughput
        metrics_.throughput = static_cast<float>(metrics_.completed_tasks) / elapsed;
        
        // Update dependency metrics
        metrics_.pending_dependencies.clear();
        for (const auto& [task_id, deps] : task_dependencies_) {
            if (!deps.empty()) {
                metrics_.pending_dependencies.push_back(task_id);
            }
        }
        
        last_metrics_update_ = now;
    }
}

void DreamAgent::reset_metrics() {
    std::lock_guard<std::mutex> lock(mutex_);
    metrics_ = AgentMetrics{};
    task_metrics_.clear();
    for (auto& [type, metrics] : resource_metrics_) {
        metrics = ResourceMetrics{};
    }
}

void DreamAgent::cancel_task(const std::string& task_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = tasks_.find(task_id);
    if (it == tasks_.end()) {
        throw std::runtime_error("Task not found: " + task_id);
    }
    
    // Remove from dependent tasks
    for (const auto& dep : it->second.dependencies) {
        auto& deps = dependent_tasks_[dep.task_id];
        deps.erase(std::remove(deps.begin(), deps.end(), task_id), deps.end());
    }
    
    // Remove task
    tasks_.erase(it);
    task_dependencies_.erase(task_id);
    
    spdlog::info("Cancelled task {}", task_id);
}

bool DreamAgent::is_task_completed(const std::string& task_id) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = tasks_.find(task_id);
    if (it == tasks_.end()) {
        throw std::runtime_error("Task not found: " + task_id);
    }
    
    return it->second.completed;
}

void DreamAgent::allocate_resources() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Allocate memory through DREAM manager
    auto& manager = DreamManager::get_instance();
    void* ptr = manager.allocate_memory(config_.max_memory, "agent_" + config_.model_name);
    if (!ptr) {
        throw std::runtime_error("Failed to allocate resources");
    }
    
    allocated_memory_ = config_.max_memory;
    spdlog::info("Allocated {} bytes for agent {}", allocated_memory_, config_.model_name);
}

void DreamAgent::release_resources() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Release memory through DREAM manager
    auto& manager = DreamManager::get_instance();
    manager.free_memory(nullptr, "agent_" + config_.model_name);
    
    allocated_memory_ = 0;
    spdlog::info("Released resources for agent {}", config_.model_name);
}

void DreamAgent::process_tasks() {
    while (true) {
        std::unique_lock<std::mutex> lock(mutex_);
        cv_.wait(lock, [this] { return !task_queue_.empty(); });
        
        // Get next task
        std::string task_id = task_queue_.top();
        task_queue_.pop();
        
        auto& task = tasks_[task_id];
        active_tasks_++;
        
        // Process task
        try {
            process_task(task);
            task.completed = true;
            
            // Notify dependent tasks
            for (const auto& dep_task_id : dependent_tasks_[task_id]) {
                auto& dep_task = tasks_[dep_task_id];
                auto& deps = task_dependencies_[dep_task_id];
                
                // Remove completed dependency
                deps.erase(std::remove_if(deps.begin(), deps.end(), 
                    [&task_id](const TaskDependency& dep) { return dep.task_id == task_id; }), deps.end());
                
                // If all dependencies are completed, add to queue
                if (deps.empty()) {
                    task_queue_.push(dep_task_id);
                    cv_.notify_one();
                }
            }
            
            // Call callback
            if (task.callback) {
                task.callback(task_id);
            }
            
        } catch (const std::exception& e) {
            spdlog::error("Error processing task {}: {}", task_id, e.what());
            metrics_.failed_tasks++;
        }
        
        active_tasks_--;
        metrics_.completed_tasks++;
        
        // Update metrics
        update_metrics();
    }
}

void DreamAgent::wait_for_task(const std::string& task_id) {
    std::unique_lock<std::mutex> lock(mutex_);
    cv_.wait(lock, [this, &task_id] {
        auto it = tasks_.find(task_id);
        return it == tasks_.end() || it->second.completed;
    });
}

void DreamAgent::update_state(const std::string& state) {
    std::lock_guard<std::mutex> lock(mutex_);
    current_state_ = state;
}

std::string DreamAgent::get_state() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return current_state_;
}

DreamAgent::AgentMetrics DreamAgent::get_metrics() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return metrics_;
}

// InterfaceLLMAgent implementation
InterfaceLLMAgent::InterfaceLLMAgent(const AgentConfig& config)
    : DreamAgent(config) {
    if (config.type != AgentType::INTERFACE_LLM) {
        throw std::runtime_error("Invalid agent type for InterfaceLLMAgent");
    }
}

void InterfaceLLMAgent::process_task(const ReasoningTask& task) {
    // Generate response using the interface LLM
    std::string response = generate_response(task.input_tokens);
    
    // Update conversation context
    update_conversation_context(response);
}

void InterfaceLLMAgent::handle_dependency_completion(const std::string& task_id) {
    // Handle completion of dependent tasks
    auto& task = tasks_[task_id];
    if (task.callback) {
        task.callback(task_id);
    }
}

std::string InterfaceLLMAgent::generate_response(
    const std::vector<std::string>& input_tokens) {
    // Implement interface LLM response generation
    // This would typically involve calling the underlying LLM model
    return "Interface LLM response";
}

void InterfaceLLMAgent::update_conversation_context(const std::string& response) {
    // Update the conversation context with the new response
    // This could involve updating a conversation history or context buffer
}

// KnowledgeLLMAgent implementation
KnowledgeLLMAgent::KnowledgeLLMAgent(const AgentConfig& config)
    : DreamAgent(config) {
    if (config.type != AgentType::KNOWLEDGE_LLM) {
        throw std::runtime_error("Invalid agent type for KnowledgeLLMAgent");
    }
}

void KnowledgeLLMAgent::process_task(const ReasoningTask& task) {
    // Retrieve knowledge using the knowledge LLM
    std::string knowledge = retrieve_knowledge(task.input_tokens);
    
    // Update knowledge base
    update_knowledge_base(knowledge);
}

void KnowledgeLLMAgent::handle_dependency_completion(const std::string& task_id) {
    // Handle completion of dependent tasks
    auto& task = tasks_[task_id];
    if (task.callback) {
        task.callback(task_id);
    }
}

std::string KnowledgeLLMAgent::retrieve_knowledge(
    const std::vector<std::string>& query) {
    // Implement knowledge retrieval using the knowledge LLM
    // This would typically involve querying a knowledge base
    return "Knowledge LLM response";
}

void KnowledgeLLMAgent::update_knowledge_base(const std::string& new_knowledge) {
    // Update the knowledge base with new information
    // This could involve adding to a vector database or other storage
}

// ReasoningAgent implementation
ReasoningAgent::ReasoningAgent(const AgentConfig& config)
    : DreamAgent(config) {
    if (config.type != AgentType::REASONING_AGENT) {
        throw std::runtime_error("Invalid agent type for ReasoningAgent");
    }
}

void ReasoningAgent::process_task(const ReasoningTask& task) {
    // Coordinate reasoning between interface and knowledge LLMs
    std::string result = coordinate_reasoning(task.input_tokens);
    
    // Resolve any conflicts in the responses
    resolve_conflicts(result, result);  // Placeholder for actual responses
}

void ReasoningAgent::handle_dependency_completion(const std::string& task_id) {
    // Handle completion of dependent tasks
    auto& task = tasks_[task_id];
    if (task.callback) {
        task.callback(task_id);
    }
}

std::string ReasoningAgent::coordinate_reasoning(
    const std::vector<std::string>& input_tokens) {
    // Implement coordination logic between LLMs
    // This would involve managing the interaction between interface and knowledge LLMs
    return "Coordinated reasoning result";
}

void ReasoningAgent::resolve_conflicts(
    const std::string& interface_response,
    const std::string& knowledge_response) {
    // Implement conflict resolution logic
    // This would involve resolving any contradictions between LLM responses
}

// EmbodiedAgent implementation
EmbodiedAgent::EmbodiedAgent(const AgentConfig& config)
    : DreamAgent(config) {
    if (config.type != AgentType::EMBODIED_AGENT) {
        throw std::runtime_error("Invalid agent type for EmbodiedAgent");
    }
}

void EmbodiedAgent::process_task(const ReasoningTask& task) {
    // Execute physical actions based on the task
    execute_physical_action(task.description);
    
    // Update environment state
    update_environment_state("Updated state");
}

void EmbodiedAgent::handle_dependency_completion(const std::string& task_id) {
    // Handle completion of dependent tasks
    auto& task = tasks_[task_id];
    if (task.callback) {
        task.callback(task_id);
    }
}

void EmbodiedAgent::execute_physical_action(const std::string& action) {
    // Implement physical action execution
    // This would involve controlling physical actuators or simulators
}

void EmbodiedAgent::update_environment_state(const std::string& state) {
    // Update the environment state
    // This would involve updating the agent's understanding of its environment
}

void DreamAgent::predict_resource_load() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto now = std::chrono::system_clock::now();
    if (now - last_prediction_update_ < std::chrono::seconds(30)) {
        return;  // Update predictions every 30 seconds
    }
    
    for (auto& [type, prediction] : resource_predictions_) {
        // Calculate moving average of historical loads
        if (!load_history_.empty()) {
            size_t window_size = std::min(load_history_.size(), max_historical_data_points_);
            float sum = std::accumulate(load_history_.end() - window_size, 
                                      load_history_.end(), 0.0f);
            float moving_avg = sum / window_size;
            
            // Apply seasonal factor if available
            if (prediction.seasonal_factor > 0) {
                moving_avg *= prediction.seasonal_factor;
            }
            
            // Update prediction
            prediction.load_prediction.predicted_load = moving_avg;
            prediction.load_prediction.confidence = calculate_prediction_confidence(prediction);
            prediction.load_prediction.prediction_time = now;
        }
    }
    
    last_prediction_update_ = now;
}

void DreamAgent::update_load_prediction_model() {
    for (auto& [type, prediction] : resource_predictions_) {
        // Update historical data
        auto& metrics = resource_metrics_[type];
        prediction.load_prediction.historical_loads.push_back(metrics.utilization);
        
        // Keep only recent history
        if (prediction.load_prediction.historical_loads.size() > max_historical_data_points_) {
            prediction.load_prediction.historical_loads.erase(
                prediction.load_prediction.historical_loads.begin());
        }
        
        // Update utilization trend
        prediction.utilization_trend = calculate_utilization_trend(
            prediction.load_prediction.historical_loads);
        
        // Update seasonal factor
        prediction.seasonal_factor = calculate_seasonal_factor(
            prediction.load_prediction.historical_loads);
    }
}

void DreamAgent::optimize_task_distribution() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Get current resource predictions
    std::unordered_map<ResourceType, float> predicted_loads;
    for (const auto& [type, prediction] : resource_predictions_) {
        predicted_loads[type] = prediction.load_prediction.predicted_load;
    }
    
    // Find underutilized resources
    std::vector<ResourceType> underutilized;
    for (const auto& [type, load] : predicted_loads) {
        if (load < 0.5f) {  // 50% threshold
            underutilized.push_back(type);
        }
    }
    
    // Redistribute tasks to underutilized resources
    for (const auto& task_id : task_queue_) {
        auto& task = tasks_[task_id];
        if (task.completed || task.started_at != std::chrono::system_clock::time_point()) {
            continue;
        }
        
        // Check if task can be moved to underutilized resources
        bool can_move = false;
        for (const auto& req : task.resource_requirements) {
            if (std::find(underutilized.begin(), underutilized.end(), req.type) 
                != underutilized.end()) {
                can_move = true;
                break;
            }
        }
        
        if (can_move) {
            // Adjust resource requirements for better distribution
            for (auto& req : task.resource_requirements) {
                req.utilization_threshold *= 0.8f;  // Reduce threshold
            }
            
            // Reschedule task
            cancel_task(task_id);
            schedule_reasoning_task(
                task.description,
                task.input_tokens,
                task.dependencies,
                task.priority,
                task.callback
            );
        }
    }
}

void DreamAgent::handle_seasonal_load_patterns() {
    for (auto& [type, prediction] : resource_predictions_) {
        // Detect seasonal patterns in resource utilization
        auto& history = prediction.load_prediction.historical_loads;
        if (history.size() < 24) {  // Need at least 24 data points
            continue;
        }
        
        // Calculate seasonal factors for different time periods
        std::vector<float> hourly_factors(24, 0.0f);
        std::vector<int> hourly_counts(24, 0);
        
        for (size_t i = 0; i < history.size(); ++i) {
            int hour = i % 24;
            hourly_factors[hour] += history[i];
            hourly_counts[hour]++;
        }
        
        // Normalize factors
        for (int i = 0; i < 24; ++i) {
            if (hourly_counts[i] > 0) {
                hourly_factors[i] /= hourly_counts[i];
            }
        }
        
        // Update seasonal factor based on current hour
        auto now = std::chrono::system_clock::now();
        auto hour = std::chrono::duration_cast<std::chrono::hours>(
            now.time_since_epoch()).count() % 24;
        prediction.seasonal_factor = hourly_factors[hour];
    }
}

void DreamAgent::register_dependency_pattern(const TaskDependencyPattern& pattern) {
    std::lock_guard<std::mutex> lock(mutex_);
    dependency_patterns_[pattern.pattern_id] = pattern;
}

void DreamAgent::optimize_dependency_resolution() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    for (auto& [task_id, task] : tasks_) {
        if (task.completed || !task.dependencies.empty()) {
            continue;
        }
        
        // Find matching dependency patterns
        for (const auto& [pattern_id, pattern] : dependency_patterns_) {
            if (pattern.success_rate > 0.8f) {  // Only use high-success patterns
                // Check if task matches pattern
                bool matches = true;
                for (const auto& dep : pattern.dependencies) {
                    if (!has_required_resources(task, dep)) {
                        matches = false;
                        break;
                    }
                }
                
                if (matches) {
                    // Apply pattern to task
                    task.dependencies = pattern.dependencies;
                    task_dependencies_[task_id] = pattern.dependencies;
                    
                    // Update dependent tasks
                    for (const auto& dep : pattern.dependencies) {
                        dependent_tasks_[dep.task_id].push_back(task_id);
                    }
                }
            }
        }
    }
}

void DreamAgent::handle_circular_dependencies() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Detect circular dependencies using DFS
    std::unordered_map<std::string, bool> visited;
    std::unordered_map<std::string, bool> recursion_stack;
    
    for (const auto& [task_id, _] : tasks_) {
        if (!visited[task_id]) {
            if (is_cyclic_util(task_id, visited, recursion_stack)) {
                // Break circular dependency by removing one dependency
                break_circular_dependency(task_id);
            }
        }
    }
}

void DreamAgent::validate_dependency_graph() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    for (const auto& [task_id, deps] : task_dependencies_) {
        // Check if all dependencies exist
        for (const auto& dep : deps) {
            if (tasks_.find(dep.task_id) == tasks_.end()) {
                spdlog::warn("Invalid dependency {} for task {}", dep.task_id, task_id);
                // Remove invalid dependency
                auto& task_deps = task_dependencies_[task_id];
                task_deps.erase(
                    std::remove(task_deps.begin(), task_deps.end(), dep),
                    task_deps.end());
            }
        }
        
        // Check for timeout
        auto now = std::chrono::system_clock::now();
        for (const auto& dep : deps) {
            auto dep_task = tasks_.find(dep.task_id);
            if (dep_task != tasks_.end() && 
                now - dep_task->second.created_at > dep.timeout) {
                handle_dependency_failure(task_id, dep.task_id);
            }
        }
    }
}

void DreamAgent::track_resource_trends() {
    for (auto& [type, metrics] : resource_metrics_) {
        // Update utilization history
        resource_utilization_history_[type].push_back(metrics.utilization);
        
        // Keep only recent history
        if (resource_utilization_history_[type].size() > max_historical_data_points_) {
            resource_utilization_history_[type].erase(
                resource_utilization_history_[type].begin());
        }
        
        // Calculate trends
        auto& history = resource_utilization_history_[type];
        if (history.size() >= 2) {
            float trend = calculate_trend(history);
            resource_predictions_[type].utilization_trend.push_back(trend);
        }
    }
}

void DreamAgent::analyze_performance_patterns() {
    for (const auto& [task_id, task] : tasks_) {
        if (task.completed) {
            // Update completion time history
            auto completion_time = std::chrono::duration_cast<std::chrono::milliseconds>(
                task.completed_at - task.started_at).count();
            task_completion_times_[task_id].push_back(completion_time);
            
            // Keep only recent history
            if (task_completion_times_[task_id].size() > max_historical_data_points_) {
                task_completion_times_[task_id].erase(
                    task_completion_times_[task_id].begin());
            }
        }
    }
}

void DreamAgent::predict_bottlenecks() {
    for (const auto& [type, prediction] : resource_predictions_) {
        // Check if resource is approaching capacity
        if (prediction.load_prediction.predicted_load > 0.8f) {
            spdlog::warn("Resource {} is predicted to be a bottleneck", 
                        static_cast<int>(type));
            
            // Generate optimization recommendations
            generate_optimization_recommendations();
        }
    }
}

void DreamAgent::generate_optimization_recommendations() {
    std::vector<std::string> recommendations;
    
    // Analyze resource utilization patterns
    for (const auto& [type, history] : resource_utilization_history_) {
        if (history.size() >= 24) {  // Need at least 24 data points
            float avg_utilization = std::accumulate(history.begin(), history.end(), 0.0f) 
                                  / history.size();
            
            if (avg_utilization > 0.8f) {
                recommendations.push_back(
                    "Consider increasing capacity for resource " + 
                    std::to_string(static_cast<int>(type)));
            }
        }
    }
    
    // Analyze task completion patterns
    for (const auto& [task_id, times] : task_completion_times_) {
        if (times.size() >= 10) {  // Need at least 10 data points
            float avg_time = std::accumulate(times.begin(), times.end(), 0.0f) 
                           / times.size();
            
            if (avg_time > 1000.0f) {  // More than 1 second
                recommendations.push_back(
                    "Task " + task_id + " is taking longer than expected");
            }
        }
    }
    
    // Log recommendations
    for (const auto& rec : recommendations) {
        spdlog::info("Optimization recommendation: {}", rec);
    }
}

// Helper functions
float DreamAgent::calculate_prediction_confidence(const ResourcePrediction& prediction) {
    if (prediction.load_prediction.historical_loads.empty()) {
        return 0.0f;
    }
    
    // Calculate standard deviation of historical loads
    float mean = std::accumulate(prediction.load_prediction.historical_loads.begin(),
                               prediction.load_prediction.historical_loads.end(), 0.0f) 
                / prediction.load_prediction.historical_loads.size();
    
    float variance = 0.0f;
    for (float load : prediction.load_prediction.historical_loads) {
        variance += (load - mean) * (load - mean);
    }
    variance /= prediction.load_prediction.historical_loads.size();
    
    // Higher confidence for lower variance
    return 1.0f / (1.0f + std::sqrt(variance));
}

std::vector<float> DreamAgent::calculate_utilization_trend(
    const std::vector<float>& history) {
    if (history.size() < 2) {
        return {};
    }
    
    std::vector<float> trend;
    for (size_t i = 1; i < history.size(); ++i) {
        trend.push_back(history[i] - history[i-1]);
    }
    return trend;
}

float DreamAgent::calculate_seasonal_factor(const std::vector<float>& history) {
    if (history.size() < 24) {
        return 1.0f;
    }
    
    // Calculate average for each hour
    std::vector<float> hourly_avgs(24, 0.0f);
    std::vector<int> hourly_counts(24, 0);
    
    for (size_t i = 0; i < history.size(); ++i) {
        int hour = i % 24;
        hourly_avgs[hour] += history[i];
        hourly_counts[hour]++;
    }
    
    // Normalize averages
    for (int i = 0; i < 24; ++i) {
        if (hourly_counts[i] > 0) {
            hourly_avgs[i] /= hourly_counts[i];
        }
    }
    
    // Calculate overall average
    float overall_avg = std::accumulate(hourly_avgs.begin(), hourly_avgs.end(), 0.0f) 
                       / hourly_avgs.size();
    
    // Return current hour's factor
    auto now = std::chrono::system_clock::now();
    auto hour = std::chrono::duration_cast<std::chrono::hours>(
        now.time_since_epoch()).count() % 24;
    return hourly_avgs[hour] / overall_avg;
}

float DreamAgent::calculate_trend(const std::vector<float>& values) {
    if (values.size() < 2) {
        return 0.0f;
    }
    
    // Simple linear regression
    float sum_x = 0.0f;
    float sum_y = 0.0f;
    float sum_xy = 0.0f;
    float sum_xx = 0.0f;
    
    for (size_t i = 0; i < values.size(); ++i) {
        sum_x += i;
        sum_y += values[i];
        sum_xy += i * values[i];
        sum_xx += i * i;
    }
    
    float n = static_cast<float>(values.size());
    float slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x);
    
    return slope;
}

bool DreamAgent::is_cyclic_util(const std::string& task_id,
                              std::unordered_map<std::string, bool>& visited,
                              std::unordered_map<std::string, bool>& recursion_stack) {
    visited[task_id] = true;
    recursion_stack[task_id] = true;
    
    for (const auto& dep : task_dependencies_[task_id]) {
        if (!visited[dep.task_id]) {
            if (is_cyclic_util(dep.task_id, visited, recursion_stack)) {
                return true;
            }
        } else if (recursion_stack[dep.task_id]) {
            return true;
        }
    }
    
    recursion_stack[task_id] = false;
    return false;
}

void DreamAgent::break_circular_dependency(const std::string& task_id) {
    auto& deps = task_dependencies_[task_id];
    if (deps.empty()) {
        return;
    }
    
    // Remove the dependency with the lowest priority
    auto min_priority = std::min_element(deps.begin(), deps.end(),
        [this](const TaskDependency& a, const TaskDependency& b) {
            return tasks_[a.task_id].priority > tasks_[b.task_id].priority;
        });
    
    if (min_priority != deps.end()) {
        spdlog::warn("Breaking circular dependency by removing {} from task {}",
                    min_priority->task_id, task_id);
        deps.erase(min_priority);
    }
}

bool DreamAgent::has_required_resources(const ReasoningTask& task,
                                      const TaskDependency& dep) {
    for (const auto& req : task.resource_requirements) {
        if (std::find(dep.required_resources.begin(),
                     dep.required_resources.end(),
                     std::to_string(static_cast<int>(req.type))) 
            != dep.required_resources.end()) {
            return true;
        }
    }
    return false;
}

} // namespace dream
} // namespace cogniware 