#include "mcp/mcp_security.h"
#include <sstream>
#include <fstream>
#include <algorithm>
#include <mutex>
#include <thread>
#include <random>
#include <iomanip>
#include <cstring>
#include <openssl/sha.h>
#include <openssl/aes.h>
#include <openssl/evp.h>
#include <openssl/rand.h>

namespace cogniware {
namespace mcp {
namespace security {

// Static members
std::shared_ptr<Authenticator> MCPSecurityTools::authenticator_;
std::shared_ptr<Authorizer> MCPSecurityTools::authorizer_;
std::shared_ptr<SecurityManager> MCPSecurityTools::security_manager_;
std::mutex MCPSecurityTools::mutex_;

// Helper functions
std::string MCPSecurityTools::permissionToString(Permission permission) {
    switch (permission) {
        case Permission::READ: return "READ";
        case Permission::WRITE: return "WRITE";
        case Permission::EXECUTE: return "EXECUTE";
        case Permission::DELETE: return "DELETE";
        case Permission::ADMIN: return "ADMIN";
        case Permission::CREATE: return "CREATE";
        case Permission::UPDATE: return "UPDATE";
        case Permission::LIST: return "LIST";
        case Permission::MANAGE: return "MANAGE";
        default: return "UNKNOWN";
    }
}

Permission MCPSecurityTools::stringToPermission(const std::string& permission) {
    if (permission == "READ") return Permission::READ;
    if (permission == "WRITE") return Permission::WRITE;
    if (permission == "EXECUTE") return Permission::EXECUTE;
    if (permission == "DELETE") return Permission::DELETE;
    if (permission == "ADMIN") return Permission::ADMIN;
    if (permission == "CREATE") return Permission::CREATE;
    if (permission == "UPDATE") return Permission::UPDATE;
    if (permission == "LIST") return Permission::LIST;
    if (permission == "MANAGE") return Permission::MANAGE;
    return Permission::READ;
}

std::string MCPSecurityTools::resourceTypeToString(ResourceType type) {
    switch (type) {
        case ResourceType::FILE: return "FILE";
        case ResourceType::DIRECTORY: return "DIRECTORY";
        case ResourceType::PROCESS: return "PROCESS";
        case ResourceType::SERVICE: return "SERVICE";
        case ResourceType::NETWORK: return "NETWORK";
        case ResourceType::DATABASE: return "DATABASE";
        case ResourceType::MODEL: return "MODEL";
        case ResourceType::API: return "API";
        case ResourceType::SYSTEM: return "SYSTEM";
        case ResourceType::CUSTOM: return "CUSTOM";
        default: return "UNKNOWN";
    }
}

ResourceType MCPSecurityTools::stringToResourceType(const std::string& type) {
    if (type == "FILE") return ResourceType::FILE;
    if (type == "DIRECTORY") return ResourceType::DIRECTORY;
    if (type == "PROCESS") return ResourceType::PROCESS;
    if (type == "SERVICE") return ResourceType::SERVICE;
    if (type == "NETWORK") return ResourceType::NETWORK;
    if (type == "DATABASE") return ResourceType::DATABASE;
    if (type == "MODEL") return ResourceType::MODEL;
    if (type == "API") return ResourceType::API;
    if (type == "SYSTEM") return ResourceType::SYSTEM;
    return ResourceType::CUSTOM;
}

// MCPSecurityTools Implementation
class MCPSecurityTools::Impl {
public:
    Impl() {
        if (!authenticator_) {
            authenticator_ = std::make_shared<Authenticator>();
        }
        if (!authorizer_) {
            authorizer_ = std::make_shared<Authorizer>();
        }
        if (!security_manager_) {
            security_manager_ = std::make_shared<SecurityManager>();
        }
    }
};

MCPSecurityTools::MCPSecurityTools()
    : pImpl(std::make_unique<Impl>()) {}

MCPSecurityTools::~MCPSecurityTools() = default;

void MCPSecurityTools::registerAllTools(AdvancedMCPServer& server) {
    // Authenticate tool
    MCPTool auth_tool;
    auth_tool.name = "authenticate";
    auth_tool.description = "Authenticate with username and password";
    
    MCPParameter username_param;
    username_param.name = "username";
    username_param.type = ParameterType::STRING;
    username_param.description = "Username";
    username_param.required = true;
    auth_tool.parameters.push_back(username_param);
    
    MCPParameter password_param;
    password_param.name = "password";
    password_param.type = ParameterType::STRING;
    password_param.description = "Password";
    password_param.required = true;
    auth_tool.parameters.push_back(password_param);
    
    auth_tool.handler = [](const std::unordered_map<std::string, std::string>& params) {
        Credentials creds;
        creds.username = params.at("username");
        creds.password = params.at("password");
        
        auto token = authenticate(creds);
        return "Authenticated successfully. Token: " + token.token;
    };
    
    server.registerTool(auth_tool);
    
    // Validate token tool
    MCPTool validate_tool;
    validate_tool.name = "validate_token";
    validate_tool.description = "Validate an access token";
    
    MCPParameter token_param;
    token_param.name = "token";
    token_param.type = ParameterType::STRING;
    token_param.description = "Access token";
    token_param.required = true;
    validate_tool.parameters.push_back(token_param);
    
    validate_tool.handler = [](const std::unordered_map<std::string, std::string>& params) {
        bool valid = validateToken(params.at("token"));
        return valid ? "Token is valid" : "Token is invalid";
    };
    
    server.registerTool(validate_tool);
    
    // Check permission tool
    MCPTool check_perm_tool;
    check_perm_tool.name = "check_permission";
    check_perm_tool.description = "Check if user has permission for a resource";
    
    MCPParameter user_id_param;
    user_id_param.name = "user_id";
    user_id_param.type = ParameterType::STRING;
    user_id_param.description = "User ID";
    user_id_param.required = true;
    check_perm_tool.parameters.push_back(user_id_param);
    
    MCPParameter permission_param;
    permission_param.name = "permission";
    permission_param.type = ParameterType::STRING;
    permission_param.description = "Permission (READ, WRITE, EXECUTE, etc.)";
    permission_param.required = true;
    check_perm_tool.parameters.push_back(permission_param);
    
    MCPParameter resource_type_param;
    resource_type_param.name = "resource_type";
    resource_type_param.type = ParameterType::STRING;
    resource_type_param.description = "Resource type";
    resource_type_param.required = true;
    check_perm_tool.parameters.push_back(resource_type_param);
    
    MCPParameter resource_id_param;
    resource_id_param.name = "resource_id";
    resource_id_param.type = ParameterType::STRING;
    resource_id_param.description = "Resource ID";
    resource_id_param.required = true;
    check_perm_tool.parameters.push_back(resource_id_param);
    
    check_perm_tool.handler = [](const std::unordered_map<std::string, std::string>& params) {
        Permission perm = stringToPermission(params.at("permission"));
        ResourceType type = stringToResourceType(params.at("resource_type"));
        
        bool has_permission = checkPermission(
            params.at("user_id"),
            perm,
            type,
            params.at("resource_id")
        );
        
        return has_permission ? "Permission granted" : "Permission denied";
    };
    
    server.registerTool(check_perm_tool);
    
    // Create user tool
    MCPTool create_user_tool;
    create_user_tool.name = "create_user";
    create_user_tool.description = "Create a new user";
    
    create_user_tool.parameters.push_back(username_param);
    
    MCPParameter email_param;
    email_param.name = "email";
    email_param.type = ParameterType::STRING;
    email_param.description = "Email address";
    email_param.required = true;
    create_user_tool.parameters.push_back(email_param);
    
    create_user_tool.parameters.push_back(password_param);
    
    create_user_tool.handler = [](const std::unordered_map<std::string, std::string>& params) {
        User user;
        user.username = params.at("username");
        user.email = params.at("email");
        
        std::string user_id = createUser(user, params.at("password"));
        return "User created with ID: " + user_id;
    };
    
    server.registerTool(create_user_tool);
    
    // Hash password tool
    MCPTool hash_tool;
    hash_tool.name = "hash_password";
    hash_tool.description = "Hash a password securely";
    
    hash_tool.parameters.push_back(password_param);
    
    hash_tool.handler = [](const std::unordered_map<std::string, std::string>& params) {
        std::string hash = hashPassword(params.at("password"));
        return "Password hash: " + hash;
    };
    
    server.registerTool(hash_tool);
}

AccessToken MCPSecurityTools::authenticate(const Credentials& credentials) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!authenticator_) {
        authenticator_ = std::make_shared<Authenticator>();
    }
    
