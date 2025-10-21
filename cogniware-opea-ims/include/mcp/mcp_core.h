#ifndef MCP_CORE_H
#define MCP_CORE_H

#include <string>
#include <vector>
#include <memory>
#include <functional>
#include <unordered_map>
#include <chrono>
#include <variant>
#include <optional>

namespace cogniware {
namespace mcp {

// Forward declarations
struct MCPMessage;
struct MCPRequest;
struct MCPResponse;
struct MCPTool;
struct MCPResource;

// MCP Protocol version
constexpr const char* MCP_VERSION = "1.0.0";

// Message types
enum class MessageType {
    REQUEST,
    RESPONSE,
    NOTIFICATION,
    ERROR
};

// Request methods
enum class RequestMethod {
    INITIALIZE,
    TOOLS_LIST,
    TOOLS_CALL,
    RESOURCES_LIST,
    RESOURCES_READ,
    RESOURCES_SUBSCRIBE,
    PROMPT_GET,
    PROMPT_LIST,
    COMPLETION_COMPLETE,
    LOGGING_SET_LEVEL,
    PING
};

// Tool parameter types
enum class ParameterType {
    STRING,
    NUMBER,
    BOOLEAN,
    OBJECT,
    ARRAY,
    NULL_TYPE
};

// Resource types
enum class ResourceType {
    FILE,
    DIRECTORY,
    URL,
    DATABASE,
    STREAM,
    CUSTOM
};

// MCP parameter definition
struct MCPParameter {
    std::string name;
    ParameterType type;
    std::string description;
    bool required;
    std::variant<std::string, double, bool> default_value;
    std::vector<std::string> enum_values;
};

// MCP tool definition
struct MCPTool {
    std::string name;
    std::string description;
    std::vector<MCPParameter> parameters;
    std::unordered_map<std::string, std::string> metadata;
    
    // Handler function for tool execution
    std::function<std::string(const std::unordered_map<std::string, std::string>&)> handler;
};

// MCP resource definition
struct MCPResource {
    std::string uri;
    std::string name;
    ResourceType type;
    std::string description;
    std::string mime_type;
    size_t size;
    std::unordered_map<std::string, std::string> metadata;
};

// MCP message base
struct MCPMessage {
    std::string id;
    MessageType type;
    std::string method;
    std::chrono::system_clock::time_point timestamp;
    std::unordered_map<std::string, std::string> metadata;
};

// MCP request
struct MCPRequest : public MCPMessage {
    RequestMethod request_method;
    std::unordered_map<std::string, std::string> parameters;
    std::string tool_name;
    std::vector<std::string> resource_uris;
};

// MCP response
struct MCPResponse : public MCPMessage {
    bool success;
    std::string result;
    std::string error_message;
    int error_code;
    std::unordered_map<std::string, std::string> data;
};

// MCP server capabilities
struct MCPServerCapabilities {
    bool supports_tools;
    bool supports_resources;
    bool supports_prompts;
    bool supports_completion;
    bool supports_logging;
    std::vector<std::string> supported_protocols;
    std::string server_name;
    std::string server_version;
};

// MCP client capabilities
struct MCPClientCapabilities {
    bool supports_sampling;
    bool supports_roots;
    std::string client_name;
    std::string client_version;
};

// MCP server interface
class MCPServer {
public:
    virtual ~MCPServer() = default;
    
    // Lifecycle
    virtual bool initialize(const MCPServerCapabilities& capabilities) = 0;
    virtual bool shutdown() = 0;
    virtual bool isRunning() const = 0;
    
    // Tool management
    virtual bool registerTool(const MCPTool& tool) = 0;
    virtual bool unregisterTool(const std::string& tool_name) = 0;
    virtual std::vector<MCPTool> listTools() const = 0;
    virtual MCPResponse callTool(const std::string& tool_name,
                                  const std::unordered_map<std::string, std::string>& params) = 0;
    
    // Resource management
    virtual bool registerResource(const MCPResource& resource) = 0;
    virtual bool unregisterResource(const std::string& uri) = 0;
    virtual std::vector<MCPResource> listResources() const = 0;
    virtual MCPResponse readResource(const std::string& uri) = 0;
    
    // Message handling
    virtual MCPResponse handleRequest(const MCPRequest& request) = 0;
    virtual void sendNotification(const std::string& method,
                                   const std::unordered_map<std::string, std::string>& params) = 0;
    
    // Capabilities
    virtual MCPServerCapabilities getCapabilities() const = 0;
};

// MCP client interface
class MCPClient {
public:
    virtual ~MCPClient() = default;
    
    // Connection
    virtual bool connect(const std::string& server_uri) = 0;
    virtual bool disconnect() = 0;
    virtual bool isConnected() const = 0;
    
    // Initialization
    virtual MCPResponse initialize(const MCPClientCapabilities& capabilities) = 0;
    
    // Tool operations
    virtual std::vector<MCPTool> listTools() = 0;
    virtual MCPResponse callTool(const std::string& tool_name,
                                  const std::unordered_map<std::string, std::string>& params) = 0;
    
    // Resource operations
    virtual std::vector<MCPResource> listResources() = 0;
    virtual MCPResponse readResource(const std::string& uri) = 0;
    virtual bool subscribeToResource(const std::string& uri) = 0;
    
    // Generic request
    virtual MCPResponse sendRequest(const MCPRequest& request) = 0;
    
    // Capabilities
    virtual MCPServerCapabilities getServerCapabilities() const = 0;
};

// Advanced MCP server implementation
class AdvancedMCPServer : public MCPServer {
public:
    AdvancedMCPServer();
    ~AdvancedMCPServer() override;
    
