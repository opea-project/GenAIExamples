/**
 * @file training_control_hooks.cpp
 * @brief Implementation of training control hooks
 */

#include "training_control_hooks.h"
#include <thread>
#include <chrono>
#include <fstream>
#include <spdlog/spdlog.h>
#include <filesystem>

namespace cogniware {

TrainingControlHooks& TrainingControlHooks::getInstance() {
    static TrainingControlHooks instance;
    return instance;
}

bool TrainingControlHooks::initialize(const TrainingConfig& config) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (isRunning_) {
        lastError_ = "Training is already running";
        return false;
    }

    // Validate configuration
    if (config.modelId.empty() || config.dataPath.empty()) {
        lastError_ = "Invalid configuration: modelId and dataPath are required";
        return false;
    }

    if (config.batchSize == 0 || config.epochs == 0) {
        lastError_ = "Invalid configuration: batchSize and epochs must be greater than 0";
        return false;
    }

    config_ = config;
    status_ = TrainingStatus::NOT_STARTED;
    isRunning_ = false;
    isPaused_ = false;
    metrics_ = TrainingMetrics{};

    // Initialize CUDA model
    std::vector<int> layerSizes = {config.inputSize};
    for (const auto& size : config.hiddenSizes) {
        layerSizes.push_back(size);
    }
    layerSizes.push_back(config.outputSize);

    model_ = std::make_unique<CUDAModel>(layerSizes);
    if (config.useGPU) {
        model_->setDevice(config.gpuDeviceId);
        model_->enableMixedPrecision(config.useMixedPrecision);
    }
    model_->setDropoutRate(config.dropoutRate);
    model_->setBatchNormMomentum(config.batchNormMomentum);

    spdlog::info("Training control hooks initialized with model: {}", config.modelId);
    return true;
}

bool TrainingControlHooks::startTraining(
    StageCallback stageCallback,
    MetricsCallback metricsCallback,
    StatusCallback statusCallback,
    ErrorCallback errorCallback
) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (isRunning_) {
        lastError_ = "Training is already running";
        return false;
    }

    stageCallback_ = stageCallback;
    metricsCallback_ = metricsCallback;
    statusCallback_ = statusCallback;
    errorCallback_ = errorCallback;

    isRunning_ = true;
    status_ = TrainingStatus::RUNNING;

    // Start training in a separate thread
    std::thread trainingThread([this]() {
        try {
            runTrainingLoop();
        } catch (const std::exception& e) {
            lastError_ = e.what();
            status_ = TrainingStatus::FAILED;
            if (errorCallback_) {
                errorCallback_(lastError_);
            }
        }
    });
    trainingThread.detach();

    return true;
}

void TrainingControlHooks::stopTraining() {
    std::lock_guard<std::mutex> lock(mutex_);
    isRunning_ = false;
    status_ = TrainingStatus::COMPLETED;
    if (statusCallback_) {
        statusCallback_(status_);
    }
}

void TrainingControlHooks::pauseTraining() {
    std::lock_guard<std::mutex> lock(mutex_);
    if (isRunning_ && !isPaused_) {
        isPaused_ = true;
        status_ = TrainingStatus::PAUSED;
        if (statusCallback_) {
            statusCallback_(status_);
        }
    }
}

void TrainingControlHooks::resumeTraining() {
    std::lock_guard<std::mutex> lock(mutex_);
    if (isRunning_ && isPaused_) {
        isPaused_ = false;
        status_ = TrainingStatus::RUNNING;
        pauseCondition_.notify_one();
        if (statusCallback_) {
            statusCallback_(status_);
        }
    }
}

TrainingStatus TrainingControlHooks::getStatus() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return status_;
}

TrainingMetrics TrainingControlHooks::getMetrics() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return metrics_;
}

