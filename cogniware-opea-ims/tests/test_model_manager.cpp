#include <gtest/gtest.h>
#include "llm_inference_core/model/model_manager.h"

using namespace cogniware;

class ModelManagerTest : public ::testing::Test {
protected:
    void SetUp() override {
        manager = &ModelManager::getInstance();
    }

    void TearDown() override {
        // Cleanup any loaded models
        std::vector<std::string> modelIds;
        for (const auto& pair : manager->getModelConfigs()) {
            modelIds.push_back(pair.first);
        }
        for (const auto& modelId : modelIds) {
            manager->unloadModel(modelId);
        }
    }

    ModelManager* manager;
};

TEST_F(ModelManagerTest, ModelLoading) {
    ModelConfig config;
    config.modelId = "test-model";
    config.modelPath = "test_model.bin";
    config.modelType = "gpt";
    config.maxBatchSize = 32;
    config.maxSequenceLength = 1024;
    config.useHalfPrecision = true;
    config.useQuantization = false;
    config.supportedTasks = {"text-generation"};

    EXPECT_FALSE(manager->loadModel(config));  // Should fail because model file doesn't exist
}

TEST_F(ModelManagerTest, ModelUnloading) {
    // Try to unload non-existent model
    EXPECT_FALSE(manager->unloadModel("nonexistent-model"));
}

TEST_F(ModelManagerTest, ModelConfiguration) {
    ModelConfig config;
    config.modelId = "test-model";
    config.modelPath = "test_model.bin";
    config.modelType = "gpt";
    config.maxBatchSize = 32;
    config.maxSequenceLength = 1024;
    config.useHalfPrecision = true;
    config.useQuantization = false;
    config.supportedTasks = {"text-generation"};

    // Test invalid model ID
    config.modelId = "";
    EXPECT_FALSE(manager->loadModel(config));

    // Test invalid model path
    config.modelId = "test-model";
    config.modelPath = "";
    EXPECT_FALSE(manager->loadModel(config));

    // Test invalid model type
    config.modelPath = "test_model.bin";
    config.modelType = "";
    EXPECT_FALSE(manager->loadModel(config));

    // Test invalid batch size
    config.modelType = "gpt";
    config.maxBatchSize = 0;
    EXPECT_FALSE(manager->loadModel(config));

    // Test invalid sequence length
    config.maxBatchSize = 32;
    config.maxSequenceLength = 0;
    EXPECT_FALSE(manager->loadModel(config));
}

TEST_F(ModelManagerTest, ModelStatistics) {
    // Test statistics for non-existent model
    auto stats = manager->getModelStats("nonexistent-model");
    EXPECT_EQ(stats.totalInferences, 0);
    EXPECT_EQ(stats.totalTokens, 0);
    EXPECT_FLOAT_EQ(stats.averageLatency, 0.0f);
    EXPECT_EQ(stats.peakMemoryUsage, 0);
    EXPECT_EQ(stats.currentMemoryUsage, 0);

    // Update statistics for non-existent model
    manager->updateModelStats("nonexistent-model", 100, 0.5f, 1024);
    stats = manager->getModelStats("nonexistent-model");
    EXPECT_EQ(stats.totalInferences, 0);  // Should not update for non-existent model
}

TEST_F(ModelManagerTest, ResourceManagement) {
    EXPECT_GE(manager->getTotalMemoryUsage(), 0);
    EXPECT_GE(manager->getAvailableMemory(), 0);

    ModelConfig config;
    config.modelId = "test-model";
    config.modelPath = "test_model.bin";
    config.modelType = "gpt";
    config.maxBatchSize = 32;
    config.maxSequenceLength = 1024;
    config.useHalfPrecision = true;
    config.useQuantization = false;
    config.supportedTasks = {"text-generation"};

    EXPECT_FALSE(manager->canLoadModel(config));  // Should fail because model file doesn't exist
}

TEST_F(ModelManagerTest, ModelCompatibility) {
    ModelConfig config;
    config.modelId = "test-model";
    config.modelPath = "test_model.bin";
    config.modelType = "unsupported-type";
    config.maxBatchSize = 32;
    config.maxSequenceLength = 1024;
    config.useHalfPrecision = true;
    config.useQuantization = false;
    config.supportedTasks = {"text-generation"};

    EXPECT_FALSE(manager->loadModel(config));  // Should fail because model type is not supported
}

TEST_F(ModelManagerTest, ErrorHandling) {
    // Test with invalid model ID
    EXPECT_FALSE(manager->isModelLoaded("nonexistent-model"));

    // Test with invalid configuration
    ModelConfig config;
    config.modelId = "test-model";
    config.modelPath = "test_model.bin";
    config.modelType = "gpt";
    config.maxBatchSize = 0;  // Invalid batch size
    config.maxSequenceLength = 1024;
    config.useHalfPrecision = true;
    config.useQuantization = false;
    config.supportedTasks = {"text-generation"};

    EXPECT_FALSE(manager->loadModel(config));
    EXPECT_FALSE(manager->getLastError().empty());
}

TEST_F(ModelManagerTest, ModelConfigUpdate) {
    ModelConfig config;
    config.modelId = "test-model";
    config.modelPath = "test_model.bin";
    config.modelType = "gpt";
    config.maxBatchSize = 32;
    config.maxSequenceLength = 1024;
    config.useHalfPrecision = true;
    config.useQuantization = false;
    config.supportedTasks = {"text-generation"};

    // Try to update non-existent model
    EXPECT_FALSE(manager->updateModelConfig(config));

    // Try to load model (should fail but we can still test update)
    manager->loadModel(config);

    // Update configuration
    config.maxBatchSize = 64;
    EXPECT_FALSE(manager->updateModelConfig(config));  // Should fail because model is not loaded
}

TEST_F(ModelManagerTest, ModelConfigRetrieval) {
    // Try to get config for non-existent model
    auto config = manager->getModelConfig("nonexistent-model");
    EXPECT_TRUE(config.modelId.empty());
    EXPECT_TRUE(config.modelPath.empty());
    EXPECT_TRUE(config.modelType.empty());
    EXPECT_EQ(config.maxBatchSize, 0);
    EXPECT_EQ(config.maxSequenceLength, 0);
    EXPECT_FALSE(config.useHalfPrecision);
    EXPECT_FALSE(config.useQuantization);
    EXPECT_TRUE(config.supportedTasks.empty());
} 