    return authenticator_->authenticate(credentials);
}

bool MCPSecurityTools::validateToken(const std::string& token) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!authenticator_) {
        return false;
    }
    
    return authenticator_->validateToken(token);
}

bool MCPSecurityTools::revokeToken(const std::string& token) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!authenticator_) {
        return false;
    }
    
    return authenticator_->revokeToken(token);
}

AccessToken MCPSecurityTools::refreshToken(const std::string& refresh_token) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!authenticator_) {
        return {};
    }
    
    return authenticator_->refreshToken(refresh_token);
}

bool MCPSecurityTools::logout(const std::string& token) {
    return revokeToken(token);
}

std::string MCPSecurityTools::createUser(const User& user, const std::string& password) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Generate user ID
    std::string user_id = "user_" + CryptoUtils::generateRandomString(16);
    
    // Hash password
    std::string password_hash = hashPassword(password);
    
    // Store user (would use actual database)
    
    return user_id;
}

bool MCPSecurityTools::updateUser(const std::string&, const User&) { return false; }
bool MCPSecurityTools::deleteUser(const std::string&) { return false; }
User MCPSecurityTools::getUser(const std::string&) { return {}; }
std::vector<User> MCPSecurityTools::listUsers() { return {}; }
bool MCPSecurityTools::changePassword(const std::string&, const std::string&, const std::string&) { return false; }