bool TrainingControlHooks::saveCheckpoint(const std::string& path) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    try {
        nlohmann::json checkpoint;
        checkpoint["status"] = static_cast<int>(status_);
        checkpoint["metrics"] = {
            {"loss", metrics_.loss},
            {"accuracy", metrics_.accuracy},
            {"learningRate", metrics_.learningRate},
            {"epoch", metrics_.epoch},
            {"step", metrics_.step},
            {"validationMetrics", metrics_.validationMetrics},
            {"customMetrics", metrics_.customMetrics}
        };
        checkpoint["config"] = {
            {"modelId", config_.modelId},
            {"dataPath", config_.dataPath},
            {"batchSize", config_.batchSize},
            {"epochs", config_.epochs},
            {"learningRate", config_.learningRate},
            {"optimizer", config_.optimizer},
            {"lossFunction", config_.lossFunction},
            {"metrics", config_.metrics},
            {"hyperparameters", config_.hyperparameters}
        };

        std::ofstream file(path);
        file << checkpoint.dump(4);
        return true;
    } catch (const std::exception& e) {
        lastError_ = e.what();
        return false;
    }
}

bool TrainingControlHooks::loadCheckpoint(const std::string& path) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    try {
        std::ifstream file(path);
        nlohmann::json checkpoint = nlohmann::json::parse(file);

        status_ = static_cast<TrainingStatus>(checkpoint["status"].get<int>());
        
        const auto& metrics = checkpoint["metrics"];
        metrics_.loss = metrics["loss"].get<float>();
        metrics_.accuracy = metrics["accuracy"].get<float>();
        metrics_.learningRate = metrics["learningRate"].get<float>();
        metrics_.epoch = metrics["epoch"].get<size_t>();
        metrics_.step = metrics["step"].get<size_t>();
        metrics_.validationMetrics = metrics["validationMetrics"].get<std::vector<float>>();
        metrics_.customMetrics = metrics["customMetrics"];

        const auto& config = checkpoint["config"];
        config_.modelId = config["modelId"].get<std::string>();
        config_.dataPath = config["dataPath"].get<std::string>();
        config_.batchSize = config["batchSize"].get<size_t>();
        config_.epochs = config["epochs"].get<size_t>();
        config_.learningRate = config["learningRate"].get<float>();
        config_.optimizer = config["optimizer"].get<std::string>();
        config_.lossFunction = config["lossFunction"].get<std::string>();
        config_.metrics = config["metrics"].get<std::vector<std::string>>();
        config_.hyperparameters = config["hyperparameters"];

        return true;
    } catch (const std::exception& e) {
        lastError_ = e.what();
        return false;
    }
}

const char* TrainingControlHooks::getLastError() const {
    return lastError_.c_str();
}

void TrainingControlHooks::runTrainingLoop() {
    if (stageCallback_) {
        stageCallback_(TrainingStage::PREPROCESSING);
    }

    if (!preprocessData()) {
        throw std::runtime_error("Data preprocessing failed: " + lastError_);
    }

    for (size_t epoch = metrics_.epoch; epoch < config_.epochs && isRunning_; ++epoch) {
        metrics_.epoch = epoch;
        
        if (stageCallback_) {
            stageCallback_(TrainingStage::TRAINING);
        }

        if (!trainModel()) {
            throw std::runtime_error("Model training failed: " + lastError_);
        }

        if (stageCallback_) {
            stageCallback_(TrainingStage::VALIDATION);
        }

        if (!validateModel()) {
            throw std::runtime_error("Model validation failed: " + lastError_);
        }

        if (checkEarlyStopping()) {
            spdlog::info("Early stopping triggered at epoch {}", epoch);
            break;
        }

        // Save checkpoint if needed
        if (config_.checkpointFrequency > 0 && 
            (epoch + 1) % config_.checkpointFrequency == 0) {
            std::string checkpointPath = config_.checkpointPath + 
                "/checkpoint_epoch_" + std::to_string(epoch + 1) + ".json";
            if (!saveCheckpoint(checkpointPath)) {
                spdlog::warn("Failed to save checkpoint at epoch {}", epoch + 1);
            }
        }

        // Handle pause
        if (isPaused_) {
            std::unique_lock<std::mutex> lock(mutex_);
            pauseCondition_.wait(lock, [this]() { return !isPaused_; });
        }
    }

    if (stageCallback_) {
        stageCallback_(TrainingStage::EVALUATION);
    }

    if (!evaluateModel()) {
        throw std::runtime_error("Model evaluation failed: " + lastError_);
    }

    if (stageCallback_) {
        stageCallback_(TrainingStage::POSTPROCESSING);
    }

    if (!postprocessResults()) {
        throw std::runtime_error("Results postprocessing failed: " + lastError_);
    }

    status_ = TrainingStatus::COMPLETED;
    if (statusCallback_) {
        statusCallback_(status_);
    }
}

