/**
 * @file cognidream_admin_api.cpp
 * @brief Implementation of CogniDream admin REST API
 */

#include "cognidream_admin_api.hpp"
#include "cognidream_admin.hpp"
#include <fstream>
#include <spdlog/spdlog.h>

namespace cognidream {

CogniDreamAdminAPI& CogniDreamAdminAPI::getInstance() {
    static CogniDreamAdminAPI instance;
    return instance;
}

bool CogniDreamAdminAPI::initialize(const std::string& config_path) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!loadConfig(config_path)) {
        spdlog::error("Failed to load CogniDream admin API configuration");
        return false;
    }

    app_ = std::make_unique<crow::SimpleApp>();
    setupRoutes();
    
    spdlog::info("CogniDream admin API initialized");
    return true;
}

void CogniDreamAdminAPI::shutdown() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (running_) {
        stop();
    }
    
    if (!saveConfig()) {
        spdlog::error("Failed to save CogniDream admin API configuration");
    }
    
    app_.reset();
    spdlog::info("CogniDream admin API shut down");
}

bool CogniDreamAdminAPI::start(int port) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!app_) {
        spdlog::error("CogniDream admin API not initialized");
        return false;
    }
    
    try {
        app_->port(port).multithreaded().run();
        running_ = true;
        spdlog::info("CogniDream admin API server started on port {}", port);
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Failed to start CogniDream admin API server: {}", e.what());
        return false;
    }
}

void CogniDreamAdminAPI::stop() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (app_) {
        app_->stop();
        running_ = false;
        spdlog::info("CogniDream admin API server stopped");
    }
}

bool CogniDreamAdminAPI::loadConfig(const std::string& config_path) {
    try {
        std::ifstream file(config_path);
        if (!file.is_open()) {
            spdlog::error("Failed to open CogniDream admin API configuration file: {}", config_path);
            return false;
        }
        
        file >> config_;
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Failed to load CogniDream admin API configuration: {}", e.what());
        return false;
    }
}

bool CogniDreamAdminAPI::saveConfig() {
    try {
        std::ofstream file(config_["config_path"].get<std::string>());
        if (!file.is_open()) {
            spdlog::error("Failed to open CogniDream admin API configuration file for writing");
            return false;
        }
        
        file << config_.dump(4);
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Failed to save CogniDream admin API configuration: {}", e.what());
        return false;
    }
}

void CogniDreamAdminAPI::setupRoutes() {
    // Session management
    CROW_ROUTE((*app_), "/api/v1/sessions")
        .methods(crow::HTTPMethod::POST)
        ([this](const crow::request& req) { return handleCreateSession(req); });
    
    CROW_ROUTE((*app_), "/api/v1/sessions/<string>")
        .methods(crow::HTTPMethod::DELETE)
        ([this](const crow::request& req, const std::string& session_id) {
            return handleEndSession(req);
        });
    
    CROW_ROUTE((*app_), "/api/v1/sessions/<string>")
        .methods(crow::HTTPMethod::GET)
        ([this](const crow::request& req, const std::string& session_id) {
            return handleGetSessionInfo(req);
        });
    
    CROW_ROUTE((*app_), "/api/v1/sessions")
        .methods(crow::HTTPMethod::GET)
        ([this](const crow::request& req) { return handleGetActiveSessions(req); });
    
    // System metrics
    CROW_ROUTE((*app_), "/api/v1/metrics")
        .methods(crow::HTTPMethod::GET)
        ([this](const crow::request& req) { return handleGetSystemMetrics(req); });
    
    // Model management
    CROW_ROUTE((*app_), "/api/v1/models/<string>/stats")
        .methods(crow::HTTPMethod::GET)
        ([this](const crow::request& req, const std::string& model_id) {
            return handleGetModelStats(req);
        });
    
    CROW_ROUTE((*app_), "/api/v1/models/<string>/config")
        .methods(crow::HTTPMethod::PUT)
        ([this](const crow::request& req, const std::string& model_id) {
            return handleUpdateModelConfig(req);
        });
    
    // User statistics
    CROW_ROUTE((*app_), "/api/v1/users/<string>/stats")
        .methods(crow::HTTPMethod::GET)
        ([this](const crow::request& req, const std::string& user_id) {
            return handleGetUserStats(req);
        });
}

