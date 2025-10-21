#include "fast_router_core.h"
#include <algorithm>
#include <chrono>
#include <thread>

namespace cogniware {
namespace dream {

FastRouter& FastRouter::getInstance() {
    static FastRouter instance;
    return instance;
}

FastRouter::FastRouter() :
    initialized_(false),
    should_stop_(false),
    request_queue_([](const RouterRequest& a, const RouterRequest& b) {
        return a.priority < b.priority;  // Higher priority comes first
    }) {
}

FastRouter::~FastRouter() {
    shutdown();
}

bool FastRouter::initialize(const RouterConfig& config) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (initialized_) {
        LOG_WARN("Fast router already initialized");
        return false;
    }

    if (!validateConfig(config)) {
        LOG_ERROR("Invalid router configuration");
        return false;
    }

    try {
        config_ = config;
        vector_client_ = std::make_shared<VectorSearchClient>();
        
        // Start worker threads
        should_stop_ = false;
        for (size_t i = 0; i < config_.num_worker_threads; ++i) {
            worker_threads_.emplace_back(&FastRouter::workerThread, this);
        }

        initialized_ = true;
        LOG_INFO("Fast router initialized with {} worker threads", config_.num_worker_threads);
        return true;
    } catch (const std::exception& e) {
        LOG_ERROR("Failed to initialize fast router: {}", e.what());
        return false;
    }
}

void FastRouter::shutdown() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!initialized_) {
        return;
    }

    try {
        // Signal worker threads to stop
        should_stop_ = true;
        cv_.notify_all();

        // Wait for worker threads to finish
        for (auto& thread : worker_threads_) {
            if (thread.joinable()) {
                thread.join();
            }
        }
        worker_threads_.clear();

        // Clear request queue
        clearQueue();

        initialized_ = false;
        LOG_INFO("Fast router shut down");
    } catch (const std::exception& e) {
        LOG_ERROR("Error during fast router shutdown: {}", e.what());
    }
}

bool FastRouter::isInitialized() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return initialized_;
}

RouterResponse FastRouter::route(const RouterRequest& request) {
    if (!initialized_) {
        LOG_ERROR("Fast router not initialized");
        return RouterResponse();
    }

    if (!validateRequest(request)) {
        LOG_ERROR("Invalid router request");
        return RouterResponse();
    }

    try {
        if (request.is_async) {
            return routeAsync(request).get();
        }

        // Track request if enabled
        if (config_.enable_request_tracking) {
            std::lock_guard<std::mutex> lock(mutex_);
            RequestTracking tracking;
            tracking.request_id = request.request_id;
            tracking.enqueue_time = std::chrono::system_clock::now();
            request_tracking_[request.request_id] = tracking;
        }

        return processRequest(request);
    } catch (const std::exception& e) {
        LOG_ERROR("Error routing request: {}", e.what());
        RouterResponse response;
        response.request_id = request.request_id;
        response.success = false;
        response.error_message = e.what();
        return response;
    }
}

std::future<RouterResponse> FastRouter::routeAsync(const RouterRequest& request) {
    if (!initialized_) {
        LOG_ERROR("Fast router not initialized");
        std::promise<RouterResponse> promise;
        promise.set_value(RouterResponse());
        return promise.get_future();
    }

    if (!validateRequest(request)) {
        LOG_ERROR("Invalid router request");
        std::promise<RouterResponse> promise;
        promise.set_value(RouterResponse());
        return promise.get_future();
    }

    try {
        std::promise<RouterResponse> promise;
        auto future = promise.get_future();

        {
            std::lock_guard<std::mutex> lock(mutex_);
            async_requests_[request.request_id] = std::move(promise);
        }

        if (!enqueueRequest(request)) {
            std::lock_guard<std::mutex> lock(mutex_);
            async_requests_.erase(request.request_id);
            std::promise<RouterResponse> new_promise;
            new_promise.set_value(RouterResponse());
            return new_promise.get_future();
        }

        return future;
    } catch (const std::exception& e) {
        LOG_ERROR("Error routing async request: {}", e.what());
        std::promise<RouterResponse> promise;
        promise.set_value(RouterResponse());
        return promise.get_future();
    }
}

bool FastRouter::cancelRequest(const std::string& request_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!initialized_) {
        LOG_ERROR("Fast router not initialized");
        return false;
    }

    try {
        auto it = async_requests_.find(request_id);
        if (it != async_requests_.end()) {
            RouterResponse response;
            response.request_id = request_id;
            response.success = false;
            response.error_message = "Request cancelled";
            it->second.set_value(response);
            async_requests_.erase(it);
            return true;
        }
        return false;
    } catch (const std::exception& e) {
        LOG_ERROR("Error cancelling request: {}", e.what());
        return false;
    }
}

size_t FastRouter::getQueueSize() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return request_queue_.size();
}

void FastRouter::clearQueue() {
    std::lock_guard<std::mutex> lock(mutex_);
    while (!request_queue_.empty()) {
        request_queue_.pop();
    }
}