bool TrainingControlHooks::preprocessData() {
    try {
        spdlog::info("Starting data preprocessing for model: {}", config_.modelId);
        
        // Load and validate data
        std::ifstream dataFile(config_.dataPath);
        if (!dataFile.is_open()) {
            lastError_ = "Failed to open data file: " + config_.dataPath;
            return false;
        }

        // Read and parse data
        std::vector<std::string> rawData;
        std::string line;
        while (std::getline(dataFile, line)) {
            if (!line.empty()) {
                rawData.push_back(line);
            }
        }

        // Split data into train/validation sets (80/20 split)
        size_t splitIndex = static_cast<size_t>(rawData.size() * 0.8);
        std::vector<std::string> trainData(rawData.begin(), rawData.begin() + splitIndex);
        std::vector<std::string> validationData(rawData.begin() + splitIndex, rawData.end());

        // Store processed data
        processedData_ = {
            .trainData = std::move(trainData),
            .validationData = std::move(validationData)
        };

        spdlog::info("Data preprocessing completed. Train samples: {}, Validation samples: {}", 
            processedData_.trainData.size(), processedData_.validationData.size());
        return true;
    } catch (const std::exception& e) {
        lastError_ = "Data preprocessing failed: " + std::string(e.what());
        spdlog::error(lastError_);
        return false;
    }
}

bool TrainingControlHooks::trainModel() {
    try {
        spdlog::info("Starting model training for epoch {}", metrics_.epoch);
        
        // Initialize optimizer
        auto optimizer = createOptimizer(config_.optimizer, config_.learningRate);
        if (!optimizer) {
            lastError_ = "Failed to create optimizer: " + config_.optimizer;
            return false;
        }

        // Initialize loss function
        auto lossFunction = createLossFunction(config_.lossFunction);
        if (!lossFunction) {
            lastError_ = "Failed to create loss function: " + config_.lossFunction;
            return false;
        }

        // Training loop
        size_t totalSteps = processedData_.trainData.size() / config_.batchSize;
        for (size_t step = 0; step < totalSteps && isRunning_; ++step) {
            if (isPaused_) {
                std::unique_lock<std::mutex> lock(mutex_);
                pauseCondition_.wait(lock, [this]() { return !isPaused_; });
            }

            // Get batch
            auto batch = getNextBatch(processedData_.trainData, step * config_.batchSize, config_.batchSize);
            
            // Forward pass
            auto outputs = model_->forward(batch);
            
            // Compute loss
            float batchLoss = lossFunction->compute(outputs, batch.targets);
            
            // Backward pass
            model_->backward(batchLoss);
            
            // Update weights
            optimizer->step();

            // Update metrics
            TrainingMetrics currentMetrics = metrics_;
            currentMetrics.loss = batchLoss;
            currentMetrics.step = step;
            currentMetrics.learningRate = optimizer->getLearningRate();
            updateMetrics(currentMetrics);

            // Log progress
            if (step % 10 == 0) {
                spdlog::info("Epoch {} - Step {}/{} - Loss: {:.4f}", 
                    metrics_.epoch, step, totalSteps, batchLoss);
            }
        }

        spdlog::info("Training completed for epoch {}", metrics_.epoch);
        return true;
    } catch (const std::exception& e) {
        lastError_ = "Model training failed: " + std::string(e.what());
        spdlog::error(lastError_);
        return false;
    }
}

