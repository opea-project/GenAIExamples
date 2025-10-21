#pragma once

#include "mcp_core.h"
#include <string>
#include <vector>
#include <memory>
#include <unordered_map>
#include <unordered_set>
#include <chrono>
#include <functional>

namespace cogniware {
namespace mcp {
namespace security {

// Forward declarations
class Authenticator;
class Authorizer;
class SecurityManager;
class AccessControl;
class TokenManager;

/**
 * @brief Authentication methods
 */
enum class AuthMethod {
    NONE,
    API_KEY,
    OAUTH2,
    JWT,
    BASIC_AUTH,
    CERTIFICATE,
    BIOMETRIC,
    MULTI_FACTOR
};

/**
 * @brief Permission types
 */
enum class Permission {
    READ,
    WRITE,
    EXECUTE,
    DELETE,
    ADMIN,
    CREATE,
    UPDATE,
    LIST,
    MANAGE
};

/**
 * @brief Resource types
 */
enum class ResourceType {
    FILE,
    DIRECTORY,
    PROCESS,
    SERVICE,
    NETWORK,
    DATABASE,
    MODEL,
    API,
    SYSTEM,
    CUSTOM
};

/**
 * @brief Security level
 */
enum class SecurityLevel {
    PUBLIC,
    RESTRICTED,
    CONFIDENTIAL,
    SECRET,
    TOP_SECRET
};

/**
 * @brief User credentials
 */
struct Credentials {
    std::string username;
    std::string password;
    std::string api_key;
    std::string token;
    std::unordered_map<std::string, std::string> metadata;
};

/**
 * @brief User information
 */
struct User {
    std::string user_id;
    std::string username;
    std::string email;
    std::vector<std::string> roles;
    std::unordered_map<std::string, std::string> attributes;
    bool enabled = true;
    std::chrono::system_clock::time_point created_at;
    std::chrono::system_clock::time_point last_login;
};

/**
 * @brief Role definition
 */
struct Role {
    std::string role_id;
    std::string name;
    std::string description;
    std::vector<Permission> permissions;
    std::vector<std::string> allowed_resources;
    SecurityLevel security_level;
};

/**
 * @brief Access token
 */
struct AccessToken {
    std::string token;
    std::string user_id;
    std::chrono::system_clock::time_point issued_at;
    std::chrono::system_clock::time_point expires_at;
    std::vector<std::string> scopes;
    std::unordered_map<std::string, std::string> claims;
};

/**
 * @brief Security policy
 */
struct SecurityPolicy {
    std::string policy_id;
    std::string name;
    std::string description;
    bool enabled = true;
    
    // Authentication settings
    AuthMethod auth_method = AuthMethod::API_KEY;
    bool require_mfa = false;
    std::chrono::seconds token_lifetime = std::chrono::hours(24);
    uint32_t max_login_attempts = 5;
    std::chrono::seconds lockout_duration = std::chrono::minutes(30);
    
    // Authorization settings
    bool enforce_rbac = true;
    bool enforce_abac = false;
    SecurityLevel min_security_level = SecurityLevel::RESTRICTED;
    
    // Network security
    std::vector<std::string> allowed_ip_addresses;
    std::vector<std::string> blocked_ip_addresses;
    bool require_tls = true;
    
    // Rate limiting
    bool enable_rate_limiting = true;
    uint32_t requests_per_minute = 60;
    uint32_t requests_per_hour = 3600;
    
    // Audit settings
    bool enable_audit_logging = true;
    bool log_all_access = false;
    bool log_failed_access = true;
};

/**
 * @brief Security audit entry
 */
struct AuditEntry {
    std::string entry_id;
    std::chrono::system_clock::time_point timestamp;
    std::string user_id;
    std::string action;
    ResourceType resource_type;
    std::string resource_id;
    bool success;
    std::string ip_address;
    std::string user_agent;
    std::unordered_map<std::string, std::string> metadata;
};

/**
 * @brief Sandbox configuration
 */
struct SandboxConfig {
    std::string sandbox_id;
    bool enabled = true;
    