crow::response CogniDreamAdminAPI::handleCreateSession(const crow::request& req) {
    try {
        auto body = nlohmann::json::parse(req.body);
        std::string user_id = body["user_id"];
        std::string model_id = body["model_id"];
        
        auto session = CogniDreamAdmin::getInstance().createSession(user_id, model_id);
        if (!session) {
            return crow::response(500, "Failed to create session");
        }
        
        nlohmann::json response = {
            {"session_id", session->session_id},
            {"user_id", session->user_id},
            {"model_id", session->model_id},
            {"created_at", session->created_at},
            {"last_activity", session->last_activity}
        };
        
        return crow::response(200, response.dump());
    } catch (const std::exception& e) {
        spdlog::error("Error creating session: {}", e.what());
        return crow::response(500, "Internal server error");
    }
}

crow::response CogniDreamAdminAPI::handleEndSession(const crow::request& req) {
    try {
        std::string session_id = req.url_params.get("session_id");
        
        if (CogniDreamAdmin::getInstance().endSession(session_id)) {
            return crow::response(200);
        }
        
        return crow::response(404, "Session not found");
    } catch (const std::exception& e) {
        spdlog::error("Error ending session: {}", e.what());
        return crow::response(500, "Internal server error");
    }
}

crow::response CogniDreamAdminAPI::handleGetSessionInfo(const crow::request& req) {
    try {
        std::string session_id = req.url_params.get("session_id");
        
        auto session = CogniDreamAdmin::getInstance().getSessionInfo(session_id);
        if (!session) {
            return crow::response(404, "Session not found");
        }
        
        nlohmann::json response = {
            {"session_id", session->session_id},
            {"user_id", session->user_id},
            {"model_id", session->model_id},
            {"created_at", session->created_at},
            {"last_activity", session->last_activity},
            {"requests_processed", session->requests_processed},
            {"tokens_generated", session->tokens_generated}
        };
        
        return crow::response(200, response.dump());
    } catch (const std::exception& e) {
        spdlog::error("Error getting session info: {}", e.what());
        return crow::response(500, "Internal server error");
    }
}

crow::response CogniDreamAdminAPI::handleGetActiveSessions(const crow::request& req) {
    try {
        auto sessions = CogniDreamAdmin::getInstance().getActiveSessions();
        
        nlohmann::json response = nlohmann::json::array();
        for (const auto& session : sessions) {
            response.push_back({
                {"session_id", session.session_id},
                {"user_id", session.user_id},
                {"model_id", session.model_id},
                {"created_at", session.created_at},
                {"last_activity", session.last_activity},
                {"requests_processed", session.requests_processed},
                {"tokens_generated", session.tokens_generated}
            });
        }
        
        return crow::response(200, response.dump());
    } catch (const std::exception& e) {
        spdlog::error("Error getting active sessions: {}", e.what());
        return crow::response(500, "Internal server error");
    }
}

crow::response CogniDreamAdminAPI::handleGetSystemMetrics(const crow::request& req) {
    try {
        auto metrics = CogniDreamAdmin::getInstance().getSystemMetrics();
        
        nlohmann::json response = {
            {"total_requests", metrics.total_requests},
            {"total_tokens", metrics.total_tokens},
            {"active_sessions", metrics.active_sessions},
            {"vram_usage", metrics.vram_usage},
            {"avg_latency", metrics.avg_latency},
            {"gpu_utilization", metrics.gpu_utilization},
            {"memory_utilization", metrics.memory_utilization}
        };
        
        return crow::response(200, response.dump());
    } catch (const std::exception& e) {
        spdlog::error("Error getting system metrics: {}", e.what());
        return crow::response(500, "Internal server error");
    }
}

crow::response CogniDreamAdminAPI::handleGetModelStats(const crow::request& req) {
    try {
        std::string model_id = req.url_params.get("model_id");
        
        auto stats = CogniDreamAdmin::getInstance().getModelStats(model_id);
        if (!stats) {
            return crow::response(404, "Model not found");
        }
        
        nlohmann::json response = {
            {"model_id", stats->model_id},
            {"requests_processed", stats->requests_processed},
            {"tokens_generated", stats->tokens_generated},
            {"avg_latency", stats->avg_latency},
            {"vram_usage", stats->vram_usage},
            {"gpu_utilization", stats->gpu_utilization},
            {"memory_utilization", stats->memory_utilization}
        };
        
        return crow::response(200, response.dump());
    } catch (const std::exception& e) {
        spdlog::error("Error getting model stats: {}", e.what());
        return crow::response(500, "Internal server error");
    }
}

crow::response CogniDreamAdminAPI::handleUpdateModelConfig(const crow::request& req) {
    try {
        std::string model_id = req.url_params.get("model_id");
        auto config = nlohmann::json::parse(req.body);
        
        if (CogniDreamAdmin::getInstance().updateModelConfig(model_id, config)) {
            return crow::response(200);
        }
        
        return crow::response(404, "Model not found");
    } catch (const std::exception& e) {
        spdlog::error("Error updating model config: {}", e.what());
        return crow::response(500, "Internal server error");
    }
}

