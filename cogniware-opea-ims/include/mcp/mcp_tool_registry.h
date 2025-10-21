#pragma once

#include "mcp_core.h"
#include <string>
#include <vector>
#include <memory>
#include <unordered_map>
#include <functional>

namespace cogniware {
namespace mcp {
namespace tool_registry {

/**
 * @brief Tool category
 */
enum class ToolCategory {
    FILESYSTEM,
    NETWORK,
    DATABASE,
    SYSTEM,
    SECURITY,
    RESOURCE,
    APPLICATION,
    CUSTOM
};

/**
 * @brief Tool capability metadata
 */
struct ToolCapability {
    std::string name;
    std::string description;
    std::vector<std::string> required_permissions;
    bool is_dangerous = false;
};

/**
 * @brief Tool metadata
 */
struct ToolMetadata {
    std::string tool_id;
    std::string name;
    std::string description;
    std::string version;
    ToolCategory category;
    std::vector<std::string> tags;
    std::vector<ToolCapability> capabilities;
    bool enabled = true;
    bool requires_authentication = false;
    std::chrono::system_clock::time_point registered_at;
};

/**
 * @brief MCP Tool Registry
 * 
 * Central registry for discovering and managing MCP tools
 */
class MCPToolRegistry {
public:
    static MCPToolRegistry& getInstance();
    
    // Tool registration
    bool registerTool(const ToolMetadata& metadata, const MCPTool& tool);
    bool unregisterTool(const std::string& tool_id);
    
    // Tool discovery
    std::vector<ToolMetadata> listTools(ToolCategory category = {});
    std::vector<ToolMetadata> searchTools(const std::string& query);
    ToolMetadata getToolMetadata(const std::string& tool_id);
    
    // Tool execution
    std::string executeTool(const std::string& tool_id,
                           const std::unordered_map<std::string, std::string>& params);
    
    // Tool management
    bool enableTool(const std::string& tool_id);
    bool disableTool(const std::string& tool_id);
    bool isToolEnabled(const std::string& tool_id);
    
    // Statistics
    size_t getToolCount() const;
    std::vector<std::string> getCategories() const;

private:
    MCPToolRegistry() = default;
    ~MCPToolRegistry() = default;
    MCPToolRegistry(const MCPToolRegistry&) = delete;
    MCPToolRegistry& operator=(const MCPToolRegistry&) = delete;
    
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

/**
 * @brief Register all MCP tools
 */
void registerAllMCPTools(AdvancedMCPServer& server);

} // namespace tool_registry
} // namespace mcp
} // namespace cogniware

