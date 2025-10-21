#pragma once

#include <string>
#include <vector>
#include <memory>
#include <mutex>
#include <unordered_map>
#include <functional>
#include <future>
#include <queue>
#include <atomic>
#include <chrono>
#include "utils/error_handler_cpp.h"
#include "utils/logger_cpp.h"
#include "vector_search_client_cpp.h"

namespace cogniware {
namespace dream {

// Request structure for routing
struct RouterRequest {
    std::string request_id;
    std::vector<float> query_vector;
    std::unordered_map<std::string, std::string> metadata;
    std::chrono::system_clock::time_point timestamp;
    int priority;
    bool is_async;
    std::string target_index;  // Added: specify target index
    std::chrono::milliseconds timeout;  // Added: per-request timeout

    RouterRequest() : priority(0), is_async(false), timeout(std::chrono::milliseconds(0)) {}
};

// Response structure for routing
struct RouterResponse {
    std::string request_id;
    std::vector<SearchResult> results;
    bool success;
    std::string error_message;
    std::chrono::system_clock::time_point timestamp;
    std::chrono::milliseconds processing_time;
    std::string target_index;  // Added: track which index was used
    size_t queue_position;     // Added: track queue position
    size_t queue_wait_time;    // Added: track time spent in queue

    RouterResponse() : success(false), queue_position(0), queue_wait_time(0) {}
};

// Router configuration
struct RouterConfig {
    size_t max_queue_size;
    size_t num_worker_threads;
    size_t batch_size;
    std::chrono::milliseconds timeout;
    bool enable_priority_queue;
    bool enable_request_tracking;  // Added: enable request tracking
    bool enable_performance_monitoring;  // Added: enable detailed monitoring
    size_t max_retries;  // Added: maximum retry attempts
    std::chrono::milliseconds retry_delay;  // Added: delay between retries
    std::unordered_map<std::string, std::string> parameters;

    RouterConfig() :
        max_queue_size(10000),
        num_worker_threads(4),
        batch_size(32),
        timeout(std::chrono::milliseconds(5000)),
        enable_priority_queue(true),
        enable_request_tracking(true),
        enable_performance_monitoring(true),
        max_retries(3),
        retry_delay(std::chrono::milliseconds(100)) {}
};

// Router statistics
struct RouterStats {
    std::atomic<size_t> total_requests;
    std::atomic<size_t> successful_requests;
    std::atomic<size_t> failed_requests;
    std::atomic<size_t> queued_requests;
    std::atomic<size_t> processing_requests;
    std::atomic<size_t> retried_requests;  // Added: track retries
    std::atomic<size_t> timed_out_requests;  // Added: track timeouts
    std::chrono::system_clock::time_point last_update;
    std::chrono::milliseconds average_processing_time;
    std::chrono::milliseconds max_processing_time;
    std::chrono::milliseconds min_processing_time;
    std::chrono::milliseconds average_queue_time;  // Added: average queue wait time
    std::chrono::milliseconds max_queue_time;      // Added: maximum queue wait time
    std::chrono::milliseconds min_queue_time;      // Added: minimum queue wait time
    std::unordered_map<std::string, size_t> index_usage;  // Added: track index usage
    
    // Copy constructor
    RouterStats(const RouterStats& other) 
        : total_requests(other.total_requests.load()),
          successful_requests(other.successful_requests.load()),
          failed_requests(other.failed_requests.load()),
          queued_requests(other.queued_requests.load()),
          processing_requests(other.processing_requests.load()),
          retried_requests(other.retried_requests.load()),
          timed_out_requests(other.timed_out_requests.load()),
          last_update(other.last_update),
          average_processing_time(other.average_processing_time),
          max_processing_time(other.max_processing_time),
          min_processing_time(other.min_processing_time),
          average_queue_time(other.average_queue_time),
          max_queue_time(other.max_queue_time),
          min_queue_time(other.min_queue_time),
          index_usage(other.index_usage) {}
    
