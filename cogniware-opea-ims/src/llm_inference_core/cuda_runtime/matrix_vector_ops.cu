#include "matrix_vector_ops.h"
#include "cuda_utils.h"
#include <cublas_v2.h>
#include <spdlog/spdlog.h>

namespace msmartcompute {
namespace llm_inference {

// Helper function to get cuBLAS handle
static cublasHandle_t getCublasHandle() {
    static cublasHandle_t handle = nullptr;
    if (handle == nullptr) {
        CUDA_CHECK(cublasCreate(&handle));
    }
    return handle;
}

// Matrix-vector multiplication kernels
__global__ void matrixVectorMultiplyKernel(
    float* output,
    const float* matrix,
    const float* vector,
    int rows,
    int cols,
    float alpha,
    float beta
) {
    int row = blockIdx.x * blockDim.x + threadIdx.x;
    if (row < rows) {
        float sum = 0.0f;
        for (int col = 0; col < cols; ++col) {
            sum += matrix[row * cols + col] * vector[col];
        }
        output[row] = alpha * sum + beta * output[row];
    }
}

__global__ void matrixVectorMultiplyKernel(
    half* output,
    const half* matrix,
    const half* vector,
    int rows,
    int cols,
    float alpha,
    float beta
) {
    int row = blockIdx.x * blockDim.x + threadIdx.x;
    if (row < rows) {
        float sum = 0.0f;
        for (int col = 0; col < cols; ++col) {
            sum += __half2float(matrix[row * cols + col]) * __half2float(vector[col]);
        }
        output[row] = __float2half(alpha * sum + beta * __half2float(output[row]));
    }
}

// Matrix-vector multiplication implementation
void matrixVectorMultiply(
    float* output,
    const float* matrix,
    const float* vector,
    int rows,
    int cols,
    float alpha,
    float beta,
    cudaStream_t stream
) {
    cublasHandle_t handle = getCublasHandle();
    if (stream) {
        CUDA_CHECK(cublasSetStream(handle, stream));
    }
    
    const float* alpha_ptr = &alpha;
    const float* beta_ptr = &beta;
    
    CUDA_CHECK(cublasSgemv(
        handle,
        CUBLAS_OP_N,
        rows,
        cols,
        alpha_ptr,
        matrix,
        rows,
        vector,
        1,
        beta_ptr,
        output,
        1
    ));
}

void matrixVectorMultiply(
    half* output,
    const half* matrix,
    const half* vector,
    int rows,
    int cols,
    float alpha,
    float beta,
    cudaStream_t stream
) {
    cublasHandle_t handle = getCublasHandle();
    if (stream) {
        CUDA_CHECK(cublasSetStream(handle, stream));
    }
    
    const float* alpha_ptr = &alpha;
    const float* beta_ptr = &beta;
    
    CUDA_CHECK(cublasHgemv(
        handle,
        CUBLAS_OP_N,
        rows,
        cols,
        alpha_ptr,
        matrix,
        rows,
        vector,
        1,
        beta_ptr,
        output,
        1
    ));
}

// Matrix-matrix multiplication implementation
void matrixMultiply(
    float* output,
    const float* matrix_a,
    const float* matrix_b,
    int m,
    int k,
    int n,
    float alpha,
    float beta,
    cudaStream_t stream
) {
    cublasHandle_t handle = getCublasHandle();
    if (stream) {
        CUDA_CHECK(cublasSetStream(handle, stream));
    }
    
    const float* alpha_ptr = &alpha;
    const float* beta_ptr = &beta;
    
    CUDA_CHECK(cublasSgemm(
        handle,
        CUBLAS_OP_N,
        CUBLAS_OP_N,
        m,
        n,
        k,
        alpha_ptr,
        matrix_a,
        m,
        matrix_b,
        k,
        beta_ptr,
        output,
        m
    ));
}

void matrixMultiply(
    half* output,
    const half* matrix_a,
    const half* matrix_b,
    int m,
    int k,
    int n,
    float alpha,
    float beta,
    cudaStream_t stream
) {
    cublasHandle_t handle = getCublasHandle();
    if (stream) {
        CUDA_CHECK(cublasSetStream(handle, stream));
    }
    
    const float* alpha_ptr = &alpha;
    const float* beta_ptr = &beta;
    
    CUDA_CHECK(cublasHgemm(
        handle,
        CUBLAS_OP_N,
        CUBLAS_OP_N,
        m,
        n,
        k,
        alpha_ptr,
        matrix_a,
        m,
        matrix_b,
        k,
        beta_ptr,
        output,
        m
    ));
}

// Vector operations kernels
__global__ void vectorAddKernel(
    float* output,
    const float* vector_a,
    const float* vector_b,
    int size,
    float alpha,
    float beta
) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        output[idx] = alpha * vector_a[idx] + beta * vector_b[idx];
    }
}

