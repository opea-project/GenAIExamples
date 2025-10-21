#include <gtest/gtest.h>
#include <torch/script.h>
#include <torch/torch.h>
#include <memory>
#include "optimization/model_optimizer.h"
#include "optimization/performance_test.h"

namespace cogniware {
namespace {

class PerformanceTestTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Create a dummy model
        auto model = torch::jit::script(torch::nn::Linear(10, 10));
        model_path_ = "dummy_model.pt";
        torch::jit::save(model, model_path_);
        
        // Initialize optimizer and performance test
        optimizer_ = std::make_shared<ModelOptimizer>();
        optimizer_->load_model(model_path_, "dummy");
        performance_test_ = std::make_unique<PerformanceTest>(optimizer_);
    }
    
    void TearDown() override {
        std::remove(model_path_.c_str());
    }
    
    std::string model_path_;
    std::shared_ptr<ModelOptimizer> optimizer_;
    std::unique_ptr<PerformanceTest> performance_test_;
};

TEST_F(PerformanceTestTest, BenchmarkInference) {
    auto results = performance_test_->benchmark_inference(10);
    EXPECT_GT(results["average_inference_time_ms"], 0.0f);
    EXPECT_GT(results["throughput_inferences_per_second"], 0.0f);
}

TEST_F(PerformanceTestTest, BenchmarkMemoryUsage) {
    auto results = performance_test_->benchmark_memory_usage();
    EXPECT_GT(results["total_gpu_memory_mb"], 0.0f);
    EXPECT_GE(results["total_gpu_memory_mb"], results["used_gpu_memory_mb"]);
}

TEST_F(PerformanceTestTest, BenchmarkOptimizationImpact) {
    auto results = performance_test_->benchmark_optimization_impact();
    EXPECT_GT(results["speedup_factor"], 0.0f);
    EXPECT_GE(results["memory_reduction_percent"], 0.0f);
}

TEST_F(PerformanceTestTest, CompareOptimizationStrategies) {
    std::vector<std::map<std::string, std::string>> strategies = {
        {{"quantization", "8bit"}},
        {{"pruning", "structured"}, {"target_sparsity", "0.5"}},
        {{"distillation", "enabled"}}
    };
    
    auto results = performance_test_->compare_optimization_strategies(strategies);
    EXPECT_GT(results["strategy_0_speedup"], 0.0f);
    EXPECT_GT(results["strategy_1_speedup"], 0.0f);
    EXPECT_GT(results["strategy_2_speedup"], 0.0f);
}

TEST_F(PerformanceTestTest, DetailedProfiling) {
    performance_test_->start_detailed_profiling();
    auto metrics = performance_test_->get_detailed_metrics();
    EXPECT_GT(metrics["profiling_duration_ms"], 0.0f);
    performance_test_->stop_detailed_profiling();
}

TEST_F(PerformanceTestTest, BenchmarkPowerUsage) {
    auto results = performance_test_->benchmark_power_usage();
    EXPECT_GT(results["power_usage_watts"], 0.0f);
    EXPECT_GT(results["power_efficiency"], 0.0f);
}

TEST_F(PerformanceTestTest, BenchmarkThroughput) {
    auto results = performance_test_->benchmark_throughput(4);
    EXPECT_GT(results["throughput_samples_per_second"], 0.0f);
    EXPECT_GT(results["batch_throughput"], 0.0f);
}

TEST_F(PerformanceTestTest, BenchmarkLatency) {
    auto results = performance_test_->benchmark_latency(100);
    EXPECT_GT(results["average_latency_ms"], 0.0f);
    EXPECT_GT(results["min_latency_ms"], 0.0f);
    EXPECT_GT(results["max_latency_ms"], 0.0f);
    EXPECT_GT(results["p50_latency_ms"], 0.0f);
    EXPECT_GT(results["p90_latency_ms"], 0.0f);
    EXPECT_GT(results["p99_latency_ms"], 0.0f);
    
    // Verify latency statistics
    EXPECT_LE(results["min_latency_ms"], results["average_latency_ms"]);
    EXPECT_GE(results["max_latency_ms"], results["average_latency_ms"]);
    EXPECT_LE(results["p50_latency_ms"], results["p90_latency_ms"]);
    EXPECT_LE(results["p90_latency_ms"], results["p99_latency_ms"]);
}

TEST_F(PerformanceTestTest, GPUUtilization) {
    auto results = performance_test_->get_gpu_utilization();
    EXPECT_GE(results["gpu_utilization_percent"], 0.0f);
    EXPECT_LE(results["gpu_utilization_percent"], 100.0f);
    EXPECT_GE(results["memory_utilization_percent"], 0.0f);
    EXPECT_LE(results["memory_utilization_percent"], 100.0f);
}

TEST_F(PerformanceTestTest, MemoryBandwidth) {
    auto results = performance_test_->get_memory_bandwidth();
    EXPECT_GT(results["total_memory_gb"], 0.0f);
    EXPECT_GE(results["total_memory_gb"], results["used_memory_gb"]);
    EXPECT_GE(results["total_memory_gb"], results["free_memory_gb"]);
    EXPECT_FLOAT_EQ(results["total_memory_gb"], 
                    results["used_memory_gb"] + results["free_memory_gb"]);
}

TEST_F(PerformanceTestTest, ComputeEfficiency) {
    auto results = performance_test_->get_compute_efficiency();
    EXPECT_GT(results["compute_efficiency"], 0.0f);
}

TEST_F(PerformanceTestTest, EnergyEfficiency) {
    auto results = performance_test_->get_energy_efficiency();
    EXPECT_GT(results["energy_efficiency"], 0.0f);
}

TEST_F(PerformanceTestTest, ComprehensiveBenchmark) {
    // Run all benchmarks and verify they don't crash
    auto inference_results = performance_test_->benchmark_inference();
    auto memory_results = performance_test_->benchmark_memory_usage();
    auto power_results = performance_test_->benchmark_power_usage();
    auto throughput_results = performance_test_->benchmark_throughput(4);
    auto latency_results = performance_test_->benchmark_latency(100);
    
    // Verify all results are non-empty
    EXPECT_FALSE(inference_results.empty());
    EXPECT_FALSE(memory_results.empty());
    EXPECT_FALSE(power_results.empty());
    EXPECT_FALSE(throughput_results.empty());
    EXPECT_FALSE(latency_results.empty());
}

TEST_F(PerformanceTestTest, OptimizationImpactWithMetrics) {
    // Run optimization impact benchmark with all metrics
    auto results = performance_test_->benchmark_optimization_impact();
    
    // Verify speedup and memory reduction
    EXPECT_GT(results["speedup_factor"], 0.0f);
    EXPECT_GE(results["memory_reduction_percent"], 0.0f);
    
    // Get additional metrics
    auto gpu_util = performance_test_->get_gpu_utilization();
    auto memory_bw = performance_test_->get_memory_bandwidth();
    auto compute_eff = performance_test_->get_compute_efficiency();
    auto energy_eff = performance_test_->get_energy_efficiency();
    
    // Verify all metrics are present
    EXPECT_FALSE(gpu_util.empty());
    EXPECT_FALSE(memory_bw.empty());
    EXPECT_FALSE(compute_eff.empty());
    EXPECT_FALSE(energy_eff.empty());
}

} // namespace
} // namespace cogniware 