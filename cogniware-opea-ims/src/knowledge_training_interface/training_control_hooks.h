/**
 * @file training_control_hooks.h
 * @brief Training control hooks for knowledge training
 */

#ifndef MSMARTCOMPUTE_TRAINING_CONTROL_HOOKS_H
#define MSMARTCOMPUTE_TRAINING_CONTROL_HOOKS_H

#include <string>
#include <vector>
#include <memory>
#include <functional>
#include <map>
#include <mutex>
#include <condition_variable>
#include <nlohmann/json.hpp>

namespace cogniware {

/**
 * @brief Training stage types
 */
enum class TrainingStage {
    PREPROCESSING,
    TRAINING,
    VALIDATION,
    EVALUATION,
    POSTPROCESSING
};

/**
 * @brief Training status
 */
enum class TrainingStatus {
    NOT_STARTED,
    RUNNING,
    PAUSED,
    COMPLETED,
    FAILED
};

/**
 * @brief Training metrics
 */
struct TrainingMetrics {
    float loss;
    float accuracy;
    float learningRate;
    size_t epoch;
    size_t step;
    std::vector<float> validationMetrics;
    nlohmann::json customMetrics;
};

/**
 * @brief Training configuration
 */
struct TrainingConfig {
    std::string modelId;
    std::string dataPath;
    size_t batchSize;
    size_t epochs;
    float learningRate;
    std::string optimizer;
    std::string lossFunction;
    std::vector<std::string> metrics;
    nlohmann::json hyperparameters;
    
    // Model architecture
    int inputSize;
    std::vector<int> hiddenSizes;
    int outputSize;
    
    // CUDA configuration
    bool useGPU;
    int gpuDeviceId;
    bool useMixedPrecision;
    float dropoutRate;
    float batchNormMomentum;
    
    // Training configuration
    size_t numWorkers;
    std::string checkpointPath;
    size_t checkpointFrequency;
    bool earlyStopping;
    size_t patience;
    float minDelta;
    
    // Additional training options
    bool useGradientClipping;
    float gradientClipValue;
    bool useLearningRateScheduling;
    std::string lrSchedulerType;
    float lrSchedulerFactor;
    size_t lrSchedulerPatience;
    float lrSchedulerMinLr;
    
    // Data augmentation
    bool useDataAugmentation;
    float augmentationProbability;
    std::vector<std::string> augmentationTypes;
    
    // Regularization
    float l1Regularization;
    float l2Regularization;
    bool useWeightDecay;
    float weightDecay;
    
    // Monitoring
    bool useTensorboard;
    std::string tensorboardLogDir;
    size_t loggingFrequency;
    bool saveBestModel;
    std::string bestModelMetric;
};

/**
 * @brief Training callback types
 */
using StageCallback = std::function<void(TrainingStage)>;
using MetricsCallback = std::function<void(const TrainingMetrics&)>;
using StatusCallback = std::function<void(TrainingStatus)>;
using ErrorCallback = std::function<void(const std::string&)>;

/**
 * @brief Processed data structure
 */
struct ProcessedData {
    std::vector<std::string> trainData;
    std::vector<std::string> validationData;
};

/**
 * @brief Data batch structure
 */
struct DataBatch {
    std::vector<float> inputs;
    std::vector<float> targets;
    size_t size;
};

/**
 * @brief Model interface
 */
class IModel {
public:
    virtual ~IModel() = default;
    virtual std::vector<float> forward(const DataBatch& batch) = 0;
    virtual void backward(float loss) = 0;
    virtual bool save(const std::string& path) const = 0;
    virtual bool load(const std::string& path) = 0;
};

/**
 * @brief Optimizer interface
 */
class IOptimizer {
public:
    virtual ~IOptimizer() = default;
    virtual void step() = 0;
    virtual float getLearningRate() const = 0;
};

/**
 * @brief Loss function interface
 */
class ILossFunction {
public:
    virtual ~ILossFunction() = default;
    virtual float compute(const std::vector<float>& outputs, const std::vector<float>& targets) = 0;
};

/**
 * @brief Training control hooks class
 */
class TrainingControlHooks {
public:
    /**
     * @brief Get singleton instance
     */
    static TrainingControlHooks& getInstance();

    /**
     * @brief Initialize training
     * @param config Training configuration
     * @return true if initialization successful
     */
    bool initialize(const TrainingConfig& config);

    /**
     * @brief Start training
     * @param stageCallback Callback for stage changes
     * @param metricsCallback Callback for metrics updates
     * @param statusCallback Callback for status changes
     * @param errorCallback Callback for errors
     * @return true if training started successfully
     */
    bool startTraining(
        StageCallback stageCallback,
        MetricsCallback metricsCallback,
        StatusCallback statusCallback,
        ErrorCallback errorCallback
    );

    /**
     * @brief Stop training
     */
    void stopTraining();

    /**
     * @brief Pause training
     */
    void pauseTraining();

