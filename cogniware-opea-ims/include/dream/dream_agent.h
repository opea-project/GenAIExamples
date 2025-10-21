#pragma once

#include <string>
#include <vector>
#include <memory>
#include <unordered_map>
#include <queue>
#include <functional>
#include <future>
#include <chrono>
#include <deque>
#include "dream/dream_manager.h"

namespace cogniware {
namespace dream {

enum class AgentType {
    INTERFACE_LLM,    // Handles user interaction and high-level reasoning
    KNOWLEDGE_LLM,    // Manages knowledge base and factual reasoning
    REASONING_AGENT,  // Coordinates between Interface and Knowledge LLMs
    EMBODIED_AGENT    // Handles physical/embodied interactions
};

enum class TaskPriority {
    CRITICAL = 0,
    HIGH = 1,
    MEDIUM = 2,
    LOW = 3,
    BACKGROUND = 4
};

enum class ResourceType {
    GPU_MEMORY,
    CPU_MEMORY,
    GPU_COMPUTE,
    CPU_COMPUTE,
    NETWORK_BANDWIDTH,
    STORAGE_IO
};

struct ResourceRequirement {
    ResourceType type;
    size_t amount;
    float utilization_threshold;
};

struct AgentConfig {
    AgentType type;
    std::string model_name;
    TaskPriority priority;
    size_t max_memory;
    float temperature;
    bool use_fp16;
    std::vector<std::string> dependencies;
    std::vector<ResourceRequirement> resource_requirements;
    size_t max_concurrent_tasks;
    size_t max_queue_size;
    std::chrono::milliseconds task_timeout;
};

struct TaskDependency {
    std::string task_id;
    std::string dependency_type;  // e.g., "data", "compute", "resource"
    bool is_optional;
    std::chrono::milliseconds timeout;
    
    bool operator==(const TaskDependency& other) const {
        return task_id == other.task_id && 
               dependency_type == other.dependency_type &&
               is_optional == other.is_optional &&
               timeout == other.timeout;
    }
};

struct ReasoningTask {
    std::string task_id;
    std::string description;
    std::vector<std::string> input_tokens;
    std::vector<TaskDependency> dependencies;
    TaskPriority priority;
    std::function<void(const std::string&)> callback;
    bool completed;
    std::chrono::system_clock::time_point created_at;
    std::chrono::system_clock::time_point started_at;
    std::chrono::system_clock::time_point completed_at;
    std::vector<ResourceRequirement> resource_requirements;
    std::unordered_map<std::string, std::string> metadata;
};

struct ResourceMetrics {
    float utilization;
    size_t allocated;
    size_t available;
    size_t peak_usage;
    std::chrono::system_clock::time_point last_update;
};

struct TaskMetrics {
    std::chrono::milliseconds processing_time;
    std::chrono::milliseconds wait_time;
    size_t memory_usage;
    float gpu_utilization;
    int retry_count;
    std::vector<std::string> error_messages;
};

struct AgentMetrics {
    // Task metrics
    int active_tasks;
    int completed_tasks;
    int failed_tasks;
    int queued_tasks;
    int cancelled_tasks;
    float average_processing_time;
    float average_wait_time;
    float task_success_rate;
    
    // Resource metrics
    float resource_utilization;
    std::unordered_map<ResourceType, ResourceMetrics> resource_metrics;
    size_t peak_memory_usage;
    float average_gpu_utilization;
    
    // Dependency metrics
    std::vector<std::string> pending_dependencies;
    int blocked_tasks;
    float dependency_resolution_time;
    
    // Performance metrics
    float throughput;
    float latency_p95;
    float latency_p99;
    int timeout_count;
    
    // System metrics
    std::chrono::system_clock::time_point last_update;
    std::vector<std::string> recent_errors;
    std::unordered_map<std::string, int> error_counts;
};

struct LoadPrediction {
    float predicted_load;
    float confidence;
    std::chrono::system_clock::time_point prediction_time;
    std::vector<float> historical_loads;
};

struct ResourcePrediction {
    ResourceType type;
    LoadPrediction load_prediction;
    std::vector<float> utilization_trend;
    float seasonal_factor;
};

struct TaskDependencyPattern {
    std::string pattern_id;
    std::vector<TaskDependency> dependencies;
    float success_rate;
    std::chrono::milliseconds average_completion_time;
    std::vector<std::string> required_resources;
};

class DreamAgent {
public:
    DreamAgent(const AgentConfig& config);
    virtual ~DreamAgent() = default;

    // Task management
    std::string schedule_reasoning_task(
        const std::string& description,
        const std::vector<std::string>& input_tokens,
        const std::vector<TaskDependency>& dependencies,
        TaskPriority priority,
        std::function<void(const std::string&)> callback);
    
    void cancel_task(const std::string& task_id);
    bool is_task_completed(const std::string& task_id) const;
    void retry_task(const std::string& task_id);
    
    // Resource management
    void allocate_resources();
    void release_resources();
    bool check_resource_availability(const std::vector<ResourceRequirement>& requirements);
    void optimize_resource_allocation();
    
    // Task processing
    void process_tasks();
    void wait_for_task(const std::string& task_id);
    void handle_task_timeout(const std::string& task_id);
    
    // State management
    void update_state(const std::string& state);
    std::string get_state() const;
    
    // Metrics
    AgentMetrics get_metrics() const;
    void update_metrics();
    void reset_metrics();
    
    // Load balancing
    void balance_load();
    void redistribute_tasks();
    void adjust_resource_limits();
    
