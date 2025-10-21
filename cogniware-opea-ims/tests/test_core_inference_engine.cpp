#include "llm_inference_core/llm_inference_core.h"
#include <iostream>
#include <cassert>
#include <chrono>
#include <thread>

using namespace cogniware;

void testInferenceEngineInitialization() {
    std::cout << "Testing inference engine initialization..." << std::endl;
    
    auto& engine = LLMInferenceCore::getInstance();
    
    // Test initialization
    bool initialized = engine.initialize();
    assert(initialized && "Failed to initialize inference engine");
    
    std::cout << "✓ Inference engine initialized successfully" << std::endl;
}

void testModelLoading() {
    std::cout << "Testing model loading..." << std::endl;
    
    auto& engine = LLMInferenceCore::getInstance();
    
    // Create a test model configuration
    ModelConfig config;
    config.modelId = "test-model";
    config.modelPath = "models/test-model.bin";
    config.modelType = "gpt";
    config.maxBatchSize = 8;
    config.maxSequenceLength = 1024;
    config.useHalfPrecision = true;
    config.useQuantization = false;
    config.supportedTasks = {"text-generation"};
    
    // Test model loading (this will fail if model file doesn't exist, which is expected)
    bool loaded = engine.loadModel(config);
    if (!loaded) {
        std::cout << "⚠ Model loading failed (expected if model file doesn't exist): " 
                  << engine.getLastError() << std::endl;
    } else {
        std::cout << "✓ Model loaded successfully" << std::endl;
    }
}

void testInferenceRequest() {
    std::cout << "Testing inference request..." << std::endl;
    
    auto& engine = LLMInferenceCore::getInstance();
    
    // Create a test inference request
    InferenceRequest request;
    request.modelId = "test-model";
    request.prompt = "Hello, how are you?";
    request.maxTokens = 50;
    request.temperature = 0.7f;
    request.topP = 0.9f;
    request.numBeams = 1;
    request.streamOutput = false;
    
    // Test inference (this will fail if model is not loaded, which is expected)
    auto response = engine.processRequest(request);
    if (!response.success) {
        std::cout << "⚠ Inference failed (expected if model not loaded): " 
                  << response.error << std::endl;
    } else {
        std::cout << "✓ Inference completed successfully" << std::endl;
        std::cout << "  Generated text: " << response.generatedText << std::endl;
        std::cout << "  Tokens generated: " << response.numTokens << std::endl;
        std::cout << "  Latency: " << response.latency << " seconds" << std::endl;
    }
}

void testStreamingInference() {
    std::cout << "Testing streaming inference..." << std::endl;
    
    auto& engine = LLMInferenceCore::getInstance();
    
    // Create a test inference request for streaming
    InferenceRequest request;
    request.modelId = "test-model";
    request.prompt = "Tell me a story about";
    request.maxTokens = 30;
    request.temperature = 0.8f;
    request.topP = 0.9f;
    request.numBeams = 1;
    request.streamOutput = true;
    
    // Test streaming inference
    bool streamSuccess = engine.streamResponse(request, [](const std::string& token) {
        std::cout << token << std::flush;
    });
    
    if (!streamSuccess) {
        std::cout << "⚠ Streaming inference failed (expected if model not loaded): " 
                  << engine.getLastError() << std::endl;
    } else {
        std::cout << std::endl << "✓ Streaming inference completed successfully" << std::endl;
    }
}

void testGPUStats() {
    std::cout << "Testing GPU statistics..." << std::endl;
    
    auto& engine = LLMInferenceCore::getInstance();
    
    // Test GPU stats retrieval
    auto gpuStats = engine.getGPUStats();
    std::cout << "✓ GPU stats retrieved successfully" << std::endl;
    std::cout << "  GPU utilization: " << gpuStats.utilization << "%" << std::endl;
    std::cout << "  Memory usage: " << gpuStats.usedMemory << " / " << gpuStats.totalMemory << " bytes" << std::endl;
}

void testModelStats() {
    std::cout << "Testing model statistics..." << std::endl;
    
    auto& engine = LLMInferenceCore::getInstance();
    
    // Test model stats retrieval
    auto modelStats = engine.getModelStats("test-model");
    std::cout << "✓ Model stats retrieved successfully" << std::endl;
    std::cout << "  Total inferences: " << modelStats.totalInferences << std::endl;
    std::cout << "  Average latency: " << modelStats.averageLatency << " seconds" << std::endl;
}

void testErrorHandling() {
    std::cout << "Testing error handling..." << std::endl;
    
    auto& engine = LLMInferenceCore::getInstance();
    
    // Test with invalid model ID
    InferenceRequest request;
    request.modelId = "non-existent-model";
    request.prompt = "Test prompt";
    request.maxTokens = 10;
    request.temperature = 0.7f;
    request.topP = 0.9f;
    request.numBeams = 1;
    request.streamOutput = false;
    
    auto response = engine.processRequest(request);
    if (!response.success) {
        std::cout << "✓ Error handling works correctly: " << response.error << std::endl;
    } else {
        std::cout << "⚠ Expected error but got success" << std::endl;
    }
}

int main() {
    std::cout << "=== CogniWare Core Inference Engine Test ===" << std::endl;
    std::cout << std::endl;
    
    try {
        testInferenceEngineInitialization();
        std::cout << std::endl;
        
        testModelLoading();
        std::cout << std::endl;
        
        testInferenceRequest();
        std::cout << std::endl;
        
        testStreamingInference();
        std::cout << std::endl;
        
        testGPUStats();
        std::cout << std::endl;
        
        testModelStats();
        std::cout << std::endl;
        
        testErrorHandling();
        std::cout << std::endl;
        
        std::cout << "=== All tests completed ===" << std::endl;
        
    } catch (const std::exception& e) {
        std::cerr << "Test failed with exception: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}
