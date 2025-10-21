#include "python_api.h"
#include <spdlog/spdlog.h>
#include <stdexcept>

namespace cogniware {

PythonAPI& PythonAPI::getInstance() {
    static PythonAPI instance;
    return instance;
}

bool PythonAPI::initialize() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (initialized_) {
        return true;
    }
    
    if (!initializePython()) {
        spdlog::error("Failed to initialize Python");
        return false;
    }
    
    if (!importModule("cognidream_platform_py")) {
        spdlog::error("Failed to import cognidream_platform_py module");
        return false;
    }
    
    initialized_ = true;
    return true;
}

void PythonAPI::shutdown() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!initialized_) {
        return;
    }
    
    // Unload all models
    for (const auto& [modelId, model] : loadedModels_) {
        unloadModel(modelId);
    }
    loadedModels_.clear();
    
    // Clean up Python
    cleanupPython();
    initialized_ = false;
}

bool PythonAPI::loadModel(const std::string& modelId, const std::string& modelPath) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!initialized_) {
        spdlog::error("Python API not initialized");
        return false;
    }
    
    try {
        PyObject* loadModelFunc = PyObject_GetAttrString(cognidreamModule_, "load_model");
        if (!loadModelFunc) {
            spdlog::error("Failed to get load_model function");
            return false;
        }
        
        PyObject* args = Py_BuildValue("(ss)", modelId.c_str(), modelPath.c_str());
        if (!args) {
            Py_DECREF(loadModelFunc);
            spdlog::error("Failed to build arguments");
            return false;
        }
        
        PyObject* result = PyObject_CallObject(loadModelFunc, args);
        Py_DECREF(args);
        Py_DECREF(loadModelFunc);
        
        if (!result) {
            spdlog::error("Failed to load model: {}", modelId);
            return false;
        }
        
        loadedModels_[modelId] = result;
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Error loading model: {}", e.what());
        return false;
    }
}

bool PythonAPI::unloadModel(const std::string& modelId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = loadedModels_.find(modelId);
    if (it == loadedModels_.end()) {
        return false;
    }
    
    try {
        PyObject* unloadModelFunc = PyObject_GetAttrString(cognidreamModule_, "unload_model");
        if (!unloadModelFunc) {
            spdlog::error("Failed to get unload_model function");
            return false;
        }
        
        PyObject* args = Py_BuildValue("(s)", modelId.c_str());
        if (!args) {
            Py_DECREF(unloadModelFunc);
            spdlog::error("Failed to build arguments");
            return false;
        }
        
        PyObject* result = PyObject_CallObject(unloadModelFunc, args);
        Py_DECREF(args);
        Py_DECREF(unloadModelFunc);
        
        if (!result) {
            spdlog::error("Failed to unload model: {}", modelId);
            return false;
        }
        
        Py_DECREF(result);
        loadedModels_.erase(it);
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Error unloading model: {}", e.what());
        return false;
    }
}

bool PythonAPI::isModelLoaded(const std::string& modelId) const {
    std::lock_guard<std::mutex> lock(mutex_);
    return loadedModels_.find(modelId) != loadedModels_.end();
}