__global__ void vectorAddKernel(
    half* output,
    const half* vector_a,
    const half* vector_b,
    int size,
    float alpha,
    float beta
) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        output[idx] = __float2half(
            alpha * __half2float(vector_a[idx]) +
            beta * __half2float(vector_b[idx])
        );
    }
}

__global__ void vectorScaleKernel(
    float* output,
    const float* vector,
    int size,
    float scale
) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        output[idx] = scale * vector[idx];
    }
}

__global__ void vectorScaleKernel(
    half* output,
    const half* vector,
    int size,
    float scale
) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        output[idx] = __float2half(scale * __half2float(vector[idx]));
    }
}

// Vector operations implementation
void vectorAdd(
    float* output,
    const float* vector_a,
    const float* vector_b,
    int size,
    float alpha,
    float beta,
    cudaStream_t stream
) {
    int block_size = 256;
    int num_blocks = (size + block_size - 1) / block_size;
    
    vectorAddKernel<<<num_blocks, block_size, 0, stream>>>(
        output, vector_a, vector_b, size, alpha, beta
    );
    CUDA_CHECK(cudaGetLastError());
}

void vectorAdd(
    half* output,
    const half* vector_a,
    const half* vector_b,
    int size,
    float alpha,
    float beta,
    cudaStream_t stream
) {
    int block_size = 256;
    int num_blocks = (size + block_size - 1) / block_size;
    
    vectorAddKernel<<<num_blocks, block_size, 0, stream>>>(
        output, vector_a, vector_b, size, alpha, beta
    );
    CUDA_CHECK(cudaGetLastError());
}

void vectorScale(
    float* output,
    const float* vector,
    int size,
    float scale,
    cudaStream_t stream
) {
    int block_size = 256;
    int num_blocks = (size + block_size - 1) / block_size;
    
    vectorScaleKernel<<<num_blocks, block_size, 0, stream>>>(
        output, vector, size, scale
    );
    CUDA_CHECK(cudaGetLastError());
}

void vectorScale(
    half* output,
    const half* vector,
    int size,
    float scale,
    cudaStream_t stream
) {
    int block_size = 256;
    int num_blocks = (size + block_size - 1) / block_size;
    
    vectorScaleKernel<<<num_blocks, block_size, 0, stream>>>(
        output, vector, size, scale
    );
    CUDA_CHECK(cudaGetLastError());
}

// Matrix operations kernels
__global__ void matrixAddKernel(
    float* output,
    const float* matrix_a,
    const float* matrix_b,
    int rows,
    int cols,
    float alpha,
    float beta
) {
    int row = blockIdx.x * blockDim.x + threadIdx.x;
    int col = blockIdx.y * blockDim.y + threadIdx.y;
    
    if (row < rows && col < cols) {
        int idx = row * cols + col;
        output[idx] = alpha * matrix_a[idx] + beta * matrix_b[idx];
    }
}

__global__ void matrixAddKernel(
    half* output,
    const half* matrix_a,
    const half* matrix_b,
    int rows,
    int cols,
    float alpha,
    float beta
) {
    int row = blockIdx.x * blockDim.x + threadIdx.x;
    int col = blockIdx.y * blockDim.y + threadIdx.y;
    
    if (row < rows && col < cols) {
        int idx = row * cols + col;
        output[idx] = __float2half(
            alpha * __half2float(matrix_a[idx]) +
            beta * __half2float(matrix_b[idx])
        );
    }
}

__global__ void matrixScaleKernel(
    float* output,
    const float* matrix,
    int rows,
    int cols,
    float scale
) {
    int row = blockIdx.x * blockDim.x + threadIdx.x;
    int col = blockIdx.y * blockDim.y + threadIdx.y;
    
    if (row < rows && col < cols) {
        int idx = row * cols + col;
        output[idx] = scale * matrix[idx];
    }
}

