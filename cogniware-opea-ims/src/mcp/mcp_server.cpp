#include "mcp/mcp_core.h"
#include <algorithm>
#include <sstream>
#include <random>
#include <mutex>
#include <iomanip>

namespace cogniware {
namespace mcp {

// Utility functions implementation
std::string generateMessageId() {
    static std::random_device rd;
    static std::mt19937 gen(rd());
    static std::uniform_int_distribution<> dis(0, 15);
    
    std::stringstream ss;
    ss << "msg_";
    for (int i = 0; i < 16; ++i) {
        ss << std::hex << dis(gen);
    }
    
    return ss.str();
}

bool validateMCPRequest(const MCPRequest& request) {
    if (request.id.empty()) return false;
    if (request.method.empty()) return false;
    return true;
}

bool validateMCPResponse(const MCPResponse& response) {
    if (response.id.empty()) return false;
    return true;
}

// AdvancedMCPServer Implementation
class AdvancedMCPServer::Impl {
public:
    bool running;
    MCPServerCapabilities capabilities;
    std::unordered_map<std::string, MCPTool> tools;
    std::unordered_map<std::string, MCPResource> resources;
    mutable std::mutex tools_mutex;
    mutable std::mutex resources_mutex;
    mutable std::mutex metrics_mutex;
    
    // Configuration
    std::chrono::milliseconds request_timeout{30000};
    size_t max_concurrent_requests{100};
    
    // Metrics
    size_t total_requests{0};
    size_t successful_requests{0};
    size_t failed_requests{0};
    std::vector<double> request_times;
    size_t active_connections{0};
    
