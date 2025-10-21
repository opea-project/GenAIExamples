#include "mcp/mcp_tool_registry.h"
#include "mcp/mcp_filesystem.h"
#include "mcp/mcp_internet.h"
#include "mcp/mcp_database.h"
#include "mcp/mcp_application.h"
#include "mcp/mcp_system_services.h"
#include "mcp/mcp_security.h"
#include "mcp/mcp_resources.h"
#include <mutex>
#include <algorithm>

namespace cogniware {
namespace mcp {
namespace tool_registry {

class MCPToolRegistry::Impl {
public:
    std::unordered_map<std::string, ToolMetadata> metadata_map;
    std::unordered_map<std::string, MCPTool> tool_map;
    mutable std::mutex mutex;
};

MCPToolRegistry& MCPToolRegistry::getInstance() {
    static MCPToolRegistry instance;
    if (!instance.pImpl) {
        instance.pImpl = std::make_unique<Impl>();
    }
    return instance;
}

bool MCPToolRegistry::registerTool(const ToolMetadata& metadata, const MCPTool& tool) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    pImpl->metadata_map[metadata.tool_id] = metadata;
    pImpl->tool_map[metadata.tool_id] = tool;
    
    return true;
}

bool MCPToolRegistry::unregisterTool(const std::string& tool_id) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    pImpl->metadata_map.erase(tool_id);
    pImpl->tool_map.erase(tool_id);
    
    return true;
}

std::vector<ToolMetadata> MCPToolRegistry::listTools(ToolCategory category) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    std::vector<ToolMetadata> result;
    for (const auto& [id, metadata] : pImpl->metadata_map) {
        if (category == ToolCategory{} || metadata.category == category) {
            result.push_back(metadata);
        }
    }
    
    return result;
}

std::vector<ToolMetadata> MCPToolRegistry::searchTools(const std::string& query) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    std::vector<ToolMetadata> result;
    std::string query_lower = query;
    std::transform(query_lower.begin(), query_lower.end(), query_lower.begin(), ::tolower);
    
    for (const auto& [id, metadata] : pImpl->metadata_map) {
        std::string name_lower = metadata.name;
        std::transform(name_lower.begin(), name_lower.end(), name_lower.begin(), ::tolower);
        
        std::string desc_lower = metadata.description;
        std::transform(desc_lower.begin(), desc_lower.end(), desc_lower.begin(), ::tolower);
        
        if (name_lower.find(query_lower) != std::string::npos ||
            desc_lower.find(query_lower) != std::string::npos) {
            result.push_back(metadata);
        }
    }
    
    return result;
}

ToolMetadata MCPToolRegistry::getToolMetadata(const std::string& tool_id) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    auto it = pImpl->metadata_map.find(tool_id);
    return (it != pImpl->metadata_map.end()) ? it->second : ToolMetadata{};
}

std::string MCPToolRegistry::executeTool(const std::string& tool_id,
                                        const std::unordered_map<std::string, std::string>& params) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    auto it = pImpl->tool_map.find(tool_id);
    if (it == pImpl->tool_map.end()) {
        return "Tool not found: " + tool_id;
    }
    
    auto metadata_it = pImpl->metadata_map.find(tool_id);
    if (metadata_it != pImpl->metadata_map.end() && !metadata_it->second.enabled) {
        return "Tool is disabled: " + tool_id;
    }
    
    return it->second.handler(params);
}

bool MCPToolRegistry::enableTool(const std::string& tool_id) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    auto it = pImpl->metadata_map.find(tool_id);
    if (it != pImpl->metadata_map.end()) {
        it->second.enabled = true;
        return true;
    }
    return false;
}

bool MCPToolRegistry::disableTool(const std::string& tool_id) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    auto it = pImpl->metadata_map.find(tool_id);
    if (it != pImpl->metadata_map.end()) {
        it->second.enabled = false;
        return true;
    }
    return false;
}

bool MCPToolRegistry::isToolEnabled(const std::string& tool_id) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    auto it = pImpl->metadata_map.find(tool_id);
    return (it != pImpl->metadata_map.end()) && it->second.enabled;
}

size_t MCPToolRegistry::getToolCount() const {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    return pImpl->tool_map.size();
}

std::vector<std::string> MCPToolRegistry::getCategories() const {
    return {"FILESYSTEM", "NETWORK", "DATABASE", "SYSTEM", "SECURITY", "RESOURCE", "APPLICATION"};
}

void registerAllMCPTools(AdvancedMCPServer& server) {
    // Register filesystem tools
    filesystem::MCPFilesystemTools::registerAllTools(server);
    
    // Register internet tools
    internet::MCPInternetTools::registerAllTools(server);
    
    // Register database tools
    database::MCPDatabaseTools::registerAllTools(server);
    
    // Register application tools
    application::MCPApplicationTools::registerAllTools(server);
    
    // Register system services tools
    system_services::MCPSystemServicesTools::registerAllTools(server);
    
    // Register security tools
    security::MCPSecurityTools::registerAllTools(server);
    
    // Register resource tools
    resources::MCPResourceTools::registerAllTools(server);
}

} // namespace tool_registry
} // namespace mcp
} // namespace cogniware

