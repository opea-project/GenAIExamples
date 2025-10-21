#pragma once

#include <string>
#include <memory>
#include <mutex>
#include <sstream>
#include <functional>
#include <spdlog/spdlog.h>
#include <spdlog/sinks/rotating_file_sink.h>
#include <spdlog/sinks/stdout_color_sinks.h>

namespace cogniware {
namespace utils {

// Log levels matching spdlog levels
enum class LogLevel {
    TRACE = SPDLOG_LEVEL_TRACE,
    DEBUG = SPDLOG_LEVEL_DEBUG,
    INFO = SPDLOG_LEVEL_INFO,
    WARN = SPDLOG_LEVEL_WARN,
    ERROR = SPDLOG_LEVEL_ERROR,
    CRITICAL = SPDLOG_LEVEL_CRITICAL,
    OFF = SPDLOG_LEVEL_OFF
};

// Logger configuration
struct LoggerConfig {
    std::string name;
    std::string log_file;
    size_t max_file_size;
    size_t max_files;
    LogLevel level;
    bool console_output;
    bool file_output;
    std::string pattern;

    LoggerConfig() :
        name("cogniware"),
        log_file("cogniware.log"),
        max_file_size(5 * 1024 * 1024),  // 5MB
        max_files(3),
        level(LogLevel::INFO),
        console_output(true),
        file_output(true),
        pattern("[%Y-%m-%d %H:%M:%S.%e] [%^%l%$] [%t] %v") {}
};

// Logger class
class Logger {
public:
    static Logger& getInstance();

    // Prevent copying
    Logger(const Logger&) = delete;
    Logger& operator=(const Logger&) = delete;

    // Initialization
    bool initialize(const LoggerConfig& config);
    void shutdown();
    bool isInitialized() const;

    // Configuration
    LoggerConfig getConfig() const;
    void setLogLevel(LogLevel level);
    LogLevel getLogLevel() const;
    void setPattern(const std::string& pattern);

    // Logging methods
    template<typename... Args>
    void trace(const char* fmt, const Args&... args) {
        if (isInitialized()) {
            logger_->trace(fmt, args...);
        }
    }

    template<typename... Args>
    void debug(const char* fmt, const Args&... args) {
        if (isInitialized()) {
            logger_->debug(fmt, args...);
        }
    }

    template<typename... Args>
    void info(const char* fmt, const Args&... args) {
        if (isInitialized()) {
            logger_->info(fmt, args...);
        }
    }

    template<typename... Args>
    void warn(const char* fmt, const Args&... args) {
        if (isInitialized()) {
            logger_->warn(fmt, args...);
        }
    }

    template<typename... Args>
    void error(const char* fmt, const Args&... args) {
        if (isInitialized()) {
            logger_->error(fmt, args...);
        }
    }

    template<typename... Args>
    void critical(const char* fmt, const Args&... args) {
        if (isInitialized()) {
            logger_->critical(fmt, args...);
        }
    }

    // Flush logs
    void flush();

    // Set callback for critical errors
    void setCriticalErrorCallback(std::function<void(const std::string&)> callback);
    void clearCriticalErrorCallback();

private:
    Logger();
    ~Logger();

    bool createLogger();
    void destroyLogger();

    LoggerConfig config_;
    std::shared_ptr<spdlog::logger> logger_;
    std::mutex mutex_;
    bool initialized_;
    std::function<void(const std::string&)> critical_error_callback_;
};

// Convenience macros for logging
#define LOG_TRACE(...) cogniware::utils::Logger::getInstance().trace(__VA_ARGS__)
#define LOG_DEBUG(...) cogniware::utils::Logger::getInstance().debug(__VA_ARGS__)
#define LOG_INFO(...) cogniware::utils::Logger::getInstance().info(__VA_ARGS__)
#define LOG_WARN(...) cogniware::utils::Logger::getInstance().warn(__VA_ARGS__)
#define LOG_ERROR(...) cogniware::utils::Logger::getInstance().error(__VA_ARGS__)
#define LOG_CRITICAL(...) cogniware::utils::Logger::getInstance().critical(__VA_ARGS__)

} // namespace utils
} // namespace cogniware
