#include "concurrency_controller.h"
#include <spdlog/spdlog.h>
#include <sstream>
#include <deque>

namespace cogniware {
namespace llm_management {

// Internal implementation
struct ConcurrencyController::Impl {
    ConcurrencyLimits limits;
    ConcurrencyStats stats;
    std::mutex controller_mutex;
    std::condition_variable slot_cv;
    std::deque<std::chrono::system_clock::time_point> request_timestamps;
    std::chrono::milliseconds total_processing_time;
    size_t processed_requests;

    Impl() : 
        total_processing_time(std::chrono::milliseconds(0)),
        processed_requests(0) {}

    void updateRateLimitStats() {
        auto now = std::chrono::system_clock::now();
        auto one_second_ago = now - std::chrono::seconds(1);

        // Remove old timestamps
        while (!request_timestamps.empty() && request_timestamps.front() < one_second_ago) {
            request_timestamps.pop_front();
        }

        stats.requests_processed_last_second = request_timestamps.size();
    }

    void updateAverageRequestTime(std::chrono::milliseconds processing_time) {
        total_processing_time += processing_time;
        ++processed_requests;
        stats.average_request_time = total_processing_time / processed_requests;
    }
};

// Constructor and destructor
ConcurrencyController::ConcurrencyController() : pimpl(std::make_unique<Impl>()) {}

ConcurrencyController::~ConcurrencyController() = default;

// Configuration
void ConcurrencyController::setLimits(const ConcurrencyLimits& limits) {
    std::lock_guard<std::mutex> lock(pimpl->controller_mutex);
    pimpl->limits = limits;
}

ConcurrencyLimits ConcurrencyController::getLimits() const {
    return pimpl->limits;
}

void ConcurrencyController::setRequestTimeout(std::chrono::milliseconds timeout) {
    std::lock_guard<std::mutex> lock(pimpl->controller_mutex);
    pimpl->limits.max_request_timeout = timeout;
}

std::chrono::milliseconds ConcurrencyController::getRequestTimeout() const {
    return pimpl->limits.max_request_timeout;
}

// Request management
bool ConcurrencyController::acquireRequestSlot() {
    std::unique_lock<std::mutex> lock(pimpl->controller_mutex);
    
    if (pimpl->stats.current_concurrent_requests >= pimpl->limits.max_concurrent_requests) {
        return false;
    }

    if (!checkRateLimit()) {
        return false;
    }

    ++pimpl->stats.current_concurrent_requests;
    pimpl->request_timestamps.push_back(std::chrono::system_clock::now());
    return true;
}

void ConcurrencyController::releaseRequestSlot() {
    std::lock_guard<std::mutex> lock(pimpl->controller_mutex);
    if (pimpl->stats.current_concurrent_requests > 0) {
        --pimpl->stats.current_concurrent_requests;
    }
    pimpl->slot_cv.notify_one();
}

bool ConcurrencyController::canProcessRequest() const {
    std::lock_guard<std::mutex> lock(pimpl->controller_mutex);
    return pimpl->stats.current_concurrent_requests < pimpl->limits.max_concurrent_requests &&
           checkRateLimit();
}

void ConcurrencyController::updateRequestStats(std::chrono::milliseconds processing_time) {
    std::lock_guard<std::mutex> lock(pimpl->controller_mutex);
    pimpl->updateAverageRequestTime(processing_time);
    ++pimpl->stats.total_requests_processed;
}

// Statistics
ConcurrencyStats ConcurrencyController::getStats() const {
    std::lock_guard<std::mutex> lock(pimpl->controller_mutex);
    return pimpl->stats;
}

void ConcurrencyController::resetStats() {
    std::lock_guard<std::mutex> lock(pimpl->controller_mutex);
    pimpl->stats = ConcurrencyStats();
    pimpl->request_timestamps.clear();
    pimpl->total_processing_time = std::chrono::milliseconds(0);
    pimpl->processed_requests = 0;
}

std::string ConcurrencyController::getStatus() const {
    std::lock_guard<std::mutex> lock(pimpl->controller_mutex);
    std::stringstream ss;
    ss << "Current Concurrent Requests: " << pimpl->stats.current_concurrent_requests << " / "
       << pimpl->limits.max_concurrent_requests << "\n"
       << "Requests Last Second: " << pimpl->stats.requests_processed_last_second << " / "
       << pimpl->limits.max_requests_per_second << "\n"
       << "Total Requests Processed: " << pimpl->stats.total_requests_processed << "\n"
       << "Average Request Time: " << pimpl->stats.average_request_time.count() << " ms\n"
       << "Max Batch Size: " << pimpl->limits.max_batch_size << "\n"
       << "Request Timeout: " << pimpl->limits.max_request_timeout.count() << " ms";
    return ss.str();
}

// Rate limiting
bool ConcurrencyController::checkRateLimit() const {
    pimpl->updateRateLimitStats();
    return pimpl->stats.requests_processed_last_second < pimpl->limits.max_requests_per_second;
}

void ConcurrencyController::updateRateLimit() {
    std::lock_guard<std::mutex> lock(pimpl->controller_mutex);
    pimpl->updateRateLimitStats();
}

size_t ConcurrencyController::getAvailableSlots() const {
    std::lock_guard<std::mutex> lock(pimpl->controller_mutex);
    return pimpl->limits.max_concurrent_requests - pimpl->stats.current_concurrent_requests;
}

// Batch processing
size_t ConcurrencyController::getOptimalBatchSize() const {
    std::lock_guard<std::mutex> lock(pimpl->controller_mutex);
    size_t available_slots = getAvailableSlots();
    return std::min(available_slots, pimpl->limits.max_batch_size);
}

bool ConcurrencyController::canProcessBatch(size_t batch_size) const {
    std::lock_guard<std::mutex> lock(pimpl->controller_mutex);
    return batch_size <= pimpl->limits.max_batch_size &&
           pimpl->stats.current_concurrent_requests + batch_size <= pimpl->limits.max_concurrent_requests &&
           checkRateLimit();
}

} // namespace llm_management
} // namespace cogniware