    // Assignment operator
    RouterStats& operator=(const RouterStats& other) {
        if (this != &other) {
            total_requests.store(other.total_requests.load());
            successful_requests.store(other.successful_requests.load());
            failed_requests.store(other.failed_requests.load());
            queued_requests.store(other.queued_requests.load());
            processing_requests.store(other.processing_requests.load());
            retried_requests.store(other.retried_requests.load());
            timed_out_requests.store(other.timed_out_requests.load());
            last_update = other.last_update;
            average_processing_time = other.average_processing_time;
            max_processing_time = other.max_processing_time;
            min_processing_time = other.min_processing_time;
            average_queue_time = other.average_queue_time;
            max_queue_time = other.max_queue_time;
            min_queue_time = other.min_queue_time;
            index_usage = other.index_usage;
        }
        return *this;
    }
};

// Request tracking structure
struct RequestTracking {
    std::string request_id;
    std::chrono::system_clock::time_point enqueue_time;
    std::chrono::system_clock::time_point dequeue_time;
    std::chrono::system_clock::time_point completion_time;
    size_t retry_count;
    bool completed;
    std::string error_message;

    RequestTracking() : retry_count(0), completed(false) {}
};

// Fast router class
class FastRouter {
public:
    static FastRouter& getInstance();

    // Prevent copying
    FastRouter(const FastRouter&) = delete;
    FastRouter& operator=(const FastRouter&) = delete;

    // Initialization
    bool initialize(const RouterConfig& config);
    void shutdown();
    bool isInitialized() const;

    // Request handling
    RouterResponse route(const RouterRequest& request);
    std::future<RouterResponse> routeAsync(const RouterRequest& request);
    bool cancelRequest(const std::string& request_id);
    bool retryRequest(const std::string& request_id);  // Added: retry failed request

    // Queue management
    size_t getQueueSize() const;
    void clearQueue();
    bool isQueueFull() const;
    size_t getQueuePosition(const std::string& request_id) const;  // Added: get queue position
    std::chrono::milliseconds getEstimatedWaitTime() const;  // Added: estimate wait time

    // Statistics and monitoring
    RouterStats getStats() const;
    void resetStats();
    RequestTracking getRequestTracking(const std::string& request_id) const;  // Added: get request tracking
    std::vector<RequestTracking> getActiveRequests() const;  // Added: get active requests

    // Configuration
    RouterConfig getConfig() const;
    bool updateConfig(const RouterConfig& config);

private:
    FastRouter();
    ~FastRouter();

    // Worker thread function
    void workerThread();
    
    // Request processing
    RouterResponse processRequest(const RouterRequest& request);
    std::vector<RouterResponse> processBatch(const std::vector<RouterRequest>& requests);
    bool shouldRetryRequest(const RouterRequest& request, const std::string& error);  // Added: retry logic

    // Queue management
    bool enqueueRequest(const RouterRequest& request);
    bool dequeueRequest(RouterRequest& request);
    std::vector<RouterRequest> dequeueBatch(size_t batch_size);
    void updateQueueStats(const RouterRequest& request, const RouterResponse& response);  // Added: update stats

    // Validation
    bool validateRequest(const RouterRequest& request) const;
    bool validateConfig(const RouterConfig& config) const;

    // Member variables
    RouterConfig config_;
    bool initialized_;
    mutable std::mutex mutex_;
    std::condition_variable cv_;
    std::priority_queue<RouterRequest, std::vector<RouterRequest>, 
        std::function<bool(const RouterRequest&, const RouterRequest&)>> request_queue_;
    std::vector<std::thread> worker_threads_;
    std::atomic<bool> should_stop_;
    RouterStats stats_;
    std::unordered_map<std::string, std::promise<RouterResponse>> async_requests_;
    std::shared_ptr<VectorSearchClient> vector_client_;
    std::unordered_map<std::string, RequestTracking> request_tracking_;  // Added: request tracking
};

} // namespace dream
} // namespace cogniware
