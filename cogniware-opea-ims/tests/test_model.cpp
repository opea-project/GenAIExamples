#include <gtest/gtest.h>
#include "engine.h"
#include <string>
#include <fstream>
#include <filesystem>

class ModelTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Create test model directory
        std::filesystem::create_directories("models");
        
        // Create a test model file
        std::ofstream model_file("models/test-model.bin", std::ios::binary);
        std::vector<float> weights = {1.0f, 2.0f, 3.0f, 4.0f};
        model_file.write(reinterpret_cast<const char*>(weights.data()), 
                        weights.size() * sizeof(float));
    }

    void TearDown() override {
        // Clean up test model file
        std::filesystem::remove("models/test-model.bin");
        std::filesystem::remove("models");
    }
};

TEST_F(ModelTest, ModelInitialization) {
    // Test model initialization
    cogniware::Model model("test-model", 0);
    EXPECT_NO_THROW(model.process("test prompt"));
}

TEST_F(ModelTest, ModelNotFound) {
    // Test handling of non-existent model
    EXPECT_THROW(cogniware::Model("non-existent-model", 0), 
                 std::runtime_error);
}

TEST_F(ModelTest, ProcessPrompt) {
    // Test prompt processing
    cogniware::Model model("test-model", 0);
    std::string response = model.process("test prompt");
    EXPECT_FALSE(response.empty());
}

TEST_F(ModelTest, MultipleDevices) {
    // Test model on different devices
    int num_devices;
    cudaGetDeviceCount(&num_devices);
    
    for (int i = 0; i < num_devices; ++i) {
        EXPECT_NO_THROW({
            cogniware::Model model("test-model", i);
            model.process("test prompt");
        });
    }
}

TEST_F(ModelTest, LargePrompt) {
    // Test handling of large prompts
    cogniware::Model model("test-model", 0);
    std::string large_prompt(10000, 'a');
    EXPECT_NO_THROW(model.process(large_prompt));
}

TEST_F(ModelTest, ConcurrentProcessing) {
    // Test concurrent processing on the same model
    cogniware::Model model("test-model", 0);
    std::vector<std::thread> threads;
    const int num_threads = 4;
    
    for (int i = 0; i < num_threads; ++i) {
        threads.emplace_back([&model, i]() {
            std::string prompt = "Thread " + std::to_string(i) + " prompt";
            EXPECT_NO_THROW(model.process(prompt));
        });
    }
    
    for (auto& thread : threads) {
        thread.join();
    }
}

TEST_F(ModelTest, ModelDestruction) {
    // Test proper cleanup on model destruction
    {
        cogniware::Model model("test-model", 0);
        model.process("test prompt");
    } // Model should be destroyed here
    
    // Verify we can create a new model after destruction
    EXPECT_NO_THROW({
        cogniware::Model model("test-model", 0);
        model.process("test prompt");
    });
}

TEST_F(ModelTest, InvalidModelFile) {
    // Test handling of corrupted model file
    std::ofstream corrupted_file("models/corrupted-model.bin", std::ios::binary);
    corrupted_file << "invalid data";
    corrupted_file.close();
    
    EXPECT_THROW(cogniware::Model("corrupted-model", 0), 
                 std::runtime_error);
    
    std::filesystem::remove("models/corrupted-model.bin");
} 