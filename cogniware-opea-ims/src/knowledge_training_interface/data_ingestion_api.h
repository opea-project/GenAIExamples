/**
 * @file data_ingestion_api.h
 * @brief Data ingestion API for knowledge training
 */

#ifndef MSMARTCOMPUTE_DATA_INGESTION_API_H
#define MSMARTCOMPUTE_DATA_INGESTION_API_H

#include <string>
#include <vector>
#include <memory>
#include <functional>
#include <nlohmann/json.hpp>

namespace cogniware {

/**
 * @brief Data source types
 */
enum class DataSourceType {
    FILE,
    DATABASE,
    API,
    STREAM
};

/**
 * @brief Data format types
 */
enum class DataFormat {
    TEXT,
    JSON,
    CSV,
    BINARY
};

/**
 * @brief Data ingestion configuration
 */
struct DataIngestionConfig {
    DataSourceType sourceType;
    DataFormat format;
    std::string sourcePath;
    std::string schemaPath;
    size_t batchSize;
    size_t maxWorkers;
    bool validateData;
    nlohmann::json options;
};

/**
 * @brief Data batch structure
 */
struct DataBatch {
    std::vector<std::string> texts;
    std::vector<nlohmann::json> metadata;
    size_t batchId;
    size_t totalBatches;
};

/**
 * @brief Data ingestion statistics
 */
struct DataIngestionStats {
    size_t totalDocuments;
    size_t processedDocuments;
    size_t failedDocuments;
    size_t totalBatches;
    double averageProcessingTime;
    std::vector<std::string> errors;
};

/**
 * @brief Data ingestion callback types
 */
using DataBatchCallback = std::function<void(const DataBatch&)>;
using ErrorCallback = std::function<void(const std::string&)>;
using ProgressCallback = std::function<void(const DataIngestionStats&)>;

/**
 * @brief Data ingestion API class
 */
class DataIngestionAPI {
public:
    /**
     * @brief Get singleton instance
     */
    static DataIngestionAPI& getInstance();

    /**
     * @brief Initialize the data ingestion API
     * @param config Configuration for data ingestion
     * @return true if initialization successful
     */
    bool initialize(const DataIngestionConfig& config);

    /**
     * @brief Start data ingestion
     * @param batchCallback Callback for processed batches
     * @param errorCallback Callback for errors
     * @param progressCallback Callback for progress updates
     * @return true if ingestion started successfully
     */
    bool startIngestion(
        DataBatchCallback batchCallback,
        ErrorCallback errorCallback,
        ProgressCallback progressCallback
    );

    /**
     * @brief Stop data ingestion
     */
    void stopIngestion();

    /**
     * @brief Pause data ingestion
     */
    void pauseIngestion();

    /**
     * @brief Resume data ingestion
     */
    void resumeIngestion();

    /**
     * @brief Get ingestion statistics
     * @return Current ingestion statistics
     */
    DataIngestionStats getStats() const;

    /**
     * @brief Validate data against schema
     * @param data Data to validate
     * @return true if data is valid
     */
    bool validateData(const nlohmann::json& data) const;

    /**
     * @brief Get last error message
     * @return Last error message
     */
    const char* getLastError() const;

private:
    DataIngestionAPI() = default;
    ~DataIngestionAPI() = default;
    DataIngestionAPI(const DataIngestionAPI&) = delete;
    DataIngestionAPI& operator=(const DataIngestionAPI&) = delete;

    /**
     * @brief Process data source
     * @param sourcePath Path to data source
     */
    void processDataSource(const std::string& sourcePath);

    /**
     * @brief Process file data
     * @param filePath Path to file
     */
    void processFile(const std::string& filePath);

    /**
     * @brief Process database data
     * @param connectionString Database connection string
     */
    void processDatabase(const std::string& connectionString);

    /**
     * @brief Process API data
     * @param apiEndpoint API endpoint
     */
    void processAPI(const std::string& apiEndpoint);

    /**
     * @brief Process stream data
     * @param streamConfig Stream configuration
     */
    void processStream(const nlohmann::json& streamConfig);

    /**
     * @brief Create data batch
     * @param texts Text data
     * @param metadata Metadata
     * @return Data batch
     */
    DataBatch createBatch(
        const std::vector<std::string>& texts,
        const std::vector<nlohmann::json>& metadata
    );

    DataIngestionConfig config_;
    DataIngestionStats stats_;
    std::string lastError_;
    bool isRunning_;
    bool isPaused_;
    std::mutex mutex_;
    std::condition_variable pauseCondition_;
};

} // namespace cogniware

#endif // MSMARTCOMPUTE_DATA_INGESTION_API_H



