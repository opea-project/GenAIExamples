#include "grpc/model_client.h"
#include <grpcpp/grpcpp.h>
#include <spdlog/spdlog.h>
#include <chrono>
#include <thread>

namespace cogniware {

ModelClient::ModelClient(const std::string& server_address)
    : stub_(ModelService::NewStub(
          grpc::CreateChannel(server_address, grpc::InsecureChannelCredentials()))) {
    spdlog::info("ModelClient initialized with server address: {}", server_address);
}

bool ModelClient::InitializeModel(const std::string& model_id, const ModelConfig& config) {
    InitializeModelRequest request;
    request.set_model_id(model_id);
    *request.mutable_config() = ConvertConfigToProto(config);

    InitializeModelResponse response;
    grpc::ClientContext context;

    auto status = stub_->InitializeModel(&context, request, &response);
    if (!status.ok()) {
        spdlog::error("InitializeModel RPC failed: {}", status.error_message());
        return false;
    }

    return response.success();
}

bool ModelClient::ShutdownModel(const std::string& model_id) {
    ShutdownModelRequest request;
    request.set_model_id(model_id);

    ShutdownModelResponse response;
    grpc::ClientContext context;

    auto status = stub_->ShutdownModel(&context, request, &response);
    if (!status.ok()) {
        spdlog::error("ShutdownModel RPC failed: {}", status.error_message());
        return false;
    }

    return response.success();
}

InferenceResult ModelClient::RunInference(const std::string& model_id,
                                        const std::vector<float>& input_data,
                                        const std::map<std::string, std::string>& parameters) {
    InferenceRequest request;
    request.set_model_id(model_id);
    *request.mutable_input_data() = {input_data.begin(), input_data.end()};
    for (const auto& [key, value] : parameters) {
        (*request.mutable_parameters())[key] = value;
    }

    InferenceResponse response;
    grpc::ClientContext context;

    auto status = stub_->RunInference(&context, request, &response);
    if (!status.ok()) {
        spdlog::error("RunInference RPC failed: {}", status.error_message());
        return InferenceResult{false, {}, {}};
    }

    if (!response.success()) {
        spdlog::error("RunInference failed: {}", response.error_message());
        return InferenceResult{false, {}, {}};
    }

    std::vector<float> output_data(response.output_data().begin(),
                                 response.output_data().end());
    std::map<std::string, float> metrics(response.metrics().begin(),
                                       response.metrics().end());

    return InferenceResult{true, output_data, metrics};
}

TrainingResult ModelClient::TrainModel(const std::string& model_id,
                                     const std::vector<float>& training_data,
                                     const TrainingConfig& config) {
    TrainingRequest request;
    request.set_model_id(model_id);
    *request.mutable_training_data() = {training_data.begin(), training_data.end()};
    *request.mutable_config() = ConvertTrainingConfigToProto(config);

    TrainingResponse response;
    grpc::ClientContext context;

    auto status = stub_->TrainModel(&context, request, &response);
    if (!status.ok()) {
        spdlog::error("TrainModel RPC failed: {}", status.error_message());
        return TrainingResult{false, {}, {}};
    }

    if (!response.success()) {
        spdlog::error("TrainModel failed: {}", response.error_message());
        return TrainingResult{false, {}, {}};
    }

    TrainingStatus status_result = ConvertProtoToTrainingStatus(response.status());
    std::map<std::string, float> metrics(response.metrics().begin(),
                                       response.metrics().end());

    return TrainingResult{true, status_result, metrics};
}

bool ModelClient::UpdateConfig(const std::string& model_id, const ModelConfig& config) {
    UpdateConfigRequest request;
    request.set_model_id(model_id);
    *request.mutable_config() = ConvertConfigToProto(config);

    UpdateConfigResponse response;
    grpc::ClientContext context;

    auto status = stub_->UpdateConfig(&context, request, &response);
    if (!status.ok()) {
        spdlog::error("UpdateConfig RPC failed: {}", status.error_message());
        return false;
    }

    return response.success();
}

std::optional<ModelConfig> ModelClient::GetConfig(const std::string& model_id) {
    GetConfigRequest request;
    request.set_model_id(model_id);

    GetConfigResponse response;
    grpc::ClientContext context;

    auto status = stub_->GetConfig(&context, request, &response);
    if (!status.ok()) {
        spdlog::error("GetConfig RPC failed: {}", status.error_message());
        return std::nullopt;
    }

    if (!response.success()) {
        spdlog::error("GetConfig failed: {}", response.error_message());
        return std::nullopt;
    }

    return ConvertProtoToConfig(response.config());
}

ResourceResult ModelClient::AllocateResources(const std::string& model_id,
                                            const std::string& resource_type,
                                            float amount,
                                            const std::map<std::string, std::string>& parameters) {
    ResourceRequest request;
    request.set_model_id(model_id);
    request.set_resource_type(resource_type);
    request.set_amount(amount);
    for (const auto& [key, value] : parameters) {
        (*request.mutable_parameters())[key] = value;
    }

    ResourceResponse response;
    grpc::ClientContext context;

    auto status = stub_->AllocateResources(&context, request, &response);
    if (!status.ok()) {
        spdlog::error("AllocateResources RPC failed: {}", status.error_message());
        return ResourceResult{false, 0.0f, {}};
    }

    if (!response.success()) {
        spdlog::error("AllocateResources failed: {}", response.error_message());
        return ResourceResult{false, 0.0f, {}};
    }

    std::map<std::string, float> metrics(response.metrics().begin(),
                                       response.metrics().end());

    return ResourceResult{true, response.allocated_amount(), metrics};
}

ResourceResult ModelClient::ReleaseResources(const std::string& model_id,
                                           const std::string& resource_type,
                                           float amount) {
    ResourceRequest request;
    request.set_model_id(model_id);
    request.set_resource_type(resource_type);
    request.set_amount(amount);

    ResourceResponse response;
    grpc::ClientContext context;

    auto status = stub_->ReleaseResources(&context, request, &response);
    if (!status.ok()) {
        spdlog::error("ReleaseResources RPC failed: {}", status.error_message());
        return ResourceResult{false, 0.0f, {}};
    }

    if (!response.success()) {
        spdlog::error("ReleaseResources failed: {}", response.error_message());
        return ResourceResult{false, 0.0f, {}};
    }

    std::map<std::string, float> metrics(response.metrics().begin(),
                                       response.metrics().end());

    return ResourceResult{true, response.allocated_amount(), metrics};
}

std::map<std::string, float> ModelClient::GetMetrics(const std::string& model_id,
                                                    const std::vector<std::string>& metric_names) {
    MetricsRequest request;
    request.set_model_id(model_id);
    *request.mutable_metric_names() = {metric_names.begin(), metric_names.end()};

    MetricsResponse response;
    grpc::ClientContext context;

    auto status = stub_->GetMetrics(&context, request, &response);
    if (!status.ok()) {
        spdlog::error("GetMetrics RPC failed: {}", status.error_message());
        return {};
    }

    return std::map<std::string, float>(response.metrics().begin(),
                                      response.metrics().end());
}

void ModelClient::StreamMetrics(const std::string& model_id,
                              const std::vector<std::string>& metric_names,
                              int interval_ms,
                              const MetricsCallback& callback) {
    MetricsRequest request;
    request.set_model_id(model_id);
    *request.mutable_metric_names() = {metric_names.begin(), metric_names.end()};
    request.set_interval_ms(interval_ms);

    grpc::ClientContext context;
    auto stream = stub_->StreamMetrics(&context, request);

    MetricsResponse response;
    while (stream->Read(&response)) {
        std::map<std::string, float> metrics(response.metrics().begin(),
                                           response.metrics().end());
        callback(response.model_id(), metrics, response.timestamp());
    }

    auto status = stream->Finish();
    if (!status.ok()) {
        spdlog::error("StreamMetrics failed: {}", status.error_message());
    }
}

ModelConfigProto ModelClient::ConvertConfigToProto(const ModelConfig& config) {
    ModelConfigProto proto;
    proto.set_model_id(config.model_id);
    proto.set_model_type(config.model_type);
    proto.set_model_path(config.model_path);
    for (const auto& [key, value] : config.parameters) {
        (*proto.mutable_parameters())[key] = value;
    }
    *proto.mutable_dependencies() = {config.dependencies.begin(),
                                   config.dependencies.end()};
    return proto;
}

ModelConfig ModelClient::ConvertProtoToConfig(const ModelConfigProto& proto) {
    ModelConfig config;
    config.model_id = proto.model_id();
    config.model_type = proto.model_type();
    config.model_path = proto.model_path();
    for (const auto& [key, value] : proto.parameters()) {
        config.parameters[key] = value;
    }
    config.dependencies = {proto.dependencies().begin(),
                         proto.dependencies().end()};
    return config;
}

TrainingConfigProto ModelClient::ConvertTrainingConfigToProto(const TrainingConfig& config) {
    TrainingConfigProto proto;
    proto.set_epochs(config.epochs);
    proto.set_learning_rate(config.learning_rate);
    proto.set_optimizer(config.optimizer);
    for (const auto& [key, value] : config.parameters) {
        (*proto.mutable_parameters())[key] = value;
    }
    return proto;
}

TrainingStatus ModelClient::ConvertProtoToTrainingStatus(const TrainingStatusProto& proto) {
    TrainingStatus status;
    status.model_id = proto.model_id();
    status.state = proto.state();
    status.current_epoch = proto.current_epoch();
    status.progress = proto.progress();
    status.metrics = std::map<std::string, float>(proto.metrics().begin(),
                                                proto.metrics().end());
    return status;
}

} // namespace cogniware 