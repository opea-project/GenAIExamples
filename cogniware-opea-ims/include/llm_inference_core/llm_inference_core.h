#pragma once

#include "llm_inference_core/inference/inference_engine.h"
#include "llm_inference_core/model/model_manager.h"
#include "llm_inference_core/monitoring/resource_monitor.h"
#include "llm_inference_core/routing/fast_router_core.h"
#include <memory>
#include <string>
#include <vector>

namespace cogniware {

class LLMInferenceCore {
public:
    static LLMInferenceCore& getInstance();

    // Delete copy constructor and assignment operator
    LLMInferenceCore(const LLMInferenceCore&) = delete;
    LLMInferenceCore& operator=(const LLMInferenceCore&) = delete;

    // Initialization
    bool initialize();
    void shutdown();
    
    // Model management
    bool loadModel(const ModelConfig& config);
    bool unloadModel(const std::string& modelId);
    bool isModelLoaded(const std::string& modelId) const;
    
    // Inference
    InferenceResponse processRequest(const InferenceRequest& request);
    bool streamResponse(const InferenceRequest& request,
                       std::function<void(const std::string&)> callback);
    
    // Routing
    std::string routeQuery(const std::string& query);
    
    // Monitoring
    void setResourceAlertCallback(ResourceMonitor::ResourceAlertCallback callback);
    GPUStats getGPUStats() const;
    ModelStats getModelStats(const std::string& modelId) const;
    
    // Error handling
    const char* getLastError() const;
    void clearLastError();

private:
    LLMInferenceCore();
    ~LLMInferenceCore();

    // Component references
    InferenceEngine& inferenceEngine_;
    ModelManager& modelManager_;
    ResourceMonitor& resourceMonitor_;
    FastRouterCore& routerCore_;
    
    // Error handling
    std::string lastError_;
};

} // namespace cogniware 