InferenceResponse PythonAPI::runInference(const std::string& modelId, const InferenceRequest& request) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!initialized_ || !isModelLoaded(modelId)) {
        return InferenceResponse();
    }
    
    try {
        PyObject* inferenceFunc = PyObject_GetAttrString(cognidreamModule_, "run_inference");
        if (!inferenceFunc) {
            spdlog::error("Failed to get run_inference function");
            return InferenceResponse();
        }
        
        // Create Python dictionary for request parameters
        PyObject* params = createPythonDict(request.parameters);
        if (!params) {
            Py_DECREF(inferenceFunc);
            spdlog::error("Failed to create parameters dictionary");
            return InferenceResponse();
        }
        
        // Create Python list for input data
        PyObject* inputData = createPythonList(request.inputData);
        if (!inputData) {
            Py_DECREF(params);
            Py_DECREF(inferenceFunc);
            spdlog::error("Failed to create input data list");
            return InferenceResponse();
        }
        
        PyObject* args = Py_BuildValue("(ssOiOiOf)",
                                     modelId.c_str(),
                                     request.requestId.c_str(),
                                     inputData,
                                     request.requireConfidence,
                                     request.requireEmbeddings,
                                     request.maxTokens,
                                     request.temperature);
        if (!args) {
            Py_DECREF(inputData);
            Py_DECREF(params);
            Py_DECREF(inferenceFunc);
            spdlog::error("Failed to build arguments");
            return InferenceResponse();
        }
        
        PyObject* result = PyObject_CallObject(inferenceFunc, args);
        Py_DECREF(args);
        Py_DECREF(inputData);
        Py_DECREF(params);
        Py_DECREF(inferenceFunc);
        
        if (!result) {
            spdlog::error("Failed to run inference for model: {}", modelId);
            return InferenceResponse();
        }
        
        // Parse response
        InferenceResponse response;
        response.requestId = request.requestId;
        response.modelId = modelId;
        
        PyObject* outputData = PyObject_GetAttrString(result, "output_data");
        if (outputData) {
            response.outputData = parsePythonList(outputData);
            Py_DECREF(outputData);
        }
        
        PyObject* confidence = PyObject_GetAttrString(result, "confidence");
        if (confidence) {
            response.confidence = PyFloat_AsDouble(confidence);
            Py_DECREF(confidence);
        }
        
        PyObject* embeddings = PyObject_GetAttrString(result, "embeddings");
        if (embeddings) {
            response.embeddings = parsePythonList(embeddings);
            Py_DECREF(embeddings);
        }
        
        PyObject* metadata = PyObject_GetAttrString(result, "metadata");
        if (metadata) {
            response.metadata = parsePythonDict(metadata);
            Py_DECREF(metadata);
        }
        
        PyObject* success = PyObject_GetAttrString(result, "success");
        if (success) {
            response.success = PyObject_IsTrue(success);
            Py_DECREF(success);
        }
        
        PyObject* errorMsg = PyObject_GetAttrString(result, "error_message");
        if (errorMsg) {
            response.errorMessage = PyUnicode_AsUTF8(errorMsg);
            Py_DECREF(errorMsg);
        }
        
        Py_DECREF(result);
        return response;
    } catch (const std::exception& e) {
        spdlog::error("Error running inference: {}", e.what());
        return InferenceResponse();
    }
}

bool PythonAPI::startAsyncInference(const std::string& modelId, const InferenceRequest& request,
                                  std::function<void(const InferenceResponse&)> callback) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!initialized_ || !isModelLoaded(modelId)) {
        return false;
    }
    
    try {
        PyObject* asyncInferenceFunc = PyObject_GetAttrString(cognidreamModule_, "start_async_inference");
        if (!asyncInferenceFunc) {
            spdlog::error("Failed to get start_async_inference function");
            return false;
        }
        
        // Create Python dictionary for request parameters
        PyObject* params = createPythonDict(request.parameters);
        if (!params) {
            Py_DECREF(asyncInferenceFunc);
            spdlog::error("Failed to create parameters dictionary");
            return false;
        }
        
        // Create Python list for input data
        PyObject* inputData = createPythonList(request.inputData);
        if (!inputData) {
            Py_DECREF(params);
            Py_DECREF(asyncInferenceFunc);
            spdlog::error("Failed to create input data list");
            return false;
        }
        
        PyObject* args = Py_BuildValue("(ssOiOiOf)",
                                     modelId.c_str(),
                                     request.requestId.c_str(),
                                     inputData,
                                     request.requireConfidence,
                                     request.requireEmbeddings,
                                     request.maxTokens,
                                     request.temperature);
        if (!args) {
            Py_DECREF(inputData);
            Py_DECREF(params);
            Py_DECREF(asyncInferenceFunc);
            spdlog::error("Failed to build arguments");
            return false;
        }
        
        PyObject* result = PyObject_CallObject(asyncInferenceFunc, args);
        Py_DECREF(args);
        Py_DECREF(inputData);
        Py_DECREF(params);
        Py_DECREF(asyncInferenceFunc);
        
        if (!result) {
            spdlog::error("Failed to start async inference for model: {}", modelId);
            return false;
        }
        
        Py_DECREF(result);
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Error starting async inference: {}", e.what());
        return false;
    }
}

