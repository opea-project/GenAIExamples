#pragma once

#include <string>
#include <vector>
#include <memory>

namespace cogniware {
namespace training {

struct TrainingConfig {
    std::string model_id;
    std::string dataset_path;
    int epochs;
    int batch_size;
    float learning_rate;
    std::vector<int> gpu_ids;
};

struct Checkpoint {
    std::string checkpoint_id;
    int epoch;
    float loss;
    std::string path;
    std::chrono::system_clock::time_point created_at;
};

class TrainingInterface {
public:
    TrainingInterface();
    ~TrainingInterface();

    std::string startTraining(const TrainingConfig& config);
    bool stopTraining(const std::string& training_id);
    
    std::string saveCheckpoint(const std::string& training_id);
    bool loadCheckpoint(const std::string& checkpoint_id);
    
    std::vector<Checkpoint> listCheckpoints(const std::string& training_id);

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

} // namespace training
} // namespace cogniware

