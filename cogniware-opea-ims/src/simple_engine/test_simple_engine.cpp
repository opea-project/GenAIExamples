#include "simple_engine.h"
#include <iostream>
#include <thread>
#include <chrono>

int main() {
    std::cout << "=== Simple Engine Test ===" << std::endl;
    
    // Create engine
    cognisynapse::SimpleEngine engine;
    
    // Initialize engine
    std::cout << "Initializing engine..." << std::endl;
    if (!engine.initialize()) {
        std::cerr << "Failed to initialize engine" << std::endl;
        return 1;
    }
    
    // Load a test model
    std::cout << "Loading test model..." << std::endl;
    if (!engine.loadModel("test_model", "/path/to/test/model")) {
        std::cerr << "Failed to load test model" << std::endl;
        return 1;
    }
    
    // Check health
    std::cout << "Engine healthy: " << (engine.isHealthy() ? "Yes" : "No") << std::endl;
    
    // Get loaded models
    auto models = engine.getLoadedModels();
    std::cout << "Loaded models: " << models.size() << std::endl;
    for (const auto& model : models) {
        std::cout << "  - " << model.id << " (" << model.name << ")" << std::endl;
    }
    
    // Test inference
    std::cout << "Testing inference..." << std::endl;
    cognisynapse::InferenceRequest request;
    request.id = "test_request_1";
    request.model_id = "test_model";
    request.prompt = "Hello, how are you?";
    request.max_tokens = 50;
    request.temperature = 0.7f;
    request.user_id = "test_user";
    request.timestamp = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::system_clock::now().time_since_epoch()).count();
    
    auto response = engine.processInference(request);
    
    std::cout << "Inference result:" << std::endl;
    std::cout << "  Success: " << (response.success ? "Yes" : "No") << std::endl;
    std::cout << "  Generated text: " << response.generated_text << std::endl;
    std::cout << "  Tokens generated: " << response.tokens_generated << std::endl;
    std::cout << "  Processing time: " << response.processing_time_ms << " ms" << std::endl;
    
    if (!response.success) {
        std::cout << "  Error: " << response.error_message << std::endl;
    }
    
    // Get statistics
    auto stats = engine.getStats();
    std::cout << "Engine statistics:" << std::endl;
    std::cout << "  Total requests: " << stats.total_requests << std::endl;
    std::cout << "  Successful requests: " << stats.successful_requests << std::endl;
    std::cout << "  Failed requests: " << stats.failed_requests << std::endl;
    std::cout << "  Average processing time: " << stats.average_processing_time_ms << " ms" << std::endl;
    std::cout << "  Memory usage: " << stats.memory_usage_mb << " MB" << std::endl;
    std::cout << "  Active models: " << stats.active_models << std::endl;
    
    // Get status as JSON
    auto status = engine.getStatus();
    std::cout << "Engine status (JSON):" << std::endl;
    std::cout << status.dump(2) << std::endl;
    
    // Test multiple requests
    std::cout << "Testing multiple requests..." << std::endl;
    for (int i = 0; i < 5; ++i) {
        request.id = "test_request_" + std::to_string(i + 2);
        request.prompt = "Test prompt " + std::to_string(i + 1);
        
        auto resp = engine.processInference(request);
        std::cout << "  Request " << (i + 2) << ": " 
                  << (resp.success ? "Success" : "Failed") 
                  << " (" << resp.processing_time_ms << " ms)" << std::endl;
    }
    
    // Final statistics
    stats = engine.getStats();
    std::cout << "Final statistics:" << std::endl;
    std::cout << "  Total requests: " << stats.total_requests << std::endl;
    std::cout << "  Success rate: " 
              << (stats.total_requests > 0 ? (100.0 * stats.successful_requests / stats.total_requests) : 0.0)
              << "%" << std::endl;
    
    // Unload model
    std::cout << "Unloading test model..." << std::endl;
    if (!engine.unloadModel("test_model")) {
        std::cerr << "Failed to unload test model" << std::endl;
    }
    
    // Shutdown engine
    std::cout << "Shutting down engine..." << std::endl;
    engine.shutdown();
    
    std::cout << "=== Test Complete ===" << std::endl;
    return 0;
}