__global__ void matrixScaleKernel(
    half* output,
    const half* matrix,
    int rows,
    int cols,
    float scale
) {
    int row = blockIdx.x * blockDim.x + threadIdx.x;
    int col = blockIdx.y * blockDim.y + threadIdx.y;
    
    if (row < rows && col < cols) {
        int idx = row * cols + col;
        output[idx] = __float2half(scale * __half2float(matrix[idx]));
    }
}

// Matrix operations implementation
void matrixAdd(
    float* output,
    const float* matrix_a,
    const float* matrix_b,
    int rows,
    int cols,
    float alpha,
    float beta,
    cudaStream_t stream
) {
    dim3 block(16, 16);
    dim3 grid(
        (rows + block.x - 1) / block.x,
        (cols + block.y - 1) / block.y
    );
    
    matrixAddKernel<<<grid, block, 0, stream>>>(
        output, matrix_a, matrix_b, rows, cols, alpha, beta
    );
    CUDA_CHECK(cudaGetLastError());
}

void matrixAdd(
    half* output,
    const half* matrix_a,
    const half* matrix_b,
    int rows,
    int cols,
    float alpha,
    float beta,
    cudaStream_t stream
) {
    dim3 block(16, 16);
    dim3 grid(
        (rows + block.x - 1) / block.x,
        (cols + block.y - 1) / block.y
    );
    
    matrixAddKernel<<<grid, block, 0, stream>>>(
        output, matrix_a, matrix_b, rows, cols, alpha, beta
    );
    CUDA_CHECK(cudaGetLastError());
}

void matrixScale(
    float* output,
    const float* matrix,
    int rows,
    int cols,
    float scale,
    cudaStream_t stream
) {
    dim3 block(16, 16);
    dim3 grid(
        (rows + block.x - 1) / block.x,
        (cols + block.y - 1) / block.y
    );
    
    matrixScaleKernel<<<grid, block, 0, stream>>>(
        output, matrix, rows, cols, scale
    );
    CUDA_CHECK(cudaGetLastError());
}

void matrixScale(
    half* output,
    const half* matrix,
    int rows,
    int cols,
    float scale,
    cudaStream_t stream
) {
    dim3 block(16, 16);
    dim3 grid(
        (rows + block.x - 1) / block.x,
        (cols + block.y - 1) / block.y
    );
    
    matrixScaleKernel<<<grid, block, 0, stream>>>(
        output, matrix, rows, cols, scale
    );
    CUDA_CHECK(cudaGetLastError());
}

// Transpose operations kernels
__global__ void matrixTransposeKernel(
    float* output,
    const float* input,
    int rows,
    int cols
) {
    int row = blockIdx.x * blockDim.x + threadIdx.x;
    int col = blockIdx.y * blockDim.y + threadIdx.y;
    
    if (row < rows && col < cols) {
        output[col * rows + row] = input[row * cols + col];
    }
}

__global__ void matrixTransposeKernel(
    half* output,
    const half* input,
    int rows,
    int cols
) {
    int row = blockIdx.x * blockDim.x + threadIdx.x;
    int col = blockIdx.y * blockDim.y + threadIdx.y;
    
    if (row < rows && col < cols) {
        output[col * rows + row] = input[row * cols + col];
    }
}

// Transpose operations implementation
void matrixTranspose(
    float* output,
    const float* input,
    int rows,
    int cols,
    cudaStream_t stream
) {
    dim3 block(16, 16);
    dim3 grid(
        (rows + block.x - 1) / block.x,
        (cols + block.y - 1) / block.y
    );
    
    matrixTransposeKernel<<<grid, block, 0, stream>>>(
        output, input, rows, cols
    );
    CUDA_CHECK(cudaGetLastError());
}

void matrixTranspose(
    half* output,
    const half* input,
    int rows,
    int cols,
    cudaStream_t stream
) {
    dim3 block(16, 16);
    dim3 grid(
        (rows + block.x - 1) / block.x,
        (cols + block.y - 1) / block.y
    );
    
    matrixTransposeKernel<<<grid, block, 0, stream>>>(
        output, input, rows, cols
    );
    CUDA_CHECK(cudaGetLastError());
}