bool TrainingControlHooks::validateModel() {
    try {
        spdlog::info("Starting model validation");
        
        // Initialize loss function
        auto lossFunction = createLossFunction(config_.lossFunction);
        if (!lossFunction) {
            lastError_ = "Failed to create loss function for validation";
            return false;
        }

        float totalLoss = 0.0f;
        float totalAccuracy = 0.0f;
        size_t numBatches = 0;

        // Validation loop
        for (size_t i = 0; i < processedData_.validationData.size(); i += config_.batchSize) {
            // Get batch
            auto batch = getNextBatch(processedData_.validationData, i, config_.batchSize);
            
            // Forward pass
            auto outputs = model_->forward(batch);
            
            // Compute loss and accuracy
            float batchLoss = lossFunction->compute(outputs, batch.targets);
            float batchAccuracy = computeAccuracy(outputs, batch.targets);
            
            totalLoss += batchLoss;
            totalAccuracy += batchAccuracy;
            numBatches++;
        }

        // Update metrics
        TrainingMetrics currentMetrics = metrics_;
        currentMetrics.validationMetrics = {
            totalLoss / numBatches,
            totalAccuracy / numBatches
        };
        updateMetrics(currentMetrics);

        spdlog::info("Validation completed - Loss: {:.4f}, Accuracy: {:.4f}", 
            currentMetrics.validationMetrics[0], currentMetrics.validationMetrics[1]);
        return true;
    } catch (const std::exception& e) {
        lastError_ = "Model validation failed: " + std::string(e.what());
        spdlog::error(lastError_);
        return false;
    }
}

bool TrainingControlHooks::evaluateModel() {
    try {
        spdlog::info("Starting model evaluation");
        
        // Initialize metrics
        std::map<std::string, float> evaluationMetrics;
        for (const auto& metricName : config_.metrics) {
            evaluationMetrics[metricName] = 0.0f;
        }

        // Evaluation loop
        for (size_t i = 0; i < processedData_.validationData.size(); i += config_.batchSize) {
            // Get batch
            auto batch = getNextBatch(processedData_.validationData, i, config_.batchSize);
            
            // Forward pass
            auto outputs = model_->forward(batch);
            
            // Compute metrics
            for (const auto& metricName : config_.metrics) {
                float metricValue = computeMetric(metricName, outputs, batch.targets);
                evaluationMetrics[metricName] += metricValue;
            }
        }

        // Average metrics
        size_t numBatches = processedData_.validationData.size() / config_.batchSize;
        for (auto& [metricName, value] : evaluationMetrics) {
            value /= numBatches;
        }

        // Update metrics
        TrainingMetrics currentMetrics = metrics_;
        currentMetrics.customMetrics = evaluationMetrics;
        updateMetrics(currentMetrics);

        // Log results
        spdlog::info("Evaluation completed");
        for (const auto& [metricName, value] : evaluationMetrics) {
            spdlog::info("{}: {:.4f}", metricName, value);
        }

        return true;
    } catch (const std::exception& e) {
        lastError_ = "Model evaluation failed: " + std::string(e.what());
        spdlog::error(lastError_);
        return false;
    }
}

bool TrainingControlHooks::postprocessResults() {
    try {
        spdlog::info("Starting results postprocessing");
        
        // Save final model
        std::string modelPath = config_.checkpointPath + "/final_model.pt";
        if (!model_->save(modelPath)) {
            lastError_ = "Failed to save final model";
            return false;
        }

        // Generate evaluation report
        std::string reportPath = config_.checkpointPath + "/evaluation_report.json";
        nlohmann::json report = {
            {"modelId", config_.modelId},
            {"finalMetrics", metrics_.customMetrics},
            {"trainingConfig", {
                {"batchSize", config_.batchSize},
                {"epochs", config_.epochs},
                {"learningRate", config_.learningRate},
                {"optimizer", config_.optimizer},
                {"lossFunction", config_.lossFunction}
            }},
            {"validationMetrics", metrics_.validationMetrics}
        };

        std::ofstream reportFile(reportPath);
        reportFile << report.dump(4);

        // Clean up temporary files
        std::filesystem::path tempDir = config_.checkpointPath + "/temp";
        if (std::filesystem::exists(tempDir)) {
            std::filesystem::remove_all(tempDir);
        }

        spdlog::info("Postprocessing completed");
        return true;
    } catch (const std::exception& e) {
        lastError_ = "Results postprocessing failed: " + std::string(e.what());
        spdlog::error(lastError_);
        return false;
    }
}