bool PythonAPI::cancelAsyncInference(const std::string& modelId, const std::string& requestId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!initialized_ || !isModelLoaded(modelId)) {
        return false;
    }
    
    try {
        PyObject* cancelFunc = PyObject_GetAttrString(cognidreamModule_, "cancel_async_inference");
        if (!cancelFunc) {
            spdlog::error("Failed to get cancel_async_inference function");
            return false;
        }
        
        PyObject* args = Py_BuildValue("(ss)", modelId.c_str(), requestId.c_str());
        if (!args) {
            Py_DECREF(cancelFunc);
            spdlog::error("Failed to build arguments");
            return false;
        }
        
        PyObject* result = PyObject_CallObject(cancelFunc, args);
        Py_DECREF(args);
        Py_DECREF(cancelFunc);
        
        if (!result) {
            spdlog::error("Failed to cancel async inference for model: {}", modelId);
            return false;
        }
        
        bool success = PyObject_IsTrue(result);
        Py_DECREF(result);
        return success;
    } catch (const std::exception& e) {
        spdlog::error("Error canceling async inference: {}", e.what());
        return false;
    }
}

TrainingResponse PythonAPI::trainModel(const std::string& modelId, const TrainingRequest& request) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!initialized_ || !isModelLoaded(modelId)) {
        return TrainingResponse();
    }
    
    try {
        PyObject* trainFunc = PyObject_GetAttrString(cognidreamModule_, "train_model");
        if (!trainFunc) {
            spdlog::error("Failed to get train_model function");
            return TrainingResponse();
        }
        
        // Create Python lists for training and validation data
        PyObject* trainingData = createPythonList(request.trainingData);
        PyObject* validationData = createPythonList(request.validationData);
        PyObject* params = createPythonDict(request.parameters);
        
        if (!trainingData || !validationData || !params) {
            if (trainingData) Py_DECREF(trainingData);
            if (validationData) Py_DECREF(validationData);
            if (params) Py_DECREF(params);
            Py_DECREF(trainFunc);
            spdlog::error("Failed to create training data structures");
            return TrainingResponse();
        }
        
        PyObject* args = Py_BuildValue("(ssOOOifss)",
                                     modelId.c_str(),
                                     request.requestId.c_str(),
                                     trainingData,
                                     validationData,
                                     params,
                                     request.epochs,
                                     request.learningRate,
                                     request.optimizer.c_str(),
                                     request.lossFunction.c_str());
        if (!args) {
            Py_DECREF(trainingData);
            Py_DECREF(validationData);
            Py_DECREF(params);
            Py_DECREF(trainFunc);
            spdlog::error("Failed to build arguments");
            return TrainingResponse();
        }
        
        PyObject* result = PyObject_CallObject(trainFunc, args);
        Py_DECREF(args);
        Py_DECREF(trainingData);
        Py_DECREF(validationData);
        Py_DECREF(params);
        Py_DECREF(trainFunc);
        
        if (!result) {
            spdlog::error("Failed to train model: {}", modelId);
            return TrainingResponse();
        }
        
        // Parse response
        TrainingResponse response;
        response.requestId = request.requestId;
        response.modelId = modelId;
        
        PyObject* finalLoss = PyObject_GetAttrString(result, "final_loss");
        if (finalLoss) {
            response.finalLoss = PyFloat_AsDouble(finalLoss);
            Py_DECREF(finalLoss);
        }
        
        PyObject* metrics = PyObject_GetAttrString(result, "metrics");
        if (metrics) {
            response.metrics = parsePythonDict(metrics);
            Py_DECREF(metrics);
        }
        
        PyObject* success = PyObject_GetAttrString(result, "success");
        if (success) {
            response.success = PyObject_IsTrue(success);
            Py_DECREF(success);
        }
        
        PyObject* errorMsg = PyObject_GetAttrString(result, "error_message");
        if (errorMsg) {
            response.errorMessage = PyUnicode_AsUTF8(errorMsg);
            Py_DECREF(errorMsg);
        }
        
        Py_DECREF(result);
        return response;
    } catch (const std::exception& e) {
        spdlog::error("Error training model: {}", e.what());
        return TrainingResponse();
    }
}