    // Lifecycle
    bool initialize(const MCPServerCapabilities& capabilities) override;
    bool shutdown() override;
    bool isRunning() const override;
    
    // Tool management
    bool registerTool(const MCPTool& tool) override;
    bool unregisterTool(const std::string& tool_name) override;
    std::vector<MCPTool> listTools() const override;
    MCPResponse callTool(const std::string& tool_name,
                        const std::unordered_map<std::string, std::string>& params) override;
    
    // Resource management
    bool registerResource(const MCPResource& resource) override;
    bool unregisterResource(const std::string& uri) override;
    std::vector<MCPResource> listResources() const override;
    MCPResponse readResource(const std::string& uri) override;
    
    // Message handling
    MCPResponse handleRequest(const MCPRequest& request) override;
    void sendNotification(const std::string& method,
                         const std::unordered_map<std::string, std::string>& params) override;
    
    // Capabilities
    MCPServerCapabilities getCapabilities() const override;
    
    // Extended functionality
    void setRequestTimeout(std::chrono::milliseconds timeout);
    void setMaxConcurrentRequests(size_t max_requests);
    
    struct ServerMetrics {
        size_t total_requests;
        size_t successful_requests;
        size_t failed_requests;
        size_t tools_registered;
        size_t resources_registered;
        double avg_request_time_ms;
        size_t active_connections;
    };
    
    ServerMetrics getMetrics() const;
    void resetMetrics();

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

// Advanced MCP client implementation
class AdvancedMCPClient : public MCPClient {
public:
    AdvancedMCPClient();
    ~AdvancedMCPClient() override;
    
    // Connection
    bool connect(const std::string& server_uri) override;
    bool disconnect() override;
    bool isConnected() const override;
    
    // Initialization
    MCPResponse initialize(const MCPClientCapabilities& capabilities) override;
    
    // Tool operations
    std::vector<MCPTool> listTools() override;
    MCPResponse callTool(const std::string& tool_name,
                        const std::unordered_map<std::string, std::string>& params) override;
    
    // Resource operations
    std::vector<MCPResource> listResources() override;
    MCPResponse readResource(const std::string& uri) override;
    bool subscribeToResource(const std::string& uri) override;
    
    // Generic request
    MCPResponse sendRequest(const MCPRequest& request) override;
    
    // Capabilities
    MCPServerCapabilities getServerCapabilities() const override;
    
    // Extended functionality
    void setConnectionTimeout(std::chrono::milliseconds timeout);
    void setRetryAttempts(int attempts);
    void enableCaching(bool enable);
    
    struct ClientMetrics {
        size_t total_requests;
        size_t successful_requests;
        size_t failed_requests;
        size_t cache_hits;
        size_t cache_misses;
        double avg_request_time_ms;
        double avg_response_size_bytes;
    };
    
    ClientMetrics getMetrics() const;
    void resetMetrics();

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

// MCP connection manager
class MCPConnectionManager {
public:
    static MCPConnectionManager& getInstance();
    
    // Server management
    bool createServer(const std::string& server_id,
                     const MCPServerCapabilities& capabilities);
    bool destroyServer(const std::string& server_id);
    std::shared_ptr<AdvancedMCPServer> getServer(const std::string& server_id);
    
    // Client management
    bool createClient(const std::string& client_id);
    bool destroyClient(const std::string& client_id);
    std::shared_ptr<AdvancedMCPClient> getClient(const std::string& client_id);
    
    // Connection management
    bool connectClientToServer(const std::string& client_id,
                               const std::string& server_uri);
    
    // Statistics
    size_t getActiveServerCount() const;
    size_t getActiveClientCount() const;
    std::vector<std::string> getServerIds() const;
    std::vector<std::string> getClientIds() const;

private:
    MCPConnectionManager();
    ~MCPConnectionManager();
    MCPConnectionManager(const MCPConnectionManager&) = delete;
    MCPConnectionManager& operator=(const MCPConnectionManager&) = delete;
    
    class ManagerImpl;
    std::unique_ptr<ManagerImpl> pImpl;
};

// Global MCP system
class GlobalMCPSystem {
public:
    static GlobalMCPSystem& getInstance();
    
    // System initialization
    bool initialize();
    bool shutdown();
    bool isInitialized() const;
    
    // Protocol management
    bool registerProtocol(const std::string& protocol_name,
                         const std::string& protocol_version);
    std::vector<std::string> getSupportedProtocols() const;
    
    // Tool discovery
    std::vector<MCPTool> discoverTools(const std::string& category = "");
    std::vector<MCPTool> searchTools(const std::string& query);
    
    // Resource discovery
    std::vector<MCPResource> discoverResources(ResourceType type);
    std::vector<MCPResource> searchResources(const std::string& query);
    
    // System metrics
    struct SystemMetrics {
        size_t total_servers;
        size_t total_clients;
        size_t total_tools_registered;
        size_t total_resources_registered;
        size_t total_requests_processed;
        double avg_request_latency_ms;
        double system_uptime_seconds;
    };
    
    SystemMetrics getSystemMetrics() const;

private:
    GlobalMCPSystem();
    ~GlobalMCPSystem();
    GlobalMCPSystem(const GlobalMCPSystem&) = delete;
    GlobalMCPSystem& operator=(const GlobalMCPSystem&) = delete;
    
    class GlobalImpl;
    std::unique_ptr<GlobalImpl> pImpl;
};

// Utility functions
std::string serializeMCPMessage(const MCPMessage& message);
MCPMessage deserializeMCPMessage(const std::string& json);
std::string generateMessageId();
bool validateMCPRequest(const MCPRequest& request);
bool validateMCPResponse(const MCPResponse& response);

} // namespace mcp
} // namespace cogniware

#endif // MCP_CORE_H

