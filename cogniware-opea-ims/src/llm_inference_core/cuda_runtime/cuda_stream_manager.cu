#include "cuda_stream_manager.h"
#include "cuda_utils.h"
#include <spdlog/spdlog.h>

namespace msmartcompute {
namespace llm_inference {

struct CUDAStreamManager::Impl {
    std::unordered_map<cudaStream_t, StreamInfo> streams;
    std::mutex mutex;
    int num_devices;
};

CUDAStreamManager& CUDAStreamManager::getInstance() {
    static CUDAStreamManager instance;
    return instance;
}

CUDAStreamManager::CUDAStreamManager() : pimpl(std::make_unique<Impl>()) {
    CUDA_CHECK(cudaGetDeviceCount(&pimpl->num_devices));
    for (int i = 0; i < pimpl->num_devices; ++i) {
        initializeDevice(i);
    }
}

CUDAStreamManager::~CUDAStreamManager() {
    clear();
}

void CUDAStreamManager::initializeDevice(int device_id) {
    CUDA_CHECK(cudaSetDevice(device_id));
    spdlog::info("Initialized CUDA device {}", device_id);
}

void CUDAStreamManager::cleanupDevice(int device_id) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    // Destroy all streams associated with this device
    for (auto it = pimpl->streams.begin(); it != pimpl->streams.end();) {
        if (it->second.device_id == device_id) {
            CUDA_CHECK(cudaStreamDestroy(it->first));
            it = pimpl->streams.erase(it);
        } else {
            ++it;
        }
    }
}

bool CUDAStreamManager::checkStream(cudaStream_t stream) const {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    return pimpl->streams.find(stream) != pimpl->streams.end();
}

cudaStream_t CUDAStreamManager::createStream(StreamPriority priority, StreamFlags flags, const std::string& tag) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    int device_id;
    CUDA_CHECK(cudaGetDevice(&device_id));
    
    cudaStream_t stream;
    cudaStreamCreateFlags stream_flags = 0;
    if (flags == StreamFlags::NON_BLOCKING) {
        stream_flags = cudaStreamNonBlocking;
    }
    
    CUDA_CHECK(cudaStreamCreateWithFlags(&stream, stream_flags));
    
    StreamInfo info;
    info.stream = stream;
    info.device_id = device_id;
    info.priority = priority;
    info.flags = flags;
    info.tag = tag;
    info.is_active = true;
    
    pimpl->streams[stream] = info;
    
    spdlog::debug("Created CUDA stream {} with tag '{}' on device {}", 
                 static_cast<void*>(stream), tag, device_id);
    
    return stream;
}

void CUDAStreamManager::destroyStream(cudaStream_t stream) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    if (!checkStream(stream)) {
        spdlog::warn("Attempted to destroy unknown CUDA stream {}", static_cast<void*>(stream));
        return;
    }
    
    synchronize(stream);
    CUDA_CHECK(cudaStreamDestroy(stream));
    pimpl->streams.erase(stream);
    
    spdlog::debug("Destroyed CUDA stream {}", static_cast<void*>(stream));
}

void CUDAStreamManager::synchronize(cudaStream_t stream) {
    if (!checkStream(stream)) {
        spdlog::warn("Attempted to synchronize unknown CUDA stream {}", static_cast<void*>(stream));
        return;
    }
    
    CUDA_CHECK(cudaStreamSynchronize(stream));
}

void CUDAStreamManager::synchronizeAll() {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    for (const auto& [stream, info] : pimpl->streams) {
        if (info.is_active) {
            CUDA_CHECK(cudaStreamSynchronize(stream));
        }
    }
}

bool CUDAStreamManager::isStreamActive(cudaStream_t stream) const {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    if (!checkStream(stream)) {
        return false;
    }
    
    return pimpl->streams.at(stream).is_active;
}

void CUDAStreamManager::setStreamActive(cudaStream_t stream, bool active) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    if (!checkStream(stream)) {
        spdlog::warn("Attempted to set active state for unknown CUDA stream {}", 
                    static_cast<void*>(stream));
        return;
    }
    
    pimpl->streams[stream].is_active = active;
}

StreamInfo CUDAStreamManager::getStreamInfo(cudaStream_t stream) const {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    if (!checkStream(stream)) {
        throw std::runtime_error("Unknown CUDA stream");
    }
    
    return pimpl->streams.at(stream);
}

std::vector<StreamInfo> CUDAStreamManager::getAllStreams() const {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    std::vector<StreamInfo> result;
    result.reserve(pimpl->streams.size());
    
    for (const auto& [stream, info] : pimpl->streams) {
        result.push_back(info);
    }
    
    return result;
}

size_t CUDAStreamManager::getStreamCount() const {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    return pimpl->streams.size();
}

void CUDAStreamManager::setStreamPriority(cudaStream_t stream, StreamPriority priority) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    if (!checkStream(stream)) {
        spdlog::warn("Attempted to set priority for unknown CUDA stream {}", 
                    static_cast<void*>(stream));
        return;
    }
    
    pimpl->streams[stream].priority = priority;
}

void CUDAStreamManager::setStreamFlags(cudaStream_t stream, StreamFlags flags) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    if (!checkStream(stream)) {
        spdlog::warn("Attempted to set flags for unknown CUDA stream {}", 
                    static_cast<void*>(stream));
        return;
    }
    
    pimpl->streams[stream].flags = flags;
}

void CUDAStreamManager::setStreamTag(cudaStream_t stream, const std::string& tag) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    if (!checkStream(stream)) {
        spdlog::warn("Attempted to set tag for unknown CUDA stream {}", 
                    static_cast<void*>(stream));
        return;
    }
    
    pimpl->streams[stream].tag = tag;
}

void CUDAStreamManager::clear() {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    for (const auto& [stream, info] : pimpl->streams) {
        CUDA_CHECK(cudaStreamDestroy(stream));
    }
    
    pimpl->streams.clear();
}

void CUDAStreamManager::reset() {
    clear();
    
    for (int i = 0; i < pimpl->num_devices; ++i) {
        initializeDevice(i);
    }
}

} // namespace llm_inference
} // namespace msmartcompute 