    /**
     * @brief Resume training
     */
    void resumeTraining();

    /**
     * @brief Get current training status
     * @return Current training status
     */
    TrainingStatus getStatus() const;

    /**
     * @brief Get current training metrics
     * @return Current training metrics
     */
    TrainingMetrics getMetrics() const;

    /**
     * @brief Save checkpoint
     * @param path Path to save checkpoint
     * @return true if checkpoint saved successfully
     */
    bool saveCheckpoint(const std::string& path);

    /**
     * @brief Load checkpoint
     * @param path Path to load checkpoint from
     * @return true if checkpoint loaded successfully
     */
    bool loadCheckpoint(const std::string& path);

    /**
     * @brief Get last error message
     * @return Last error message
     */
    const char* getLastError() const;

    /**
     * @brief Compute precision
     * @param outputs Model outputs
     * @param targets Target values
     * @return Precision value
     */
    float computePrecision(const std::vector<float>& outputs, const std::vector<float>& targets);

    /**
     * @brief Compute recall
     * @param outputs Model outputs
     * @param targets Target values
     * @return Recall value
     */
    float computeRecall(const std::vector<float>& outputs, const std::vector<float>& targets);

    /**
     * @brief Compute F1 score
     * @param outputs Model outputs
     * @param targets Target values
     * @return F1 score value
     */
    float computeF1Score(const std::vector<float>& outputs, const std::vector<float>& targets);

    /**
     * @brief Compute Root Mean Square Error
     * @param outputs Model outputs
     * @param targets Target values
     * @return RMSE value
     */
    float computeRMSE(const std::vector<float>& outputs, const std::vector<float>& targets);

    /**
     * @brief Compute Mean Absolute Error
     * @param outputs Model outputs
     * @param targets Target values
     * @return MAE value
     */
    float computeMAE(const std::vector<float>& outputs, const std::vector<float>& targets);

private:
    TrainingControlHooks() = default;
    ~TrainingControlHooks() = default;
    TrainingControlHooks(const TrainingControlHooks&) = delete;
    TrainingControlHooks& operator=(const TrainingControlHooks&) = delete;

    /**
     * @brief Run training loop
     */
    void runTrainingLoop();

    /**
     * @brief Preprocess data
     * @return true if preprocessing successful
     */
    bool preprocessData();

    /**
     * @brief Train model
     * @return true if training successful
     */
    bool trainModel();

    /**
     * @brief Validate model
     * @return true if validation successful
     */
    bool validateModel();

    /**
     * @brief Evaluate model
     * @return true if evaluation successful
     */
    bool evaluateModel();

    /**
     * @brief Postprocess results
     * @return true if postprocessing successful
     */
    bool postprocessResults();

    /**
     * @brief Update metrics
     * @param metrics New metrics
     */
    void updateMetrics(const TrainingMetrics& metrics);

    /**
     * @brief Check early stopping
     * @return true if training should stop
     */
    bool checkEarlyStopping();

    /**
     * @brief Create optimizer
     * @param name Optimizer name
     * @param learningRate Learning rate
     * @return Optimizer instance
     */
    std::unique_ptr<IOptimizer> createOptimizer(const std::string& name, float learningRate);

    /**
     * @brief Create loss function
     * @param name Loss function name
     * @return Loss function instance
     */
    std::unique_ptr<ILossFunction> createLossFunction(const std::string& name);

    /**
     * @brief Get next batch of data
     * @param data Data to batch
     * @param startIndex Start index
     * @param batchSize Batch size
     * @return Data batch
     */
    DataBatch getNextBatch(const std::vector<std::string>& data, size_t startIndex, size_t batchSize);

    /**
     * @brief Compute accuracy
     * @param outputs Model outputs
     * @param targets Target values
     * @return Accuracy value
     */
    float computeAccuracy(const std::vector<float>& outputs, const std::vector<float>& targets);

    /**
     * @brief Compute metric
     * @param metricName Metric name
     * @param outputs Model outputs
     * @param targets Target values
     * @return Metric value
     */
    float computeMetric(const std::string& metricName, const std::vector<float>& outputs, const std::vector<float>& targets);

    TrainingConfig config_;
    TrainingStatus status_;
    TrainingMetrics metrics_;
    std::string lastError_;
    bool isRunning_;
    bool isPaused_;
    std::mutex mutex_;
    std::condition_variable pauseCondition_;
    
    StageCallback stageCallback_;
    MetricsCallback metricsCallback_;
    StatusCallback statusCallback_;
    ErrorCallback errorCallback_;

    // Additional member variables
    std::unique_ptr<IModel> model_;
    ProcessedData processedData_;
    float bestValidationLoss_ = std::numeric_limits<float>::infinity();
    size_t epochsWithoutImprovement_ = 0;
};

} // namespace cogniware

#endif // MSMARTCOMPUTE_TRAINING_CONTROL_HOOKS_H