void TrainingControlHooks::updateMetrics(const TrainingMetrics& metrics) {
    std::lock_guard<std::mutex> lock(mutex_);
    metrics_ = metrics;
    if (metricsCallback_) {
        metricsCallback_(metrics_);
    }
}

bool TrainingControlHooks::checkEarlyStopping() {
    if (!config_.earlyStopping) {
        return false;
    }

    try {
        // Get current validation loss
        float currentLoss = metrics_.validationMetrics[0];
        
        // Update best loss if needed
        if (currentLoss < bestValidationLoss_) {
            bestValidationLoss_ = currentLoss;
            epochsWithoutImprovement_ = 0;
            
            // Save best model
            std::string bestModelPath = config_.checkpointPath + "/best_model.pt";
            if (!model_->save(bestModelPath)) {
                spdlog::warn("Failed to save best model");
            }
        } else {
            epochsWithoutImprovement_++;
        }

        // Check if we should stop
        if (epochsWithoutImprovement_ >= config_.patience) {
            spdlog::info("Early stopping triggered after {} epochs without improvement", 
                epochsWithoutImprovement_);
            return true;
        }

        return false;
    } catch (const std::exception& e) {
        lastError_ = "Early stopping check failed: " + std::string(e.what());
        spdlog::error(lastError_);
        return false;
    }
}

std::unique_ptr<IOptimizer> TrainingControlHooks::createOptimizer(const std::string& name, float learningRate) {
    try {
        if (name == "adam") {
            return std::make_unique<AdamOptimizer>(learningRate);
        } else if (name == "sgd") {
            return std::make_unique<SGDOptimizer>(learningRate);
        } else if (name == "rmsprop") {
            return std::make_unique<RMSPropOptimizer>(learningRate);
        } else {
            lastError_ = "Unsupported optimizer: " + name;
            return nullptr;
        }
    } catch (const std::exception& e) {
        lastError_ = "Failed to create optimizer: " + std::string(e.what());
        return nullptr;
    }
}

std::unique_ptr<ILossFunction> TrainingControlHooks::createLossFunction(const std::string& name) {
    if (config_.useGPU) {
        if (name == "cross_entropy") {
            return std::make_unique<CUDACrossEntropyLoss>();
        } else if (name == "mse") {
            return std::make_unique<CUDAMSELoss>();
        } else if (name == "binary_cross_entropy") {
            return std::make_unique<CUDABinaryCrossEntropyLoss>();
        }
    } else {
        if (name == "cross_entropy") {
            return std::make_unique<CrossEntropyLoss>();
        } else if (name == "mse") {
            return std::make_unique<MSELoss>();
        } else if (name == "binary_cross_entropy") {
            return std::make_unique<BinaryCrossEntropyLoss>();
        }
    }
    
    spdlog::error("Unsupported loss function: {}", name);
    return nullptr;
}

DataBatch TrainingControlHooks::getNextBatch(const std::vector<std::string>& data, size_t startIndex, size_t batchSize) {
    DataBatch batch;
    batch.size = std::min(batchSize, data.size() - startIndex);
    batch.inputs.reserve(batch.size);
    batch.targets.reserve(batch.size);

    for (size_t i = 0; i < batch.size; ++i) {
        const auto& item = data[startIndex + i];
        try {
            // Parse data item (assuming JSON format)
            auto json = nlohmann::json::parse(item);
            
            // Extract features and target
            auto features = json["features"].get<std::vector<float>>();
            auto target = json["target"].get<float>();
            
            // Add to batch
            batch.inputs.insert(batch.inputs.end(), features.begin(), features.end());
            batch.targets.push_back(target);
        } catch (const std::exception& e) {
            spdlog::warn("Failed to parse data item: {}", e.what());
            // Skip invalid items
            batch.size--;
        }
    }

    return batch;
}

