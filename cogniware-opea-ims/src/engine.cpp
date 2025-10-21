#include "engine.h"
#include <cuda_runtime.h>
#include <cublas_v2.h>
#include <cudnn.h>
#include <json/json.h>
#include <memory>
#include <vector>
#include <string>
#include <unordered_map>
#include <mutex>
#include <thread>
#include <queue>
#include <condition_variable>
#include <spdlog/spdlog.h>
#include <fstream>
#include <stdexcept>

namespace cogniware {

class EngineImpl {
private:
    int device_id_;
    bool initialized_;
    cublasHandle_t cublas_handle_;
    cudnnHandle_t cudnn_handle_;
    std::mutex mutex_;
    std::queue<std::pair<std::string, std::promise<std::string>>> request_queue_;
    std::condition_variable queue_cv_;
    std::thread worker_thread_;
    bool running_;

    // Model cache
    std::unordered_map<std::string, std::shared_ptr<Model>> model_cache_;
    std::mutex model_cache_mutex_;

    // GPU memory management
    struct GPUMemory {
        void* ptr;
        size_t size;
    };
    std::vector<GPUMemory> gpu_memory_pool_;
    std::mutex memory_mutex_;

    void worker_loop() {
        while (running_) {
            std::unique_lock<std::mutex> lock(mutex_);
            queue_cv_.wait(lock, [this] { return !request_queue_.empty() || !running_; });

            while (!request_queue_.empty()) {
                auto [request, promise] = std::move(request_queue_.front());
                request_queue_.pop();
                lock.unlock();

                try {
                    std::string response = process_request_internal(request);
                    promise.set_value(response);
                } catch (const std::exception& e) {
                    promise.set_exception(std::current_exception());
                }

                lock.lock();
            }
        }
    }

    std::string process_request_internal(const std::string& request_json) {
        Json::Value request;
        Json::Reader reader;
        if (!reader.parse(request_json, request)) {
            throw std::runtime_error("Invalid JSON request");
        }

        // Extract model and prompt
        std::string model_name = request["model"].asString();
        std::string prompt = request["prompt"].asString();

        // Get or load model
        auto model = get_model(model_name);
        if (!model) {
            throw std::runtime_error("Model not found: " + model_name);
        }

        // Process the request using CUDA
        return model->process(prompt);
    }

    std::shared_ptr<Model> get_model(const std::string& model_name) {
        std::lock_guard<std::mutex> lock(model_cache_mutex_);
        auto it = model_cache_.find(model_name);
        if (it != model_cache_.end()) {
            return it->second;
        }

        // Load model if not in cache
        auto model = std::make_shared<Model>(model_name, device_id_);
        model_cache_[model_name] = model;
        return model;
    }

    void* allocate_gpu_memory(size_t size) {
        std::lock_guard<std::mutex> lock(memory_mutex_);
        void* ptr;
        cudaError_t error = cudaMalloc(&ptr, size);
        if (error != cudaSuccess) {
            throw std::runtime_error("Failed to allocate GPU memory: " + 
                                   std::string(cudaGetErrorString(error)));
        }
        gpu_memory_pool_.push_back({ptr, size});
        return ptr;
    }

    void free_gpu_memory(void* ptr) {
        std::lock_guard<std::mutex> lock(memory_mutex_);
        auto it = std::find_if(gpu_memory_pool_.begin(), gpu_memory_pool_.end(),
                             [ptr](const GPUMemory& mem) { return mem.ptr == ptr; });
        if (it != gpu_memory_pool_.end()) {
            cudaFree(ptr);
            gpu_memory_pool_.erase(it);
        }
    }

public:
    EngineImpl(int device_id) : device_id_(device_id), initialized_(false), running_(false) {}

    bool initialize() {
        if (initialized_) return true;

        try {
            // Set CUDA device
            cudaError_t error = cudaSetDevice(device_id_);
            if (error != cudaSuccess) {
                throw std::runtime_error("Failed to set CUDA device: " + 
                                       std::string(cudaGetErrorString(error)));
            }

            // Initialize cuBLAS
            cublasStatus_t cublas_status = cublasCreate(&cublas_handle_);
            if (cublas_status != CUBLAS_STATUS_SUCCESS) {
                throw std::runtime_error("Failed to initialize cuBLAS");
            }

            // Initialize cuDNN
            cudnnStatus_t cudnn_status = cudnnCreate(&cudnn_handle_);
            if (cudnn_status != CUDNN_STATUS_SUCCESS) {
                throw std::runtime_error("Failed to initialize cuDNN");
            }

            // Start worker thread
            running_ = true;
            worker_thread_ = std::thread(&EngineImpl::worker_loop, this);

            initialized_ = true;
            return true;
        } catch (const std::exception& e) {
            cleanup();
            throw;
        }
    }

    std::string process_request(const std::string& request_json) {
        if (!initialized_) {
            throw std::runtime_error("Engine not initialized");
        }

        std::promise<std::string> promise;
        std::future<std::string> future = promise.get_future();

        {
            std::lock_guard<std::mutex> lock(mutex_);
            request_queue_.push({request_json, std::move(promise)});
        }
        queue_cv_.notify_one();

        return future.get();
    }

    void shutdown() {
        if (!initialized_) return;

        {
            std::lock_guard<std::mutex> lock(mutex_);
            running_ = false;
        }
        queue_cv_.notify_one();

        if (worker_thread_.joinable()) {
            worker_thread_.join();
        }

        cleanup();
    }

private:
    void cleanup() {
        if (initialized_) {
            cublasDestroy(cublas_handle_);
            cudnnDestroy(cudnn_handle_);

            // Free GPU memory
            for (const auto& mem : gpu_memory_pool_) {
                cudaFree(mem.ptr);
            }
            gpu_memory_pool_.clear();

            initialized_ = false;
        }
    }
};

// C interface implementation
extern "C" {

bool initialize_engine(int device_id) {
    try {
        static std::unique_ptr<EngineImpl> engine = std::make_unique<EngineImpl>(device_id);
        return engine->initialize();
    } catch (const std::exception& e) {
        return false;
    }
}

const char* process_request(const char* request_json, char* response_buffer) {
    try {
        static std::unique_ptr<EngineImpl> engine = std::make_unique<EngineImpl>(0);
        std::string response = engine->process_request(request_json);
        strncpy(response_buffer, response.c_str(), response.size());
        response_buffer[response.size()] = '\0';
        return response_buffer;
    } catch (const std::exception& e) {
        return nullptr;
    }
}

void shutdown_engine() {
    static std::unique_ptr<EngineImpl> engine = std::make_unique<EngineImpl>(0);
    engine->shutdown();
}

} // extern "C"

} // namespace cogniware 