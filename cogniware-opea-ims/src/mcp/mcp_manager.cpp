#include "mcp/mcp_core.h"
#include <algorithm>
#include <mutex>

namespace cogniware {
namespace mcp {

// MCPConnectionManager Implementation
class MCPConnectionManager::ManagerImpl {
public:
    std::unordered_map<std::string, std::shared_ptr<AdvancedMCPServer>> servers;
    std::unordered_map<std::string, std::shared_ptr<AdvancedMCPClient>> clients;
    mutable std::mutex servers_mutex;
    mutable std::mutex clients_mutex;
};

MCPConnectionManager::MCPConnectionManager()
    : pImpl(std::make_unique<ManagerImpl>()) {}

MCPConnectionManager::~MCPConnectionManager() = default;

MCPConnectionManager& MCPConnectionManager::getInstance() {
    static MCPConnectionManager instance;
    return instance;
}

bool MCPConnectionManager::createServer(
    const std::string& server_id,
    const MCPServerCapabilities& capabilities) {
    
    std::lock_guard<std::mutex> lock(pImpl->servers_mutex);
    
    if (pImpl->servers.find(server_id) != pImpl->servers.end()) {
        return false;
    }

    auto server = std::make_shared<AdvancedMCPServer>();
    if (server->initialize(capabilities)) {
        pImpl->servers[server_id] = server;
        return true;
    }
    
    return false;
}

bool MCPConnectionManager::destroyServer(const std::string& server_id) {
    std::lock_guard<std::mutex> lock(pImpl->servers_mutex);
    
    auto it = pImpl->servers.find(server_id);
    if (it != pImpl->servers.end()) {
        it->second->shutdown();
        pImpl->servers.erase(it);
        return true;
    }
    
    return false;
}

std::shared_ptr<AdvancedMCPServer> MCPConnectionManager::getServer(
    const std::string& server_id) {
    
    std::lock_guard<std::mutex> lock(pImpl->servers_mutex);
    auto it = pImpl->servers.find(server_id);
    return (it != pImpl->servers.end()) ? it->second : nullptr;
}

bool MCPConnectionManager::createClient(const std::string& client_id) {
    std::lock_guard<std::mutex> lock(pImpl->clients_mutex);
    
    if (pImpl->clients.find(client_id) != pImpl->clients.end()) {
        return false;
    }

    pImpl->clients[client_id] = std::make_shared<AdvancedMCPClient>();
    return true;
}

bool MCPConnectionManager::destroyClient(const std::string& client_id) {
    std::lock_guard<std::mutex> lock(pImpl->clients_mutex);
    
    auto it = pImpl->clients.find(client_id);
    if (it != pImpl->clients.end()) {
        if (it->second->isConnected()) {
            it->second->disconnect();
        }
        pImpl->clients.erase(it);
        return true;
    }
    
    return false;
}

std::shared_ptr<AdvancedMCPClient> MCPConnectionManager::getClient(
    const std::string& client_id) {
    
    std::lock_guard<std::mutex> lock(pImpl->clients_mutex);
    auto it = pImpl->clients.find(client_id);
    return (it != pImpl->clients.end()) ? it->second : nullptr;
}

bool MCPConnectionManager::connectClientToServer(
    const std::string& client_id,
    const std::string& server_uri) {
    
    std::lock_guard<std::mutex> clients_lock(pImpl->clients_mutex);
    
    auto it = pImpl->clients.find(client_id);
    if (it == pImpl->clients.end()) {
        return false;
    }
    
    return it->second->connect(server_uri);
}

size_t MCPConnectionManager::getActiveServerCount() const {
    std::lock_guard<std::mutex> lock(pImpl->servers_mutex);
    return pImpl->servers.size();
}

size_t MCPConnectionManager::getActiveClientCount() const {
    std::lock_guard<std::mutex> lock(pImpl->clients_mutex);
    return pImpl->clients.size();
}

std::vector<std::string> MCPConnectionManager::getServerIds() const {
    std::lock_guard<std::mutex> lock(pImpl->servers_mutex);
    
    std::vector<std::string> ids;
    ids.reserve(pImpl->servers.size());
    
    for (const auto& [id, _] : pImpl->servers) {
        ids.push_back(id);
    }
    
    return ids;
}

std::vector<std::string> MCPConnectionManager::getClientIds() const {
    std::lock_guard<std::mutex> lock(pImpl->clients_mutex);
    
    std::vector<std::string> ids;
    ids.reserve(pImpl->clients.size());
    
    for (const auto& [id, _] : pImpl->clients) {
        ids.push_back(id);
    }
    
    return ids;
}

// GlobalMCPSystem Implementation
class GlobalMCPSystem::GlobalImpl {
public:
    bool initialized;
    std::vector<std::string> supported_protocols;
    std::unordered_map<std::string, std::vector<MCPTool>> tool_registry;
    std::unordered_map<std::string, std::vector<MCPResource>> resource_registry;
    mutable std::mutex registry_mutex;
    
