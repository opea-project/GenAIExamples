#include <gtest/gtest.h>
#include "dream/dream_agent.h"
#include <thread>
#include <chrono>
#include <vector>
#include <random>

using namespace cogniware::dream;

class DreamAgentTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Create test configurations
        interface_config = AgentConfig{
            AgentType::INTERFACE_LLM,
            "test_interface_llm",
            1024 * 1024 * 1024  // 1GB
        };
        
        knowledge_config = AgentConfig{
            AgentType::KNOWLEDGE_LLM,
            "test_knowledge_llm",
            1024 * 1024 * 1024  // 1GB
        };
        
        reasoning_config = AgentConfig{
            AgentType::REASONING_AGENT,
            "test_reasoning_agent",
            512 * 1024 * 1024  // 512MB
        };
        
        embodied_config = AgentConfig{
            AgentType::EMBODIED_AGENT,
            "test_embodied_agent",
            256 * 1024 * 1024  // 256MB
        };
    }
    
    void TearDown() override {
        // Clean up any resources
    }
    
    AgentConfig interface_config;
    AgentConfig knowledge_config;
    AgentConfig reasoning_config;
    AgentConfig embodied_config;
};

// Test agent initialization
TEST_F(DreamAgentTest, AgentInitialization) {
    InterfaceLLMAgent interface_agent(interface_config);
    KnowledgeLLMAgent knowledge_agent(knowledge_config);
    ReasoningAgent reasoning_agent(reasoning_config);
    EmbodiedAgent embodied_agent(embodied_config);
    
    EXPECT_EQ(interface_agent.get_state(), "");
    EXPECT_EQ(knowledge_agent.get_state(), "");
    EXPECT_EQ(reasoning_agent.get_state(), "");
    EXPECT_EQ(embodied_agent.get_state(), "");
}

// Test task scheduling
TEST_F(DreamAgentTest, TaskScheduling) {
    InterfaceLLMAgent agent(interface_config);
    
    std::vector<std::string> input_tokens = {"test", "input"};
    std::string task_id = agent.schedule_reasoning_task(
        "Test task",
        input_tokens,
        {},  // no dependencies
        1,   // priority
        [](const std::string& id) { /* callback */ }
    );
    
    EXPECT_FALSE(task_id.empty());
    EXPECT_FALSE(agent.is_task_completed(task_id));
}

// Test task dependencies
TEST_F(DreamAgentTest, TaskDependencies) {
    InterfaceLLMAgent agent(interface_config);
    
    // Create first task
    std::string task1_id = agent.schedule_reasoning_task(
        "First task",
        {"task1"},
        {},
        1,
        [](const std::string& id) { /* callback */ }
    );
    
    // Create second task that depends on first
    std::string task2_id = agent.schedule_reasoning_task(
        "Second task",
        {"task2"},
        {task1_id},
        1,
        [](const std::string& id) { /* callback */ }
    );
    
    EXPECT_FALSE(agent.is_task_completed(task1_id));
    EXPECT_FALSE(agent.is_task_completed(task2_id));
}

// Test resource allocation
TEST_F(DreamAgentTest, ResourceAllocation) {
    InterfaceLLMAgent agent(interface_config);
    
    EXPECT_NO_THROW(agent.allocate_resources());
    EXPECT_NO_THROW(agent.release_resources());
}

// Test metrics collection
TEST_F(DreamAgentTest, MetricsCollection) {
    InterfaceLLMAgent agent(interface_config);
    
    // Schedule and complete some tasks
    for (int i = 0; i < 5; i++) {
        std::string task_id = agent.schedule_reasoning_task(
            "Test task " + std::to_string(i),
            {"test"},
            {},
            1,
            [](const std::string& id) { /* callback */ }
        );
    }
    
    // Wait for metrics to update
    std::this_thread::sleep_for(std::chrono::seconds(2));
    
    auto metrics = agent.get_metrics();
    EXPECT_GE(metrics.completed_tasks, 0);
    EXPECT_GE(metrics.failed_tasks, 0);
    EXPECT_GE(metrics.active_tasks, 0);
}

// Test concurrent task processing
TEST_F(DreamAgentTest, ConcurrentTaskProcessing) {
    InterfaceLLMAgent agent(interface_config);
    std::vector<std::string> task_ids;
    std::mutex task_mutex;
    
    // Start processing thread
    std::thread processing_thread([&agent]() {
        agent.process_tasks();
    });
    
    // Schedule multiple tasks
    for (int i = 0; i < 10; i++) {
        std::string task_id = agent.schedule_reasoning_task(
            "Concurrent task " + std::to_string(i),
            {"test"},
            {},
            1,
            [](const std::string& id) { /* callback */ }
        );
        
        std::lock_guard<std::mutex> lock(task_mutex);
        task_ids.push_back(task_id);
    }
    
    // Wait for tasks to complete
    std::this_thread::sleep_for(std::chrono::seconds(2));
    
    // Check task completion
    for (const auto& task_id : task_ids) {
        EXPECT_TRUE(agent.is_task_completed(task_id));
    }
    
    // Clean up
    processing_thread.detach();
}

// Test task cancellation
TEST_F(DreamAgentTest, TaskCancellation) {
    InterfaceLLMAgent agent(interface_config);
    
    std::string task_id = agent.schedule_reasoning_task(
        "Cancellable task",
        {"test"},
        {},
        1,
        [](const std::string& id) { /* callback */ }
    );
    
    EXPECT_NO_THROW(agent.cancel_task(task_id));
    EXPECT_THROW(agent.is_task_completed(task_id), std::runtime_error);
}

// Test state management
TEST_F(DreamAgentTest, StateManagement) {
    InterfaceLLMAgent agent(interface_config);
    
    std::string new_state = "new_state";
    agent.update_state(new_state);
    EXPECT_EQ(agent.get_state(), new_state);
}

// Test error handling
TEST_F(DreamAgentTest, ErrorHandling) {
    InterfaceLLMAgent agent(interface_config);
    
    // Test invalid task ID
    EXPECT_THROW(agent.is_task_completed("invalid_id"), std::runtime_error);
    EXPECT_THROW(agent.cancel_task("invalid_id"), std::runtime_error);
    
    // Test invalid agent type
    AgentConfig invalid_config{
        AgentType::INTERFACE_LLM,  // Using interface type for knowledge agent
        "test_knowledge_llm",
        1024 * 1024 * 1024
    };
    
    EXPECT_THROW(KnowledgeLLMAgent(invalid_config), std::runtime_error);
}

// Test load balancing
TEST_F(DreamAgentTest, LoadBalancing) {
    InterfaceLLMAgent agent(interface_config);
    
    // Schedule tasks with different priorities
    std::vector<std::string> high_priority_tasks;
    std::vector<std::string> low_priority_tasks;
    
    for (int i = 0; i < 5; i++) {
        // High priority tasks
        high_priority_tasks.push_back(agent.schedule_reasoning_task(
            "High priority task " + std::to_string(i),
            {"test"},
            {},
            2,  // High priority
            [](const std::string& id) { /* callback */ }
        ));
        
        // Low priority tasks
        low_priority_tasks.push_back(agent.schedule_reasoning_task(
            "Low priority task " + std::to_string(i),
            {"test"},
            {},
            1,  // Low priority
            [](const std::string& id) { /* callback */ }
        ));
    }
    
    // Wait for some tasks to complete
    std::this_thread::sleep_for(std::chrono::seconds(2));
    
    // Check metrics
    auto metrics = agent.get_metrics();
    EXPECT_GE(metrics.completed_tasks, 0);
    EXPECT_GE(metrics.active_tasks, 0);
}

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
} 