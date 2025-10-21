# Core LLM Inference Engine Documentation

## Overview

The Core LLM Inference Engine is the foundational component of the CogniWare platform that handles text generation, model management, and inference orchestration. It provides a high-performance, CUDA-accelerated interface for running Large Language Models (LLMs) with support for streaming, batching, and resource management.

## Architecture

### Core Components

1. **LLMInferenceCore**: Main interface and orchestrator
2. **InferenceEngine**: Handles actual inference execution
3. **ModelManager**: Manages model lifecycle and resources
4. **TokenizerFactory**: Creates and manages tokenizers
5. **BPETokenizer**: Byte-Pair Encoding tokenizer implementation

### Key Features

- **CUDA Acceleration**: GPU-accelerated inference with memory management
- **Streaming Support**: Real-time token streaming for responsive user experience
- **Model Management**: Dynamic loading/unloading of models with resource tracking
- **Tokenizer Support**: BPE tokenization with configurable special tokens
- **Error Handling**: Comprehensive error reporting and recovery
- **Statistics**: Performance metrics and resource monitoring

## API Reference

### LLMInferenceCore

The main interface for the inference engine.

#### Initialization

```cpp
auto& engine = LLMInferenceCore::getInstance();
bool success = engine.initialize();
```

#### Model Management

```cpp
// Load a model
ModelConfig config;
config.modelId = "gpt-2";
config.modelPath = "/path/to/model.bin";
config.modelType = "gpt";
config.maxBatchSize = 8;
config.maxSequenceLength = 1024;
config.useHalfPrecision = true;
config.useQuantization = false;
config.supportedTasks = {"text-generation"};

bool loaded = engine.loadModel(config);

// Check if model is loaded
bool isLoaded = engine.isModelLoaded("gpt-2");

// Unload a model
bool unloaded = engine.unloadModel("gpt-2");
```

#### Inference

```cpp
// Standard inference
InferenceRequest request;
request.modelId = "gpt-2";
request.prompt = "Hello, how are you?";
request.maxTokens = 100;
request.temperature = 0.7f;
request.topP = 0.9f;
request.numBeams = 4;
request.streamOutput = false;

InferenceResponse response = engine.processRequest(request);
if (response.success) {
    std::cout << "Generated: " << response.generatedText << std::endl;
    std::cout << "Tokens: " << response.numTokens << std::endl;
    std::cout << "Latency: " << response.latency << " seconds" << std::endl;
}
```

#### Streaming Inference

```cpp
// Streaming inference
InferenceRequest streamRequest;
streamRequest.modelId = "gpt-2";
streamRequest.prompt = "Tell me a story about";
streamRequest.maxTokens = 200;
streamRequest.temperature = 0.8f;
streamRequest.topP = 0.9f;
streamRequest.numBeams = 1;
streamRequest.streamOutput = true;

bool streamSuccess = engine.streamResponse(streamRequest, 
    [](const std::string& token) {
        std::cout << token << std::flush;
    });
```

#### Statistics and Monitoring

```cpp
// Get GPU statistics
GPUStats gpuStats = engine.getGPUStats();
std::cout << "GPU Utilization: " << gpuStats.utilization << "%" << std::endl;
std::cout << "Memory Usage: " << gpuStats.usedMemory << " / " 
          << gpuStats.totalMemory << " bytes" << std::endl;

// Get model statistics
ModelStats modelStats = engine.getModelStats("gpt-2");
std::cout << "Total Inferences: " << modelStats.totalInferences << std::endl;
std::cout << "Average Latency: " << modelStats.averageLatency << " seconds" << std::endl;
```

### Data Structures

#### ModelConfig

```cpp
struct ModelConfig {
    std::string modelId;           // Unique model identifier
    std::string modelPath;         // Path to model file
    std::string modelType;         // Model type (gpt, bert, etc.)
    size_t maxBatchSize;          // Maximum batch size
    size_t maxSequenceLength;     // Maximum sequence length
    bool useHalfPrecision;        // Use FP16 precision
    bool useQuantization;         // Use model quantization
    std::vector<std::string> supportedTasks; // Supported tasks
};
```

#### InferenceRequest

```cpp
struct InferenceRequest {
    std::string modelId;          // Model to use for inference
    std::string prompt;           // Input text prompt
    size_t maxTokens;            // Maximum tokens to generate
    float temperature;           // Sampling temperature (0.0-2.0)
    float topP;                 // Top-p sampling (0.0-1.0)
    size_t numBeams;            // Number of beams for beam search
    bool streamOutput;          // Enable streaming output
};
```

#### InferenceResponse

```cpp
struct InferenceResponse {
    std::string generatedText;   // Generated text output
    size_t numTokens;           // Number of tokens generated
    float latency;              // Inference latency in seconds
    bool success;               // Whether inference succeeded
    std::string error;          // Error message if failed
};
```

#### GPUStats

```cpp
struct GPUStats {
    float utilization;          // GPU utilization percentage
    size_t usedMemory;          // Used GPU memory in bytes
    size_t totalMemory;         // Total GPU memory in bytes
    float temperature;          // GPU temperature in Celsius
    float powerUsage;           // Power usage in watts
};
```

