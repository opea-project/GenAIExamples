#include "distributed/distributed_system.h"
#include <mutex>

namespace cogniware {
namespace distributed {

class DistributedSystem::Impl {
public:
    std::vector<WorkerNode> workers;
    mutable std::mutex mutex;
    bool initialized = false;
};

DistributedSystem::DistributedSystem() : pImpl(std::make_unique<Impl>()) {}
DistributedSystem::~DistributedSystem() { shutdown(); }

bool DistributedSystem::initialize(const std::string&, int) {
    pImpl->initialized = true;
    return true;
}

void DistributedSystem::shutdown() {
    pImpl->initialized = false;
}

bool DistributedSystem::registerWorker(const WorkerNode& node) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    pImpl->workers.push_back(node);
    return true;
}

bool DistributedSystem::removeWorker(const std::string& node_id) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    pImpl->workers.erase(std::remove_if(pImpl->workers.begin(), pImpl->workers.end(),
        [&](const WorkerNode& n) { return n.node_id == node_id; }), pImpl->workers.end());
    return true;
}

std::vector<WorkerNode> DistributedSystem::listWorkers() {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    return pImpl->workers;
}

bool DistributedSystem::distributeModel(const std::string&, const std::vector<std::string>&) {
    return true;
}

std::string DistributedSystem::submitDistributedJob(const std::string&,
                                                   const std::unordered_map<std::string, std::string>&) {
    return "job_distributed_001";
}

} // namespace distributed
} // namespace cogniware

