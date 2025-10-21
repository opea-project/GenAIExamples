#include "llm_inference_core/concurrency/concurrency_controller.h"
#include "llm_inference_core/llm_management/llm_instance_manager.h"
#include <algorithm>
#include <chrono>

namespace cogniware {

ConcurrencyController& ConcurrencyController::getInstance() {
    static ConcurrencyController instance;
    return instance;
}

ConcurrencyController::ConcurrencyController()
    : maxConcurrentRequests_(4)
    , maxBatchSize_(8)
    , running_(false)
    , activeRequestCount_(0) {
}

ConcurrencyController::~ConcurrencyController() {
    stop();
}

bool ConcurrencyController::start() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (running_) {
        lastError_ = "Controller is already running";
        return false;
    }
    
    running_ = true;
    
    // Create worker threads
    for (size_t i = 0; i < maxConcurrentRequests_; ++i) {
        workerThreads_.emplace_back(&ConcurrencyController::workerThread, this);
    }
    
    return true;
}

void ConcurrencyController::stop() {
    {
        std::lock_guard<std::mutex> lock(mutex_);
        if (!running_) {
            return;
        }
        
        running_ = false;
    }
    
    // Notify all worker threads
    cv_.notify_all();
    
    // Wait for all threads to finish
    for (auto& thread : workerThreads_) {
        if (thread.joinable()) {
            thread.join();
        }
    }
    
    workerThreads_.clear();
    
    // Clear the request queue
    std::queue<Request> empty;
    std::swap(requestQueue_, empty);
}

bool ConcurrencyController::isRunning() const {
    return running_;
}

bool ConcurrencyController::submitRequest(const Request& request) {
    if (!running_) {
        lastError_ = "Controller is not running";
        return false;
    }
    
    if (!addToQueue(request)) {
        return false;
    }
    
    cv_.notify_one();
    return true;
}

bool ConcurrencyController::cancelRequest(const std::string& requestId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!removeFromQueue(requestId)) {
        lastError_ = "Request not found in queue";
        return false;
    }
    
    return true;
}

void ConcurrencyController::setMaxConcurrentRequests(size_t maxRequests) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (running_) {
        lastError_ = "Cannot change max concurrent requests while running";
        return;
    }
    
    maxConcurrentRequests_ = maxRequests;
}

void ConcurrencyController::setMaxBatchSize(size_t maxBatchSize) {
    std::lock_guard<std::mutex> lock(mutex_);
    maxBatchSize_ = maxBatchSize;
}

size_t ConcurrencyController::getQueueSize() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return requestQueue_.size();
}

size_t ConcurrencyController::getActiveRequestCount() const {
    return activeRequestCount_;
}

const char* ConcurrencyController::getLastError() const {
    return lastError_.c_str();
}

void ConcurrencyController::clearLastError() {
    lastError_.clear();
}

void ConcurrencyController::workerThread() {
    while (true) {
        std::vector<Request> batch;
        
        {
            std::unique_lock<std::mutex> lock(mutex_);
            
            // Wait for requests or stop signal
            cv_.wait(lock, [this] {
                return !running_ || !requestQueue_.empty();
            });
            
            if (!running_) {
                break;
            }
            
            // Get next batch of requests
            batch = getNextBatch();
        }
        
        if (!batch.empty()) {
            processBatch(batch);
        }
    }
}

void ConcurrencyController::processRequest(const Request& request) {
    auto& instanceManager = LLMInstanceManager::getInstance();
    auto instance = instanceManager.getInstance(request.modelId);
    
    if (!instance) {
        lastError_ = "Model instance not found: " + request.modelId;
        return;
    }
    
    std::vector<int> outputIds;
    if (!instance->generate(request.inputIds,
                          outputIds,
                          request.maxLength,
                          request.temperature,
                          request.topK,
                          request.topP)) {
        lastError_ = "Generation failed: " + std::string(instance->getLastError());
        return;
    }
    
    if (request.callback) {
        request.callback(outputIds);
    }
}

void ConcurrencyController::processBatch(const std::vector<Request>& batch) {
    activeRequestCount_ += batch.size();
    
    for (const auto& request : batch) {
        processRequest(request);
    }
    
    activeRequestCount_ -= batch.size();
}

bool ConcurrencyController::addToQueue(const Request& request) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (requestQueue_.size() >= maxBatchSize_ * maxConcurrentRequests_) {
        lastError_ = "Request queue is full";
        return false;
    }
    
    requestQueue_.push(request);
    return true;
}

bool ConcurrencyController::removeFromQueue(const std::string& requestId) {
    std::queue<Request> tempQueue;
    bool found = false;
    
    while (!requestQueue_.empty()) {
        Request request = requestQueue_.front();
        requestQueue_.pop();
        
        if (request.modelId == requestId) {
            found = true;
        } else {
            tempQueue.push(request);
        }
    }
    
    requestQueue_ = std::move(tempQueue);
    return found;
}

std::vector<Request> ConcurrencyController::getNextBatch() {
    std::vector<Request> batch;
    batch.reserve(maxBatchSize_);
    
    while (!requestQueue_.empty() && batch.size() < maxBatchSize_) {
        batch.push_back(requestQueue_.front());
        requestQueue_.pop();
    }
    
    return batch;
}

} // namespace cogniware 