crow::response CogniDreamAdminAPI::handleGetUserStats(const crow::request& req) {
    try {
        std::string user_id = req.url_params.get("user_id");
        
        auto stats = CogniDreamAdmin::getInstance().getUserStats(user_id);
        if (!stats) {
            return crow::response(404, "User not found");
        }
        
        nlohmann::json response = {
            {"user_id", stats->user_id},
            {"total_requests", stats->total_requests},
            {"total_tokens", stats->total_tokens},
            {"active_sessions", stats->active_sessions},
            {"avg_latency", stats->avg_latency}
        };
        
        return crow::response(200, response.dump());
    } catch (const std::exception& e) {
        spdlog::error("Error getting user stats: {}", e.what());
        return crow::response(500, "Internal server error");
    }
}

nlohmann::json CogniDreamAdminAPI::handleRequest(const std::string& endpoint, const nlohmann::json& request) {
    try {
        if (endpoint_handlers_.empty()) {
            initializeEndpointHandlers();
        }

        auto it = endpoint_handlers_.find(endpoint);
        if (it == endpoint_handlers_.end()) {
            return createErrorResponse("Invalid endpoint: " + endpoint, 404);
        }

        return it->second(request);
    } catch (const std::exception& e) {
        spdlog::error("Error handling request: {}", e.what());
        return createErrorResponse(e.what());
    }
}

nlohmann::json CogniDreamAdminAPI::initialize(const nlohmann::json& request) {
    if (!validateRequest(request, {"config_path"})) {
        return createErrorResponse("Missing required fields");
    }

    bool success = CogniDreamAdmin::getInstance().initialize(request["config_path"]);
    if (!success) {
        return createErrorResponse("Failed to initialize system");
    }

    return createSuccessResponse();
}

nlohmann::json CogniDreamAdminAPI::shutdown(const nlohmann::json& request) {
    bool success = CogniDreamAdmin::getInstance().shutdown();
    if (!success) {
        return createErrorResponse("Failed to shutdown system");
    }

    return createSuccessResponse();
}

nlohmann::json CogniDreamAdminAPI::getStatus(const nlohmann::json& request) {
    bool initialized = CogniDreamAdmin::getInstance().isInitialized();
    return createSuccessResponse({
        {"initialized", initialized}
    });
}

nlohmann::json CogniDreamAdminAPI::loadModel(const nlohmann::json& request) {
    if (!validateRequest(request, {"model_id", "model_path"})) {
        return createErrorResponse("Missing required fields");
    }

    bool success = CogniDreamAdmin::getInstance().loadModel(
        request["model_id"],
        request["model_path"]
    );

    if (!success) {
        return createErrorResponse("Failed to load model");
    }

    return createSuccessResponse();
}

nlohmann::json CogniDreamAdminAPI::unloadModel(const nlohmann::json& request) {
    if (!validateRequest(request, {"model_id"})) {
        return createErrorResponse("Missing required fields");
    }

    bool success = CogniDreamAdmin::getInstance().unloadModel(request["model_id"]);
    if (!success) {
        return createErrorResponse("Failed to unload model");
    }

    return createSuccessResponse();
}

nlohmann::json CogniDreamAdminAPI::listModels(const nlohmann::json& request) {
    auto models = CogniDreamAdmin::getInstance().getLoadedModels();
    return createSuccessResponse({
        {"models", models}
    });
}

nlohmann::json CogniDreamAdminAPI::setResourceLimits(const nlohmann::json& request) {
    if (!validateRequest(request, {"resource_type", "limits"})) {
        return createErrorResponse("Missing required fields");
    }

    bool success = CogniDreamAdmin::getInstance().setResourceLimits(
        request["resource_type"],
        request["limits"]
    );

    if (!success) {
        return createErrorResponse("Failed to set resource limits");
    }

    return createSuccessResponse();
}

nlohmann::json CogniDreamAdminAPI::getResourceUsage(const nlohmann::json& request) {
    auto usage = CogniDreamAdmin::getInstance().getResourceUsage();
    return createSuccessResponse({
        {"usage", usage}
    });
}

nlohmann::json CogniDreamAdminAPI::adjustResources(const nlohmann::json& request) {
    if (!validateRequest(request, {"resource_type", "allocation"})) {
        return createErrorResponse("Missing required fields");
    }

    bool success = CogniDreamAdmin::getInstance().adjustResourceAllocation(
        request["resource_type"],
        request["allocation"]
    );

    if (!success) {
        return createErrorResponse("Failed to adjust resource allocation");
    }

    return createSuccessResponse();
}

