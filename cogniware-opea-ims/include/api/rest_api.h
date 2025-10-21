#pragma once

#include <string>
#include <vector>
#include <memory>
#include <unordered_map>
#include <functional>
#include <chrono>

namespace cogniware {
namespace api {

/**
 * @brief HTTP methods
 */
enum class HttpMethod {
    GET,
    POST,
    PUT,
    DELETE,
    PATCH,
    OPTIONS,
    HEAD
};

/**
 * @brief HTTP status codes
 */
enum class HttpStatus {
    OK = 200,
    CREATED = 201,
    ACCEPTED = 202,
    NO_CONTENT = 204,
    BAD_REQUEST = 400,
    UNAUTHORIZED = 401,
    FORBIDDEN = 403,
    NOT_FOUND = 404,
    METHOD_NOT_ALLOWED = 405,
    CONFLICT = 409,
    INTERNAL_SERVER_ERROR = 500,
    NOT_IMPLEMENTED = 501,
    SERVICE_UNAVAILABLE = 503
};

/**
 * @brief HTTP request
 */
struct HttpRequest {
    HttpMethod method;
    std::string path;
    std::string body;
    std::unordered_map<std::string, std::string> headers;
    std::unordered_map<std::string, std::string> query_params;
    std::unordered_map<std::string, std::string> path_params;
    std::string client_ip;
};

/**
 * @brief HTTP response
 */
struct HttpResponse {
    HttpStatus status;
    std::string body;
    std::unordered_map<std::string, std::string> headers;
    
    HttpResponse() : status(HttpStatus::OK) {
        headers["Content-Type"] = "application/json";
    }
};

/**
 * @brief Route handler function
 */
using RouteHandler = std::function<HttpResponse(const HttpRequest&)>;

/**
 * @brief Middleware function
 */
using Middleware = std::function<bool(HttpRequest&, HttpResponse&)>;

/**
 * @brief REST API Server
 */
class RestAPIServer {
public:
    RestAPIServer(const std::string& host = "0.0.0.0", uint16_t port = 8080);
    ~RestAPIServer();

    // Server control
    bool start();
    bool stop();
    bool isRunning() const;
    
    // Route registration
    void registerRoute(HttpMethod method, const std::string& path, RouteHandler handler);
    void get(const std::string& path, RouteHandler handler);
    void post(const std::string& path, RouteHandler handler);
    void put(const std::string& path, RouteHandler handler);
    void del(const std::string& path, RouteHandler handler);
    void patch(const std::string& path, RouteHandler handler);
    
    // Middleware
    void use(Middleware middleware);
    
    // Configuration
    void setHost(const std::string& host);
    void setPort(uint16_t port);
    void enableCORS(bool enabled = true);
    void setMaxConnections(size_t max);
    void setRequestTimeout(std::chrono::seconds timeout);

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

/**
 * @brief REST API endpoints for Cogniware Core
 */
class CogniwareRestAPI {
public:
    explicit CogniwareRestAPI(uint16_t port = 8080);
    ~CogniwareRestAPI();

    // Server control
    bool start();
    bool stop();
    
    // Register all endpoints
    void registerAllEndpoints();

private:
    std::unique_ptr<RestAPIServer> server_;
    
    // Endpoint handlers
    
    // Health & Status
    HttpResponse handleHealthCheck(const HttpRequest& req);
    HttpResponse handleStatus(const HttpRequest& req);
    HttpResponse handleMetrics(const HttpRequest& req);
    
    // Model Management
    HttpResponse handleListModels(const HttpRequest& req);
    HttpResponse handleGetModel(const HttpRequest& req);
    HttpResponse handleLoadModel(const HttpRequest& req);
    HttpResponse handleUnloadModel(const HttpRequest& req);
    HttpResponse handleUpdateModel(const HttpRequest& req);
    
    // Inference
    HttpResponse handleInference(const HttpRequest& req);
    HttpResponse handleBatchInference(const HttpRequest& req);
    HttpResponse handleStreamInference(const HttpRequest& req);
    HttpResponse handleAsyncInference(const HttpRequest& req);
    HttpResponse handleInferenceStatus(const HttpRequest& req);
    
    // Multi-LLM Orchestration
    HttpResponse handleParallelInference(const HttpRequest& req);
    HttpResponse handleConsensusInference(const HttpRequest& req);
    HttpResponse handleOrchestration(const HttpRequest& req);
    
    // Resource Management
    HttpResponse handleResourceUsage(const HttpRequest& req);
    HttpResponse handleAllocateResource(const HttpRequest& req);
    HttpResponse handleReleaseResource(const HttpRequest& req);
    HttpResponse handleResourceQuota(const HttpRequest& req);
    
    // System Monitoring
    HttpResponse handleSystemInfo(const HttpRequest& req);
    HttpResponse handleCPUInfo(const HttpRequest& req);
    HttpResponse handleGPUInfo(const HttpRequest& req);
    HttpResponse handleMemoryInfo(const HttpRequest& req);
    
    // Configuration
    HttpResponse handleGetConfig(const HttpRequest& req);
    HttpResponse handleUpdateConfig(const HttpRequest& req);
    
    // Logs & Audit
    HttpResponse handleGetLogs(const HttpRequest& req);
    HttpResponse handleGetAudit(const HttpRequest& req);
    
    // Authentication
    HttpResponse handleLogin(const HttpRequest& req);
    HttpResponse handleLogout(const HttpRequest& req);
    HttpResponse handleRefreshToken(const HttpRequest& req);
    
    // Middleware
    bool authMiddleware(HttpRequest& req, HttpResponse& res);
    bool loggingMiddleware(HttpRequest& req, HttpResponse& res);
    bool rateLimitMiddleware(HttpRequest& req, HttpResponse& res);
    bool corsMiddleware(HttpRequest& req, HttpResponse& res);
};

/**
 * @brief JSON utilities
 */
class JsonUtils {
public:
    static std::string toJson(const std::unordered_map<std::string, std::string>& map);
    static std::string toJson(const std::vector<std::string>& vec);
    static std::unordered_map<std::string, std::string> fromJson(const std::string& json);
    static std::string escapeJson(const std::string& str);
};

/**
 * @brief API response builders
 */
class ResponseBuilder {
public:
    static HttpResponse success(const std::string& data);
    static HttpResponse created(const std::string& data);
    static HttpResponse noContent();
    static HttpResponse badRequest(const std::string& message);
    static HttpResponse unauthorized(const std::string& message);
    static HttpResponse forbidden(const std::string& message);
    static HttpResponse notFound(const std::string& message);
    static HttpResponse internalError(const std::string& message);
    
    static std::string errorJson(const std::string& message, int code);
    static std::string successJson(const std::string& message, const std::string& data = "");
};

} // namespace api
} // namespace cogniware

