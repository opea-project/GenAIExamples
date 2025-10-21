#include "gpu/gpu_virtualization.h"
#include <mutex>

namespace cogniware {
namespace gpu {

class GPUVirtualization::Impl {
public:
    std::unordered_map<std::string, VirtualGPU> vgpus;
    mutable std::mutex mutex;
    std::atomic<uint64_t> vgpu_counter{0};
};

GPUVirtualization::GPUVirtualization() : pImpl(std::make_unique<Impl>()) {}
GPUVirtualization::~GPUVirtualization() { shutdown(); }

bool GPUVirtualization::initialize() { return true; }
void GPUVirtualization::shutdown() {}

std::string GPUVirtualization::createVirtualGPU(int physical_gpu_id, uint64_t memory_mb, uint32_t compute_percent) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    VirtualGPU vgpu;
    vgpu.vgpu_id = "vgpu_" + std::to_string(++pImpl->vgpu_counter);
    vgpu.physical_gpu_id = physical_gpu_id;
    vgpu.memory_limit_mb = memory_mb;
    vgpu.compute_limit_percent = compute_percent;
    vgpu.active = true;
    
    pImpl->vgpus[vgpu.vgpu_id] = vgpu;
    return vgpu.vgpu_id;
}

bool GPUVirtualization::destroyVirtualGPU(const std::string& vgpu_id) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    return pImpl->vgpus.erase(vgpu_id) > 0;
}

std::vector<VirtualGPU> GPUVirtualization::listVirtualGPUs() {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    std::vector<VirtualGPU> result;
    for (const auto& [id, vgpu] : pImpl->vgpus) {
        result.push_back(vgpu);
    }
    return result;
}

VirtualGPU GPUVirtualization::getVirtualGPU(const std::string& vgpu_id) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    auto it = pImpl->vgpus.find(vgpu_id);
    return (it != pImpl->vgpus.end()) ? it->second : VirtualGPU{};
}

bool GPUVirtualization::allocateToVGPU(const std::string&, const std::string&, uint64_t) {
    return true;
}

} // namespace gpu
} // namespace cogniware

