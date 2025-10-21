#pragma once

#include <cuda_runtime.h>
#include <cuda_fp16.h>

namespace cogniware {
namespace llm_inference {

// Activation function types
enum class ActivationType {
    RELU,
    GELU,
    SILU,  // Also known as Swish
    TANH,
    SIGMOID,
    SOFTMAX
};

// Kernel launcher functions
void launchReLU(float* output, const float* input, int size, cudaStream_t stream = nullptr);
void launchReLU(half* output, const half* input, int size, cudaStream_t stream = nullptr);

void launchGELU(float* output, const float* input, int size, cudaStream_t stream = nullptr);
void launchGELU(half* output, const half* input, int size, cudaStream_t stream = nullptr);

void launchSiLU(float* output, const float* input, int size, cudaStream_t stream = nullptr);
void launchSiLU(half* output, const half* input, int size, cudaStream_t stream = nullptr);

void launchTanh(float* output, const float* input, int size, cudaStream_t stream = nullptr);
void launchTanh(half* output, const half* input, int size, cudaStream_t stream = nullptr);

void launchSigmoid(float* output, const float* input, int size, cudaStream_t stream = nullptr);
void launchSigmoid(half* output, const half* input, int size, cudaStream_t stream = nullptr);

void launchSoftmax(float* output, const float* input, int batch_size, int seq_len, int hidden_size, cudaStream_t stream = nullptr);
void launchSoftmax(half* output, const half* input, int batch_size, int seq_len, int hidden_size, cudaStream_t stream = nullptr);

// Generic activation launcher
void launchActivation(float* output, const float* input, int size, ActivationType type, cudaStream_t stream = nullptr);
void launchActivation(half* output, const half* input, int size, ActivationType type, cudaStream_t stream = nullptr);

} // namespace llm_inference
} // namespace cogniware