    // File system restrictions
    std::vector<std::string> allowed_read_paths;
    std::vector<std::string> allowed_write_paths;
    std::vector<std::string> blocked_paths;
    bool read_only_filesystem = false;
    
    // Network restrictions
    bool allow_network = false;
    std::vector<std::string> allowed_domains;
    std::vector<uint16_t> allowed_ports;
    
    // Process restrictions
    bool allow_process_spawn = false;
    uint32_t max_processes = 10;
    std::vector<std::string> allowed_executables;
    
    // Resource limits
    uint64_t max_memory_bytes = 1024 * 1024 * 1024; // 1GB
    uint64_t max_disk_bytes = 1024 * 1024 * 1024;   // 1GB
    uint32_t max_cpu_percent = 50;
    std::chrono::seconds max_execution_time = std::chrono::minutes(5);
    
    // System call filtering
    std::vector<std::string> allowed_syscalls;
    std::vector<std::string> blocked_syscalls;
};

/**
 * @brief Encryption configuration
 */
struct EncryptionConfig {
    enum class Algorithm {
        AES_128,
        AES_256,
        RSA_2048,
        RSA_4096,
        CHACHA20
    };
    
    Algorithm algorithm = Algorithm::AES_256;
    std::vector<uint8_t> key;
    std::vector<uint8_t> iv;
    bool enabled = true;
};

/**
 * @brief MCP Security Tools
 * 
 * Provides authentication, authorization, and security features
 * for the Model Context Protocol interface.
 */
class MCPSecurityTools {
public:
    MCPSecurityTools();
    ~MCPSecurityTools();

    /**
     * @brief Register all security tools with MCP server
     * @param server MCP server instance
     */
    static void registerAllTools(AdvancedMCPServer& server);

    // Authentication
    static AccessToken authenticate(const Credentials& credentials);
    static bool validateToken(const std::string& token);
    static bool revokeToken(const std::string& token);
    static AccessToken refreshToken(const std::string& refresh_token);
    static bool logout(const std::string& token);
    
    // User management
    static std::string createUser(const User& user, const std::string& password);
    static bool updateUser(const std::string& user_id, const User& user);
    static bool deleteUser(const std::string& user_id);
    static User getUser(const std::string& user_id);
    static std::vector<User> listUsers();
    static bool changePassword(const std::string& user_id, 
                              const std::string& old_password,
                              const std::string& new_password);
    
    // Role management
    static std::string createRole(const Role& role);
    static bool updateRole(const std::string& role_id, const Role& role);
    static bool deleteRole(const std::string& role_id);
    static Role getRole(const std::string& role_id);
    static std::vector<Role> listRoles();
    static bool assignRole(const std::string& user_id, const std::string& role_id);
    static bool revokeRole(const std::string& user_id, const std::string& role_id);
    
    // Authorization
    static bool checkPermission(const std::string& user_id, 
                               Permission permission,
                               ResourceType resource_type,
                               const std::string& resource_id);
    static bool grantPermission(const std::string& user_id,
                               Permission permission,
                               ResourceType resource_type,
                               const std::string& resource_id);
    static bool revokePermission(const std::string& user_id,
                                Permission permission,
                                ResourceType resource_type,
                                const std::string& resource_id);
    
    // Security policies
    static std::string createPolicy(const SecurityPolicy& policy);
    static bool updatePolicy(const std::string& policy_id, const SecurityPolicy& policy);
    static bool deletePolicy(const std::string& policy_id);
    static SecurityPolicy getPolicy(const std::string& policy_id);
    static std::vector<SecurityPolicy> listPolicies();
    static bool applyPolicy(const std::string& policy_id);
    
    // Audit logging
    static void logAudit(const AuditEntry& entry);
    static std::vector<AuditEntry> queryAudit(const std::string& user_id = "",
                                             const std::string& action = "",
                                             std::chrono::system_clock::time_point since = {},
                                             size_t limit = 100);
    static bool exportAudit(const std::string& filepath, const std::string& format = "json");
    
