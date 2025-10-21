#include <gtest/gtest.h>
#include "mcp/mcp_core.h"
#include <thread>
#include <chrono>

using namespace cogniware::mcp;

class MCPCoreTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Setup test environment
    }

    void TearDown() override {
        // Cleanup
    }

    MCPServerCapabilities createServerCapabilities() {
        MCPServerCapabilities caps;
        caps.supports_tools = true;
        caps.supports_resources = true;
        caps.supports_prompts = true;
        caps.supports_completion = false;
        caps.supports_logging = true;
        caps.server_name = "Test Server";
        caps.server_version = "1.0.0";
        caps.supported_protocols = {"mcp/1.0", "stdio/1.0"};
        return caps;
    }

    MCPClientCapabilities createClientCapabilities() {
        MCPClientCapabilities caps;
        caps.supports_sampling = true;
        caps.supports_roots = true;
        caps.client_name = "Test Client";
        caps.client_version = "1.0.0";
        return caps;
    }

    MCPTool createTestTool(const std::string& name) {
        MCPTool tool;
        tool.name = name;
        tool.description = "Test tool: " + name;
        
        MCPParameter param;
        param.name = "input";
        param.type = ParameterType::STRING;
        param.description = "Input parameter";
        param.required = true;
        tool.parameters.push_back(param);
        
        tool.handler = [](const std::unordered_map<std::string, std::string>& params) {
            auto it = params.find("input");
            return it != params.end() ? "Processed: " + it->second : "No input";
        };
        
        return tool;
    }

    MCPResource createTestResource(const std::string& uri) {
        MCPResource resource;
        resource.uri = uri;
        resource.name = "Test Resource";
        resource.type = ResourceType::FILE;
        resource.description = "Test resource at " + uri;
        resource.mime_type = "text/plain";
        resource.size = 1024;
        return resource;
    }
};

// Test 1: Server initialization and shutdown
TEST_F(MCPCoreTest, ServerInitializeShutdown) {
    AdvancedMCPServer server;
    
    EXPECT_FALSE(server.isRunning());
    
    auto caps = createServerCapabilities();
    ASSERT_TRUE(server.initialize(caps));
    EXPECT_TRUE(server.isRunning());
    
    ASSERT_TRUE(server.shutdown());
    EXPECT_FALSE(server.isRunning());
}

// Test 2: Server double initialization
TEST_F(MCPCoreTest, ServerDoubleInitialization) {
    AdvancedMCPServer server;
    auto caps = createServerCapabilities();
    
    ASSERT_TRUE(server.initialize(caps));
    EXPECT_FALSE(server.initialize(caps));  // Should fail
}

// Test 3: Tool registration
TEST_F(MCPCoreTest, ToolRegistration) {
    AdvancedMCPServer server;
    server.initialize(createServerCapabilities());
    
    auto tool = createTestTool("test_tool");
    ASSERT_TRUE(server.registerTool(tool));
    
    auto tools = server.listTools();
    EXPECT_EQ(tools.size(), 1);
    EXPECT_EQ(tools[0].name, "test_tool");
}

// Test 4: Tool duplicate registration
TEST_F(MCPCoreTest, ToolDuplicateRegistration) {
    AdvancedMCPServer server;
    server.initialize(createServerCapabilities());
    
    auto tool = createTestTool("test_tool");
    ASSERT_TRUE(server.registerTool(tool));
    EXPECT_FALSE(server.registerTool(tool));  // Should fail
}

// Test 5: Tool unregistration
TEST_F(MCPCoreTest, ToolUnregistration) {
    AdvancedMCPServer server;
    server.initialize(createServerCapabilities());
    
    auto tool = createTestTool("test_tool");
    server.registerTool(tool);
    
    ASSERT_TRUE(server.unregisterTool("test_tool"));
    
    auto tools = server.listTools();
    EXPECT_EQ(tools.size(), 0);
}

