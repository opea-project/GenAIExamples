#pragma once

#include <atomic>
#include <condition_variable>
#include <functional>
#include <mutex>
#include <queue>
#include <thread>
#include <vector>

namespace cogniware {

struct Request {
    std::string modelId;
    std::vector<int> inputIds;
    int maxLength;
    float temperature;
    int topK;
    float topP;
    std::function<void(const std::vector<int>&)> callback;
};

class ConcurrencyController {
public:
    static ConcurrencyController& getInstance();

    // Delete copy constructor and assignment operator
    ConcurrencyController(const ConcurrencyController&) = delete;
    ConcurrencyController& operator=(const ConcurrencyController&) = delete;

    // Controller lifecycle
    bool start();
    void stop();
    bool isRunning() const;
    
    // Request management
    bool submitRequest(const Request& request);
    bool cancelRequest(const std::string& requestId);
    
    // Configuration
    void setMaxConcurrentRequests(size_t maxRequests);
    void setMaxBatchSize(size_t maxBatchSize);
    
    // Statistics
    size_t getQueueSize() const;
    size_t getActiveRequestCount() const;
    
    // Error handling
    const char* getLastError() const;
    void clearLastError();

private:
    ConcurrencyController();
    ~ConcurrencyController();

    // Worker thread function
    void workerThread();
    
    // Request processing
    void processRequest(const Request& request);
    void processBatch(const std::vector<Request>& batch);
    
    // Queue management
    bool addToQueue(const Request& request);
    bool removeFromQueue(const std::string& requestId);
    std::vector<Request> getNextBatch();
    
    // Thread synchronization
    std::mutex mutex_;
    std::condition_variable cv_;
    std::queue<Request> requestQueue_;
    std::vector<std::thread> workerThreads_;
    
    // Configuration
    std::atomic<size_t> maxConcurrentRequests_;
    std::atomic<size_t> maxBatchSize_;
    
    // State
    std::atomic<bool> running_;
    std::atomic<size_t> activeRequestCount_;
    
    // Error handling
    std::string lastError_;
};

} // namespace cogniware 