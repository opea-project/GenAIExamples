#include "security/security_manager.h"
#include <spdlog/spdlog.h>
#include <chrono>
#include <algorithm>
#include <sstream>
#include <iomanip>
#include <openssl/sha.h>

namespace cogniware {

SecurityManager::SecurityManager(const std::string& secret_key)
    : secret_key_(secret_key) {
    spdlog::info("SecurityManager initialized");
}

SecurityManager::TokenInfo SecurityManager::create_token(
    const std::string& user_id,
    const std::string& role,
    const std::chrono::seconds& expiry) {
    
    try {
        auto now = std::chrono::system_clock::now();
        auto expiry_time = now + expiry;
        
        // Create JWT token
        auto token = jwt::create()
            .set_issuer("cogniware")
            .set_type("JWS")
            .set_issued_at(now)
            .set_expires_at(expiry_time)
            .set_payload_claim("user_id", jwt::claim(user_id))
            .set_payload_claim("role", jwt::claim(role))
            .sign(jwt::algorithm::hs256{secret_key_});
        
        TokenInfo info{
            token,
            expiry_time,
            user_id,
            role
        };
        
        spdlog::info("Created token for user {} with role {}", user_id, role);
        return info;
    } catch (const std::exception& e) {
        spdlog::error("Failed to create token: {}", e.what());
        return TokenInfo{};
    }
}

bool SecurityManager::verify_token(const std::string& token) {
    try {
        auto decoded = jwt::decode(token);
        auto verifier = jwt::verify()
            .allow_algorithm(jwt::algorithm::hs256{secret_key_})
            .with_issuer("cogniware");
        
        verifier.verify(decoded);
        
        // Check if token is expired
        auto now = std::chrono::system_clock::now();
        auto exp = decoded.get_expires_at();
        if (now > exp) {
            spdlog::warn("Token expired");
            return false;
        }
        
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Token verification failed: {}", e.what());
        return false;
    }
}

bool SecurityManager::refresh_token(const std::string& token) {
    try {
        if (!verify_token(token)) {
            return false;
        }
        
        auto decoded = jwt::decode(token);
        auto user_id = decoded.get_payload_claim("user_id").as_string();
        auto role = decoded.get_payload_claim("role").as_string();
        
        // Create new token with extended expiry
        auto new_token = create_token(user_id, role);
        
        spdlog::info("Refreshed token for user {}", user_id);
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Failed to refresh token: {}", e.what());
        return false;
    }
}

bool SecurityManager::check_permission(
    const std::string& token,
    const std::string& resource,
    const std::string& action) {
    
    try {
        if (!verify_token(token)) {
            return false;
        }
        
        auto decoded = jwt::decode(token);
        auto role = decoded.get_payload_claim("role").as_string();
        
        // Check if permission exists
        auto key = resource + ":" + action;
        auto it = permissions_.find(key);
        if (it == permissions_.end()) {
            spdlog::warn("No permission defined for {}:{}", resource, action);
            return false;
        }
        
        // Check if role is allowed
        const auto& allowed_roles = it->second.allowed_roles;
        bool has_permission = std::find(allowed_roles.begin(), 
                                      allowed_roles.end(), 
                                      role) != allowed_roles.end();
        
        // Log security event
        SecurityEvent event{
            "permission_check",
            decoded.get_payload_claim("user_id").as_string(),
            resource,
            action,
            "", // IP address not available in this context
            std::chrono::system_clock::now(),
            has_permission
        };
        log_security_event(event);
        
        return has_permission;
    } catch (const std::exception& e) {
        spdlog::error("Permission check failed: {}", e.what());
        return false;
    }
}

void SecurityManager::add_permission(const Permission& permission) {
    try {
        auto key = permission.resource + ":" + permission.action;
        permissions_[key] = permission;
        spdlog::info("Added permission for {}:{}", 
                    permission.resource, permission.action);
    } catch (const std::exception& e) {
        spdlog::error("Failed to add permission: {}", e.what());
    }
}

void SecurityManager::remove_permission(
    const std::string& resource,
    const std::string& action) {
    
    try {
        auto key = resource + ":" + action;
        permissions_.erase(key);
        spdlog::info("Removed permission for {}:{}", resource, action);
    } catch (const std::exception& e) {
        spdlog::error("Failed to remove permission: {}", e.what());
    }
}

bool SecurityManager::check_access(
    const std::string& token,
    const std::string& resource,
    const std::string& ip_address) {
    
    try {
        if (!verify_token(token)) {
            return false;
        }
        
        auto decoded = jwt::decode(token);
        auto role = decoded.get_payload_claim("role").as_string();
        auto user_id = decoded.get_payload_claim("user_id").as_string();
        
        // Check if access policy exists
        auto it = access_policies_.find(resource);
        if (it == access_policies_.end()) {
            spdlog::warn("No access policy defined for {}", resource);
            return false;
        }
        
        const auto& policy = it->second;
        
        // Check role
        bool role_allowed = std::find(policy.allowed_roles.begin(),
                                    policy.allowed_roles.end(),
                                    role) != policy.allowed_roles.end();
        
        // Check IP
        bool ip_allowed = check_ip_whitelist(ip_address, policy.allowed_ips);
        
        // Check rate limit
        bool rate_allowed = check_rate_limit(user_id, resource);
        
        bool access_granted = role_allowed && ip_allowed && rate_allowed;
        
        // Log security event
        SecurityEvent event{
            "access_check",
            user_id,
            resource,
            "access",
            ip_address,
            std::chrono::system_clock::now(),
            access_granted
        };
        log_security_event(event);
        
        return access_granted;
    } catch (const std::exception& e) {
        spdlog::error("Access check failed: {}", e.what());
        return false;
    }
}

void SecurityManager::add_access_policy(const AccessPolicy& policy) {
    try {
        access_policies_[policy.resource] = policy;
        spdlog::info("Added access policy for {}", policy.resource);
    } catch (const std::exception& e) {
        spdlog::error("Failed to add access policy: {}", e.what());
    }
}

void SecurityManager::remove_access_policy(const std::string& resource) {
    try {
        access_policies_.erase(resource);
        spdlog::info("Removed access policy for {}", resource);
    } catch (const std::exception& e) {
        spdlog::error("Failed to remove access policy: {}", e.what());
    }
}

void SecurityManager::log_security_event(const SecurityEvent& event) {
    try {
        std::lock_guard<std::mutex> lock(security_mutex_);
        security_events_.push_back(event);
        
        // Rotate logs if needed
        if (security_events_.size() > 10000) {
            rotate_security_logs();
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to log security event: {}", e.what());
    }
}

std::vector<SecurityManager::SecurityEvent> SecurityManager::get_security_events(
    const std::chrono::system_clock::time_point& start_time,
    const std::chrono::system_clock::time_point& end_time) {
    
    std::vector<SecurityEvent> filtered_events;
    
    try {
        std::lock_guard<std::mutex> lock(security_mutex_);
        
        std::copy_if(security_events_.begin(),
                    security_events_.end(),
                    std::back_inserter(filtered_events),
                    [&](const SecurityEvent& event) {
                        return event.timestamp >= start_time && 
                               event.timestamp <= end_time;
                    });
    } catch (const std::exception& e) {
        spdlog::error("Failed to get security events: {}", e.what());
    }
    
    return filtered_events;
}

bool SecurityManager::check_rate_limit(
    const std::string& user_id,
    const std::string& resource) {
    
    try {
        auto it = rate_limits_.find(resource);
        if (it == rate_limits_.end()) {
            return true; // No rate limit defined
        }
        
        const auto& limit = it->second;
        auto now = std::chrono::system_clock::now();
        
        // Count requests in the time window
        int request_count = 0;
        for (const auto& event : security_events_) {
            if (event.user_id == user_id && 
                event.resource == resource &&
                event.timestamp >= now - limit.window) {
                request_count++;
            }
        }
        
        return request_count < limit.max_requests;
    } catch (const std::exception& e) {
        spdlog::error("Rate limit check failed: {}", e.what());
        return false;
    }
}

void SecurityManager::set_rate_limit(
    const std::string& resource,
    const RateLimit& limit) {
    
    try {
        rate_limits_[resource] = limit;
        spdlog::info("Set rate limit for {}: {} requests per {} seconds",
                    resource, limit.max_requests,
                    std::chrono::duration_cast<std::chrono::seconds>(
                        limit.window).count());
    } catch (const std::exception& e) {
        spdlog::error("Failed to set rate limit: {}", e.what());
    }
}

bool SecurityManager::validate_token_payload(const jwt::decoded_jwt& jwt) {
    try {
        // Check required claims
        if (!jwt.has_payload_claim("user_id") || 
            !jwt.has_payload_claim("role")) {
            return false;
        }
        
        // Validate role
        auto role = jwt.get_payload_claim("role").as_string();
        if (role != "admin" && role != "user") {
            return false;
        }
        
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Token payload validation failed: {}", e.what());
        return false;
    }
}

bool SecurityManager::check_ip_whitelist(
    const std::string& ip_address,
    const std::vector<std::string>& allowed_ips) {
    
    if (allowed_ips.empty()) {
        return true; // No IP restrictions
    }
    
    return std::find(allowed_ips.begin(), allowed_ips.end(), ip_address) != 
           allowed_ips.end();
}

void SecurityManager::cleanup_expired_tokens() {
    try {
        auto now = std::chrono::system_clock::now();
        
        // Remove expired tokens from security events
        security_events_.erase(
            std::remove_if(security_events_.begin(),
                          security_events_.end(),
                          [&](const SecurityEvent& event) {
                              return event.timestamp < now - std::chrono::hours(24);
                          }),
            security_events_.end()
        );
    } catch (const std::exception& e) {
        spdlog::error("Failed to cleanup expired tokens: {}", e.what());
    }
}

void SecurityManager::rotate_security_logs() {
    try {
        // Keep only the last 1000 events
        if (security_events_.size() > 1000) {
            security_events_.erase(
                security_events_.begin(),
                security_events_.begin() + (security_events_.size() - 1000)
            );
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to rotate security logs: {}", e.what());
    }
}

} // namespace cogniware 