bool FastRouter::isQueueFull() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return request_queue_.size() >= config_.max_queue_size;
}

RouterStats FastRouter::getStats() const {
    return stats_;
}

void FastRouter::resetStats() {
    stats_ = RouterStats();
}

RouterConfig FastRouter::getConfig() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return config_;
}

bool FastRouter::updateConfig(const RouterConfig& config) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!initialized_) {
        LOG_ERROR("Fast router not initialized");
        return false;
    }

    if (!validateConfig(config)) {
        LOG_ERROR("Invalid router configuration");
        return false;
    }

    try {
        // Update configuration
        config_ = config;
        LOG_INFO("Router configuration updated");
        return true;
    } catch (const std::exception& e) {
        LOG_ERROR("Error updating router configuration: {}", e.what());
        return false;
    }
}

void FastRouter::workerThread() {
    while (!should_stop_) {
        std::vector<RouterRequest> batch;
        {
            std::unique_lock<std::mutex> lock(mutex_);
            cv_.wait(lock, [this] {
                return should_stop_ || !request_queue_.empty();
            });

            if (should_stop_) {
                break;
            }

            batch = dequeueBatch(config_.batch_size);
        }

        if (!batch.empty()) {
            auto responses = processBatch(batch);
            
            // Handle async responses and update tracking
            std::lock_guard<std::mutex> lock(mutex_);
            for (const auto& response : responses) {
                // Update request tracking
                if (config_.enable_request_tracking) {
                    auto it = request_tracking_.find(response.request_id);
                    if (it != request_tracking_.end()) {
                        it->second.completion_time = std::chrono::system_clock::now();
                        it->second.completed = true;
                        it->second.error_message = response.error_message;
                    }
                }

                // Handle async response
                auto async_it = async_requests_.find(response.request_id);
                if (async_it != async_requests_.end()) {
                    async_it->second.set_value(response);
                    async_requests_.erase(async_it);
                }
            }
        }
    }
}

RouterResponse FastRouter::processRequest(const RouterRequest& request) {
    auto start_time = std::chrono::system_clock::now();
    RouterResponse response;
    response.request_id = request.request_id;
    response.timestamp = start_time;
    response.target_index = request.target_index.empty() ? "default_index" : request.target_index;

    try {
        // Process the request using vector search client
        SearchOptions options;
        options.top_k = 10;  // Default value, can be configured
        options.include_vectors = true;
        options.include_metadata = true;

        response.results = vector_client_->search(response.target_index, request.query_vector, options);
        response.success = true;

        auto end_time = std::chrono::system_clock::now();
        response.processing_time = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);

        // Update statistics
        updateQueueStats(request, response);
        
        // Update index usage statistics
        if (config_.enable_performance_monitoring) {
            stats_.index_usage[response.target_index]++;
        }

        return response;
    } catch (const std::exception& e) {
        response.success = false;
        response.error_message = e.what();
        stats_.failed_requests++;

        // Check if request should be retried
        if (shouldRetryRequest(request, e.what())) {
            retryRequest(request.request_id);
        }

        return response;
    }
}

void FastRouter::updateQueueStats(const RouterRequest& request, const RouterResponse& response) {
    stats_.total_requests++;
    if (response.success) {
        stats_.successful_requests++;
    } else {
        stats_.failed_requests++;
    }
    stats_.last_update = std::chrono::system_clock::now();

    // Update processing time statistics
    if (stats_.total_requests == 1) {
        stats_.min_processing_time = response.processing_time;
        stats_.max_processing_time = response.processing_time;
        stats_.average_processing_time = response.processing_time;
        stats_.min_queue_time = std::chrono::milliseconds(response.queue_wait_time);
        stats_.max_queue_time = std::chrono::milliseconds(response.queue_wait_time);
        stats_.average_queue_time = std::chrono::milliseconds(response.queue_wait_time);
    } else {
        stats_.min_processing_time = std::min(stats_.min_processing_time, response.processing_time);
        stats_.max_processing_time = std::max(stats_.max_processing_time, response.processing_time);
        stats_.average_processing_time = std::chrono::milliseconds(
            (stats_.average_processing_time.count() * (stats_.total_requests - 1) + 
             response.processing_time.count()) / stats_.total_requests
        );
        stats_.min_queue_time = std::min(stats_.min_queue_time, std::chrono::milliseconds(response.queue_wait_time));
        stats_.max_queue_time = std::max(stats_.max_queue_time, std::chrono::milliseconds(response.queue_wait_time));
        stats_.average_queue_time = std::chrono::milliseconds(
            (stats_.average_queue_time.count() * (stats_.total_requests - 1) + 
             response.queue_wait_time) / stats_.total_requests
        );
    }
}

bool FastRouter::shouldRetryRequest(const RouterRequest& request, const std::string& error) {
    // Check if error is retryable
    if (error.find("timeout") != std::string::npos ||
        error.find("connection") != std::string::npos ||
        error.find("temporary") != std::string::npos) {
        return true;
    }

    // Check retry count
    auto it = request_tracking_.find(request.request_id);
    if (it != request_tracking_.end() && it->second.retry_count >= config_.max_retries) {
        return false;
    }

    return false;
}

