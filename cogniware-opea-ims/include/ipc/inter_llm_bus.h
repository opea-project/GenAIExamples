#pragma once

#include <string>
#include <vector>
#include <memory>
#include <functional>

namespace cogniware {
namespace ipc {

struct Message {
    std::string sender_id;
    std::string receiver_id;
    std::string type;
    std::string payload;
    std::chrono::system_clock::time_point timestamp;
};

class InterLLMBus {
public:
    InterLLMBus();
    ~InterLLMBus();

    bool initialize();
    void shutdown();
    
    bool sendMessage(const Message& msg);
    Message receiveMessage(const std::string& receiver_id);
    
    void subscribe(const std::string& topic, std::function<void(const Message&)> callback);
    void publish(const std::string& topic, const std::string& payload);

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

} // namespace ipc
} // namespace cogniware