bool PythonAPI::startAsyncTraining(const std::string& modelId, const TrainingRequest& request,
                                 std::function<void(const TrainingResponse&)> callback) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!initialized_ || !isModelLoaded(modelId)) {
        return false;
    }
    
    try {
        PyObject* asyncTrainFunc = PyObject_GetAttrString(cognidreamModule_, "start_async_training");
        if (!asyncTrainFunc) {
            spdlog::error("Failed to get start_async_training function");
            return false;
        }
        
        // Create Python lists for training and validation data
        PyObject* trainingData = createPythonList(request.trainingData);
        PyObject* validationData = createPythonList(request.validationData);
        PyObject* params = createPythonDict(request.parameters);
        
        if (!trainingData || !validationData || !params) {
            if (trainingData) Py_DECREF(trainingData);
            if (validationData) Py_DECREF(validationData);
            if (params) Py_DECREF(params);
            Py_DECREF(asyncTrainFunc);
            spdlog::error("Failed to create training data structures");
            return false;
        }
        
        PyObject* args = Py_BuildValue("(ssOOOifss)",
                                     modelId.c_str(),
                                     request.requestId.c_str(),
                                     trainingData,
                                     validationData,
                                     params,
                                     request.epochs,
                                     request.learningRate,
                                     request.optimizer.c_str(),
                                     request.lossFunction.c_str());
        if (!args) {
            Py_DECREF(trainingData);
            Py_DECREF(validationData);
            Py_DECREF(params);
            Py_DECREF(asyncTrainFunc);
            spdlog::error("Failed to build arguments");
            return false;
        }
        
        PyObject* result = PyObject_CallObject(asyncTrainFunc, args);
        Py_DECREF(args);
        Py_DECREF(trainingData);
        Py_DECREF(validationData);
        Py_DECREF(params);
        Py_DECREF(asyncTrainFunc);
        
        if (!result) {
            spdlog::error("Failed to start async training for model: {}", modelId);
            return false;
        }
        
        Py_DECREF(result);
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Error starting async training: {}", e.what());
        return false;
    }
}

bool PythonAPI::cancelAsyncTraining(const std::string& modelId, const std::string& requestId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!initialized_ || !isModelLoaded(modelId)) {
        return false;
    }
    
    try {
        PyObject* cancelFunc = PyObject_GetAttrString(cognidreamModule_, "cancel_async_training");
        if (!cancelFunc) {
            spdlog::error("Failed to get cancel_async_training function");
            return false;
        }
        
        PyObject* args = Py_BuildValue("(ss)", modelId.c_str(), requestId.c_str());
        if (!args) {
            Py_DECREF(cancelFunc);
            spdlog::error("Failed to build arguments");
            return false;
        }
        
        PyObject* result = PyObject_CallObject(cancelFunc, args);
        Py_DECREF(args);
        Py_DECREF(cancelFunc);
        
        if (!result) {
            spdlog::error("Failed to cancel async training for model: {}", modelId);
            return false;
        }
        
        bool success = PyObject_IsTrue(result);
        Py_DECREF(result);
        return success;
    } catch (const std::exception& e) {
        spdlog::error("Error canceling async training: {}", e.what());
        return false;
    }
}

bool PythonAPI::updateModelConfig(const std::string& modelId, const ModelConfig& config) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!initialized_ || !isModelLoaded(modelId)) {
        return false;
    }
    
    try {
        PyObject* updateConfigFunc = PyObject_GetAttrString(cognidreamModule_, "update_model_config");
        if (!updateConfigFunc) {
            spdlog::error("Failed to get update_model_config function");
            return false;
        }
        
        PyObject* params = createPythonDict(config.parameters);
        if (!params) {
            Py_DECREF(updateConfigFunc);
            spdlog::error("Failed to create parameters dictionary");
            return false;
        }
        
        PyObject* args = Py_BuildValue("(sssOifsi)",
                                     modelId.c_str(),
                                     config.modelType.c_str(),
                                     config.modelPath.c_str(),
                                     params,
                                     config.enableGpu,
                                     config.maxBatchSize,
                                     config.memoryLimit,
                                     config.quantizationType.c_str(),
                                     config.enableDynamicBatching);
        if (!args) {
            Py_DECREF(params);
            Py_DECREF(updateConfigFunc);
            spdlog::error("Failed to build arguments");
            return false;
        }
        
        PyObject* result = PyObject_CallObject(updateConfigFunc, args);
        Py_DECREF(args);
        Py_DECREF(params);
        Py_DECREF(updateConfigFunc);
        
        if (!result) {
            spdlog::error("Failed to update model config for model: {}", modelId);
            return false;
        }
        
        bool success = PyObject_IsTrue(result);
        Py_DECREF(result);
        return success;
    } catch (const std::exception& e) {
        spdlog::error("Error updating model config: {}", e.what());
        return false;
    }
}

