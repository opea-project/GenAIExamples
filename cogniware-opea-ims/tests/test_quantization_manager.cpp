#include <gtest/gtest.h>
#include "llm_inference_core/optimization/quantization_manager.h"

using namespace cogniware;

class QuantizationManagerTest : public ::testing::Test {
protected:
    void SetUp() override {
        manager = &QuantizationManager::getInstance();
    }

    void TearDown() override {
        manager->reset();
    }

    QuantizationManager* manager;
};

TEST_F(QuantizationManagerTest, Initialization) {
    EXPECT_TRUE(manager->initialize());
}

TEST_F(QuantizationManagerTest, ModelQuantization) {
    ASSERT_TRUE(manager->initialize());

    // Test quantizing a model
    EXPECT_FALSE(manager->quantizeModel("test-model", "test_model.bin", "test_model_quantized.bin", 8));
}

TEST_F(QuantizationManagerTest, QuantizationConfig) {
    ASSERT_TRUE(manager->initialize());

    // Test setting quantization configuration
    QuantizationConfig config;
    config.bits = 8;
    config.symmetric = true;
    config.perChannel = true;
    config.calibrationMethod = "minmax";

    EXPECT_TRUE(manager->setQuantizationConfig(config));

    // Test getting quantization configuration
    auto retrievedConfig = manager->getQuantizationConfig();
    EXPECT_EQ(retrievedConfig.bits, config.bits);
    EXPECT_EQ(retrievedConfig.symmetric, config.symmetric);
    EXPECT_EQ(retrievedConfig.perChannel, config.perChannel);
    EXPECT_EQ(retrievedConfig.calibrationMethod, config.calibrationMethod);
}

TEST_F(QuantizationManagerTest, CalibrationData) {
    ASSERT_TRUE(manager->initialize());

    // Test adding calibration data
    std::vector<float> calibrationData = {1.0f, 2.0f, 3.0f, 4.0f, 5.0f};
    EXPECT_TRUE(manager->addCalibrationData("test-model", calibrationData));

    // Test getting calibration data
    auto retrievedData = manager->getCalibrationData("test-model");
    EXPECT_EQ(retrievedData.size(), calibrationData.size());
    for (size_t i = 0; i < calibrationData.size(); ++i) {
        EXPECT_FLOAT_EQ(retrievedData[i], calibrationData[i]);
    }
}

TEST_F(QuantizationManagerTest, ErrorHandling) {
    ASSERT_TRUE(manager->initialize());

    // Test invalid model ID
    EXPECT_FALSE(manager->quantizeModel("", "test_model.bin", "test_model_quantized.bin", 8));
    EXPECT_FALSE(manager->addCalibrationData("", std::vector<float>()));
    EXPECT_TRUE(manager->getCalibrationData("").empty());

    // Test invalid bits
    EXPECT_FALSE(manager->quantizeModel("test-model", "test_model.bin", "test_model_quantized.bin", 0));
    EXPECT_FALSE(manager->quantizeModel("test-model", "test_model.bin", "test_model_quantized.bin", 9));

    // Test invalid calibration method
    QuantizationConfig config;
    config.bits = 8;
    config.symmetric = true;
    config.perChannel = true;
    config.calibrationMethod = "invalid";
    EXPECT_FALSE(manager->setQuantizationConfig(config));
}

TEST_F(QuantizationManagerTest, QuantizationStats) {
    ASSERT_TRUE(manager->initialize());

    // Test getting quantization statistics
    auto stats = manager->getQuantizationStats("test-model");
    EXPECT_EQ(stats.originalSize, 0);
    EXPECT_EQ(stats.quantizedSize, 0);
    EXPECT_FLOAT_EQ(stats.compressionRatio, 0.0f);
    EXPECT_FLOAT_EQ(stats.accuracyLoss, 0.0f);
}

TEST_F(QuantizationManagerTest, MultipleQuantization) {
    ASSERT_TRUE(manager->initialize());

    // Test quantizing the same model multiple times
    EXPECT_FALSE(manager->quantizeModel("test-model", "test_model.bin", "test_model_quantized_1.bin", 8));
    EXPECT_FALSE(manager->quantizeModel("test-model", "test_model.bin", "test_model_quantized_2.bin", 4));
    EXPECT_FALSE(manager->quantizeModel("test-model", "test_model.bin", "test_model_quantized_3.bin", 2));
}

TEST_F(QuantizationManagerTest, CalibrationMethods) {
    ASSERT_TRUE(manager->initialize());

    // Test different calibration methods
    std::vector<std::string> methods = {"minmax", "kl", "entropy"};
    for (const auto& method : methods) {
        QuantizationConfig config;
        config.bits = 8;
        config.symmetric = true;
        config.perChannel = true;
        config.calibrationMethod = method;
        EXPECT_TRUE(manager->setQuantizationConfig(config));
    }
}

TEST_F(QuantizationManagerTest, QuantizationReset) {
    ASSERT_TRUE(manager->initialize());

    // Set some configuration
    QuantizationConfig config;
    config.bits = 8;
    config.symmetric = true;
    config.perChannel = true;
    config.calibrationMethod = "minmax";
    EXPECT_TRUE(manager->setQuantizationConfig(config));

    // Add some calibration data
    std::vector<float> calibrationData = {1.0f, 2.0f, 3.0f, 4.0f, 5.0f};
    EXPECT_TRUE(manager->addCalibrationData("test-model", calibrationData));

    // Reset quantization manager
    manager->reset();

    // Verify reset
    auto retrievedConfig = manager->getQuantizationConfig();
    EXPECT_EQ(retrievedConfig.bits, 0);
    EXPECT_FALSE(retrievedConfig.symmetric);
    EXPECT_FALSE(retrievedConfig.perChannel);
    EXPECT_TRUE(retrievedConfig.calibrationMethod.empty());

    EXPECT_TRUE(manager->getCalibrationData("test-model").empty());
} 