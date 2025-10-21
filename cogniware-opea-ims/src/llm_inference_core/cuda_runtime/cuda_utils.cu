#include "cuda_utils.h"
#include <spdlog/spdlog.h>

namespace msmartcompute {
namespace llm_inference {

CUDADeviceProperties getDeviceProperties(int device_id) {
    CUDADeviceProperties props;
    props.device_id = device_id;

    // Get device properties
    CUDA_CHECK(cudaGetDeviceProperties(&props.properties, device_id));

    // Get memory info
    size_t free, total;
    getDeviceMemoryInfo(free, total, device_id);
    props.total_memory = total;
    props.free_memory = free;

    // Get compute capability
    props.compute_capability_major = props.properties.major;
    props.compute_capability_minor = props.properties.minor;

    // Get multi processor count
    props.multi_processor_count = props.properties.multiProcessorCount;

    // Get max threads per block
    props.max_threads_per_block = props.properties.maxThreadsPerBlock;

    // Get warp size
    props.warp_size = props.properties.warpSize;

    // Get max shared memory per block
    props.max_shared_memory_per_block = props.properties.sharedMemPerBlock;

    // Get max registers per block
    props.max_registers_per_block = props.properties.regsPerBlock;

    // Get max threads per multi processor
    props.max_threads_per_multi_processor = props.properties.maxThreadsPerMultiProcessor;

    // Get max blocks per multi processor
    props.max_blocks_per_multi_processor = props.properties.maxBlocksPerMultiProcessor;

    // Get max grid dimensions
    props.max_grid_dim_x = props.properties.maxGridSize[0];
    props.max_grid_dim_y = props.properties.maxGridSize[1];
    props.max_grid_dim_z = props.properties.maxGridSize[2];

    // Get max block dimensions
    props.max_block_dim_x = props.properties.maxThreadsDim[0];
    props.max_block_dim_y = props.properties.maxThreadsDim[1];
    props.max_block_dim_z = props.properties.maxThreadsDim[2];

    // Get clock rate
    props.clock_rate = props.properties.clockRate;

    // Get memory clock rate
    props.memory_clock_rate = props.properties.memoryClockRate;

    // Get memory bus width
    props.memory_bus_width = props.properties.memoryBusWidth;

    // Get L2 cache size
    props.l2_cache_size = props.properties.l2CacheSize;

    // Calculate derived properties
    props.max_threads_per_sm = props.properties.maxThreadsPerMultiProcessor;
    props.max_blocks_per_sm = props.properties.maxBlocksPerMultiProcessor;
    props.max_shared_memory_per_sm = props.properties.sharedMemPerMultiprocessor;
    props.max_registers_per_sm = props.properties.regsPerMultiprocessor;
    props.max_warps_per_sm = props.max_threads_per_sm / props.warp_size;
    props.max_threads_per_warp = props.warp_size;
    props.max_blocks_per_grid = props.max_grid_dim_x * props.max_grid_dim_y * props.max_grid_dim_z;
    props.max_shared_memory_per_grid = props.max_shared_memory_per_block * props.max_blocks_per_grid;
    props.max_registers_per_grid = props.max_registers_per_block * props.max_blocks_per_grid;
    props.max_warps_per_grid = props.max_threads_per_grid / props.warp_size;
    props.max_threads_per_grid = props.max_threads_per_block * props.max_blocks_per_grid;
    props.max_blocks_per_device = props.max_blocks_per_sm * props.multi_processor_count;
    props.max_shared_memory_per_device = props.max_shared_memory_per_sm * props.multi_processor_count;
    props.max_registers_per_device = props.max_registers_per_sm * props.multi_processor_count;
    props.max_warps_per_device = props.max_warps_per_sm * props.multi_processor_count;
    props.max_threads_per_device = props.max_threads_per_sm * props.multi_processor_count;

    return props;
}

void initializeCUDA(int device_id) {
    try {
        // Set device
        CUDA_CHECK(cudaSetDevice(device_id));

        // Get device properties
        cudaDeviceProp prop;
        CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));

        spdlog::info("Initialized CUDA device {}: {}", device_id, prop.name);
        spdlog::info("Compute capability: {}.{}", prop.major, prop.minor);
        spdlog::info("Total memory: {} MB", prop.totalGlobalMem / (1024 * 1024));
        spdlog::info("Multi-processors: {}", prop.multiProcessorCount);
        spdlog::info("Max threads per block: {}", prop.maxThreadsPerBlock);
        spdlog::info("Warp size: {}", prop.warpSize);
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize CUDA: {}", e.what());
        throw;
    }
}

