#pragma once

#include <string>
#include <vector>
#include <memory>

namespace cogniware {
namespace distributed {

struct WorkerNode {
    std::string node_id;
    std::string hostname;
    int port;
    std::vector<int> gpu_ids;
    bool active;
};

class DistributedSystem {
public:
    DistributedSystem();
    ~DistributedSystem();

    bool initialize(const std::string& master_host, int port);
    void shutdown();
    
    bool registerWorker(const WorkerNode& node);
    bool removeWorker(const std::string& node_id);
    std::vector<WorkerNode> listWorkers();
    
    bool distributeModel(const std::string& model_id, const std::vector<std::string>& worker_ids);
    
    std::string submitDistributedJob(const std::string& job_type,
                                    const std::unordered_map<std::string, std::string>& params);

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

} // namespace distributed
} // namespace cogniware

