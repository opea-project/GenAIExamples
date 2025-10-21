#include "data_ingestion_api.h"
#include <fstream>
#include <sstream>
#include <thread>
#include <chrono>
#include <filesystem>
#include <spdlog/spdlog.h>

namespace cogniware {

DataIngestionAPI& DataIngestionAPI::getInstance() {
    static DataIngestionAPI instance;
    return instance;
}

bool DataIngestionAPI::initialize(const DataIngestionConfig& config) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    try {
        // Validate configuration
        if (config.sourcePath.empty()) {
            lastError_ = "Invalid source path";
            return false;
        }
        
        if (config.batchSize == 0) {
            lastError_ = "Invalid batch size";
            return false;
        }
        
        if (config.maxWorkers == 0) {
            lastError_ = "Invalid number of workers";
            return false;
        }
        
        // Store configuration
        config_ = config;
        
        // Reset statistics
        stats_ = DataIngestionStats{};
        
        // Reset state
        isRunning_ = false;
        isPaused_ = false;
        
        spdlog::info("Data ingestion API initialized with source: {}", config.sourcePath);
        return true;
    } catch (const std::exception& e) {
        lastError_ = e.what();
        spdlog::error("Failed to initialize data ingestion API: {}", e.what());
        return false;
    }
}

bool DataIngestionAPI::startIngestion(
    DataBatchCallback batchCallback,
    ErrorCallback errorCallback,
    ProgressCallback progressCallback
) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (isRunning_) {
        lastError_ = "Ingestion already running";
        return false;
    }
    
    try {
        isRunning_ = true;
        isPaused_ = false;
        
        // Start ingestion in a separate thread
        std::thread([this, batchCallback, errorCallback, progressCallback]() {
            try {
                processDataSource(config_.sourcePath);
            } catch (const std::exception& e) {
                if (errorCallback) {
                    errorCallback(e.what());
                }
                spdlog::error("Error during data ingestion: {}", e.what());
            }
            
            isRunning_ = false;
        }).detach();
        
        return true;
    } catch (const std::exception& e) {
        lastError_ = e.what();
        spdlog::error("Failed to start data ingestion: {}", e.what());
        return false;
    }
}

void DataIngestionAPI::stopIngestion() {
    std::lock_guard<std::mutex> lock(mutex_);
    isRunning_ = false;
    isPaused_ = false;
    pauseCondition_.notify_all();
}

void DataIngestionAPI::pauseIngestion() {
    std::lock_guard<std::mutex> lock(mutex_);
    isPaused_ = true;
}

void DataIngestionAPI::resumeIngestion() {
    std::lock_guard<std::mutex> lock(mutex_);
    isPaused_ = false;
    pauseCondition_.notify_all();
}

DataIngestionStats DataIngestionAPI::getStats() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return stats_;
}

bool DataIngestionAPI::validateData(const nlohmann::json& data) const {
    try {
        if (!config_.validateData) {
            return true;
        }
        
        // Load schema
        std::ifstream schemaFile(config_.schemaPath);
        if (!schemaFile.is_open()) {
            spdlog::error("Failed to open schema file: {}", config_.schemaPath);
            return false;
        }
        
        nlohmann::json schema = nlohmann::json::parse(schemaFile);
        
        // Validate against schema
        // TODO: Implement schema validation
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Data validation failed: {}", e.what());
        return false;
    }
}

const char* DataIngestionAPI::getLastError() const {
    return lastError_.c_str();
}

void DataIngestionAPI::processDataSource(const std::string& sourcePath) {
    switch (config_.sourceType) {
        case DataSourceType::FILE:
            processFile(sourcePath);
            break;
        case DataSourceType::DATABASE:
            processDatabase(sourcePath);
            break;
        case DataSourceType::API:
            processAPI(sourcePath);
            break;
        case DataSourceType::STREAM:
            processStream(nlohmann::json::parse(sourcePath));
            break;
        default:
            throw std::runtime_error("Unsupported data source type");
    }
}

void DataIngestionAPI::processFile(const std::string& filePath) {
    std::ifstream file(filePath);
    if (!file.is_open()) {
        throw std::runtime_error("Failed to open file: " + filePath);
    }
    
    std::vector<std::string> texts;
    std::vector<nlohmann::json> metadata;
    size_t batchId = 0;
    
    std::string line;
    while (std::getline(file, line)) {
        if (!isRunning_) {
            break;
        }
        
        {
            std::unique_lock<std::mutex> lock(mutex_);
            pauseCondition_.wait(lock, [this]() { return !isPaused_; });
        }
        
        try {
            if (config_.format == DataFormat::JSON) {
                auto data = nlohmann::json::parse(line);
                if (validateData(data)) {
                    texts.push_back(data["text"].get<std::string>());
                    metadata.push_back(data["metadata"]);
                } else {
                    stats_.failedDocuments++;
                    continue;
                }
            } else {
                texts.push_back(line);
                metadata.push_back(nlohmann::json::object());
            }
            
            stats_.processedDocuments++;
            
            if (texts.size() >= config_.batchSize) {
                auto batch = createBatch(texts, metadata);
                batch.batchId = batchId++;
                batch.totalBatches = stats_.totalDocuments / config_.batchSize;
                
                // TODO: Call batch callback
                
                texts.clear();
                metadata.clear();
                stats_.totalBatches++;
            }
        } catch (const std::exception& e) {
            stats_.failedDocuments++;
            stats_.errors.push_back(e.what());
            spdlog::error("Error processing line: {}", e.what());
        }
    }
    
    // Process remaining items
    if (!texts.empty()) {
        auto batch = createBatch(texts, metadata);
        batch.batchId = batchId;
        batch.totalBatches = stats_.totalBatches;
        
        // TODO: Call batch callback
    }
}

void DataIngestionAPI::processDatabase(const std::string& connectionString) {
    // TODO: Implement database processing
    throw std::runtime_error("Database processing not implemented");
}

void DataIngestionAPI::processAPI(const std::string& apiEndpoint) {
    // TODO: Implement API processing
    throw std::runtime_error("API processing not implemented");
}

void DataIngestionAPI::processStream(const nlohmann::json& streamConfig) {
    // TODO: Implement stream processing
    throw std::runtime_error("Stream processing not implemented");
}

DataBatch DataIngestionAPI::createBatch(
    const std::vector<std::string>& texts,
    const std::vector<nlohmann::json>& metadata
) {
    DataBatch batch;
    batch.texts = texts;
    batch.metadata = metadata;
    return batch;
}

} // namespace cogniware



