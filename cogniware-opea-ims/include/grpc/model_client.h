#pragma once

#include <string>
#include <vector>
#include <map>
#include <optional>
#include <functional>
#include <memory>

#include "common_interfaces/protos/model_service.grpc.pb.h"

namespace cogniware {

struct ModelConfig {
    std::string model_id;
    std::string model_type;
    std::string model_path;
    std::map<std::string, std::string> parameters;
    std::vector<std::string> dependencies;
};

struct TrainingConfig {
    int epochs;
    float learning_rate;
    std::string optimizer;
    std::map<std::string, std::string> parameters;
};

struct TrainingStatus {
    std::string model_id;
    std::string state;
    int current_epoch;
    float progress;
    std::map<std::string, float> metrics;
};

struct InferenceResult {
    bool success;
    std::vector<float> output_data;
    std::map<std::string, float> metrics;
};

struct TrainingResult {
    bool success;
    TrainingStatus status;
    std::map<std::string, float> metrics;
};

struct ResourceResult {
    bool success;
    float allocated_amount;
    std::map<std::string, float> metrics;
};

using MetricsCallback = std::function<void(const std::string& model_id,
                                         const std::map<std::string, float>& metrics,
                                         int64_t timestamp)>;

class ModelClient {
public:
    explicit ModelClient(const std::string& server_address);

    // Model lifecycle management
    bool InitializeModel(const std::string& model_id, const ModelConfig& config);
    bool ShutdownModel(const std::string& model_id);

    // Model operations
    InferenceResult RunInference(const std::string& model_id,
                               const std::vector<float>& input_data,
                               const std::map<std::string, std::string>& parameters);
    TrainingResult TrainModel(const std::string& model_id,
                            const std::vector<float>& training_data,
                            const TrainingConfig& config);

    // Configuration management
    bool UpdateConfig(const std::string& model_id, const ModelConfig& config);
    std::optional<ModelConfig> GetConfig(const std::string& model_id);

    // Resource management
    ResourceResult AllocateResources(const std::string& model_id,
                                   const std::string& resource_type,
                                   float amount,
                                   const std::map<std::string, std::string>& parameters);
    ResourceResult ReleaseResources(const std::string& model_id,
                                  const std::string& resource_type,
                                  float amount);

    // Monitoring
    std::map<std::string, float> GetMetrics(const std::string& model_id,
                                          const std::vector<std::string>& metric_names);
    void StreamMetrics(const std::string& model_id,
                      const std::vector<std::string>& metric_names,
                      int interval_ms,
                      const MetricsCallback& callback);

private:
    // Protocol buffer conversion helpers
    ModelConfigProto ConvertConfigToProto(const ModelConfig& config);
    ModelConfig ConvertProtoToConfig(const ModelConfigProto& proto);
    TrainingConfigProto ConvertTrainingConfigToProto(const TrainingConfig& config);
    TrainingStatus ConvertProtoToTrainingStatus(const TrainingStatusProto& proto);

    std::unique_ptr<ModelService::Stub> stub_;
};

} // namespace cogniware 