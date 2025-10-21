/**
 * @file test_cognidream_admin_api.cpp
 * @brief Tests for CogniDream admin REST API
 */

#include <gtest/gtest.h>
#include <fstream>
#include <filesystem>
#include <thread>
#include <chrono>
#include "admin/cognidream_admin_api.hpp"

namespace cogniware {
namespace test {

class CogniDreamAdminAPITest : public ::testing::Test {
protected:
    void SetUp() override {
        // Create temporary config file
        config_path_ = std::filesystem::temp_directory_path() / "cognidream_admin_api_test_config.json";
        std::ofstream config_file(config_path_);
        config_file << R"({
            "config_path": ")" << config_path_.string() << R"(",
            "session_timeout": 3600,
            "metrics_update_interval": 60,
            "cleanup_interval": 300
        })";
        config_file.close();

        // Initialize API
        ASSERT_TRUE(CogniDreamAdminAPI::getInstance().initialize(config_path_.string()));
    }

    void TearDown() override {
        // Shutdown API
        CogniDreamAdminAPI::getInstance().shutdown();

        // Remove temporary config file
        std::filesystem::remove(config_path_);
    }

    std::filesystem::path config_path_;
};

TEST_F(CogniDreamAdminAPITest, StartStop) {
    // Start API server
    ASSERT_TRUE(CogniDreamAdminAPI::getInstance().start(8080));

    // Stop API server
    CogniDreamAdminAPI::getInstance().stop();
}

TEST_F(CogniDreamAdminAPITest, CreateSession) {
    ASSERT_TRUE(CogniDreamAdminAPI::getInstance().start(8080));

    // Create session
    auto response = CogniDreamAdminAPI::getInstance().handleCreateSession(
        crow::request("POST", "/api/v1/sessions", R"({"user_id": "test_user", "model_id": "test_model"})")
    );

    ASSERT_EQ(response.code, 200);
    auto body = nlohmann::json::parse(response.body);
    ASSERT_TRUE(body.contains("session_id"));
    ASSERT_EQ(body["user_id"], "test_user");
    ASSERT_EQ(body["model_id"], "test_model");

    CogniDreamAdminAPI::getInstance().stop();
}

TEST_F(CogniDreamAdminAPITest, EndSession) {
    ASSERT_TRUE(CogniDreamAdminAPI::getInstance().start(8080));

    // Create session
    auto create_response = CogniDreamAdminAPI::getInstance().handleCreateSession(
        crow::request("POST", "/api/v1/sessions", R"({"user_id": "test_user", "model_id": "test_model"})")
    );
    auto session_id = nlohmann::json::parse(create_response.body)["session_id"];

    // End session
    auto response = CogniDreamAdminAPI::getInstance().handleEndSession(
        crow::request("DELETE", "/api/v1/sessions/" + session_id.get<std::string>())
    );

    ASSERT_EQ(response.code, 200);

    CogniDreamAdminAPI::getInstance().stop();
}

TEST_F(CogniDreamAdminAPITest, GetSessionInfo) {
    ASSERT_TRUE(CogniDreamAdminAPI::getInstance().start(8080));

    // Create session
    auto create_response = CogniDreamAdminAPI::getInstance().handleCreateSession(
        crow::request("POST", "/api/v1/sessions", R"({"user_id": "test_user", "model_id": "test_model"})")
    );
    auto session_id = nlohmann::json::parse(create_response.body)["session_id"];

    // Get session info
    auto response = CogniDreamAdminAPI::getInstance().handleGetSessionInfo(
        crow::request("GET", "/api/v1/sessions/" + session_id.get<std::string>())
    );

    ASSERT_EQ(response.code, 200);
    auto body = nlohmann::json::parse(response.body);
    ASSERT_EQ(body["session_id"], session_id);
    ASSERT_EQ(body["user_id"], "test_user");
    ASSERT_EQ(body["model_id"], "test_model");

    CogniDreamAdminAPI::getInstance().stop();
}

TEST_F(CogniDreamAdminAPITest, GetActiveSessions) {
    ASSERT_TRUE(CogniDreamAdminAPI::getInstance().start(8080));

    // Create multiple sessions
    for (int i = 0; i < 3; ++i) {
        auto response = CogniDreamAdminAPI::getInstance().handleCreateSession(
            crow::request("POST", "/api/v1/sessions", 
                R"({"user_id": "test_user")" + std::to_string(i) + R"(, "model_id": "test_model"})")
        );
        ASSERT_EQ(response.code, 200);
    }

    // Get active sessions
    auto response = CogniDreamAdminAPI::getInstance().handleGetActiveSessions(
        crow::request("GET", "/api/v1/sessions")
    );

    ASSERT_EQ(response.code, 200);
    auto sessions = nlohmann::json::parse(response.body);
    ASSERT_EQ(sessions.size(), 3);

    CogniDreamAdminAPI::getInstance().stop();
}

