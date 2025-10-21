#include "cuda_optimizer.h"
#include "cuda_kernels.cu"
#include <spdlog/spdlog.h>

namespace msmartcompute {

// CUDA Adam Optimizer Implementation
CUDAAdamOptimizer::CUDAAdamOptimizer(float learningRate, float beta1, float beta2, float epsilon)
    : learningRate_(learningRate),
      beta1_(beta1),
      beta2_(beta2),
      epsilon_(epsilon),
      step_(0)
{
    CUDA_CHECK(cudaStreamCreate(&stream_));
}

CUDAAdamOptimizer::~CUDAAdamOptimizer() {
    CUDA_CHECK(cudaStreamDestroy(stream_));
}

void CUDAAdamOptimizer::step() {
    step_++;
    
    // Update weights using Adam optimizer
    int blockSize = 256;
    int numBlocks = (momentum_.size() + blockSize - 1) / blockSize;
    
    adamUpdateKernel<<<numBlocks, blockSize, 0, stream_>>>(
        thrust::raw_pointer_cast(momentum_.data()),
        thrust::raw_pointer_cast(velocity_.data()),
        thrust::raw_pointer_cast(momentum_.data()),
        thrust::raw_pointer_cast(velocity_.data()),
        momentum_.size(),
        learningRate_,
        beta1_,
        beta2_,
        epsilon_,
        step_
    );
}

float CUDAAdamOptimizer::getLearningRate() const {
    return learningRate_;
}

void CUDAAdamOptimizer::setLearningRate(float lr) {
    learningRate_ = lr;
}

void CUDAAdamOptimizer::setBeta1(float beta1) {
    beta1_ = beta1;
}

void CUDAAdamOptimizer::setBeta2(float beta2) {
    beta2_ = beta2;
}

void CUDAAdamOptimizer::setEpsilon(float epsilon) {
    epsilon_ = epsilon;
}

// CUDA SGD Optimizer Implementation
CUDASGDOptimizer::CUDASGDOptimizer(float learningRate, float momentum, float weightDecay)
    : learningRate_(learningRate),
      momentum_(momentum),
      weightDecay_(weightDecay)
{
    CUDA_CHECK(cudaStreamCreate(&stream_));
}

CUDASGDOptimizer::~CUDASGDOptimizer() {
    CUDA_CHECK(cudaStreamDestroy(stream_));
}

void CUDASGDOptimizer::step() {
    int blockSize = 256;
    int numBlocks = (velocity_.size() + blockSize - 1) / blockSize;
    
    // Update velocity with momentum
    if (momentum_ > 0.0f) {
        thrust::transform(
            velocity_.begin(),
            velocity_.end(),
            velocity_.begin(),
            [this](float v) { return momentum_ * v; }
        );
    }
    
    // Add gradient to velocity
    thrust::transform(
        velocity_.begin(),
        velocity_.end(),
        velocity_.begin(),
        [this](float v) { return v - learningRate_ * v; }
    );
    
    // Apply weight decay if enabled
    if (weightDecay_ > 0.0f) {
        thrust::transform(
            velocity_.begin(),
            velocity_.end(),
            velocity_.begin(),
            [this](float v) { return v - learningRate_ * weightDecay_ * v; }
        );
    }
}

float CUDASGDOptimizer::getLearningRate() const {
    return learningRate_;
}

void CUDASGDOptimizer::setLearningRate(float lr) {
    learningRate_ = lr;
}

void CUDASGDOptimizer::setMomentum(float momentum) {
    momentum_ = momentum;
}

void CUDASGDOptimizer::setWeightDecay(float weightDecay) {
    weightDecay_ = weightDecay;
}

// CUDA RMSProp Optimizer Implementation
CUDARMSPropOptimizer::CUDARMSPropOptimizer(float learningRate, float alpha, float epsilon, float weightDecay)
    : learningRate_(learningRate),
      alpha_(alpha),
      epsilon_(epsilon),
      weightDecay_(weightDecay)
{
    CUDA_CHECK(cudaStreamCreate(&stream_));
}

CUDARMSPropOptimizer::~CUDARMSPropOptimizer() {
    CUDA_CHECK(cudaStreamDestroy(stream_));
}

void CUDARMSPropOptimizer::step() {
    int blockSize = 256;
    int numBlocks = (squareAvg_.size() + blockSize - 1) / blockSize;
    
    // Update square average
    thrust::transform(
        squareAvg_.begin(),
        squareAvg_.end(),
        squareAvg_.begin(),
        [this](float avg) { return alpha_ * avg + (1.0f - alpha_) * avg * avg; }
    );
    
    // Update weights
    thrust::transform(
        squareAvg_.begin(),
        squareAvg_.end(),
        squareAvg_.begin(),
        [this](float avg) {
            float update = -learningRate_ / (std::sqrt(avg) + epsilon_);
            if (weightDecay_ > 0.0f) {
                update -= learningRate_ * weightDecay_;
            }
            return update;
        }
    );
}

float CUDARMSPropOptimizer::getLearningRate() const {
    return learningRate_;
}

void CUDARMSPropOptimizer::setLearningRate(float lr) {
    learningRate_ = lr;
}

void CUDARMSPropOptimizer::setAlpha(float alpha) {
    alpha_ = alpha;
}

void CUDARMSPropOptimizer::setEpsilon(float epsilon) {
    epsilon_ = epsilon;
}

void CUDARMSPropOptimizer::setWeightDecay(float weightDecay) {
    weightDecay_ = weightDecay;
}

} // namespace msmartcompute 