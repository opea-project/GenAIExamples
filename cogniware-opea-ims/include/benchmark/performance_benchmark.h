#pragma once

#include <string>
#include <vector>
#include <memory>
#include <unordered_map>
#include <chrono>
#include <functional>

namespace cogniware {
namespace benchmark {

/**
 * @brief Benchmark categories
 */
enum class BenchmarkCategory {
    INFERENCE,
    MODEL_LOADING,
    BATCH_PROCESSING,
    MULTI_LLM,
    MEMORY_OPS,
    CONTEXT_SWITCHING,
    STREAMING,
    OVERALL
};

/**
 * @brief Benchmark result
 */
struct BenchmarkResult {
    std::string name;
    BenchmarkCategory category;
    
    // Timing
    std::chrono::nanoseconds duration;
    std::chrono::nanoseconds min_duration;
    std::chrono::nanoseconds max_duration;
    std::chrono::nanoseconds avg_duration;
    std::chrono::nanoseconds std_deviation;
    
    // Throughput
    double tokens_per_second;
    double requests_per_second;
    double bandwidth_mbps;
    
    // Resource usage
    double peak_memory_mb;
    double avg_memory_mb;
    double peak_cpu_percent;
    double avg_cpu_percent;
    double peak_gpu_percent;
    double avg_gpu_percent;
    
    // Iterations
    size_t iterations;
    size_t successful;
    size_t failed;
    
    // Comparison
    double baseline_duration_ms;
    double speedup_factor;
    
    // Metadata
    std::unordered_map<std::string, std::string> metadata;
    std::chrono::system_clock::time_point timestamp;
};

/**
 * @brief Benchmark configuration
 */
struct BenchmarkConfig {
    std::string name;
    BenchmarkCategory category;
    size_t iterations = 100;
    size_t warmup_iterations = 10;
    bool collect_detailed_stats = true;
    bool compare_to_baseline = true;
    std::string baseline_name = "traditional";
    
    // Test parameters
    size_t batch_size = 1;
    size_t sequence_length = 512;
    size_t max_tokens = 100;
    std::vector<std::string> model_ids;
};

/**
 * @brief Benchmark suite
 */
struct BenchmarkSuite {
    std::string name;
    std::string description;
    std::vector<BenchmarkConfig> benchmarks;
    std::chrono::system_clock::time_point start_time;
    std::chrono::system_clock::time_point end_time;
    std::vector<BenchmarkResult> results;
};

/**
 * @brief Performance Benchmark System
 */
class PerformanceBenchmark {
public:
    PerformanceBenchmark();
    ~PerformanceBenchmark();

    // Suite management
    void addBenchmark(const BenchmarkConfig& config);
    void removeBenchmark(const std::string& name);
    std::vector<std::string> listBenchmarks() const;
    
    // Execution
    BenchmarkResult runBenchmark(const std::string& name);
    BenchmarkSuite runSuite(const std::string& suite_name = "default");
    BenchmarkSuite runAll();
    
    // Predefined benchmarks
    BenchmarkResult benchmarkSingleInference();
    BenchmarkResult benchmarkBatchInference();
    BenchmarkResult benchmarkModelLoading();
    BenchmarkResult benchmarkMultiLLM();
    BenchmarkResult benchmarkContextSwitching();
    BenchmarkResult benchmarkStreamingInference();
    BenchmarkResult benchmarkMemoryOperations();
    BenchmarkResult benchmarkThroughput();
    
    // Comparison
    BenchmarkResult compareWithBaseline(const BenchmarkConfig& config);
    double calculateSpeedup(double cogniware_time_ms, double baseline_time_ms);
    
    // Reporting
    std::string generateReport(const BenchmarkSuite& suite);
    std::string generateSummary(const BenchmarkSuite& suite);
    std::string generateDetailedReport(const BenchmarkResult& result);
    bool exportResults(const BenchmarkSuite& suite, const std::string& filepath);
    
    // Validation
    bool validate15xImprovement(const BenchmarkSuite& suite);
    std::vector<std::string> getFailedBenchmarks(const BenchmarkSuite& suite);

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

/**
 * @brief Benchmark utilities
 */
class BenchmarkUtils {
public:
    // Timing
    static std::chrono::nanoseconds measureDuration(std::function<void()> func);
    static std::vector<std::chrono::nanoseconds> measureMultiple(
        std::function<void()> func, size_t iterations);
    
    // Statistics
    static double calculateMean(const std::vector<double>& values);
    static double calculateStdDev(const std::vector<double>& values);
    static double calculateMedian(std::vector<double> values);
    static double calculatePercentile(std::vector<double> values, double percentile);
    
    // Formatting
    static std::string formatDuration(std::chrono::nanoseconds duration);
    static std::string formatThroughput(double tokens_per_second);
    static std::string formatSpeedup(double factor);
    static std::string formatMemory(double megabytes);
    
    // Warmup
    static void warmupCPU();
    static void warmupGPU();
    static void clearCaches();
};

/**
 * @brief Standard benchmark suite
 */
class StandardBenchmarkSuite {
public:
    // Create standard suite for 15x validation
    static BenchmarkSuite createValidationSuite();
    
    // Individual benchmark configs
    static BenchmarkConfig createSingleInferenceBenchmark();
    static BenchmarkConfig createBatchInferenceBenchmark();
    static BenchmarkConfig createModelLoadingBenchmark();
    static BenchmarkConfig createMultiLLMBenchmark();
    static BenchmarkConfig createContextSwitchingBenchmark();
    static BenchmarkConfig createStreamingBenchmark();
    static BenchmarkConfig createThroughputBenchmark();
};

/**
 * @brief Continuous benchmarking
 */
class ContinuousBenchmark {
public:
    ContinuousBenchmark();
    ~ContinuousBenchmark();

    // Control
    void start();
    void stop();
    bool isRunning() const;
    void setInterval(std::chrono::seconds interval);
    
    // Configuration
    void addBenchmark(const BenchmarkConfig& config);
    void setBenchmarkSuite(const BenchmarkSuite& suite);
    
    // Results
    std::vector<BenchmarkResult> getResults() const;
    BenchmarkResult getLatestResult() const;
    
    // Callbacks
    using ResultCallback = std::function<void(const BenchmarkResult&)>;
    void setResultCallback(ResultCallback callback);
    
    using AlertCallback = std::function<void(const std::string&, double)>;
    void setPerformanceAlert(double threshold_speedup, AlertCallback callback);

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

/**
 * @brief Benchmark reporter
 */
class BenchmarkReporter {
public:
    // Report formats
    enum class Format {
        TEXT,
        JSON,
        CSV,
        HTML,
        MARKDOWN
    };
    
    // Generate reports
    static std::string generateReport(const BenchmarkSuite& suite, Format format);
    static std::string generateSummaryTable(const BenchmarkSuite& suite);
    static std::string generateSpeedupChart(const BenchmarkSuite& suite);
    static std::string generateComparisonTable(
        const BenchmarkSuite& cogniware,
        const BenchmarkSuite& baseline);
    
    // Export
    static bool exportToFile(const BenchmarkSuite& suite, 
                            const std::string& filepath,
                            Format format);
    
    // Visualization data
    static std::string generateChartData(const BenchmarkSuite& suite);
};

} // namespace benchmark
} // namespace cogniware

