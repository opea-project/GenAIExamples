#pragma once

#include <string>
#include <vector>
#include <memory>
#include <mutex>
#include <shared_mutex>
#include <atomic>
#include <chrono>
#include <functional>
#include <queue>
#include <unordered_map>
#include "utils/error_handler_cpp.h"
#include "utils/logger_cpp.h"
#include "shared_tensor_buffer.h"

namespace cogniware {
namespace bus {

// Message types for IPC communication
enum class MessageType {
    TENSOR_REQUEST,
    TENSOR_RESPONSE,
    TENSOR_UPDATE,
    TENSOR_DELETE,
    HEARTBEAT,
    ERROR,
    SHUTDOWN
};

// Message structure for IPC communication
struct IPCMessage {
    MessageType type;
    std::string sender_id;
    std::string receiver_id;
    std::string message_id;
    std::chrono::system_clock::time_point timestamp;
    std::unordered_map<std::string, std::string> metadata;
    std::vector<uint8_t> payload;

    IPCMessage() : type(MessageType::ERROR) {}
};

// IPC manager configuration
struct IPCConfig {
    std::string process_id;
    std::string shared_memory_name;
    size_t shared_memory_size;
    size_t max_message_size;
    size_t max_queue_size;
    std::chrono::milliseconds heartbeat_interval;
    std::chrono::milliseconds timeout;
    bool enable_encryption;
    std::string encryption_key;
    std::unordered_map<std::string, std::string> parameters;

    IPCConfig() :
        shared_memory_size(1024 * 1024),  // 1MB
        max_message_size(64 * 1024),      // 64KB
        max_queue_size(1000),
        heartbeat_interval(std::chrono::seconds(5)),
        timeout(std::chrono::seconds(30)),
        enable_encryption(false) {}
};

// IPC manager statistics
struct IPCStats {
    std::atomic<size_t> total_messages;
    std::atomic<size_t> successful_messages;
    std::atomic<size_t> failed_messages;
    std::atomic<size_t> queued_messages;
    std::atomic<size_t> dropped_messages;
    std::chrono::system_clock::time_point last_update;
    std::chrono::milliseconds average_latency;
    std::chrono::milliseconds max_latency;
    std::chrono::milliseconds min_latency;
    std::unordered_map<std::string, size_t> message_type_counts;
    std::unordered_map<std::string, size_t> process_communication;
};

// Message handler function type
using MessageHandler = std::function<void(const IPCMessage&)>;

// IPC manager class
class IPCManager {
public:
    static IPCManager& getInstance();

    // Prevent copying
    IPCManager(const IPCManager&) = delete;
    IPCManager& operator=(const IPCManager&) = delete;

    // Initialization
    bool initialize(const IPCConfig& config);
    void shutdown();
    bool isInitialized() const;

    // Message handling
    bool sendMessage(const IPCMessage& message);
    bool registerMessageHandler(MessageType type, MessageHandler handler);
    bool unregisterMessageHandler(MessageType type);
    bool processMessages();

    // Process management
    bool registerProcess(const std::string& process_id);
    bool unregisterProcess(const std::string& process_id);
    std::vector<std::string> getRegisteredProcesses() const;
    bool isProcessRegistered(const std::string& process_id) const;

    // Queue management
    size_t getQueueSize() const;
    void clearQueue();
    bool isQueueFull() const;

    // Statistics and monitoring
    IPCStats getStats() const;
    void resetStats();

    // Configuration
    IPCConfig getConfig() const;
    bool updateConfig(const IPCConfig& config);

private:
    IPCManager();
    ~IPCManager();

    // Message processing
    void processMessage(const IPCMessage& message);
    bool validateMessage(const IPCMessage& message) const;
    void updateStats(const IPCMessage& message, bool success);

    // Shared memory management
    bool initializeSharedMemory();
    void cleanupSharedMemory();
    bool writeToSharedMemory(const void* data, size_t size);
    bool readFromSharedMemory(void* data, size_t size);

    // Security
    bool encryptMessage(const IPCMessage& message, std::vector<uint8_t>& encrypted);
    bool decryptMessage(const std::vector<uint8_t>& encrypted, IPCMessage& message);

    // Member variables
    IPCConfig config_;
    bool initialized_;
    mutable std::shared_mutex mutex_;
    std::queue<IPCMessage> message_queue_;
    std::unordered_map<MessageType, MessageHandler> message_handlers_;
    std::unordered_map<std::string, std::chrono::system_clock::time_point> process_heartbeats_;
    std::atomic<size_t> total_messages_;
    IPCStats stats_;
    void* shared_memory_;
    size_t shared_memory_size_;
    std::atomic<bool> should_stop_;
};

} // namespace bus
} // namespace cogniware
