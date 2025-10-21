/**
 * @file test_cognidream_admin.cpp
 * @brief Tests for the CogniDream admin interface
 */

#include <gtest/gtest.h>
#include "admin/cognidream_admin.hpp"
#include <fstream>
#include <filesystem>
#include <thread>
#include <chrono>

namespace cogniware {
namespace test {

class CogniDreamAdminTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Create temporary config file
        config_path_ = std::filesystem::temp_directory_path() / "test_config.json";
        std::ofstream config_file(config_path_);
        config_file << R"({
            "config_path": ")" << config_path_.string() << R"(",
            "session_timeout_seconds": 300,
            "instance_manager_config": {
                "max_instances": 10,
                "default_device": 0
            }
        })";
        config_file.close();

        // Initialize admin
        admin_ = &CogniDreamAdmin::getInstance();
        ASSERT_TRUE(admin_->initialize(config_path_.string()));
    }

    void TearDown() override {
        // Shutdown admin
        admin_->shutdown();

        // Clean up temporary files
        std::filesystem::remove(config_path_);
    }

    std::filesystem::path config_path_;
    CogniDreamAdmin* admin_;
};

TEST_F(CogniDreamAdminTest, CreateSession) {
    std::string session_id = admin_->createSession("user1", "model1");
    ASSERT_FALSE(session_id.empty());

    auto session = admin_->getSessionInfo(session_id);
    ASSERT_EQ(session.user_id, "user1");
    ASSERT_EQ(session.model_id, "model1");
    ASSERT_EQ(session.requests_processed, 0);
    ASSERT_EQ(session.tokens_generated, 0);
}

TEST_F(CogniDreamAdminTest, EndSession) {
    std::string session_id = admin_->createSession("user1", "model1");
    ASSERT_TRUE(admin_->endSession(session_id));

    auto session = admin_->getSessionInfo(session_id);
    ASSERT_TRUE(session.session_id.empty());
}

TEST_F(CogniDreamAdminTest, GetActiveSessions) {
    std::string session1 = admin_->createSession("user1", "model1");
    std::string session2 = admin_->createSession("user2", "model2");

    auto sessions = admin_->getActiveSessions();
    ASSERT_EQ(sessions.size(), 2);

    bool found_session1 = false;
    bool found_session2 = false;
    for (const auto& session : sessions) {
        if (session.session_id == session1) {
            found_session1 = true;
        }
        if (session.session_id == session2) {
            found_session2 = true;
        }
    }
    ASSERT_TRUE(found_session1);
    ASSERT_TRUE(found_session2);
}

TEST_F(CogniDreamAdminTest, GetSystemMetrics) {
    auto metrics = admin_->getSystemMetrics();
    ASSERT_EQ(metrics.active_sessions, 0);
    ASSERT_EQ(metrics.total_requests, 0);
    ASSERT_EQ(metrics.total_tokens, 0);
    ASSERT_GT(metrics.total_vram_available, 0);
}

TEST_F(CogniDreamAdminTest, GetModelStats) {
    auto stats = admin_->getModelStats("model1");
    ASSERT_TRUE(stats.empty());

    // Update model config
    nlohmann::json config = {
        {"max_tokens", 100},
        {"temperature", 0.7},
        {"top_k", 50},
        {"top_p", 0.9}
    };
    ASSERT_TRUE(admin_->updateModelConfig("model1", config));

    stats = admin_->getModelStats("model1");
    ASSERT_FALSE(stats.empty());
}

TEST_F(CogniDreamAdminTest, GetUserStats) {
    auto stats = admin_->getUserStats("user1");
    ASSERT_TRUE(stats.empty());

    // Create and end session
    std::string session_id = admin_->createSession("user1", "model1");
    ASSERT_TRUE(admin_->endSession(session_id));

    stats = admin_->getUserStats("user1");
    ASSERT_FALSE(stats.empty());
    ASSERT_EQ(stats["total_sessions"], 1);
}

TEST_F(CogniDreamAdminTest, SessionTimeout) {
    // Create session
    std::string session_id = admin_->createSession("user1", "model1");
    ASSERT_FALSE(session_id.empty());

    // Wait for session to expire
    std::this_thread::sleep_for(std::chrono::seconds(1));

    // Force cleanup
    admin_->shutdown();
    admin_->initialize(config_path_.string());

    // Check if session is gone
    auto session = admin_->getSessionInfo(session_id);
    ASSERT_TRUE(session.session_id.empty());
}

TEST_F(CogniDreamAdminTest, MultipleSessions) {
    // Create multiple sessions for same user
    std::string session1 = admin_->createSession("user1", "model1");
    std::string session2 = admin_->createSession("user1", "model2");
    std::string session3 = admin_->createSession("user1", "model1");

    auto sessions = admin_->getActiveSessions();
    ASSERT_EQ(sessions.size(), 3);

    auto stats = admin_->getUserStats("user1");
    ASSERT_EQ(stats["total_sessions"], 3);

    // End all sessions
    ASSERT_TRUE(admin_->endSession(session1));
    ASSERT_TRUE(admin_->endSession(session2));
    ASSERT_TRUE(admin_->endSession(session3));

    sessions = admin_->getActiveSessions();
    ASSERT_EQ(sessions.size(), 0);
}

TEST_F(CogniDreamAdminTest, InvalidSession) {
    ASSERT_FALSE(admin_->endSession("invalid_session"));
    auto session = admin_->getSessionInfo("invalid_session");
    ASSERT_TRUE(session.session_id.empty());
}

TEST_F(CogniDreamAdminTest, ResourceMonitoring) {
    auto metrics1 = admin_->getSystemMetrics();
    std::this_thread::sleep_for(std::chrono::seconds(6));
    auto metrics2 = admin_->getSystemMetrics();

    // Metrics should be updated
    ASSERT_NE(metrics1.total_vram_used, metrics2.total_vram_used);
    ASSERT_NE(metrics1.gpu_utilization, metrics2.gpu_utilization);
    ASSERT_NE(metrics1.memory_utilization, metrics2.memory_utilization);
}

} // namespace test
} // namespace cogniware 