// Test 6: Tool execution
TEST_F(MCPCoreTest, ToolExecution) {
    AdvancedMCPServer server;
    server.initialize(createServerCapabilities());
    
    auto tool = createTestTool("echo_tool");
    server.registerTool(tool);
    
    std::unordered_map<std::string, std::string> params;
    params["input"] = "Hello, MCP!";
    
    auto response = server.callTool("echo_tool", params);
    
    EXPECT_TRUE(response.success);
    EXPECT_EQ(response.result, "Processed: Hello, MCP!");
}

// Test 7: Tool execution with missing parameters
TEST_F(MCPCoreTest, ToolExecutionMissingParameters) {
    AdvancedMCPServer server;
    server.initialize(createServerCapabilities());
    
    auto tool = createTestTool("test_tool");
    server.registerTool(tool);
    
    std::unordered_map<std::string, std::string> params;
    // Missing required "input" parameter
    
    auto response = server.callTool("test_tool", params);
    
    EXPECT_FALSE(response.success);
    EXPECT_EQ(response.error_code, 400);
}

// Test 8: Tool execution non-existent tool
TEST_F(MCPCoreTest, ToolExecutionNonExistent) {
    AdvancedMCPServer server;
    server.initialize(createServerCapabilities());
    
    std::unordered_map<std::string, std::string> params;
    auto response = server.callTool("nonexistent_tool", params);
    
    EXPECT_FALSE(response.success);
    EXPECT_EQ(response.error_code, 404);
}

// Test 9: Resource registration
TEST_F(MCPCoreTest, ResourceRegistration) {
    AdvancedMCPServer server;
    server.initialize(createServerCapabilities());
    
    auto resource = createTestResource("file:///test/resource.txt");
    ASSERT_TRUE(server.registerResource(resource));
    
    auto resources = server.listResources();
    EXPECT_EQ(resources.size(), 1);
    EXPECT_EQ(resources[0].uri, "file:///test/resource.txt");
}

// Test 10: Resource reading
TEST_F(MCPCoreTest, ResourceReading) {
    AdvancedMCPServer server;
    server.initialize(createServerCapabilities());
    
    auto resource = createTestResource("file:///test/data.txt");
    server.registerResource(resource);
    
    auto response = server.readResource("file:///test/data.txt");
    
    EXPECT_TRUE(response.success);
    EXPECT_FALSE(response.result.empty());
}

// Test 11: Request handling - PING
TEST_F(MCPCoreTest, RequestHandlingPing) {
    AdvancedMCPServer server;
    server.initialize(createServerCapabilities());
    
    MCPRequest request;
    request.id = generateMessageId();
    request.type = MessageType::REQUEST;
    request.request_method = RequestMethod::PING;
    request.method = "ping";
    
    auto response = server.handleRequest(request);
    
    EXPECT_TRUE(response.success);
    EXPECT_EQ(response.result, "pong");
}

// Test 12: Server capabilities
TEST_F(MCPCoreTest, ServerCapabilities) {
    AdvancedMCPServer server;
    auto caps = createServerCapabilities();
    server.initialize(caps);
    
    auto retrieved_caps = server.getCapabilities();
    
    EXPECT_EQ(retrieved_caps.server_name, "Test Server");
    EXPECT_TRUE(retrieved_caps.supports_tools);
    EXPECT_TRUE(retrieved_caps.supports_resources);
}

// Test 13: Server metrics
TEST_F(MCPCoreTest, ServerMetrics) {
    AdvancedMCPServer server;
    server.initialize(createServerCapabilities());
    
    auto tool = createTestTool("test_tool");
    server.registerTool(tool);
    
    std::unordered_map<std::string, std::string> params;
    params["input"] = "test";
    
    server.callTool("test_tool", params);
    server.callTool("test_tool", params);
    
    auto metrics = server.getMetrics();
    
    EXPECT_EQ(metrics.total_requests, 2);
    EXPECT_EQ(metrics.successful_requests, 2);
    EXPECT_EQ(metrics.tools_registered, 1);
}

