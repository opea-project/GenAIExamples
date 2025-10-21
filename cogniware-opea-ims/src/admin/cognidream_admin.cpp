/**
 * @file cognidream_admin.cpp
 * @brief Implementation of the CogniDream admin interface
 */

#include "admin/cognidream_admin.hpp"
#include <fstream>
#include <chrono>
#include <random>
#include <sstream>
#include <iomanip>
#include <spdlog/spdlog.h>
#include <jwt-cpp/jwt.h>

namespace cogniware {

CogniDreamAdmin& CogniDreamAdmin::getInstance() {
    static CogniDreamAdmin instance;
    return instance;
}

bool CogniDreamAdmin::initialize(const std::string& config_path) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (running_) {
        spdlog::warn("CogniDream admin already initialized");
        return true;
    }
    
    // Load configuration
    if (!loadConfig(config_path)) {
        spdlog::error("Failed to load configuration from {}", config_path);
        return false;
    }
    
    // Initialize instance manager
    instance_manager_ = std::make_shared<LLMInstanceManager>();
    if (!instance_manager_->initialize(config_["instance_manager_config"])) {
        spdlog::error("Failed to initialize instance manager");
        return false;
    }
    
    // Initialize resource monitor
    resource_monitor_ = std::make_shared<ResourceMonitor>();
    if (!resource_monitor_->initialize()) {
        spdlog::error("Failed to initialize resource monitor");
        return false;
    }
    
    // Start monitoring threads
    running_ = true;
    monitor_thread_ = std::thread(&CogniDreamAdmin::monitorSessions, this);
    metrics_thread_ = std::thread(&CogniDreamAdmin::updateMetrics, this);
    cleanup_thread_ = std::thread(&CogniDreamAdmin::cleanupExpiredSessions, this);
    
    spdlog::info("CogniDream admin initialized successfully");
    return true;
}

void CogniDreamAdmin::shutdown() {
    {
        std::lock_guard<std::mutex> lock(mutex_);
        
        if (!running_) {
            return;
        }
        
        running_ = false;
    }
    
    // Notify all threads
    monitor_cv_.notify_one();
    metrics_cv_.notify_one();
    cleanup_cv_.notify_one();
    
    // Wait for threads to finish
    if (monitor_thread_.joinable()) {
        monitor_thread_.join();
    }
    if (metrics_thread_.joinable()) {
        metrics_thread_.join();
    }
    if (cleanup_thread_.joinable()) {
        cleanup_thread_.join();
    }
    
    // Save configuration
    saveConfig();
    
    spdlog::info("CogniDream admin shut down");
}

std::string CogniDreamAdmin::createSession(const std::string& user_id, const std::string& model_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Generate session ID
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, 15);
    const char* hex = "0123456789abcdef";
    std::string session_id;
    for (int i = 0; i < 32; ++i) {
        session_id += hex[dis(gen)];
    }
    
    // Create session
    UserSession session{
        .session_id = session_id,
        .user_id = user_id,
        .model_id = model_id,
        .created_at = std::chrono::system_clock::now(),
        .last_active = std::chrono::system_clock::now(),
        .requests_processed = 0,
        .tokens_generated = 0
    };
    
    sessions_[session_id] = session;
    
    // Update user stats
    if (!user_stats_.contains(user_id)) {
        user_stats_[user_id] = {
            {"total_sessions", 0},
            {"total_requests", 0},
            {"total_tokens", 0},
            {"average_latency", 0.0}
        };
    }
    user_stats_[user_id]["total_sessions"] = user_stats_[user_id]["total_sessions"].get<int>() + 1;
    
    spdlog::info("Created session {} for user {} with model {}", session_id, user_id, model_id);
    return session_id;
}

bool CogniDreamAdmin::endSession(const std::string& session_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = sessions_.find(session_id);
    if (it == sessions_.end()) {
        spdlog::warn("Session {} not found", session_id);
        return false;
    }
    
    // Update user stats
    const auto& session = it->second;
    auto& user_stats = user_stats_[session.user_id];
    user_stats["total_requests"] = user_stats["total_requests"].get<int>() + session.requests_processed;
    user_stats["total_tokens"] = user_stats["total_tokens"].get<int>() + session.tokens_generated;
    
    // Remove session
    sessions_.erase(it);
    
    spdlog::info("Ended session {}", session_id);
    return true;
}

UserSession CogniDreamAdmin::getSessionInfo(const std::string& session_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = sessions_.find(session_id);
    if (it == sessions_.end()) {
        return UserSession{};
    }
    
    return it->second;
}

std::vector<UserSession> CogniDreamAdmin::getActiveSessions() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    std::vector<UserSession> active_sessions;
    active_sessions.reserve(sessions_.size());
    
    for (const auto& [session_id, session] : sessions_) {
        active_sessions.push_back(session);
    }
    
    return active_sessions;
}