#### ModelStats

```cpp
struct ModelStats {
    size_t totalInferences;     // Total number of inferences
    size_t totalTokens;         // Total tokens generated
    float averageLatency;       // Average inference latency
    size_t peakMemoryUsage;     // Peak memory usage
    size_t currentMemoryUsage;  // Current memory usage
};
```

## Tokenizer System

### BPETokenizer

The BPE (Byte-Pair Encoding) tokenizer handles text tokenization and detokenization.

#### Configuration

```cpp
auto config = std::make_shared<TokenizerConfig>();
config->model_path = "/path/to/tokenizer";
config->model_type = "bpe";
config->vocabulary_size = 50000;
config->max_sequence_length = 2048;
config->use_bos_token = true;
config->use_eos_token = true;
config->use_pad_token = true;
config->use_unk_token = true;
config->bos_token = "<s>";
config->eos_token = "</s>";
config->pad_token = "<pad>";
config->unk_token = "<unk>";
```

#### Usage

```cpp
auto tokenizer = std::make_shared<BPETokenizer>(config);

// Encode text to tokens
std::vector<int> tokens = tokenizer->encode("Hello, world!");

// Decode tokens to text
std::string text = tokenizer->decode(tokens);

// Get vocabulary information
size_t vocabSize = tokenizer->getVocabularySize();
std::string token = tokenizer->getToken(123);
int tokenId = tokenizer->getTokenId("hello");
```

## Error Handling

The inference engine provides comprehensive error handling with detailed error messages.

### Common Error Scenarios

1. **Model Not Found**: When trying to use a model that hasn't been loaded
2. **Insufficient Resources**: When there's not enough GPU memory
3. **Invalid Configuration**: When model configuration is invalid
4. **CUDA Errors**: When GPU operations fail
5. **Tokenizer Errors**: When tokenization fails

### Error Recovery

```cpp
// Check for errors
if (!response.success) {
    std::cerr << "Inference failed: " << response.error << std::endl;
    
    // Clear error and retry
    engine.clearLastError();
    // ... retry logic
}

// Get last error
const char* error = engine.getLastError();
if (error && strlen(error) > 0) {
    std::cerr << "Last error: " << error << std::endl;
}
```

## Performance Optimization

### Memory Management

- Automatic GPU memory allocation and deallocation
- Memory pooling for efficient resource usage
- Model memory estimation and tracking

### CUDA Optimization

- GPU stream management for parallel execution
- Mixed precision support (FP16) for faster inference
- Tensor core utilization when available

### Batch Processing

- Dynamic batching for improved throughput
- Batch size optimization based on available memory
- Parallel processing of multiple requests

## Thread Safety

The inference engine is fully thread-safe and supports concurrent access:

- All public methods are protected by mutexes
- Safe for use in multi-threaded applications
- Concurrent model loading and inference support

## Resource Monitoring

### GPU Monitoring

- Real-time GPU utilization tracking
- Memory usage monitoring
- Temperature and power monitoring
- Automatic resource alerts

### Model Statistics

- Per-model performance metrics
- Inference latency tracking
- Token generation statistics
- Memory usage per model

## Configuration

### System Requirements

- CUDA-capable GPU (recommended)
- Minimum 8GB GPU memory
- C++17 compatible compiler
- CUDA Toolkit 11.0 or later

### Build Configuration

```cmake
# Enable CUDA support
find_package(CUDA REQUIRED)
enable_language(CUDA)

# Link CUDA libraries
target_link_libraries(your_target
    ${CUDA_LIBRARIES}
    ${CUDA_CUBLAS_LIBRARIES}
    ${CUDA_CUDNN_LIBRARIES}
)
```

## Testing

### Unit Tests

Run the comprehensive test suite:

```bash
cd build
make test_core_inference_engine
./tests/test_core_inference_engine
```

### Performance Benchmarks

```cpp
// Benchmark inference latency
auto start = std::chrono::high_resolution_clock::now();
auto response = engine.processRequest(request);
auto end = std::chrono::high_resolution_clock::now();

auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
std::cout << "Inference latency: " << duration.count() << " ms" << std::endl;
```

## Troubleshooting

### Common Issues

1. **CUDA Initialization Failed**
   - Check CUDA installation
   - Verify GPU drivers
   - Ensure CUDA_HOME is set correctly

2. **Model Loading Failed**
   - Verify model file exists
   - Check file permissions
   - Ensure sufficient GPU memory

3. **Tokenizer Errors**
   - Verify tokenizer files exist
   - Check vocabulary file format
   - Ensure proper encoding

### Debug Mode

Enable debug logging:

```cpp
// Set log level to debug
spdlog::set_level(spdlog::level::debug);
```

## Future Enhancements

- Support for additional tokenizer types (SentencePiece, WordPiece)
- Advanced sampling strategies (nucleus sampling, top-k sampling)
- Model quantization and optimization
- Distributed inference support
- Advanced caching mechanisms
- Multi-GPU support

## Contributing

When contributing to the core inference engine:

1. Follow the existing code style and patterns
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure thread safety for all new code
5. Add proper error handling and logging

## License

This component is part of the CogniWare platform and is licensed under the MIT License.
