#include "performance_test.h"
#include <torch/cuda.h>
#include <cuda_runtime.h>
#include <spdlog/spdlog.h>
#include <nvml.h>

namespace cogniware {

PerformanceTest::PerformanceTest(std::shared_ptr<ModelOptimizer> optimizer)
    : optimizer_(optimizer), is_profiling_(false) {}

std::map<std::string, float> PerformanceTest::benchmark_inference(int num_runs) {
    std::map<std::string, float> results;
    
    // Create sample input
    auto input = torch::randn({1, 10}).to(torch::kCUDA);
    
    // Warmup
    for (int i = 0; i < 10; ++i) {
        optimizer_->optimize_model();
    }
    
    // Benchmark
    float total_time = 0.0f;
    for (int i = 0; i < num_runs; ++i) {
        total_time += measure_inference_time(input);
    }
    
    results["average_inference_time_ms"] = total_time / num_runs;
    results["throughput_inferences_per_second"] = 1000.0f / (total_time / num_runs);
    
    log_benchmark_results("inference", results);
    return results;
}

std::map<std::string, float> PerformanceTest::benchmark_memory_usage() {
    std::map<std::string, float> results;
    
    size_t free_memory, total_memory;
    cudaMemGetInfo(&free_memory, &total_memory);
    
    results["total_gpu_memory_mb"] = total_memory / (1024.0f * 1024.0f);
    results["free_gpu_memory_mb"] = free_memory / (1024.0f * 1024.0f);
    results["used_gpu_memory_mb"] = (total_memory - free_memory) / (1024.0f * 1024.0f);
    
    log_benchmark_results("memory", results);
    return results;
}

std::map<std::string, float> PerformanceTest::benchmark_optimization_impact() {
    std::map<std::string, float> results;
    
    // Measure baseline performance
    auto baseline = benchmark_inference();
    auto baseline_memory = benchmark_memory_usage();
    
    // Apply optimizations
    optimizer_->optimize_model();
    
    // Measure optimized performance
    auto optimized = benchmark_inference();
    auto optimized_memory = benchmark_memory_usage();
    
    // Calculate improvements
    results["speedup_factor"] = baseline["average_inference_time_ms"] / 
                               optimized["average_inference_time_ms"];
    results["memory_reduction_percent"] = 100.0f * (1.0f - 
        optimized_memory["used_gpu_memory_mb"] / baseline_memory["used_gpu_memory_mb"]);
    
    log_benchmark_results("optimization_impact", results);
    return results;
}

std::map<std::string, float> PerformanceTest::compare_optimization_strategies(
    const std::vector<std::map<std::string, std::string>>& strategies) {
    std::map<std::string, float> results;
    
    for (size_t i = 0; i < strategies.size(); ++i) {
        const auto& strategy = strategies[i];
        optimizer_->initialize_optimization(strategy);
        optimizer_->optimize_model();
        
        auto strategy_results = benchmark_optimization_impact();
        results["strategy_" + std::to_string(i) + "_speedup"] = 
            strategy_results["speedup_factor"];
        results["strategy_" + std::to_string(i) + "_memory_reduction"] = 
            strategy_results["memory_reduction_percent"];
    }
    
    return results;
}

void PerformanceTest::start_detailed_profiling() {
    is_profiling_ = true;
    profiling_start_ = std::chrono::high_resolution_clock::now();
    optimizer_->start_profiling();
}

std::map<std::string, float> PerformanceTest::get_detailed_metrics() {
    if (!is_profiling_) {
        return {};
    }
    
    auto metrics = optimizer_->get_performance_metrics();
    auto current_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(
        current_time - profiling_start_).count();
    
    metrics["profiling_duration_ms"] = static_cast<float>(duration);
    return metrics;
}

void PerformanceTest::stop_detailed_profiling() {
    is_profiling_ = false;
    optimizer_->stop_profiling();
}

float PerformanceTest::measure_inference_time(const torch::Tensor& input) {
    auto start = std::chrono::high_resolution_clock::now();
    optimizer_->optimize_model();
    auto end = std::chrono::high_resolution_clock::now();
    
    return std::chrono::duration_cast<std::chrono::microseconds>(end - start).count() / 1000.0f;
}

float PerformanceTest::measure_memory_usage() {
    size_t free_memory, total_memory;
    cudaMemGetInfo(&free_memory, &total_memory);
    return (total_memory - free_memory) / (1024.0f * 1024.0f);
}

void PerformanceTest::log_benchmark_results(
    const std::string& benchmark_type,
    const std::map<std::string, float>& results) {
    spdlog::info("Benchmark results for {}:", benchmark_type);
    for (const auto& [metric, value] : results) {
        spdlog::info("  {}: {:.2f}", metric, value);
    }
}

std::map<std::string, float> PerformanceTest::benchmark_power_usage() {
    std::map<std::string, float> results;
    
    nvmlInit();
    nvmlDevice_t device;
    nvmlDeviceGetHandleByIndex(0, &device);
    
    unsigned int power;
    nvmlDeviceGetPowerUsage(device, &power);
    
    results["power_usage_watts"] = power / 1000.0f;
    results["power_efficiency"] = measure_compute_efficiency() / (power / 1000.0f);
    
    log_benchmark_results("power", results);
    return results;
}

std::map<std::string, float> PerformanceTest::benchmark_throughput(int batch_size) {
    std::map<std::string, float> results;
    
    // Create batch input
    std::vector<torch::Tensor> inputs;
    for (int i = 0; i < batch_size; ++i) {
        inputs.push_back(torch::randn({1, 10}).to(torch::kCUDA));
    }
    
    // Warmup
    for (int i = 0; i < 5; ++i) {
        for (const auto& input : inputs) {
            optimizer_->optimize_model();
        }
    }
    
    // Measure throughput
    auto start = std::chrono::high_resolution_clock::now();
    int num_batches = 10;
    for (int i = 0; i < num_batches; ++i) {
        for (const auto& input : inputs) {
            optimizer_->optimize_model();
        }
    }
    auto end = std::chrono::high_resolution_clock::now();
    
    float total_time = std::chrono::duration_cast<std::chrono::milliseconds>(
        end - start).count() / 1000.0f;
    
    results["throughput_samples_per_second"] = (num_batches * batch_size) / total_time;
    results["batch_throughput"] = num_batches / total_time;
    
    log_benchmark_results("throughput", results);
    return results;
}

std::map<std::string, float> PerformanceTest::benchmark_latency(int num_runs) {
    std::map<std::string, float> results;
    std::vector<float> latencies;
    
    auto input = torch::randn({1, 10}).to(torch::kCUDA);
    
    // Warmup
    for (int i = 0; i < 10; ++i) {
        optimizer_->optimize_model();
    }
    
    // Measure latencies
    for (int i = 0; i < num_runs; ++i) {
        auto start = std::chrono::high_resolution_clock::now();
        optimizer_->optimize_model();
        auto end = std::chrono::high_resolution_clock::now();
        
        float latency = std::chrono::duration_cast<std::chrono::microseconds>(
            end - start).count() / 1000.0f;
        latencies.push_back(latency);
    }
    
    // Calculate statistics
    float sum = 0.0f;
    float min_latency = latencies[0];
    float max_latency = latencies[0];
    
    for (float latency : latencies) {
        sum += latency;
        min_latency = std::min(min_latency, latency);
        max_latency = std::max(max_latency, latency);
    }
    
    float avg_latency = sum / num_runs;
    
    // Calculate percentiles
    std::sort(latencies.begin(), latencies.end());
    float p50 = latencies[num_runs * 0.5];
    float p90 = latencies[num_runs * 0.9];
    float p99 = latencies[num_runs * 0.99];
    
    results["average_latency_ms"] = avg_latency;
    results["min_latency_ms"] = min_latency;
    results["max_latency_ms"] = max_latency;
    results["p50_latency_ms"] = p50;
    results["p90_latency_ms"] = p90;
    results["p99_latency_ms"] = p99;
    
    log_benchmark_results("latency", results);
    return results;
}

std::map<std::string, float> PerformanceTest::get_gpu_utilization() {
    std::map<std::string, float> results;
    
    nvmlInit();
    nvmlDevice_t device;
    nvmlDeviceGetHandleByIndex(0, &device);
    
    nvmlUtilization_t utilization;
    nvmlDeviceGetUtilizationRates(device, &utilization);
    
    results["gpu_utilization_percent"] = utilization.gpu;
    results["memory_utilization_percent"] = utilization.memory;
    
    return results;
}

std::map<std::string, float> PerformanceTest::get_memory_bandwidth() {
    std::map<std::string, float> results;
    
    nvmlInit();
    nvmlDevice_t device;
    nvmlDeviceGetHandleByIndex(0, &device);
    
    nvmlMemory_t memory;
    nvmlDeviceGetMemoryInfo(device, &memory);
    
    results["total_memory_gb"] = memory.total / (1024.0f * 1024.0f * 1024.0f);
    results["used_memory_gb"] = memory.used / (1024.0f * 1024.0f * 1024.0f);
    results["free_memory_gb"] = memory.free / (1024.0f * 1024.0f * 1024.0f);
    
    return results;
}

std::map<std::string, float> PerformanceTest::get_compute_efficiency() {
    auto performance = benchmark_inference();
    auto utilization = get_gpu_utilization();
    
    return calculate_efficiency_metrics(performance, utilization);
}

std::map<std::string, float> PerformanceTest::get_energy_efficiency() {
    auto performance = benchmark_inference();
    auto power = benchmark_power_usage();
    
    return calculate_efficiency_metrics(performance, power);
}

float PerformanceTest::measure_power_usage() {
    nvmlInit();
    nvmlDevice_t device;
    nvmlDeviceGetHandleByIndex(0, &device);
    
    unsigned int power;
    nvmlDeviceGetPowerUsage(device, &power);
    
    return power / 1000.0f;
}

float PerformanceTest::measure_gpu_utilization() {
    nvmlInit();
    nvmlDevice_t device;
    nvmlDeviceGetHandleByIndex(0, &device);
    
    nvmlUtilization_t utilization;
    nvmlDeviceGetUtilizationRates(device, &utilization);
    
    return utilization.gpu;
}

float PerformanceTest::measure_memory_bandwidth() {
    nvmlInit();
    nvmlDevice_t device;
    nvmlDeviceGetHandleByIndex(0, &device);
    
    nvmlMemory_t memory;
    nvmlDeviceGetMemoryInfo(device, &memory);
    
    return memory.used / (1024.0f * 1024.0f * 1024.0f);
}

std::map<std::string, float> PerformanceTest::calculate_efficiency_metrics(
    const std::map<std::string, float>& performance_metrics,
    const std::map<std::string, float>& resource_metrics) {
    
    std::map<std::string, float> results;
    
    // Calculate compute efficiency
    if (performance_metrics.count("throughput_inferences_per_second") &&
        resource_metrics.count("gpu_utilization_percent")) {
        results["compute_efficiency"] = 
            performance_metrics.at("throughput_inferences_per_second") /
            resource_metrics.at("gpu_utilization_percent");
    }
    
    // Calculate energy efficiency
    if (performance_metrics.count("throughput_inferences_per_second") &&
        resource_metrics.count("power_usage_watts")) {
        results["energy_efficiency"] = 
            performance_metrics.at("throughput_inferences_per_second") /
            resource_metrics.at("power_usage_watts");
    }
    
    return results;
}

} // namespace cogniware 