// Test 14: Client connection
TEST_F(MCPCoreTest, ClientConnection) {
    AdvancedMCPClient client;
    
    EXPECT_FALSE(client.isConnected());
    
    ASSERT_TRUE(client.connect("mcp://localhost:8080"));
    EXPECT_TRUE(client.isConnected());
    
    ASSERT_TRUE(client.disconnect());
    EXPECT_FALSE(client.isConnected());
}

// Test 15: Client initialization
TEST_F(MCPCoreTest, ClientInitialization) {
    AdvancedMCPClient client;
    client.connect("mcp://localhost:8080");
    
    auto caps = createClientCapabilities();
    auto response = client.initialize(caps);
    
    EXPECT_TRUE(response.success);
}

// Test 16: Client tool listing
TEST_F(MCPCoreTest, ClientToolListing) {
    AdvancedMCPClient client;
    client.connect("mcp://localhost:8080");
    
    auto tools = client.listTools();
    // Would contain actual tools in production
}

// Test 17: Client tool calling
TEST_F(MCPCoreTest, ClientToolCalling) {
    AdvancedMCPClient client;
    client.connect("mcp://localhost:8080");
    
    std::unordered_map<std::string, std::string> params;
    params["input"] = "test";
    
    auto response = client.callTool("test_tool", params);
    EXPECT_TRUE(response.success);
}

// Test 18: Client caching
TEST_F(MCPCoreTest, ClientCaching) {
    AdvancedMCPClient client;
    client.enableCaching(true);
    client.connect("mcp://localhost:8080");
    
    // First call - cache miss
    auto tools1 = client.listTools();
    
    // Second call - should hit cache
    auto tools2 = client.listTools();
    
    auto metrics = client.getMetrics();
    EXPECT_GT(metrics.cache_hits, 0);
}

// Test 19: Client metrics
TEST_F(MCPCoreTest, ClientMetrics) {
    AdvancedMCPClient client;
    client.connect("mcp://localhost:8080");
    
    std::unordered_map<std::string, std::string> params;
    client.callTool("test_tool", params);
    
    auto metrics = client.getMetrics();
    EXPECT_GT(metrics.total_requests, 0);
}

// Test 20: Connection Manager - Server management
TEST_F(MCPCoreTest, ConnectionManagerServerManagement) {
    auto& manager = MCPConnectionManager::getInstance();
    
    auto caps = createServerCapabilities();
    ASSERT_TRUE(manager.createServer("server1", caps));
    EXPECT_EQ(manager.getActiveServerCount(), 1);
    
    auto server = manager.getServer("server1");
    ASSERT_NE(server, nullptr);
    EXPECT_TRUE(server->isRunning());
    
    ASSERT_TRUE(manager.destroyServer("server1"));
    EXPECT_EQ(manager.getActiveServerCount(), 0);
}

// Test 21: Connection Manager - Client management
TEST_F(MCPCoreTest, ConnectionManagerClientManagement) {
    auto& manager = MCPConnectionManager::getInstance();
    
    ASSERT_TRUE(manager.createClient("client1"));
    EXPECT_EQ(manager.getActiveClientCount(), 1);
    
    auto client = manager.getClient("client1");
    ASSERT_NE(client, nullptr);
    
    ASSERT_TRUE(manager.destroyClient("client1"));
    EXPECT_EQ(manager.getActiveClientCount(), 0);
}

// Test 22: Connection Manager - Client-Server connection
TEST_F(MCPCoreTest, ConnectionManagerClientServerConnection) {
    auto& manager = MCPConnectionManager::getInstance();
    
    manager.createServer("server1", createServerCapabilities());
    manager.createClient("client1");
    
    ASSERT_TRUE(manager.connectClientToServer("client1", "mcp://server1"));
    
    auto client = manager.getClient("client1");
    EXPECT_TRUE(client->isConnected());
    
    manager.destroyClient("client1");
    manager.destroyServer("server1");
}