std::vector<RouterResponse> FastRouter::processBatch(const std::vector<RouterRequest>& requests) {
    std::vector<RouterResponse> responses;
    responses.reserve(requests.size());

    for (const auto& request : requests) {
        responses.push_back(processRequest(request));
    }

    return responses;
}

bool FastRouter::enqueueRequest(const RouterRequest& request) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (request_queue_.size() >= config_.max_queue_size) {
        LOG_ERROR("Request queue is full");
        return false;
    }

    request_queue_.push(request);
    stats_.queued_requests++;
    cv_.notify_one();
    return true;
}

bool FastRouter::dequeueRequest(RouterRequest& request) {
    if (request_queue_.empty()) {
        return false;
    }

    request = request_queue_.top();
    request_queue_.pop();
    stats_.queued_requests--;
    stats_.processing_requests++;
    return true;
}

std::vector<RouterRequest> FastRouter::dequeueBatch(size_t batch_size) {
    std::vector<RouterRequest> batch;
    batch.reserve(batch_size);

    while (!request_queue_.empty() && batch.size() < batch_size) {
        RouterRequest request;
        if (dequeueRequest(request)) {
            batch.push_back(std::move(request));
        }
    }

    return batch;
}

bool FastRouter::retryRequest(const std::string& request_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!initialized_) {
        LOG_ERROR("Fast router not initialized");
        return false;
    }

    try {
        auto it = request_tracking_.find(request_id);
        if (it == request_tracking_.end()) {
            LOG_ERROR("Request not found: {}", request_id);
            return false;
        }

        if (it->second.retry_count >= config_.max_retries) {
            LOG_ERROR("Maximum retry attempts reached for request: {}", request_id);
            return false;
        }

        // Create new request with retry information
        RouterRequest retry_request;
        retry_request.request_id = request_id;
        retry_request.priority = 1;  // Higher priority for retries
        retry_request.is_async = true;

        // Enqueue retry request
        if (!enqueueRequest(retry_request)) {
            LOG_ERROR("Failed to enqueue retry request: {}", request_id);
            return false;
        }

        it->second.retry_count++;
        stats_.retried_requests++;
        return true;
    } catch (const std::exception& e) {
        LOG_ERROR("Error retrying request: {}", e.what());
        return false;
    }
}

size_t FastRouter::getQueuePosition(const std::string& request_id) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!config_.enable_request_tracking) {
        return 0;
    }

    auto it = request_tracking_.find(request_id);
    if (it == request_tracking_.end()) {
        return 0;
    }

    return it->second.retry_count + 1;  // Position is retry count + 1
}

std::chrono::milliseconds FastRouter::getEstimatedWaitTime() const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (stats_.total_requests == 0) {
        return std::chrono::milliseconds(0);
    }

    return std::chrono::milliseconds(
        (stats_.average_processing_time.count() * request_queue_.size()) / config_.num_worker_threads
    );
}

RequestTracking FastRouter::getRequestTracking(const std::string& request_id) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!config_.enable_request_tracking) {
        return RequestTracking();
    }

    auto it = request_tracking_.find(request_id);
    if (it == request_tracking_.end()) {
        return RequestTracking();
    }

    return it->second;
}

std::vector<RequestTracking> FastRouter::getActiveRequests() const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!config_.enable_request_tracking) {
        return {};
    }

    std::vector<RequestTracking> active_requests;
    for (const auto& [id, tracking] : request_tracking_) {
        if (!tracking.completed) {
            active_requests.push_back(tracking);
        }
    }

    return active_requests;
}

bool FastRouter::validateRequest(const RouterRequest& request) const {
    if (request.request_id.empty()) {
        LOG_ERROR("Request ID cannot be empty");
        return false;
    }

    if (request.query_vector.empty()) {
        LOG_ERROR("Query vector cannot be empty");
        return false;
    }

    if (request.timeout.count() > 0 && request.timeout < std::chrono::milliseconds(100)) {
        LOG_ERROR("Timeout must be at least 100ms");
        return false;
    }

    return true;
}

bool FastRouter::validateConfig(const RouterConfig& config) const {
    if (config.max_queue_size == 0) {
        LOG_ERROR("Max queue size must be greater than 0");
        return false;
    }

    if (config.num_worker_threads == 0) {
        LOG_ERROR("Number of worker threads must be greater than 0");
        return false;
    }

    if (config.batch_size == 0) {
        LOG_ERROR("Batch size must be greater than 0");
        return false;
    }

    if (config.timeout.count() <= 0) {
        LOG_ERROR("Timeout must be greater than 0");
        return false;
    }

    if (config.max_retries == 0) {
        LOG_ERROR("Max retries must be greater than 0");
        return false;
    }

    if (config.retry_delay.count() <= 0) {
        LOG_ERROR("Retry delay must be greater than 0");
        return false;
    }

    return true;
}

} // namespace dream
} // namespace cogniware
