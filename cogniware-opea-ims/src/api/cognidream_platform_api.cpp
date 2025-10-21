#include "cognidream_platform_api.h"
#include "enhanced_driver.h"
#include <spdlog/spdlog.h>
#include <fstream>
#include <sstream>
#include <random>
#include <chrono>
#include <algorithm>

namespace cogniware {

CogniDreamPlatformAPI& CogniDreamPlatformAPI::getInstance() {
    static CogniDreamPlatformAPI instance;
    return instance;
}

bool CogniDreamPlatformAPI::initialize(const nlohmann::json& config) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (initialized_) {
        spdlog::warn("CogniDream Platform API already initialized");
        return true;
    }
    
    try {
        // Initialize enhanced driver
        driver_ = std::make_unique<EnhancedDriver>();
        
        EnhancedDriverConfig driverConfig;
        driverConfig.deviceId = config.value("device_id", 0);
        driverConfig.numStreams = config.value("num_streams", 4);
        driverConfig.monitoringInterval = config.value("monitoring_interval", 100);
        driverConfig.enableTensorCores = config.value("enable_tensor_cores", true);
        driverConfig.enableMixedPrecision = config.value("enable_mixed_precision", true);
        driverConfig.optimizationLevel = config.value("optimization_level", 2);
        
        if (!driver_->initialize(driverConfig)) {
            spdlog::error("Failed to initialize enhanced driver");
            return false;
        }
        
        // Start background threads
        running_ = true;
        requestProcessor_ = std::thread(&CogniDreamPlatformAPI::processRequests, this);
        metricsCollector_ = std::thread(&CogniDreamPlatformAPI::collectMetrics, this);
        
        initialized_ = true;
        spdlog::info("CogniDream Platform API initialized successfully");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize CogniDream Platform API: {}", e.what());
        return false;
    }
}

void CogniDreamPlatformAPI::shutdown() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!initialized_) return;
    
    running_ = false;
    
    // Stop background threads
    if (requestProcessor_.joinable()) {
        requestProcessor_.join();
    }
    if (metricsCollector_.joinable()) {
        metricsCollector_.join();
    }
    
    // Shutdown driver
    if (driver_) {
        driver_->shutdown();
        driver_.reset();
    }
    
    // Clear all data
    loadedModels_.clear();
    modelWeights_.clear();
    pendingInferences_.clear();
    pendingTraining_.clear();
    completedInferences_.clear();
    completedTraining_.clear();
    resourceAllocations_.clear();
    sessions_.clear();
    
    initialized_ = false;
    spdlog::info("CogniDream Platform API shutdown completed");
}

bool CogniDreamPlatformAPI::loadModel(const ModelConfig& config) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!initialized_) {
        setLastError("API not initialized");
        return false;
    }
    
    try {
        // Load model weights from file
        std::ifstream file(config.modelPath, std::ios::binary);
        if (!file.is_open()) {
            setLastError("Failed to open model file: " + config.modelPath);
            return false;
        }
        
        // Read model weights (simplified - in production, use proper model format)
        std::vector<float> weights;
        float weight;
        while (file.read(reinterpret_cast<char*>(&weight), sizeof(float))) {
            weights.push_back(weight);
        }
        
        loadedModels_[config.modelId] = config;
        modelWeights_[config.modelId] = weights;
        
        spdlog::info("Model loaded successfully: {}", config.modelId);
        return true;
        
    } catch (const std::exception& e) {
        setLastError("Failed to load model: " + std::string(e.what()));
        return false;
    }
}

bool CogniDreamPlatformAPI::unloadModel(const std::string& modelId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (loadedModels_.erase(modelId) > 0) {
        modelWeights_.erase(modelId);
        spdlog::info("Model unloaded: {}", modelId);
        return true;
    }
    
    return false;
}

