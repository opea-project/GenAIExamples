#include <gtest/gtest.h>
#include "llm_instance_manager.h"
#include "gpu_memory_manager.h"
#include <vector>
#include <string>
#include <thread>

class LLMInstanceManagerTest : public ::testing::Test {
protected:
    void SetUp() override {
        manager = &LLMInstanceManager::getInstance();
    }
    
    void TearDown() override {
        // Clean up any test instances
        auto instances = manager->getLoadedModelIds();
        for (const auto& model_id : instances) {
            manager->removeInstance(model_id);
        }
    }
    
    LLMInstanceManager* manager;
};

TEST_F(LLMInstanceManagerTest, SingletonInstance) {
    auto& instance1 = LLMInstanceManager::getInstance();
    auto& instance2 = LLMInstanceManager::getInstance();
    EXPECT_EQ(&instance1, &instance2);
}

TEST_F(LLMInstanceManagerTest, CreateAndRemoveInstance) {
    const std::string model_id = "test_model";
    const std::string model_path = "path/to/model.gguf";
    
    // Create instance
    auto instance = manager->createInstance(model_id, model_path, ModelFormat::GGUF);
    EXPECT_NE(instance, nullptr);
    
    // Verify instance exists
    auto retrieved_instance = manager->getInstance(model_id);
    EXPECT_EQ(retrieved_instance, instance);
    
    // Remove instance
    manager->removeInstance(model_id);
    
    // Verify instance is removed
    retrieved_instance = manager->getInstance(model_id);
    EXPECT_EQ(retrieved_instance, nullptr);
}

TEST_F(LLMInstanceManagerTest, GetTotalInstances) {
    EXPECT_EQ(manager->getTotalInstances(), 0);
    
    // Create multiple instances
    const std::vector<std::string> model_ids = {"model1", "model2", "model3"};
    for (const auto& model_id : model_ids) {
        manager->createInstance(model_id, "path/to/model.gguf", ModelFormat::GGUF);
    }
    
    EXPECT_EQ(manager->getTotalInstances(), model_ids.size());
    
    // Remove instances
    for (const auto& model_id : model_ids) {
        manager->removeInstance(model_id);
    }
    
    EXPECT_EQ(manager->getTotalInstances(), 0);
}

TEST_F(LLMInstanceManagerTest, GetLoadedModelIds) {
    // Create multiple instances
    const std::vector<std::string> model_ids = {"model1", "model2", "model3"};
    for (const auto& model_id : model_ids) {
        manager->createInstance(model_id, "path/to/model.gguf", ModelFormat::GGUF);
    }
    
    auto loaded_ids = manager->getLoadedModelIds();
    EXPECT_EQ(loaded_ids.size(), model_ids.size());
    
    // Verify all model IDs are present
    for (const auto& model_id : model_ids) {
        EXPECT_NE(std::find(loaded_ids.begin(), loaded_ids.end(), model_id), loaded_ids.end());
    }
}

TEST_F(LLMInstanceManagerTest, ConcurrentInstanceCreation) {
    const size_t num_threads = 4;
    const size_t instances_per_thread = 2;
    std::vector<std::thread> threads;
    
    for (size_t i = 0; i < num_threads; ++i) {
        threads.emplace_back([&, i]() {
            for (size_t j = 0; j < instances_per_thread; ++j) {
                std::string model_id = "model_" + std::to_string(i) + "_" + std::to_string(j);
                manager->createInstance(model_id, "path/to/model.gguf", ModelFormat::GGUF);
            }
        });
    }
    
    for (auto& thread : threads) {
        thread.join();
    }
    
    EXPECT_EQ(manager->getTotalInstances(), num_threads * instances_per_thread);
}

TEST_F(LLMInstanceManagerTest, InstanceGeneration) {
    const std::string model_id = "test_model";
    auto instance = manager->createInstance(model_id, "path/to/model.gguf", ModelFormat::GGUF);
    EXPECT_NE(instance, nullptr);
    
    // Test generation with a simple prompt
    const std::string prompt = "Hello, world!";
    const size_t max_tokens = 10;
    
    // Note: This test is limited since we can't actually load a model in the test environment
    // In a real test, we would verify the generated output
    EXPECT_NO_THROW({
        instance->generate(prompt, max_tokens);
    });
}

TEST_F(LLMInstanceManagerTest, InvalidModelPath) {
    const std::string model_id = "test_model";
    const std::string invalid_path = "nonexistent/path/to/model.gguf";
    
    // Attempt to create instance with invalid path
    auto instance = manager->createInstance(model_id, invalid_path, ModelFormat::GGUF);
    EXPECT_EQ(instance, nullptr);
}

TEST_F(LLMInstanceManagerTest, DuplicateModelId) {
    const std::string model_id = "test_model";
    const std::string model_path = "path/to/model.gguf";
    
    // Create first instance
    auto instance1 = manager->createInstance(model_id, model_path, ModelFormat::GGUF);
    EXPECT_NE(instance1, nullptr);
    
    // Attempt to create second instance with same ID
    auto instance2 = manager->createInstance(model_id, model_path, ModelFormat::GGUF);
    EXPECT_EQ(instance2, nullptr);
}

TEST_F(LLMInstanceManagerTest, RemoveNonexistentInstance) {
    const std::string model_id = "nonexistent_model";
    
    // Attempt to remove non-existent instance
    EXPECT_NO_THROW({
        manager->removeInstance(model_id);
    });
}

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
} 