// Batch matrix multiplication implementation
void batchMatrixMultiply(
    float* output,
    const float* matrix_a,
    const float* matrix_b,
    int batch_size,
    int m,
    int k,
    int n,
    float alpha,
    float beta,
    cudaStream_t stream
) {
    cublasHandle_t handle = getCublasHandle();
    if (stream) {
        CUDA_CHECK(cublasSetStream(handle, stream));
    }
    
    const float* alpha_ptr = &alpha;
    const float* beta_ptr = &beta;
    
    CUDA_CHECK(cublasSgemmStridedBatched(
        handle,
        CUBLAS_OP_N,
        CUBLAS_OP_N,
        m,
        n,
        k,
        alpha_ptr,
        matrix_a,
        m,
        m * k,
        matrix_b,
        k,
        k * n,
        beta_ptr,
        output,
        m,
        m * n,
        batch_size
    ));
}

void batchMatrixMultiply(
    half* output,
    const half* matrix_a,
    const half* matrix_b,
    int batch_size,
    int m,
    int k,
    int n,
    float alpha,
    float beta,
    cudaStream_t stream
) {
    cublasHandle_t handle = getCublasHandle();
    if (stream) {
        CUDA_CHECK(cublasSetStream(handle, stream));
    }
    
    const float* alpha_ptr = &alpha;
    const float* beta_ptr = &beta;
    
    CUDA_CHECK(cublasHgemmStridedBatched(
        handle,
        CUBLAS_OP_N,
        CUBLAS_OP_N,
        m,
        n,
        k,
        alpha_ptr,
        matrix_a,
        m,
        m * k,
        matrix_b,
        k,
        k * n,
        beta_ptr,
        output,
        m,
        m * n,
        batch_size
    ));
}

// Reduction operations kernels
__global__ void reduceSumKernel(
    float* output,
    const float* input,
    int size
) {
    extern __shared__ float sdata[];
    
    int tid = threadIdx.x;
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    sdata[tid] = (idx < size) ? input[idx] : 0.0f;
    __syncthreads();
    
    for (int offset = blockDim.x/2; offset > 0; offset >>= 1) {
        if (tid < offset) {
            sdata[tid] += sdata[tid + offset];
        }
        __syncthreads();
    }
    
    if (tid == 0) {
        output[blockIdx.x] = sdata[0];
    }
}

__global__ void reduceSumKernel(
    half* output,
    const half* input,
    int size
) {
    extern __shared__ float sdata[];
    
    int tid = threadIdx.x;
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    sdata[tid] = (idx < size) ? __half2float(input[idx]) : 0.0f;
    __syncthreads();
    
    for (int offset = blockDim.x/2; offset > 0; offset >>= 1) {
        if (tid < offset) {
            sdata[tid] += sdata[tid + offset];
        }
        __syncthreads();
    }
    
    if (tid == 0) {
        output[blockIdx.x] = __float2half(sdata[0]);
    }
}

__global__ void reduceMaxKernel(
    float* output,
    const float* input,
    int size
) {
    extern __shared__ float sdata[];
    
    int tid = threadIdx.x;
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    sdata[tid] = (idx < size) ? input[idx] : -INFINITY;
    __syncthreads();
    
    for (int offset = blockDim.x/2; offset > 0; offset >>= 1) {
        if (tid < offset) {
            sdata[tid] = max(sdata[tid], sdata[tid + offset]);
        }
        __syncthreads();
    }
    
    if (tid == 0) {
        output[blockIdx.x] = sdata[0];
    }
}

__global__ void reduceMaxKernel(
    half* output,
    const half* input,
    int size
) {
    extern __shared__ float sdata[];
    
    int tid = threadIdx.x;
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    sdata[tid] = (idx < size) ? __half2float(input[idx]) : -INFINITY;
    __syncthreads();
    
    for (int offset = blockDim.x/2; offset > 0; offset >>= 1) {
        if (tid < offset) {
            sdata[tid] = max(sdata[tid], sdata[tid + offset]);
        }
        __syncthreads();
    }
    
    if (tid == 0) {
        output[blockIdx.x] = __float2half(sdata[0]);
    }
}

// Reduction operations implementation
void reduceSum(
    float* output,
    const float* input,
    int size,
    cudaStream_t stream
) {
    int block_size = 256;
    int num_blocks = (size + block_size - 1) / block_size;
    size_t shared_mem_size = block_size * sizeof(float);
    
    reduceSumKernel<<<num_blocks, block_size, shared_mem_size, stream>>>(
        output, input, size
    );
    CUDA_CHECK(cudaGetLastError());
}

