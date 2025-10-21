#pragma once

#include <string>
#include <memory>
#include <mutex>
#include <unordered_map>
#include <functional>
#include <stdexcept>
#include "logger_cpp.h"

namespace cogniware {
namespace utils {

// Error codes
enum class ErrorCode {
    // System errors (1000-1999)
    SYSTEM_ERROR = 1000,
    MEMORY_ERROR = 1001,
    FILE_ERROR = 1002,
    NETWORK_ERROR = 1003,
    TIMEOUT_ERROR = 1004,
    CONFIGURATION_ERROR = 1005,

    // Model errors (2000-2999)
    MODEL_ERROR = 2000,
    MODEL_LOAD_ERROR = 2001,
    MODEL_INIT_ERROR = 2002,
    MODEL_INFERENCE_ERROR = 2003,
    MODEL_UNLOAD_ERROR = 2004,

    // Tokenizer errors (3000-3999)
    TOKENIZER_ERROR = 3000,
    TOKENIZER_LOAD_ERROR = 3001,
    TOKENIZER_INIT_ERROR = 3002,
    TOKENIZER_ENCODE_ERROR = 3003,
    TOKENIZER_DECODE_ERROR = 3004,

    // Resource errors (4000-4999)
    RESOURCE_ERROR = 4000,
    GPU_ERROR = 4001,
    CPU_ERROR = 4002,
    MEMORY_LIMIT_ERROR = 4003,
    CONCURRENCY_ERROR = 4004,

    // Request errors (5000-5999)
    REQUEST_ERROR = 5000,
    INVALID_REQUEST = 5001,
    REQUEST_TIMEOUT = 5002,
    REQUEST_CANCELLED = 5003,
    REQUEST_QUEUE_FULL = 5004,

    // Validation errors (6000-6999)
    VALIDATION_ERROR = 6000,
    INVALID_PARAMETER = 6001,
    INVALID_CONFIG = 6002,
    INVALID_STATE = 6003,

    // Unknown error
    UNKNOWN_ERROR = 9999
};

// Error structure
struct Error {
    ErrorCode code;
    std::string message;
    std::string details;
    std::string file;
    int line;
    std::string function;
    std::chrono::system_clock::time_point timestamp;

    Error() : 
        code(ErrorCode::UNKNOWN_ERROR),
        line(0),
        timestamp(std::chrono::system_clock::now()) {}
};

// Error handler class
class ErrorHandler {
public:
    static ErrorHandler& getInstance();

    // Prevent copying
    ErrorHandler(const ErrorHandler&) = delete;
    ErrorHandler& operator=(const ErrorHandler&) = delete;

    // Error handling
    void handleError(const Error& error);
    void handleException(const std::exception& e, ErrorCode code = ErrorCode::UNKNOWN_ERROR);
    void handleUnknownException();

    // Error callbacks
    void setErrorCallback(std::function<void(const Error&)> callback);
    void clearErrorCallback();
    void setExceptionCallback(std::function<void(const std::exception&, ErrorCode)> callback);
    void clearExceptionCallback();

    // Error information
    Error getLastError() const;
    void clearLastError();
    std::string getErrorString(const Error& error) const;
    std::string getErrorCodeString(ErrorCode code) const;

    // Error recovery
    bool canRecover(ErrorCode code) const;
    void setRecoveryCallback(ErrorCode code, std::function<bool()> callback);
    void clearRecoveryCallback(ErrorCode code);
    bool attemptRecovery(ErrorCode code);

private:
    ErrorHandler();
    ~ErrorHandler();

    void logError(const Error& error);
    void notifyError(const Error& error);
    bool tryRecovery(const Error& error);

    Error last_error_;
    std::mutex mutex_;
    std::function<void(const Error&)> error_callback_;
    std::function<void(const std::exception&, ErrorCode)> exception_callback_;
    std::unordered_map<ErrorCode, std::function<bool()>> recovery_callbacks_;
};

// Error macros
#define THROW_ERROR(code, message) \
    do { \
        cogniware::utils::Error error; \
        error.code = code; \
        error.message = message; \
        error.file = __FILE__; \
        error.line = __LINE__; \
        error.function = __FUNCTION__; \
        cogniware::utils::ErrorHandler::getInstance().handleError(error); \
        throw std::runtime_error(message); \
    } while (0)

#define CHECK_ERROR(condition, code, message) \
    do { \
        if (!(condition)) { \
            THROW_ERROR(code, message); \
        } \
    } while (0)

#define HANDLE_EXCEPTION(code) \
    catch (const std::exception& e) { \
        cogniware::utils::ErrorHandler::getInstance().handleException(e, code); \
    } \
    catch (...) { \
        cogniware::utils::ErrorHandler::getInstance().handleUnknownException(); \
    }

} // namespace utils
} // namespace cogniware
