#include "logger_cpp.h"
#include <filesystem>
#include <iostream>

namespace cogniware {
namespace utils {

// Singleton instance
Logger& Logger::getInstance() {
    static Logger instance;
    return instance;
}

// Constructor and destructor
Logger::Logger() : initialized_(false) {
    // Initialize spdlog
    spdlog::set_error_handler([](const std::string& msg) {
        std::cerr << "spdlog error: " << msg << std::endl;
    });
}

Logger::~Logger() {
    shutdown();
}

// Initialization
bool Logger::initialize(const LoggerConfig& config) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (initialized_) {
        return false;
    }

    config_ = config;
    
    if (!createLogger()) {
        return false;
    }

    initialized_ = true;
    return true;
}

void Logger::shutdown() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!initialized_) {
        return;
    }

    destroyLogger();
    initialized_ = false;
}

bool Logger::isInitialized() const {
    return initialized_;
}

// Configuration
LoggerConfig Logger::getConfig() const {
    return config_;
}

void Logger::setLogLevel(LogLevel level) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!initialized_) {
        return;
    }

    config_.level = level;
    logger_->set_level(static_cast<spdlog::level::level_enum>(level));
}

LogLevel Logger::getLogLevel() const {
    return config_.level;
}

void Logger::setPattern(const std::string& pattern) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!initialized_) {
        return;
    }

    config_.pattern = pattern;
    logger_->set_pattern(pattern);
}

// Flush logs
void Logger::flush() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!initialized_) {
        return;
    }

    logger_->flush();
}

// Critical error callback
void Logger::setCriticalErrorCallback(std::function<void(const std::string&)> callback) {
    std::lock_guard<std::mutex> lock(mutex_);
    critical_error_callback_ = std::move(callback);
}

void Logger::clearCriticalErrorCallback() {
    std::lock_guard<std::mutex> lock(mutex_);
    critical_error_callback_ = nullptr;
}

// Private methods
bool Logger::createLogger() {
    try {
        std::vector<spdlog::sink_ptr> sinks;

        // Add console sink if enabled
        if (config_.console_output) {
            auto console_sink = std::make_shared<spdlog::sinks::stdout_color_sink_mt>();
            console_sink->set_pattern(config_.pattern);
            sinks.push_back(console_sink);
        }

        // Add file sink if enabled
        if (config_.file_output) {
            // Create log directory if it doesn't exist
            auto log_dir = std::filesystem::path(config_.log_file).parent_path();
            if (!log_dir.empty() && !std::filesystem::exists(log_dir)) {
                std::filesystem::create_directories(log_dir);
            }

            auto file_sink = std::make_shared<spdlog::sinks::rotating_file_sink_mt>(
                config_.log_file,
                config_.max_file_size,
                config_.max_files
            );
            file_sink->set_pattern(config_.pattern);
            sinks.push_back(file_sink);
        }

        // Create logger with all sinks
        logger_ = std::make_shared<spdlog::logger>(config_.name, sinks.begin(), sinks.end());
        logger_->set_level(static_cast<spdlog::level::level_enum>(config_.level));
        
        // Set error handler
        logger_->set_error_handler([this](const std::string& msg) {
            if (critical_error_callback_) {
                critical_error_callback_(msg);
            }
        });

        return true;
    } catch (const std::exception& e) {
        std::cerr << "Failed to create logger: " << e.what() << std::endl;
        return false;
    }
}

void Logger::destroyLogger() {
    if (logger_) {
        logger_->flush();
        logger_.reset();
    }
}

} // namespace utils
} // namespace cogniware
