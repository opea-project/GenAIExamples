#include "enhanced_engine.h"
#include <iostream>
#include <thread>
#include <chrono>
#include <vector>
#include <future>

int main() {
    std::cout << "=== Enhanced Engine Test ===" << std::endl;
    
    // Create enhanced engine
    cognisynapse::EnhancedEngine engine;
    
    // Initialize engine
    std::cout << "Initializing enhanced engine..." << std::endl;
    if (!engine.initialize()) {
        std::cerr << "Failed to initialize enhanced engine" << std::endl;
        return 1;
    }
    
    // Check health
    std::cout << "Engine healthy: " << (engine.isHealthy() ? "Yes" : "No") << std::endl;
    
    // Get compute node status
    auto node_statuses = engine.getComputeNodeStatus();
    std::cout << "Compute nodes: " << node_statuses.size() << std::endl;
    for (const auto& status : node_statuses) {
        std::cout << "  - Node " << status.node_id << ": " 
                  << (status.active ? "Active" : "Inactive") 
                  << " (Memory: " << status.used_memory_mb << "/" << (status.used_memory_mb + status.available_memory_mb) << " MB)"
                  << " (Models: " << status.active_models << ")" << std::endl;
    }
    
    // Get loaded models
    auto models = engine.getLoadedModels();
    std::cout << "Loaded models: " << models.size() << std::endl;
    for (const auto& model : models) {
        std::cout << "  - " << model.id << " (" << model.name << ") on " << model.compute_node_id
                  << " (" << model.memory_usage_mb << " MB)" << std::endl;
    }
    
    // Test parallel inference
    std::cout << "Testing parallel inference..." << std::endl;
    std::vector<std::future<cognisynapse::EnhancedInferenceResponse>> futures;
    
    // Create multiple requests
    for (int i = 0; i < 10; ++i) {
        cognisynapse::EnhancedInferenceRequest request;
        request.id = "test_request_" + std::to_string(i);
        request.model_id = "llama-7b";  // Use one of the default models
        request.prompt = "Hello, this is test request " + std::to_string(i);
        request.max_tokens = 50;
        request.temperature = 0.7f;
        request.user_id = "test_user";
        request.priority = i % 3;  // Vary priority
        request.timestamp = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::system_clock::now().time_since_epoch()).count();
        
        futures.push_back(engine.processInferenceAsync(request));
    }
    
    // Wait for all requests to complete
    std::vector<cognisynapse::EnhancedInferenceResponse> responses;
    for (auto& future : futures) {
        responses.push_back(future.get());
    }
    
    // Analyze results
    int successful = 0;
    float total_processing_time = 0.0f;
    std::unordered_map<std::string, int> node_usage;
    
    for (const auto& response : responses) {
        if (response.success) {
            successful++;
            total_processing_time += response.processing_time_ms;
            node_usage[response.compute_node_id]++;
            
            std::cout << "  Request " << response.id << ": Success (" 
                      << response.processing_time_ms << " ms) on " << response.compute_node_id << std::endl;
        } else {
            std::cout << "  Request " << response.id << ": Failed - " << response.error_message << std::endl;
        }
    }
    
    std::cout << "Parallel inference results:" << std::endl;
    std::cout << "  Successful: " << successful << "/" << responses.size() << std::endl;
    std::cout << "  Average processing time: " << (total_processing_time / successful) << " ms" << std::endl;
    std::cout << "  Node usage:" << std::endl;
    for (const auto& usage : node_usage) {
        std::cout << "    - " << usage.first << ": " << usage.second << " requests" << std::endl;
    }
    
    // Get enhanced statistics
    auto stats = engine.getStats();
    std::cout << "Enhanced engine statistics:" << std::endl;
    std::cout << "  Total requests: " << stats.total_requests << std::endl;
    std::cout << "  Successful requests: " << stats.successful_requests << std::endl;
    std::cout << "  Failed requests: " << stats.failed_requests << std::endl;
    std::cout << "  Average processing time: " << stats.average_processing_time_ms << " ms" << std::endl;
    std::cout << "  Total memory usage: " << stats.total_memory_usage_mb << " MB" << std::endl;
    std::cout << "  Active models: " << stats.active_models << std::endl;
    std::cout << "  Active compute nodes: " << stats.active_compute_nodes << std::endl;
    std::cout << "  Overall GPU utilization: " << stats.overall_gpu_utilization << std::endl;
    std::cout << "  Overall memory utilization: " << stats.overall_memory_utilization << std::endl;
    
    // Test load balancing
    std::cout << "Testing load balancing..." << std::endl;
    for (int i = 0; i < 5; ++i) {
        cognisynapse::EnhancedInferenceRequest request;
        request.id = "balance_test_" + std::to_string(i);
        request.model_id = "gpt-3.5-turbo";
        request.prompt = "Load balancing test " + std::to_string(i);
        request.max_tokens = 30;
        
        std::string best_node = engine.selectBestComputeNode(request);
        std::cout << "  Request " << request.id << " -> Node: " << best_node << std::endl;
    }
    
    // Get detailed status
    auto status = engine.getStatus();
    std::cout << "Enhanced engine status (JSON):" << std::endl;
    std::cout << status.dump(2) << std::endl;
    
    // Test model management
    std::cout << "Testing model management..." << std::endl;
    if (engine.loadModel("test-model", "/path/to/test/model")) {
        std::cout << "  ✅ Test model loaded successfully" << std::endl;
        
        auto updated_models = engine.getLoadedModels();
        std::cout << "  Total models after loading: " << updated_models.size() << std::endl;
        
        if (engine.unloadModel("test-model")) {
            std::cout << "  ✅ Test model unloaded successfully" << std::endl;
        } else {
            std::cout << "  ❌ Failed to unload test model" << std::endl;
        }
    } else {
        std::cout << "  ❌ Failed to load test model" << std::endl;
    }
    
    // Shutdown engine
    std::cout << "Shutting down enhanced engine..." << std::endl;
    engine.shutdown();
    
    std::cout << "=== Enhanced Engine Test Complete ===" << std::endl;
    return 0;
}
