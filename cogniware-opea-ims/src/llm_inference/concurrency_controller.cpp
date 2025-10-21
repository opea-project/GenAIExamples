#include "../../include/concurrency_controller.h"
#include <chrono>
#include <algorithm>
#include <spdlog/spdlog.h>

namespace cogniware {

ConcurrencyController& ConcurrencyController::getInstance() {
    static ConcurrencyController instance;
    return instance;
}

ConcurrencyController::ConcurrencyController()
    : running_(false)
    , active_requests_(0)
    , max_concurrent_requests_(4)
    , max_batch_size_(8)
{
    // Create worker threads
    size_t num_threads = std::thread::hardware_concurrency();
    worker_threads_.reserve(num_threads);
    for (size_t i = 0; i < num_threads; ++i) {
        worker_threads_.emplace_back(&ConcurrencyController::workerThread, this);
    }
}

ConcurrencyController::~ConcurrencyController() {
    stop();
    for (auto& thread : worker_threads_) {
        if (thread.joinable()) {
            thread.join();
        }
    }
}

bool ConcurrencyController::submitRequest(const InferenceRequest& request) {
    if (!running_) {
        return false;
    }

    std::lock_guard<std::mutex> lock(queue_mutex_);
    request_queue_.push(request);
    queue_cv_.notify_one();
    return true;
}

void ConcurrencyController::cancelRequest(const std::string& request_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Find the request in the queue
    auto it = std::find_if(
        request_queue_.begin(),
        request_queue_.end(),
        [&](const auto& request) { return request.id == request_id; }
    );
    
    if (it != request_queue_.end()) {
        // Remove from queue
        request_queue_.erase(it);
        
        // Notify waiting threads
        cv_.notify_all();
        
        // Update statistics
        stats_.cancelled_requests++;
        
        // Log cancellation
        logger_->info("Request {} cancelled", request_id);
    } else {
        // Check if request is currently being processed
        auto processing_it = std::find_if(
            processing_requests_.begin(),
            processing_requests_.end(),
            [&](const auto& request) { return request.id == request_id; }
        );
        
        if (processing_it != processing_requests_.end()) {
            // Mark request for cancellation
            processing_it->cancelled = true;
            
            // Notify the processing thread
            cv_.notify_all();
            
            // Update statistics
            stats_.cancelled_requests++;
            
            // Log cancellation
            logger_->info("Request {} marked for cancellation", request_id);
        } else {
            logger_->warn("Request {} not found for cancellation", request_id);
        }
    }
}

bool ConcurrencyController::isRequestCancelled(const std::string& request_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Check if request is marked for cancellation
    auto it = std::find_if(
        processing_requests_.begin(),
        processing_requests_.end(),
        [&](const auto& request) { return request.id == request_id; }
    );
    
    return it != processing_requests_.end() && it->cancelled;
}

void ConcurrencyController::setMaxConcurrentRequests(size_t max_requests) {
    std::lock_guard<std::mutex> lock(queue_mutex_);
    max_concurrent_requests_ = max_requests;
}

void ConcurrencyController::setMaxBatchSize(size_t max_batch_size) {
    std::lock_guard<std::mutex> lock(queue_mutex_);
    max_batch_size_ = max_batch_size;
}

size_t ConcurrencyController::getCurrentQueueSize() const {
    std::lock_guard<std::mutex> lock(queue_mutex_);
    return request_queue_.size();
}

size_t ConcurrencyController::getActiveRequestCount() const {
    return active_requests_;
}

void ConcurrencyController::start() {
    std::lock_guard<std::mutex> lock(queue_mutex_);
    if (!running_) {
        running_ = true;
        queue_cv_.notify_all();
        spdlog::info("ConcurrencyController started");
    }
}

void ConcurrencyController::stop() {
    std::lock_guard<std::mutex> lock(queue_mutex_);
    if (running_) {
        running_ = false;
        queue_cv_.notify_all();
        spdlog::info("ConcurrencyController stopped");
    }
}

bool ConcurrencyController::isRunning() const {
    return running_;
}

void ConcurrencyController::workerThread() {
    while (true) {
        std::unique_lock<std::mutex> lock(queue_mutex_);
        queue_cv_.wait(lock, [this] {
            return !running_ || !request_queue_.empty();
        });

        if (!running_ && request_queue_.empty()) {
            break;
        }

        // Collect requests for batching
        std::vector<InferenceRequest> batch;
        batch.reserve(max_batch_size_);

        while (!request_queue_.empty() && batch.size() < max_batch_size_) {
            batch.push_back(request_queue_.front());
            request_queue_.pop();
        }

        lock.unlock();

        // Process the batch
        if (!batch.empty()) {
            processBatch(batch);
        }
    }
}

bool ConcurrencyController::processBatch(const std::vector<InferenceRequest>& batch) {
    try {
        if (batch.empty()) {
            return true;
        }

        // Get the model ID from the first request
        const std::string& model_id = batch[0].model_id;

        // Check if all requests are for the same model
        for (const auto& request : batch) {
            if (request.model_id != model_id) {
                spdlog::error("Batch contains requests for different models");
                return false;
            }
        }

        // Get model instance
        auto& instance_manager = LLMInstanceManager::getInstance();
        if (!instance_manager.isModelLoaded(model_id)) {
            spdlog::error("Model {} is not loaded", model_id);
            return false;
        }

        // Prepare batch inputs
        std::vector<std::string> prompts;
        std::vector<std::unordered_map<std::string, std::string>> parameters;
        prompts.reserve(batch.size());
        parameters.reserve(batch.size());

        for (const auto& request : batch) {
            prompts.push_back(request.prompt);
            parameters.push_back(request.parameters);
        }

        // Process batch
        std::vector<std::string> outputs;
        if (!instance_manager.batchGenerate(model_id, prompts, parameters, outputs)) {
            spdlog::error("Batch generation failed for model {}", model_id);
            return false;
        }

        // Send results back to callbacks
        for (size_t i = 0; i < batch.size(); ++i) {
            if (batch[i].callback) {
                batch[i].callback(outputs[i]);
            }
        }

        return true;
    } catch (const std::exception& e) {
        spdlog::error("Error processing batch: {}", e.what());
        return false;
    }
}

} // namespace cogniware 