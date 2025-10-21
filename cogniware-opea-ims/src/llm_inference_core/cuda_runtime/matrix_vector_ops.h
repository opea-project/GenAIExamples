#pragma once

#include <cuda_runtime.h>
#include <cuda_fp16.h>

namespace cogniware {
namespace llm_inference {

// Matrix-vector multiplication
void matrixVectorMultiply(
    float* output,
    const float* matrix,
    const float* vector,
    int rows,
    int cols,
    float alpha = 1.0f,
    float beta = 0.0f,
    cudaStream_t stream = nullptr
);

void matrixVectorMultiply(
    half* output,
    const half* matrix,
    const half* vector,
    int rows,
    int cols,
    float alpha = 1.0f,
    float beta = 0.0f,
    cudaStream_t stream = nullptr
);

// Matrix-matrix multiplication
void matrixMultiply(
    float* output,
    const float* matrix_a,
    const float* matrix_b,
    int m,
    int k,
    int n,
    float alpha = 1.0f,
    float beta = 0.0f,
    cudaStream_t stream = nullptr
);

void matrixMultiply(
    half* output,
    const half* matrix_a,
    const half* matrix_b,
    int m,
    int k,
    int n,
    float alpha = 1.0f,
    float beta = 0.0f,
    cudaStream_t stream = nullptr
);

// Vector operations
void vectorAdd(
    float* output,
    const float* vector_a,
    const float* vector_b,
    int size,
    float alpha = 1.0f,
    float beta = 1.0f,
    cudaStream_t stream = nullptr
);

void vectorAdd(
    half* output,
    const half* vector_a,
    const half* vector_b,
    int size,
    float alpha = 1.0f,
    float beta = 1.0f,
    cudaStream_t stream = nullptr
);

void vectorScale(
    float* output,
    const float* vector,
    int size,
    float scale,
    cudaStream_t stream = nullptr
);

void vectorScale(
    half* output,
    const half* vector,
    int size,
    float scale,
    cudaStream_t stream = nullptr
);

// Matrix operations
void matrixAdd(
    float* output,
    const float* matrix_a,
    const float* matrix_b,
    int rows,
    int cols,
    float alpha = 1.0f,
    float beta = 1.0f,
    cudaStream_t stream = nullptr
);

void matrixAdd(
    half* output,
    const half* matrix_a,
    const half* matrix_b,
    int rows,
    int cols,
    float alpha = 1.0f,
    float beta = 1.0f,
    cudaStream_t stream = nullptr
);

void matrixScale(
    float* output,
    const float* matrix,
    int rows,
    int cols,
    float scale,
    cudaStream_t stream = nullptr
);

void matrixScale(
    half* output,
    const half* matrix,
    int rows,
    int cols,
    float scale,
    cudaStream_t stream = nullptr
);

// Transpose operations
void matrixTranspose(
    float* output,
    const float* input,
    int rows,
    int cols,
    cudaStream_t stream = nullptr
);

void matrixTranspose(
    half* output,
    const half* input,
    int rows,
    int cols,
    cudaStream_t stream = nullptr
);

// Batch operations
void batchMatrixMultiply(
    float* output,
    const float* matrix_a,
    const float* matrix_b,
    int batch_size,
    int m,
    int k,
    int n,
    float alpha = 1.0f,
    float beta = 0.0f,
    cudaStream_t stream = nullptr
);

void batchMatrixMultiply(
    half* output,
    const half* matrix_a,
    const half* matrix_b,
    int batch_size,
    int m,
    int k,
    int n,
    float alpha = 1.0f,
    float beta = 0.0f,
    cudaStream_t stream = nullptr
);

// Reduction operations
void reduceSum(
    float* output,
    const float* input,
    int size,
    cudaStream_t stream = nullptr
);

void reduceSum(
    half* output,
    const half* input,
    int size,
    cudaStream_t stream = nullptr
);

void reduceMax(
    float* output,
    const float* input,
    int size,
    cudaStream_t stream = nullptr
);

void reduceMax(
    half* output,
    const half* input,
    int size,
    cudaStream_t stream = nullptr
);

// Utility functions
void setMatrixToIdentity(
    float* matrix,
    int size,
    cudaStream_t stream = nullptr
);

void setMatrixToIdentity(
    half* matrix,
    int size,
    cudaStream_t stream = nullptr
);

void setMatrixToZero(
    float* matrix,
    int rows,
    int cols,
    cudaStream_t stream = nullptr
);

void setMatrixToZero(
    half* matrix,
    int rows,
    int cols,
    cudaStream_t stream = nullptr
);

} // namespace llm_inference
} // namespace cogniware