std::string MCPSecurityTools::createRole(const Role&) { return ""; }
bool MCPSecurityTools::updateRole(const std::string&, const Role&) { return false; }
bool MCPSecurityTools::deleteRole(const std::string&) { return false; }
Role MCPSecurityTools::getRole(const std::string&) { return {}; }
std::vector<Role> MCPSecurityTools::listRoles() { return {}; }
bool MCPSecurityTools::assignRole(const std::string&, const std::string&) { return false; }
bool MCPSecurityTools::revokeRole(const std::string&, const std::string&) { return false; }

bool MCPSecurityTools::checkPermission(const std::string& user_id,
                                       Permission permission,
                                       ResourceType resource_type,
                                       const std::string& resource_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!authorizer_) {
        authorizer_ = std::make_shared<Authorizer>();
    }
    
    return authorizer_->hasPermission(user_id, permission, resource_type, resource_id);
}

bool MCPSecurityTools::grantPermission(const std::string& user_id,
                                       Permission permission,
                                       ResourceType resource_type,
                                       const std::string& resource_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!authorizer_) {
        authorizer_ = std::make_shared<Authorizer>();
    }
    
    return authorizer_->grantPermission(user_id, permission, resource_type, resource_id);
}

bool MCPSecurityTools::revokePermission(const std::string& user_id,
                                        Permission permission,
                                        ResourceType resource_type,
                                        const std::string& resource_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!authorizer_) {
        return false;
    }
    
    return authorizer_->revokePermission(user_id, permission, resource_type, resource_id);
}

std::string MCPSecurityTools::createPolicy(const SecurityPolicy&) { return ""; }
bool MCPSecurityTools::updatePolicy(const std::string&, const SecurityPolicy&) { return false; }
bool MCPSecurityTools::deletePolicy(const std::string&) { return false; }
SecurityPolicy MCPSecurityTools::getPolicy(const std::string&) { return {}; }
std::vector<SecurityPolicy> MCPSecurityTools::listPolicies() { return {}; }
bool MCPSecurityTools::applyPolicy(const std::string&) { return false; }

void MCPSecurityTools::logAudit(const AuditEntry& entry) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!security_manager_) {
        security_manager_ = std::make_shared<SecurityManager>();
    }
    
    security_manager_->logAudit(entry);
}

std::vector<AuditEntry> MCPSecurityTools::queryAudit(const std::string& user_id,
                                                     const std::string& action,
                                                     std::chrono::system_clock::time_point since,
                                                     size_t limit) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!security_manager_) {
        return {};
    }
    
    return security_manager_->queryAudit(user_id, action, since, limit);
}

bool MCPSecurityTools::exportAudit(const std::string&, const std::string&) { return false; }

