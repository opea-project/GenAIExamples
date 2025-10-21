#include "distributed/model_distributor.h"
#include <grpcpp/grpcpp.h>
#include <spdlog/spdlog.h>
#include <algorithm>
#include <chrono>
#include <thread>

namespace cogniware {

ModelDistributor::ModelDistributor(const std::string& coordinator_address)
    : coordinator_address_(coordinator_address) {
    // Initialize gRPC channel
    coordinator_channel_ = grpc::CreateChannel(
        coordinator_address_,
        grpc::InsecureChannelCredentials()
    );
    
    spdlog::info("ModelDistributor initialized with coordinator at {}", coordinator_address_);
}

bool ModelDistributor::distribute_model(
    const std::string& model_id,
    const std::vector<std::string>& worker_addresses) {
    
    try {
        // Validate worker addresses
        for (const auto& address : worker_addresses) {
            if (!check_worker_health(address)) {
                spdlog::error("Worker {} is not healthy", address);
                return false;
            }
        }
        
        // Check resource availability on workers
        for (const auto& address : worker_addresses) {
            auto resources = get_worker_resources(address);
            if (resources.active_models >= 10) { // Example threshold
                spdlog::error("Worker {} has reached maximum model capacity", address);
                return false;
            }
        }
        
        // Store distribution information
        model_distribution_[model_id] = worker_addresses;
        
        // Update worker loads
        for (const auto& address : worker_addresses) {
            update_worker_load(address, 0.0f); // Initial load
        }
        
        spdlog::info("Model {} distributed to {} workers", model_id, worker_addresses.size());
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Failed to distribute model {}: {}", model_id, e.what());
        return false;
    }
}

bool ModelDistributor::remove_distribution(const std::string& model_id) {
    try {
        auto it = model_distribution_.find(model_id);
        if (it == model_distribution_.end()) {
            spdlog::warn("Model {} not found in distribution", model_id);
            return false;
        }
        
        // Update worker loads
        for (const auto& address : it->second) {
            update_worker_load(address, -1.0f); // Decrease load
        }
        
        model_distribution_.erase(it);
        spdlog::info("Model {} distribution removed", model_id);
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Failed to remove model distribution {}: {}", model_id, e.what());
        return false;
    }
}

std::string ModelDistributor::get_optimal_worker(const std::string& model_id) {
    try {
        auto it = model_distribution_.find(model_id);
        if (it == model_distribution_.end()) {
            spdlog::error("Model {} not found in distribution", model_id);
            return "";
        }
        
        // Find worker with lowest load
        std::string optimal_worker;
        float min_load = std::numeric_limits<float>::max();
        
        for (const auto& address : it->second) {
            auto load_it = worker_loads_.find(address);
            if (load_it != worker_loads_.end() && load_it->second < min_load) {
                min_load = load_it->second;
                optimal_worker = address;
            }
        }
        
        if (optimal_worker.empty()) {
            spdlog::error("No optimal worker found for model {}", model_id);
            return "";
        }
        
        return optimal_worker;
    } catch (const std::exception& e) {
        spdlog::error("Failed to get optimal worker for model {}: {}", model_id, e.what());
        return "";
    }
}

void ModelDistributor::update_worker_load(const std::string& worker_address, float load) {
    try {
        worker_loads_[worker_address] = std::max(0.0f, worker_loads_[worker_address] + load);
        spdlog::debug("Updated load for worker {}: {}", worker_address, worker_loads_[worker_address]);
    } catch (const std::exception& e) {
        spdlog::error("Failed to update worker load {}: {}", worker_address, e.what());
    }
}

bool ModelDistributor::check_worker_health(const std::string& worker_address) {
    try {
        // Create gRPC stub for health check
        auto stub = model_service::ModelService::NewStub(
            grpc::CreateChannel(worker_address, grpc::InsecureChannelCredentials())
        );
        
        // Set timeout
        grpc::ClientContext context;
        context.set_deadline(std::chrono::system_clock::now() + std::chrono::seconds(5));
        
        // Make health check request
        model_service::HealthRequest request;
        model_service::HealthResponse response;
        
        auto status = stub->GetHealthStatus(&context, request, &response);
        
        if (!status.ok()) {
            spdlog::error("Health check failed for worker {}: {}", 
                         worker_address, status.error_message());
            return false;
        }
        
        return response.status() == model_service::HealthResponse::HEALTHY;
    } catch (const std::exception& e) {
        spdlog::error("Health check failed for worker {}: {}", worker_address, e.what());
        return false;
    }
}

std::map<std::string, bool> ModelDistributor::get_worker_health_status() {
    std::map<std::string, bool> health_status;
    
    try {
        // Check health for all known workers
        for (const auto& [address, _] : worker_loads_) {
            health_status[address] = check_worker_health(address);
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to get worker health status: {}", e.what());
    }
    
    return health_status;
}

ModelDistributor::WorkerResources ModelDistributor::get_worker_resources(
    const std::string& worker_address) {
    
    try {
        auto it = worker_resources_.find(worker_address);
        if (it != worker_resources_.end()) {
            return it->second;
        }
        
        // If not cached, fetch from worker
        auto stub = model_service::ModelService::NewStub(
            grpc::CreateChannel(worker_address, grpc::InsecureChannelCredentials())
        );
        
        grpc::ClientContext context;
        model_service::ResourceUsageRequest request;
        model_service::ResourceUsageResponse response;
        
        auto status = stub->GetResourceUsage(&context, request, &response);
        
        if (!status.ok()) {
            spdlog::error("Failed to get resources for worker {}: {}", 
                         worker_address, status.error_message());
            return WorkerResources{};
        }
        
        // Update cache
        WorkerResources resources{
            response.usage_metrics().at("gpu_memory"),
            response.usage_metrics().at("cpu_utilization"),
            response.usage_metrics().at("memory_available"),
            static_cast<int>(response.usage_metrics().at("active_models"))
        };
        
        worker_resources_[worker_address] = resources;
        return resources;
    } catch (const std::exception& e) {
        spdlog::error("Failed to get worker resources {}: {}", worker_address, e.what());
        return WorkerResources{};
    }
}

bool ModelDistributor::allocate_worker_resources(
    const std::string& worker_address,
    const WorkerResources& required) {
    
    try {
        if (!validate_worker_capacity(worker_address, required)) {
            spdlog::error("Worker {} does not have sufficient resources", worker_address);
            return false;
        }
        
        // Update resource cache
        auto& current = worker_resources_[worker_address];
        current.gpu_memory_available -= required.gpu_memory_available;
        current.memory_available -= required.memory_available;
        current.active_models++;
        
        spdlog::info("Allocated resources on worker {}", worker_address);
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Failed to allocate resources on worker {}: {}", 
                     worker_address, e.what());
        return false;
    }
}

bool ModelDistributor::validate_worker_capacity(
    const std::string& worker_address,
    const WorkerResources& required) {
    
    try {
        auto current = get_worker_resources(worker_address);
        
        return current.gpu_memory_available >= required.gpu_memory_available &&
               current.memory_available >= required.memory_available &&
               current.cpu_utilization < 90.0f; // Example threshold
    } catch (const std::exception& e) {
        spdlog::error("Failed to validate worker capacity {}: {}", 
                     worker_address, e.what());
        return false;
    }
}

void ModelDistributor::update_worker_metrics(const std::string& worker_address) {
    try {
        // Update resource metrics
        auto resources = get_worker_resources(worker_address);
        worker_resources_[worker_address] = resources;
        
        // Update load metrics
        update_worker_load(worker_address, 0.0f);
        
        spdlog::debug("Updated metrics for worker {}", worker_address);
    } catch (const std::exception& e) {
        spdlog::error("Failed to update worker metrics {}: {}", 
                     worker_address, e.what());
    }
}

} // namespace cogniware 