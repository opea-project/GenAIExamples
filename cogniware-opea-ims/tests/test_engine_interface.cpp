#include <gtest/gtest.h>
#include "llm_inference_core/engine/engine_interface.h"

using namespace cogniware;

class EngineInterfaceTest : public ::testing::Test {
protected:
    void SetUp() override {
        interface = &EngineInterface::getInstance();
    }

    void TearDown() override {
        interface->shutdown();
    }

    EngineInterface* interface;
};

TEST_F(EngineInterfaceTest, Initialization) {
    EXPECT_TRUE(interface->initialize());
}

TEST_F(EngineInterfaceTest, ModelLoading) {
    ASSERT_TRUE(interface->initialize());

    // Test loading a model
    EXPECT_FALSE(interface->loadModel("test-model", "test_model.bin"));
}

TEST_F(EngineInterfaceTest, RequestProcessing) {
    ASSERT_TRUE(interface->initialize());

    // Test processing a request
    InferenceRequest request;
    request.modelId = "test-model";
    request.prompt = "Hello, world!";
    request.maxTokens = 100;
    request.temperature = 0.7f;
    request.topP = 0.9f;
    request.numBeams = 4;
    request.streamOutput = false;

    auto response = interface->processRequest(request);
    EXPECT_FALSE(response.success);
    EXPECT_FALSE(response.error.empty());
}

TEST_F(EngineInterfaceTest, RequestValidation) {
    ASSERT_TRUE(interface->initialize());

    // Test empty prompt
    InferenceRequest request;
    request.modelId = "test-model";
    request.prompt = "";
    request.maxTokens = 100;
    request.temperature = 0.7f;
    request.topP = 0.9f;
    request.numBeams = 4;
    request.streamOutput = false;

    auto response = interface->processRequest(request);
    EXPECT_FALSE(response.success);
    EXPECT_FALSE(response.error.empty());

    // Test invalid temperature
    request.prompt = "Hello, world!";
    request.temperature = 2.5f;
    response = interface->processRequest(request);
    EXPECT_FALSE(response.success);
    EXPECT_FALSE(response.error.empty());

    // Test invalid top-p
    request.temperature = 0.7f;
    request.topP = 1.5f;
    response = interface->processRequest(request);
    EXPECT_FALSE(response.success);
    EXPECT_FALSE(response.error.empty());

    // Test zero max tokens
    request.topP = 0.9f;
    request.maxTokens = 0;
    response = interface->processRequest(request);
    EXPECT_FALSE(response.success);
    EXPECT_FALSE(response.error.empty());

    // Test zero beams
    request.maxTokens = 100;
    request.numBeams = 0;
    response = interface->processRequest(request);
    EXPECT_FALSE(response.success);
    EXPECT_FALSE(response.error.empty());
}

TEST_F(EngineInterfaceTest, StreamingResponse) {
    ASSERT_TRUE(interface->initialize());

    // Test streaming response
    InferenceRequest request;
    request.modelId = "test-model";
    request.prompt = "Hello, world!";
    request.maxTokens = 100;
    request.temperature = 0.7f;
    request.topP = 0.9f;
    request.numBeams = 4;
    request.streamOutput = true;

    bool callbackCalled = false;
    EXPECT_FALSE(interface->streamResponse(request,
        [&callbackCalled](const std::string& token) {
            callbackCalled = true;
        }
    ));
    EXPECT_FALSE(callbackCalled);
}

TEST_F(EngineInterfaceTest, ErrorHandling) {
    ASSERT_TRUE(interface->initialize());

    // Test with invalid model ID
    EXPECT_FALSE(interface->isModelLoaded("nonexistent-model"));

    // Test with invalid request
    InferenceRequest request;
    request.modelId = "nonexistent-model";
    request.prompt = "Hello, world!";
    request.maxTokens = 100;
    request.temperature = 0.7f;
    request.topP = 0.9f;
    request.numBeams = 4;
    request.streamOutput = false;

    auto response = interface->processRequest(request);
    EXPECT_FALSE(response.success);
    EXPECT_FALSE(response.error.empty());
}

TEST_F(EngineInterfaceTest, MultipleInitialization) {
    EXPECT_TRUE(interface->initialize());
    EXPECT_TRUE(interface->initialize());  // Should be idempotent
}

TEST_F(EngineInterfaceTest, Shutdown) {
    ASSERT_TRUE(interface->initialize());
    interface->shutdown();
    EXPECT_TRUE(interface->initialize());  // Should be able to reinitialize after shutdown
}

TEST_F(EngineInterfaceTest, ModelManagement) {
    ASSERT_TRUE(interface->initialize());

    // Test model loading
    EXPECT_FALSE(interface->loadModel("test-model", "test_model.bin"));
    EXPECT_FALSE(interface->isModelLoaded("test-model"));

    // Test model unloading
    EXPECT_FALSE(interface->unloadModel("test-model"));
}

TEST_F(EngineInterfaceTest, Statistics) {
    ASSERT_TRUE(interface->initialize());

    EXPECT_EQ(interface->getTotalInferences(), 0);
    EXPECT_FLOAT_EQ(interface->getAverageLatency(), 0.0f);

    auto stats = interface->getModelStats("test-model");
    EXPECT_EQ(stats.totalInferences, 0);
    EXPECT_EQ(stats.totalTokens, 0);
    EXPECT_FLOAT_EQ(stats.averageLatency, 0.0f);
    EXPECT_EQ(stats.peakMemoryUsage, 0);
    EXPECT_EQ(stats.currentMemoryUsage, 0);
} 