float TrainingControlHooks::computeAccuracy(const std::vector<float>& outputs, const std::vector<float>& targets) {
    if (outputs.empty() || targets.empty() || outputs.size() != targets.size()) {
        return 0.0f;
    }

    size_t correct = 0;
    for (size_t i = 0; i < outputs.size(); ++i) {
        // For classification tasks, round the output to get the predicted class
        int predicted = static_cast<int>(std::round(outputs[i]));
        int actual = static_cast<int>(std::round(targets[i]));
        if (predicted == actual) {
            correct++;
        }
    }

    return static_cast<float>(correct) / outputs.size();
}

float TrainingControlHooks::computeMetric(const std::string& metricName, const std::vector<float>& outputs, const std::vector<float>& targets) {
    if (outputs.empty() || targets.empty() || outputs.size() != targets.size()) {
        return 0.0f;
    }

    try {
        if (metricName == "accuracy") {
            return computeAccuracy(outputs, targets);
        } else if (metricName == "precision") {
            return computePrecision(outputs, targets);
        } else if (metricName == "recall") {
            return computeRecall(outputs, targets);
        } else if (metricName == "f1") {
            return computeF1Score(outputs, targets);
        } else if (metricName == "rmse") {
            return computeRMSE(outputs, targets);
        } else if (metricName == "mae") {
            return computeMAE(outputs, targets);
        } else {
            spdlog::warn("Unsupported metric: {}", metricName);
            return 0.0f;
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to compute metric {}: {}", metricName, e.what());
        return 0.0f;
    }
}

float TrainingControlHooks::computePrecision(const std::vector<float>& outputs, const std::vector<float>& targets) {
    size_t truePositives = 0;
    size_t falsePositives = 0;

    for (size_t i = 0; i < outputs.size(); ++i) {
        int predicted = static_cast<int>(std::round(outputs[i]));
        int actual = static_cast<int>(std::round(targets[i]));
        
        if (predicted == 1 && actual == 1) {
            truePositives++;
        } else if (predicted == 1 && actual == 0) {
            falsePositives++;
        }
    }

    return truePositives + falsePositives > 0 ? 
        static_cast<float>(truePositives) / (truePositives + falsePositives) : 0.0f;
}

float TrainingControlHooks::computeRecall(const std::vector<float>& outputs, const std::vector<float>& targets) {
    size_t truePositives = 0;
    size_t falseNegatives = 0;

    for (size_t i = 0; i < outputs.size(); ++i) {
        int predicted = static_cast<int>(std::round(outputs[i]));
        int actual = static_cast<int>(std::round(targets[i]));
        
        if (predicted == 1 && actual == 1) {
            truePositives++;
        } else if (predicted == 0 && actual == 1) {
            falseNegatives++;
        }
    }

    return truePositives + falseNegatives > 0 ? 
        static_cast<float>(truePositives) / (truePositives + falseNegatives) : 0.0f;
}

float TrainingControlHooks::computeF1Score(const std::vector<float>& outputs, const std::vector<float>& targets) {
    float precision = computePrecision(outputs, targets);
    float recall = computeRecall(outputs, targets);

    return precision + recall > 0 ? 
        2.0f * (precision * recall) / (precision + recall) : 0.0f;
}

float TrainingControlHooks::computeRMSE(const std::vector<float>& outputs, const std::vector<float>& targets) {
    float sumSquaredError = 0.0f;
    for (size_t i = 0; i < outputs.size(); ++i) {
        float error = outputs[i] - targets[i];
        sumSquaredError += error * error;
    }
    return std::sqrt(sumSquaredError / outputs.size());
}

float TrainingControlHooks::computeMAE(const std::vector<float>& outputs, const std::vector<float>& targets) {
    float sumAbsoluteError = 0.0f;
    for (size_t i = 0; i < outputs.size(); ++i) {
        sumAbsoluteError += std::abs(outputs[i] - targets[i]);
    }
    return sumAbsoluteError / outputs.size();
}

} // namespace cogniware
