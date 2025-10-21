#include "cuda_stream.h"
#include "cuda_utils.h"
#include <spdlog/spdlog.h>
#include <unordered_map>
#include <mutex>
#include <stdexcept>

namespace msmartcompute {
namespace llm_inference {

// Implementation of CUDAStreamManager
struct CUDAStreamManager::Impl {
    std::unordered_map<cudaStream_t, StreamInfo> streams;
    std::mutex mutex;
};

CUDAStreamManager& CUDAStreamManager::getInstance() {
    static CUDAStreamManager instance;
    return instance;
}

CUDAStreamManager::CUDAStreamManager() : pimpl(std::make_unique<Impl>()) {
    // Initialize stream manager
    int device_count = getDeviceCount();
    for (int i = 0; i < device_count; ++i) {
        initializeDevice(i);
    }
}

CUDAStreamManager::~CUDAStreamManager() {
    clear();
}

void CUDAStreamManager::initializeDevice(int device_id) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    // Set device
    setDevice(device_id);
    
    spdlog::info("Initialized CUDA stream manager for device {}", device_id);
}

void CUDAStreamManager::cleanupDevice(int device_id) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    // Destroy all streams for this device
    for (auto it = pimpl->streams.begin(); it != pimpl->streams.end();) {
        if (it->second.device_id == device_id) {
            destroyStream(it->first);
            it = pimpl->streams.erase(it);
        } else {
            ++it;
        }
    }
}

void CUDAStreamManager::checkStream(cudaStream_t stream) const {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    if (pimpl->streams.find(stream) == pimpl->streams.end()) {
        throw std::runtime_error("Unknown stream");
    }
}

cudaStream_t CUDAStreamManager::createStream(StreamPriority priority, StreamFlags flags, const std::string& tag) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    int device_id = getCurrentDevice();
    
    try {
        // Create stream
        cudaStream_t stream;
        CUDA_CHECK(cudaStreamCreateWithPriority(&stream, static_cast<cudaStreamFlags>(flags), static_cast<int>(priority)));
        
        // Record stream info
        StreamInfo info{
            stream,
            device_id,
            priority,
            flags,
            tag,
            true
        };
        pimpl->streams[stream] = info;
        
        spdlog::debug("Created CUDA stream on device {} with priority {} and tag '{}'",
                     device_id, static_cast<int>(priority), tag);
        
        return stream;
    } catch (const std::exception& e) {
        spdlog::error("Failed to create CUDA stream: {}", e.what());
        throw;
    }
}

void CUDAStreamManager::destroyStream(cudaStream_t stream) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    auto it = pimpl->streams.find(stream);
    if (it == pimpl->streams.end()) {
        throw std::runtime_error("Attempt to destroy unknown stream");
    }
    
    try {
        // Synchronize stream before destroying
        synchronize(stream);
        
        // Destroy stream
        CUDA_CHECK(cudaStreamDestroy(stream));
        
        // Remove stream info
        pimpl->streams.erase(it);
        
        spdlog::debug("Destroyed CUDA stream with tag '{}'", it->second.tag);
    } catch (const std::exception& e) {
        spdlog::error("Failed to destroy CUDA stream: {}", e.what());
        throw;
    }
}

void CUDAStreamManager::synchronize(cudaStream_t stream) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    checkStream(stream);
    
    try {
        CUDA_CHECK(cudaStreamSynchronize(stream));
    } catch (const std::exception& e) {
        spdlog::error("Failed to synchronize CUDA stream: {}", e.what());
        throw;
    }
}

void CUDAStreamManager::synchronizeAll() {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    try {
        for (const auto& pair : pimpl->streams) {
            if (pair.second.is_active) {
                CUDA_CHECK(cudaStreamSynchronize(pair.first));
            }
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to synchronize all CUDA streams: {}", e.what());
        throw;
    }
}

bool CUDAStreamManager::isStreamActive(cudaStream_t stream) const {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    checkStream(stream);
    return pimpl->streams.at(stream).is_active;
}

void CUDAStreamManager::setStreamActive(cudaStream_t stream, bool active) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    checkStream(stream);
    pimpl->streams[stream].is_active = active;
}

StreamInfo CUDAStreamManager::getStreamInfo(cudaStream_t stream) const {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    checkStream(stream);
    return pimpl->streams.at(stream);
}

std::vector<StreamInfo> CUDAStreamManager::getAllStreams() const {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    std::vector<StreamInfo> result;
    result.reserve(pimpl->streams.size());
    for (const auto& pair : pimpl->streams) {
        result.push_back(pair.second);
    }
    return result;
}

int CUDAStreamManager::getStreamCount() const {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    return static_cast<int>(pimpl->streams.size());
}

void CUDAStreamManager::setStreamPriority(cudaStream_t stream, StreamPriority priority) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    checkStream(stream);
    
    try {
        CUDA_CHECK(cudaStreamSetPriority(stream, static_cast<int>(priority)));
        pimpl->streams[stream].priority = priority;
    } catch (const std::exception& e) {
        spdlog::error("Failed to set stream priority: {}", e.what());
        throw;
    }
}

void CUDAStreamManager::setStreamFlags(cudaStream_t stream, StreamFlags flags) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    checkStream(stream);
    pimpl->streams[stream].flags = flags;
}

void CUDAStreamManager::setStreamTag(cudaStream_t stream, const std::string& tag) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    checkStream(stream);
    pimpl->streams[stream].tag = tag;
}

void CUDAStreamManager::clear() {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    // Destroy all streams
    for (const auto& pair : pimpl->streams) {
        try {
            destroyStream(pair.first);
        } catch (const std::exception& e) {
            spdlog::error("Failed to destroy stream during clear: {}", e.what());
        }
    }
    
    pimpl->streams.clear();
}

void CUDAStreamManager::reset() {
    clear();
    
    // Reinitialize all devices
    int device_count = getDeviceCount();
    for (int i = 0; i < device_count; ++i) {
        initializeDevice(i);
    }
}

// Helper function implementations
cudaStream_t createStream(StreamPriority priority, StreamFlags flags) {
    return CUDAStreamManager::getInstance().createStream(priority, flags);
}

void destroyStream(cudaStream_t stream) {
    CUDAStreamManager::getInstance().destroyStream(stream);
}

void synchronizeStream(cudaStream_t stream) {
    CUDAStreamManager::getInstance().synchronize(stream);
}

void synchronizeAllStreams() {
    CUDAStreamManager::getInstance().synchronizeAll();
}

bool isStreamActive(cudaStream_t stream) {
    return CUDAStreamManager::getInstance().isStreamActive(stream);
}

void setStreamActive(cudaStream_t stream, bool active) {
    CUDAStreamManager::getInstance().setStreamActive(stream, active);
}

void setStreamPriority(cudaStream_t stream, StreamPriority priority) {
    CUDAStreamManager::getInstance().setStreamPriority(stream, priority);
}

void setStreamFlags(cudaStream_t stream, StreamFlags flags) {
    CUDAStreamManager::getInstance().setStreamFlags(stream, flags);
}

// Stream callback implementation
void CUDART_CB streamCallback(cudaStream_t stream, cudaError_t status, void* userData) {
    auto* callback = static_cast<StreamCallback*>(userData);
    (*callback)(stream, status, nullptr);
    delete callback;
}

void addStreamCallback(cudaStream_t stream, StreamCallback callback, void* userData) {
    auto* callback_ptr = new StreamCallback(std::move(callback));
    CUDA_CHECK(cudaStreamAddCallback(stream, streamCallback, callback_ptr, 0));
}

} // namespace llm_inference
} // namespace msmartcompute 