SystemMetrics CogniDreamAdmin::getSystemMetrics() {
    std::lock_guard<std::mutex> lock(mutex_);
    return current_metrics_;
}

nlohmann::json CogniDreamAdmin::getModelStats(const std::string& model_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = model_stats_.find(model_id);
    if (it == model_stats_.end()) {
        return nlohmann::json::object();
    }
    
    return it->second;
}

std::unordered_map<std::string, nlohmann::json> CogniDreamAdmin::getAllModelStats() {
    std::lock_guard<std::mutex> lock(mutex_);
    return model_stats_;
}

bool CogniDreamAdmin::updateModelConfig(const std::string& model_id, const nlohmann::json& config) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!instance_manager_->updateModelConfig(model_id, config)) {
        spdlog::error("Failed to update model config for {}", model_id);
        return false;
    }
    
    spdlog::info("Updated model config for {}", model_id);
    return true;
}

nlohmann::json CogniDreamAdmin::getUserStats(const std::string& user_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = user_stats_.find(user_id);
    if (it == user_stats_.end()) {
        return nlohmann::json::object();
    }
    
    return it->second;
}

std::unordered_map<std::string, nlohmann::json> CogniDreamAdmin::getAllUserStats() {
    std::lock_guard<std::mutex> lock(mutex_);
    return user_stats_;
}

bool CogniDreamAdmin::loadConfig(const std::string& config_path) {
    try {
        std::ifstream file(config_path);
        if (!file.is_open()) {
            spdlog::error("Failed to open config file: {}", config_path);
            return false;
        }
        
        file >> config_;
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Failed to load config: {}", e.what());
        return false;
    }
}

bool CogniDreamAdmin::saveConfig() {
    try {
        std::ofstream file(config_["config_path"]);
        if (!file.is_open()) {
            spdlog::error("Failed to open config file for writing");
            return false;
        }
        
        file << std::setw(4) << config_;
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Failed to save config: {}", e.what());
        return false;
    }
}

void CogniDreamAdmin::monitorSessions() {
    while (running_) {
        std::unique_lock<std::mutex> lock(mutex_);
        
        // Wait for notification or timeout
        monitor_cv_.wait_for(lock, std::chrono::seconds(1), [this] {
            return !running_;
        });
        
        if (!running_) {
            break;
        }
        
        // Update session last active times
        auto now = std::chrono::system_clock::now();
        for (auto& [session_id, session] : sessions_) {
            session.last_active = now;
        }
    }
}

void CogniDreamAdmin::updateMetrics() {
    while (running_) {
        std::unique_lock<std::mutex> lock(mutex_);
        
        // Wait for notification or timeout
        metrics_cv_.wait_for(lock, std::chrono::seconds(5), [this] {
            return !running_;
        });
        
        if (!running_) {
            break;
        }
        
        // Update system metrics
        current_metrics_.active_sessions = sessions_.size();
        current_metrics_.total_requests = 0;
        current_metrics_.total_tokens = 0;
        
        for (const auto& [session_id, session] : sessions_) {
            current_metrics_.total_requests += session.requests_processed;
            current_metrics_.total_tokens += session.tokens_generated;
        }
        
        // Update resource metrics
        auto device_stats = resource_monitor_->getAllDeviceStats();
        current_metrics_.total_vram_used = 0;
        current_metrics_.total_vram_available = 0;
        current_metrics_.gpu_utilization.clear();
        current_metrics_.memory_utilization.clear();
        
        for (const auto& [device_id, stats] : device_stats) {
            current_metrics_.total_vram_used += stats.vram_used;
            current_metrics_.total_vram_available += stats.vram_total;
            current_metrics_.gpu_utilization.push_back(stats.gpu_utilization);
            current_metrics_.memory_utilization.push_back(stats.memory_utilization);
        }
    }
}

void CogniDreamAdmin::cleanupExpiredSessions() {
    while (running_) {
        std::unique_lock<std::mutex> lock(mutex_);
        
        // Wait for notification or timeout
        cleanup_cv_.wait_for(lock, std::chrono::seconds(60), [this] {
            return !running_;
        });
        
        if (!running_) {
            break;
        }
        
        // Remove expired sessions
        auto now = std::chrono::system_clock::now();
        auto timeout = std::chrono::seconds(config_["session_timeout_seconds"].get<int>());
        
        for (auto it = sessions_.begin(); it != sessions_.end();) {
            if (now - it->second.last_active > timeout) {
                spdlog::info("Session {} expired", it->second.session_id);
                it = sessions_.erase(it);
            } else {
                ++it;
            }
        }
    }
}

} // namespace cogniware 