ModelConfig PythonAPI::getModelConfig(const std::string& modelId) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!initialized_ || !isModelLoaded(modelId)) {
        return ModelConfig();
    }
    
    try {
        PyObject* getConfigFunc = PyObject_GetAttrString(cognidreamModule_, "get_model_config");
        if (!getConfigFunc) {
            spdlog::error("Failed to get get_model_config function");
            return ModelConfig();
        }
        
        PyObject* args = Py_BuildValue("(s)", modelId.c_str());
        if (!args) {
            Py_DECREF(getConfigFunc);
            spdlog::error("Failed to build arguments");
            return ModelConfig();
        }
        
        PyObject* result = PyObject_CallObject(getConfigFunc, args);
        Py_DECREF(args);
        Py_DECREF(getConfigFunc);
        
        if (!result) {
            spdlog::error("Failed to get model config for model: {}", modelId);
            return ModelConfig();
        }
        
        ModelConfig config;
        config.modelId = modelId;
        
        PyObject* modelType = PyObject_GetAttrString(result, "model_type");
        if (modelType) {
            config.modelType = PyUnicode_AsUTF8(modelType);
            Py_DECREF(modelType);
        }
        
        PyObject* modelPath = PyObject_GetAttrString(result, "model_path");
        if (modelPath) {
            config.modelPath = PyUnicode_AsUTF8(modelPath);
            Py_DECREF(modelPath);
        }
        
        PyObject* params = PyObject_GetAttrString(result, "parameters");
        if (params) {
            config.parameters = parsePythonDict(params);
            Py_DECREF(params);
        }
        
        PyObject* enableGpu = PyObject_GetAttrString(result, "enable_gpu");
        if (enableGpu) {
            config.enableGpu = PyObject_IsTrue(enableGpu);
            Py_DECREF(enableGpu);
        }
        
        PyObject* maxBatchSize = PyObject_GetAttrString(result, "max_batch_size");
        if (maxBatchSize) {
            config.maxBatchSize = PyLong_AsLong(maxBatchSize);
            Py_DECREF(maxBatchSize);
        }
        
        PyObject* memoryLimit = PyObject_GetAttrString(result, "memory_limit");
        if (memoryLimit) {
            config.memoryLimit = PyFloat_AsDouble(memoryLimit);
            Py_DECREF(memoryLimit);
        }
        
        PyObject* quantizationType = PyObject_GetAttrString(result, "quantization_type");
        if (quantizationType) {
            config.quantizationType = PyUnicode_AsUTF8(quantizationType);
            Py_DECREF(quantizationType);
        }
        
        PyObject* enableDynamicBatching = PyObject_GetAttrString(result, "enable_dynamic_batching");
        if (enableDynamicBatching) {
            config.enableDynamicBatching = PyObject_IsTrue(enableDynamicBatching);
            Py_DECREF(enableDynamicBatching);
        }
        
        Py_DECREF(result);
        return config;
    } catch (const std::exception& e) {
        spdlog::error("Error getting model config: {}", e.what());
        return ModelConfig();
    }
}

std::vector<std::string> PythonAPI::getAvailableModels() const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!initialized_) {
        return std::vector<std::string>();
    }
    
    try {
        PyObject* getModelsFunc = PyObject_GetAttrString(cognidreamModule_, "get_available_models");
        if (!getModelsFunc) {
            spdlog::error("Failed to get get_available_models function");
            return std::vector<std::string>();
        }
        
        PyObject* result = PyObject_CallObject(getModelsFunc, nullptr);
        Py_DECREF(getModelsFunc);
        
        if (!result) {
            spdlog::error("Failed to get available models");
            return std::vector<std::string>();
        }
        
        std::vector<std::string> models;
        Py_ssize_t size = PyList_Size(result);
        for (Py_ssize_t i = 0; i < size; ++i) {
            PyObject* item = PyList_GetItem(result, i);
            if (item) {
                models.push_back(PyUnicode_AsUTF8(item));
            }
        }
        
        Py_DECREF(result);
        return models;
    } catch (const std::exception& e) {
        spdlog::error("Error getting available models: {}", e.what());
        return std::vector<std::string>();
    }
}

