#include "mcp/mcp_application.h"
#include <sstream>
#include <algorithm>
#include <mutex>
#include <thread>
#include <queue>
#include <condition_variable>
#include <sys/types.h>
#include <sys/wait.h>
#include <signal.h>
#include <unistd.h>
#include <fcntl.h>

namespace cogniware {
namespace mcp {
namespace application {

// Static members
std::unordered_map<int, std::shared_ptr<Process>> MCPApplicationTools::processes_;
std::mutex MCPApplicationTools::processes_mutex_;

// Helper functions
std::string MCPApplicationTools::formatProcessInfo(const ProcessInfo& info) {
    std::stringstream ss;
    ss << "PID: " << info.pid << "\n";
    ss << "Name: " << info.name << "\n";
    ss << "Command: " << info.command << "\n";
    ss << "Status: ";
    
    switch (info.status) {
        case ProcessStatus::RUNNING: ss << "Running"; break;
        case ProcessStatus::STOPPED: ss << "Stopped"; break;
        case ProcessStatus::CRASHED: ss << "Crashed"; break;
        case ProcessStatus::ZOMBIE: ss << "Zombie"; break;
        case ProcessStatus::SLEEPING: ss << "Sleeping"; break;
        default: ss << "Unknown";
    }
    
    ss << "\n";
    ss << "CPU: " << info.stats.cpu_percent << "%\n";
    ss << "Memory: " << (info.stats.memory_bytes / 1024 / 1024) << " MB\n";
    ss << "Threads: " << info.stats.num_threads << "\n";
    
    return ss.str();
}

std::string MCPApplicationTools::formatProcessList(const std::vector<ProcessInfo>& processes) {
    std::stringstream ss;
    ss << "Total processes: " << processes.size() << "\n\n";
    
    for (const auto& proc : processes) {
        ss << formatProcessInfo(proc) << "\n";
    }
    
    return ss.str();
}

// MCPApplicationTools Implementation
class MCPApplicationTools::Impl {
public:
    Impl() = default;
};

MCPApplicationTools::MCPApplicationTools() 
    : pImpl(std::make_unique<Impl>()) {}

MCPApplicationTools::~MCPApplicationTools() = default;

void MCPApplicationTools::registerAllTools(AdvancedMCPServer& server) {
    // Launch process tool
    MCPTool launch_tool;
    launch_tool.name = "launch_process";
    launch_tool.description = "Launch a new process";
    
    MCPParameter exec_param;
    exec_param.name = "executable";
    exec_param.type = ParameterType::STRING;
    exec_param.description = "Path to executable";
    exec_param.required = true;
    launch_tool.parameters.push_back(exec_param);
    
    MCPParameter args_param;
    args_param.name = "arguments";
    args_param.type = ParameterType::STRING;
    args_param.description = "Command line arguments (space-separated)";
    args_param.required = false;
    launch_tool.parameters.push_back(args_param);
    
    launch_tool.handler = [](const std::unordered_map<std::string, std::string>& params) {
        LaunchConfig config;
        config.executable = params.at("executable");
        
        if (params.count("arguments")) {
            std::istringstream iss(params.at("arguments"));
            std::string arg;
            while (iss >> arg) {
                config.arguments.push_back(arg);
            }
        }
        
        auto process = launchProcess(config);
        if (process) {
            return "Process launched with PID: " + std::to_string(process->getPid());
        }
        return "Failed to launch process";
    };
    
    server.registerTool(launch_tool);
    
    // Execute command tool
    MCPTool exec_tool;
    exec_tool.name = "execute_command";
    exec_tool.description = "Execute a shell command and return output";
    
    MCPParameter cmd_param;
    cmd_param.name = "command";
    cmd_param.type = ParameterType::STRING;
    cmd_param.description = "Command to execute";
    cmd_param.required = true;
    exec_tool.parameters.push_back(cmd_param);
    
    exec_tool.handler = [](const std::unordered_map<std::string, std::string>& params) {
        auto result = executeCommand(params.at("command"));
        
        std::stringstream ss;
        ss << "Exit code: " << result.exit_code << "\n";
        ss << "Execution time: " << result.execution_time.count() << "ms\n\n";
        ss << "STDOUT:\n" << result.stdout_output << "\n\n";
        ss << "STDERR:\n" << result.stderr_output << "\n";
        
        return ss.str();
    };
    
    server.registerTool(exec_tool);
    
    // Kill process tool
    MCPTool kill_tool;
    kill_tool.name = "kill_process";
    kill_tool.description = "Kill a running process";
    
    MCPParameter pid_param;
    pid_param.name = "pid";
    pid_param.type = ParameterType::NUMBER;
    pid_param.description = "Process ID";
    pid_param.required = true;
    kill_tool.parameters.push_back(pid_param);
    
    kill_tool.handler = [](const std::unordered_map<std::string, std::string>& params) {
        int pid = std::stoi(params.at("pid"));
        bool success = killProcess(pid);
        return success ? "Process killed successfully" : "Failed to kill process";
    };
    
    server.registerTool(kill_tool);
    
    // List processes tool
    MCPTool list_tool;
    list_tool.name = "list_processes";
    list_tool.description = "List all running processes";
    
    list_tool.handler = [](const std::unordered_map<std::string, std::string>&) {
        auto processes = listProcesses();
        return formatProcessList(processes);
    };
    
    server.registerTool(list_tool);
    
    // Open application tool
    MCPTool open_app_tool;
    open_app_tool.name = "open_application";
    open_app_tool.description = "Open a desktop application";
    
    MCPParameter app_name_param;
    app_name_param.name = "application";
    app_name_param.type = ParameterType::STRING;
    app_name_param.description = "Application name (e.g., firefox, code, gedit)";
    app_name_param.required = true;
    open_app_tool.parameters.push_back(app_name_param);
    
    open_app_tool.handler = [](const std::unordered_map<std::string, std::string>& params) {
        bool success = openApplication(params.at("application"));
        return success ? "Application opened successfully" : "Failed to open application";
    };
    
    server.registerTool(open_app_tool);
    
    // Service management tools
    MCPTool start_service_tool;
    start_service_tool.name = "start_service";
    start_service_tool.description = "Start a systemd service";
    
    MCPParameter service_param;
    service_param.name = "service";
    service_param.type = ParameterType::STRING;
    service_param.description = "Service name";
    service_param.required = true;
    start_service_tool.parameters.push_back(service_param);
    
    start_service_tool.handler = [](const std::unordered_map<std::string, std::string>& params) {
        bool success = startService(params.at("service"));
        return success ? "Service started successfully" : "Failed to start service";
    };
    
    server.registerTool(start_service_tool);
}

std::shared_ptr<Process> MCPApplicationTools::launchProcess(const LaunchConfig& config) {
    auto process = std::make_shared<Process>(config);
    
    if (process->start()) {
        std::lock_guard<std::mutex> lock(processes_mutex_);
        processes_[process->getPid()] = process;
        return process;
    }
    
    return nullptr;
}

ProcessResult MCPApplicationTools::executeCommand(
    const std::string& command,
    const std::string& working_dir,
    std::chrono::seconds timeout) {
    
    auto start_time = std::chrono::high_resolution_clock::now();
    
    ProcessResult result;
    result.success = false;
    result.exit_code = -1;
    
    // Execute command using popen
    FILE* pipe = popen(command.c_str(), "r");
    if (!pipe) {
        result.error_message = "Failed to execute command";
        return result;
    }
    
    // Read output
    char buffer[256];
    while (fgets(buffer, sizeof(buffer), pipe) != nullptr) {
        result.stdout_output += buffer;
    }
    
    // Get exit status
    int status = pclose(pipe);
    result.exit_code = WEXITSTATUS(status);
    result.success = (result.exit_code == 0);
    
    auto end_time = std::chrono::high_resolution_clock::now();
    result.execution_time = std::chrono::duration_cast<std::chrono::milliseconds>(
        end_time - start_time);
    
    return result;
}

std::shared_ptr<Process> MCPApplicationTools::launchApplication(
    const std::string& app_name,
    const std::vector<std::string>& args) {
    
    LaunchConfig config;
    config.executable = app_name;
    config.arguments = args;
    config.detached = true;
    
    return launchProcess(config);
}

bool MCPApplicationTools::killProcess(int pid, bool force) {
    int signal = force ? SIGKILL : SIGTERM;
    return ::kill(pid, signal) == 0;
}

bool MCPApplicationTools::terminateProcess(int pid) {
    return killProcess(pid, false);
}

bool MCPApplicationTools::stopProcess(int pid) {
    return ::kill(pid, SIGSTOP) == 0;
}

bool MCPApplicationTools::resumeProcess(int pid) {
    return ::kill(pid, SIGCONT) == 0;
}

bool MCPApplicationTools::setPriority(int pid, ProcessPriority priority) {
    return setpriority(PRIO_PROCESS, pid, static_cast<int>(priority)) == 0;
}

ProcessInfo MCPApplicationTools::getProcessInfo(int pid) {
    ProcessInfo info;
    info.pid = pid;
    info.parent_pid = 0;
    info.name = "unknown";
    info.status = ProcessStatus::UNKNOWN;
    
    // Read from /proc filesystem
    std::string stat_path = "/proc/" + std::to_string(pid) + "/stat";
    FILE* stat_file = fopen(stat_path.c_str(), "r");
    
    if (stat_file) {
        char comm[256];
        char state;
        fscanf(stat_file, "%*d %s %c %d", comm, &state, &info.parent_pid);
        info.name = comm;
        
        switch (state) {
            case 'R': info.status = ProcessStatus::RUNNING; break;
            case 'S': info.status = ProcessStatus::SLEEPING; break;
            case 'T': info.status = ProcessStatus::STOPPED; break;
            case 'Z': info.status = ProcessStatus::ZOMBIE; break;
            default: info.status = ProcessStatus::UNKNOWN;
        }
        
        fclose(stat_file);
    }
    
    return info;
}

std::vector<ProcessInfo> MCPApplicationTools::listProcesses() {
    std::vector<ProcessInfo> processes;
    
    // List /proc directory
    DIR* dir = opendir("/proc");
    if (!dir) return processes;
    
    struct dirent* entry;
    while ((entry = readdir(dir)) != nullptr) {
        // Check if directory name is a number (PID)
        if (entry->d_type == DT_DIR) {
            char* endptr;
            int pid = strtol(entry->d_name, &endptr, 10);
            
            if (*endptr == '\0' && pid > 0) {
                auto info = getProcessInfo(pid);
                if (info.status != ProcessStatus::UNKNOWN) {
                    processes.push_back(info);
                }
            }
        }
    }
    
    closedir(dir);
    return processes;
}

std::vector<ProcessInfo> MCPApplicationTools::findProcesses(const ProcessSearchCriteria& criteria) {
    auto all_processes = listProcesses();
    std::vector<ProcessInfo> matched;
    
    for (const auto& proc : all_processes) {
        bool match = true;
        
        if (!criteria.name_pattern.empty()) {
            if (proc.name.find(criteria.name_pattern) == std::string::npos) {
                match = false;
            }
        }
        
        if (criteria.status != ProcessStatus::UNKNOWN) {
            if (proc.status != criteria.status) {
                match = false;
            }
        }
        
        if (match) {
            matched.push_back(proc);
        }
    }
    
    return matched;
}

bool MCPApplicationTools::isProcessRunning(int pid) {
    return ::kill(pid, 0) == 0;
}

int MCPApplicationTools::getProcessByName(const std::string& name) {
    auto processes = listProcesses();
    
    for (const auto& proc : processes) {
        if (proc.name.find(name) != std::string::npos) {
            return proc.pid;
        }
    }
    
    return -1;
}

bool MCPApplicationTools::openApplication(const std::string& app_name) {
    LaunchConfig config;
    config.executable = app_name;
    config.detached = true;
    
    auto process = launchProcess(config);
    return process != nullptr;
}

bool MCPApplicationTools::closeApplication(const std::string& app_name) {
    int pid = getProcessByName(app_name);
    if (pid > 0) {
        return killProcess(pid);
    }
    return false;
}

std::vector<std::string> MCPApplicationTools::listInstalledApplications() {
    std::vector<std::string> apps;
    
    // List applications from common directories
    const char* app_dirs[] = {
        "/usr/share/applications",
        "/usr/local/share/applications",
        "~/.local/share/applications"
    };
    
    for (const char* dir_path : app_dirs) {
        DIR* dir = opendir(dir_path);
        if (!dir) continue;
        
        struct dirent* entry;
        while ((entry = readdir(dir)) != nullptr) {
            std::string name = entry->d_name;
            if (name.size() > 8 && name.substr(name.size() - 8) == ".desktop") {
                apps.push_back(name.substr(0, name.size() - 8));
            }
        }
        
        closedir(dir);
    }
    
    return apps;
}

std::vector<std::string> MCPApplicationTools::listRunningApplications() {
    auto processes = listProcesses();
    std::vector<std::string> apps;
    
    for (const auto& proc : processes) {
        if (proc.status == ProcessStatus::RUNNING) {
            apps.push_back(proc.name);
        }
    }
    
    return apps;
}

// Service management (systemd)
bool MCPApplicationTools::startService(const std::string& service_name) {
    std::string command = "systemctl start " + service_name;
    auto result = executeCommand(command);
    return result.success;
}

bool MCPApplicationTools::stopService(const std::string& service_name) {
    std::string command = "systemctl stop " + service_name;
    auto result = executeCommand(command);
    return result.success;
}

bool MCPApplicationTools::restartService(const std::string& service_name) {
    std::string command = "systemctl restart " + service_name;
    auto result = executeCommand(command);
    return result.success;
}

bool MCPApplicationTools::enableService(const std::string& service_name) {
    std::string command = "systemctl enable " + service_name;
    auto result = executeCommand(command);
    return result.success;
}

bool MCPApplicationTools::disableService(const std::string& service_name) {
    std::string command = "systemctl disable " + service_name;
    auto result = executeCommand(command);
    return result.success;
}

std::string MCPApplicationTools::getServiceStatus(const std::string& service_name) {
    std::string command = "systemctl status " + service_name;
    auto result = executeCommand(command);
    return result.stdout_output;
}

std::vector<std::string> MCPApplicationTools::listServices() {
    std::vector<std::string> services;
    
    auto result = executeCommand("systemctl list-units --type=service --all");
    
    std::istringstream iss(result.stdout_output);
    std::string line;
    while (std::getline(iss, line)) {
        // Parse service name from output
        if (line.find(".service") != std::string::npos) {
            size_t start = line.find_first_not_of(" ");
            size_t end = line.find(".service");
            if (start != std::string::npos && end != std::string::npos) {
                services.push_back(line.substr(start, end - start));
            }
        }
    }
    
    return services;
}

// Window management stubs (would require X11/Wayland integration)
bool MCPApplicationTools::focusWindow(const std::string&) { return false; }
bool MCPApplicationTools::minimizeWindow(const std::string&) { return false; }
bool MCPApplicationTools::maximizeWindow(const std::string&) { return false; }
bool MCPApplicationTools::closeWindow(const std::string&) { return false; }
std::vector<std::string> MCPApplicationTools::listOpenWindows() { return {}; }

// Process class implementation
class Process::Impl {
public:
    LaunchConfig config;
    int pid = -1;
    int exit_code = -1;
    ProcessStatus status = ProcessStatus::UNKNOWN;
    int stdout_pipe[2] = {-1, -1};
    int stderr_pipe[2] = {-1, -1};
    int stdin_pipe[2] = {-1, -1};
    std::mutex mutex;
    
