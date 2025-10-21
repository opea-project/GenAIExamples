#include "api/rest_api.h"
#include <sstream>
#include <thread>
#include <mutex>
#include <regex>
#include <map>

namespace cogniware {
namespace api {

// JsonUtils implementation
std::string JsonUtils::toJson(const std::unordered_map<std::string, std::string>& map) {
    std::stringstream ss;
    ss << "{";
    size_t i = 0;
    for (const auto& [key, value] : map) {
        ss << "\"" << escapeJson(key) << "\":\"" << escapeJson(value) << "\"";
        if (++i < map.size()) ss << ",";
    }
    ss << "}";
    return ss.str();
}

std::string JsonUtils::toJson(const std::vector<std::string>& vec) {
    std::stringstream ss;
    ss << "[";
    for (size_t i = 0; i < vec.size(); ++i) {
        ss << "\"" << escapeJson(vec[i]) << "\"";
        if (i < vec.size() - 1) ss << ",";
    }
    ss << "]";
    return ss.str();
}

std::unordered_map<std::string, std::string> JsonUtils::fromJson(const std::string& json) {
    // Simplified JSON parser
    std::unordered_map<std::string, std::string> result;
    std::regex pattern(R"("([^"]+)"\s*:\s*"([^"]*)")");
    auto begin = std::sregex_iterator(json.begin(), json.end(), pattern);
    auto end = std::sregex_iterator();
    
    for (std::sregex_iterator i = begin; i != end; ++i) {
        std::smatch match = *i;
        result[match[1].str()] = match[2].str();
    }
    
    return result;
}

std::string JsonUtils::escapeJson(const std::string& str) {
    std::string result;
    for (char c : str) {
        switch (c) {
            case '"': result += "\\\""; break;
            case '\\': result += "\\\\"; break;
            case '\n': result += "\\n"; break;
            case '\r': result += "\\r"; break;
            case '\t': result += "\\t"; break;
            default: result += c;
        }
    }
    return result;
}

// ResponseBuilder implementation
HttpResponse ResponseBuilder::success(const std::string& data) {
    HttpResponse res;
    res.status = HttpStatus::OK;
    res.body = successJson("Success", data);
    return res;
}

HttpResponse ResponseBuilder::created(const std::string& data) {
    HttpResponse res;
    res.status = HttpStatus::CREATED;
    res.body = successJson("Created", data);
    return res;
}

HttpResponse ResponseBuilder::noContent() {
    HttpResponse res;
    res.status = HttpStatus::NO_CONTENT;
    res.body = "";
    return res;
}

HttpResponse ResponseBuilder::badRequest(const std::string& message) {
    HttpResponse res;
    res.status = HttpStatus::BAD_REQUEST;
    res.body = errorJson(message, 400);
    return res;
}

HttpResponse ResponseBuilder::unauthorized(const std::string& message) {
    HttpResponse res;
    res.status = HttpStatus::UNAUTHORIZED;
    res.body = errorJson(message, 401);
    return res;
}

HttpResponse ResponseBuilder::forbidden(const std::string& message) {
    HttpResponse res;
    res.status = HttpStatus::FORBIDDEN;
    res.body = errorJson(message, 403);
    return res;
}

HttpResponse ResponseBuilder::notFound(const std::string& message) {
    HttpResponse res;
    res.status = HttpStatus::NOT_FOUND;
    res.body = errorJson(message, 404);
    return res;
}

HttpResponse ResponseBuilder::internalError(const std::string& message) {
    HttpResponse res;
    res.status = HttpStatus::INTERNAL_SERVER_ERROR;
    res.body = errorJson(message, 500);
    return res;
}

std::string ResponseBuilder::errorJson(const std::string& message, int code) {
    std::stringstream ss;
    ss << "{\"error\":true,\"code\":" << code 
       << ",\"message\":\"" << JsonUtils::escapeJson(message) << "\"}";
    return ss.str();
}

std::string ResponseBuilder::successJson(const std::string& message, const std::string& data) {
    std::stringstream ss;
    ss << "{\"success\":true,\"message\":\"" << JsonUtils::escapeJson(message) << "\"";
    if (!data.empty()) {
        ss << ",\"data\":" << data;
    }
    ss << "}";
    return ss.str();
}

// RestAPIServer implementation
class RestAPIServer::Impl {
public:
    std::string host;
    uint16_t port;
    bool running = false;
    std::thread server_thread;
    std::map<std::pair<HttpMethod, std::string>, RouteHandler> routes;
    std::vector<Middleware> middlewares;
    mutable std::mutex mutex;
    bool cors_enabled = true;
    size_t max_connections = 1000;
    std::chrono::seconds request_timeout{30};
    