bool PythonAPI::allocateResources(const std::string& modelId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!initialized_ || !isModelLoaded(modelId)) {
        return false;
    }
    
    try {
        PyObject* allocateFunc = PyObject_GetAttrString(cognidreamModule_, "allocate_resources");
        if (!allocateFunc) {
            spdlog::error("Failed to get allocate_resources function");
            return false;
        }
        
        PyObject* args = Py_BuildValue("(s)", modelId.c_str());
        if (!args) {
            Py_DECREF(allocateFunc);
            spdlog::error("Failed to build arguments");
            return false;
        }
        
        PyObject* result = PyObject_CallObject(allocateFunc, args);
        Py_DECREF(args);
        Py_DECREF(allocateFunc);
        
        if (!result) {
            spdlog::error("Failed to allocate resources for model: {}", modelId);
            return false;
        }
        
        bool success = PyObject_IsTrue(result);
        Py_DECREF(result);
        return success;
    } catch (const std::exception& e) {
        spdlog::error("Error allocating resources: {}", e.what());
        return false;
    }
}

bool PythonAPI::releaseResources(const std::string& modelId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!initialized_ || !isModelLoaded(modelId)) {
        return false;
    }
    
    try {
        PyObject* releaseFunc = PyObject_GetAttrString(cognidreamModule_, "release_resources");
        if (!releaseFunc) {
            spdlog::error("Failed to get release_resources function");
            return false;
        }
        
        PyObject* args = Py_BuildValue("(s)", modelId.c_str());
        if (!args) {
            Py_DECREF(releaseFunc);
            spdlog::error("Failed to build arguments");
            return false;
        }
        
        PyObject* result = PyObject_CallObject(releaseFunc, args);
        Py_DECREF(args);
        Py_DECREF(releaseFunc);
        
        if (!result) {
            spdlog::error("Failed to release resources for model: {}", modelId);
            return false;
        }
        
        bool success = PyObject_IsTrue(result);
        Py_DECREF(result);
        return success;
    } catch (const std::exception& e) {
        spdlog::error("Error releasing resources: {}", e.what());
        return false;
    }
}

std::map<std::string, float> PythonAPI::getResourceUtilization(const std::string& modelId) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!initialized_ || !isModelLoaded(modelId)) {
        return std::map<std::string, float>();
    }
    
    try {
        PyObject* getUtilFunc = PyObject_GetAttrString(cognidreamModule_, "get_resource_utilization");
        if (!getUtilFunc) {
            spdlog::error("Failed to get get_resource_utilization function");
            return std::map<std::string, float>();
        }
        
        PyObject* args = Py_BuildValue("(s)", modelId.c_str());
        if (!args) {
            Py_DECREF(getUtilFunc);
            spdlog::error("Failed to build arguments");
            return std::map<std::string, float>();
        }
        
        PyObject* result = PyObject_CallObject(getUtilFunc, args);
        Py_DECREF(args);
        Py_DECREF(getUtilFunc);
        
        if (!result) {
            spdlog::error("Failed to get resource utilization for model: {}", modelId);
            return std::map<std::string, float>();
        }
        
        std::map<std::string, float> utilization = parsePythonDict(result);
        Py_DECREF(result);
        return utilization;
    } catch (const std::exception& e) {
        spdlog::error("Error getting resource utilization: {}", e.what());
        return std::map<std::string, float>();
    }
}

void PythonAPI::enableMonitoring(bool enable) {
    std::lock_guard<std::mutex> lock(mutex_);
    monitoringEnabled_ = enable;
}

void PythonAPI::setStatusCallback(std::function<void(const std::string&, const ModelStatus&)> callback) {
    std::lock_guard<std::mutex> lock(mutex_);
    statusCallback_ = callback;
}

void PythonAPI::printStats() const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    spdlog::info("Python API Stats:");
    spdlog::info("  Initialized: {}", initialized_);
    spdlog::info("  Loaded Models: {}", loadedModels_.size());
    spdlog::info("  Monitoring Enabled: {}", monitoringEnabled_);
    
    for (const auto& [modelId, _] : loadedModels_) {
        auto utilization = getResourceUtilization(modelId);
        spdlog::info("  Model {} Resource Utilization:", modelId);
        for (const auto& [resource, value] : utilization) {
            spdlog::info("    {}: {:.2f}%", resource, value * 100.0f);
        }
    }
}