    Impl() : running(false) {}
};

AdvancedMCPServer::AdvancedMCPServer()
    : pImpl(std::make_unique<Impl>()) {}

AdvancedMCPServer::~AdvancedMCPServer() {
    if (pImpl->running) {
        shutdown();
    }
}

bool AdvancedMCPServer::initialize(const MCPServerCapabilities& capabilities) {
    if (pImpl->running) {
        return false;
    }
    
    pImpl->capabilities = capabilities;
    pImpl->running = true;
    
    return true;
}

bool AdvancedMCPServer::shutdown() {
    if (!pImpl->running) {
        return false;
    }
    
    pImpl->running = false;
    
    std::lock_guard<std::mutex> tools_lock(pImpl->tools_mutex);
    std::lock_guard<std::mutex> resources_lock(pImpl->resources_mutex);
    
    pImpl->tools.clear();
    pImpl->resources.clear();
    
    return true;
}

bool AdvancedMCPServer::isRunning() const {
    return pImpl->running;
}

bool AdvancedMCPServer::registerTool(const MCPTool& tool) {
    if (!pImpl->running) {
        return false;
    }
    
    std::lock_guard<std::mutex> lock(pImpl->tools_mutex);
    
    if (pImpl->tools.find(tool.name) != pImpl->tools.end()) {
        return false;  // Tool already registered
    }
    
    pImpl->tools[tool.name] = tool;
    return true;
}

bool AdvancedMCPServer::unregisterTool(const std::string& tool_name) {
    if (!pImpl->running) {
        return false;
    }
    
    std::lock_guard<std::mutex> lock(pImpl->tools_mutex);
    return pImpl->tools.erase(tool_name) > 0;
}

std::vector<MCPTool> AdvancedMCPServer::listTools() const {
    std::lock_guard<std::mutex> lock(pImpl->tools_mutex);
    
    std::vector<MCPTool> tool_list;
    tool_list.reserve(pImpl->tools.size());
    
    for (const auto& [name, tool] : pImpl->tools) {
        tool_list.push_back(tool);
    }
    
    return tool_list;
}

MCPResponse AdvancedMCPServer::callTool(
    const std::string& tool_name,
    const std::unordered_map<std::string, std::string>& params) {
    
    auto start_time = std::chrono::high_resolution_clock::now();
    
    MCPResponse response;
    response.id = generateMessageId();
    response.type = MessageType::RESPONSE;
    response.timestamp = std::chrono::system_clock::now();
    response.success = false;
    
    if (!pImpl->running) {
        response.error_message = "Server not running";
        response.error_code = 500;
        return response;
    }
    
    std::lock_guard<std::mutex> lock(pImpl->tools_mutex);
    
    auto it = pImpl->tools.find(tool_name);
    if (it == pImpl->tools.end()) {
        response.error_message = "Tool not found: " + tool_name;
        response.error_code = 404;
        
        std::lock_guard<std::mutex> metrics_lock(pImpl->metrics_mutex);
        pImpl->total_requests++;
        pImpl->failed_requests++;
        
        return response;
    }
    
    const MCPTool& tool = it->second;
    
    // Validate parameters
    for (const auto& param : tool.parameters) {
        if (param.required && params.find(param.name) == params.end()) {
            response.error_message = "Missing required parameter: " + param.name;
            response.error_code = 400;
            
            std::lock_guard<std::mutex> metrics_lock(pImpl->metrics_mutex);
            pImpl->total_requests++;
            pImpl->failed_requests++;
            
            return response;
        }
    }
    
    // Execute tool
    try {
        if (tool.handler) {
            response.result = tool.handler(params);
            response.success = true;
            response.error_code = 0;
        } else {
            response.error_message = "Tool handler not implemented";
            response.error_code = 501;
        }
    } catch (const std::exception& e) {
        response.error_message = "Tool execution failed: " + std::string(e.what());
        response.error_code = 500;
    }
    
    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
    
    std::lock_guard<std::mutex> metrics_lock(pImpl->metrics_mutex);
    pImpl->total_requests++;
    if (response.success) {
        pImpl->successful_requests++;
    } else {
        pImpl->failed_requests++;
    }
    pImpl->request_times.push_back(duration.count());
    
    return response;
}

bool AdvancedMCPServer::registerResource(const MCPResource& resource) {
    if (!pImpl->running) {
        return false;
    }
    
    std::lock_guard<std::mutex> lock(pImpl->resources_mutex);
    
    if (pImpl->resources.find(resource.uri) != pImpl->resources.end()) {
        return false;  // Resource already registered
    }
    
    pImpl->resources[resource.uri] = resource;
    return true;
}

bool AdvancedMCPServer::unregisterResource(const std::string& uri) {
    if (!pImpl->running) {
        return false;
    }
    
    std::lock_guard<std::mutex> lock(pImpl->resources_mutex);
    return pImpl->resources.erase(uri) > 0;
}

std::vector<MCPResource> AdvancedMCPServer::listResources() const {
    std::lock_guard<std::mutex> lock(pImpl->resources_mutex);
    
    std::vector<MCPResource> resource_list;
    resource_list.reserve(pImpl->resources.size());
    
    for (const auto& [uri, resource] : pImpl->resources) {
        resource_list.push_back(resource);
    }
    
    return resource_list;
}

MCPResponse AdvancedMCPServer::readResource(const std::string& uri) {
    MCPResponse response;
    response.id = generateMessageId();
    response.type = MessageType::RESPONSE;
    response.timestamp = std::chrono::system_clock::now();
    response.success = false;
    
    if (!pImpl->running) {
        response.error_message = "Server not running";
        response.error_code = 500;
        return response;
    }
    
    std::lock_guard<std::mutex> lock(pImpl->resources_mutex);
    
    auto it = pImpl->resources.find(uri);
    if (it == pImpl->resources.end()) {
        response.error_message = "Resource not found: " + uri;
        response.error_code = 404;
        return response;
    }
    
    // Simulate resource read
    response.result = "Resource content for: " + uri;
    response.success = true;
    response.error_code = 0;
    
    return response;
}

MCPResponse AdvancedMCPServer::handleRequest(const MCPRequest& request) {
    if (!validateMCPRequest(request)) {
        MCPResponse response;
        response.id = request.id;
        response.type = MessageType::ERROR;
        response.success = false;
        response.error_message = "Invalid request";
        response.error_code = 400;
        return response;
    }
    
    switch (request.request_method) {
        case RequestMethod::TOOLS_LIST:
            {
                MCPResponse response;
                response.id = request.id;
                response.type = MessageType::RESPONSE;
                response.success = true;
                auto tools = listTools();
                response.result = std::to_string(tools.size()) + " tools available";
                return response;
            }
        
        case RequestMethod::TOOLS_CALL:
            return callTool(request.tool_name, request.parameters);
        
        case RequestMethod::RESOURCES_LIST:
            {
                MCPResponse response;
                response.id = request.id;
                response.type = MessageType::RESPONSE;
                response.success = true;
                auto resources = listResources();
                response.result = std::to_string(resources.size()) + " resources available";
                return response;
            }
        
        case RequestMethod::RESOURCES_READ:
            if (!request.resource_uris.empty()) {
                return readResource(request.resource_uris[0]);
            }
            break;
        
        case RequestMethod::PING:
            {
                MCPResponse response;
                response.id = request.id;
                response.type = MessageType::RESPONSE;
                response.success = true;
                response.result = "pong";
                return response;
            }
        
        default:
            break;
    }
    
    MCPResponse response;
    response.id = request.id;
    response.type = MessageType::ERROR;
    response.success = false;
    response.error_message = "Unsupported request method";
    response.error_code = 501;
    return response;
}

void AdvancedMCPServer::sendNotification(
    const std::string& method,
    const std::unordered_map<std::string, std::string>& params) {
    
    // Notification implementation (would send to connected clients)
    // For now, this is a placeholder
}

MCPServerCapabilities AdvancedMCPServer::getCapabilities() const {
    return pImpl->capabilities;
}

void AdvancedMCPServer::setRequestTimeout(std::chrono::milliseconds timeout) {
    pImpl->request_timeout = timeout;
}

void AdvancedMCPServer::setMaxConcurrentRequests(size_t max_requests) {
    pImpl->max_concurrent_requests = max_requests;
}

AdvancedMCPServer::ServerMetrics AdvancedMCPServer::getMetrics() const {
    std::lock_guard<std::mutex> metrics_lock(pImpl->metrics_mutex);
    std::lock_guard<std::mutex> tools_lock(pImpl->tools_mutex);
    std::lock_guard<std::mutex> resources_lock(pImpl->resources_mutex);
    
    ServerMetrics metrics;
    metrics.total_requests = pImpl->total_requests;
    metrics.successful_requests = pImpl->successful_requests;
    metrics.failed_requests = pImpl->failed_requests;
    metrics.tools_registered = pImpl->tools.size();
    metrics.resources_registered = pImpl->resources.size();
    metrics.active_connections = pImpl->active_connections;
    
    if (!pImpl->request_times.empty()) {
        metrics.avg_request_time_ms = std::accumulate(
            pImpl->request_times.begin(),
            pImpl->request_times.end(),
            0.0) / pImpl->request_times.size();
    } else {
        metrics.avg_request_time_ms = 0.0;
    }
    
    return metrics;
}

void AdvancedMCPServer::resetMetrics() {
    std::lock_guard<std::mutex> lock(pImpl->metrics_mutex);
    pImpl->total_requests = 0;
    pImpl->successful_requests = 0;
    pImpl->failed_requests = 0;
    pImpl->request_times.clear();
}

} // namespace mcp
} // namespace cogniware