void reduceSum(
    half* output,
    const half* input,
    int size,
    cudaStream_t stream
) {
    int block_size = 256;
    int num_blocks = (size + block_size - 1) / block_size;
    size_t shared_mem_size = block_size * sizeof(float);
    
    reduceSumKernel<<<num_blocks, block_size, shared_mem_size, stream>>>(
        output, input, size
    );
    CUDA_CHECK(cudaGetLastError());
}

void reduceMax(
    float* output,
    const float* input,
    int size,
    cudaStream_t stream
) {
    int block_size = 256;
    int num_blocks = (size + block_size - 1) / block_size;
    size_t shared_mem_size = block_size * sizeof(float);
    
    reduceMaxKernel<<<num_blocks, block_size, shared_mem_size, stream>>>(
        output, input, size
    );
    CUDA_CHECK(cudaGetLastError());
}

void reduceMax(
    half* output,
    const half* input,
    int size,
    cudaStream_t stream
) {
    int block_size = 256;
    int num_blocks = (size + block_size - 1) / block_size;
    size_t shared_mem_size = block_size * sizeof(float);
    
    reduceMaxKernel<<<num_blocks, block_size, shared_mem_size, stream>>>(
        output, input, size
    );
    CUDA_CHECK(cudaGetLastError());
}

// Utility functions kernels
__global__ void setMatrixToIdentityKernel(
    float* matrix,
    int size
) {
    int row = blockIdx.x * blockDim.x + threadIdx.x;
    int col = blockIdx.y * blockDim.y + threadIdx.y;
    
    if (row < size && col < size) {
        matrix[row * size + col] = (row == col) ? 1.0f : 0.0f;
    }
}

__global__ void setMatrixToIdentityKernel(
    half* matrix,
    int size
) {
    int row = blockIdx.x * blockDim.x + threadIdx.x;
    int col = blockIdx.y * blockDim.y + threadIdx.y;
    
    if (row < size && col < size) {
        matrix[row * size + col] = (row == col) ? __float2half(1.0f) : __float2half(0.0f);
    }
}

__global__ void setMatrixToZeroKernel(
    float* matrix,
    int rows,
    int cols
) {
    int row = blockIdx.x * blockDim.x + threadIdx.x;
    int col = blockIdx.y * blockDim.y + threadIdx.y;
    
    if (row < rows && col < cols) {
        matrix[row * cols + col] = 0.0f;
    }
}

__global__ void setMatrixToZeroKernel(
    half* matrix,
    int rows,
    int cols
) {
    int row = blockIdx.x * blockDim.x + threadIdx.x;
    int col = blockIdx.y * blockDim.y + threadIdx.y;
    
    if (row < rows && col < cols) {
        matrix[row * cols + col] = __float2half(0.0f);
    }
}

// Utility functions implementation
void setMatrixToIdentity(
    float* matrix,
    int size,
    cudaStream_t stream
) {
    dim3 block(16, 16);
    dim3 grid(
        (size + block.x - 1) / block.x,
        (size + block.y - 1) / block.y
    );
    
    setMatrixToIdentityKernel<<<grid, block, 0, stream>>>(
        matrix, size
    );
    CUDA_CHECK(cudaGetLastError());
}

void setMatrixToIdentity(
    half* matrix,
    int size,
    cudaStream_t stream
) {
    dim3 block(16, 16);
    dim3 grid(
        (size + block.x - 1) / block.x,
        (size + block.y - 1) / block.y
    );
    
    setMatrixToIdentityKernel<<<grid, block, 0, stream>>>(
        matrix, size
    );
    CUDA_CHECK(cudaGetLastError());
}

void setMatrixToZero(
    float* matrix,
    int rows,
    int cols,
    cudaStream_t stream
) {
    dim3 block(16, 16);
    dim3 grid(
        (rows + block.x - 1) / block.x,
        (cols + block.y - 1) / block.y
    );
    
    setMatrixToZeroKernel<<<grid, block, 0, stream>>>(
        matrix, rows, cols
    );
    CUDA_CHECK(cudaGetLastError());
}

void setMatrixToZero(
    half* matrix,
    int rows,
    int cols,
    cudaStream_t stream
) {
    dim3 block(16, 16);
    dim3 grid(
        (rows + block.x - 1) / block.x,
        (cols + block.y - 1) / block.y
    );
    
    setMatrixToZeroKernel<<<grid, block, 0, stream>>>(
        matrix, rows, cols
    );
    CUDA_CHECK(cudaGetLastError());
}

} // namespace llm_inference
} // namespace msmartcompute