    // Sandboxing
    static std::string createSandbox(const SandboxConfig& config);
    static bool updateSandbox(const std::string& sandbox_id, const SandboxConfig& config);
    static bool deleteSandbox(const std::string& sandbox_id);
    static SandboxConfig getSandbox(const std::string& sandbox_id);
    static bool executeSandboxed(const std::string& sandbox_id, 
                                 const std::function<void()>& function);
    
    // Encryption
    static std::vector<uint8_t> encrypt(const std::vector<uint8_t>& data,
                                       const EncryptionConfig& config);
    static std::vector<uint8_t> decrypt(const std::vector<uint8_t>& encrypted_data,
                                       const EncryptionConfig& config);
    static std::string hashPassword(const std::string& password);
    static bool verifyPassword(const std::string& password, const std::string& hash);
    
    // Rate limiting
    static bool checkRateLimit(const std::string& identifier);
    static bool incrementRateLimit(const std::string& identifier);
    static void resetRateLimit(const std::string& identifier);
    static uint32_t getRemainingRequests(const std::string& identifier);
    
    // IP filtering
    static bool isIPAllowed(const std::string& ip_address);
    static bool isIPBlocked(const std::string& ip_address);
    static bool addAllowedIP(const std::string& ip_address);
    static bool addBlockedIP(const std::string& ip_address);
    static bool removeAllowedIP(const std::string& ip_address);
    static bool removeBlockedIP(const std::string& ip_address);
    
    // Helper functions
    static std::string permissionToString(Permission permission);
    static Permission stringToPermission(const std::string& permission);
    static std::string resourceTypeToString(ResourceType type);
    static ResourceType stringToResourceType(const std::string& type);

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
    
    static std::shared_ptr<Authenticator> authenticator_;
    static std::shared_ptr<Authorizer> authorizer_;
    static std::shared_ptr<SecurityManager> security_manager_;
    static std::mutex mutex_;
};

/**
 * @brief Authenticator
 */
class Authenticator {
public:
    Authenticator();
    ~Authenticator();

    // Authentication
    AccessToken authenticate(const Credentials& credentials);
    bool validateToken(const std::string& token);
    bool revokeToken(const std::string& token);
    AccessToken refreshToken(const std::string& refresh_token);
    
    // Session management
    bool createSession(const std::string& user_id, const std::string& token);
    bool destroySession(const std::string& token);
    bool isSessionValid(const std::string& token);
    std::string getUserIdFromToken(const std::string& token);
    
    // Token generation
    std::string generateToken(const std::string& user_id, 
                             const std::vector<std::string>& scopes);
    std::string generateRefreshToken(const std::string& user_id);
    std::string generateAPIKey(const std::string& user_id);
    
    // Multi-factor authentication
    bool enableMFA(const std::string& user_id);
    bool disableMFA(const std::string& user_id);
    std::string generateMFACode(const std::string& user_id);
    bool verifyMFACode(const std::string& user_id, const std::string& code);
    
    // Configuration
    void setTokenLifetime(std::chrono::seconds lifetime);
    void setMaxLoginAttempts(uint32_t attempts);
    void setLockoutDuration(std::chrono::seconds duration);

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

/**
 * @brief Authorizer
 */
class Authorizer {
public:
    Authorizer();
    ~Authorizer();

    // Permission checking
    bool hasPermission(const std::string& user_id,
                      Permission permission,
                      ResourceType resource_type,
                      const std::string& resource_id);
    
    bool hasRole(const std::string& user_id, const std::string& role_id);
    
    // Permission management
    bool grantPermission(const std::string& user_id,
                        Permission permission,
                        ResourceType resource_type,
                        const std::string& resource_id);
    
    bool revokePermission(const std::string& user_id,
                         Permission permission,
                         ResourceType resource_type,
                         const std::string& resource_id);
    
    // Role-based access control (RBAC)
    bool assignRole(const std::string& user_id, const std::string& role_id);
    bool revokeRole(const std::string& user_id, const std::string& role_id);
    std::vector<std::string> getUserRoles(const std::string& user_id);
    std::vector<Permission> getRolePermissions(const std::string& role_id);
    
    // Attribute-based access control (ABAC)
    bool evaluatePolicy(const std::string& user_id,
                       const std::string& action,
                       const std::unordered_map<std::string, std::string>& context);

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

/**
 * @brief Security manager
 */
class SecurityManager {
public:
    SecurityManager();
    ~SecurityManager();

