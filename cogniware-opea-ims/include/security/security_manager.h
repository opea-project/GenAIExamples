#pragma once

#include <string>
#include <vector>
#include <map>
#include <memory>
#include <chrono>
#include <mutex>
#include <jwt-cpp/jwt.h>

namespace cogniware {

class SecurityManager {
public:
    SecurityManager(const std::string& secret_key);
    
    // Authentication
    struct TokenInfo {
        std::string token;
        std::chrono::system_clock::time_point expiry;
        std::string user_id;
        std::string role;
    };
    
    TokenInfo create_token(const std::string& user_id, 
                         const std::string& role,
                         const std::chrono::seconds& expiry = std::chrono::hours(1));
    bool verify_token(const std::string& token);
    bool refresh_token(const std::string& token);
    
    // Authorization
    struct Permission {
        std::string resource;
        std::string action;
        std::vector<std::string> allowed_roles;
    };
    
    bool check_permission(const std::string& token,
                         const std::string& resource,
                         const std::string& action);
    void add_permission(const Permission& permission);
    void remove_permission(const std::string& resource, const std::string& action);
    
    // Access Control
    struct AccessPolicy {
        std::string resource;
        std::vector<std::string> allowed_roles;
        std::vector<std::string> allowed_ips;
        std::vector<std::string> allowed_origins;
    };
    
    bool check_access(const std::string& token,
                     const std::string& resource,
                     const std::string& ip_address);
    void add_access_policy(const AccessPolicy& policy);
    void remove_access_policy(const std::string& resource);
    
    // Security Monitoring
    struct SecurityEvent {
        std::string event_type;
        std::string user_id;
        std::string resource;
        std::string action;
        std::string ip_address;
        std::chrono::system_clock::time_point timestamp;
        bool success;
    };
    
    void log_security_event(const SecurityEvent& event);
    std::vector<SecurityEvent> get_security_events(
        const std::chrono::system_clock::time_point& start_time,
        const std::chrono::system_clock::time_point& end_time);
    
    // Rate Limiting
    struct RateLimit {
        int max_requests;
        std::chrono::seconds window;
    };
    
    bool check_rate_limit(const std::string& user_id,
                         const std::string& resource);
    void set_rate_limit(const std::string& resource, const RateLimit& limit);

private:
    std::string secret_key_;
    std::mutex security_mutex_;
    
    std::map<std::string, Permission> permissions_;
    std::map<std::string, AccessPolicy> access_policies_;
    std::map<std::string, RateLimit> rate_limits_;
    std::vector<SecurityEvent> security_events_;
    
    // Internal methods
    bool validate_token_payload(const jwt::decoded_jwt& jwt);
    bool check_ip_whitelist(const std::string& ip_address, 
                           const std::vector<std::string>& allowed_ips);
    void cleanup_expired_tokens();
    void rotate_security_logs();
};
} 