bool PythonAPI::initializePython() {
    Py_Initialize();
    if (PyErr_Occurred()) {
        spdlog::error("Failed to initialize Python");
        return false;
    }
    
    mainModule_ = PyImport_AddModule("__main__");
    if (!mainModule_) {
        spdlog::error("Failed to get main module");
        return false;
    }
    
    return true;
}

void PythonAPI::cleanupPython() {
    if (cognidreamModule_) {
        Py_DECREF(cognidreamModule_);
        cognidreamModule_ = nullptr;
    }
    
    if (mainModule_) {
        Py_DECREF(mainModule_);
        mainModule_ = nullptr;
    }
    
    Py_Finalize();
}

bool PythonAPI::importModule(const std::string& moduleName) {
    PyObject* module = PyImport_ImportModule(moduleName.c_str());
    if (!module) {
        spdlog::error("Failed to import module: {}", moduleName);
        return false;
    }
    
    if (moduleName == "cognidream_platform_py") {
        cognidreamModule_ = module;
    } else {
        Py_DECREF(module);
    }
    
    return true;
}

PyObject* PythonAPI::createPythonDict(const std::map<std::string, std::string>& params) {
    PyObject* dict = PyDict_New();
    if (!dict) {
        return nullptr;
    }
    
    for (const auto& [key, value] : params) {
        PyObject* pyKey = PyUnicode_FromString(key.c_str());
        PyObject* pyValue = PyUnicode_FromString(value.c_str());
        
        if (!pyKey || !pyValue) {
            if (pyKey) Py_DECREF(pyKey);
            if (pyValue) Py_DECREF(pyValue);
            Py_DECREF(dict);
            return nullptr;
        }
        
        if (PyDict_SetItem(dict, pyKey, pyValue) < 0) {
            Py_DECREF(pyKey);
            Py_DECREF(pyValue);
            Py_DECREF(dict);
            return nullptr;
        }
        
        Py_DECREF(pyKey);
        Py_DECREF(pyValue);
    }
    
    return dict;
}

std::map<std::string, std::string> PythonAPI::parsePythonDict(PyObject* dict) {
    std::map<std::string, std::string> result;
    
    if (!dict || !PyDict_Check(dict)) {
        return result;
    }
    
    PyObject* key;
    PyObject* value;
    Py_ssize_t pos = 0;
    
    while (PyDict_Next(dict, &pos, &key, &value)) {
        const char* keyStr = PyUnicode_AsUTF8(key);
        const char* valueStr = PyUnicode_AsUTF8(value);
        
        if (keyStr && valueStr) {
            result[keyStr] = valueStr;
        }
    }
    
    return result;
}

std::vector<float> PythonAPI::parsePythonList(PyObject* list) {
    std::vector<float> result;
    
    if (!list || !PyList_Check(list)) {
        return result;
    }
    
    Py_ssize_t size = PyList_Size(list);
    result.reserve(size);
    
    for (Py_ssize_t i = 0; i < size; ++i) {
        PyObject* item = PyList_GetItem(list, i);
        if (item && PyFloat_Check(item)) {
            result.push_back(PyFloat_AsDouble(item));
        }
    }
    
    return result;
}

PyObject* PythonAPI::createPythonList(const std::vector<float>& data) {
    PyObject* list = PyList_New(data.size());
    if (!list) {
        return nullptr;
    }
    
    for (size_t i = 0; i < data.size(); ++i) {
        PyObject* item = PyFloat_FromDouble(data[i]);
        if (!item) {
            Py_DECREF(list);
            return nullptr;
        }
        
        PyList_SetItem(list, i, item);
    }
    
    return list;
}

bool PythonAPI::checkPythonError() {
    if (PyErr_Occurred()) {
        PyObject* type;
        PyObject* value;
        PyObject* traceback;
        
        PyErr_Fetch(&type, &value, &traceback);
        
        if (value) {
            const char* errorMsg = PyUnicode_AsUTF8(value);
            if (errorMsg) {
                spdlog::error("Python error: {}", errorMsg);
            }
            Py_DECREF(value);
        }
        
        if (type) {
            Py_DECREF(type);
        }
        
        if (traceback) {
            Py_DECREF(traceback);
        }
        
        return true;
    }
    
    return false;
}

} // namespace cogniware 