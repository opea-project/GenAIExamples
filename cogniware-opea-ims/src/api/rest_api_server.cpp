#include "rest_api_server.h"
#include "cognidream_platform_api.h"
#include <spdlog/spdlog.h>
#include <httplib.h>
#include <nlohmann/json.hpp>
#include <thread>
#include <chrono>

namespace cogniware {

RESTServer& RESTServer::getInstance() {
    static RESTServer instance;
    return instance;
}

bool RESTServer::initialize(const ServerConfig& config) {
    config_ = config;
    
    // Initialize CogniDream Platform API
    nlohmann::json apiConfig;
    apiConfig["device_id"] = config.deviceId;
    apiConfig["num_streams"] = config.numStreams;
    apiConfig["monitoring_interval"] = config.monitoringInterval;
    apiConfig["enable_tensor_cores"] = config.enableTensorCores;
    apiConfig["enable_mixed_precision"] = config.enableMixedPrecision;
    apiConfig["optimization_level"] = config.optimizationLevel;
    
    if (!CogniDreamPlatformAPI::getInstance().initialize(apiConfig)) {
        spdlog::error("Failed to initialize CogniDream Platform API");
        return false;
    }
    
    // Setup HTTP server
    server_ = std::make_unique<httplib::Server>();
    
    // Setup CORS
    server_->set_default_headers({
        {"Access-Control-Allow-Origin", "*"},
        {"Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS"},
        {"Access-Control-Allow-Headers", "Content-Type, Authorization"}
    });
    
    // Setup routes
    setupRoutes();
    
    // Start server in background thread
    running_ = true;
    serverThread_ = std::thread([this]() {
        if (!server_->listen(config_.host.c_str(), config_.port)) {
            spdlog::error("Failed to start HTTP server on {}:{}", config_.host, config_.port);
            running_ = false;
        }
    });
    
    spdlog::info("REST API Server started on {}:{}", config_.host, config_.port);
    return true;
}

void RESTServer::shutdown() {
    if (!running_) return;
    
    running_ = false;
    
    // Stop HTTP server
    if (server_) {
        server_->stop();
    }
    
    // Wait for server thread
    if (serverThread_.joinable()) {
        serverThread_.join();
    }
    
    // Shutdown CogniDream Platform API
    CogniDreamPlatformAPI::getInstance().shutdown();
    
    spdlog::info("REST API Server shutdown completed");
}

void RESTServer::setupRoutes() {
    // Health check
    server_->Get("/health", [](const httplib::Request&, httplib::Response& res) {
        nlohmann::json response = {
            {"status", "healthy"},
            {"timestamp", std::chrono::system_clock::now().time_since_epoch().count()},
            {"version", "1.0.0"}
        };
        res.set_content(response.dump(), "application/json");
    });
    
    // Model management endpoints
    server_->Post("/api/v1/models", [this](const httplib::Request& req, httplib::Response& res) {
        handleLoadModel(req, res);
    });
    
    server_->Delete("/api/v1/models/(.*)", [this](const httplib::Request& req, httplib::Response& res) {
        handleUnloadModel(req, res);
    });
    
    server_->Get("/api/v1/models", [this](const httplib::Request&, httplib::Response& res) {
        handleListModels(res);
    });
    
    // Inference endpoints
    server_->Post("/api/v1/inference", [this](const httplib::Request& req, httplib::Response& res) {
        handleInference(req, res);
    });
    
    server_->Post("/api/v1/inference/async", [this](const httplib::Request& req, httplib::Response& res) {
        handleAsyncInference(req, res);
    });
    
    server_->Get("/api/v1/inference/(.*)", [this](const httplib::Request& req, httplib::Response& res) {
        handleGetInferenceResult(req, res);
    });
    
    // Training endpoints
    server_->Post("/api/v1/training", [this](const httplib::Request& req, httplib::Response& res) {
        handleTraining(req, res);
    });
    
    server_->Post("/api/v1/training/async", [this](const httplib::Request& req, httplib::Response& res) {
        handleAsyncTraining(req, res);
    });
    
    server_->Get("/api/v1/training/(.*)", [this](const httplib::Request& req, httplib::Response& res) {
        handleGetTrainingResult(req, res);
    });
    
    // Session management
    server_->Post("/api/v1/sessions", [this](const httplib::Request& req, httplib::Response& res) {
        handleCreateSession(req, res);
    });
    
    server_->Delete("/api/v1/sessions/(.*)", [this](const httplib::Request& req, httplib::Response& res) {
        handleEndSession(req, res);
    });
    
    // Performance monitoring
    server_->Get("/api/v1/metrics", [this](const httplib::Request&, httplib::Response& res) {
        handleGetMetrics(res);
    });
    
    server_->Get("/api/v1/metrics/history", [this](const httplib::Request& req, httplib::Response& res) {
        handleGetMetricsHistory(req, res);
    });
    
    // Resource management
    server_->Post("/api/v1/resources", [this](const httplib::Request& req, httplib::Response& res) {
        handleAllocateResources(req, res);
    });
    
    server_->Delete("/api/v1/resources/(.*)", [this](const httplib::Request& req, httplib::Response& res) {
        handleDeallocateResources(req, res);
    });
    
    // Error handler
    server_->set_exception_handler([](const auto& req, auto& res, std::exception_ptr ep) {
        try {
            std::rethrow_exception(ep);
        } catch (const std::exception& e) {
            nlohmann::json error = {
                {"error", "Internal server error"},
                {"message", e.what()},
                {"status", 500}
            };
            res.status = 500;
            res.set_content(error.dump(), "application/json");
        }
    });
}

void RESTServer::handleLoadModel(const httplib::Request& req, httplib::Response& res) {
    try {
        auto json = nlohmann::json::parse(req.body);
        
        ModelConfig config;
        config.modelId = json["model_id"];
        config.modelType = json["model_type"];
        config.modelPath = json["model_path"];
        config.maxBatchSize = json.value("max_batch_size", 32);
        config.maxSequenceLength = json.value("max_sequence_length", 512);
        config.enableQuantization = json.value("enable_quantization", false);
        config.enableTensorCores = json.value("enable_tensor_cores", true);
        config.enableMixedPrecision = json.value("enable_mixed_precision", true);
        config.parameters = json.value("parameters", nlohmann::json::object());
        
        bool success = CogniDreamPlatformAPI::getInstance().loadModel(config);
        
        if (success) {
            nlohmann::json response = {
                {"success", true},
                {"model_id", config.modelId},
                {"message", "Model loaded successfully"}
            };
            res.set_content(response.dump(), "application/json");
        } else {
            nlohmann::json response = {
                {"success", false},
                {"error", CogniDreamPlatformAPI::getInstance().getLastError()}
            };
            res.status = 400;
            res.set_content(response.dump(), "application/json");
        }
        
    } catch (const std::exception& e) {
        nlohmann::json response = {
            {"success", false},
            {"error", "Invalid request format"},
            {"message", e.what()}
        };
        res.status = 400;
        res.set_content(response.dump(), "application/json");
    }
}

void RESTServer::handleUnloadModel(const httplib::Request& req, httplib::Response& res) {
    std::string modelId = req.matches[1];
    
    bool success = CogniDreamPlatformAPI::getInstance().unloadModel(modelId);
    
    nlohmann::json response = {
        {"success", success},
        {"model_id", modelId}
    };
    
    if (!success) {
        response["error"] = "Model not found or failed to unload";
        res.status = 404;
    }
    
    res.set_content(response.dump(), "application/json");
}

void RESTServer::handleListModels(const httplib::Response& res) {
    auto models = CogniDreamPlatformAPI::getInstance().getLoadedModels();
    
    nlohmann::json response = {
        {"success", true},
        {"models", models}
    };
    
    res.set_content(response.dump(), "application/json");
}

void RESTServer::handleInference(const httplib::Request& req, httplib::Response& res) {
    try {
        auto json = nlohmann::json::parse(req.body);
        
        InferenceRequest request;
        request.requestId = json.value("request_id", generateRequestId());
        request.modelId = json["model_id"];
        request.batchSize = json["batch_size"];
        request.sequenceLength = json["sequence_length"];
        request.dataType = json.value("data_type", "float32");
        request.options = json.value("options", nlohmann::json::object());
        
        // Parse input data
        auto inputData = json["input_data"];
        for (const auto& batch : inputData) {
            std::vector<float> batchData = batch.get<std::vector<float>>();
            request.inputData.push_back(batchData);
        }
        
        auto response = CogniDreamPlatformAPI::getInstance().executeInference(request);
        
        nlohmann::json result = {
            {"success", response.success},
            {"request_id", response.requestId},
            {"inference_time", response.inferenceTime}
        };
        
        if (response.success) {
            result["output_data"] = response.outputData;
        } else {
            result["error"] = response.errorMessage;
            res.status = 400;
        }
        
        res.set_content(result.dump(), "application/json");
        
    } catch (const std::exception& e) {
        nlohmann::json response = {
            {"success", false},
            {"error", "Invalid request format"},
            {"message", e.what()}
        };
        res.status = 400;
        res.set_content(response.dump(), "application/json");
    }
}

void RESTServer::handleTraining(const httplib::Request& req, httplib::Response& res) {
    try {
        auto json = nlohmann::json::parse(req.body);
        
        TrainingRequest request;
        request.requestId = json.value("request_id", generateRequestId());
        request.modelId = json["model_id"];
        request.epochs = json["epochs"];
        request.learningRate = json["learning_rate"];
        request.optimizer = json.value("optimizer", "adam");
        request.lossFunction = json.value("loss_function", "cross_entropy");
        request.hyperparameters = json.value("hyperparameters", nlohmann::json::object());
        
        // Parse training data
        auto trainingData = json["training_data"];
        for (const auto& batch : trainingData) {
            std::vector<float> batchData = batch.get<std::vector<float>>();
            request.trainingData.push_back(batchData);
        }
        
        // Parse labels
        auto labels = json["labels"];
        for (const auto& batch : labels) {
            std::vector<float> batchData = batch.get<std::vector<float>>();
            request.labels.push_back(batchData);
        }
        
        auto response = CogniDreamPlatformAPI::getInstance().executeTraining(request);
        
        nlohmann::json result = {
            {"success", response.success},
            {"request_id", response.requestId},
            {"training_time", response.trainingTime}
        };
        
        if (response.success) {
            result["final_loss"] = response.finalLoss;
            result["loss_history"] = response.lossHistory;
        } else {
            result["error"] = response.errorMessage;
            res.status = 400;
        }
        
        res.set_content(result.dump(), "application/json");
        
    } catch (const std::exception& e) {
        nlohmann::json response = {
            {"success", false},
            {"error", "Invalid request format"},
            {"message", e.what()}
        };
        res.status = 400;
        res.set_content(response.dump(), "application/json");
    }
}

void RESTServer::handleCreateSession(const httplib::Request& req, httplib::Response& res) {
    try {
        auto json = nlohmann::json::parse(req.body);
        
        std::string userId = json["user_id"];
        std::string modelId = json["model_id"];
        
        std::string sessionId = CogniDreamPlatformAPI::getInstance().createSession(userId, modelId);
        
        if (!sessionId.empty()) {
            nlohmann::json response = {
                {"success", true},
                {"session_id", sessionId},
                {"user_id", userId},
                {"model_id", modelId}
            };
            res.set_content(response.dump(), "application/json");
        } else {
            nlohmann::json response = {
                {"success", false},
                {"error", CogniDreamPlatformAPI::getInstance().getLastError()}
            };
            res.status = 400;
            res.set_content(response.dump(), "application/json");
        }
        
    } catch (const std::exception& e) {
        nlohmann::json response = {
            {"success", false},
            {"error", "Invalid request format"},
            {"message", e.what()}
        };
        res.status = 400;
        res.set_content(response.dump(), "application/json");
    }
}

void RESTServer::handleEndSession(const httplib::Request& req, httplib::Response& res) {
    std::string sessionId = req.matches[1];
    
    bool success = CogniDreamPlatformAPI::getInstance().endSession(sessionId);
    
    nlohmann::json response = {
        {"success", success},
        {"session_id", sessionId}
    };
    
    if (!success) {
        response["error"] = "Session not found";
        res.status = 404;
    }
    
    res.set_content(response.dump(), "application/json");
}

void RESTServer::handleGetMetrics(const httplib::Response& res) {
    auto metrics = CogniDreamPlatformAPI::getInstance().getPerformanceMetrics();
    
    nlohmann::json response = {
        {"success", true},
        {"metrics", {
            {"gpu_utilization", metrics.gpuUtilization},
            {"memory_utilization", metrics.memoryUtilization},
            {"temperature", metrics.temperature},
            {"power_usage", metrics.powerUsage},
            {"throughput", metrics.throughput},
            {"latency", metrics.latency},
            {"active_requests", metrics.activeRequests},
            {"queued_requests", metrics.queuedRequests}
        }}
    };
    
    res.set_content(response.dump(), "application/json");
}

std::string RESTServer::generateRequestId() {
    static std::atomic<int> counter{0};
    auto timestamp = std::chrono::system_clock::now().time_since_epoch().count();
    return "req_" + std::to_string(timestamp) + "_" + std::to_string(++counter);
}

// Placeholder implementations for async operations
void RESTServer::handleAsyncInference(const httplib::Request& req, httplib::Response& res) {
    // Implementation for async inference
    nlohmann::json response = {
        {"success", true},
        {"message", "Async inference not yet implemented"}
    };
    res.set_content(response.dump(), "application/json");
}

void RESTServer::handleAsyncTraining(const httplib::Request& req, httplib::Response& res) {
    // Implementation for async training
    nlohmann::json response = {
        {"success", true},
        {"message", "Async training not yet implemented"}
    };
    res.set_content(response.dump(), "application/json");
}

void RESTServer::handleGetInferenceResult(const httplib::Request& req, httplib::Response& res) {
    // Implementation for getting inference result
    nlohmann::json response = {
        {"success", true},
        {"message", "Get inference result not yet implemented"}
    };
    res.set_content(response.dump(), "application/json");
}

void RESTServer::handleGetTrainingResult(const httplib::Request& req, httplib::Response& res) {
    // Implementation for getting training result
    nlohmann::json response = {
        {"success", true},
        {"message", "Get training result not yet implemented"}
    };
    res.set_content(response.dump(), "application/json");
}

void RESTServer::handleGetMetricsHistory(const httplib::Request& req, httplib::Response& res) {
    // Implementation for getting metrics history
    nlohmann::json response = {
        {"success", true},
        {"message", "Metrics history not yet implemented"}
    };
    res.set_content(response.dump(), "application/json");
}

void RESTServer::handleAllocateResources(const httplib::Request& req, httplib::Response& res) {
    // Implementation for resource allocation
    nlohmann::json response = {
        {"success", true},
        {"message", "Resource allocation not yet implemented"}
    };
    res.set_content(response.dump(), "application/json");
}

void RESTServer::handleDeallocateResources(const httplib::Request& req, httplib::Response& res) {
    // Implementation for resource deallocation
    nlohmann::json response = {
        {"success", true},
        {"message", "Resource deallocation not yet implemented"}
    };
    res.set_content(response.dump(), "application/json");
}

} // namespace cogniware 