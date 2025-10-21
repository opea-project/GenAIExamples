#ifndef CONCURRENCY_CONTROLLER_H
#define CONCURRENCY_CONTROLLER_H

#include <string>
#include <memory>
#include <queue>
#include <mutex>
#include <condition_variable>
#include <thread>
#include <atomic>
#include <functional>
#include "llm_instance_manager.h"

namespace cogniware {

struct InferenceRequest {
    std::string model_id;
    std::string prompt;
    size_t max_tokens;
    float temperature;
    float top_p;
    int top_k;
    std::function<void(const std::string&)> callback;
};

class ConcurrencyController {
public:
    static ConcurrencyController& getInstance();

    // Request submission
    bool submitRequest(const InferenceRequest& request);
    bool cancelRequest(const std::string& request_id);

    // Resource management
    void setMaxConcurrentRequests(size_t max_requests);
    void setMaxBatchSize(size_t max_batch_size);
    size_t getCurrentQueueSize() const;
    size_t getActiveRequestCount() const;

    // Control
    void start();
    void stop();
    bool isRunning() const;

private:
    ConcurrencyController();
    ~ConcurrencyController();

    // Prevent copying
    ConcurrencyController(const ConcurrencyController&) = delete;
    ConcurrencyController& operator=(const ConcurrencyController&) = delete;

    // Worker thread
    void workerThread();
    bool processRequest(const InferenceRequest& request);
    bool batchRequests(std::vector<InferenceRequest>& batch);

    // Internal state
    std::queue<InferenceRequest> request_queue_;
    std::mutex queue_mutex_;
    std::condition_variable queue_cv_;
    std::atomic<bool> running_;
    std::atomic<size_t> active_requests_;
    size_t max_concurrent_requests_;
    size_t max_batch_size_;

    // Worker threads
    std::vector<std::thread> worker_threads_;
};

} // namespace cogniware

#endif // CONCURRENCY_CONTROLLER_H 