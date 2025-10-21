#include "grpc/model_client.h"
#include <spdlog/spdlog.h>
#include <chrono>
#include <thread>
#include <vector>
#include <map>

using namespace cogniware;

void metrics_callback(const std::string& model_id,
                     const std::map<std::string, float>& metrics,
                     int64_t timestamp) {
    spdlog::info("Received metrics for model {} at timestamp {}:", model_id, timestamp);
    for (const auto& [name, value] : metrics) {
        spdlog::info("  {}: {}", name, value);
    }
}

int main() {
    try {
        // Create client
        ModelClient client("localhost:50051");
        spdlog::info("Created ModelClient instance");

        // Initialize a model
        std::string model_id = "example_model";
        ModelConfig config{
            .model_id = model_id,
            .model_type = "transformer",
            .model_path = "/path/to/model",
            .parameters = {
                {"batch_size", "32"},
                {"max_length", "512"}
            },
            .dependencies = {"torch", "transformers"}
        };

        bool init_success = client.InitializeModel(model_id, config);
        if (!init_success) {
            spdlog::error("Failed to initialize model");
            return 1;
        }
        spdlog::info("Model initialized successfully");

        // Run inference
        std::vector<float> input_data = {0.1f, 0.2f, 0.3f, 0.4f, 0.5f};
        std::map<std::string, std::string> inference_params = {
            {"temperature", "0.7"}
        };

        auto inference_result = client.RunInference(model_id, input_data, inference_params);
        if (!inference_result.success) {
            spdlog::error("Inference failed");
            return 1;
        }

        spdlog::info("Inference completed successfully");
        spdlog::info("Output data size: {}", inference_result.output_data.size());
        for (const auto& [name, value] : inference_result.metrics) {
            spdlog::info("Metric {}: {}", name, value);
        }

        // Train the model
        std::vector<float> training_data = {0.1f, 0.2f, 0.3f, 0.4f, 0.5f};
        TrainingConfig training_config{
            .epochs = 10,
            .learning_rate = 0.001f,
            .optimizer = "adam",
            .parameters = {
                {"batch_size", "32"}
            }
        };

        auto training_result = client.TrainModel(model_id, training_data, training_config);
        if (!training_result.success) {
            spdlog::error("Training failed");
            return 1;
        }

        spdlog::info("Training completed successfully");
        spdlog::info("Training status: {}", training_result.status.state);
        spdlog::info("Current epoch: {}", training_result.status.current_epoch);
        spdlog::info("Progress: {}", training_result.status.progress);
        for (const auto& [name, value] : training_result.metrics) {
            spdlog::info("Metric {}: {}", name, value);
        }

        // Get model metrics
        std::vector<std::string> metric_names = {"accuracy", "loss"};
        auto metrics = client.GetMetrics(model_id, metric_names);
        spdlog::info("Current metrics:");
        for (const auto& [name, value] : metrics) {
            spdlog::info("  {}: {}", name, value);
        }

        // Stream metrics for 5 seconds
        spdlog::info("Starting metrics streaming...");
        client.StreamMetrics(model_id, metric_names, 1000, metrics_callback);
        std::this_thread::sleep_for(std::chrono::seconds(5));

        // Allocate resources
        auto alloc_result = client.AllocateResources(
            model_id,
            "gpu",
            1.0f,
            {{"device", "cuda:0"}}
        );
        if (!alloc_result.success) {
            spdlog::error("Resource allocation failed");
            return 1;
        }
        spdlog::info("Resources allocated successfully");
        spdlog::info("Allocated amount: {}", alloc_result.allocated_amount);
        for (const auto& [name, value] : alloc_result.metrics) {
            spdlog::info("Resource metric {}: {}", name, value);
        }

        // Release resources
        auto release_result = client.ReleaseResources(model_id, "gpu", 1.0f);
        if (!release_result.success) {
            spdlog::error("Resource release failed");
            return 1;
        }
        spdlog::info("Resources released successfully");
        for (const auto& [name, value] : release_result.metrics) {
            spdlog::info("Resource metric {}: {}", name, value);
        }

        // Shutdown the model
        bool shutdown_success = client.ShutdownModel(model_id);
        if (!shutdown_success) {
            spdlog::error("Model shutdown failed");
            return 1;
        }
        spdlog::info("Model shut down successfully");

    } catch (const std::exception& e) {
        spdlog::error("Error occurred: {}", e.what());
        return 1;
    }

    return 0;
} 