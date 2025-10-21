#include "mcp/mcp_core.h"
#include <algorithm>
#include <mutex>

namespace cogniware {
namespace mcp {

// AdvancedMCPClient Implementation
class AdvancedMCPClient::Impl {
public:
    bool connected;
    std::string server_uri;
    MCPClientCapabilities client_capabilities;
    MCPServerCapabilities server_capabilities;
    
    mutable std::mutex connection_mutex;
    mutable std::mutex cache_mutex;
    mutable std::mutex metrics_mutex;
    
    // Configuration
    std::chrono::milliseconds connection_timeout{10000};
    int retry_attempts{3};
    bool caching_enabled{true};
    
    // Cache
    std::unordered_map<std::string, MCPResponse> response_cache;
    std::unordered_map<std::string, std::vector<MCPTool>> tools_cache;
    std::unordered_map<std::string, std::vector<MCPResource>> resources_cache;
    
    // Metrics
    size_t total_requests{0};
    size_t successful_requests{0};
    size_t failed_requests{0};
    size_t cache_hits{0};
    size_t cache_misses{0};
    std::vector<double> request_times;
    std::vector<size_t> response_sizes;
    
    Impl() : connected(false) {}
};

AdvancedMCPClient::AdvancedMCPClient()
    : pImpl(std::make_unique<Impl>()) {}

AdvancedMCPClient::~AdvancedMCPClient() {
    if (pImpl->connected) {
        disconnect();
    }
}

bool AdvancedMCPClient::connect(const std::string& server_uri) {
    std::lock_guard<std::mutex> lock(pImpl->connection_mutex);
    
    if (pImpl->connected) {
        return false;
    }
    
    pImpl->server_uri = server_uri;
    pImpl->connected = true;  // Simulate connection
    
    return true;
}

bool AdvancedMCPClient::disconnect() {
    std::lock_guard<std::mutex> lock(pImpl->connection_mutex);
    
    if (!pImpl->connected) {
        return false;
    }
    
    pImpl->connected = false;
    pImpl->server_uri.clear();
    
    return true;
}

bool AdvancedMCPClient::isConnected() const {
    std::lock_guard<std::mutex> lock(pImpl->connection_mutex);
    return pImpl->connected;
}

MCPResponse AdvancedMCPClient::initialize(const MCPClientCapabilities& capabilities) {
    MCPResponse response;
    response.id = generateMessageId();
    response.type = MessageType::RESPONSE;
    response.timestamp = std::chrono::system_clock::now();
    response.success = false;
    
    if (!pImpl->connected) {
        response.error_message = "Not connected to server";
        response.error_code = 503;
        return response;
    }
    
    pImpl->client_capabilities = capabilities;
    
    // Simulate initialization exchange
    pImpl->server_capabilities.supports_tools = true;
    pImpl->server_capabilities.supports_resources = true;
    pImpl->server_capabilities.supports_prompts = true;
    pImpl->server_capabilities.supports_completion = false;
    pImpl->server_capabilities.supports_logging = true;
    pImpl->server_capabilities.server_name = "Cogniware MCP Server";
    pImpl->server_capabilities.server_version = MCP_VERSION;
    
    response.success = true;
    response.result = "Initialization successful";
    response.error_code = 0;
    
    return response;
}

std::vector<MCPTool> AdvancedMCPClient::listTools() {
    auto start_time = std::chrono::high_resolution_clock::now();
    
    if (!pImpl->connected) {
        return {};
    }
    
    // Check cache
    if (pImpl->caching_enabled) {
        std::lock_guard<std::mutex> cache_lock(pImpl->cache_mutex);
        auto it = pImpl->tools_cache.find(pImpl->server_uri);
        if (it != pImpl->tools_cache.end()) {
            std::lock_guard<std::mutex> metrics_lock(pImpl->metrics_mutex);
            pImpl->cache_hits++;
            return it->second;
        }
        pImpl->cache_misses++;
    }
    
    // Create request
    MCPRequest request;
    request.id = generateMessageId();
    request.type = MessageType::REQUEST;
    request.request_method = RequestMethod::TOOLS_LIST;
    request.method = "tools/list";
    request.timestamp = std::chrono::system_clock::now();
    
    // Send request (simulated)
    std::vector<MCPTool> tools;  // Would be populated from actual response
    
    // Cache result
    if (pImpl->caching_enabled) {
        std::lock_guard<std::mutex> cache_lock(pImpl->cache_mutex);
        pImpl->tools_cache[pImpl->server_uri] = tools;
    }
    
    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
    
    std::lock_guard<std::mutex> metrics_lock(pImpl->metrics_mutex);
    pImpl->total_requests++;
    pImpl->successful_requests++;
    pImpl->request_times.push_back(duration.count());
    
    return tools;
}

MCPResponse AdvancedMCPClient::callTool(
    const std::string& tool_name,
    const std::unordered_map<std::string, std::string>& params) {
    
    auto start_time = std::chrono::high_resolution_clock::now();
    
    MCPResponse response;
    response.id = generateMessageId();
    response.type = MessageType::RESPONSE;
    response.timestamp = std::chrono::system_clock::now();
    response.success = false;
    
    if (!pImpl->connected) {
        response.error_message = "Not connected to server";
        response.error_code = 503;
        return response;
    }
    
    // Create request
    MCPRequest request;
    request.id = generateMessageId();
    request.type = MessageType::REQUEST;
    request.request_method = RequestMethod::TOOLS_CALL;
    request.method = "tools/call";
    request.tool_name = tool_name;
    request.parameters = params;
    request.timestamp = std::chrono::system_clock::now();
    
    // Send request (simulated)
    response = sendRequest(request);
    
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
    pImpl->response_sizes.push_back(response.result.size());
    
    return response;
}

std::vector<MCPResource> AdvancedMCPClient::listResources() {
    if (!pImpl->connected) {
        return {};
    }
    
    // Check cache
    if (pImpl->caching_enabled) {
        std::lock_guard<std::mutex> cache_lock(pImpl->cache_mutex);
        auto it = pImpl->resources_cache.find(pImpl->server_uri);
        if (it != pImpl->resources_cache.end()) {
            std::lock_guard<std::mutex> metrics_lock(pImpl->metrics_mutex);
            pImpl->cache_hits++;
            return it->second;
        }
        pImpl->cache_misses++;
    }
    
    // Create request
    MCPRequest request;
    request.id = generateMessageId();
    request.type = MessageType::REQUEST;
    request.request_method = RequestMethod::RESOURCES_LIST;
    request.method = "resources/list";
    request.timestamp = std::chrono::system_clock::now();
    
    // Send request (simulated)
    std::vector<MCPResource> resources;  // Would be populated from actual response
    
    // Cache result
    if (pImpl->caching_enabled) {
        std::lock_guard<std::mutex> cache_lock(pImpl->cache_mutex);
        pImpl->resources_cache[pImpl->server_uri] = resources;
    }
    
    return resources;
}

MCPResponse AdvancedMCPClient::readResource(const std::string& uri) {
    MCPResponse response;
    response.id = generateMessageId();
    response.type = MessageType::RESPONSE;
    response.timestamp = std::chrono::system_clock::now();
    response.success = false;
    
    if (!pImpl->connected) {
        response.error_message = "Not connected to server";
        response.error_code = 503;
        return response;
    }
    
    // Create request
    MCPRequest request;
    request.id = generateMessageId();
    request.type = MessageType::REQUEST;
    request.request_method = RequestMethod::RESOURCES_READ;
    request.method = "resources/read";
    request.resource_uris.push_back(uri);
    request.timestamp = std::chrono::system_clock::now();
    
    // Send request
    response = sendRequest(request);
    
    return response;
}

bool AdvancedMCPClient::subscribeToResource(const std::string& uri) {
    if (!pImpl->connected) {
        return false;
    }
    
    // Create subscription request
    MCPRequest request;
    request.id = generateMessageId();
    request.type = MessageType::REQUEST;
    request.request_method = RequestMethod::RESOURCES_SUBSCRIBE;
    request.method = "resources/subscribe";
    request.resource_uris.push_back(uri);
    request.timestamp = std::chrono::system_clock::now();
    
    auto response = sendRequest(request);
    return response.success;
}

MCPResponse AdvancedMCPClient::sendRequest(const MCPRequest& request) {
    MCPResponse response;
    response.id = request.id;
    response.type = MessageType::RESPONSE;
    response.timestamp = std::chrono::system_clock::now();
    
    if (!pImpl->connected) {
        response.success = false;
        response.error_message = "Not connected to server";
        response.error_code = 503;
        return response;
    }
    
    if (!validateMCPRequest(request)) {
        response.success = false;
        response.error_message = "Invalid request";
        response.error_code = 400;
        return response;
    }
    
    // Simulate request/response (would actually communicate with server)
    response.success = true;
    response.result = "Request processed successfully";
    response.error_code = 0;
    
    return response;
}

MCPServerCapabilities AdvancedMCPClient::getServerCapabilities() const {
    return pImpl->server_capabilities;
}

void AdvancedMCPClient::setConnectionTimeout(std::chrono::milliseconds timeout) {
    pImpl->connection_timeout = timeout;
}

void AdvancedMCPClient::setRetryAttempts(int attempts) {
    pImpl->retry_attempts = attempts;
}

void AdvancedMCPClient::enableCaching(bool enable) {
    pImpl->caching_enabled = enable;
    if (!enable) {
        std::lock_guard<std::mutex> lock(pImpl->cache_mutex);
        pImpl->response_cache.clear();
        pImpl->tools_cache.clear();
        pImpl->resources_cache.clear();
    }
}

AdvancedMCPClient::ClientMetrics AdvancedMCPClient::getMetrics() const {
    std::lock_guard<std::mutex> lock(pImpl->metrics_mutex);
    
    ClientMetrics metrics;
    metrics.total_requests = pImpl->total_requests;
    metrics.successful_requests = pImpl->successful_requests;
    metrics.failed_requests = pImpl->failed_requests;
    metrics.cache_hits = pImpl->cache_hits;
    metrics.cache_misses = pImpl->cache_misses;
    
    if (!pImpl->request_times.empty()) {
        metrics.avg_request_time_ms = std::accumulate(
            pImpl->request_times.begin(),
            pImpl->request_times.end(),
            0.0) / pImpl->request_times.size();
    } else {
        metrics.avg_request_time_ms = 0.0;
    }
    
    if (!pImpl->response_sizes.empty()) {
        metrics.avg_response_size_bytes = std::accumulate(
            pImpl->response_sizes.begin(),
            pImpl->response_sizes.end(),
            0.0) / pImpl->response_sizes.size();
    } else {
        metrics.avg_response_size_bytes = 0.0;
    }
    
    return metrics;
}

void AdvancedMCPClient::resetMetrics() {
    std::lock_guard<std::mutex> lock(pImpl->metrics_mutex);
    pImpl->total_requests = 0;
    pImpl->successful_requests = 0;
    pImpl->failed_requests = 0;
    pImpl->cache_hits = 0;
    pImpl->cache_misses = 0;
    pImpl->request_times.clear();
    pImpl->response_sizes.clear();
}

} // namespace mcp
} // namespace cogniware

