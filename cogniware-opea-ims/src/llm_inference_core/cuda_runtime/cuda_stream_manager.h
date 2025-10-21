#pragma once

#include <cuda_runtime.h>
#include <memory>
#include <mutex>
#include <unordered_map>
#include <string>
#include <vector>

namespace cogniware {
namespace llm_inference {

// Stream priority levels
enum class StreamPriority {
    HIGH,
    NORMAL,
    LOW
};

// Stream flags
enum class StreamFlags {
    DEFAULT = 0,
    NON_BLOCKING = 1
};

// Stream information structure
struct StreamInfo {
    cudaStream_t stream;
    int device_id;
    StreamPriority priority;
    StreamFlags flags;
    std::string tag;
    bool is_active;
};

class CUDAStreamManager {
public:
    static CUDAStreamManager& getInstance();

    // Prevent copying
    CUDAStreamManager(const CUDAStreamManager&) = delete;
    CUDAStreamManager& operator=(const CUDAStreamManager&) = delete;

    // Stream creation and destruction
    cudaStream_t createStream(StreamPriority priority = StreamPriority::NORMAL,
                            StreamFlags flags = StreamFlags::DEFAULT,
                            const std::string& tag = "");

    void destroyStream(cudaStream_t stream);

    // Stream synchronization
    void synchronize(cudaStream_t stream);
    void synchronizeAll();

    // Stream status
    bool isStreamActive(cudaStream_t stream) const;
    void setStreamActive(cudaStream_t stream, bool active);

    // Stream information
    StreamInfo getStreamInfo(cudaStream_t stream) const;
    std::vector<StreamInfo> getAllStreams() const;
    size_t getStreamCount() const;

    // Stream properties
    void setStreamPriority(cudaStream_t stream, StreamPriority priority);
    void setStreamFlags(cudaStream_t stream, StreamFlags flags);
    void setStreamTag(cudaStream_t stream, const std::string& tag);

    // Cleanup
    void clear();
    void reset();

private:
    CUDAStreamManager();
    ~CUDAStreamManager();

    void initializeDevice(int device_id);
    void cleanupDevice(int device_id);
    bool checkStream(cudaStream_t stream) const;

    struct Impl;
    std::unique_ptr<Impl> pimpl;
};

// Helper functions
inline cudaStream_t createStream(StreamPriority priority = StreamPriority::NORMAL,
                               StreamFlags flags = StreamFlags::DEFAULT,
                               const std::string& tag = "") {
    return CUDAStreamManager::getInstance().createStream(priority, flags, tag);
}

inline void destroyStream(cudaStream_t stream) {
    CUDAStreamManager::getInstance().destroyStream(stream);
}

inline void synchronize(cudaStream_t stream) {
    CUDAStreamManager::getInstance().synchronize(stream);
}

inline void synchronizeAll() {
    CUDAStreamManager::getInstance().synchronizeAll();
}

inline bool isStreamActive(cudaStream_t stream) {
    return CUDAStreamManager::getInstance().isStreamActive(stream);
}

inline void setStreamActive(cudaStream_t stream, bool active) {
    CUDAStreamManager::getInstance().setStreamActive(stream, active);
}

inline StreamInfo getStreamInfo(cudaStream_t stream) {
    return CUDAStreamManager::getInstance().getStreamInfo(stream);
}

inline std::vector<StreamInfo> getAllStreams() {
    return CUDAStreamManager::getInstance().getAllStreams();
}

inline size_t getStreamCount() {
    return CUDAStreamManager::getInstance().getStreamCount();
}

inline void setStreamPriority(cudaStream_t stream, StreamPriority priority) {
    CUDAStreamManager::getInstance().setStreamPriority(stream, priority);
}

inline void setStreamFlags(cudaStream_t stream, StreamFlags flags) {
    CUDAStreamManager::getInstance().setStreamFlags(stream, flags);
}

inline void setStreamTag(cudaStream_t stream, const std::string& tag) {
    CUDAStreamManager::getInstance().setStreamTag(stream, tag);
}

inline void clearStreams() {
    CUDAStreamManager::getInstance().clear();
}

inline void resetStreams() {
    CUDAStreamManager::getInstance().reset();
}

} // namespace llm_inference
} // namespace cogniware
