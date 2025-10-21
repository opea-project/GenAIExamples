#include "request_queue.h"
#include <spdlog/spdlog.h>
#include <algorithm>
#include <unordered_map>
#include <deque>

namespace cogniware {
namespace llm_management {

// Internal implementation
struct RequestQueue::Impl {
    std::deque<Request> queue;
    std::unordered_map<std::string, Request> active_requests;
    std::mutex queue_mutex;
    std::condition_variable queue_cv;
    size_t max_queue_size;
    std::chrono::seconds request_timeout;
    size_t pending_count;
    size_t processing_count;
    size_t completed_count;
    size_t failed_count;
    size_t cancelled_count;
    std::chrono::milliseconds total_processing_time;
    size_t processed_requests;

    Impl() : 
        max_queue_size(1000),
        request_timeout(std::chrono::seconds(300)),
        pending_count(0),
        processing_count(0),
        completed_count(0),
        failed_count(0),
        cancelled_count(0),
        total_processing_time(std::chrono::milliseconds(0)),
        processed_requests(0) {}

    void updateRequestCounts(RequestStatus old_status, RequestStatus new_status) {
        switch (old_status) {
            case RequestStatus::PENDING:
                --pending_count;
                break;
            case RequestStatus::PROCESSING:
                --processing_count;
                break;
            case RequestStatus::COMPLETED:
                --completed_count;
                break;
            case RequestStatus::FAILED:
                --failed_count;
                break;
            case RequestStatus::CANCELLED:
                --cancelled_count;
                break;
        }

        switch (new_status) {
            case RequestStatus::PENDING:
                ++pending_count;
                break;
            case RequestStatus::PROCESSING:
                ++processing_count;
                break;
            case RequestStatus::COMPLETED:
                ++completed_count;
                break;
            case RequestStatus::FAILED:
                ++failed_count;
                break;
            case RequestStatus::CANCELLED:
                ++cancelled_count;
                break;
        }
    }
};

// Constructor and destructor
RequestQueue::RequestQueue() : pimpl(std::make_unique<Impl>()) {}

RequestQueue::~RequestQueue() = default;

// Queue management
void RequestQueue::push(const Request& request) {
    std::lock_guard<std::mutex> lock(pimpl->queue_mutex);
    
    if (pimpl->queue.size() >= pimpl->max_queue_size) {
        throw std::runtime_error("Queue is full");
    }

    pimpl->queue.push_back(request);
    pimpl->updateRequestCounts(RequestStatus::PENDING, request.status);
    pimpl->queue_cv.notify_one();
}

bool RequestQueue::pop(Request& request) {
    std::unique_lock<std::mutex> lock(pimpl->queue_mutex);
    
    if (pimpl->queue.empty()) {
        return false;
    }

    request = pimpl->queue.front();
    pimpl->queue.pop_front();
    pimpl->active_requests[request.id] = request;
    return true;
}

bool RequestQueue::peek(Request& request) const {
    std::lock_guard<std::mutex> lock(pimpl->queue_mutex);
    
    if (pimpl->queue.empty()) {
        return false;
    }

    request = pimpl->queue.front();
    return true;
}

size_t RequestQueue::size() const {
    std::lock_guard<std::mutex> lock(pimpl->queue_mutex);
    return pimpl->queue.size();
}

bool RequestQueue::empty() const {
    std::lock_guard<std::mutex> lock(pimpl->queue_mutex);
    return pimpl->queue.empty();
}

void RequestQueue::clear() {
    std::lock_guard<std::mutex> lock(pimpl->queue_mutex);
    pimpl->queue.clear();
    pimpl->active_requests.clear();
    pimpl->pending_count = 0;
    pimpl->processing_count = 0;
    pimpl->completed_count = 0;
    pimpl->failed_count = 0;
    pimpl->cancelled_count = 0;
}

// Request management
bool RequestQueue::updateRequestStatus(const std::string& request_id, RequestStatus status) {
    std::lock_guard<std::mutex> lock(pimpl->queue_mutex);
    
    auto it = pimpl->active_requests.find(request_id);
    if (it == pimpl->active_requests.end()) {
        return false;
    }

    RequestStatus old_status = it->second.status;
    it->second.status = status;

    if (status == RequestStatus::PROCESSING) {
        it->second.started_at = std::chrono::system_clock::now();
    } else if (status == RequestStatus::COMPLETED || status == RequestStatus::FAILED) {
        it->second.completed_at = std::chrono::system_clock::now();
        if (status == RequestStatus::COMPLETED) {
            auto processing_time = std::chrono::duration_cast<std::chrono::milliseconds>(
                it->second.completed_at - it->second.started_at);
            pimpl->total_processing_time += processing_time;
            ++pimpl->processed_requests;
        }
        if (it->second.callback) {
            it->second.callback(it->second);
        }
    }

    pimpl->updateRequestCounts(old_status, status);
    return true;
}

bool RequestQueue::updateRequestOutput(const std::string& request_id, const std::vector<std::string>& output) {
    std::lock_guard<std::mutex> lock(pimpl->queue_mutex);
    
    auto it = pimpl->active_requests.find(request_id);
    if (it == pimpl->active_requests.end()) {
        return false;
    }

    it->second.output = output;
    return true;
}

bool RequestQueue::updateRequestError(const std::string& request_id, const std::string& error_message) {
    std::lock_guard<std::mutex> lock(pimpl->queue_mutex);
    
    auto it = pimpl->active_requests.find(request_id);
    if (it == pimpl->active_requests.end()) {
        return false;
    }

    it->second.error_message = error_message;
    return true;
}

bool RequestQueue::getRequest(const std::string& request_id, Request& request) const {
    std::lock_guard<std::mutex> lock(pimpl->queue_mutex);
    
    auto it = pimpl->active_requests.find(request_id);
    if (it == pimpl->active_requests.end()) {
        return false;
    }

    request = it->second;
    return true;
}

bool RequestQueue::cancelRequest(const std::string& request_id) {
    std::lock_guard<std::mutex> lock(pimpl->queue_mutex);
    
    auto it = pimpl->active_requests.find(request_id);
    if (it == pimpl->active_requests.end()) {
        return false;
    }

    if (it->second.status == RequestStatus::PENDING) {
        auto queue_it = std::find_if(pimpl->queue.begin(), pimpl->queue.end(),
                                   [&](const Request& req) { return req.id == request_id; });
        if (queue_it != pimpl->queue.end()) {
            pimpl->queue.erase(queue_it);
        }
    }

    pimpl->updateRequestCounts(it->second.status, RequestStatus::CANCELLED);
    it->second.status = RequestStatus::CANCELLED;
    return true;
}

// Queue configuration
void RequestQueue::setMaxQueueSize(size_t size) {
    std::lock_guard<std::mutex> lock(pimpl->queue_mutex);
    pimpl->max_queue_size = size;
}

size_t RequestQueue::getMaxQueueSize() const {
    return pimpl->max_queue_size;
}

void RequestQueue::setRequestTimeout(std::chrono::seconds timeout) {
    pimpl->request_timeout = timeout;
}

std::chrono::seconds RequestQueue::getRequestTimeout() const {
    return pimpl->request_timeout;
}

// Queue statistics
size_t RequestQueue::getPendingCount() const {
    return pimpl->pending_count;
}

size_t RequestQueue::getProcessingCount() const {
    return pimpl->processing_count;
}

size_t RequestQueue::getCompletedCount() const {
    return pimpl->completed_count;
}

size_t RequestQueue::getFailedCount() const {
    return pimpl->failed_count;
}

size_t RequestQueue::getCancelledCount() const {
    return pimpl->cancelled_count;
}

std::chrono::milliseconds RequestQueue::getAverageProcessingTime() const {
    if (pimpl->processed_requests == 0) {
        return std::chrono::milliseconds(0);
    }
    return pimpl->total_processing_time / pimpl->processed_requests;
}

} // namespace llm_management
} // namespace cogniware