// Test 23: Global MCP System - Initialization
TEST_F(MCPCoreTest, GlobalMCPSystemInitialization) {
    auto& global = GlobalMCPSystem::getInstance();
    
    ASSERT_TRUE(global.initialize());
    EXPECT_TRUE(global.isInitialized());
    
    ASSERT_TRUE(global.shutdown());
    EXPECT_FALSE(global.isInitialized());
}

// Test 24: Global MCP System - Protocol registration
TEST_F(MCPCoreTest, GlobalMCPSystemProtocolRegistration) {
    auto& global = GlobalMCPSystem::getInstance();
    global.initialize();
    
    auto protocols = global.getSupportedProtocols();
    EXPECT_GT(protocols.size(), 0);
    
    ASSERT_TRUE(global.registerProtocol("custom", "1.0"));
    
    protocols = global.getSupportedProtocols();
    bool found = false;
    for (const auto& p : protocols) {
        if (p == "custom/1.0") {
            found = true;
            break;
        }
    }
    EXPECT_TRUE(found);
    
    global.shutdown();
}

// Test 25: Global MCP System - Tool discovery
TEST_F(MCPCoreTest, GlobalMCPSystemToolDiscovery) {
    auto& global = GlobalMCPSystem::getInstance();
    global.initialize();
    
    auto tools = global.discoverTools();
    // Would contain discovered tools in production
    
    global.shutdown();
}

// Test 26: Global MCP System - Resource discovery
TEST_F(MCPCoreTest, GlobalMCPSystemResourceDiscovery) {
    auto& global = GlobalMCPSystem::getInstance();
    global.initialize();
    
    auto resources = global.discoverResources(ResourceType::FILE);
    // Would contain discovered resources in production
    
    global.shutdown();
}

// Test 27: Global MCP System - System metrics
TEST_F(MCPCoreTest, GlobalMCPSystemMetrics) {
    auto& global = GlobalMCPSystem::getInstance();
    global.initialize();
    
    auto& manager = MCPConnectionManager::getInstance();
    manager.createServer("test_server", createServerCapabilities());
    manager.createClient("test_client");
    
    auto metrics = global.getSystemMetrics();
    EXPECT_GT(metrics.total_servers, 0);
    EXPECT_GT(metrics.total_clients, 0);
    EXPECT_GT(metrics.system_uptime_seconds, 0.0);
    
    manager.destroyServer("test_server");
    manager.destroyClient("test_client");
    global.shutdown();
}

// Test 28: Message ID generation
TEST_F(MCPCoreTest, MessageIdGeneration) {
    auto id1 = generateMessageId();
    auto id2 = generateMessageId();
    
    EXPECT_FALSE(id1.empty());
    EXPECT_FALSE(id2.empty());
    EXPECT_NE(id1, id2);
}

// Test 29: Request validation
TEST_F(MCPCoreTest, RequestValidation) {
    MCPRequest valid_request;
    valid_request.id = generateMessageId();
    valid_request.method = "test";
    EXPECT_TRUE(validateMCPRequest(valid_request));
    
    MCPRequest invalid_request;
    EXPECT_FALSE(validateMCPRequest(invalid_request));
}

// Test 30: Concurrent server operations
TEST_F(MCPCoreTest, ConcurrentServerOperations) {
    AdvancedMCPServer server;
    server.initialize(createServerCapabilities());
    
    for (int i = 0; i < 5; ++i) {
        auto tool = createTestTool("tool_" + std::to_string(i));
        server.registerTool(tool);
    }
    
    std::vector<std::thread> threads;
    std::atomic<int> successful_calls{0};
    
    for (int t = 0; t < 3; ++t) {
        threads.emplace_back([&server, &successful_calls]() {
            for (int i = 0; i < 10; ++i) {
                std::unordered_map<std::string, std::string> params;
                params["input"] = "test_" + std::to_string(i);
                
                auto response = server.callTool("tool_0", params);
                if (response.success) {
                    ++successful_calls;
                }
            }
        });
    }
    
    for (auto& thread : threads) {
        thread.join();
    }
    
    EXPECT_EQ(successful_calls.load(), 30);
}

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}

