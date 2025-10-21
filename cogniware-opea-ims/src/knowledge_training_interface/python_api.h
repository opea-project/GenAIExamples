#pragma once

#include <string>
#include <vector>
#include <map>
#include <memory>
#include <functional>
#include <Python.h>
#include "../common_interfaces/model_interface.h"

namespace cogniware {

class PythonAPI {
public:
    static PythonAPI& getInstance();

    // Initialization and cleanup
    bool initialize();
    void shutdown();

    // Model management
    bool loadModel(const std::string& modelId, const std::string& modelPath);
    bool unloadModel(const std::string& modelId);
    bool isModelLoaded(const std::string& modelId) const;

    // Inference
    InferenceResponse runInference(const std::string& modelId, const InferenceRequest& request);
    bool startAsyncInference(const std::string& modelId, const InferenceRequest& request,
                            std::function<void(const InferenceResponse&)> callback);
    bool cancelAsyncInference(const std::string& modelId, const std::string& requestId);

    // Training
    TrainingResponse trainModel(const std::string& modelId, const TrainingRequest& request);
    bool startAsyncTraining(const std::string& modelId, const TrainingRequest& request,
                           std::function<void(const TrainingResponse&)> callback);
    bool cancelAsyncTraining(const std::string& modelId, const std::string& requestId);

    // Model configuration
    bool updateModelConfig(const std::string& modelId, const ModelConfig& config);
    ModelConfig getModelConfig(const std::string& modelId) const;
    std::vector<std::string> getAvailableModels() const;

    // Resource management
    bool allocateResources(const std::string& modelId);
    bool releaseResources(const std::string& modelId);
    std::map<std::string, float> getResourceUtilization(const std::string& modelId) const;

    // Monitoring
    void enableMonitoring(bool enable);
    void setStatusCallback(std::function<void(const std::string&, const ModelStatus&)> callback);
    void printStats() const;

private:
    PythonAPI() = default;
    ~PythonAPI() = default;
    PythonAPI(const PythonAPI&) = delete;
    PythonAPI& operator=(const PythonAPI&) = delete;

    // Internal methods
    bool initializePython();
    void cleanupPython();
    bool importModule(const std::string& moduleName);
    PyObject* createPythonDict(const std::map<std::string, std::string>& params);
    std::map<std::string, std::string> parsePythonDict(PyObject* dict);
    std::vector<float> parsePythonList(PyObject* list);
    PyObject* createPythonList(const std::vector<float>& data);
    bool checkPythonError();

    // Member variables
    std::mutex mutex_;
    std::atomic<bool> initialized_{false};
    PyObject* mainModule_{nullptr};
    PyObject* cognidreamModule_{nullptr};
    std::map<std::string, PyObject*> loadedModels_;
    std::atomic<bool> monitoringEnabled_{false};
    std::function<void(const std::string&, const ModelStatus&)> statusCallback_;
};

} // namespace cogniware 