    // Task dependency management
    void resolve_dependencies(const std::string& task_id);
    void handle_dependency_failure(const std::string& task_id, const std::string& dependency_id);
    bool check_dependency_health(const std::string& task_id);

    // Advanced load balancing
    void predict_resource_load();
    void update_load_prediction_model();
    void optimize_task_distribution();
    void handle_seasonal_load_patterns();
    
    // Advanced dependency patterns
    void register_dependency_pattern(const TaskDependencyPattern& pattern);
    void optimize_dependency_resolution();
    void handle_circular_dependencies();
    void validate_dependency_graph();
    
    // Enhanced monitoring
    void track_resource_trends();
    void analyze_performance_patterns();
    void predict_bottlenecks();
    void generate_optimization_recommendations();
    
    // Helper functions
    float calculate_prediction_confidence(const ResourcePrediction& prediction);
    std::vector<float> calculate_utilization_trend(const std::vector<float>& history);
    float calculate_seasonal_factor(const std::vector<float>& history);
    float calculate_trend(const std::vector<float>& values);
    bool is_cyclic_util(const std::string& task_id, 
                       std::unordered_map<std::string, bool>& visited,
                       std::unordered_map<std::string, bool>& recursion_stack);
    void break_circular_dependency(const std::string& task_id);
    bool has_required_resources(const ReasoningTask& task, const TaskDependency& dep);

protected:
    virtual void process_task(const ReasoningTask& task) = 0;
    virtual void handle_dependency_completion(const std::string& task_id) = 0;
    virtual void handle_task_failure(const std::string& task_id, const std::string& error) = 0;
    
    // Resource optimization
    virtual void optimize_memory_usage() = 0;
    virtual void optimize_compute_usage() = 0;
    virtual void optimize_network_usage() = 0;
    
    // ML-based prediction
    virtual void train_load_prediction_model() = 0;
    virtual float predict_task_completion_time(const ReasoningTask& task) = 0;
    virtual void update_prediction_model(const std::string& task_id, float actual_time) = 0;
    
    // Resource optimization
    virtual void optimize_resource_allocation_patterns() = 0;
    virtual void predict_resource_requirements(const ReasoningTask& task) = 0;
    virtual void adjust_resource_allocation_based_on_prediction() = 0;
    
    // Advanced monitoring
    virtual void collect_detailed_metrics() = 0;
    virtual void analyze_resource_utilization_patterns() = 0;
    virtual void predict_system_bottlenecks() = 0;
    
    AgentConfig config_;
    std::unordered_map<std::string, ReasoningTask> tasks_;
    std::priority_queue<std::string, std::vector<std::string>, 
        std::function<bool(const std::string&, const std::string&)>> task_queue_;
    std::string current_state_;
    std::mutex mutex_;
    std::condition_variable cv_;
    
    // Resource tracking
    size_t allocated_memory_;
    int active_tasks_;
    std::chrono::system_clock::time_point last_metrics_update_;
    AgentMetrics metrics_;
    
    // Task dependency tracking
    std::unordered_map<std::string, std::vector<TaskDependency>> task_dependencies_;
    std::unordered_map<std::string, std::vector<std::string>> dependent_tasks_;
    
    // Resource optimization
    std::unordered_map<ResourceType, ResourceMetrics> resource_metrics_;
    std::deque<std::string> recent_task_history_;
    std::unordered_map<std::string, TaskMetrics> task_metrics_;
    
    // Load balancing
    std::chrono::system_clock::time_point last_load_balance_;
    float current_load_factor_;
    std::vector<std::string> overloaded_resources_;

    // Advanced monitoring
    std::unordered_map<ResourceType, ResourcePrediction> resource_predictions_;
    std::unordered_map<std::string, TaskDependencyPattern> dependency_patterns_;
    std::vector<float> load_history_;
    std::chrono::system_clock::time_point last_prediction_update_;
    float prediction_confidence_threshold_;
    size_t max_historical_data_points_;
    std::unordered_map<std::string, std::vector<float>> task_completion_times_;
    std::unordered_map<ResourceType, std::vector<float>> resource_utilization_history_;
};

class InterfaceLLMAgent : public DreamAgent {
public:
    InterfaceLLMAgent(const AgentConfig& config);
    
protected:
    void process_task(const ReasoningTask& task) override;
    void handle_dependency_completion(const std::string& task_id) override;
    
private:
    std::string generate_response(const std::vector<std::string>& input_tokens);
    void update_conversation_context(const std::string& response);
};

class KnowledgeLLMAgent : public DreamAgent {
public:
    KnowledgeLLMAgent(const AgentConfig& config);
    
protected:
    void process_task(const ReasoningTask& task) override;
    void handle_dependency_completion(const std::string& task_id) override;
    
private:
    std::string retrieve_knowledge(const std::vector<std::string>& query);
    void update_knowledge_base(const std::string& new_knowledge);
};

class ReasoningAgent : public DreamAgent {
public:
    ReasoningAgent(const AgentConfig& config);
    
protected:
    void process_task(const ReasoningTask& task) override;
    void handle_dependency_completion(const std::string& task_id) override;
    
private:
    std::string coordinate_reasoning(const std::vector<std::string>& input_tokens);
    void resolve_conflicts(const std::string& interface_response,
                         const std::string& knowledge_response);
};

class EmbodiedAgent : public DreamAgent {
public:
    EmbodiedAgent(const AgentConfig& config);
    
protected:
    void process_task(const ReasoningTask& task) override;
    void handle_dependency_completion(const std::string& task_id) override;
    
private:
    void execute_physical_action(const std::string& action);
    void update_environment_state(const std::string& state);
};

} // namespace dream
} // namespace cogniware 