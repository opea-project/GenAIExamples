#pragma once

#include <memory>
#include <string>
#include <vector>
#include <mutex>
#include <condition_variable>
#include <chrono>
#include <functional>

namespace cogniware {
namespace llm_management {

// Concurrency limits
struct ConcurrencyLimits {
    size_t max_concurrent_requests;    // Maximum number of concurrent requests
    size_t max_requests_per_second;    // Maximum number of requests per second
    size_t max_batch_size;            // Maximum batch size for processing
    std::chrono::milliseconds max_request_timeout;  // Maximum request timeout

    ConcurrencyLimits() :
        max_concurrent_requests(10),
        max_requests_per_second(100),
        max_batch_size(32),
        max_request_timeout(std::chrono::seconds(300)) {}
};

// Concurrency statistics
struct ConcurrencyStats {
    size_t current_concurrent_requests;
    size_t requests_processed_last_second;
    size_t total_requests_processed;
    std::chrono::system_clock::time_point last_reset_time;
    std::chrono::milliseconds average_request_time;

    ConcurrencyStats() :
        current_concurrent_requests(0),
        requests_processed_last_second(0),
        total_requests_processed(0),
        last_reset_time(std::chrono::system_clock::now()),
        average_request_time(std::chrono::milliseconds(0)) {}
};

// Concurrency controller class
class ConcurrencyController {
public:
    ConcurrencyController();
    ~ConcurrencyController();

    // Prevent copying
    ConcurrencyController(const ConcurrencyController&) = delete;
    ConcurrencyController& operator=(const ConcurrencyController&) = delete;

    // Configuration
    void setLimits(const ConcurrencyLimits& limits);
    ConcurrencyLimits getLimits() const;
    void setRequestTimeout(std::chrono::milliseconds timeout);
    std::chrono::milliseconds getRequestTimeout() const;

    // Request management
    bool acquireRequestSlot();
    void releaseRequestSlot();
    bool canProcessRequest() const;
    void updateRequestStats(std::chrono::milliseconds processing_time);

    // Statistics
    ConcurrencyStats getStats() const;
    void resetStats();
    std::string getStatus() const;

    // Rate limiting
    bool checkRateLimit() const;
    void updateRateLimit();
    size_t getAvailableSlots() const;

    // Batch processing
    size_t getOptimalBatchSize() const;
    bool canProcessBatch(size_t batch_size) const;

private:
    // Internal implementation
    struct Impl;
    std::unique_ptr<Impl> pimpl;
};

} // namespace llm_management
} // namespace cogniware
