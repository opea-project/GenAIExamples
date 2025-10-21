#include "cuda_loss.h"
#include "cuda_kernels.cu"
#include <spdlog/spdlog.h>

namespace msmartcompute {

// CUDA Cross Entropy Loss Implementation
CUDACrossEntropyLoss::CUDACrossEntropyLoss() {
    CUDA_CHECK(cudaStreamCreate(&stream_));
}

CUDACrossEntropyLoss::~CUDACrossEntropyLoss() {
    CUDA_CHECK(cudaStreamDestroy(stream_));
}

float CUDACrossEntropyLoss::compute(const std::vector<float>& outputs, const std::vector<float>& targets) {
    // Resize device vectors if needed
    if (deviceOutputs_.size() != outputs.size()) {
        deviceOutputs_.resize(outputs.size());
        deviceTargets_.resize(targets.size());
        deviceLoss_.resize(outputs.size());
    }

    // Copy data to device
    thrust::copy(outputs.begin(), outputs.end(), deviceOutputs_.begin());
    thrust::copy(targets.begin(), targets.end(), deviceTargets_.begin());

    // Compute softmax
    thrust::device_vector<float> expOutputs(outputs.size());
    thrust::transform(deviceOutputs_.begin(), deviceOutputs_.end(), expOutputs.begin(),
        [](float x) { return std::exp(x); });
    
    float sum = thrust::reduce(expOutputs.begin(), expOutputs.end(), 0.0f, thrust::plus<float>());
    
    thrust::transform(expOutputs.begin(), expOutputs.end(), deviceOutputs_.begin(),
        [sum](float x) { return x / sum; });

    // Compute cross entropy loss
    thrust::transform(deviceOutputs_.begin(), deviceOutputs_.end(), deviceTargets_.begin(),
        deviceLoss_.begin(), [](float pred, float target) {
            return -target * std::log(pred + 1e-8f);
        });

    // Reduce loss
    float totalLoss = thrust::reduce(deviceLoss_.begin(), deviceLoss_.end(), 0.0f, thrust::plus<float>());
    return totalLoss / outputs.size();
}

// CUDA MSE Loss Implementation
CUDAMSELoss::CUDAMSELoss() {
    CUDA_CHECK(cudaStreamCreate(&stream_));
}

CUDAMSELoss::~CUDAMSELoss() {
    CUDA_CHECK(cudaStreamDestroy(stream_));
}

float CUDAMSELoss::compute(const std::vector<float>& outputs, const std::vector<float>& targets) {
    // Resize device vectors if needed
    if (deviceOutputs_.size() != outputs.size()) {
        deviceOutputs_.resize(outputs.size());
        deviceTargets_.resize(targets.size());
        deviceLoss_.resize(outputs.size());
    }

    // Copy data to device
    thrust::copy(outputs.begin(), outputs.end(), deviceOutputs_.begin());
    thrust::copy(targets.begin(), targets.end(), deviceTargets_.begin());

    // Compute squared differences
    thrust::transform(deviceOutputs_.begin(), deviceOutputs_.end(), deviceTargets_.begin(),
        deviceLoss_.begin(), [](float pred, float target) {
            float diff = pred - target;
            return diff * diff;
        });

    // Reduce loss
    float totalLoss = thrust::reduce(deviceLoss_.begin(), deviceLoss_.end(), 0.0f, thrust::plus<float>());
    return totalLoss / outputs.size();
}

// CUDA Binary Cross Entropy Loss Implementation
CUDABinaryCrossEntropyLoss::CUDABinaryCrossEntropyLoss() {
    CUDA_CHECK(cudaStreamCreate(&stream_));
}

CUDABinaryCrossEntropyLoss::~CUDABinaryCrossEntropyLoss() {
    CUDA_CHECK(cudaStreamDestroy(stream_));
}

float CUDABinaryCrossEntropyLoss::compute(const std::vector<float>& outputs, const std::vector<float>& targets) {
    // Resize device vectors if needed
    if (deviceOutputs_.size() != outputs.size()) {
        deviceOutputs_.resize(outputs.size());
        deviceTargets_.resize(targets.size());
        deviceLoss_.resize(outputs.size());
    }

    // Copy data to device
    thrust::copy(outputs.begin(), outputs.end(), deviceOutputs_.begin());
    thrust::copy(targets.begin(), targets.end(), deviceTargets_.begin());

    // Apply sigmoid to outputs
    thrust::transform(deviceOutputs_.begin(), deviceOutputs_.end(), deviceOutputs_.begin(),
        [](float x) { return 1.0f / (1.0f + std::exp(-x)); });

    // Compute binary cross entropy loss
    thrust::transform(deviceOutputs_.begin(), deviceOutputs_.end(), deviceTargets_.begin(),
        deviceLoss_.begin(), [](float pred, float target) {
            return -(target * std::log(pred + 1e-8f) + 
                    (1.0f - target) * std::log(1.0f - pred + 1e-8f));
        });

    // Reduce loss
    float totalLoss = thrust::reduce(deviceLoss_.begin(), deviceLoss_.end(), 0.0f, thrust::plus<float>());
    return totalLoss / outputs.size();
}

} // namespace msmartcompute 