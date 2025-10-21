#pragma once

#include <memory>
#include <string>
#include <vector>
#include <unordered_map>
#include <functional>
#include "llm_inference_core.h"
#include "model_config_manager.h"
#include "dream/dream_agent.h"
#include "monitoring/metrics_collector.h"
#include "security/security_manager.h"
#include "optimization/optimization_manager.h"
#include "distributed/distributed_manager.h"

namespace cogniware {

class Engine {
public:
    static Engine& get_instance();

    // Initialization and configuration
    void initialize(const std::string& config_path);
    void configure(const std::unordered_map<std::string, std::string>& config);
    void shutdown();

    // Model management
    void load_model(const std::string& model_id, const std::string& model_path);
    void unload_model(const std::string& model_id);
    bool is_model_loaded(const std::string& model_id) const;

    // Inference operations
    std::vector<float> run_inference(
        const std::string& model_id,
        const std::vector<float>& input,
        const std::unordered_map<std::string, std::string>& parameters);

    // DREAM agent operations
    void register_agent(const std::string& agent_id, 
                       std::shared_ptr<dream::DreamAgent> agent);
    void unregister_agent(const std::string& agent_id);
    std::shared_ptr<dream::DreamAgent> get_agent(const std::string& agent_id);

    // Resource management
    void allocate_resources(const std::string& model_id, size_t memory_size);
    void release_resources(const std::string& model_id);
    size_t get_available_memory() const;

    // Monitoring and metrics
    void collect_metrics();
    std::unordered_map<std::string, float> get_metrics() const;
    void set_metrics_callback(std::function<void(const std::unordered_map<std::string, float>&)> callback);

    // Security operations
    void enable_security(const std::string& security_config);
    void disable_security();
    bool is_security_enabled() const;

    // Optimization operations
    void optimize_model(const std::string& model_id);
    void set_optimization_level(int level);
    int get_optimization_level() const;

    // Distributed operations
    void join_cluster(const std::string& cluster_config);
    void leave_cluster();
    bool is_in_cluster() const;

private:
    Engine() = default;
    ~Engine() = default;
    Engine(const Engine&) = delete;
    Engine& operator=(const Engine&) = delete;

    // Core components
    std::unique_ptr<LLMInferenceCore> inference_core_;
    std::unique_ptr<ModelConfigManager> config_manager_;
    std::unique_ptr<monitoring::MetricsCollector> metrics_collector_;
    std::unique_ptr<security::SecurityManager> security_manager_;
    std::unique_ptr<optimization::OptimizationManager> optimization_manager_;
    std::unique_ptr<distributed::DistributedManager> distributed_manager_;

    // State tracking
    std::unordered_map<std::string, std::shared_ptr<dream::DreamAgent>> agents_;
    std::unordered_map<std::string, bool> loaded_models_;
    std::unordered_map<std::string, size_t> allocated_memory_;
    bool is_initialized_ = false;
    bool is_security_enabled_ = false;
    int optimization_level_ = 0;
    bool is_in_cluster_ = false;

    // Helper functions
    void validate_model_id(const std::string& model_id) const;
    void check_initialization() const;
    void update_metrics();
    void handle_error(const std::string& error_message);
};

} // namespace cogniware

// C interface declarations
extern "C" {

bool initialize_engine(int device_id);
const char* process_request(const char* request_json, char* response_buffer);
void shutdown_engine();

} 