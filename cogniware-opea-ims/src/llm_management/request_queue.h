#pragma once

#include <memory>
#include <string>
#include <vector>
#include <queue>
#include <mutex>
#include <condition_variable>
#include <chrono>
#include <functional>

namespace cogniware {
namespace llm_management {

// Request status
enum class RequestStatus {
    PENDING,
    PROCESSING,
    COMPLETED,
    FAILED,
    CANCELLED
};

// Request priority
enum class RequestPriority {
    LOW,
    NORMAL,
    HIGH,
    CRITICAL
};

// Request structure
struct Request {
    std::string id;
    std::string model_id;
    std::string input;
    std::vector<std::string> output;
    RequestStatus status;
    RequestPriority priority;
    std::chrono::system_clock::time_point created_at;
    std::chrono::system_clock::time_point started_at;
    std::chrono::system_clock::time_point completed_at;
    std::string error_message;
    std::function<void(const Request&)> callback;

    Request() : 
        status(RequestStatus::PENDING),
        priority(RequestPriority::NORMAL),
        created_at(std::chrono::system_clock::now()) {}
};

// Request queue class
class RequestQueue {
public:
    RequestQueue();
    ~RequestQueue();

    // Prevent copying
    RequestQueue(const RequestQueue&) = delete;
    RequestQueue& operator=(const RequestQueue&) = delete;

    // Queue management
    void push(const Request& request);
    bool pop(Request& request);
    bool peek(Request& request) const;
    size_t size() const;
    bool empty() const;
    void clear();

    // Request management
    bool updateRequestStatus(const std::string& request_id, RequestStatus status);
    bool updateRequestOutput(const std::string& request_id, const std::vector<std::string>& output);
    bool updateRequestError(const std::string& request_id, const std::string& error_message);
    bool getRequest(const std::string& request_id, Request& request) const;
    bool cancelRequest(const std::string& request_id);

    // Queue configuration
    void setMaxQueueSize(size_t size);
    size_t getMaxQueueSize() const;
    void setRequestTimeout(std::chrono::seconds timeout);
    std::chrono::seconds getRequestTimeout() const;

    // Queue statistics
    size_t getPendingCount() const;
    size_t getProcessingCount() const;
    size_t getCompletedCount() const;
    size_t getFailedCount() const;
    size_t getCancelledCount() const;
    std::chrono::milliseconds getAverageProcessingTime() const;

private:
    // Internal implementation
    struct Impl;
    std::unique_ptr<Impl> pimpl;
};

} // namespace llm_management
} // namespace cogniware