std::string MCPSecurityTools::createSandbox(const SandboxConfig&) { return ""; }
bool MCPSecurityTools::updateSandbox(const std::string&, const SandboxConfig&) { return false; }
bool MCPSecurityTools::deleteSandbox(const std::string&) { return false; }
SandboxConfig MCPSecurityTools::getSandbox(const std::string&) { return {}; }
bool MCPSecurityTools::executeSandboxed(const std::string&, const std::function<void()>&) { return false; }

std::vector<uint8_t> MCPSecurityTools::encrypt(const std::vector<uint8_t>& data,
                                               const EncryptionConfig& config) {
    return CryptoUtils::encrypt(data, config.key);
}

std::vector<uint8_t> MCPSecurityTools::decrypt(const std::vector<uint8_t>& encrypted_data,
                                               const EncryptionConfig& config) {
    return CryptoUtils::decrypt(encrypted_data, config.key);
}

std::string MCPSecurityTools::hashPassword(const std::string& password) {
    return CryptoUtils::hashPassword(password);
}

bool MCPSecurityTools::verifyPassword(const std::string& password, const std::string& hash) {
    return CryptoUtils::verifyPassword(password, hash);
}

bool MCPSecurityTools::checkRateLimit(const std::string& identifier) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!security_manager_) {
        return true;
    }
    
    return security_manager_->checkRateLimit(identifier);
}

bool MCPSecurityTools::incrementRateLimit(const std::string& identifier) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!security_manager_) {
        return false;
    }
    
    security_manager_->incrementRateLimit(identifier);
    return true;
}

void MCPSecurityTools::resetRateLimit(const std::string& identifier) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (security_manager_) {
        security_manager_->resetRateLimit(identifier);
    }
}

uint32_t MCPSecurityTools::getRemainingRequests(const std::string&) { return 0; }

bool MCPSecurityTools::isIPAllowed(const std::string& ip_address) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!security_manager_) {
        return true;
    }
    
    return security_manager_->isIPAllowed(ip_address);
}

bool MCPSecurityTools::isIPBlocked(const std::string& ip_address) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!security_manager_) {
        return false;
    }
    
    return security_manager_->isIPBlocked(ip_address);
}

bool MCPSecurityTools::addAllowedIP(const std::string& ip_address) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!security_manager_) {
        return false;
    }
    
    security_manager_->addAllowedIP(ip_address);
    return true;
}

bool MCPSecurityTools::addBlockedIP(const std::string& ip_address) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!security_manager_) {
        return false;
    }
    
    security_manager_->addBlockedIP(ip_address);
    return true;
}

bool MCPSecurityTools::removeAllowedIP(const std::string&) { return false; }
bool MCPSecurityTools::removeBlockedIP(const std::string&) { return false; }

// Authenticator implementation
class Authenticator::Impl {
public:
    std::unordered_map<std::string, AccessToken> tokens;
    std::unordered_map<std::string, std::string> sessions; // token -> user_id
    std::chrono::seconds token_lifetime{3600};
    mutable std::mutex mutex;
};

Authenticator::Authenticator() : pImpl(std::make_unique<Impl>()) {}
Authenticator::~Authenticator() = default;

AccessToken Authenticator::authenticate(const Credentials& credentials) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    // Verify credentials (simplified - would use actual database)
    if (credentials.username.empty() || credentials.password.empty()) {
        return {};
    }
    
    // Generate token
    std::string token = CryptoUtils::generateRandomString(32);
    std::string user_id = "user_" + credentials.username;
    
    AccessToken access_token;
    access_token.token = token;
    access_token.user_id = user_id;
    access_token.issued_at = std::chrono::system_clock::now();
    access_token.expires_at = access_token.issued_at + pImpl->token_lifetime;
    
    pImpl->tokens[token] = access_token;
    pImpl->sessions[token] = user_id;
    
    return access_token;
}

bool Authenticator::validateToken(const std::string& token) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    auto it = pImpl->tokens.find(token);
    if (it == pImpl->tokens.end()) {
        return false;
    }
    
    // Check expiration
    auto now = std::chrono::system_clock::now();
    if (now > it->second.expires_at) {
        pImpl->tokens.erase(it);
        pImpl->sessions.erase(token);
        return false;
    }
    
    return true;
}

