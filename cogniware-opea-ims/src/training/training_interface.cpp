#include "training/training_interface.h"
#include <mutex>

namespace cogniware {
namespace training {

class TrainingInterface::Impl {
public:
    std::unordered_map<std::string, TrainingConfig> trainings;
    std::unordered_map<std::string, std::vector<Checkpoint>> checkpoints;
    mutable std::mutex mutex;
    std::atomic<uint64_t> training_counter{0};
};

TrainingInterface::TrainingInterface() : pImpl(std::make_unique<Impl>()) {}
TrainingInterface::~TrainingInterface() = default;

std::string TrainingInterface::startTraining(const TrainingConfig& config) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    std::string training_id = "training_" + std::to_string(++pImpl->training_counter);
    pImpl->trainings[training_id] = config;
    return training_id;
}

bool TrainingInterface::stopTraining(const std::string& training_id) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    return pImpl->trainings.erase(training_id) > 0;
}

std::string TrainingInterface::saveCheckpoint(const std::string& training_id) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    Checkpoint cp;
    cp.checkpoint_id = training_id + "_checkpoint_" + std::to_string(pImpl->checkpoints[training_id].size());
    cp.epoch = pImpl->checkpoints[training_id].size();
    cp.loss = 0.5f;
    cp.created_at = std::chrono::system_clock::now();
    pImpl->checkpoints[training_id].push_back(cp);
    return cp.checkpoint_id;
}

bool TrainingInterface::loadCheckpoint(const std::string&) {
    return true;
}

std::vector<Checkpoint> TrainingInterface::listCheckpoints(const std::string& training_id) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    return pImpl->checkpoints[training_id];
}

} // namespace training
} // namespace cogniware

