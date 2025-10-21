#pragma once

#include <string>
#include <vector>
#include <memory>
#include <unordered_map>
#include <chrono>
#include <functional>
#include <future>
#include <queue>

namespace cogniware {
namespace async_processing {

enum class JobStatus {
    PENDING,
    QUEUED,
    PROCESSING,
    COMPLETED,
    FAILED,
    CANCELLED,
    TIMEOUT
};

enum class JobPriority {
    LOW = 0,
    NORMAL = 50,
    HIGH = 100,
    CRITICAL = 200
};

struct Job {
    std::string job_id;
    std::string type;
    JobPriority priority;
    JobStatus status;
    std::unordered_map<std::string, std::string> parameters;
    std::string result;
    std::string error_message;
    std::chrono::system_clock::time_point created_at;
    std::chrono::system_clock::time_point started_at;
    std::chrono::system_clock::time_point completed_at;
    std::chrono::milliseconds execution_time;
};

struct JobResult {
    std::string job_id;
    bool success;
    std::string result;
    std::string error;
    std::chrono::milliseconds execution_time;
};

class AsyncProcessor {
public:
    AsyncProcessor(size_t num_workers = 4);
    ~AsyncProcessor();

    void start();
    void stop();
    bool isRunning() const;
    
    std::string submitJob(const std::string& type,
                         const std::unordered_map<std::string, std::string>& params,
                         JobPriority priority = JobPriority::NORMAL);
    
    JobStatus getJobStatus(const std::string& job_id);
    JobResult getJobResult(const std::string& job_id);
    bool cancelJob(const std::string& job_id);
    
    std::vector<Job> listJobs(JobStatus status = {});
    size_t getQueueSize() const;
    size_t getActiveJobs() const;

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

class ResultCache {
public:
    ResultCache(size_t max_size = 10000);
    ~ResultCache();

    void put(const std::string& key, const std::string& value,
            std::chrono::seconds ttl = std::chrono::hours(1));
    std::string get(const std::string& key);
    bool has(const std::string& key);
    void remove(const std::string& key);
    void clear();
    
    size_t size() const;
    double getHitRate() const;

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

class JobQueue {
public:
    JobQueue();
    ~JobQueue();

    void push(const Job& job);
    Job pop();
    bool empty() const;
    size_t size() const;
    void clear();

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

} // namespace async_processing
} // namespace cogniware

