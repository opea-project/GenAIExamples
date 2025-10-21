#pragma once

#include <cuda_runtime.h>
#include <string>
#include <vector>
#include <memory>
#include <functional>

namespace cogniware {
namespace llm_inference {

// Stream priority levels
enum class StreamPriority {
    HIGH = -1,
    NORMAL = 0,
    LOW = 1
};

// Stream flags
enum class StreamFlags {
    DEFAULT = cudaStreamDefault,
    NON_BLOCKING = cudaStreamNonBlocking
};

// Stream info
struct StreamInfo {
    cudaStream_t stream;        // CUDA stream handle
    int device_id;             // Device ID
    StreamPriority priority;    // Stream priority
    StreamFlags flags;          // Stream flags
    std::string tag;           // Optional tag for debugging
    bool is_active;            // Whether stream is active
};

// Stream manager class
class CUDAStreamManager {
public:
    static CUDAStreamManager& getInstance();

    // Stream creation and destruction
    cudaStream_t createStream(StreamPriority priority = StreamPriority::NORMAL,
                            StreamFlags flags = StreamFlags::DEFAULT,
                            const std::string& tag = "");
    void destroyStream(cudaStream_t stream);

    // Stream operations
    void synchronize(cudaStream_t stream);
    void synchronizeAll();
    bool isStreamActive(cudaStream_t stream) const;
    void setStreamActive(cudaStream_t stream, bool active);

    // Stream info
    StreamInfo getStreamInfo(cudaStream_t stream) const;
    std::vector<StreamInfo> getAllStreams() const;
    int getStreamCount() const;

    // Stream management
    void setStreamPriority(cudaStream_t stream, StreamPriority priority);
    void setStreamFlags(cudaStream_t stream, StreamFlags flags);
    void setStreamTag(cudaStream_t stream, const std::string& tag);

    // Stream cleanup
    void clear();
    void reset();

private:
    CUDAStreamManager();
    ~CUDAStreamManager();

    // Prevent copying
    CUDAStreamManager(const CUDAStreamManager&) = delete;
    CUDAStreamManager& operator=(const CUDAStreamManager&) = delete;

    // Helper functions
    void initializeDevice(int device_id);
    void cleanupDevice(int device_id);
    void checkStream(cudaStream_t stream) const;

    // Internal state
    struct Impl;
    std::unique_ptr<Impl> pimpl;
};

// Helper functions
cudaStream_t createStream(StreamPriority priority = StreamPriority::NORMAL,
                         StreamFlags flags = StreamFlags::DEFAULT);
void destroyStream(cudaStream_t stream);
void synchronizeStream(cudaStream_t stream);
void synchronizeAllStreams();
bool isStreamActive(cudaStream_t stream);
void setStreamActive(cudaStream_t stream, bool active);
void setStreamPriority(cudaStream_t stream, StreamPriority priority);
void setStreamFlags(cudaStream_t stream, StreamFlags flags);

// Stream callback
using StreamCallback = std::function<void(cudaStream_t, cudaError_t, void*)>;
void addStreamCallback(cudaStream_t stream, StreamCallback callback, void* userData);

} // namespace llm_inference
} // namespace cogniware 