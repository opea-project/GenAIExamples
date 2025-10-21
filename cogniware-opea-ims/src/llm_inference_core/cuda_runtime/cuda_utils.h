#pragma once

#include <cuda_runtime.h>
#include <cublas_v2.h>
#include <cusparse.h>
#include <spdlog/spdlog.h>
#include <stdexcept>
#include <string>

namespace cogniware {
namespace llm_inference {

// CUDA error checking macro
#define CUDA_CHECK(call) \
    do { \
        cudaError_t error = call; \
        if (error != cudaSuccess) { \
            throw std::runtime_error(std::string("CUDA error at ") + __FILE__ + ":" + \
                std::to_string(__LINE__) + ": " + cudaGetErrorString(error)); \
        } \
    } while(0)

// cuBLAS error checking macro
#define CUBLAS_CHECK(call) \
    do { \
        cublasStatus_t status = call; \
        if (status != CUBLAS_STATUS_SUCCESS) { \
            throw std::runtime_error(std::string("cuBLAS error at ") + __FILE__ + ":" + \
                std::to_string(__LINE__) + ": " + std::to_string(status)); \
        } \
    } while(0)

// cuSPARSE error checking macro
#define CUSPARSE_CHECK(call) \
    do { \
        cusparseStatus_t status = call; \
        if (status != CUSPARSE_STATUS_SUCCESS) { \
            throw std::runtime_error(std::string("cuSPARSE error at ") + __FILE__ + ":" + \
                std::to_string(__LINE__) + ": " + std::to_string(status)); \
        } \
    } while(0)

// CUDA device properties
struct CUDADeviceProperties {
    int device_id;
    cudaDeviceProp properties;
    size_t total_memory;
    size_t free_memory;
    int compute_capability_major;
    int compute_capability_minor;
    int multi_processor_count;
    int max_threads_per_block;
    int warp_size;
    int max_shared_memory_per_block;
    int max_registers_per_block;
    int max_threads_per_multi_processor;
    int max_blocks_per_multi_processor;
    int max_grid_dim_x;
    int max_grid_dim_y;
    int max_grid_dim_z;
    int max_block_dim_x;
    int max_block_dim_y;
    int max_block_dim_z;
    int clock_rate;
    int memory_clock_rate;
    int memory_bus_width;
    int l2_cache_size;
    int max_threads_per_sm;
    int max_blocks_per_sm;
    int max_shared_memory_per_sm;
    int max_registers_per_sm;
    int max_warps_per_sm;
    int max_threads_per_warp;
    int max_blocks_per_grid;
    int max_shared_memory_per_grid;
    int max_registers_per_grid;
    int max_warps_per_grid;
    int max_threads_per_grid;
    int max_blocks_per_device;
    int max_shared_memory_per_device;
    int max_registers_per_device;
    int max_warps_per_device;
    int max_threads_per_device;
};

// Get CUDA device properties
CUDADeviceProperties getDeviceProperties(int device_id = 0);

// Initialize CUDA
void initializeCUDA(int device_id = 0);

// Get current CUDA device
int getCurrentDevice();

// Set CUDA device
void setDevice(int device_id);

// Get device count
int getDeviceCount();

// Get device name
std::string getDeviceName(int device_id = 0);

// Get device memory info
void getDeviceMemoryInfo(size_t& free, size_t& total, int device_id = 0);

// Get device compute capability
void getDeviceComputeCapability(int& major, int& minor, int device_id = 0);

// Get device multi processor count
int getDeviceMultiProcessorCount(int device_id = 0);

// Get device max threads per block
int getDeviceMaxThreadsPerBlock(int device_id = 0);

// Get device warp size
int getDeviceWarpSize(int device_id = 0);

// Get device max shared memory per block
int getDeviceMaxSharedMemoryPerBlock(int device_id = 0);

// Get device max registers per block
int getDeviceMaxRegistersPerBlock(int device_id = 0);

// Get device max threads per multi processor
int getDeviceMaxThreadsPerMultiProcessor(int device_id = 0);

// Get device max blocks per multi processor
int getDeviceMaxBlocksPerMultiProcessor(int device_id = 0);

// Get device max grid dimensions
void getDeviceMaxGridDimensions(int& x, int& y, int& z, int device_id = 0);

// Get device max block dimensions
void getDeviceMaxBlockDimensions(int& x, int& y, int& z, int device_id = 0);

// Get device clock rate
int getDeviceClockRate(int device_id = 0);

// Get device memory clock rate
int getDeviceMemoryClockRate(int device_id = 0);

// Get device memory bus width
int getDeviceMemoryBusWidth(int device_id = 0);

// Get device L2 cache size
int getDeviceL2CacheSize(int device_id = 0);

// Get device max threads per SM
int getDeviceMaxThreadsPerSM(int device_id = 0);

// Get device max blocks per SM
int getDeviceMaxBlocksPerSM(int device_id = 0);

// Get device max shared memory per SM
int getDeviceMaxSharedMemoryPerSM(int device_id = 0);

// Get device max registers per SM
int getDeviceMaxRegistersPerSM(int device_id = 0);

// Get device max warps per SM
int getDeviceMaxWarpsPerSM(int device_id = 0);

// Get device max threads per warp
int getDeviceMaxThreadsPerWarp(int device_id = 0);

// Get device max blocks per grid
int getDeviceMaxBlocksPerGrid(int device_id = 0);

// Get device max shared memory per grid
int getDeviceMaxSharedMemoryPerGrid(int device_id = 0);

// Get device max registers per grid
int getDeviceMaxRegistersPerGrid(int device_id = 0);

// Get device max warps per grid
int getDeviceMaxWarpsPerGrid(int device_id = 0);

// Get device max threads per grid
int getDeviceMaxThreadsPerGrid(int device_id = 0);

// Get device max blocks per device
int getDeviceMaxBlocksPerDevice(int device_id = 0);

// Get device max shared memory per device
int getDeviceMaxSharedMemoryPerDevice(int device_id = 0);

// Get device max registers per device
int getDeviceMaxRegistersPerDevice(int device_id = 0);

// Get device max warps per device
int getDeviceMaxWarpsPerDevice(int device_id = 0);

// Get device max threads per device
int getDeviceMaxThreadsPerDevice(int device_id = 0);

} // namespace llm_inference
} // namespace cogniware
