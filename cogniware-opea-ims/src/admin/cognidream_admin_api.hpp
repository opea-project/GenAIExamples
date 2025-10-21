#pragma once

#include <string>
#include <vector>
#include <memory>
#include <functional>
#include <nlohmann/json.hpp>

namespace cognidream {

class CogniDreamAdminAPI {
public:
    static CogniDreamAdminAPI& getInstance();

    // Delete copy constructor and assignment operator
    CogniDreamAdminAPI(const CogniDreamAdminAPI&) = delete;
    CogniDreamAdminAPI& operator=(const CogniDreamAdminAPI&) = delete;

    // API endpoints
    nlohmann::json handleRequest(const std::string& endpoint, const nlohmann::json& request);

    // System management endpoints
    nlohmann::json initialize(const nlohmann::json& request);
    nlohmann::json shutdown(const nlohmann::json& request);
    nlohmann::json getStatus(const nlohmann::json& request);

    // Model management endpoints
    nlohmann::json loadModel(const nlohmann::json& request);
    nlohmann::json unloadModel(const nlohmann::json& request);
    nlohmann::json listModels(const nlohmann::json& request);

    // Resource management endpoints
    nlohmann::json setResourceLimits(const nlohmann::json& request);
    nlohmann::json getResourceUsage(const nlohmann::json& request);
    nlohmann::json adjustResources(const nlohmann::json& request);

    // Monitoring endpoints
    nlohmann::json getSystemMetrics(const nlohmann::json& request);
    nlohmann::json getModelMetrics(const nlohmann::json& request);
    nlohmann::json setMonitoringConfig(const nlohmann::json& request);

    // Security endpoints
    nlohmann::json updateSecurityConfig(const nlohmann::json& request);
    nlohmann::json validateToken(const nlohmann::json& request);
    nlohmann::json generateToken(const nlohmann::json& request);

private:
    CogniDreamAdminAPI() = default;
    ~CogniDreamAdminAPI() = default;

    // Response helpers
    nlohmann::json createSuccessResponse(const nlohmann::json& data = nullptr);
    nlohmann::json createErrorResponse(const std::string& error, int code = 400);

    // Request validation
    bool validateRequest(const nlohmann::json& request, const std::vector<std::string>& required_fields);
    bool validateToken(const std::string& token);

    // Endpoint handlers
    using EndpointHandler = std::function<nlohmann::json(const nlohmann::json&)>;
    std::unordered_map<std::string, EndpointHandler> endpoint_handlers_;
    void initializeEndpointHandlers();
};

} // namespace cognidream 