#include <gtest/gtest.h>
#include "optimization/performance_test.h"
#include <torch/torch.h>

namespace cognidream {
namespace test {

class PerformanceTestTest : public ::testing::Test {
protected:
    void SetUp() override {
        perf_test = &PerformanceTest::getInstance();
        
        // Configure test parameters
        nlohmann::json params = {
            {"num_runs", 10},
            {"batch_size", 1}
        };
        perf_test->setTestParameters(params);
    }

    PerformanceTest* perf_test;
};

TEST_F(PerformanceTestTest, ConfigureTest) {
    nlohmann::json config = {
        {"num_runs", 10},
        {"batch_size", 1}
    };
    EXPECT_TRUE(perf_test->configureTest("test_model", config));
}

TEST_F(PerformanceTestTest, RunInferenceTest) {
    auto result = perf_test->runInferenceTest("test_model");
    EXPECT_GE(result.inference_time, 0.0);
    EXPECT_GE(result.throughput, 0.0);
    EXPECT_GE(result.latency, 0.0);
}

TEST_F(PerformanceTestTest, RunLoadTest) {
    auto result = perf_test->runLoadTest("test_model", 10);
    EXPECT_GE(result.inference_time, 0.0);
    EXPECT_GE(result.throughput, 0.0);
    EXPECT_GE(result.latency, 0.0);
}

TEST_F(PerformanceTestTest, RunStressTest) {
    auto result = perf_test->runStressTest("test_model", 5);
    EXPECT_GE(result.inference_time, 0.0);
    EXPECT_GE(result.throughput, 0.0);
    EXPECT_GE(result.latency, 0.0);
}

TEST_F(PerformanceTestTest, RunMemoryTest) {
    auto result = perf_test->runMemoryTest("test_model");
    EXPECT_GE(result.memory_usage, 0.0);
    EXPECT_FALSE(result.gpu_utilization.empty());
    EXPECT_FALSE(result.memory_utilization.empty());
}

TEST_F(PerformanceTestTest, AnalyzeResults) {
    auto result = perf_test->runInferenceTest("test_model");
    auto analysis = perf_test->analyzeResults(result);
    EXPECT_TRUE(analysis.contains("latency"));
    EXPECT_TRUE(analysis.contains("resources"));
    EXPECT_TRUE(analysis.contains("metrics"));
}

TEST_F(PerformanceTestTest, CompareResults) {
    auto baseline = perf_test->runInferenceTest("test_model");
    auto optimized = perf_test->runInferenceTest("test_model");
    auto comparison = perf_test->compareResults(baseline, optimized);
    EXPECT_TRUE(comparison.contains("latency"));
    EXPECT_TRUE(comparison.contains("throughput"));
    EXPECT_TRUE(comparison.contains("resources"));
}

TEST_F(PerformanceTestTest, GetTestRecommendations) {
    auto result = perf_test->runInferenceTest("test_model");
    auto recommendations = perf_test->getTestRecommendations(result);
    EXPECT_FALSE(recommendations.empty());
}

TEST_F(PerformanceTestTest, GenerateReport) {
    auto report = perf_test->generateReport("test_model");
    EXPECT_TRUE(report.contains("model_id"));
    EXPECT_TRUE(report.contains("test_config"));
    EXPECT_TRUE(report.contains("results"));
}

TEST_F(PerformanceTestTest, ExportResults) {
    EXPECT_TRUE(perf_test->exportResults("test_model", "test_results.json"));
}

} // namespace test
} // namespace cognidream 