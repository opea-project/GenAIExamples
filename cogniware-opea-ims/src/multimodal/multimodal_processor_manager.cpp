#include "multimodal/multimodal_processor.h"
#include <algorithm>

namespace cogniware {
namespace multimodal {

// MultimodalProcessorManager Implementation
class MultimodalProcessorManager::ManagerImpl {
public:
    std::unordered_map<std::string, std::shared_ptr<AdvancedMultimodalProcessor>> processors;
    mutable std::mutex processors_mutex;
};

MultimodalProcessorManager::MultimodalProcessorManager()
    : pImpl(std::make_unique<ManagerImpl>()) {}

MultimodalProcessorManager::~MultimodalProcessorManager() = default;

MultimodalProcessorManager& MultimodalProcessorManager::getInstance() {
    static MultimodalProcessorManager instance;
    return instance;
}

bool MultimodalProcessorManager::createProcessor(
    const std::string& processor_id,
    const MultimodalConfig& config) {
    
    std::lock_guard<std::mutex> lock(pImpl->processors_mutex);
    
    if (pImpl->processors.find(processor_id) != pImpl->processors.end()) {
        return false;
    }

    pImpl->processors[processor_id] = 
        std::make_shared<AdvancedMultimodalProcessor>(config);
    
    return true;
}

bool MultimodalProcessorManager::destroyProcessor(const std::string& processor_id) {
    std::lock_guard<std::mutex> lock(pImpl->processors_mutex);
    return pImpl->processors.erase(processor_id) > 0;
}

std::shared_ptr<AdvancedMultimodalProcessor> 
MultimodalProcessorManager::getProcessor(const std::string& processor_id) {
    std::lock_guard<std::mutex> lock(pImpl->processors_mutex);
    auto it = pImpl->processors.find(processor_id);
    return (it != pImpl->processors.end()) ? it->second : nullptr;
}

std::vector<ProcessingResult> 
MultimodalProcessorManager::processBatchAcrossProcessors(
    const std::vector<MultimodalInput>& inputs) {
    
    std::vector<ProcessingResult> results;
    results.reserve(inputs.size());

    std::lock_guard<std::mutex> lock(pImpl->processors_mutex);
    
    if (pImpl->processors.empty()) {
        return results;
    }

    // Distribute inputs across processors
    size_t processor_idx = 0;
    std::vector<std::shared_ptr<AdvancedMultimodalProcessor>> processor_list;
    for (const auto& [id, proc] : pImpl->processors) {
        processor_list.push_back(proc);
    }

    for (const auto& input : inputs) {
        auto& processor = processor_list[processor_idx % processor_list.size()];
        results.push_back(processor->processMultimodal(input));
        ++processor_idx;
    }

    return results;
}

size_t MultimodalProcessorManager::getActiveProcessorCount() const {
    std::lock_guard<std::mutex> lock(pImpl->processors_mutex);
    return pImpl->processors.size();
}

std::vector<std::string> MultimodalProcessorManager::getActiveProcessorIds() const {
    std::lock_guard<std::mutex> lock(pImpl->processors_mutex);
    std::vector<std::string> ids;
    for (const auto& [id, _] : pImpl->processors) {
        ids.push_back(id);
    }
    return ids;
}

} // namespace multimodal
} // namespace cogniware