    explicit Impl(const LaunchConfig& cfg) : config(cfg) {}
    
    ~Impl() {
        cleanup_pipes();
    }
    
    void cleanup_pipes() {
        if (stdout_pipe[0] != -1) close(stdout_pipe[0]);
        if (stdout_pipe[1] != -1) close(stdout_pipe[1]);
        if (stderr_pipe[0] != -1) close(stderr_pipe[0]);
        if (stderr_pipe[1] != -1) close(stderr_pipe[1]);
        if (stdin_pipe[0] != -1) close(stdin_pipe[0]);
        if (stdin_pipe[1] != -1) close(stdin_pipe[1]);
    }
};

Process::Process(const LaunchConfig& config)
    : pImpl(std::make_unique<Impl>(config)) {}

Process::~Process() {
    if (isRunning()) {
        stop();
    }
}

bool Process::start() {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    // Create pipes if needed
    if (pImpl->config.capture_stdout) {
        if (pipe(pImpl->stdout_pipe) != 0) return false;
    }
    if (pImpl->config.capture_stderr) {
        if (pipe(pImpl->stderr_pipe) != 0) return false;
    }
    
    // Fork process
    pid_t pid = fork();
    
    if (pid < 0) {
        // Fork failed
        return false;
    } else if (pid == 0) {
        // Child process
        
        // Redirect stdout
        if (pImpl->config.capture_stdout) {
            close(pImpl->stdout_pipe[0]);
            dup2(pImpl->stdout_pipe[1], STDOUT_FILENO);
            close(pImpl->stdout_pipe[1]);
        }
        
        // Redirect stderr
        if (pImpl->config.capture_stderr) {
            close(pImpl->stderr_pipe[0]);
            dup2(pImpl->stderr_pipe[1], STDERR_FILENO);
            close(pImpl->stderr_pipe[1]);
        }
        
        // Change working directory
        if (!pImpl->config.working_directory.empty()) {
            chdir(pImpl->config.working_directory.c_str());
        }
        
        // Build argument list
        std::vector<char*> args;
        args.push_back(const_cast<char*>(pImpl->config.executable.c_str()));
        for (const auto& arg : pImpl->config.arguments) {
            args.push_back(const_cast<char*>(arg.c_str()));
        }
        args.push_back(nullptr);
        
        // Execute
        execvp(pImpl->config.executable.c_str(), args.data());
        
        // If execvp returns, it failed
        _exit(1);
    } else {
        // Parent process
        pImpl->pid = pid;
        pImpl->status = ProcessStatus::RUNNING;
        
        // Close write ends of pipes
        if (pImpl->config.capture_stdout) {
            close(pImpl->stdout_pipe[1]);
            pImpl->stdout_pipe[1] = -1;
        }
        if (pImpl->config.capture_stderr) {
            close(pImpl->stderr_pipe[1]);
            pImpl->stderr_pipe[1] = -1;
        }
        
        return true;
    }
    
    return false;
}

bool Process::stop() {
    return MCPApplicationTools::terminateProcess(pImpl->pid);
}

bool Process::kill(bool force) {
    return MCPApplicationTools::killProcess(pImpl->pid, force);
}

bool Process::wait(std::chrono::milliseconds timeout) {
    int status;
    int result = waitpid(pImpl->pid, &status, WNOHANG);
    
    if (result > 0) {
        pImpl->exit_code = WEXITSTATUS(status);
        pImpl->status = ProcessStatus::STOPPED;
        return true;
    }
    
    return false;
}

int Process::getPid() const {
    return pImpl->pid;
}

ProcessStatus Process::getStatus() const {
    return pImpl->status;
}

bool Process::isRunning() const {
    return pImpl->status == ProcessStatus::RUNNING && 
           MCPApplicationTools::isProcessRunning(pImpl->pid);
}

int Process::getExitCode() const {
    return pImpl->exit_code;
}

std::string Process::readStdout() {
    std::string output;
    if (pImpl->stdout_pipe[0] != -1) {
        char buffer[4096];
        ssize_t n = read(pImpl->stdout_pipe[0], buffer, sizeof(buffer) - 1);
        if (n > 0) {
            buffer[n] = '\0';
            output = buffer;
        }
    }
    return output;
}

std::string Process::readStderr() {
    std::string output;
    if (pImpl->stderr_pipe[0] != -1) {
        char buffer[4096];
        ssize_t n = read(pImpl->stderr_pipe[0], buffer, sizeof(buffer) - 1);
        if (n > 0) {
            buffer[n] = '\0';
            output = buffer;
        }
    }
    return output;
}

bool Process::writeStdin(const std::string& data) {
    if (pImpl->stdin_pipe[1] != -1) {
        return write(pImpl->stdin_pipe[1], data.c_str(), data.length()) > 0;
    }
    return false;
}

ProcessInfo Process::getInfo() const {
    return MCPApplicationTools::getProcessInfo(pImpl->pid);
}

ProcessStats Process::getStats() const {
    ProcessStats stats{};
    // Would implement proper stat reading
    return stats;
}

bool Process::setMemoryLimit(uint64_t) { return false; }
bool Process::setCpuLimit(uint64_t) { return false; }
bool Process::setPriority(ProcessPriority priority) {
    return MCPApplicationTools::setPriority(pImpl->pid, priority);
}

void Process::setStdoutCallback(OutputCallback) {}
void Process::setStderrCallback(OutputCallback) {}
void Process::setExitCallback(std::function<void(int)>) {}

// ProcessMonitor stub
class ProcessMonitor::Impl {
public:
    bool running = false;
};

ProcessMonitor::ProcessMonitor() : pImpl(std::make_unique<Impl>()) {}
ProcessMonitor::~ProcessMonitor() = default;
void ProcessMonitor::start() { pImpl->running = true; }
void ProcessMonitor::stop() { pImpl->running = false; }
bool ProcessMonitor::isRunning() const { return pImpl->running; }
void ProcessMonitor::watchProcess(int) {}
void ProcessMonitor::unwatchProcess(int) {}
void ProcessMonitor::watchAllProcesses() {}
void ProcessMonitor::setProcessStartCallback(ProcessEventCallback) {}
void ProcessMonitor::setProcessStopCallback(ProcessEventCallback) {}
void ProcessMonitor::setProcessCrashCallback(ProcessEventCallback) {}
void ProcessMonitor::setResourceCallback(ResourceCallback) {}
void ProcessMonitor::setMonitorInterval(std::chrono::milliseconds) {}
std::vector<ProcessInfo> ProcessMonitor::getWatchedProcesses() const { return {}; }
ProcessStats ProcessMonitor::getProcessStats(int) const { return {}; }

// ApplicationManager stub
class ApplicationManager::Impl {};
ApplicationManager::ApplicationManager() : pImpl(std::make_unique<Impl>()) {}
ApplicationManager::~ApplicationManager() = default;
void ApplicationManager::registerApplication(const std::string&, const std::string&) {}
void ApplicationManager::unregisterApplication(const std::string&) {}
std::vector<std::string> ApplicationManager::listApplications() const { return {}; }
std::shared_ptr<Process> ApplicationManager::launchApplication(const std::string&, const std::vector<std::string>&) { return nullptr; }
bool ApplicationManager::closeApplication(const std::string&) { return false; }
bool ApplicationManager::isApplicationRunning(const std::string&) const { return false; }
std::string ApplicationManager::createProcessGroup(const std::vector<int>&) { return ""; }
bool ApplicationManager::stopProcessGroup(const std::string&) { return false; }
bool ApplicationManager::killProcessGroup(const std::string&) { return false; }
std::vector<int> ApplicationManager::getProcessGroup(const std::string&) const { return {}; }
bool ApplicationManager::setGroupMemoryLimit(const std::string&, uint64_t) { return false; }
bool ApplicationManager::setGroupCpuLimit(const std::string&, uint64_t) { return false; }
ProcessStats ApplicationManager::getGroupStats(const std::string&) const { return {}; }
void ApplicationManager::setAutoRestart(int, bool) {}
void ApplicationManager::setMaxRestarts(int, int) {}
void ApplicationManager::setRestartDelay(int, std::chrono::seconds) {}
ApplicationManager::ManagerStats ApplicationManager::getStats() const { return {}; }

// ApplicationSandbox stub
class ApplicationSandbox::Impl {
public:
    SandboxConfig config;
    explicit Impl(const SandboxConfig& cfg) : config(cfg) {}
};

ApplicationSandbox::ApplicationSandbox(const SandboxConfig& config)
    : pImpl(std::make_unique<Impl>(config)) {}
ApplicationSandbox::~ApplicationSandbox() = default;
std::shared_ptr<Process> ApplicationSandbox::execute(const LaunchConfig&) { return nullptr; }
ProcessResult ApplicationSandbox::executeCommand(const std::string&) { return {}; }
bool ApplicationSandbox::addAllowedPath(const std::string&) { return false; }
bool ApplicationSandbox::removeAllowedPath(const std::string&) { return false; }
bool ApplicationSandbox::addAllowedHost(const std::string&) { return false; }
bool ApplicationSandbox::removeAllowedHost(const std::string&) { return false; }
bool ApplicationSandbox::isActive() const { return false; }
ApplicationSandbox::SandboxConfig ApplicationSandbox::getConfig() const { return pImpl->config; }
void ApplicationSandbox::updateConfig(const SandboxConfig& config) { pImpl->config = config; }

// DesktopIntegration stubs
std::string DesktopIntegration::getDesktopEnvironment() {
    const char* desktop = getenv("XDG_CURRENT_DESKTOP");
    return desktop ? desktop : "unknown";
}

bool DesktopIntegration::isWayland() {
    const char* session = getenv("WAYLAND_DISPLAY");
    return session != nullptr;
}

bool DesktopIntegration::isX11() {
    const char* display = getenv("DISPLAY");
    return display != nullptr;
}

bool DesktopIntegration::sendNotification(const std::string& title,
                                         const std::string& message,
                                         const std::string& icon) {
    std::string command = "notify-send";
    if (!icon.empty()) {
        command += " -i " + icon;
    }
    command += " \"" + title + "\" \"" + message + "\"";
    
    auto result = MCPApplicationTools::executeCommand(command);
    return result.success;
}

std::string DesktopIntegration::getClipboardText() { return ""; }
bool DesktopIntegration::setClipboardText(const std::string&) { return false; }
std::vector<DesktopIntegration::ScreenInfo> DesktopIntegration::getScreens() { return {}; }
bool DesktopIntegration::createDesktopShortcut(const std::string&, const std::string&, const std::string&) { return false; }
bool DesktopIntegration::removeDesktopShortcut(const std::string&) { return false; }

} // namespace application
} // namespace mcp
} // namespace cogniware