InferenceResponse CogniDreamPlatformAPI::executeInference(const InferenceRequest& request) {
    InferenceResponse response;
    response.requestId = request.requestId;
    
    if (!validateRequest(request)) {
        response.success = false;
        response.errorMessage = getLastError();
        return response;
    }
    
    auto startTime = std::chrono::high_resolution_clock::now();
    
    try {
        // Convert input data to GPU format
        std::vector<float> flattenedInput;
        for (const auto& batch : request.inputData) {
            flattenedInput.insert(flattenedInput.end(), batch.begin(), batch.end());
        }
        
        // Allocate GPU memory
        float *d_input, *d_output;
        size_t inputSize = flattenedInput.size() * sizeof(float);
        size_t outputSize = request.batchSize * request.sequenceLength * sizeof(float);
        
        cudaMalloc(&d_input, inputSize);
        cudaMalloc(&d_output, outputSize);
        
        // Copy input to GPU
        cudaMemcpy(d_input, flattenedInput.data(), inputSize, cudaMemcpyHostToDevice);
        
        // Execute inference using enhanced driver
        bool success = driver_->executeMatrixMultiply(
            d_input, nullptr, d_output,
            request.batchSize, request.sequenceLength, request.sequenceLength,
            CUDA_R_32F, 1.0f, 0.0f, 0
        );
        
        if (success) {
            // Copy result back to host
            std::vector<float> outputData(outputSize / sizeof(float));
            cudaMemcpy(outputData.data(), d_output, outputSize, cudaMemcpyDeviceToHost);
            
            // Reshape output
            response.outputData.resize(request.batchSize);
            for (int i = 0; i < request.batchSize; ++i) {
                response.outputData[i].assign(
                    outputData.begin() + i * request.sequenceLength,
                    outputData.begin() + (i + 1) * request.sequenceLength
                );
            }
            
            response.success = true;
        } else {
            response.success = false;
            response.errorMessage = "Inference execution failed";
        }
        
        // Cleanup
        cudaFree(d_input);
        cudaFree(d_output);
        
    } catch (const std::exception& e) {
        response.success = false;
        response.errorMessage = "Inference error: " + std::string(e.what());
    }
    
    auto endTime = std::chrono::high_resolution_clock::now();
    response.inferenceTime = std::chrono::duration<float>(endTime - startTime).count();
    
    return response;
}