    // System metrics
    size_t total_requests_processed;
    std::vector<double> request_latencies;
    std::chrono::system_clock::time_point start_time;
    mutable std::mutex metrics_mutex;
    
    GlobalImpl() 
        : initialized(false)
        , total_requests_processed(0) {}
};

GlobalMCPSystem::GlobalMCPSystem()
    : pImpl(std::make_unique<GlobalImpl>()) {}

GlobalMCPSystem::~GlobalMCPSystem() {
    if (pImpl->initialized) {
        shutdown();
    }
}

GlobalMCPSystem& GlobalMCPSystem::getInstance() {
    static GlobalMCPSystem instance;
    return instance;
}

bool GlobalMCPSystem::initialize() {
    if (pImpl->initialized) {
        return false;
    }

    pImpl->start_time = std::chrono::system_clock::now();
    pImpl->initialized = true;
    
    // Register default protocols
    registerProtocol("mcp", MCP_VERSION);
    registerProtocol("stdio", "1.0");
    registerProtocol("http", "1.1");
    
    return true;
}

bool GlobalMCPSystem::shutdown() {
    if (!pImpl->initialized) {
        return false;
    }

    std::lock_guard<std::mutex> lock(pImpl->registry_mutex);
    pImpl->tool_registry.clear();
    pImpl->resource_registry.clear();
    pImpl->supported_protocols.clear();
    pImpl->initialized = false;
    
    return true;
}

bool GlobalMCPSystem::isInitialized() const {
    return pImpl->initialized;
}

bool GlobalMCPSystem::registerProtocol(
    const std::string& protocol_name,
    const std::string& protocol_version) {
    
    if (!pImpl->initialized) {
        return false;
    }

    std::lock_guard<std::mutex> lock(pImpl->registry_mutex);
    
    std::string full_protocol = protocol_name + "/" + protocol_version;
    
    auto it = std::find(pImpl->supported_protocols.begin(),
                       pImpl->supported_protocols.end(),
                       full_protocol);
    
    if (it != pImpl->supported_protocols.end()) {
        return false;
    }
    
    pImpl->supported_protocols.push_back(full_protocol);
    return true;
}

std::vector<std::string> GlobalMCPSystem::getSupportedProtocols() const {
    if (!pImpl->initialized) {
        return {};
    }

    std::lock_guard<std::mutex> lock(pImpl->registry_mutex);
    return pImpl->supported_protocols;
}

std::vector<MCPTool> GlobalMCPSystem::discoverTools(const std::string& category) {
    if (!pImpl->initialized) {
        return {};
    }

    std::lock_guard<std::mutex> lock(pImpl->registry_mutex);
    
    std::vector<MCPTool> tools;
    
    if (category.empty()) {
        // Return all tools
        for (const auto& [cat, tool_list] : pImpl->tool_registry) {
            tools.insert(tools.end(), tool_list.begin(), tool_list.end());
        }
    } else {
        // Return tools for specific category
        auto it = pImpl->tool_registry.find(category);
        if (it != pImpl->tool_registry.end()) {
            tools = it->second;
        }
    }
    
    return tools;
}

std::vector<MCPTool> GlobalMCPSystem::searchTools(const std::string& query) {
    if (!pImpl->initialized) {
        return {};
    }

    std::lock_guard<std::mutex> lock(pImpl->registry_mutex);
    
    std::vector<MCPTool> matching_tools;
    
    for (const auto& [category, tool_list] : pImpl->tool_registry) {
        for (const auto& tool : tool_list) {
            // Simple search in name and description
            if (tool.name.find(query) != std::string::npos ||
                tool.description.find(query) != std::string::npos) {
                matching_tools.push_back(tool);
            }
        }
    }
    
    return matching_tools;
}

std::vector<MCPResource> GlobalMCPSystem::discoverResources(ResourceType type) {
    if (!pImpl->initialized) {
        return {};
    }

    std::lock_guard<std::mutex> lock(pImpl->registry_mutex);
    
    std::vector<MCPResource> resources;
    
    for (const auto& [category, resource_list] : pImpl->resource_registry) {
        for (const auto& resource : resource_list) {
            if (resource.type == type) {
                resources.push_back(resource);
            }
        }
    }
    
    return resources;
}

std::vector<MCPResource> GlobalMCPSystem::searchResources(const std::string& query) {
    if (!pImpl->initialized) {
        return {};
    }

    std::lock_guard<std::mutex> lock(pImpl->registry_mutex);
    
    std::vector<MCPResource> matching_resources;
    
    for (const auto& [category, resource_list] : pImpl->resource_registry) {
        for (const auto& resource : resource_list) {
            // Simple search in URI and name
            if (resource.uri.find(query) != std::string::npos ||
                resource.name.find(query) != std::string::npos ||
                resource.description.find(query) != std::string::npos) {
                matching_resources.push_back(resource);
            }
        }
    }
    
    return matching_resources;
}

GlobalMCPSystem::SystemMetrics GlobalMCPSystem::getSystemMetrics() const {
    SystemMetrics metrics;
    
    auto& manager = MCPConnectionManager::getInstance();
    metrics.total_servers = manager.getActiveServerCount();
    metrics.total_clients = manager.getActiveClientCount();
    
    std::lock_guard<std::mutex> registry_lock(pImpl->registry_mutex);
    
    size_t total_tools = 0;
    for (const auto& [category, tool_list] : pImpl->tool_registry) {
        total_tools += tool_list.size();
    }
    metrics.total_tools_registered = total_tools;
    
    size_t total_resources = 0;
    for (const auto& [category, resource_list] : pImpl->resource_registry) {
        total_resources += resource_list.size();
    }
    metrics.total_resources_registered = total_resources;
    
    std::lock_guard<std::mutex> metrics_lock(pImpl->metrics_mutex);
    metrics.total_requests_processed = pImpl->total_requests_processed;
    
    if (!pImpl->request_latencies.empty()) {
        metrics.avg_request_latency_ms = std::accumulate(
            pImpl->request_latencies.begin(),
            pImpl->request_latencies.end(),
            0.0) / pImpl->request_latencies.size();
    } else {
        metrics.avg_request_latency_ms = 0.0;
    }
    
    if (pImpl->initialized) {
        auto now = std::chrono::system_clock::now();
        auto uptime = std::chrono::duration_cast<std::chrono::seconds>(
            now - pImpl->start_time);
        metrics.system_uptime_seconds = uptime.count();
    } else {
        metrics.system_uptime_seconds = 0.0;
    }
    
    return metrics;
}

// Serialization utilities
std::string serializeMCPMessage(const MCPMessage& message) {
    // Simple JSON-like serialization (would use proper JSON library in production)
    std::stringstream ss;
    ss << "{"
       << "\"id\":\"" << message.id << "\","
       << "\"type\":" << static_cast<int>(message.type) << ","
       << "\"method\":\"" << message.method << "\""
       << "}";
    return ss.str();
}

MCPMessage deserializeMCPMessage(const std::string& json) {
    // Simple deserialization (would use proper JSON library in production)
    MCPMessage message;
    message.id = "deserialized_" + generateMessageId();
    message.type = MessageType::REQUEST;
    message.method = "unknown";
    message.timestamp = std::chrono::system_clock::now();
    return message;
}

} // namespace mcp
} // namespace cogniware

