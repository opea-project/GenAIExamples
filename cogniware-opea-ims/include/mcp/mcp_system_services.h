#pragma once

#include "mcp_core.h"
#include <string>
#include <vector>
#include <memory>
#include <unordered_map>
#include <chrono>
#include <functional>

namespace cogniware {
namespace mcp {
namespace system_services {

// Forward declarations
class SystemLogger;
class SystemMonitor;
class ResourceTracker;
class ServiceRegistry;

/**
 * @brief Log levels
 */
enum class LogLevel {
    TRACE,
    DEBUG,
    INFO,
    WARNING,
    ERROR,
    CRITICAL
};

/**
 * @brief Log entry
 */
struct LogEntry {
    std::chrono::system_clock::time_point timestamp;
    LogLevel level;
    std::string component;
    std::string message;
    std::unordered_map<std::string, std::string> metadata;
};

/**
 * @brief System metrics
 */
struct SystemMetrics {
    // CPU metrics
    double cpu_usage_percent;
    double cpu_temperature;
    uint32_t cpu_frequency_mhz;
    uint32_t num_cores;
    uint32_t num_threads;
    
    // Memory metrics
    uint64_t total_memory_bytes;
    uint64_t used_memory_bytes;
    uint64_t free_memory_bytes;
    uint64_t cached_memory_bytes;
    uint64_t swap_total_bytes;
    uint64_t swap_used_bytes;
    
    // Disk metrics
    uint64_t total_disk_bytes;
    uint64_t used_disk_bytes;
    uint64_t free_disk_bytes;
    uint64_t disk_read_bytes_per_sec;
    uint64_t disk_write_bytes_per_sec;
    
    // Network metrics
    uint64_t network_rx_bytes_per_sec;
    uint64_t network_tx_bytes_per_sec;
    uint64_t network_rx_packets_per_sec;
    uint64_t network_tx_packets_per_sec;
    uint64_t network_errors;
    
    // GPU metrics
    struct GPUMetrics {
        uint32_t index;
        std::string name;
        double utilization_percent;
        double memory_used_mb;
        double memory_total_mb;
        double temperature;
        uint32_t power_usage_watts;
        uint32_t fan_speed_percent;
    };
    std::vector<GPUMetrics> gpus;
    
    // System info
    std::chrono::system_clock::time_point boot_time;
    std::chrono::seconds uptime;
    uint32_t num_processes;
    double load_average_1min;
    double load_average_5min;
    double load_average_15min;
};

/**
 * @brief System event types
 */
enum class SystemEventType {
    PROCESS_START,
    PROCESS_STOP,
    PROCESS_CRASH,
    SERVICE_START,
    SERVICE_STOP,
    SERVICE_RESTART,
    RESOURCE_LIMIT,
    HARDWARE_ERROR,
    NETWORK_CHANGE,
    DISK_SPACE_LOW,
    MEMORY_PRESSURE,
    THERMAL_ALERT,
    POWER_EVENT,
    USER_LOGIN,
    USER_LOGOUT,
    SYSTEM_SHUTDOWN,
    SYSTEM_STARTUP
};

/**
 * @brief System event
 */
struct SystemEvent {
    SystemEventType type;
    std::chrono::system_clock::time_point timestamp;
    std::string source;
    std::string description;
    std::unordered_map<std::string, std::string> data;
    LogLevel severity;
};

/**
 * @brief Alert configuration
 */
struct AlertConfig {
    std::string name;
    std::string description;
    bool enabled;
    
    // Conditions
    double cpu_threshold_percent = 90.0;
    double memory_threshold_percent = 90.0;
    double disk_threshold_percent = 90.0;
    double temperature_threshold_celsius = 80.0;
    
    // Actions
    bool send_notification = true;
    bool log_event = true;
    bool execute_command = false;
    std::string command;
    