TrainingResponse CogniDreamPlatformAPI::executeTraining(const TrainingRequest& request) {
    TrainingResponse response;
    response.requestId = request.requestId;
    
    if (!validateRequest(request)) {
        response.success = false;
        response.errorMessage = getLastError();
        return response;
    }
    
    auto startTime = std::chrono::high_resolution_clock::now();
    
    try {
        // Convert training data to GPU format
        std::vector<float> flattenedData, flattenedLabels;
        for (const auto& batch : request.trainingData) {
            flattenedData.insert(flattenedData.end(), batch.begin(), batch.end());
        }
        for (const auto& batch : request.labels) {
            flattenedLabels.insert(flattenedLabels.end(), batch.begin(), batch.end());
        }
        
        // Allocate GPU memory
        float *d_data, *d_labels, *d_gradients, *d_params;
        size_t dataSize = flattenedData.size() * sizeof(float);
        size_t labelSize = flattenedLabels.size() * sizeof(float);
        size_t paramSize = dataSize; // Simplified
        
        cudaMalloc(&d_data, dataSize);
        cudaMalloc(&d_labels, labelSize);
        cudaMalloc(&d_gradients, dataSize);
        cudaMalloc(&d_params, paramSize);
        
        // Copy data to GPU
        cudaMemcpy(d_data, flattenedData.data(), dataSize, cudaMemcpyHostToDevice);
        cudaMemcpy(d_labels, flattenedLabels.data(), labelSize, cudaMemcpyHostToDevice);
        
        // Training loop
        response.lossHistory.resize(request.epochs);
        float currentLoss = 0.0f;
        
        for (int epoch = 0; epoch < request.epochs; ++epoch) {
            // Forward pass (simplified)
            driver_->executeMatrixMultiply(d_data, d_params, d_gradients, 
                request.batchSize, request.sequenceLength, request.sequenceLength,
                CUDA_R_32F, 1.0f, 0.0f, 0);
            
            // Compute loss
            driver_->executeLoss(&currentLoss, d_gradients, d_labels,
                request.batchSize, request.sequenceLength,
                request.lossFunction, CUDA_R_32F, 0);
            
            response.lossHistory[epoch] = currentLoss;
            
            // Backward pass and optimization (simplified)
            std::vector<float> m(paramSize / sizeof(float), 0.0f);
            std::vector<float> v(paramSize / sizeof(float), 0.0f);
            float *d_m, *d_v;
            cudaMalloc(&d_m, paramSize);
            cudaMalloc(&d_v, paramSize);
            cudaMemcpy(d_m, m.data(), paramSize, cudaMemcpyHostToDevice);
            cudaMemcpy(d_v, v.data(), paramSize, cudaMemcpyHostToDevice);
            
            driver_->executeOptimizer(d_params, d_gradients, d_m, d_v,
                paramSize / sizeof(float), request.learningRate, 0.9f, 0.999f, 1e-8f, epoch + 1,
                request.optimizer, CUDA_R_32F, 0);
            
            cudaFree(d_m);
            cudaFree(d_v);
        }
        
        response.finalLoss = currentLoss;
        response.success = true;
        
        // Cleanup
        cudaFree(d_data);
        cudaFree(d_labels);
        cudaFree(d_gradients);
        cudaFree(d_params);
        
    } catch (const std::exception& e) {
        response.success = false;
        response.errorMessage = "Training error: " + std::string(e.what());
    }
    
    auto endTime = std::chrono::high_resolution_clock::now();
    response.trainingTime = std::chrono::duration<float>(endTime - startTime).count();
    
    return response;
}

std::string CogniDreamPlatformAPI::createSession(const std::string& userId, const std::string& modelId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!isModelLoaded(modelId)) {
        setLastError("Model not loaded: " + modelId);
        return "";
    }
    
    // Generate session ID
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, 999999);
    std::string sessionId = userId + "_" + std::to_string(dis(gen));
    
    sessions_[sessionId] = userId;
    spdlog::info("Session created: {} for user: {}", sessionId, userId);
    
    return sessionId;
}

bool CogniDreamPlatformAPI::endSession(const std::string& sessionId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (sessions_.erase(sessionId) > 0) {
        spdlog::info("Session ended: {}", sessionId);
        return true;
    }
    
    return false;
}

PerformanceMetrics CogniDreamPlatformAPI::getPerformanceMetrics() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return currentMetrics_;
}

