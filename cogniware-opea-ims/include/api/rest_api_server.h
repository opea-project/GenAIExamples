#ifndef MSMARTCOMPUTE_REST_API_SERVER_H
#define MSMARTCOMPUTE_REST_API_SERVER_H

#include <string>
#include <memory>
#include <thread>
#include <atomic>
#include <httplib.h>

namespace cogniware {

// Server configuration
struct ServerConfig {
    std::string host = "localhost";
    int port = 8080;
    int deviceId = 0;
    int numStreams = 4;
    int monitoringInterval = 100;
    bool enableTensorCores = true;
    bool enableMixedPrecision = true;
    int optimizationLevel = 2;
    int maxConnections = 1000;
    int requestTimeout = 30;
    bool enableCORS = true;
    std::string logLevel = "info";
};

// REST API Server Class
class RESTServer {
public:
    static RESTServer& getInstance();
    
    // Disable copy constructor and assignment operator
    RESTServer(const RESTServer&) = delete;
    RESTServer& operator=(const RESTServer&) = delete;
    
    // Initialization and shutdown
    bool initialize(const ServerConfig& config);
    void shutdown();
    bool isRunning() const { return running_; }
    
    // Configuration
    ServerConfig getConfig() const { return config_; }
    bool updateConfig(const ServerConfig& config);

private:
    RESTServer() = default;
    ~RESTServer() = default;
    
    // Internal state
    bool running_ = false;
    ServerConfig config_;
    std::unique_ptr<httplib::Server> server_;
    std::thread serverThread_;
    
    // Route handlers
    void setupRoutes();
    void handleLoadModel(const httplib::Request& req, httplib::Response& res);
    void handleUnloadModel(const httplib::Request& req, httplib::Response& res);
    void handleListModels(const httplib::Response& res);
    void handleInference(const httplib::Request& req, httplib::Response& res);
    void handleAsyncInference(const httplib::Request& req, httplib::Response& res);
    void handleGetInferenceResult(const httplib::Request& req, httplib::Response& res);
    void handleTraining(const httplib::Request& req, httplib::Response& res);
    void handleAsyncTraining(const httplib::Request& req, httplib::Response& res);
    void handleGetTrainingResult(const httplib::Request& req, httplib::Response& res);
    void handleCreateSession(const httplib::Request& req, httplib::Response& res);
    void handleEndSession(const httplib::Request& req, httplib::Response& res);
    void handleGetMetrics(const httplib::Response& res);
    void handleGetMetricsHistory(const httplib::Request& req, httplib::Response& res);
    void handleAllocateResources(const httplib::Request& req, httplib::Response& res);
    void handleDeallocateResources(const httplib::Request& req, httplib::Response& res);
    
    // Utility functions
    std::string generateRequestId();
};

} // namespace cogniware

#endif // MSMARTCOMPUTE_REST_API_SERVER_H 