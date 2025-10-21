#pragma once

#include "model_selector.h"
#include <string>
#include <vector>
#include <memory>
#include <functional>
#include <thread>
#include <atomic>
#include <mutex>
#include <condition_variable>

namespace cogniware {

// Download status
enum class DownloadStatus {
    PENDING,
    DOWNLOADING,
    EXTRACTING,
    CONFIGURING,
    COMPLETED,
    FAILED,
    CANCELLED
};

// Download progress info
struct DownloadProgress {
    std::string modelId;
    DownloadStatus status;
    size_t downloadedBytes;
    size_t totalBytes;
    float progressPercentage;
    std::string currentFile;
    std::string statusMessage;
    std::chrono::system_clock::time_point startTime;
    std::chrono::system_clock::time_point lastUpdate;
    std::string errorMessage;
};

// Download task
struct DownloadTask {
    std::string taskId;
    ModelMetadata model;
    std::string downloadPath;
    std::string extractPath;
    std::string configPath;
    DownloadProgressCallback progressCallback;
    std::atomic<bool> cancelled;
    std::atomic<DownloadStatus> status;
    std::string errorMessage;
};

// Model downloader interface
class ModelDownloader {
public:
    virtual ~ModelDownloader() = default;

    // Download management
    virtual std::string startDownload(const ModelMetadata& model, 
                                    const std::string& downloadPath,
                                    DownloadProgressCallback callback = nullptr) = 0;
    virtual bool cancelDownload(const std::string& taskId) = 0;
    virtual DownloadProgress getDownloadProgress(const std::string& taskId) = 0;
    virtual std::vector<DownloadProgress> getAllDownloadProgress() = 0;
    virtual bool isDownloading(const std::string& taskId) = 0;

    // Download utilities
    virtual bool verifyDownload(const std::string& modelPath) = 0;
    virtual bool cleanupFailedDownload(const std::string& taskId) = 0;
    virtual std::vector<std::string> getDownloadedModels() = 0;
};

// Hugging Face model downloader
class HuggingFaceModelDownloader : public ModelDownloader {
public:
    HuggingFaceModelDownloader();
    ~HuggingFaceModelDownloader() override;

    // Download management
    std::string startDownload(const ModelMetadata& model, 
                            const std::string& downloadPath,
                            DownloadProgressCallback callback = nullptr) override;
    bool cancelDownload(const std::string& taskId) override;
    DownloadProgress getDownloadProgress(const std::string& taskId) override;
    std::vector<DownloadProgress> getAllDownloadProgress() override;
    bool isDownloading(const std::string& taskId) override;

    // Download utilities
    bool verifyDownload(const std::string& modelPath) override;
    bool cleanupFailedDownload(const std::string& taskId) override;
    std::vector<std::string> getDownloadedModels() override;

    // Hugging Face specific methods
    bool downloadModelFiles(const std::string& modelId, 
                          const std::string& downloadPath,
                          const std::vector<std::string>& files = {});
    bool downloadTokenizer(const std::string& modelId, 
                         const std::string& downloadPath);
    bool downloadConfig(const std::string& modelId, 
                       const std::string& downloadPath);

private:
    std::string apiBaseUrl_;
    std::string apiToken_;
    std::map<std::string, std::unique_ptr<DownloadTask>> activeDownloads_;
    std::vector<std::thread> downloadThreads_;
    std::mutex downloadsMutex_;
    std::condition_variable downloadCondition_;
    std::atomic<bool> shutdown_;

    // Helper methods
    void downloadWorker();
    bool downloadFile(const std::string& url, 
                     const std::string& localPath,
                     DownloadProgressCallback callback,
                     const std::string& taskId);
    bool extractModelFiles(const std::string& archivePath, 
                          const std::string& extractPath);
    bool configureModel(const ModelMetadata& model, 
                       const std::string& configPath);
    std::string generateTaskId();
    void updateProgress(const std::string& taskId, 
                       DownloadStatus status,
                       size_t downloaded = 0,
                       size_t total = 0,
                       const std::string& message = "");
};

// Ollama model downloader
class OllamaModelDownloader : public ModelDownloader {
public:
    OllamaModelDownloader();
    ~OllamaModelDownloader() override;

    // Download management
    std::string startDownload(const ModelMetadata& model, 
                            const std::string& downloadPath,
                            DownloadProgressCallback callback = nullptr) override;
    bool cancelDownload(const std::string& taskId) override;
    DownloadProgress getDownloadProgress(const std::string& taskId) override;
    std::vector<DownloadProgress> getAllDownloadProgress() override;
    bool isDownloading(const std::string& taskId) override;

    // Download utilities
    bool verifyDownload(const std::string& modelPath) override;
    bool cleanupFailedDownload(const std::string& taskId) override;
    std::vector<std::string> getDownloadedModels() override;

    // Ollama specific methods
    bool pullModel(const std::string& modelId);
    bool removeModel(const std::string& modelId);
    std::vector<std::string> listLocalModels();

private:
    std::string ollamaBaseUrl_;
    std::map<std::string, std::unique_ptr<DownloadTask>> activeDownloads_;
    std::vector<std::thread> downloadThreads_;
    std::mutex downloadsMutex_;
    std::condition_variable downloadCondition_;
    std::atomic<bool> shutdown_;

    // Helper methods
    void downloadWorker();
    bool pullModelFromOllama(const std::string& modelId, 
                           DownloadProgressCallback callback,
                           const std::string& taskId);
    std::string generateTaskId();
    void updateProgress(const std::string& taskId, 
                       DownloadStatus status,
                       size_t downloaded = 0,
                       size_t total = 0,
                       const std::string& message = "");
};

// Model downloader factory
class ModelDownloaderFactory {
public:
    static std::unique_ptr<ModelDownloader> createDownloader(ModelSource source);
    static std::unique_ptr<ModelDownloader> createDownloader(const ModelMetadata& model);
};

// Model download manager
class ModelDownloadManager {
public:
    static ModelDownloadManager& getInstance();

    // Download management
    std::string downloadModel(const ModelMetadata& model, 
                            const std::string& downloadPath,
                            DownloadProgressCallback callback = nullptr);
    bool cancelDownload(const std::string& taskId);
    DownloadProgress getDownloadProgress(const std::string& taskId);
    std::vector<DownloadProgress> getAllDownloadProgress();
    bool isDownloading(const std::string& taskId);

    // Download utilities
    bool verifyDownload(const std::string& modelPath);
    bool cleanupFailedDownload(const std::string& taskId);
    std::vector<std::string> getDownloadedModels();
    void cleanup();

    // Configuration
    void setDownloadPath(const std::string& path);
    std::string getDownloadPath() const;
    void setMaxConcurrentDownloads(size_t max);
    size_t getMaxConcurrentDownloads() const;

private:
    ModelDownloadManager();
    ~ModelDownloadManager();

    std::string downloadPath_;
    size_t maxConcurrentDownloads_;
    std::map<ModelSource, std::unique_ptr<ModelDownloader>> downloaders_;
    std::mutex managerMutex_;
};

} // namespace cogniware
