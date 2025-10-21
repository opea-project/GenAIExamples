#include "llm_inference_core/llm_inference_core.h"

namespace cogniware {

LLMInferenceCore& LLMInferenceCore::getInstance() {
    static LLMInferenceCore instance;
    return instance;
}

LLMInferenceCore::LLMInferenceCore()
    : inferenceEngine_(InferenceEngine::getInstance())
    , modelManager_(ModelManager::getInstance())
    , resourceMonitor_(ResourceMonitor::getInstance())
    , routerCore_(FastRouterCore::getInstance()) {
}

LLMInferenceCore::~LLMInferenceCore() {
    shutdown();
}

bool LLMInferenceCore::initialize() {
    // Initialize components
    if (!inferenceEngine_.initialize()) {
        lastError_ = "Failed to initialize inference engine: " +
                    std::string(inferenceEngine_.getLastError());
        return false;
    }
    
    if (!resourceMonitor_.startMonitoring()) {
        lastError_ = "Failed to start resource monitoring: " +
                    std::string(resourceMonitor_.getLastError());
        return false;
    }
    
    return true;
}

void LLMInferenceCore::shutdown() {
    // Shutdown components
    inferenceEngine_.shutdown();
    resourceMonitor_.stopMonitoring();
}

bool LLMInferenceCore::loadModel(const ModelConfig& config) {
    // Check if model can be loaded
    if (!modelManager_.canLoadModel(config)) {
        lastError_ = "Insufficient resources to load model: " + config.modelId;
        return false;
    }
    
    // Load model
    if (!inferenceEngine_.loadModel(config)) {
        lastError_ = "Failed to load model: " + std::string(inferenceEngine_.getLastError());
        return false;
    }
    
    // Create model profile for routing
    ModelProfile profile;
    profile.modelId = config.modelId;
    profile.confidence = 1.0f;
    profile.memoryUsage = 0;  // Will be updated by ModelManager
    profile.averageLatency = 0.0f;  // Will be updated by ModelManager
    
    // Add model profile to router
    if (!routerCore_.addModelProfile(profile)) {
        lastError_ = "Failed to add model profile: " + std::string(routerCore_.getLastError());
        inferenceEngine_.unloadModel(config.modelId);
        return false;
    }
    
    return true;
}

bool LLMInferenceCore::unloadModel(const std::string& modelId) {
    // Remove model profile from router
    if (!routerCore_.removeModelProfile(modelId)) {
        lastError_ = "Failed to remove model profile: " + std::string(routerCore_.getLastError());
        return false;
    }
    
    // Unload model
    if (!inferenceEngine_.unloadModel(modelId)) {
        lastError_ = "Failed to unload model: " + std::string(inferenceEngine_.getLastError());
        return false;
    }
    
    return true;
}

bool LLMInferenceCore::isModelLoaded(const std::string& modelId) const {
    return inferenceEngine_.isModelLoaded(modelId);
}

InferenceResponse LLMInferenceCore::processRequest(const InferenceRequest& request) {
    // Route query if model ID is not specified
    InferenceRequest processedRequest = request;
    if (processedRequest.modelId.empty()) {
        processedRequest.modelId = routeQuery(request.prompt);
        if (processedRequest.modelId.empty()) {
            InferenceResponse response;
            response.success = false;
            response.error = "Failed to route query: " + std::string(routerCore_.getLastError());
            return response;
        }
    }
    
    // Process request
    return inferenceEngine_.processRequest(processedRequest);
}

bool LLMInferenceCore::streamResponse(const InferenceRequest& request,
                                    std::function<void(const std::string&)> callback) {
    // Route query if model ID is not specified
    InferenceRequest processedRequest = request;
    if (processedRequest.modelId.empty()) {
        processedRequest.modelId = routeQuery(request.prompt);
        if (processedRequest.modelId.empty()) {
            lastError_ = "Failed to route query: " + std::string(routerCore_.getLastError());
            return false;
        }
    }
    
    // Stream response
    return inferenceEngine_.streamResponse(processedRequest, callback);
}

std::string LLMInferenceCore::routeQuery(const std::string& query) {
    return routerCore_.routeQuery(query);
}

void LLMInferenceCore::setResourceAlertCallback(ResourceMonitor::ResourceAlertCallback callback) {
    resourceMonitor_.setResourceAlertCallback(callback);
}

GPUStats LLMInferenceCore::getGPUStats() const {
    return resourceMonitor_.getGPUStats();
}

ModelStats LLMInferenceCore::getModelStats(const std::string& modelId) const {
    return inferenceEngine_.getModelStats(modelId);
}

const char* LLMInferenceCore::getLastError() const {
    return lastError_.c_str();
}

void LLMInferenceCore::clearLastError() {
    lastError_.clear();
}

} // namespace cogniware 