    // Policy management
    void applyPolicy(const SecurityPolicy& policy);
    SecurityPolicy getCurrentPolicy() const;
    
    // Audit logging
    void logAudit(const AuditEntry& entry);
    std::vector<AuditEntry> queryAudit(const std::string& user_id = "",
                                      const std::string& action = "",
                                      std::chrono::system_clock::time_point since = {},
                                      size_t limit = 100);
    
    // Rate limiting
    bool checkRateLimit(const std::string& identifier);
    void incrementRateLimit(const std::string& identifier);
    void resetRateLimit(const std::string& identifier);
    
    // IP filtering
    bool isIPAllowed(const std::string& ip_address);
    bool isIPBlocked(const std::string& ip_address);
    void addAllowedIP(const std::string& ip_address);
    void addBlockedIP(const std::string& ip_address);
    
    // Encryption
    std::vector<uint8_t> encrypt(const std::vector<uint8_t>& data);
    std::vector<uint8_t> decrypt(const std::vector<uint8_t>& encrypted_data);
    
    // Statistics
    struct SecurityStats {
        uint64_t total_authentications;
        uint64_t failed_authentications;
        uint64_t active_sessions;
        uint64_t total_audit_entries;
        uint64_t blocked_requests;
        std::chrono::system_clock::time_point last_incident;
    };
    SecurityStats getStats() const;

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

/**
 * @brief Access control list (ACL)
 */
class AccessControl {
public:
    AccessControl();
    ~AccessControl();

    // ACL management
    bool addEntry(const std::string& principal,
                 Permission permission,
                 ResourceType resource_type,
                 const std::string& resource_id);
    
    bool removeEntry(const std::string& principal,
                    Permission permission,
                    ResourceType resource_type,
                    const std::string& resource_id);
    
    bool hasAccess(const std::string& principal,
                  Permission permission,
                  ResourceType resource_type,
                  const std::string& resource_id);
    
    // Inheritance
    void setInheritance(const std::string& child_resource,
                       const std::string& parent_resource);
    
    // Listing
    std::vector<std::string> getResourcesWithAccess(const std::string& principal,
                                                    Permission permission);

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

/**
 * @brief Token manager
 */
class TokenManager {
public:
    TokenManager();
    ~TokenManager();

    // Token operations
    std::string createToken(const std::string& user_id,
                           const std::vector<std::string>& scopes,
                           std::chrono::seconds lifetime);
    
    bool validateToken(const std::string& token);
    bool revokeToken(const std::string& token);
    AccessToken getTokenInfo(const std::string& token);
    
    // Token refresh
    std::string refreshToken(const std::string& refresh_token);
    
    // Token cleanup
    void cleanupExpiredTokens();
    size_t getActiveTokenCount() const;

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

/**
 * @brief Cryptography utilities
 */
class CryptoUtils {
public:
    // Hashing
    static std::string hash(const std::string& data, const std::string& algorithm = "SHA256");
    static std::string hashPassword(const std::string& password);
    static bool verifyPassword(const std::string& password, const std::string& hash);
    
    // Encryption
    static std::vector<uint8_t> encrypt(const std::vector<uint8_t>& data,
                                       const std::vector<uint8_t>& key);
    static std::vector<uint8_t> decrypt(const std::vector<uint8_t>& encrypted_data,
                                       const std::vector<uint8_t>& key);
    
    // Key generation
    static std::vector<uint8_t> generateKey(size_t length);
    static std::vector<uint8_t> generateIV(size_t length);
    
    // Random
    static std::string generateRandomString(size_t length);
    static uint64_t generateRandomNumber();
    
    // Encoding
    static std::string base64Encode(const std::vector<uint8_t>& data);
    static std::vector<uint8_t> base64Decode(const std::string& encoded);
    static std::string hexEncode(const std::vector<uint8_t>& data);
    static std::vector<uint8_t> hexDecode(const std::string& hex);
};

} // namespace security
} // namespace mcp
} // namespace cogniware

