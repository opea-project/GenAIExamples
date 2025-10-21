#include "ipc/inter_llm_bus.h"
#include <mutex>
#include <queue>

namespace cogniware {
namespace ipc {

class InterLLMBus::Impl {
public:
    std::queue<Message> message_queue;
    mutable std::mutex mutex;
    bool initialized = false;
};

InterLLMBus::InterLLMBus() : pImpl(std::make_unique<Impl>()) {}
InterLLMBus::~InterLLMBus() { shutdown(); }

bool InterLLMBus::initialize() {
    pImpl->initialized = true;
    return true;
}

void InterLLMBus::shutdown() {
    pImpl->initialized = false;
}

bool InterLLMBus::sendMessage(const Message& msg) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    pImpl->message_queue.push(msg);
    return true;
}

Message InterLLMBus::receiveMessage(const std::string& receiver_id) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    if (pImpl->message_queue.empty()) return {};
    Message msg = pImpl->message_queue.front();
    pImpl->message_queue.pop();
    return msg;
}

void InterLLMBus::subscribe(const std::string& topic, std::function<void(const Message&)> callback) {}
void InterLLMBus::publish(const std::string& topic, const std::string& payload) {}

} // namespace ipc
} // namespace cogniware

