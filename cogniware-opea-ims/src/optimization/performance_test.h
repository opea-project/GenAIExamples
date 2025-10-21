#pragma once

#include <string>
#include <vector>
#include <map>
#include <chrono>
#include <torch/torch.h>
#include "model_optimizer.h"

namespace cogniware {

class PerformanceTest {
public:
    PerformanceTest(std::shared_ptr<ModelOptimizer> optimizer);
    
    // Benchmark methods
    std::map<std::string, float> benchmark_inference(int num_runs = 100);
    std::map<std::string, float> benchmark_memory_usage();
    std::map<std::string, float> benchmark_optimization_impact();
    std::map<std::string, float> benchmark_power_usage();
    std::map<std::string, float> benchmark_throughput(int batch_size = 1);
    std::map<std::string, float> benchmark_latency(int num_runs = 100);
    
    // Comparison methods
    std::map<std::string, float> compare_optimization_strategies(
        const std::vector<std::map<std::string, std::string>>& strategies);
    
    // Detailed profiling
    void start_detailed_profiling();
    std::map<std::string, float> get_detailed_metrics();
    void stop_detailed_profiling();
    
    // Advanced metrics
    std::map<std::string, float> get_gpu_utilization();
    std::map<std::string, float> get_memory_bandwidth();
    std::map<std::string, float> get_compute_efficiency();
    std::map<std::string, float> get_energy_efficiency();

private:
    std::shared_ptr<ModelOptimizer> optimizer_;
    bool is_profiling_;
    std::chrono::time_point<std::chrono::high_resolution_clock> profiling_start_;
    
    // Helper methods
    float measure_inference_time(const torch::Tensor& input);
    float measure_memory_usage();
    float measure_power_usage();
    float measure_gpu_utilization();
    float measure_memory_bandwidth();
    void log_benchmark_results(const std::string& benchmark_type, 
                             const std::map<std::string, float>& results);
    std::map<std::string, float> calculate_efficiency_metrics(
        const std::map<std::string, float>& performance_metrics,
        const std::map<std::string, float>& resource_metrics);
};

} // namespace cogniware 