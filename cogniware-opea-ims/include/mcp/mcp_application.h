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
namespace application {

// Forward declarations
class Process;
class ProcessMonitor;
class ApplicationManager;

/**
 * @brief Process status information
 */
enum class ProcessStatus {
    RUNNING,
    STOPPED,
    CRASHED,
    ZOMBIE,
    SLEEPING,
    UNKNOWN
};

/**
 * @brief Process priority levels
 */
enum class ProcessPriority {
    VERY_LOW = -20,
    LOW = -10,
    NORMAL = 0,
    HIGH = 10,
    VERY_HIGH = 20
};

/**
 * @brief Process resource usage statistics
 */
struct ProcessStats {
    uint64_t cpu_time_ms;           // CPU time in milliseconds
    uint64_t memory_bytes;          // Memory usage in bytes
    double cpu_percent;             // CPU usage percentage
    double memory_percent;          // Memory usage percentage
    uint64_t num_threads;           // Number of threads
    uint64_t num_file_descriptors;  // Number of open file descriptors
    uint64_t read_bytes;            // Bytes read from disk
    uint64_t write_bytes;           // Bytes written to disk
    std::chrono::system_clock::time_point start_time;
    std::chrono::milliseconds uptime;
};

/**
 * @brief Application/Process information
 */
struct ProcessInfo {
    int pid;
    int parent_pid;
    std::string name;
    std::string command;
    std::string working_directory;
    ProcessStatus status;
    ProcessPriority priority;
    ProcessStats stats;
    std::vector<std::string> arguments;
    std::unordered_map<std::string, std::string> environment;
};

/**
 * @brief Process launch configuration
 */
struct LaunchConfig {
    std::string executable;
    std::vector<std::string> arguments;
    std::unordered_map<std::string, std::string> environment;
    std::string working_directory;
    ProcessPriority priority = ProcessPriority::NORMAL;
    bool capture_stdout = false;
    bool capture_stderr = false;
    bool detached = false;
    uint64_t memory_limit_bytes = 0;     // 0 = no limit
    uint64_t cpu_limit_percent = 100;    // 0-100
    std::chrono::seconds timeout = std::chrono::seconds(0); // 0 = no timeout
};

/**
 * @brief Process execution result
 */
struct ProcessResult {
    bool success;
    int exit_code;
    std::string stdout_output;
    std::string stderr_output;
    std::chrono::milliseconds execution_time;
    std::string error_message;
};

/**
 * @brief Process search criteria
 */
struct ProcessSearchCriteria {
    std::string name_pattern;
    std::string command_pattern;
    ProcessStatus status = ProcessStatus::UNKNOWN;
    int min_cpu_percent = 0;
    int min_memory_mb = 0;
};

/**
 * @brief MCP Application Control Tools
 * 
 * Provides tools for launching, managing, and monitoring system applications
 * through the Model Context Protocol interface.
 */
class MCPApplicationTools {
public:
    MCPApplicationTools();
    ~MCPApplicationTools();

    /**
     * @brief Register all application control tools with MCP server
     * @param server MCP server instance
     */
    static void registerAllTools(AdvancedMCPServer& server);

    // Process launching
    static std::shared_ptr<Process> launchProcess(const LaunchConfig& config);
    static ProcessResult executeCommand(const std::string& command, 
                                       const std::string& working_dir = "",
                                       std::chrono::seconds timeout = std::chrono::seconds(30));
    static std::shared_ptr<Process> launchApplication(const std::string& app_name,
                                                     const std::vector<std::string>& args = {});

    // Process management
    static bool killProcess(int pid, bool force = false);
    static bool terminateProcess(int pid);
    static bool stopProcess(int pid);
    static bool resumeProcess(int pid);
    static bool setPriority(int pid, ProcessPriority priority);

    // Process information
    static ProcessInfo getProcessInfo(int pid);
    static std::vector<ProcessInfo> listProcesses();
    static std::vector<ProcessInfo> findProcesses(const ProcessSearchCriteria& criteria);
    static bool isProcessRunning(int pid);
    static int getProcessByName(const std::string& name);

    // Application management
    static bool openApplication(const std::string& app_name);
    static bool closeApplication(const std::string& app_name);
    static std::vector<std::string> listInstalledApplications();
    static std::vector<std::string> listRunningApplications();

    // Window management (X11/Wayland)
    static bool focusWindow(const std::string& window_title);
    static bool minimizeWindow(const std::string& window_title);
    static bool maximizeWindow(const std::string& window_title);
    static bool closeWindow(const std::string& window_title);
    static std::vector<std::string> listOpenWindows();

    // Service management (systemd)
    static bool startService(const std::string& service_name);
    static bool stopService(const std::string& service_name);
    static bool restartService(const std::string& service_name);
    static bool enableService(const std::string& service_name);
    static bool disableService(const std::string& service_name);
    static std::string getServiceStatus(const std::string& service_name);
    static std::vector<std::string> listServices();

    // Helper functions
    static std::string formatProcessInfo(const ProcessInfo& info);
    static std::string formatProcessList(const std::vector<ProcessInfo>& processes);

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;

    static std::unordered_map<int, std::shared_ptr<Process>> processes_;
    static std::mutex processes_mutex_;
};

/**
 * @brief Represents a managed process
 */
class Process {
public:
    explicit Process(const LaunchConfig& config);
    ~Process();

