#ifndef MSMARTCOMPUTE_CUDA_OPTIMIZER_H
#define MSMARTCOMPUTE_CUDA_OPTIMIZER_H

#include "training_control_hooks.h"
#include <cuda_runtime.h>
#include <thrust/device_vector.h>
#include <memory>

namespace cogniware {

class CUDAAdamOptimizer : public IOptimizer {
public:
    CUDAAdamOptimizer(float learningRate, float beta1 = 0.9f, float beta2 = 0.999f, float epsilon = 1e-8f);
    ~CUDAAdamOptimizer();

    void step() override;
    float getLearningRate() const override;
    void setLearningRate(float lr);
    void setBeta1(float beta1);
    void setBeta2(float beta2);
    void setEpsilon(float epsilon);

private:
    float learningRate_;
    float beta1_;
    float beta2_;
    float epsilon_;
    int step_;
    cudaStream_t stream_;
    thrust::device_vector<float> momentum_;
    thrust::device_vector<float> velocity_;
};

class CUDASGDOptimizer : public IOptimizer {
public:
    CUDASGDOptimizer(float learningRate, float momentum = 0.0f, float weightDecay = 0.0f);
    ~CUDASGDOptimizer();

    void step() override;
    float getLearningRate() const override;
    void setLearningRate(float lr);
    void setMomentum(float momentum);
    void setWeightDecay(float weightDecay);

private:
    float learningRate_;
    float momentum_;
    float weightDecay_;
    cudaStream_t stream_;
    thrust::device_vector<float> velocity_;
};

class CUDARMSPropOptimizer : public IOptimizer {
public:
    CUDARMSPropOptimizer(float learningRate, float alpha = 0.99f, float epsilon = 1e-8f, float weightDecay = 0.0f);
    ~CUDARMSPropOptimizer();

    void step() override;
    float getLearningRate() const override;
    void setLearningRate(float lr);
    void setAlpha(float alpha);
    void setEpsilon(float epsilon);
    void setWeightDecay(float weightDecay);

private:
    float learningRate_;
    float alpha_;
    float epsilon_;
    float weightDecay_;
    cudaStream_t stream_;
    thrust::device_vector<float> squareAvg_;
};

} // namespace cogniware

#endif // MSMARTCOMPUTE_CUDA_OPTIMIZER_H 