#include "cuda_model.h"
#include "cuda_kernels.cu"
#include <random>
#include <fstream>
#include <spdlog/spdlog.h>

namespace msmartcompute {

CUDAModel::CUDAModel(const std::vector<int>& layerSizes)
    : layerSizes_(layerSizes),
      currentDevice_(0),
      mixedPrecision_(false),
      dropoutRate_(0.0f),
      batchNormMomentum_(0.9f),
      trainingMode_(true)
{
    // Initialize CUDA resources
    CUDA_CHECK(cudaSetDevice(currentDevice_));
    CUDA_CHECK(cudaStreamCreate(&stream_));
    CUDA_CHECK(cublasCreate(&cublasHandle_));
    CUDA_CHECK(cusolverDnCreate(&cusolverHandle_));

    // Set stream for cuBLAS and cuSOLVER
    CUDA_CHECK(cublasSetStream(cublasHandle_, stream_));
    CUDA_CHECK(cusolverDnSetStream(cusolverHandle_, stream_));

    // Initialize layers
    layers_.resize(layerSizes_.size() - 1);
    allocateDeviceMemory();
    initializeWeights();
    initializeBatchNorm();
}

CUDAModel::~CUDAModel() {
    freeDeviceMemory();
    CUDA_CHECK(cublasDestroy(cublasHandle_));
    CUDA_CHECK(cusolverDnDestroy(cusolverHandle_));
    CUDA_CHECK(cudaStreamDestroy(stream_));
}

void CUDAModel::setDevice(int deviceId) {
    if (deviceId != currentDevice_) {
        currentDevice_ = deviceId;
        CUDA_CHECK(cudaSetDevice(deviceId));
    }
}

void CUDAModel::enableMixedPrecision(bool enable) {
    mixedPrecision_ = enable;
}

void CUDAModel::setDropoutRate(float rate) {
    dropoutRate_ = rate;
}

void CUDAModel::setBatchNormMomentum(float momentum) {
    batchNormMomentum_ = momentum;
}

std::vector<float> CUDAModel::forward(const DataBatch& batch) {
    // Copy input to device
    thrust::device_vector<float> input(batch.inputs.begin(), batch.inputs.end());
    
    // Forward pass through layers
    for (size_t i = 0; i < layers_.size(); ++i) {
        Layer& layer = layers_[i];
        
        // Matrix multiplication
        float alpha = 1.0f;
        float beta = 0.0f;
        CUDA_CHECK(cublasSgemm(cublasHandle_, CUBLAS_OP_N, CUBLAS_OP_N,
            layerSizes_[i + 1], batch.size, layerSizes_[i],
            &alpha, layer.weights.data().get(), layerSizes_[i + 1],
            input.data().get(), layerSizes_[i],
            &beta, layer.activations.data().get(), layerSizes_[i + 1]));

        // Add bias
        thrust::transform(layer.activations.begin(), layer.activations.end(),
            layer.biases.begin(), layer.activations.begin(),
            thrust::plus<float>());

        // Apply batch normalization
        if (trainingMode_) {
            applyBatchNorm(layer, true);
        }

        // Apply activation
        applyActivation(layer, "relu");

        // Apply dropout
        if (trainingMode_ && dropoutRate_ > 0.0f) {
            applyDropout(layer.activations);
        }

        // Update input for next layer
        input = layer.activations;
    }

    // Copy result back to host
    std::vector<float> result(input.size());
    thrust::copy(input.begin(), input.end(), result.begin());
    return result;
}

void CUDAModel::backward(float loss) {
    // Compute output gradient
    thrust::device_vector<float> outputGrad(layers_.back().activations.size());
    thrust::fill(outputGrad.begin(), outputGrad.end(), loss);

    // Backward pass through layers
    for (int i = layers_.size() - 1; i >= 0; --i) {
        Layer& layer = layers_[i];
        
        // Compute activation gradient
        computeActivationGrad(layer, "relu");

        // Compute weight gradients
        computeGradients(outputGrad);

        // Update weights
        updateWeights(0.001f);  // Learning rate

        // Prepare gradient for next layer
        if (i > 0) {
            outputGrad = layer.gradients;
        }
    }
}

bool CUDAModel::save(const std::string& path) const {
    try {
        std::ofstream file(path, std::ios::binary);
        if (!file) {
            return false;
        }

        // Save layer sizes
        size_t numLayers = layerSizes_.size();
        file.write(reinterpret_cast<const char*>(&numLayers), sizeof(numLayers));
        file.write(reinterpret_cast<const char*>(layerSizes_.data()), 
                  numLayers * sizeof(int));

        // Save layer parameters
        for (const auto& layer : layers_) {
            // Save weights
            std::vector<float> weights(layer.weights.size());
            thrust::copy(layer.weights.begin(), layer.weights.end(), weights.begin());
            file.write(reinterpret_cast<const char*>(weights.data()), 
                      weights.size() * sizeof(float));

            // Save biases
            std::vector<float> biases(layer.biases.size());
            thrust::copy(layer.biases.begin(), layer.biases.end(), biases.begin());
            file.write(reinterpret_cast<const char*>(biases.data()), 
                      biases.size() * sizeof(float));

            // Save batch norm parameters
            std::vector<float> gamma(layer.gamma.size());
            thrust::copy(layer.gamma.begin(), layer.gamma.end(), gamma.begin());
            file.write(reinterpret_cast<const char*>(gamma.data()), 
                      gamma.size() * sizeof(float));

            std::vector<float> beta(layer.beta.size());
            thrust::copy(layer.beta.begin(), layer.beta.end(), beta.begin());
            file.write(reinterpret_cast<const char*>(beta.data()), 
                      beta.size() * sizeof(float));
        }

        return true;
    } catch (const std::exception& e) {
        spdlog::error("Failed to save model: {}", e.what());
        return false;
    }
}

bool CUDAModel::load(const std::string& path) {
    try {
        std::ifstream file(path, std::ios::binary);
        if (!file) {
            return false;
        }

        // Load layer sizes
        size_t numLayers;
        file.read(reinterpret_cast<char*>(&numLayers), sizeof(numLayers));
        layerSizes_.resize(numLayers);
        file.read(reinterpret_cast<char*>(layerSizes_.data()), 
                 numLayers * sizeof(int));

        // Reinitialize layers
        layers_.resize(layerSizes_.size() - 1);
        allocateDeviceMemory();

        // Load layer parameters
        for (auto& layer : layers_) {
            // Load weights
            std::vector<float> weights(layer.weights.size());
            file.read(reinterpret_cast<char*>(weights.data()), 
                     weights.size() * sizeof(float));
            thrust::copy(weights.begin(), weights.end(), layer.weights.begin());

            // Load biases
            std::vector<float> biases(layer.biases.size());
            file.read(reinterpret_cast<char*>(biases.data()), 
                     biases.size() * sizeof(float));
            thrust::copy(biases.begin(), biases.end(), layer.biases.begin());

            // Load batch norm parameters
            std::vector<float> gamma(layer.gamma.size());
            file.read(reinterpret_cast<char*>(gamma.data()), 
                     gamma.size() * sizeof(float));
            thrust::copy(gamma.begin(), gamma.end(), layer.gamma.begin());

            std::vector<float> beta(layer.beta.size());
            file.read(reinterpret_cast<char*>(beta.data()), 
                     beta.size() * sizeof(float));
            thrust::copy(beta.begin(), beta.end(), layer.beta.begin());
        }

        return true;
    } catch (const std::exception& e) {
        spdlog::error("Failed to load model: {}", e.what());
        return false;
    }
}

void CUDAModel::initializeWeights() {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::normal_distribution<float> dist(0.0f, 0.02f);

    for (auto& layer : layers_) {
        // Initialize weights
        std::vector<float> weights(layer.weights.size());
        for (auto& w : weights) {
            w = dist(gen);
        }
        thrust::copy(weights.begin(), weights.end(), layer.weights.begin());

        // Initialize biases
        std::vector<float> biases(layer.biases.size(), 0.0f);
        thrust::copy(biases.begin(), biases.end(), layer.biases.begin());

        // Initialize optimizer states
        thrust::fill(layer.momentum.begin(), layer.momentum.end(), 0.0f);
        thrust::fill(layer.velocity.begin(), layer.velocity.end(), 0.0f);
    }
}

void CUDAModel::initializeBatchNorm() {
    for (auto& layer : layers_) {
        // Initialize gamma (scale)
        thrust::fill(layer.gamma.begin(), layer.gamma.end(), 1.0f);
        
        // Initialize beta (shift)
        thrust::fill(layer.beta.begin(), layer.beta.end(), 0.0f);
        
        // Initialize running statistics
        thrust::fill(layer.runningMean.begin(), layer.runningMean.end(), 0.0f);
        thrust::fill(layer.runningVar.begin(), layer.runningVar.end(), 1.0f);
    }
}

void CUDAModel::computeGradients(const thrust::device_vector<float>& outputGrad) {
    for (auto& layer : layers_) {
        // Compute weight gradients using cuBLAS
        float alpha = 1.0f;
        float beta = 0.0f;
        CUDA_CHECK(cublasSgemm(cublasHandle_, CUBLAS_OP_N, CUBLAS_OP_T,
            layer.weights.size(), outputGrad.size(), layer.activations.size(),
            &alpha, layer.activations.data().get(), layer.weights.size(),
            outputGrad.data().get(), outputGrad.size(),
            &beta, layer.gradients.data().get(), layer.weights.size()));
    }
}

void CUDAModel::updateWeights(float learningRate) {
    for (auto& layer : layers_) {
        // Update weights using Adam optimizer
        int blockSize = 256;
        int numBlocks = (layer.weights.size() + blockSize - 1) / blockSize;
        
        adamUpdateKernel<<<numBlocks, blockSize, 0, stream_>>>(
            layer.weights.data().get(),
            layer.momentum.data().get(),
            layer.velocity.data().get(),
            layer.gradients.data().get(),
            layer.weights.size(),
            learningRate,
            0.9f,  // beta1
            0.999f,  // beta2
            1e-8f,  // epsilon
            1  // step
        );
    }
}

void CUDAModel::applyDropout(thrust::device_vector<float>& data) {
    int blockSize = 256;
    int numBlocks = (data.size() + blockSize - 1) / blockSize;
    
    dropoutKernel<<<numBlocks, blockSize, 0, stream_>>>(
        data.data().get(),
        dropoutMask_.data().get(),
        data.size(),
        dropoutRate_,
        randomStates_.data().get()
    );
}

void CUDAModel::applyBatchNorm(Layer& layer, bool training) {
    int blockSize = 256;
    int numBlocks = (layer.activations.size() + blockSize - 1) / blockSize;
    
    batchNormForwardKernel<<<numBlocks, blockSize, 0, stream_>>>(
        layer.activations.data().get(),
        layer.activations.data().get(),
        layer.gamma.data().get(),
        layer.beta.data().get(),
        layer.runningMean.data().get(),
        layer.runningVar.data().get(),
        1,  // batchSize
        layerSizes_[0],  // channels
        layer.activations.size() / layerSizes_[0],  // spatialSize
        batchNormMomentum_,
        1e-5f  // epsilon
    );
}

void CUDAModel::applyActivation(Layer& layer, const std::string& activationType) {
    int blockSize = 256;
    int numBlocks = (layer.activations.size() + blockSize - 1) / blockSize;
    
    if (activationType == "relu") {
        reluKernel<<<numBlocks, blockSize, 0, stream_>>>(
            layer.activations.data().get(),
            layer.activations.size()
        );
    }
}

void CUDAModel::computeActivationGrad(Layer& layer, const std::string& activationType) {
    int blockSize = 256;
    int numBlocks = (layer.activations.size() + blockSize - 1) / blockSize;
    
    if (activationType == "relu") {
        reluGradKernel<<<numBlocks, blockSize, 0, stream_>>>(
            layer.activations.data().get(),
            layer.gradients.data().get(),
            layer.gradients.data().get(),
            layer.activations.size()
        );
    }
}

void CUDAModel::allocateDeviceMemory() {
    for (size_t i = 0; i < layers_.size(); ++i) {
        Layer& layer = layers_[i];
        size_t inputSize = layerSizes_[i];
        size_t outputSize = layerSizes_[i + 1];
        
        // Allocate memory for weights and biases
        layer.weights.resize(inputSize * outputSize);
        layer.biases.resize(outputSize);
        layer.activations.resize(outputSize);
        layer.gradients.resize(inputSize * outputSize);
        layer.momentum.resize(inputSize * outputSize);
        layer.velocity.resize(inputSize * outputSize);
        
        // Allocate memory for batch normalization
        layer.gamma.resize(outputSize);
        layer.beta.resize(outputSize);
        layer.runningMean.resize(outputSize);
        layer.runningVar.resize(outputSize);
    }
    
    // Allocate memory for dropout
    dropoutMask_.resize(layerSizes_.back());
    randomStates_.resize(layerSizes_.back());
    
    // Initialize random states
    int blockSize = 256;
    int numBlocks = (randomStates_.size() + blockSize - 1) / blockSize;
    curand_init<<<numBlocks, blockSize, 0, stream_>>>(
        time(nullptr),
        thrust::raw_pointer_cast(randomStates_.data()),
        randomStates_.size()
    );
}

void CUDAModel::freeDeviceMemory() {
    for (auto& layer : layers_) {
        layer.weights.clear();
        layer.biases.clear();
        layer.activations.clear();
        layer.gradients.clear();
        layer.momentum.clear();
        layer.velocity.clear();
        layer.gamma.clear();
        layer.beta.clear();
        layer.runningMean.clear();
        layer.runningVar.clear();
    }
    dropoutMask_.clear();
    randomStates_.clear();
}

void CUDAModel::synchronizeDevice() {
    CUDA_CHECK(cudaStreamSynchronize(stream_));
}

} // namespace msmartcompute 