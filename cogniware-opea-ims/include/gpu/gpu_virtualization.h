#pragma once

#include <string>
#include <vector>
#include <memory>

namespace cogniware {
namespace gpu {

struct VirtualGPU {
    std::string vgpu_id;
    int physical_gpu_id;
    uint64_t memory_limit_mb;
    uint32_t compute_limit_percent;
    bool active;
};

class GPUVirtualization {
public:
    GPUVirtualization();
    ~GPUVirtualization();

    bool initialize();
    void shutdown();
    
    std::string createVirtualGPU(int physical_gpu_id, uint64_t memory_mb, uint32_t compute_percent);
    bool destroyVirtualGPU(const std::string& vgpu_id);
    
    std::vector<VirtualGPU> listVirtualGPUs();
    VirtualGPU getVirtualGPU(const std::string& vgpu_id);
    
    bool allocateToVGPU(const std::string& vgpu_id, const std::string& resource_type, uint64_t amount);

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

} // namespace gpu
} // namespace cogniware

