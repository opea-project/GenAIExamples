#include <gtest/gtest.h>
#include "llm_inference_core/engine/engine_manager.h"

using namespace cogniware;

class EngineManagerTest : public ::testing::Test {
protected:
    void SetUp() override {
        manager = &EngineManager::getInstance();
    }

    void TearDown() override {
        manager->shutdown();
    }

    EngineManager* manager;
};

TEST_F(EngineManagerTest, Initialization) {
    EXPECT_TRUE(manager->initialize());
}

TEST_F(EngineManagerTest, EngineCreation) {
    ASSERT_TRUE(manager->initialize());

    // Test creating an engine
    EXPECT_FALSE(manager->createEngine("test-engine", "test_model.bin"));
}

TEST_F(EngineManagerTest, EngineConfiguration) {
    ASSERT_TRUE(manager->initialize());

    // Test setting engine configuration
    EngineConfig config;
    config.maxBatchSize = 32;
    config.maxSequenceLength = 1024;
    config.useHalfPrecision = true;
    config.useQuantization = false;
    config.supportedTasks = {"text-generation"};

    EXPECT_TRUE(manager->setEngineConfig(config));

    // Test getting engine configuration
    auto retrievedConfig = manager->getEngineConfig();
    EXPECT_EQ(retrievedConfig.maxBatchSize, config.maxBatchSize);
    EXPECT_EQ(retrievedConfig.maxSequenceLength, config.maxSequenceLength);
    EXPECT_EQ(retrievedConfig.useHalfPrecision, config.useHalfPrecision);
    EXPECT_EQ(retrievedConfig.useQuantization, config.useQuantization);
    EXPECT_EQ(retrievedConfig.supportedTasks, config.supportedTasks);
}

TEST_F(EngineManagerTest, EngineStats) {
    ASSERT_TRUE(manager->initialize());

    // Test getting engine statistics
    auto stats = manager->getEngineStats("test-engine");
    EXPECT_EQ(stats.totalInferences, 0);
    EXPECT_EQ(stats.totalTokens, 0);
    EXPECT_FLOAT_EQ(stats.averageLatency, 0.0f);
    EXPECT_EQ(stats.peakMemoryUsage, 0);
    EXPECT_EQ(stats.currentMemoryUsage, 0);
}

TEST_F(EngineManagerTest, ErrorHandling) {
    ASSERT_TRUE(manager->initialize());

    // Test invalid engine ID
    EXPECT_FALSE(manager->createEngine("", "test_model.bin"));
    EXPECT_TRUE(manager->getEngineStats("").totalInferences == 0);

    // Test invalid batch size
    EngineConfig config;
    config.maxBatchSize = 0;
    config.maxSequenceLength = 1024;
    config.useHalfPrecision = true;
    config.useQuantization = false;
    config.supportedTasks = {"text-generation"};
    EXPECT_FALSE(manager->setEngineConfig(config));

    // Test invalid sequence length
    config.maxBatchSize = 32;
    config.maxSequenceLength = 0;
    EXPECT_FALSE(manager->setEngineConfig(config));
}

TEST_F(EngineManagerTest, MultipleEngines) {
    ASSERT_TRUE(manager->initialize());

    // Test creating multiple engines
    EXPECT_FALSE(manager->createEngine("engine1", "test_model1.bin"));
    EXPECT_FALSE(manager->createEngine("engine2", "test_model2.bin"));
    EXPECT_FALSE(manager->createEngine("engine3", "test_model3.bin"));
}

TEST_F(EngineManagerTest, EngineShutdown) {
    ASSERT_TRUE(manager->initialize());

    // Create an engine
    EXPECT_FALSE(manager->createEngine("test-engine", "test_model.bin"));

    // Shutdown the engine
    EXPECT_TRUE(manager->shutdownEngine("test-engine"));

    // Try to use the engine after shutdown
    EXPECT_TRUE(manager->getEngineStats("test-engine").totalInferences == 0);
}

TEST_F(EngineManagerTest, EngineReset) {
    ASSERT_TRUE(manager->initialize());

    // Set some configuration
    EngineConfig config;
    config.maxBatchSize = 32;
    config.maxSequenceLength = 1024;
    config.useHalfPrecision = true;
    config.useQuantization = false;
    config.supportedTasks = {"text-generation"};
    EXPECT_TRUE(manager->setEngineConfig(config));

    // Reset engine manager
    manager->reset();

    // Verify reset
    auto retrievedConfig = manager->getEngineConfig();
    EXPECT_EQ(retrievedConfig.maxBatchSize, 0);
    EXPECT_EQ(retrievedConfig.maxSequenceLength, 0);
    EXPECT_FALSE(retrievedConfig.useHalfPrecision);
    EXPECT_FALSE(retrievedConfig.useQuantization);
    EXPECT_TRUE(retrievedConfig.supportedTasks.empty());
}

TEST_F(EngineManagerTest, TaskSupport) {
    ASSERT_TRUE(manager->initialize());

    // Test different supported tasks
    std::vector<std::string> tasks = {"text-generation", "text-completion", "text-embedding"};
    for (const auto& task : tasks) {
        EngineConfig config;
        config.maxBatchSize = 32;
        config.maxSequenceLength = 1024;
        config.useHalfPrecision = true;
        config.useQuantization = false;
        config.supportedTasks = {task};
        EXPECT_TRUE(manager->setEngineConfig(config));
    }
}

TEST_F(EngineManagerTest, PrecisionModes) {
    ASSERT_TRUE(manager->initialize());

    // Test different precision modes
    std::vector<bool> halfPrecisionModes = {true, false};
    std::vector<bool> quantizationModes = {true, false};
    for (bool halfPrecision : halfPrecisionModes) {
        for (bool quantization : quantizationModes) {
            EngineConfig config;
            config.maxBatchSize = 32;
            config.maxSequenceLength = 1024;
            config.useHalfPrecision = halfPrecision;
            config.useQuantization = quantization;
            config.supportedTasks = {"text-generation"};
            EXPECT_TRUE(manager->setEngineConfig(config));
        }
    }
} 