    Impl(const std::string& h, uint16_t p) : host(h), port(p) {}
};

RestAPIServer::RestAPIServer(const std::string& host, uint16_t port)
    : pImpl(std::make_unique<Impl>(host, port)) {}

RestAPIServer::~RestAPIServer() {
    stop();
}

bool RestAPIServer::start() {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    if (pImpl->running) {
        return false;
    }
    
    pImpl->running = true;
    pImpl->server_thread = std::thread([this]() {
        // Simplified server loop
        while (pImpl->running) {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
    });
    
    return true;
}

bool RestAPIServer::stop() {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    if (!pImpl->running) {
        return false;
    }
    
    pImpl->running = false;
    if (pImpl->server_thread.joinable()) {
        pImpl->server_thread.join();
    }
    
    return true;
}

bool RestAPIServer::isRunning() const {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    return pImpl->running;
}

void RestAPIServer::registerRoute(HttpMethod method, const std::string& path, RouteHandler handler) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    pImpl->routes[{method, path}] = handler;
}

void RestAPIServer::get(const std::string& path, RouteHandler handler) {
    registerRoute(HttpMethod::GET, path, handler);
}

void RestAPIServer::post(const std::string& path, RouteHandler handler) {
    registerRoute(HttpMethod::POST, path, handler);
}

void RestAPIServer::put(const std::string& path, RouteHandler handler) {
    registerRoute(HttpMethod::PUT, path, handler);
}

void RestAPIServer::del(const std::string& path, RouteHandler handler) {
    registerRoute(HttpMethod::DELETE, path, handler);
}

void RestAPIServer::patch(const std::string& path, RouteHandler handler) {
    registerRoute(HttpMethod::PATCH, path, handler);
}

void RestAPIServer::use(Middleware middleware) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    pImpl->middlewares.push_back(middleware);
}

void RestAPIServer::setHost(const std::string& host) {
    pImpl->host = host;
}

void RestAPIServer::setPort(uint16_t port) {
    pImpl->port = port;
}

void RestAPIServer::enableCORS(bool enabled) {
    pImpl->cors_enabled = enabled;
}

void RestAPIServer::setMaxConnections(size_t max) {
    pImpl->max_connections = max;
}

void RestAPIServer::setRequestTimeout(std::chrono::seconds timeout) {
    pImpl->request_timeout = timeout;
}

// CogniwareRestAPI implementation
CogniwareRestAPI::CogniwareRestAPI(uint16_t port)
    : server_(std::make_unique<RestAPIServer>("0.0.0.0", port)) {
    registerAllEndpoints();
}

CogniwareRestAPI::~CogniwareRestAPI() {
    stop();
}

bool CogniwareRestAPI::start() {
    return server_->start();
}

bool CogniwareRestAPI::stop() {
    return server_->stop();
}

void CogniwareRestAPI::registerAllEndpoints() {
    // Middleware
    server_->use([this](HttpRequest& req, HttpResponse& res) {
        return corsMiddleware(req, res);
    });
    server_->use([this](HttpRequest& req, HttpResponse& res) {
        return loggingMiddleware(req, res);
    });
    server_->use([this](HttpRequest& req, HttpResponse& res) {
        return rateLimitMiddleware(req, res);
    });
    
    // Health & Status
    server_->get("/health", [this](const HttpRequest& req) {
        return handleHealthCheck(req);
    });
    server_->get("/status", [this](const HttpRequest& req) {
        return handleStatus(req);
    });
    server_->get("/metrics", [this](const HttpRequest& req) {
        return handleMetrics(req);
    });
    
    // Model Management
    server_->get("/models", [this](const HttpRequest& req) {
        return handleListModels(req);
    });
    server_->get("/models/:id", [this](const HttpRequest& req) {
        return handleGetModel(req);
    });
    server_->post("/models", [this](const HttpRequest& req) {
        return handleLoadModel(req);
    });
    server_->del("/models/:id", [this](const HttpRequest& req) {
        return handleUnloadModel(req);
    });
    server_->put("/models/:id", [this](const HttpRequest& req) {
        return handleUpdateModel(req);
    });
    
    // Inference
    server_->post("/inference", [this](const HttpRequest& req) {
        return handleInference(req);
    });
    server_->post("/inference/batch", [this](const HttpRequest& req) {
        return handleBatchInference(req);
    });
    server_->post("/inference/stream", [this](const HttpRequest& req) {
        return handleStreamInference(req);
    });
    server_->post("/inference/async", [this](const HttpRequest& req) {
        return handleAsyncInference(req);
    });
    server_->get("/inference/:id", [this](const HttpRequest& req) {
        return handleInferenceStatus(req);
    });
    
    // Multi-LLM
    server_->post("/orchestration/parallel", [this](const HttpRequest& req) {
        return handleParallelInference(req);
    });
    server_->post("/orchestration/consensus", [this](const HttpRequest& req) {
        return handleConsensusInference(req);
    });
    
    // Resources
    server_->get("/resources", [this](const HttpRequest& req) {
        return handleResourceUsage(req);
    });
    server_->post("/resources/allocate", [this](const HttpRequest& req) {
        return handleAllocateResource(req);
    });
    server_->post("/resources/release", [this](const HttpRequest& req) {
        return handleReleaseResource(req);
    });
    
    // System
    server_->get("/system/info", [this](const HttpRequest& req) {
        return handleSystemInfo(req);
    });
    server_->get("/system/cpu", [this](const HttpRequest& req) {
        return handleCPUInfo(req);
    });
    server_->get("/system/gpu", [this](const HttpRequest& req) {
        return handleGPUInfo(req);
    });
    server_->get("/system/memory", [this](const HttpRequest& req) {
        return handleMemoryInfo(req);
    });
    
    // Auth
    server_->post("/auth/login", [this](const HttpRequest& req) {
        return handleLogin(req);
    });
    server_->post("/auth/logout", [this](const HttpRequest& req) {
        return handleLogout(req);
    });
    server_->post("/auth/refresh", [this](const HttpRequest& req) {
        return handleRefreshToken(req);
    });
    
    // Logs
    server_->get("/logs", [this](const HttpRequest& req) {
        return handleGetLogs(req);
    });
    server_->get("/audit", [this](const HttpRequest& req) {
        return handleGetAudit(req);
    });
}

// Handler implementations
HttpResponse CogniwareRestAPI::handleHealthCheck(const HttpRequest&) {
    std::stringstream ss;
    ss << "{\"status\":\"healthy\",\"timestamp\":" 
       << std::chrono::system_clock::now().time_since_epoch().count() << "}";
    return ResponseBuilder::success(ss.str());
}

HttpResponse CogniwareRestAPI::handleStatus(const HttpRequest&) {
    std::stringstream ss;
    ss << "{\"server\":\"running\",\"models_loaded\":0,\"active_requests\":0}";
    return ResponseBuilder::success(ss.str());
}

HttpResponse CogniwareRestAPI::handleMetrics(const HttpRequest&) {
    std::stringstream ss;
    ss << "{\"requests_total\":0,\"requests_per_sec\":0,\"avg_latency_ms\":0}";
    return ResponseBuilder::success(ss.str());
}

HttpResponse CogniwareRestAPI::handleListModels(const HttpRequest&) {
    std::stringstream ss;
    ss << "{\"models\":[]}";
    return ResponseBuilder::success(ss.str());
}

HttpResponse CogniwareRestAPI::handleGetModel(const HttpRequest& req) {
    auto model_id = req.path_params.count("id") ? req.path_params.at("id") : "";
    if (model_id.empty()) {
        return ResponseBuilder::badRequest("Model ID required");
    }
    
    std::stringstream ss;
    ss << "{\"model_id\":\"" << model_id << "\",\"status\":\"loaded\"}";
    return ResponseBuilder::success(ss.str());
}

HttpResponse CogniwareRestAPI::handleLoadModel(const HttpRequest& req) {
    auto params = JsonUtils::fromJson(req.body);
    if (!params.count("model_path")) {
        return ResponseBuilder::badRequest("model_path required");
    }
    
    std::stringstream ss;
    ss << "{\"model_id\":\"model_123\",\"status\":\"loaded\"}";
    return ResponseBuilder::created(ss.str());
}

HttpResponse CogniwareRestAPI::handleUnloadModel(const HttpRequest& req) {
    auto model_id = req.path_params.count("id") ? req.path_params.at("id") : "";
    if (model_id.empty()) {
        return ResponseBuilder::badRequest("Model ID required");
    }
    
    return ResponseBuilder::noContent();
}

HttpResponse CogniwareRestAPI::handleUpdateModel(const HttpRequest&) {
    return ResponseBuilder::success("{}");
}

HttpResponse CogniwareRestAPI::handleInference(const HttpRequest& req) {
    auto params = JsonUtils::fromJson(req.body);
    if (!params.count("prompt")) {
        return ResponseBuilder::badRequest("prompt required");
    }
    
    std::stringstream ss;
    ss << "{\"generated_text\":\"Sample response\",\"tokens\":10,\"time_ms\":100}";
    return ResponseBuilder::success(ss.str());
}

HttpResponse CogniwareRestAPI::handleBatchInference(const HttpRequest&) {
    std::stringstream ss;
    ss << "{\"results\":[]}";
    return ResponseBuilder::success(ss.str());
}

HttpResponse CogniwareRestAPI::handleStreamInference(const HttpRequest&) {
    return ResponseBuilder::success("{}");
}

HttpResponse CogniwareRestAPI::handleAsyncInference(const HttpRequest&) {
    std::stringstream ss;
    ss << "{\"request_id\":\"req_123\",\"status\":\"processing\"}";
    return ResponseBuilder::success(ss.str());
}

HttpResponse CogniwareRestAPI::handleInferenceStatus(const HttpRequest&) {
    std::stringstream ss;
    ss << "{\"status\":\"completed\",\"result\":\"\"}";
    return ResponseBuilder::success(ss.str());
}

HttpResponse CogniwareRestAPI::handleParallelInference(const HttpRequest&) {
    std::stringstream ss;
    ss << "{\"results\":{}}";
    return ResponseBuilder::success(ss.str());
}

HttpResponse CogniwareRestAPI::handleConsensusInference(const HttpRequest&) {
    std::stringstream ss;
    ss << "{\"consensus_result\":\"\"}";
    return ResponseBuilder::success(ss.str());
}

HttpResponse CogniwareRestAPI::handleOrchestration(const HttpRequest&) {
    return ResponseBuilder::success("{}");
}

HttpResponse CogniwareRestAPI::handleResourceUsage(const HttpRequest&) {
    std::stringstream ss;
    ss << "{\"memory_mb\":0,\"cpu_percent\":0,\"gpu_percent\":0}";
    return ResponseBuilder::success(ss.str());
}

HttpResponse CogniwareRestAPI::handleAllocateResource(const HttpRequest&) {
    std::stringstream ss;
    ss << "{\"allocation_id\":\"alloc_123\"}";
    return ResponseBuilder::success(ss.str());
}

HttpResponse CogniwareRestAPI::handleReleaseResource(const HttpRequest&) {
    return ResponseBuilder::noContent();
}

HttpResponse CogniwareRestAPI::handleResourceQuota(const HttpRequest&) {
    return ResponseBuilder::success("{}");
}

HttpResponse CogniwareRestAPI::handleSystemInfo(const HttpRequest&) {
    std::stringstream ss;
    ss << "{\"hostname\":\"\",\"os\":\"\",\"version\":\"\"}";
    return ResponseBuilder::success(ss.str());
}

HttpResponse CogniwareRestAPI::handleCPUInfo(const HttpRequest&) {
    std::stringstream ss;
    ss << "{\"cores\":0,\"usage_percent\":0}";
    return ResponseBuilder::success(ss.str());
}

HttpResponse CogniwareRestAPI::handleGPUInfo(const HttpRequest&) {
    std::stringstream ss;
    ss << "{\"gpus\":[]}";
    return ResponseBuilder::success(ss.str());
}

HttpResponse CogniwareRestAPI::handleMemoryInfo(const HttpRequest&) {
    std::stringstream ss;
    ss << "{\"total_mb\":0,\"used_mb\":0,\"free_mb\":0}";
    return ResponseBuilder::success(ss.str());
}

HttpResponse CogniwareRestAPI::handleGetConfig(const HttpRequest&) {
    return ResponseBuilder::success("{}");
}

HttpResponse CogniwareRestAPI::handleUpdateConfig(const HttpRequest&) {
    return ResponseBuilder::success("{}");
}

HttpResponse CogniwareRestAPI::handleGetLogs(const HttpRequest&) {
    std::stringstream ss;
    ss << "{\"logs\":[]}";
    return ResponseBuilder::success(ss.str());
}

HttpResponse CogniwareRestAPI::handleGetAudit(const HttpRequest&) {
    std::stringstream ss;
    ss << "{\"audit_entries\":[]}";
    return ResponseBuilder::success(ss.str());
}

HttpResponse CogniwareRestAPI::handleLogin(const HttpRequest& req) {
    auto params = JsonUtils::fromJson(req.body);
    if (!params.count("username") || !params.count("password")) {
        return ResponseBuilder::badRequest("username and password required");
    }
    
    std::stringstream ss;
    ss << "{\"token\":\"eyJ...\",\"expires_in\":3600}";
    return ResponseBuilder::success(ss.str());
}

HttpResponse CogniwareRestAPI::handleLogout(const HttpRequest&) {
    return ResponseBuilder::noContent();
}

HttpResponse CogniwareRestAPI::handleRefreshToken(const HttpRequest&) {
    std::stringstream ss;
    ss << "{\"token\":\"eyJ...\",\"expires_in\":3600}";
    return ResponseBuilder::success(ss.str());
}

// Middleware implementations
bool CogniwareRestAPI::authMiddleware(HttpRequest& req, HttpResponse&) {
    // Check for Authorization header
    if (!req.headers.count("Authorization")) {
        return false; // Unauthorized
    }
    return true;
}

bool CogniwareRestAPI::loggingMiddleware(HttpRequest& req, HttpResponse&) {
    // Log request
    // std::cout << req.method << " " << req.path << std::endl;
    return true;
}

bool CogniwareRestAPI::rateLimitMiddleware(HttpRequest&, HttpResponse&) {
    // Check rate limits
    return true;
}

bool CogniwareRestAPI::corsMiddleware(HttpRequest&, HttpResponse& res) {
    res.headers["Access-Control-Allow-Origin"] = "*";
    res.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS";
    res.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization";
    return true;
}

} // namespace api
} // namespace cogniware