    // Cooldown
    std::chrono::seconds cooldown_period = std::chrono::seconds(300);
};

/**
 * @brief Service configuration
 */
struct ServiceConfig {
    std::string name;
    std::string description;
    std::string executable;
    std::vector<std::string> arguments;
    std::string working_directory;
    bool auto_start = false;
    bool auto_restart = true;
    uint32_t max_restarts = 3;
    std::chrono::seconds restart_delay = std::chrono::seconds(5);
    std::unordered_map<std::string, std::string> environment;
};

/**
 * @brief MCP System Services Tools
 * 
 * Provides tools for system monitoring, logging, and service management
 * through the Model Context Protocol interface.
 */
class MCPSystemServicesTools {
public:
    MCPSystemServicesTools();
    ~MCPSystemServicesTools();

    /**
     * @brief Register all system services tools with MCP server
     * @param server MCP server instance
     */
    static void registerAllTools(AdvancedMCPServer& server);

    // System monitoring
    static SystemMetrics getSystemMetrics();
    static double getCpuUsage();
    static uint64_t getMemoryUsage();
    static uint64_t getDiskUsage(const std::string& path = "/");
    static double getTemperature();
    static std::vector<SystemMetrics::GPUMetrics> getGpuMetrics();
    
    // System information
    static std::string getHostname();
    static std::string getOSVersion();
    static std::string getKernelVersion();
    static std::chrono::system_clock::time_point getBootTime();
    static std::chrono::seconds getUptime();
    static double getLoadAverage();
    
    // Logging
    static void log(LogLevel level, const std::string& component, 
                   const std::string& message,
                   const std::unordered_map<std::string, std::string>& metadata = {});
    static std::vector<LogEntry> queryLogs(const std::string& component = "",
                                          LogLevel min_level = LogLevel::INFO,
                                          std::chrono::system_clock::time_point since = {},
                                          size_t limit = 100);
    static bool clearLogs(const std::string& component = "");
    static bool exportLogs(const std::string& filepath, const std::string& format = "json");
    
    // Event management
    static void emitEvent(const SystemEvent& event);
    static std::vector<SystemEvent> getEvents(SystemEventType type = {},
                                             std::chrono::system_clock::time_point since = {},
                                             size_t limit = 100);
    static void subscribeToEvents(SystemEventType type,
                                  std::function<void(const SystemEvent&)> callback);
    
    // Alerting
    static std::string createAlert(const AlertConfig& config);
    static bool updateAlert(const std::string& alert_id, const AlertConfig& config);
    static bool deleteAlert(const std::string& alert_id);
    static std::vector<AlertConfig> listAlerts();
    static bool enableAlert(const std::string& alert_id);
    static bool disableAlert(const std::string& alert_id);
    
    // Service registry
    static std::string registerService(const ServiceConfig& config);
    static bool unregisterService(const std::string& service_id);
    static std::vector<ServiceConfig> listServices();
    static ServiceConfig getServiceConfig(const std::string& service_id);
    static bool updateServiceConfig(const std::string& service_id, const ServiceConfig& config);
    
    // Service control
    static bool startManagedService(const std::string& service_id);
    static bool stopManagedService(const std::string& service_id);
    static bool restartManagedService(const std::string& service_id);
    static std::string getServiceStatus(const std::string& service_id);
    
    // Health checks
    static bool performHealthCheck();
    static std::unordered_map<std::string, std::string> getHealthStatus();
    static bool registerHealthCheck(const std::string& name,
                                    std::function<bool()> check_function);
    
    // Scheduling
    static std::string scheduleTask(const std::string& name,
                                   const std::string& command,
                                   const std::string& schedule); // cron format
    static bool cancelScheduledTask(const std::string& task_id);
    static std::vector<std::string> listScheduledTasks();
    
    // Helper functions
    static std::string formatSystemMetrics(const SystemMetrics& metrics);
    static std::string formatLogEntry(const LogEntry& entry);
    static std::string logLevelToString(LogLevel level);
    static LogLevel stringToLogLevel(const std::string& level);

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
    
    static std::shared_ptr<SystemLogger> logger_;
    static std::shared_ptr<SystemMonitor> monitor_;
    static std::shared_ptr<ServiceRegistry> registry_;
    static std::mutex mutex_;
};

/**
 * @brief System logger
 */
class SystemLogger {
public:
    SystemLogger();
    ~SystemLogger();

