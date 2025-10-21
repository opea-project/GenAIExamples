#include <gtest/gtest.h>
#include "dream/dream_manager.h"
#include <thread>
#include <chrono>
#include <vector>
#include <random>

namespace cogniware {
namespace test {

class DreamManagerTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Initialize DREAM manager with 2 GPUs
        dream::DreamManager::get_instance().initialize_resources(2);
    }
    
    void TearDown() override {
        dream::DreamManager::get_instance().release_resources();
    }
    
    // Helper function to generate random input tokens
    std::vector<int> generate_random_input(int length) {
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_int_distribution<> dis(0, 1000);
        
        std::vector<int> tokens(length);
        for (int i = 0; i < length; i++) {
            tokens[i] = dis(gen);
        }
        return tokens;
    }
};

TEST_F(DreamManagerTest, ResourceInitialization) {
    auto metrics = dream::DreamManager::get_instance().get_all_resource_metrics();
    EXPECT_EQ(metrics.size(), 2);
    
    for (const auto& metric : metrics) {
        EXPECT_GE(metric.total_memory, 0);
        EXPECT_GE(metric.free_memory, 0);
        EXPECT_GE(metric.memory_utilization, 0.0f);
        EXPECT_LE(metric.memory_utilization, 1.0f);
        EXPECT_GE(metric.compute_utilization, 0.0f);
        EXPECT_LE(metric.compute_utilization, 1.0f);
    }
}

TEST_F(DreamManagerTest, TaskScheduling) {
    auto& manager = dream::DreamManager::get_instance();
    
    // Schedule a task
    auto input = generate_random_input(10);
    std::string task_id = manager.schedule_task("test_model", input, 1);
    
    // Verify task metrics
    auto metrics = manager.get_task_metrics(task_id);
    EXPECT_EQ(metrics.model_name, "test_model");
    EXPECT_EQ(metrics.priority, 1);
    EXPECT_FALSE(metrics.completed);
    EXPECT_EQ(metrics.status, "scheduled");
    
    // Update task status
    manager.update_task_status(task_id, "processing");
    metrics = manager.get_task_metrics(task_id);
    EXPECT_EQ(metrics.status, "processing");
    
    // Complete task
    manager.update_task_status(task_id, "completed");
    metrics = manager.get_task_metrics(task_id);
    EXPECT_TRUE(metrics.completed);
    EXPECT_EQ(metrics.status, "completed");
}

TEST_F(DreamManagerTest, MemoryManagement) {
    auto& manager = dream::DreamManager::get_instance();
    
    // Schedule a task
    auto input = generate_random_input(10);
    std::string task_id = manager.schedule_task("test_model", input, 1);
    
    // Allocate memory
    const size_t memory_size = 1024 * 1024;  // 1MB
    void* ptr = manager.allocate_memory(memory_size, task_id);
    EXPECT_NE(ptr, nullptr);
    
    // Verify memory allocation
    auto metrics = manager.get_task_metrics(task_id);
    EXPECT_GE(metrics.memory_usage, memory_size);
    
    // Free memory
    manager.free_memory(ptr, task_id);
    
    // Complete task
    manager.update_task_status(task_id, "completed");
}

TEST_F(DreamManagerTest, ConcurrentTasks) {
    auto& manager = dream::DreamManager::get_instance();
    const int num_tasks = 10;
    std::vector<std::string> task_ids;
    
    // Schedule multiple tasks
    for (int i = 0; i < num_tasks; i++) {
        auto input = generate_random_input(10);
        task_ids.push_back(manager.schedule_task("test_model", input, i % 3));
    }
    
    // Verify all tasks are scheduled
    auto active_tasks = manager.get_active_tasks();
    EXPECT_EQ(active_tasks.size(), num_tasks);
    
    // Complete all tasks
    for (const auto& task_id : task_ids) {
        manager.update_task_status(task_id, "completed");
    }
    
    // Verify no active tasks remain
    active_tasks = manager.get_active_tasks();
    EXPECT_EQ(active_tasks.size(), 0);
}

TEST_F(DreamManagerTest, LoadBalancing) {
    auto& manager = dream::DreamManager::get_instance();
    
    // Schedule tasks on first device
    for (int i = 0; i < 5; i++) {
        auto input = generate_random_input(10);
        manager.schedule_task("test_model", input, 1);
    }
    
    // Trigger load balancing
    manager.balance_load();
    
    // Verify tasks are distributed
    auto metrics = manager.get_all_resource_metrics();
    EXPECT_LE(std::abs(metrics[0].compute_utilization - metrics[1].compute_utilization), 0.3f);
}

TEST_F(DreamManagerTest, TaskCancellation) {
    auto& manager = dream::DreamManager::get_instance();
    
    // Schedule a task
    auto input = generate_random_input(10);
    std::string task_id = manager.schedule_task("test_model", input, 1);
    
    // Allocate memory
    void* ptr = manager.allocate_memory(1024 * 1024, task_id);
    
    // Cancel task
    manager.cancel_task(task_id);
    
    // Verify task is removed
    EXPECT_THROW(manager.get_task_metrics(task_id), std::runtime_error);
    
    // Verify no active tasks
    auto active_tasks = manager.get_active_tasks();
    EXPECT_EQ(active_tasks.size(), 0);
}

TEST_F(DreamManagerTest, ResourceOptimization) {
    auto& manager = dream::DreamManager::get_instance();
    
    // Schedule multiple tasks
    for (int i = 0; i < 5; i++) {
        auto input = generate_random_input(10);
        manager.schedule_task("test_model", input, i % 3);
    }
    
    // Run optimization
    manager.optimize_resource_allocation();
    
    // Verify resource metrics are updated
    auto metrics = manager.get_all_resource_metrics();
    for (const auto& metric : metrics) {
        EXPECT_GE(metric.memory_utilization, 0.0f);
        EXPECT_LE(metric.memory_utilization, 1.0f);
        EXPECT_GE(metric.compute_utilization, 0.0f);
        EXPECT_LE(metric.compute_utilization, 1.0f);
    }
}

TEST_F(DreamManagerTest, PriorityManagement) {
    auto& manager = dream::DreamManager::get_instance();
    
    // Schedule tasks with different priorities
    auto input = generate_random_input(10);
    std::string task_id = manager.schedule_task("test_model", input, 1);
    
    // Update priority
    manager.set_task_priority(task_id, 2);
    
    // Verify priority update
    auto metrics = manager.get_task_metrics(task_id);
    EXPECT_EQ(metrics.priority, 2);
}

} // namespace test
} // namespace cogniware 