nlohmann::json CogniDreamAdminAPI::getSystemMetrics(const nlohmann::json& request) {
    auto metrics = CogniDreamAdmin::getInstance().getSystemMetrics();
    return createSuccessResponse({
        {"metrics", metrics}
    });
}

nlohmann::json CogniDreamAdminAPI::getModelMetrics(const nlohmann::json& request) {
    if (!validateRequest(request, {"model_id"})) {
        return createErrorResponse("Missing required fields");
    }

    auto metrics = CogniDreamAdmin::getInstance().getModelMetrics(request["model_id"]);
    return createSuccessResponse({
        {"metrics", metrics}
    });
}

nlohmann::json CogniDreamAdminAPI::setMonitoringConfig(const nlohmann::json& request) {
    if (!validateRequest(request, {"config"})) {
        return createErrorResponse("Missing required fields");
    }

    bool success = CogniDreamAdmin::getInstance().setMonitoringConfig(request["config"]);
    if (!success) {
        return createErrorResponse("Failed to set monitoring configuration");
    }

    return createSuccessResponse();
}

nlohmann::json CogniDreamAdminAPI::updateSecurityConfig(const nlohmann::json& request) {
    if (!validateRequest(request, {"config"})) {
        return createErrorResponse("Missing required fields");
    }

    bool success = CogniDreamAdmin::getInstance().updateSecurityConfig(request["config"]);
    if (!success) {
        return createErrorResponse("Failed to update security configuration");
    }

    return createSuccessResponse();
}

nlohmann::json CogniDreamAdminAPI::validateToken(const nlohmann::json& request) {
    if (!validateRequest(request, {"token"})) {
        return createErrorResponse("Missing required fields");
    }

    bool valid = CogniDreamAdmin::getInstance().validateAccessToken(request["token"]);
    return createSuccessResponse({
        {"valid", valid}
    });
}

nlohmann::json CogniDreamAdminAPI::generateToken(const nlohmann::json& request) {
    if (!validateRequest(request, {"user_id", "permissions"})) {
        return createErrorResponse("Missing required fields");
    }

    try {
        std::string token = CogniDreamAdmin::getInstance().generateAccessToken(
            request["user_id"],
            request["permissions"].get<std::vector<std::string>>()
        );
        return createSuccessResponse({
            {"token", token}
        });
    } catch (const std::exception& e) {
        return createErrorResponse("Failed to generate token: " + std::string(e.what()));
    }
}

nlohmann::json CogniDreamAdminAPI::createSuccessResponse(const nlohmann::json& data) {
    nlohmann::json response = {
        {"success", true},
        {"error", nullptr}
    };
    
    if (data != nullptr) {
        response["data"] = data;
    }
    
    return response;
}

nlohmann::json CogniDreamAdminAPI::createErrorResponse(const std::string& error, int code) {
    return {
        {"success", false},
        {"error", {
            {"message", error},
            {"code", code}
        }},
        {"data", nullptr}
    };
}

bool CogniDreamAdminAPI::validateRequest(const nlohmann::json& request, const std::vector<std::string>& required_fields) {
    for (const auto& field : required_fields) {
        if (!request.contains(field)) {
            return false;
        }
    }
    return true;
}

void CogniDreamAdminAPI::initializeEndpointHandlers() {
    endpoint_handlers_ = {
        {"initialize", [this](const nlohmann::json& req) { return initialize(req); }},
        {"shutdown", [this](const nlohmann::json& req) { return shutdown(req); }},
        {"getStatus", [this](const nlohmann::json& req) { return getStatus(req); }},
        {"loadModel", [this](const nlohmann::json& req) { return loadModel(req); }},
        {"unloadModel", [this](const nlohmann::json& req) { return unloadModel(req); }},
        {"listModels", [this](const nlohmann::json& req) { return listModels(req); }},
        {"setResourceLimits", [this](const nlohmann::json& req) { return setResourceLimits(req); }},
        {"getResourceUsage", [this](const nlohmann::json& req) { return getResourceUsage(req); }},
        {"adjustResources", [this](const nlohmann::json& req) { return adjustResources(req); }},
        {"getSystemMetrics", [this](const nlohmann::json& req) { return getSystemMetrics(req); }},
        {"getModelMetrics", [this](const nlohmann::json& req) { return getModelMetrics(req); }},
        {"setMonitoringConfig", [this](const nlohmann::json& req) { return setMonitoringConfig(req); }},
        {"updateSecurityConfig", [this](const nlohmann::json& req) { return updateSecurityConfig(req); }},
        {"validateToken", [this](const nlohmann::json& req) { return validateToken(req); }},
        {"generateToken", [this](const nlohmann::json& req) { return generateToken(req); }}
    };
}

} // namespace cognidream 