    // Logging
    void log(const LogEntry& entry);
    void trace(const std::string& component, const std::string& message);
    void debug(const std::string& component, const std::string& message);
    void info(const std::string& component, const std::string& message);
    void warning(const std::string& component, const std::string& message);
    void error(const std::string& component, const std::string& message);
    void critical(const std::string& component, const std::string& message);
    
    // Query
    std::vector<LogEntry> query(const std::string& component = "",
                               LogLevel min_level = LogLevel::INFO,
                               std::chrono::system_clock::time_point since = {},
                               size_t limit = 100);
    
    // Configuration
    void setMinLogLevel(LogLevel level);
    void setMaxLogEntries(size_t count);
    void enableFileLogging(const std::string& filepath);
    void disableFileLogging();
    void enableConsoleLogging(bool enabled);
    void enableSyslogLogging(bool enabled);
    
    // Management
    void clear();
    bool exportToFile(const std::string& filepath, const std::string& format = "json");
    size_t getLogCount() const;
    
    // Rotation
    void setRotationSize(uint64_t bytes);
    void setRotationInterval(std::chrono::hours hours);
    void rotate();

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

/**
 * @brief System monitor
 */
class SystemMonitor {
public:
    SystemMonitor();
    ~SystemMonitor();

    // Monitoring control
    void start();
    void stop();
    bool isRunning() const;
    void setUpdateInterval(std::chrono::seconds interval);
    
    // Metrics collection
    SystemMetrics getCurrentMetrics() const;
    std::vector<SystemMetrics> getMetricsHistory(
        std::chrono::system_clock::time_point since,
        std::chrono::system_clock::time_point until) const;
    
    // Specific metrics
    double getCpuUsage() const;
    uint64_t getMemoryUsage() const;
    uint64_t getDiskUsage(const std::string& path = "/") const;
    double getTemperature() const;
    std::vector<SystemMetrics::GPUMetrics> getGpuMetrics() const;
    
    // Callbacks
    using MetricsCallback = std::function<void(const SystemMetrics&)>;
    void setMetricsCallback(MetricsCallback callback);
    
    using ThresholdCallback = std::function<void(const std::string&, double)>;
    void setThresholdCallback(const std::string& metric, double threshold, ThresholdCallback callback);
    
    // Statistics
    struct MonitorStats {
        size_t samples_collected;
        std::chrono::system_clock::time_point start_time;
        std::chrono::seconds uptime;
        double avg_cpu_usage;
        double avg_memory_usage;
    };
    MonitorStats getStats() const;

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

/**
 * @brief Resource tracker
 */
class ResourceTracker {
public:
    ResourceTracker();
    ~ResourceTracker();

    // Tracking
    void trackProcess(int pid);
    void untrackProcess(int pid);
    void trackAllProcesses();
    
    // Resource usage
    struct ProcessResources {
        int pid;
        double cpu_percent;
        uint64_t memory_bytes;
        uint64_t disk_read_bytes;
        uint64_t disk_write_bytes;
        uint64_t network_rx_bytes;
        uint64_t network_tx_bytes;
        uint32_t num_threads;
        uint32_t num_file_descriptors;
    };
    ProcessResources getProcessResources(int pid) const;
    std::vector<ProcessResources> getAllTrackedResources() const;
    
    // Resource limits
    bool setProcessMemoryLimit(int pid, uint64_t bytes);
    bool setProcessCpuLimit(int pid, double percent);
    bool setProcessIOLimit(int pid, uint64_t bytes_per_sec);
    
    // Aggregation
    struct AggregatedResources {
        double total_cpu_percent;
        uint64_t total_memory_bytes;
        uint64_t total_disk_io_bytes;
        uint64_t total_network_io_bytes;
        size_t num_processes;
    };
    AggregatedResources getAggregatedResources() const;
    
    // Reporting
    std::string generateReport() const;
    bool exportReport(const std::string& filepath) const;

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

/**
 * @brief Service registry and manager
 */
class ServiceRegistry {
public:
    ServiceRegistry();
    ~ServiceRegistry();

