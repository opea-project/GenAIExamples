#include "error_handler_cpp.h"
#include <sstream>
#include <iomanip>

namespace cogniware {
namespace utils {

// Singleton instance
ErrorHandler& ErrorHandler::getInstance() {
    static ErrorHandler instance;
    return instance;
}

// Constructor and destructor
ErrorHandler::ErrorHandler() {}

ErrorHandler::~ErrorHandler() = default;

// Error handling
void ErrorHandler::handleError(const Error& error) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    last_error_ = error;
    logError(error);
    notifyError(error);
    tryRecovery(error);
}

void ErrorHandler::handleException(const std::exception& e, ErrorCode code) {
    Error error;
    error.code = code;
    error.message = e.what();
    error.timestamp = std::chrono::system_clock::now();
    
    handleError(error);

    if (exception_callback_) {
        exception_callback_(e, code);
    }
}

void ErrorHandler::handleUnknownException() {
    Error error;
    error.code = ErrorCode::UNKNOWN_ERROR;
    error.message = "Unknown exception occurred";
    error.timestamp = std::chrono::system_clock::now();
    
    handleError(error);
}

// Error callbacks
void ErrorHandler::setErrorCallback(std::function<void(const Error&)> callback) {
    std::lock_guard<std::mutex> lock(mutex_);
    error_callback_ = std::move(callback);
}

void ErrorHandler::clearErrorCallback() {
    std::lock_guard<std::mutex> lock(mutex_);
    error_callback_ = nullptr;
}

void ErrorHandler::setExceptionCallback(std::function<void(const std::exception&, ErrorCode)> callback) {
    std::lock_guard<std::mutex> lock(mutex_);
    exception_callback_ = std::move(callback);
}

void ErrorHandler::clearExceptionCallback() {
    std::lock_guard<std::mutex> lock(mutex_);
    exception_callback_ = nullptr;
}

// Error information
Error ErrorHandler::getLastError() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return last_error_;
}

void ErrorHandler::clearLastError() {
    std::lock_guard<std::mutex> lock(mutex_);
    last_error_ = Error();
}

std::string ErrorHandler::getErrorString(const Error& error) const {
    std::stringstream ss;
    ss << "Error [" << static_cast<int>(error.code) << "]: " << error.message;
    
    if (!error.details.empty()) {
        ss << "\nDetails: " << error.details;
    }
    
    ss << "\nLocation: " << error.file << ":" << error.line << " in " << error.function;
    
    auto time = std::chrono::system_clock::to_time_t(error.timestamp);
    ss << "\nTime: " << std::put_time(std::localtime(&time), "%Y-%m-%d %H:%M:%S");
    
    return ss.str();
}

std::string ErrorHandler::getErrorCodeString(ErrorCode code) const {
    switch (code) {
        case ErrorCode::SYSTEM_ERROR:
            return "System Error";
        case ErrorCode::MEMORY_ERROR:
            return "Memory Error";
        case ErrorCode::FILE_ERROR:
            return "File Error";
        case ErrorCode::NETWORK_ERROR:
            return "Network Error";
        case ErrorCode::TIMEOUT_ERROR:
            return "Timeout Error";
        case ErrorCode::CONFIGURATION_ERROR:
            return "Configuration Error";
        case ErrorCode::MODEL_ERROR:
            return "Model Error";
        case ErrorCode::MODEL_LOAD_ERROR:
            return "Model Load Error";
        case ErrorCode::MODEL_INIT_ERROR:
            return "Model Initialization Error";
        case ErrorCode::MODEL_INFERENCE_ERROR:
            return "Model Inference Error";
        case ErrorCode::MODEL_UNLOAD_ERROR:
            return "Model Unload Error";
        case ErrorCode::TOKENIZER_ERROR:
            return "Tokenizer Error";
        case ErrorCode::TOKENIZER_LOAD_ERROR:
            return "Tokenizer Load Error";
        case ErrorCode::TOKENIZER_INIT_ERROR:
            return "Tokenizer Initialization Error";
        case ErrorCode::TOKENIZER_ENCODE_ERROR:
            return "Tokenizer Encode Error";
        case ErrorCode::TOKENIZER_DECODE_ERROR:
            return "Tokenizer Decode Error";
        case ErrorCode::RESOURCE_ERROR:
            return "Resource Error";
        case ErrorCode::GPU_ERROR:
            return "GPU Error";
        case ErrorCode::CPU_ERROR:
            return "CPU Error";
        case ErrorCode::MEMORY_LIMIT_ERROR:
            return "Memory Limit Error";
        case ErrorCode::CONCURRENCY_ERROR:
            return "Concurrency Error";
        case ErrorCode::REQUEST_ERROR:
            return "Request Error";
        case ErrorCode::INVALID_REQUEST:
            return "Invalid Request";
        case ErrorCode::REQUEST_TIMEOUT:
            return "Request Timeout";
        case ErrorCode::REQUEST_CANCELLED:
            return "Request Cancelled";
        case ErrorCode::REQUEST_QUEUE_FULL:
            return "Request Queue Full";
        case ErrorCode::VALIDATION_ERROR:
            return "Validation Error";
        case ErrorCode::INVALID_PARAMETER:
            return "Invalid Parameter";
        case ErrorCode::INVALID_CONFIG:
            return "Invalid Configuration";
        case ErrorCode::INVALID_STATE:
            return "Invalid State";
        case ErrorCode::UNKNOWN_ERROR:
        default:
            return "Unknown Error";
    }
}

// Error recovery
bool ErrorHandler::canRecover(ErrorCode code) const {
    std::lock_guard<std::mutex> lock(mutex_);
    return recovery_callbacks_.find(code) != recovery_callbacks_.end();
}

void ErrorHandler::setRecoveryCallback(ErrorCode code, std::function<bool()> callback) {
    std::lock_guard<std::mutex> lock(mutex_);
    recovery_callbacks_[code] = std::move(callback);
}

void ErrorHandler::clearRecoveryCallback(ErrorCode code) {
    std::lock_guard<std::mutex> lock(mutex_);
    recovery_callbacks_.erase(code);
}

bool ErrorHandler::attemptRecovery(ErrorCode code) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = recovery_callbacks_.find(code);
    if (it == recovery_callbacks_.end()) {
        return false;
    }

    try {
        return it->second();
    } catch (const std::exception& e) {
        LOG_ERROR("Recovery attempt failed: {}", e.what());
        return false;
    }
}

// Private methods
void ErrorHandler::logError(const Error& error) {
    std::string error_str = getErrorString(error);
    
    switch (error.code) {
        case ErrorCode::CRITICAL_ERROR:
            LOG_CRITICAL("{}", error_str);
            break;
        case ErrorCode::ERROR:
            LOG_ERROR("{}", error_str);
            break;
        case ErrorCode::WARNING:
            LOG_WARN("{}", error_str);
            break;
        default:
            LOG_INFO("{}", error_str);
            break;
    }
}

void ErrorHandler::notifyError(const Error& error) {
    if (error_callback_) {
        try {
            error_callback_(error);
        } catch (const std::exception& e) {
            LOG_ERROR("Error callback failed: {}", e.what());
        }
    }
}

bool ErrorHandler::tryRecovery(const Error& error) {
    if (canRecover(error.code)) {
        LOG_INFO("Attempting recovery for error: {}", getErrorCodeString(error.code));
        return attemptRecovery(error.code);
    }
    return false;
}

} // namespace utils
} // namespace cogniware