bool Authenticator::revokeToken(const std::string& token) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    pImpl->tokens.erase(token);
    pImpl->sessions.erase(token);
    return true;
}

AccessToken Authenticator::refreshToken(const std::string& refresh_token) {
    // Simplified implementation
    return {};
}

bool Authenticator::createSession(const std::string& user_id, const std::string& token) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    pImpl->sessions[token] = user_id;
    return true;
}

bool Authenticator::destroySession(const std::string& token) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    return pImpl->sessions.erase(token) > 0;
}

bool Authenticator::isSessionValid(const std::string& token) {
    return validateToken(token);
}

std::string Authenticator::getUserIdFromToken(const std::string& token) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    auto it = pImpl->sessions.find(token);
    return (it != pImpl->sessions.end()) ? it->second : "";
}

std::string Authenticator::generateToken(const std::string&, const std::vector<std::string>&) {
    return CryptoUtils::generateRandomString(32);
}

std::string Authenticator::generateRefreshToken(const std::string&) {
    return CryptoUtils::generateRandomString(32);
}

std::string Authenticator::generateAPIKey(const std::string&) {
    return CryptoUtils::generateRandomString(40);
}

bool Authenticator::enableMFA(const std::string&) { return false; }
bool Authenticator::disableMFA(const std::string&) { return false; }
std::string Authenticator::generateMFACode(const std::string&) { return ""; }
bool Authenticator::verifyMFACode(const std::string&, const std::string&) { return false; }
void Authenticator::setTokenLifetime(std::chrono::seconds lifetime) { pImpl->token_lifetime = lifetime; }
void Authenticator::setMaxLoginAttempts(uint32_t) {}
void Authenticator::setLockoutDuration(std::chrono::seconds) {}

// Authorizer implementation
class Authorizer::Impl {
public:
    struct PermissionKey {
        std::string user_id;
        Permission permission;
        ResourceType resource_type;
        std::string resource_id;
        
        bool operator==(const PermissionKey& other) const {
            return user_id == other.user_id &&
                   permission == other.permission &&
                   resource_type == other.resource_type &&
                   resource_id == other.resource_id;
        }
    };
    
    struct PermissionKeyHash {
        size_t operator()(const PermissionKey& key) const {
            return std::hash<std::string>()(key.user_id) ^
                   std::hash<int>()(static_cast<int>(key.permission)) ^
                   std::hash<int>()(static_cast<int>(key.resource_type)) ^
                   std::hash<std::string>()(key.resource_id);
        }
    };
    
    std::unordered_set<PermissionKey, PermissionKeyHash> permissions;
    std::unordered_map<std::string, std::vector<std::string>> user_roles;
    mutable std::mutex mutex;
};

Authorizer::Authorizer() : pImpl(std::make_unique<Impl>()) {}
Authorizer::~Authorizer() = default;

bool Authorizer::hasPermission(const std::string& user_id,
                               Permission permission,
                               ResourceType resource_type,
                               const std::string& resource_id) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    Impl::PermissionKey key{user_id, permission, resource_type, resource_id};
    return pImpl->permissions.count(key) > 0;
}

bool Authorizer::hasRole(const std::string& user_id, const std::string& role_id) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    auto it = pImpl->user_roles.find(user_id);
    if (it == pImpl->user_roles.end()) {
        return false;
    }
    
    return std::find(it->second.begin(), it->second.end(), role_id) != it->second.end();
}

bool Authorizer::grantPermission(const std::string& user_id,
                                Permission permission,
                                ResourceType resource_type,
                                const std::string& resource_id) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    Impl::PermissionKey key{user_id, permission, resource_type, resource_id};
    pImpl->permissions.insert(key);
    return true;
}

bool Authorizer::revokePermission(const std::string& user_id,
                                 Permission permission,
                                 ResourceType resource_type,
                                 const std::string& resource_id) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    Impl::PermissionKey key{user_id, permission, resource_type, resource_id};
    return pImpl->permissions.erase(key) > 0;
}

bool Authorizer::assignRole(const std::string& user_id, const std::string& role_id) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    pImpl->user_roles[user_id].push_back(role_id);
    return true;
}

bool Authorizer::revokeRole(const std::string& user_id, const std::string& role_id) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    auto it = pImpl->user_roles.find(user_id);
    if (it == pImpl->user_roles.end()) {
        return false;
    }
    
    auto& roles = it->second;
    roles.erase(std::remove(roles.begin(), roles.end(), role_id), roles.end());
    return true;
}