int getCurrentDevice() {
    int device;
    CUDA_CHECK(cudaGetDevice(&device));
    return device;
}

void setDevice(int device_id) {
    CUDA_CHECK(cudaSetDevice(device_id));
}

int getDeviceCount() {
    int count;
    CUDA_CHECK(cudaGetDeviceCount(&count));
    return count;
}

std::string getDeviceName(int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    return prop.name;
}

void getDeviceMemoryInfo(size_t& free, size_t& total, int device_id) {
    CUDA_CHECK(cudaSetDevice(device_id));
    CUDA_CHECK(cudaMemGetInfo(&free, &total));
}

void getDeviceComputeCapability(int& major, int& minor, int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    major = prop.major;
    minor = prop.minor;
}

int getDeviceMultiProcessorCount(int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    return prop.multiProcessorCount;
}

int getDeviceMaxThreadsPerBlock(int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    return prop.maxThreadsPerBlock;
}

int getDeviceWarpSize(int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    return prop.warpSize;
}

int getDeviceMaxSharedMemoryPerBlock(int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    return prop.sharedMemPerBlock;
}

int getDeviceMaxRegistersPerBlock(int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    return prop.regsPerBlock;
}

int getDeviceMaxThreadsPerMultiProcessor(int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    return prop.maxThreadsPerMultiProcessor;
}

int getDeviceMaxBlocksPerMultiProcessor(int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    return prop.maxBlocksPerMultiProcessor;
}

void getDeviceMaxGridDimensions(int& x, int& y, int& z, int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    x = prop.maxGridSize[0];
    y = prop.maxGridSize[1];
    z = prop.maxGridSize[2];
}

void getDeviceMaxBlockDimensions(int& x, int& y, int& z, int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    x = prop.maxThreadsDim[0];
    y = prop.maxThreadsDim[1];
    z = prop.maxThreadsDim[2];
}

int getDeviceClockRate(int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    return prop.clockRate;
}

int getDeviceMemoryClockRate(int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    return prop.memoryClockRate;
}

int getDeviceMemoryBusWidth(int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    return prop.memoryBusWidth;
}

int getDeviceL2CacheSize(int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    return prop.l2CacheSize;
}

int getDeviceMaxThreadsPerSM(int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    return prop.maxThreadsPerMultiProcessor;
}

int getDeviceMaxBlocksPerSM(int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    return prop.maxBlocksPerMultiProcessor;
}

int getDeviceMaxSharedMemoryPerSM(int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    return prop.sharedMemPerMultiprocessor;
}

int getDeviceMaxRegistersPerSM(int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    return prop.regsPerMultiprocessor;
}

int getDeviceMaxWarpsPerSM(int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    return prop.maxThreadsPerMultiProcessor / prop.warpSize;
}

int getDeviceMaxThreadsPerWarp(int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    return prop.warpSize;
}

int getDeviceMaxBlocksPerGrid(int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    return prop.maxGridSize[0] * prop.maxGridSize[1] * prop.maxGridSize[2];
}

int getDeviceMaxSharedMemoryPerGrid(int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    return prop.sharedMemPerBlock * getDeviceMaxBlocksPerGrid(device_id);
}

int getDeviceMaxRegistersPerGrid(int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    return prop.regsPerBlock * getDeviceMaxBlocksPerGrid(device_id);
}

int getDeviceMaxWarpsPerGrid(int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    return getDeviceMaxThreadsPerGrid(device_id) / prop.warpSize;
}

int getDeviceMaxThreadsPerGrid(int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    return prop.maxThreadsPerBlock * getDeviceMaxBlocksPerGrid(device_id);
}

int getDeviceMaxBlocksPerDevice(int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    return prop.maxBlocksPerMultiProcessor * prop.multiProcessorCount;
}

int getDeviceMaxSharedMemoryPerDevice(int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    return prop.sharedMemPerMultiprocessor * prop.multiProcessorCount;
}

int getDeviceMaxRegistersPerDevice(int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    return prop.regsPerMultiprocessor * prop.multiProcessorCount;
}

int getDeviceMaxWarpsPerDevice(int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    return getDeviceMaxThreadsPerDevice(device_id) / prop.warpSize;
}

int getDeviceMaxThreadsPerDevice(int device_id) {
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, device_id));
    return prop.maxThreadsPerMultiProcessor * prop.multiProcessorCount;
}

} // namespace llm_inference
} // namespace msmartcompute
