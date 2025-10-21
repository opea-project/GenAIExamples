#include "llm_inference_core.h"
#include <cuda_runtime.h>
#include <cublas_v2.h>
#include <cudnn.h>
#include <stdexcept>
#include <fstream>
#include <sstream>

namespace cogniware {

// CUDA kernel for attention computation
__global__ void attention_kernel(
    const float* query, const float* key, const float* value,
    float* output, int batch_size, int seq_length, int num_heads, int head_dim) {
    
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    if (tid >= batch_size * seq_length * num_heads * head_dim) return;
    
    // Calculate indices
    int batch_idx = tid / (seq_length * num_heads * head_dim);
    int seq_idx = (tid / (num_heads * head_dim)) % seq_length;
    int head_idx = (tid / head_dim) % num_heads;
    int dim_idx = tid % head_dim;
    
    // Compute attention scores
    float score = 0.0f;
    for (int i = 0; i < seq_length; i++) {
        float q_val = query[batch_idx * seq_length * num_heads * head_dim + 
                          seq_idx * num_heads * head_dim + 
                          head_idx * head_dim + dim_idx];
        float k_val = key[batch_idx * seq_length * num_heads * head_dim + 
                         i * num_heads * head_dim + 
                         head_idx * head_dim + dim_idx];
        score += q_val * k_val;
    }
    
    // Apply softmax
    score = expf(score) / (expf(score) + 1e-6f);
    
    // Compute weighted sum
    float weighted_sum = 0.0f;
    for (int i = 0; i < seq_length; i++) {
        float v_val = value[batch_idx * seq_length * num_heads * head_dim + 
                          i * num_heads * head_dim + 
                          head_idx * head_dim + dim_idx];
        weighted_sum += score * v_val;
    }
    
    // Store result
    output[tid] = weighted_sum;
}

// CUDA kernel for feedforward network
__global__ void feedforward_kernel(
    const float* input, float* output, int batch_size, int hidden_size) {
    
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    if (tid >= batch_size * hidden_size) return;
    
    // Calculate indices
    int batch_idx = tid / hidden_size;
    int dim_idx = tid % hidden_size;
    
    // Apply feedforward transformation (simple ReLU activation)
    float val = input[tid];
    output[tid] = val > 0.0f ? val : 0.0f;
}

// CUDA kernel for layer normalization
__global__ void layer_norm_kernel(
    const float* input, float* output, int batch_size, int hidden_size) {
    
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    if (tid >= batch_size * hidden_size) return;
    
    // Calculate indices
    int batch_idx = tid / hidden_size;
    int dim_idx = tid % hidden_size;
    
    // Compute mean
    float mean = 0.0f;
    for (int i = 0; i < hidden_size; i++) {
        mean += input[batch_idx * hidden_size + i];
    }
    mean /= hidden_size;
    
    // Compute variance
    float variance = 0.0f;
    for (int i = 0; i < hidden_size; i++) {
        float diff = input[batch_idx * hidden_size + i] - mean;
        variance += diff * diff;
    }
    variance /= hidden_size;
    
    // Normalize
    float val = input[tid];
    output[tid] = (val - mean) / sqrtf(variance + 1e-6f);
}

LLMInferenceCore::LLMInferenceCore(const LLMConfig& config, int device_id)
    : config_(config), device_id_(device_id) {
    initialize();
}

LLMInferenceCore::~LLMInferenceCore() {
    // Free CUDA resources
    cublasDestroy(cublas_handle_);
    cudnnDestroy(cudnn_handle_);
    cudaStreamDestroy(stream_);
    cudaEventDestroy(start_event_);
    cudaEventDestroy(end_event_);
    
    // Free model weights
    free_weights();
}

void LLMInferenceCore::initialize() {
    try {
        // Set CUDA device
        cudaError_t error = cudaSetDevice(device_id_);
        if (error != cudaSuccess) {
            throw std::runtime_error("Failed to set CUDA device: " + 
                                   std::string(cudaGetErrorString(error)));
        }
        
        // Initialize CUDA resources
        initialize_cuda();
        
        // Load model weights
        load_weights();
    } catch (const std::exception& e) {
        throw std::runtime_error("Failed to initialize LLM inference core: " + 
                               std::string(e.what()));
    }
}

void LLMInferenceCore::initialize_cuda() {
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
    
    // Create CUDA stream
    cudaError_t error = cudaStreamCreate(&stream_);
    if (error != cudaSuccess) {
        throw std::runtime_error("Failed to create CUDA stream: " + 
                               std::string(cudaGetErrorString(error)));
    }
    
    // Create CUDA events
    error = cudaEventCreate(&start_event_);
    if (error != cudaSuccess) {
        throw std::runtime_error("Failed to create start event: " + 
                               std::string(cudaGetErrorString(error)));
    }
    
    error = cudaEventCreate(&end_event_);
    if (error != cudaSuccess) {
        throw std::runtime_error("Failed to create end event: " + 
                               std::string(cudaGetErrorString(error)));
    }
}

void LLMInferenceCore::load_weights() {
    try {
        // Allocate GPU memory for weights
        size_t embedding_size = config_.vocab_size * config_.hidden_size * sizeof(float);
        size_t attention_size = config_.num_layers * config_.num_heads * config_.hidden_size * sizeof(float);
        size_t feedforward_size = config_.num_layers * config_.hidden_size * config_.hidden_size * sizeof(float);
        size_t layer_norm_size = config_.num_layers * config_.hidden_size * sizeof(float);
        
        cudaMalloc(&weights_.embedding_weights, embedding_size);
        cudaMalloc(&weights_.attention_weights, attention_size);
        cudaMalloc(&weights_.feedforward_weights, feedforward_size);
        cudaMalloc(&weights_.layer_norm_weights, layer_norm_size);
        
        // Load weights from file
        std::string weights_path = "models/" + std::to_string(config_.hidden_size) + "/weights.bin";
        std::ifstream file(weights_path, std::ios::binary);
        if (!file) {
            throw std::runtime_error("Failed to open weights file: " + weights_path);
        }
        
        // Read and transfer weights to GPU
        std::vector<float> buffer;
        
        // Embedding weights
        buffer.resize(config_.vocab_size * config_.hidden_size);
        file.read(reinterpret_cast<char*>(buffer.data()), embedding_size);
        cudaMemcpy(weights_.embedding_weights, buffer.data(), embedding_size, cudaMemcpyHostToDevice);
        
        // Attention weights
        buffer.resize(config_.num_layers * config_.num_heads * config_.hidden_size);
        file.read(reinterpret_cast<char*>(buffer.data()), attention_size);
        cudaMemcpy(weights_.attention_weights, buffer.data(), attention_size, cudaMemcpyHostToDevice);
        
        // Feedforward weights
        buffer.resize(config_.num_layers * config_.hidden_size * config_.hidden_size);
        file.read(reinterpret_cast<char*>(buffer.data()), feedforward_size);
        cudaMemcpy(weights_.feedforward_weights, buffer.data(), feedforward_size, cudaMemcpyHostToDevice);
        
        // Layer normalization weights
        buffer.resize(config_.num_layers * config_.hidden_size);
        file.read(reinterpret_cast<char*>(buffer.data()), layer_norm_size);
        cudaMemcpy(weights_.layer_norm_weights, buffer.data(), layer_norm_size, cudaMemcpyHostToDevice);
        
    } catch (const std::exception& e) {
        throw std::runtime_error("Failed to load weights: " + std::string(e.what()));
    }
}

void LLMInferenceCore::free_weights() {
    // Free GPU memory for weights
    if (weights_.embedding_weights) cudaFree(weights_.embedding_weights);
    if (weights_.attention_weights) cudaFree(weights_.attention_weights);
    if (weights_.feedforward_weights) cudaFree(weights_.feedforward_weights);
    if (weights_.layer_norm_weights) cudaFree(weights_.layer_norm_weights);
}

std::vector<int> LLMInferenceCore::process(const std::vector<int>& input_tokens) {
    if (input_tokens.empty()) {
        throw std::runtime_error("Empty input tokens");
    }
    
    try {
        // Record start time
        cudaEventRecord(start_event_, stream_);
        
        // Allocate GPU memory for input and output
        size_t input_size = input_tokens.size() * sizeof(int);
        size_t hidden_size = input_tokens.size() * config_.hidden_size * sizeof(float);
        
        int* d_input;
        float* d_hidden;
        float* d_output;
        
        cudaMalloc(&d_input, input_size);
        cudaMalloc(&d_hidden, hidden_size);
        cudaMalloc(&d_output, hidden_size);
        
        // Copy input to GPU
        cudaMemcpy(d_input, input_tokens.data(), input_size, cudaMemcpyHostToDevice);
        
        // Process through transformer layers
        for (int layer = 0; layer < config_.num_layers; layer++) {
            // Compute attention
            compute_attention(
                d_hidden,
                weights_.attention_weights,
                weights_.attention_weights + config_.hidden_size,
                d_output,
                input_tokens.size(),
                input_tokens.size()
            );
            
            // Compute feedforward
            compute_feedforward(d_output, d_hidden, input_tokens.size());
            
            // Apply layer normalization
            compute_layer_norm(d_hidden, d_output, input_tokens.size());
            
            // Swap buffers
            std::swap(d_hidden, d_output);
        }
        
        // Record end time
        cudaEventRecord(end_event_, stream_);
        cudaEventSynchronize(end_event_);
        
        // Copy result back to host
        std::vector<float> output_hidden(input_tokens.size() * config_.hidden_size);
        cudaMemcpy(output_hidden.data(), d_hidden, hidden_size, cudaMemcpyDeviceToHost);
        
        // Free GPU memory
        cudaFree(d_input);
        cudaFree(d_hidden);
        cudaFree(d_output);
        
        // Convert output to token IDs (simple argmax for now)
        std::vector<int> output_tokens(input_tokens.size());
        for (size_t i = 0; i < input_tokens.size(); i++) {
            float max_val = output_hidden[i * config_.hidden_size];
            int max_idx = 0;
            for (int j = 1; j < config_.hidden_size; j++) {
                float val = output_hidden[i * config_.hidden_size + j];
                if (val > max_val) {
                    max_val = val;
                    max_idx = j;
                }
            }
            output_tokens[i] = max_idx;
        }
        
        return output_tokens;
    } catch (const std::exception& e) {
        throw std::runtime_error("Error processing tokens: " + std::string(e.what()));
    }
}

void LLMInferenceCore::compute_attention(
    const void* query, const void* key, const void* value,
    void* output, int batch_size, int seq_length) {
    
    // Launch attention kernel
    int block_size = 256;
    int num_blocks = (batch_size * seq_length * config_.num_heads * config_.hidden_size / config_.num_heads + block_size - 1) / block_size;
    
    attention_kernel<<<num_blocks, block_size, 0, stream_>>>(
        static_cast<const float*>(query),
        static_cast<const float*>(key),
        static_cast<const float*>(value),
        static_cast<float*>(output),
        batch_size,
        seq_length,
        config_.num_heads,
        config_.hidden_size / config_.num_heads
    );
}

void LLMInferenceCore::compute_feedforward(
    const void* input, void* output, int batch_size) {
    
    // Launch feedforward kernel
    int block_size = 256;
    int num_blocks = (batch_size * config_.hidden_size + block_size - 1) / block_size;
    
    feedforward_kernel<<<num_blocks, block_size, 0, stream_>>>(
        static_cast<const float*>(input),
        static_cast<float*>(output),
        batch_size,
        config_.hidden_size
    );
}

void LLMInferenceCore::compute_layer_norm(
    const void* input, void* output, int batch_size) {
    
    // Launch layer normalization kernel
    int block_size = 256;
    int num_blocks = (batch_size * config_.hidden_size + block_size - 1) / block_size;
    
    layer_norm_kernel<<<num_blocks, block_size, 0, stream_>>>(
        static_cast<const float*>(input),
        static_cast<float*>(output),
        batch_size,
        config_.hidden_size
    );
}

} // namespace cogniware 