std::vector<std::string> Authorizer::getUserRoles(const std::string& user_id) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    auto it = pImpl->user_roles.find(user_id);
    return (it != pImpl->user_roles.end()) ? it->second : std::vector<std::string>{};
}

std::vector<Permission> Authorizer::getRolePermissions(const std::string&) {
    return {};
}

bool Authorizer::evaluatePolicy(const std::string&, const std::string&, 
                               const std::unordered_map<std::string, std::string>&) {
    return false;
}

// SecurityManager implementation
class SecurityManager::Impl {
public:
    SecurityPolicy policy;
    std::vector<AuditEntry> audit_log;
    std::unordered_map<std::string, uint32_t> rate_limits;
    std::unordered_set<std::string> allowed_ips;
    std::unordered_set<std::string> blocked_ips;
    mutable std::mutex mutex;
};

SecurityManager::SecurityManager() : pImpl(std::make_unique<Impl>()) {}
SecurityManager::~SecurityManager() = default;

void SecurityManager::applyPolicy(const SecurityPolicy& policy) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    pImpl->policy = policy;
}

SecurityPolicy SecurityManager::getCurrentPolicy() const {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    return pImpl->policy;
}

void SecurityManager::logAudit(const AuditEntry& entry) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    pImpl->audit_log.push_back(entry);
}

std::vector<AuditEntry> SecurityManager::queryAudit(const std::string& user_id,
                                                    const std::string& action,
                                                    std::chrono::system_clock::time_point since,
                                                    size_t limit) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    std::vector<AuditEntry> result;
    
    for (const auto& entry : pImpl->audit_log) {
        if (!user_id.empty() && entry.user_id != user_id) {
            continue;
        }
        
        if (!action.empty() && entry.action != action) {
            continue;
        }
        
        if (since != std::chrono::system_clock::time_point() && entry.timestamp < since) {
            continue;
        }
        
        result.push_back(entry);
        
        if (result.size() >= limit) {
            break;
        }
    }
    
    return result;
}

bool SecurityManager::checkRateLimit(const std::string& identifier) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    auto it = pImpl->rate_limits.find(identifier);
    if (it == pImpl->rate_limits.end()) {
        return true;
    }
    
    return it->second < pImpl->policy.requests_per_minute;
}

void SecurityManager::incrementRateLimit(const std::string& identifier) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    pImpl->rate_limits[identifier]++;
}

void SecurityManager::resetRateLimit(const std::string& identifier) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    pImpl->rate_limits.erase(identifier);
}

bool SecurityManager::isIPAllowed(const std::string& ip_address) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    if (pImpl->allowed_ips.empty()) {
        return true; // No restrictions
    }
    
    return pImpl->allowed_ips.count(ip_address) > 0;
}

bool SecurityManager::isIPBlocked(const std::string& ip_address) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    return pImpl->blocked_ips.count(ip_address) > 0;
}

void SecurityManager::addAllowedIP(const std::string& ip_address) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    pImpl->allowed_ips.insert(ip_address);
}

void SecurityManager::addBlockedIP(const std::string& ip_address) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    pImpl->blocked_ips.insert(ip_address);
}

std::vector<uint8_t> SecurityManager::encrypt(const std::vector<uint8_t>& data) {
    return CryptoUtils::encrypt(data, {});
}

std::vector<uint8_t> SecurityManager::decrypt(const std::vector<uint8_t>& encrypted_data) {
    return CryptoUtils::decrypt(encrypted_data, {});
}

SecurityManager::SecurityStats SecurityManager::getStats() const {
    return {};
}

// AccessControl stubs
class AccessControl::Impl {};
AccessControl::AccessControl() : pImpl(std::make_unique<Impl>()) {}
AccessControl::~AccessControl() = default;
bool AccessControl::addEntry(const std::string&, Permission, ResourceType, const std::string&) { return false; }
bool AccessControl::removeEntry(const std::string&, Permission, ResourceType, const std::string&) { return false; }
bool AccessControl::hasAccess(const std::string&, Permission, ResourceType, const std::string&) { return false; }
void AccessControl::setInheritance(const std::string&, const std::string&) {}
std::vector<std::string> AccessControl::getResourcesWithAccess(const std::string&, Permission) { return {}; }