void CogniDreamPlatformAPI::processRequests() {
    while (running_) {
        // Process pending inference requests
        {
            std::lock_guard<std::mutex> lock(mutex_);
            for (auto it = pendingInferences_.begin(); it != pendingInferences_.end();) {
                auto response = executeInference(it->second);
                completedInferences_[it->first] = response;
                it = pendingInferences_.erase(it);
            }
            
            // Process pending training requests
            for (auto it = pendingTraining_.begin(); it != pendingTraining_.end();) {
                auto response = executeTraining(it->second);
                completedTraining_[it->first] = response;
                it = pendingTraining_.erase(it);
            }
        }
        
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
}

void CogniDreamPlatformAPI::collectMetrics() {
    while (running_) {
        if (metricsCollectionEnabled_ && driver_) {
            auto driverStats = driver_->getStats();
            
            std::lock_guard<std::mutex> lock(mutex_);
            currentMetrics_.gpuUtilization = driverStats.gpuUtilization;
            currentMetrics_.memoryUtilization = driverStats.memoryUtilization;
            currentMetrics_.temperature = driverStats.temperature;
            currentMetrics_.powerUsage = driverStats.powerUsage;
            currentMetrics_.activeRequests = pendingInferences_.size() + pendingTraining_.size();
            currentMetrics_.queuedRequests = completedInferences_.size() + completedTraining_.size();
            
            // Calculate throughput and latency (simplified)
            currentMetrics_.throughput = currentMetrics_.activeRequests * 100.0f; // requests per second
            currentMetrics_.latency = 1.0f / (currentMetrics_.throughput + 1.0f); // seconds
            
            metricsHistory_.push_back(currentMetrics_);
            if (metricsHistory_.size() > 1000) {
                metricsHistory_.erase(metricsHistory_.begin());
            }
        }
        
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
}

bool CogniDreamPlatformAPI::validateRequest(const InferenceRequest& request) const {
    if (!isModelLoaded(request.modelId)) {
        setLastError("Model not loaded: " + request.modelId);
        return false;
    }
    
    if (request.batchSize <= 0 || request.sequenceLength <= 0) {
        setLastError("Invalid batch size or sequence length");
        return false;
    }
    
    if (request.inputData.empty() || request.inputData[0].empty()) {
        setLastError("Empty input data");
        return false;
    }
    
    return true;
}

bool CogniDreamPlatformAPI::validateRequest(const TrainingRequest& request) const {
    if (!isModelLoaded(request.modelId)) {
        setLastError("Model not loaded: " + request.modelId);
        return false;
    }
    
    if (request.epochs <= 0 || request.learningRate <= 0) {
        setLastError("Invalid training parameters");
        return false;
    }
    
    if (request.trainingData.empty() || request.labels.empty()) {
        setLastError("Empty training data or labels");
        return false;
    }
    
    return true;
}

void CogniDreamPlatformAPI::setLastError(const std::string& error) const {
    std::lock_guard<std::mutex> lock(errorMutex_);
    lastError_ = error;
}

std::string CogniDreamPlatformAPI::getLastError() const {
    std::lock_guard<std::mutex> lock(errorMutex_);
    return lastError_;
}

// Convenience functions implementation
namespace cognidream_api {

std::vector<std::vector<float>> quickInference(
    const std::string& modelId,
    const std::vector<std::vector<float>>& inputData,
    const nlohmann::json& options
) {
    auto& api = CogniDreamPlatformAPI::getInstance();
    
    InferenceRequest request;
    request.requestId = "quick_" + std::to_string(std::chrono::system_clock::now().time_since_epoch().count());
    request.modelId = modelId;
    request.inputData = inputData;
    request.batchSize = inputData.size();
    request.sequenceLength = inputData.empty() ? 0 : inputData[0].size();
    request.dataType = "float32";
    request.options = options;
    
    auto response = api.executeInference(request);
    
    if (response.success) {
        return response.outputData;
    } else {
        spdlog::error("Quick inference failed: {}", response.errorMessage);
        return {};
    }
}

bool quickTraining(
    const std::string& modelId,
    const std::vector<std::vector<float>>& trainingData,
    const std::vector<std::vector<float>>& labels,
    int epochs,
    float learningRate
) {
    auto& api = CogniDreamPlatformAPI::getInstance();
    
    TrainingRequest request;
    request.requestId = "quick_" + std::to_string(std::chrono::system_clock::now().time_since_epoch().count());
    request.modelId = modelId;
    request.trainingData = trainingData;
    request.labels = labels;
    request.epochs = epochs;
    request.learningRate = learningRate;
    request.optimizer = "adam";
    request.lossFunction = "cross_entropy";
    
    auto response = api.executeTraining(request);
    
    if (response.success) {
        spdlog::info("Quick training completed. Final loss: {}", response.finalLoss);
        return true;
    } else {
        spdlog::error("Quick training failed: {}", response.errorMessage);
        return false;
    }
}

} // namespace cognidream_api

} // namespace cogniware 