    // Service registration
    std::string registerService(const ServiceConfig& config);
    bool unregisterService(const std::string& service_id);
    std::vector<std::string> listServices() const;
    ServiceConfig getServiceConfig(const std::string& service_id) const;
    bool updateServiceConfig(const std::string& service_id, const ServiceConfig& config);
    
    // Service lifecycle
    bool startService(const std::string& service_id);
    bool stopService(const std::string& service_id);
    bool restartService(const std::string& service_id);
    
    // Service status
    enum class ServiceStatus {
        STOPPED,
        STARTING,
        RUNNING,
        STOPPING,
        CRASHED,
        UNKNOWN
    };
    ServiceStatus getServiceStatus(const std::string& service_id) const;
    bool isServiceRunning(const std::string& service_id) const;
    int getServicePid(const std::string& service_id) const;
    
    // Service monitoring
    struct ServiceStats {
        std::string service_id;
        ServiceStatus status;
        int pid;
        std::chrono::system_clock::time_point start_time;
        std::chrono::seconds uptime;
        uint32_t restart_count;
        std::chrono::system_clock::time_point last_restart;
    };
    ServiceStats getServiceStats(const std::string& service_id) const;
    std::vector<ServiceStats> getAllServiceStats() const;
    
    // Dependencies
    bool addDependency(const std::string& service_id, const std::string& depends_on);
    bool removeDependency(const std::string& service_id, const std::string& depends_on);
    std::vector<std::string> getDependencies(const std::string& service_id) const;

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

/**
 * @brief Performance profiler
 */
class PerformanceProfiler {
public:
    PerformanceProfiler();
    ~PerformanceProfiler();

    // Profiling control
    void startProfiling(const std::string& name);
    void stopProfiling(const std::string& name);
    void resetProfiling(const std::string& name);
    
    // Measurements
    struct ProfileData {
        std::string name;
        uint64_t call_count;
        std::chrono::nanoseconds total_time;
        std::chrono::nanoseconds min_time;
        std::chrono::nanoseconds max_time;
        std::chrono::nanoseconds avg_time;
    };
    ProfileData getProfileData(const std::string& name) const;
    std::vector<ProfileData> getAllProfiles() const;
    
    // Scoped profiling
    class ScopedProfile {
    public:
        explicit ScopedProfile(PerformanceProfiler& profiler, const std::string& name);
        ~ScopedProfile();
    private:
        PerformanceProfiler& profiler_;
        std::string name_;
        std::chrono::high_resolution_clock::time_point start_;
    };
    
    // Reporting
    std::string generateReport() const;
    bool exportReport(const std::string& filepath) const;
    void clearAll();

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

/**
 * @brief System utilities
 */
class SystemUtils {
public:
    // System information
    static std::string getHostname();
    static std::string getUsername();
    static std::string getHomeDirectory();
    static std::string getTempDirectory();
    
    // OS information
    static std::string getOSName();
    static std::string getOSVersion();
    static std::string getKernelVersion();
    static std::string getArchitecture();
    
    // Hardware information
    static uint32_t getNumCPUs();
    static uint64_t getTotalMemory();
    static std::string getCPUModel();
    static std::vector<std::string> getGPUNames();
    
    // Time utilities
    static std::chrono::system_clock::time_point getBootTime();
    static std::chrono::seconds getUptime();
    static std::string formatTimestamp(std::chrono::system_clock::time_point time);
    static std::string formatDuration(std::chrono::seconds duration);
    
    // File system utilities
    static bool pathExists(const std::string& path);
    static bool isDirectory(const std::string& path);
    static bool isFile(const std::string& path);
    static uint64_t getFileSize(const std::string& path);
    static uint64_t getDiskSpace(const std::string& path);
    static uint64_t getFreeDiskSpace(const std::string& path);
    
    // Process utilities
    static int getCurrentPid();
    static int getParentPid();
    static std::string getProcessName(int pid);
    static std::string getProcessPath(int pid);
};

} // namespace system_services
} // namespace mcp
} // namespace cogniware

