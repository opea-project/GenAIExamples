# MSmartCompute Optimization and Performance Testing Guide

This guide demonstrates how to use MSmartCompute's optimization and performance testing features to optimize and benchmark your models.

## Basic Usage

### Loading and Optimizing a Model

```cpp
#include "inference/inference_manager.h"

// Create an inference manager
cogniware::InferenceManager manager;

// Load a model
manager.load_model("path/to/model.pt", "model_type");

// Configure optimization settings
std::map<std::string, std::string> config = {
    {"quantization", "8bit"},
    {"pruning", "structured"},
    {"target_sparsity", "0.3"}
};

// Optimize the model
manager.optimize_model(config);
```

### Running Inference

```cpp
// Create input tensor
auto input = torch::randn({1, 10}).to(torch::kCUDA);

// Run inference
auto output = manager.run_inference(input);

// Run batch inference
std::vector<torch::Tensor> inputs;
for (int i = 0; i < 3; ++i) {
    inputs.push_back(torch::randn({1, 10}).to(torch::kCUDA));
}
auto outputs = manager.run_batch_inference(inputs);
```

## Performance Testing

### Basic Benchmarking

```cpp
#include "optimization/performance_test.h"

// Create a performance test instance
auto optimizer = std::make_shared<cogniware::ModelOptimizer>();
auto performance_test = std::make_unique<cogniware::PerformanceTest>(optimizer);

// Run basic benchmarks
auto inference_results = performance_test->benchmark_inference();
auto memory_results = performance_test->benchmark_memory_usage();
auto power_results = performance_test->benchmark_power_usage();
```

### Advanced Metrics

```cpp
// Get detailed performance metrics
auto gpu_util = performance_test->get_gpu_utilization();
auto memory_bw = performance_test->get_memory_bandwidth();
auto compute_eff = performance_test->get_compute_efficiency();
auto energy_eff = performance_test->get_energy_efficiency();

// Benchmark throughput with different batch sizes
auto throughput_results = performance_test->benchmark_throughput(4);

// Measure latency with percentiles
auto latency_results = performance_test->benchmark_latency(100);
```

### Comparing Optimization Strategies

```cpp
// Define different optimization strategies
std::vector<std::map<std::string, std::string>> strategies = {
    {{"quantization", "8bit"}},
    {{"quantization", "4bit"}},
    {{"pruning", "structured"}, {"target_sparsity", "0.3"}},
    {{"pruning", "unstructured"}, {"threshold", "0.1"}},
    {{"distillation", "enabled"}}
};

// Compare strategies
auto results = performance_test->compare_optimization_strategies(strategies);
```

## Performance Monitoring

### Real-time Monitoring

```cpp
// Start monitoring
manager.start_monitoring();

// Run some inference
for (int i = 0; i < 100; ++i) {
    auto input = torch::randn({1, 10}).to(torch::kCUDA);
    manager.run_inference(input);
}

// Get performance metrics
auto metrics = manager.get_performance_metrics();

// Stop monitoring
manager.stop_monitoring();
```

### Auto-optimization

```cpp
// Enable auto-optimization
manager.enable_auto_optimization();

// Set batch size and precision
manager.set_batch_size(4);
manager.set_precision("fp16");
```

## Performance Metrics

The following metrics are available:

### Inference Metrics
- `average_inference_time_ms`: Average time per inference
- `throughput_inferences_per_second`: Number of inferences per second
- `min_latency_ms`: Minimum inference latency
- `max_latency_ms`: Maximum inference latency
- `p50_latency_ms`: 50th percentile latency
- `p90_latency_ms`: 90th percentile latency
- `p99_latency_ms`: 99th percentile latency

### Memory Metrics
- `total_gpu_memory_mb`: Total GPU memory
- `free_gpu_memory_mb`: Free GPU memory
- `used_gpu_memory_mb`: Used GPU memory
- `memory_bandwidth_gb`: Memory bandwidth usage

### Power Metrics
- `power_usage_watts`: Current power usage
- `power_efficiency`: Inferences per watt
- `energy_efficiency`: Energy efficiency score

### GPU Metrics
- `gpu_utilization_percent`: GPU utilization
- `memory_utilization_percent`: Memory utilization
- `compute_efficiency`: Compute efficiency score

## Best Practices

1. **Warmup**: Always run a few warmup iterations before benchmarking
2. **Batch Size**: Experiment with different batch sizes to find optimal throughput
3. **Precision**: Try different precision modes (fp32, fp16, int8) for your use case
4. **Monitoring**: Use performance monitoring to identify bottlenecks
5. **Auto-optimization**: Let the system find the best optimization strategy
6. **Memory Management**: Monitor memory usage and adjust batch sizes accordingly

## Troubleshooting

### Common Issues

1. **High Latency**
   - Check GPU utilization
   - Try different batch sizes
   - Consider using a lower precision

2. **Memory Issues**
   - Reduce batch size
   - Enable memory optimization
   - Check for memory leaks

3. **Low Throughput**
   - Enable auto-optimization
   - Try different optimization strategies
   - Check GPU utilization

### Performance Tuning

1. Start with default settings
2. Monitor performance metrics
3. Enable auto-optimization
4. Fine-tune based on specific requirements
5. Compare different strategies
6. Document successful configurations

## Example Configurations

### High Throughput Configuration
```cpp
std::map<std::string, std::string> config = {
    {"quantization", "8bit"},
    {"batch_size", "32"},
    {"precision", "fp16"}
};
```

### Low Latency Configuration
```cpp
std::map<std::string, std::string> config = {
    {"quantization", "4bit"},
    {"batch_size", "1"},
    {"precision", "fp32"}
};
```

### Memory Efficient Configuration
```cpp
std::map<std::string, std::string> config = {
    {"pruning", "structured"},
    {"target_sparsity", "0.5"},
    {"enable_memory_optimization", "true"}
};
``` 