    // Process control
    bool start();
    bool stop();
    bool kill(bool force = false);
    bool wait(std::chrono::milliseconds timeout = std::chrono::milliseconds(0));
    
    // Process status
    int getPid() const;
    ProcessStatus getStatus() const;
    bool isRunning() const;
    int getExitCode() const;
    
    // Process I/O
    std::string readStdout();
    std::string readStderr();
    bool writeStdin(const std::string& data);
    
    // Process information
    ProcessInfo getInfo() const;
    ProcessStats getStats() const;
    
    // Resource management
    bool setMemoryLimit(uint64_t bytes);
    bool setCpuLimit(uint64_t percent);
    bool setPriority(ProcessPriority priority);
    
    // Callbacks
    using OutputCallback = std::function<void(const std::string&)>;
    void setStdoutCallback(OutputCallback callback);
    void setStderrCallback(OutputCallback callback);
    void setExitCallback(std::function<void(int)> callback);

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

/**
 * @brief Monitors processes for changes and events
 */
class ProcessMonitor {
public:
    ProcessMonitor();
    ~ProcessMonitor();

    // Monitor control
    void start();
    void stop();
    bool isRunning() const;
    
    // Process watching
    void watchProcess(int pid);
    void unwatchProcess(int pid);
    void watchAllProcesses();
    
    // Event callbacks
    using ProcessEventCallback = std::function<void(int pid, ProcessStatus status)>;
    void setProcessStartCallback(ProcessEventCallback callback);
    void setProcessStopCallback(ProcessEventCallback callback);
    void setProcessCrashCallback(ProcessEventCallback callback);
    
    // Resource monitoring
    using ResourceCallback = std::function<void(int pid, const ProcessStats&)>;
    void setResourceCallback(ResourceCallback callback);
    void setMonitorInterval(std::chrono::milliseconds interval);
    
    // Get current state
    std::vector<ProcessInfo> getWatchedProcesses() const;
    ProcessStats getProcessStats(int pid) const;

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

/**
 * @brief Manages application lifecycle and coordination
 */
class ApplicationManager {
public:
    ApplicationManager();
    ~ApplicationManager();

    // Application registry
    void registerApplication(const std::string& name, const std::string& executable);
    void unregisterApplication(const std::string& name);
    std::vector<std::string> listApplications() const;
    
    // Application launching
    std::shared_ptr<Process> launchApplication(const std::string& name, 
                                              const std::vector<std::string>& args = {});
    bool closeApplication(const std::string& name);
    bool isApplicationRunning(const std::string& name) const;
    
    // Process groups
    std::string createProcessGroup(const std::vector<int>& pids);
    bool stopProcessGroup(const std::string& group_id);
    bool killProcessGroup(const std::string& group_id);
    std::vector<int> getProcessGroup(const std::string& group_id) const;
    
    // Resource management
    bool setGroupMemoryLimit(const std::string& group_id, uint64_t bytes);
    bool setGroupCpuLimit(const std::string& group_id, uint64_t percent);
    ProcessStats getGroupStats(const std::string& group_id) const;
    
    // Lifecycle management
    void setAutoRestart(int pid, bool enabled);
    void setMaxRestarts(int pid, int count);
    void setRestartDelay(int pid, std::chrono::seconds delay);
    
    // Statistics
    struct ManagerStats {
        size_t total_processes;
        size_t running_processes;
        size_t crashed_processes;
        size_t total_restarts;
        std::chrono::system_clock::time_point start_time;
    };
    ManagerStats getStats() const;

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

/**
 * @brief Application sandbox for secure execution
 */
class ApplicationSandbox {
public:
    struct SandboxConfig {
        bool restrict_network = false;
        bool restrict_filesystem = true;
        std::vector<std::string> allowed_paths;
        std::vector<std::string> allowed_hosts;
        uint64_t memory_limit_mb = 1024;
        uint64_t disk_quota_mb = 1024;
        bool allow_process_spawn = false;
        std::chrono::seconds execution_timeout = std::chrono::seconds(300);
    };

    explicit ApplicationSandbox(const SandboxConfig& config);
    ~ApplicationSandbox();

    // Sandbox execution
    std::shared_ptr<Process> execute(const LaunchConfig& config);
    ProcessResult executeCommand(const std::string& command);
    
    // Sandbox management
    bool addAllowedPath(const std::string& path);
    bool removeAllowedPath(const std::string& path);
    bool addAllowedHost(const std::string& host);
    bool removeAllowedHost(const std::string& host);
    
    // Sandbox state
    bool isActive() const;
    SandboxConfig getConfig() const;
    void updateConfig(const SandboxConfig& config);

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

/**
 * @brief Desktop environment integration
 */
class DesktopIntegration {
public:
    // Desktop detection
    static std::string getDesktopEnvironment();
    static bool isWayland();
    static bool isX11();
    
    // Notification system
    static bool sendNotification(const std::string& title, 
                                const std::string& message,
                                const std::string& icon = "");
    
    // Clipboard operations
    static std::string getClipboardText();
    static bool setClipboardText(const std::string& text);
    
    // Screen information
    struct ScreenInfo {
        int width;
        int height;
        int refresh_rate;
        std::string name;
    };
    static std::vector<ScreenInfo> getScreens();
    
    // Desktop shortcuts
    static bool createDesktopShortcut(const std::string& name,
                                     const std::string& executable,
                                     const std::string& icon = "");
    static bool removeDesktopShortcut(const std::string& name);
};

} // namespace application
} // namespace mcp
} // namespace cogniware