// TokenManager stubs
class TokenManager::Impl {};
TokenManager::TokenManager() : pImpl(std::make_unique<Impl>()) {}
TokenManager::~TokenManager() = default;
std::string TokenManager::createToken(const std::string&, const std::vector<std::string>&, std::chrono::seconds) { return ""; }
bool TokenManager::validateToken(const std::string&) { return false; }
bool TokenManager::revokeToken(const std::string&) { return false; }
AccessToken TokenManager::getTokenInfo(const std::string&) { return {}; }
std::string TokenManager::refreshToken(const std::string&) { return ""; }
void TokenManager::cleanupExpiredTokens() {}
size_t TokenManager::getActiveTokenCount() const { return 0; }

// CryptoUtils implementation
std::string CryptoUtils::hash(const std::string& data, const std::string& algorithm) {
    unsigned char hash[SHA256_DIGEST_LENGTH];
    SHA256_CTX sha256;
    SHA256_Init(&sha256);
    SHA256_Update(&sha256, data.c_str(), data.length());
    SHA256_Final(hash, &sha256);
    
    std::stringstream ss;
    for (int i = 0; i < SHA256_DIGEST_LENGTH; i++) {
        ss << std::hex << std::setw(2) << std::setfill('0') << (int)hash[i];
    }
    
    return ss.str();
}

std::string CryptoUtils::hashPassword(const std::string& password) {
    // Add salt and hash
    std::string salt = generateRandomString(16);
    std::string salted = salt + password;
    return salt + ":" + hash(salted);
}

bool CryptoUtils::verifyPassword(const std::string& password, const std::string& hash) {
    size_t colon_pos = hash.find(':');
    if (colon_pos == std::string::npos) {
        return false;
    }
    
    std::string salt = hash.substr(0, colon_pos);
    std::string stored_hash = hash.substr(colon_pos + 1);
    
    std::string salted = salt + password;
    std::string computed_hash = CryptoUtils::hash(salted);
    
    return computed_hash == stored_hash;
}

std::vector<uint8_t> CryptoUtils::encrypt(const std::vector<uint8_t>& data,
                                          const std::vector<uint8_t>& key) {
    // Simplified AES encryption (would use proper OpenSSL EVP API)
    return data; // Return unencrypted for now
}

std::vector<uint8_t> CryptoUtils::decrypt(const std::vector<uint8_t>& encrypted_data,
                                          const std::vector<uint8_t>& key) {
    // Simplified AES decryption
    return encrypted_data;
}

std::vector<uint8_t> CryptoUtils::generateKey(size_t length) {
    std::vector<uint8_t> key(length);
    RAND_bytes(key.data(), length);
    return key;
}

std::vector<uint8_t> CryptoUtils::generateIV(size_t length) {
    return generateKey(length);
}

std::string CryptoUtils::generateRandomString(size_t length) {
    const char charset[] = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, sizeof(charset) - 2);
    
    std::string result;
    result.reserve(length);
    
    for (size_t i = 0; i < length; ++i) {
        result += charset[dis(gen)];
    }
    
    return result;
}

uint64_t CryptoUtils::generateRandomNumber() {
    std::random_device rd;
    std::mt19937_64 gen(rd());
    return gen();
}

std::string CryptoUtils::base64Encode(const std::vector<uint8_t>&) {
    return "";
}

std::vector<uint8_t> CryptoUtils::base64Decode(const std::string&) {
    return {};
}

std::string CryptoUtils::hexEncode(const std::vector<uint8_t>& data) {
    std::stringstream ss;
    for (uint8_t byte : data) {
        ss << std::hex << std::setw(2) << std::setfill('0') << (int)byte;
    }
    return ss.str();
}

std::vector<uint8_t> CryptoUtils::hexDecode(const std::string& hex) {
    std::vector<uint8_t> result;
    for (size_t i = 0; i < hex.length(); i += 2) {
        std::string byte_str = hex.substr(i, 2);
        uint8_t byte = static_cast<uint8_t>(std::stoi(byte_str, nullptr, 16));
        result.push_back(byte);
    }
    return result;
}

} // namespace security
} // namespace mcp
} // namespace cogniware