TEST_F(CogniDreamAdminAPITest, GetSystemMetrics) {
    ASSERT_TRUE(CogniDreamAdminAPI::getInstance().start(8080));

    // Get system metrics
    auto response = CogniDreamAdminAPI::getInstance().handleGetSystemMetrics(
        crow::request("GET", "/api/v1/metrics")
    );

    ASSERT_EQ(response.code, 200);
    auto metrics = nlohmann::json::parse(response.body);
    ASSERT_TRUE(metrics.contains("total_requests"));
    ASSERT_TRUE(metrics.contains("total_tokens"));
    ASSERT_TRUE(metrics.contains("active_sessions"));
    ASSERT_TRUE(metrics.contains("vram_usage"));
    ASSERT_TRUE(metrics.contains("avg_latency"));
    ASSERT_TRUE(metrics.contains("gpu_utilization"));
    ASSERT_TRUE(metrics.contains("memory_utilization"));

    CogniDreamAdminAPI::getInstance().stop();
}

TEST_F(CogniDreamAdminAPITest, GetModelStats) {
    ASSERT_TRUE(CogniDreamAdminAPI::getInstance().start(8080));

    // Create session with model
    auto create_response = CogniDreamAdminAPI::getInstance().handleCreateSession(
        crow::request("POST", "/api/v1/sessions", R"({"user_id": "test_user", "model_id": "test_model"})")
    );

    // Get model stats
    auto response = CogniDreamAdminAPI::getInstance().handleGetModelStats(
        crow::request("GET", "/api/v1/models/test_model/stats")
    );

    ASSERT_EQ(response.code, 200);
    auto stats = nlohmann::json::parse(response.body);
    ASSERT_EQ(stats["model_id"], "test_model");
    ASSERT_TRUE(stats.contains("requests_processed"));
    ASSERT_TRUE(stats.contains("tokens_generated"));
    ASSERT_TRUE(stats.contains("avg_latency"));
    ASSERT_TRUE(stats.contains("vram_usage"));
    ASSERT_TRUE(stats.contains("gpu_utilization"));
    ASSERT_TRUE(stats.contains("memory_utilization"));

    CogniDreamAdminAPI::getInstance().stop();
}

TEST_F(CogniDreamAdminAPITest, UpdateModelConfig) {
    ASSERT_TRUE(CogniDreamAdminAPI::getInstance().start(8080));

    // Create session with model
    auto create_response = CogniDreamAdminAPI::getInstance().handleCreateSession(
        crow::request("POST", "/api/v1/sessions", R"({"user_id": "test_user", "model_id": "test_model"})")
    );

    // Update model config
    auto response = CogniDreamAdminAPI::getInstance().handleUpdateModelConfig(
        crow::request("PUT", "/api/v1/models/test_model/config", 
            R"({"max_tokens": 2048, "temperature": 0.7, "top_p": 0.9})")
    );

    ASSERT_EQ(response.code, 200);

    CogniDreamAdminAPI::getInstance().stop();
}

TEST_F(CogniDreamAdminAPITest, GetUserStats) {
    ASSERT_TRUE(CogniDreamAdminAPI::getInstance().start(8080));

    // Create session
    auto create_response = CogniDreamAdminAPI::getInstance().handleCreateSession(
        crow::request("POST", "/api/v1/sessions", R"({"user_id": "test_user", "model_id": "test_model"})")
    );

    // Get user stats
    auto response = CogniDreamAdminAPI::getInstance().handleGetUserStats(
        crow::request("GET", "/api/v1/users/test_user/stats")
    );

    ASSERT_EQ(response.code, 200);
    auto stats = nlohmann::json::parse(response.body);
    ASSERT_EQ(stats["user_id"], "test_user");
    ASSERT_TRUE(stats.contains("total_requests"));
    ASSERT_TRUE(stats.contains("total_tokens"));
    ASSERT_TRUE(stats.contains("active_sessions"));
    ASSERT_TRUE(stats.contains("avg_latency"));

    CogniDreamAdminAPI::getInstance().stop();
}

TEST_F(CogniDreamAdminAPITest, InvalidSession) {
    ASSERT_TRUE(CogniDreamAdminAPI::getInstance().start(8080));

    // Try to get info for non-existent session
    auto response = CogniDreamAdminAPI::getInstance().handleGetSessionInfo(
        crow::request("GET", "/api/v1/sessions/invalid_session")
    );

    ASSERT_EQ(response.code, 404);

    CogniDreamAdminAPI::getInstance().stop();
}

TEST_F(CogniDreamAdminAPITest, InvalidModel) {
    ASSERT_TRUE(CogniDreamAdminAPI::getInstance().start(8080));

    // Try to get stats for non-existent model
    auto response = CogniDreamAdminAPI::getInstance().handleGetModelStats(
        crow::request("GET", "/api/v1/models/invalid_model/stats")
    );

    ASSERT_EQ(response.code, 404);

    CogniDreamAdminAPI::getInstance().stop();
}

TEST_F(CogniDreamAdminAPITest, InvalidUser) {
    ASSERT_TRUE(CogniDreamAdminAPI::getInstance().start(8080));

    // Try to get stats for non-existent user
    auto response = CogniDreamAdminAPI::getInstance().handleGetUserStats(
        crow::request("GET", "/api/v1/users/invalid_user/stats")
    );

    ASSERT_EQ(response.code, 404);

    CogniDreamAdminAPI::getInstance().stop();
}

} // namespace test
} // namespace cogniware 