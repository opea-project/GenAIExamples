#include <gtest/gtest.h>
#include "llm_inference_core/optimization/optimization_manager.h"

using namespace cogniware;

class OptimizationManagerTest : public ::testing::Test {
protected:
    void SetUp() override {
        manager = &OptimizationManager::getInstance();
    }

    void TearDown() override {
        manager->reset();
    }

    OptimizationManager* manager;
};

TEST_F(OptimizationManagerTest, Initialization) {
    EXPECT_TRUE(manager->initialize());
}

TEST_F(OptimizationManagerTest, ModelOptimization) {
    ASSERT_TRUE(manager->initialize());

    // Test optimizing a model
    EXPECT_FALSE(manager->optimizeModel("test-model", "test_model.bin", "test_model_optimized.bin"));
}

TEST_F(OptimizationManagerTest, OptimizationConfig) {
    ASSERT_TRUE(manager->initialize());

    // Test setting optimization configuration
    OptimizationConfig config;
    config.enableFusion = true;
    config.enablePruning = true;
    config.enableQuantization = true;
    config.targetDevice = "cuda";
    config.optimizationLevel = 3;

    EXPECT_TRUE(manager->setOptimizationConfig(config));

    // Test getting optimization configuration
    auto retrievedConfig = manager->getOptimizationConfig();
    EXPECT_EQ(retrievedConfig.enableFusion, config.enableFusion);
    EXPECT_EQ(retrievedConfig.enablePruning, config.enablePruning);
    EXPECT_EQ(retrievedConfig.enableQuantization, config.enableQuantization);
    EXPECT_EQ(retrievedConfig.targetDevice, config.targetDevice);
    EXPECT_EQ(retrievedConfig.optimizationLevel, config.optimizationLevel);
}

TEST_F(OptimizationManagerTest, OptimizationStats) {
    ASSERT_TRUE(manager->initialize());

    // Test getting optimization statistics
    auto stats = manager->getOptimizationStats("test-model");
    EXPECT_EQ(stats.originalSize, 0);
    EXPECT_EQ(stats.optimizedSize, 0);
    EXPECT_FLOAT_EQ(stats.compressionRatio, 0.0f);
    EXPECT_FLOAT_EQ(stats.speedup, 0.0f);
}

TEST_F(OptimizationManagerTest, ErrorHandling) {
    ASSERT_TRUE(manager->initialize());

    // Test invalid model ID
    EXPECT_FALSE(manager->optimizeModel("", "test_model.bin", "test_model_optimized.bin"));
    EXPECT_TRUE(manager->getOptimizationStats("").originalSize == 0);

    // Test invalid optimization level
    OptimizationConfig config;
    config.enableFusion = true;
    config.enablePruning = true;
    config.enableQuantization = true;
    config.targetDevice = "cuda";
    config.optimizationLevel = 5;  // Invalid level
    EXPECT_FALSE(manager->setOptimizationConfig(config));

    // Test invalid target device
    config.optimizationLevel = 3;
    config.targetDevice = "invalid";
    EXPECT_FALSE(manager->setOptimizationConfig(config));
}

TEST_F(OptimizationManagerTest, MultipleOptimization) {
    ASSERT_TRUE(manager->initialize());

    // Test optimizing the same model multiple times with different configurations
    OptimizationConfig config1;
    config1.enableFusion = true;
    config1.enablePruning = false;
    config1.enableQuantization = false;
    config1.targetDevice = "cuda";
    config1.optimizationLevel = 1;
    EXPECT_TRUE(manager->setOptimizationConfig(config1));
    EXPECT_FALSE(manager->optimizeModel("test-model", "test_model.bin", "test_model_optimized_1.bin"));

    OptimizationConfig config2;
    config2.enableFusion = true;
    config2.enablePruning = true;
    config2.enableQuantization = false;
    config2.targetDevice = "cuda";
    config2.optimizationLevel = 2;
    EXPECT_TRUE(manager->setOptimizationConfig(config2));
    EXPECT_FALSE(manager->optimizeModel("test-model", "test_model.bin", "test_model_optimized_2.bin"));

    OptimizationConfig config3;
    config3.enableFusion = true;
    config3.enablePruning = true;
    config3.enableQuantization = true;
    config3.targetDevice = "cuda";
    config3.optimizationLevel = 3;
    EXPECT_TRUE(manager->setOptimizationConfig(config3));
    EXPECT_FALSE(manager->optimizeModel("test-model", "test_model.bin", "test_model_optimized_3.bin"));
}

TEST_F(OptimizationManagerTest, OptimizationReset) {
    ASSERT_TRUE(manager->initialize());

    // Set some configuration
    OptimizationConfig config;
    config.enableFusion = true;
    config.enablePruning = true;
    config.enableQuantization = true;
    config.targetDevice = "cuda";
    config.optimizationLevel = 3;
    EXPECT_TRUE(manager->setOptimizationConfig(config));

    // Reset optimization manager
    manager->reset();

    // Verify reset
    auto retrievedConfig = manager->getOptimizationConfig();
    EXPECT_FALSE(retrievedConfig.enableFusion);
    EXPECT_FALSE(retrievedConfig.enablePruning);
    EXPECT_FALSE(retrievedConfig.enableQuantization);
    EXPECT_TRUE(retrievedConfig.targetDevice.empty());
    EXPECT_EQ(retrievedConfig.optimizationLevel, 0);
}

TEST_F(OptimizationManagerTest, DeviceSupport) {
    ASSERT_TRUE(manager->initialize());

    // Test different target devices
    std::vector<std::string> devices = {"cuda", "cpu", "rocm"};
    for (const auto& device : devices) {
        OptimizationConfig config;
        config.enableFusion = true;
        config.enablePruning = true;
        config.enableQuantization = true;
        config.targetDevice = device;
        config.optimizationLevel = 3;
        EXPECT_TRUE(manager->setOptimizationConfig(config));
    }
}

TEST_F(OptimizationManagerTest, OptimizationLevels) {
    ASSERT_TRUE(manager->initialize());

    // Test different optimization levels
    for (int level = 0; level <= 3; ++level) {
        OptimizationConfig config;
        config.enableFusion = true;
        config.enablePruning = true;
        config.enableQuantization = true;
        config.targetDevice = "cuda";
        config.optimizationLevel = level;
        EXPECT_TRUE(manager->setOptimizationConfig(config));
    }
} 