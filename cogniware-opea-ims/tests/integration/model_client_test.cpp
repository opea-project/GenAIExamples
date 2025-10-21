#include <gtest/gtest.h>
#include <grpcpp/grpcpp.h>
#include <memory>
#include <thread>
#include <chrono>
#include <future>

#include "grpc/model_client.h"
#include "common_interfaces/protos/model_service.grpc.pb.h"

using namespace cogniware;

class ModelClientTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Start the server in a separate thread
        server_thread_ = std::thread([this]() {
            grpc::ServerBuilder builder;
            builder.AddListeningPort("localhost:50051", grpc::InsecureServerCredentials());
            builder.RegisterService(&service_);
            server_ = builder.BuildAndStart();
            server_->Wait();
        });

        // Wait for server to start
        std::this_thread::sleep_for(std::chrono::seconds(1));

        // Create client
        client_ = std::make_unique<ModelClient>("localhost:50051");
    }

    void TearDown() override {
        if (server_) {
            server_->Shutdown();
        }
        if (server_thread_.joinable()) {
            server_thread_.join();
        }
    }

    std::unique_ptr<ModelClient> client_;
    std::unique_ptr<grpc::Server> server_;
    std::thread server_thread_;
    ModelServiceServicer service_;
};

TEST_F(ModelClientTest, InitializeModel) {
    ModelConfig config{
        .model_id = "test-model",
        .model_type = "transformer",
        .model_path = "/path/to/model",
        .parameters = {{"batch_size", "32"}},
        .dependencies = {"torch"}
    };

    bool success = client_->InitializeModel("test-model", config);
    EXPECT_TRUE(success);
}

TEST_F(ModelClientTest, RunInference) {
    // First initialize the model
    ModelConfig config{
        .model_id = "test-model",
        .model_type = "transformer",
        .model_path = "/path/to/model",
        .parameters = {{"batch_size", "32"}},
        .dependencies = {"torch"}
    };
    client_->InitializeModel("test-model", config);

    // Run inference
    std::vector<float> input_data = {0.1f, 0.2f, 0.3f, 0.4f, 0.5f};
    std::map<std::string, std::string> parameters = {{"temperature", "0.7"}};

    auto result = client_->RunInference("test-model", input_data, parameters);
    EXPECT_TRUE(result.success);
    EXPECT_FALSE(result.output_data.empty());
}

TEST_F(ModelClientTest, ModelVersioning) {
    // Create a new version
    auto version_result = client_->CreateVersion("test-model", "1.0.0", "Test version");
    EXPECT_TRUE(version_result.success);
    EXPECT_FALSE(version_result.version_id.empty());

    // List versions
    auto versions = client_->ListVersions("test-model");
    EXPECT_FALSE(versions.empty());
    EXPECT_EQ(versions[0].version, "1.0.0");
}

TEST_F(ModelClientTest, ResourceManagement) {
    // Allocate resources
    auto alloc_result = client_->AllocateResources(
        "test-model",
        "gpu",
        1.0f,
        {{"device", "cuda:0"}}
    );
    EXPECT_TRUE(alloc_result.success);
    EXPECT_GT(alloc_result.allocated_amount, 0.0f);

    // Get resource usage
    auto usage = client_->GetResourceUsage("test-model", "gpu");
    EXPECT_GT(usage.total_allocated, 0.0f);
}

TEST_F(ModelClientTest, HealthCheck) {
    auto health = client_->GetHealthStatus("test-model");
    EXPECT_EQ(health.status, HealthStatus::HEALTHY);
    EXPECT_FALSE(health.details.empty());
}

TEST_F(ModelClientTest, ErrorHandling) {
    // Test with invalid model ID
    std::vector<float> input_data = {0.1f, 0.2f, 0.3f};
    std::map<std::string, std::string> parameters;

    auto result = client_->RunInference("non-existent-model", input_data, parameters);
    EXPECT_FALSE(result.success);
}

TEST_F(ModelClientTest, MetricsStreaming) {
    std::vector<std::string> metric_names = {"accuracy", "loss"};
    std::promise<void> metrics_received;
    bool metrics_callback_called = false;

    client_->StreamMetrics(
        "test-model",
        metric_names,
        1000,
        [&](const std::string& model_id,
            const std::map<std::string, float>& metrics,
            int64_t timestamp) {
            EXPECT_EQ(model_id, "test-model");
            EXPECT_FALSE(metrics.empty());
            metrics_callback_called = true;
            metrics_received.set_value();
        }
    );

    // Wait for metrics to be received
    auto future = metrics_received.get_future();
    EXPECT_EQ(future.wait_for(std::chrono::seconds(5)), std::future_status::ready);
    EXPECT_TRUE(metrics_callback_called);
}

TEST_F(ModelClientTest, ModelBackup) {
    // Create a backup
    auto backup_result = client_->CreateBackup(
        "test-model",
        "test-backup",
        {{"description", "Test backup"}}
    );
    EXPECT_TRUE(backup_result.success);
    EXPECT_FALSE(backup_result.backup_id.empty());

    // List backups
    auto backups = client_->ListBackups("test-model");
    EXPECT_FALSE(backups.empty());
    EXPECT_EQ(backups[0].backup_name, "test-backup");

    // Restore backup
    auto restore_result = client_->RestoreBackup(
        "test-model",
        backup_result.backup_id
    );
    EXPECT_TRUE(restore_result.success);
}

TEST_F(ModelClientTest, ModelEvaluation) {
    std::vector<float> test_data = {0.1f, 0.2f, 0.3f, 0.4f, 0.5f};
    std::map<std::string, std::string> parameters = {{"batch_size", "32"}};

    auto result = client_->EvaluateModel("test-model", test_data, parameters);
    EXPECT_TRUE(result.success);
    EXPECT_FALSE(result.metrics.empty());
    EXPECT_FALSE(result.detailed_metrics.empty());
}

TEST_F(ModelClientTest, ModelExport) {
    auto result = client_->ExportModel(
        "test-model",
        "onnx",
        "/path/to/export",
        {{"opset_version", "12"}}
    );
    EXPECT_TRUE(result.success);
    EXPECT_FALSE(result.exported_path.empty());
    EXPECT_FALSE(result.metadata.empty());
}

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
} 