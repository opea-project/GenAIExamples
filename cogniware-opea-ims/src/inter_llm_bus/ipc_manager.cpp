#include "ipc_manager.h"
#include <algorithm>
#include <chrono>
#include <thread>
#include <cstring>
#include <sys/mman.h>
#include <fcntl.h>
#include <unistd.h>

namespace cogniware {
namespace bus {

IPCManager& IPCManager::getInstance() {
    static IPCManager instance;
    return instance;
}

IPCManager::IPCManager() :
    initialized_(false),
    shared_memory_(nullptr),
    shared_memory_size_(0),
    should_stop_(false) {
}

IPCManager::~IPCManager() {
    shutdown();
}

bool IPCManager::initialize(const IPCConfig& config) {
    std::unique_lock<std::shared_mutex> lock(mutex_);
    
    if (initialized_) {
        LOG_WARN("IPC manager already initialized");
        return false;
    }

    try {
        config_ = config;
        shared_memory_size_ = config_.shared_memory_size;

        if (!initializeSharedMemory()) {
            LOG_ERROR("Failed to initialize shared memory");
            return false;
        }

        // Register this process
        if (!registerProcess(config_.process_id)) {
            LOG_ERROR("Failed to register process");
            cleanupSharedMemory();
            return false;
        }

        initialized_ = true;
        LOG_INFO("IPC manager initialized for process {}", config_.process_id);
        return true;
    } catch (const std::exception& e) {
        LOG_ERROR("Failed to initialize IPC manager: {}", e.what());
        return false;
    }
}

void IPCManager::shutdown() {
    std::unique_lock<std::shared_mutex> lock(mutex_);
    
    if (!initialized_) {
        return;
    }

    try {
        should_stop_ = true;

        // Unregister this process
        unregisterProcess(config_.process_id);

        // Clean up shared memory
        cleanupSharedMemory();

        // Clear message queue and handlers
        clearQueue();
        message_handlers_.clear();
        process_heartbeats_.clear();

        initialized_ = false;
        LOG_INFO("IPC manager shut down");
    } catch (const std::exception& e) {
        LOG_ERROR("Error during IPC manager shutdown: {}", e.what());
    }
}

bool IPCManager::isInitialized() const {
    std::shared_lock<std::shared_mutex> lock(mutex_);
    return initialized_;
}

bool IPCManager::sendMessage(const IPCMessage& message) {
    if (!initialized_) {
        LOG_ERROR("IPC manager not initialized");
        return false;
    }

    if (!validateMessage(message)) {
        LOG_ERROR("Invalid message");
        return false;
    }

    std::unique_lock<std::shared_mutex> lock(mutex_);
    
    try {
        if (message_queue_.size() >= config_.max_queue_size) {
            LOG_ERROR("Message queue is full");
            stats_.dropped_messages++;
            return false;
        }

        // Encrypt message if enabled
        std::vector<uint8_t> encrypted;
        if (config_.enable_encryption) {
            if (!encryptMessage(message, encrypted)) {
                LOG_ERROR("Failed to encrypt message");
                return false;
            }
        }

        // Write message to shared memory
        const void* data = config_.enable_encryption ? encrypted.data() : &message;
        size_t size = config_.enable_encryption ? encrypted.size() : sizeof(message);
        
        if (!writeToSharedMemory(data, size)) {
            LOG_ERROR("Failed to write message to shared memory");
            return false;
        }

        message_queue_.push(message);
        stats_.queued_messages++;
        stats_.total_messages++;
        stats_.message_type_counts[std::to_string(static_cast<int>(message.type))]++;
        stats_.process_communication[message.receiver_id]++;
        stats_.last_update = std::chrono::system_clock::now();

        LOG_INFO("Message sent from {} to {}", message.sender_id, message.receiver_id);
        return true;
    } catch (const std::exception& e) {
        LOG_ERROR("Error sending message: {}", e.what());
        stats_.failed_messages++;
        return false;
    }
}

bool IPCManager::registerMessageHandler(MessageType type, MessageHandler handler) {
    std::unique_lock<std::shared_mutex> lock(mutex_);
    
    if (!initialized_) {
        LOG_ERROR("IPC manager not initialized");
        return false;
    }

    try {
        message_handlers_[type] = handler;
        LOG_INFO("Message handler registered for type {}", static_cast<int>(type));
        return true;
    } catch (const std::exception& e) {
        LOG_ERROR("Error registering message handler: {}", e.what());
        return false;
    }
}

bool IPCManager::unregisterMessageHandler(MessageType type) {
    std::unique_lock<std::shared_mutex> lock(mutex_);
    
    if (!initialized_) {
        LOG_ERROR("IPC manager not initialized");
        return false;
    }

    try {
        message_handlers_.erase(type);
        LOG_INFO("Message handler unregistered for type {}", static_cast<int>(type));
        return true;
    } catch (const std::exception& e) {
        LOG_ERROR("Error unregistering message handler: {}", e.what());
        return false;
    }
}

bool IPCManager::processMessages() {
    if (!initialized_) {
        LOG_ERROR("IPC manager not initialized");
        return false;
    }

    std::unique_lock<std::shared_mutex> lock(mutex_);
    
    try {
        while (!message_queue_.empty() && !should_stop_) {
            IPCMessage message = message_queue_.front();
            message_queue_.pop();
            stats_.queued_messages--;

            // Process message
            processMessage(message);
        }

        return true;
    } catch (const std::exception& e) {
        LOG_ERROR("Error processing messages: {}", e.what());
        return false;
    }
}

bool IPCManager::registerProcess(const std::string& process_id) {
    std::unique_lock<std::shared_mutex> lock(mutex_);
    
    if (process_heartbeats_.find(process_id) != process_heartbeats_.end()) {
        LOG_ERROR("Process {} already registered", process_id);
        return false;
    }

    try {
        process_heartbeats_[process_id] = std::chrono::system_clock::now();
        LOG_INFO("Process {} registered", process_id);
        return true;
    } catch (const std::exception& e) {
        LOG_ERROR("Error registering process: {}", e.what());
        return false;
    }
}

bool IPCManager::unregisterProcess(const std::string& process_id) {
    std::unique_lock<std::shared_mutex> lock(mutex_);
    
    if (process_heartbeats_.find(process_id) == process_heartbeats_.end()) {
        LOG_ERROR("Process {} not registered", process_id);
        return false;
    }

    try {
        process_heartbeats_.erase(process_id);
        LOG_INFO("Process {} unregistered", process_id);
        return true;
    } catch (const std::exception& e) {
        LOG_ERROR("Error unregistering process: {}", e.what());
        return false;
    }
}

std::vector<std::string> IPCManager::getRegisteredProcesses() const {
    std::shared_lock<std::shared_mutex> lock(mutex_);
    std::vector<std::string> processes;
    processes.reserve(process_heartbeats_.size());
    for (const auto& [id, _] : process_heartbeats_) {
        processes.push_back(id);
    }
    return processes;
}

bool IPCManager::isProcessRegistered(const std::string& process_id) const {
    std::shared_lock<std::shared_mutex> lock(mutex_);
    return process_heartbeats_.find(process_id) != process_heartbeats_.end();
}

size_t IPCManager::getQueueSize() const {
    std::shared_lock<std::shared_mutex> lock(mutex_);
    return message_queue_.size();
}

void IPCManager::clearQueue() {
    std::unique_lock<std::shared_mutex> lock(mutex_);
    std::queue<IPCMessage> empty;
    std::swap(message_queue_, empty);
}

bool IPCManager::isQueueFull() const {
    std::shared_lock<std::shared_mutex> lock(mutex_);
    return message_queue_.size() >= config_.max_queue_size;
}

IPCStats IPCManager::getStats() const {
    return stats_;
}

void IPCManager::resetStats() {
    stats_ = IPCStats();
}

IPCConfig IPCManager::getConfig() const {
    std::shared_lock<std::shared_mutex> lock(mutex_);
    return config_;
}

bool IPCManager::updateConfig(const IPCConfig& config) {
    std::unique_lock<std::shared_mutex> lock(mutex_);
    
    if (!initialized_) {
        LOG_ERROR("IPC manager not initialized");
        return false;
    }

    try {
        config_ = config;
        LOG_INFO("IPC configuration updated");
        return true;
    } catch (const std::exception& e) {
        LOG_ERROR("Error updating IPC configuration: {}", e.what());
        return false;
    }
}

void IPCManager::processMessage(const IPCMessage& message) {
    auto it = message_handlers_.find(message.type);
    if (it != message_handlers_.end()) {
        try {
            it->second(message);
            stats_.successful_messages++;
        } catch (const std::exception& e) {
            LOG_ERROR("Error processing message: {}", e.what());
            stats_.failed_messages++;
        }
    } else {
        LOG_WARN("No handler registered for message type {}", static_cast<int>(message.type));
    }
}

bool IPCManager::validateMessage(const IPCMessage& message) const {
    if (message.sender_id.empty()) {
        LOG_ERROR("Message sender ID cannot be empty");
        return false;
    }

    if (message.receiver_id.empty()) {
        LOG_ERROR("Message receiver ID cannot be empty");
        return false;
    }

    if (message.message_id.empty()) {
        LOG_ERROR("Message ID cannot be empty");
        return false;
    }

    if (message.payload.size() > config_.max_message_size) {
        LOG_ERROR("Message payload exceeds maximum size");
        return false;
    }

    return true;
}

void IPCManager::updateStats(const IPCMessage& message, bool success) {
    auto now = std::chrono::system_clock::now();
    auto latency = std::chrono::duration_cast<std::chrono::milliseconds>(
        now - message.timestamp
    );

    if (success) {
        stats_.successful_messages++;
    } else {
        stats_.failed_messages++;
    }

    if (stats_.total_messages == 1) {
        stats_.min_latency = latency;
        stats_.max_latency = latency;
        stats_.average_latency = latency;
    } else {
        stats_.min_latency = std::min(stats_.min_latency, latency);
        stats_.max_latency = std::max(stats_.max_latency, latency);
        stats_.average_latency = std::chrono::milliseconds(
            (stats_.average_latency.count() * (stats_.total_messages - 1) + 
             latency.count()) / stats_.total_messages
        );
    }

    stats_.last_update = now;
}

bool IPCManager::initializeSharedMemory() {
    try {
        int fd = shm_open(config_.shared_memory_name.c_str(), 
                         O_CREAT | O_RDWR, 
                         S_IRUSR | S_IWUSR);
        
        if (fd == -1) {
            LOG_ERROR("Failed to create shared memory object");
            return false;
        }

        if (ftruncate(fd, shared_memory_size_) == -1) {
            close(fd);
            LOG_ERROR("Failed to set shared memory size");
            return false;
        }

        shared_memory_ = mmap(nullptr, 
                            shared_memory_size_,
                            PROT_READ | PROT_WRITE,
                            MAP_SHARED,
                            fd,
                            0);

        close(fd);

        if (shared_memory_ == MAP_FAILED) {
            LOG_ERROR("Failed to map shared memory");
            return false;
        }

        LOG_INFO("Shared memory initialized with size {} bytes", shared_memory_size_);
        return true;
    } catch (const std::exception& e) {
        LOG_ERROR("Error initializing shared memory: {}", e.what());
        return false;
    }
}

void IPCManager::cleanupSharedMemory() {
    if (shared_memory_) {
        munmap(shared_memory_, shared_memory_size_);
        shm_unlink(config_.shared_memory_name.c_str());
        shared_memory_ = nullptr;
        shared_memory_size_ = 0;
    }
}

bool IPCManager::writeToSharedMemory(const void* data, size_t size) {
    if (!shared_memory_ || size > shared_memory_size_) {
        return false;
    }

    try {
        std::memcpy(shared_memory_, data, size);
        return true;
    } catch (const std::exception& e) {
        LOG_ERROR("Error writing to shared memory: {}", e.what());
        return false;
    }
}

bool IPCManager::readFromSharedMemory(void* data, size_t size) {
    if (!shared_memory_ || size > shared_memory_size_) {
        return false;
    }

    try {
        std::memcpy(data, shared_memory_, size);
        return true;
    } catch (const std::exception& e) {
        LOG_ERROR("Error reading from shared memory: {}", e.what());
        return false;
    }
}

bool IPCManager::encryptMessage(const IPCMessage& message, std::vector<uint8_t>& encrypted) {
    // TODO: Implement encryption using OpenSSL or similar
    return false;
}

bool IPCManager::decryptMessage(const std::vector<uint8_t>& encrypted, IPCMessage& message) {
    // TODO: Implement decryption using OpenSSL or similar
    return false;
}

} // namespace bus
} // namespace cogniware
