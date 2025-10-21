#pragma once

#include <string>
#include <vector>
#include <map>
#include <memory>
#include <grpcpp/grpcpp.h>
#include "common_interfaces/protos/model_service.grpc.pb.h"

namespace cogniware {

class ModelDistributor {
public:
    ModelDistributor(const std::string& coordinator_address);
    
    // Model distribution
    bool distribute_model(const std::string& model_id, 
                         const std::vector<std::string>& worker_addresses);
    bool remove_distribution(const std::string& model_id);
    
    // Load balancing
    std::string get_optimal_worker(const std::string& model_id);
    void update_worker_load(const std::string& worker_address, float load);
    
    // Health monitoring
    bool check_worker_health(const std::string& worker_address);
    std::map<std::string, bool> get_worker_health_status();
    
    // Resource management
    struct WorkerResources {
        float gpu_memory_available;
        float cpu_utilization;
        float memory_available;
        int active_models;
    };
    
    WorkerResources get_worker_resources(const std::string& worker_address);
    bool allocate_worker_resources(const std::string& worker_address, 
                                 const WorkerResources& required);

private:
    std::string coordinator_address_;
    std::unique_ptr<grpc::Channel> coordinator_channel_;
    std::map<std::string, std::vector<std::string>> model_distribution_;
    std::map<std::string, float> worker_loads_;
    std::map<std::string, WorkerResources> worker_resources_;
    
    // Internal methods
    bool validate_worker_capacity(const std::string& worker_address,
                                const WorkerResources& required);
    void update_worker_metrics(const std::string& worker_address);
}; 