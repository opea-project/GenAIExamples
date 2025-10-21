#include "cuda_event.h"
#include "cuda_utils.h"
#include <spdlog/spdlog.h>
#include <unordered_map>
#include <mutex>
#include <stdexcept>

namespace msmartcompute {
namespace llm_inference {

// Implementation of CUDAEventManager
struct CUDAEventManager::Impl {
    std::unordered_map<cudaEvent_t, EventInfo> events;
    std::mutex mutex;
};

CUDAEventManager& CUDAEventManager::getInstance() {
    static CUDAEventManager instance;
    return instance;
}

CUDAEventManager::CUDAEventManager() : pimpl(std::make_unique<Impl>()) {
    // Initialize event manager
    int device_count = getDeviceCount();
    for (int i = 0; i < device_count; ++i) {
        initializeDevice(i);
    }
}

CUDAEventManager::~CUDAEventManager() {
    clear();
}

void CUDAEventManager::initializeDevice(int device_id) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    // Set device
    setDevice(device_id);
    
    spdlog::info("Initialized CUDA event manager for device {}", device_id);
}

void CUDAEventManager::cleanupDevice(int device_id) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    // Destroy all events for this device
    for (auto it = pimpl->events.begin(); it != pimpl->events.end();) {
        if (it->second.device_id == device_id) {
            destroyEvent(it->first);
            it = pimpl->events.erase(it);
        } else {
            ++it;
        }
    }
}

void CUDAEventManager::checkEvent(cudaEvent_t event) const {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    if (pimpl->events.find(event) == pimpl->events.end()) {
        throw std::runtime_error("Unknown event");
    }
}

cudaEvent_t CUDAEventManager::createEvent(EventFlags flags, const std::string& tag) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    int device_id = getCurrentDevice();
    
    try {
        // Create event
        cudaEvent_t event;
        CUDA_CHECK(cudaEventCreateWithFlags(&event, static_cast<cudaEventFlags>(flags)));
        
        // Record event info
        EventInfo info{
            event,
            device_id,
            flags,
            tag,
            true,
            0.0f
        };
        pimpl->events[event] = info;
        
        spdlog::debug("Created CUDA event on device {} with flags {} and tag '{}'",
                     device_id, static_cast<int>(flags), tag);
        
        return event;
    } catch (const std::exception& e) {
        spdlog::error("Failed to create CUDA event: {}", e.what());
        throw;
    }
}

void CUDAEventManager::destroyEvent(cudaEvent_t event) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    auto it = pimpl->events.find(event);
    if (it == pimpl->events.end()) {
        throw std::runtime_error("Attempt to destroy unknown event");
    }
    
    try {
        // Synchronize event before destroying
        synchronize(event);
        
        // Destroy event
        CUDA_CHECK(cudaEventDestroy(event));
        
        // Remove event info
        pimpl->events.erase(it);
        
        spdlog::debug("Destroyed CUDA event with tag '{}'", it->second.tag);
    } catch (const std::exception& e) {
        spdlog::error("Failed to destroy CUDA event: {}", e.what());
        throw;
    }
}

void CUDAEventManager::record(cudaEvent_t event, cudaStream_t stream) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    checkEvent(event);
    
    try {
        CUDA_CHECK(cudaEventRecord(event, stream));
    } catch (const std::exception& e) {
        spdlog::error("Failed to record CUDA event: {}", e.what());
        throw;
    }
}

void CUDAEventManager::synchronize(cudaEvent_t event) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    checkEvent(event);
    
    try {
        CUDA_CHECK(cudaEventSynchronize(event));
    } catch (const std::exception& e) {
        spdlog::error("Failed to synchronize CUDA event: {}", e.what());
        throw;
    }
}

float CUDAEventManager::getElapsedTime(cudaEvent_t start, cudaEvent_t end) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    checkEvent(start);
    checkEvent(end);
    
    try {
        float elapsed_time;
        CUDA_CHECK(cudaEventElapsedTime(&elapsed_time, start, end));
        return elapsed_time;
    } catch (const std::exception& e) {
        spdlog::error("Failed to get elapsed time between events: {}", e.what());
        throw;
    }
}

bool CUDAEventManager::isEventActive(cudaEvent_t event) const {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    checkEvent(event);
    return pimpl->events.at(event).is_active;
}

void CUDAEventManager::setEventActive(cudaEvent_t event, bool active) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    checkEvent(event);
    pimpl->events[event].is_active = active;
}

EventInfo CUDAEventManager::getEventInfo(cudaEvent_t event) const {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    checkEvent(event);
    return pimpl->events.at(event);
}

std::vector<EventInfo> CUDAEventManager::getAllEvents() const {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    std::vector<EventInfo> result;
    result.reserve(pimpl->events.size());
    for (const auto& pair : pimpl->events) {
        result.push_back(pair.second);
    }
    return result;
}

int CUDAEventManager::getEventCount() const {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    return static_cast<int>(pimpl->events.size());
}

void CUDAEventManager::setEventFlags(cudaEvent_t event, EventFlags flags) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    checkEvent(event);
    pimpl->events[event].flags = flags;
}

void CUDAEventManager::setEventTag(cudaEvent_t event, const std::string& tag) {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    checkEvent(event);
    pimpl->events[event].tag = tag;
}

void CUDAEventManager::clear() {
    std::lock_guard<std::mutex> lock(pimpl->mutex);
    
    // Destroy all events
    for (const auto& pair : pimpl->events) {
        try {
            destroyEvent(pair.first);
        } catch (const std::exception& e) {
            spdlog::error("Failed to destroy event during clear: {}", e.what());
        }
    }
    
    pimpl->events.clear();
}

void CUDAEventManager::reset() {
    clear();
    
    // Reinitialize all devices
    int device_count = getDeviceCount();
    for (int i = 0; i < device_count; ++i) {
        initializeDevice(i);
    }
}

// Helper function implementations
cudaEvent_t createEvent(EventFlags flags) {
    return CUDAEventManager::getInstance().createEvent(flags);
}

void destroyEvent(cudaEvent_t event) {
    CUDAEventManager::getInstance().destroyEvent(event);
}

void recordEvent(cudaEvent_t event, cudaStream_t stream) {
    CUDAEventManager::getInstance().record(event, stream);
}

void synchronizeEvent(cudaEvent_t event) {
    CUDAEventManager::getInstance().synchronize(event);
}

float getElapsedTime(cudaEvent_t start, cudaEvent_t end) {
    return CUDAEventManager::getInstance().getElapsedTime(start, end);
}

bool isEventActive(cudaEvent_t event) {
    return CUDAEventManager::getInstance().isEventActive(event);
}

void setEventActive(cudaEvent_t event, bool active) {
    CUDAEventManager::getInstance().setEventActive(event, active);
}

void setEventFlags(cudaEvent_t event, EventFlags flags) {
    CUDAEventManager::getInstance().setEventFlags(event, flags);
}

} // namespace llm_inference
} // namespace msmartcompute 