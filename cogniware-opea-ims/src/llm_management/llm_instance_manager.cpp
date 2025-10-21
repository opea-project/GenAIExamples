/**
 * @file llm_instance_manager.cpp
 * @brief Implementation of the LLM instance manager
 */

#include "llm_management/llm_instance_manager.hpp"
#include "llm_management/llm_instance.hpp"
#include "model_config_manager/model_config_manager.hpp"
#include "model_config_manager/model_registry_manager.hpp"
#include <fstream>
#include <filesystem>
#include <chrono>
#include <thread>

namespace cogniware {

LLMInstanceManager& LLMInstanceManager::getInstance() {
    static LLMInstanceManager instance;
    return instance;
}

bool LLMInstanceManager::initialize(const std::string& config_path) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    config_path_ = config_path;
    
    // Load configurations
    if (!loadConfigurations()) {
        return false;
    }
    
    // Start resource monitoring
    running_ = true;
    monitor_thread_ = std::thread(&LLMInstanceManager::monitorResources, this);
    
    return true;
}

bool LLMInstanceManager::createInstance(const std::string& model_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Check if instance already exists
    if (instances_.find(model_id) != instances_.end()) {
        return false;
    }
    
    // Get model configuration
    auto& config_manager = ModelConfigManager::getInstance();
    auto config = config_manager.getModelConfig(model_id);
    if (!config) {
        return false;
    }
    
    // Create new instance
    auto instance = std::make_shared<LLMInstance>(model_id, *config);
    if (!instance->initialize()) {
        return false;
    }
    
    instances_[model_id] = instance;
    return true;
}

bool LLMInstanceManager::destroyInstance(const std::string& model_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = instances_.find(model_id);
    if (it == instances_.end()) {
        return false;
    }
    
    it->second->shutdown();
    instances_.erase(it);
    return true;
}

bool LLMInstanceManager::submitInferenceRequest(
    const InferenceRequest& request,
    InferenceResponse& response
) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = instances_.find(request.model_id);
    if (it == instances_.end()) {
        return false;
    }
    
    return it->second->infer(request, response);
}

nlohmann::json LLMInstanceManager::getInstanceStatus(const std::string& model_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = instances_.find(model_id);
    if (it == instances_.end()) {
        return nlohmann::json::object();
    }
    
    return it->second->getStatus();
}

nlohmann::json LLMInstanceManager::getResourceUsage() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    nlohmann::json usage = nlohmann::json::object();
    for (const auto& [model_id, instance] : instances_) {
        usage[model_id] = instance->getResourceUsage();
    }
    
    return usage;
}

bool LLMInstanceManager::setInstanceConfig(
    const std::string& model_id,
    const nlohmann::json& config
) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = instances_.find(model_id);
    if (it == instances_.end()) {
        return false;
    }
    
    return it->second->setConfig(config);
}

nlohmann::json LLMInstanceManager::getInstanceConfig(const std::string& model_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = instances_.find(model_id);
    if (it == instances_.end()) {
        return nlohmann::json::object();
    }
    
    return it->second->getConfig();
}

bool LLMInstanceManager::loadConfigurations() {
    try {
        std::filesystem::path config_dir(config_path_);
        std::filesystem::path instances_dir = config_dir / "instances";
        
        if (!std::filesystem::exists(instances_dir)) {
            std::filesystem::create_directories(instances_dir);
            return true;
        }
        
        for (const auto& entry : std::filesystem::directory_iterator(instances_dir)) {
            if (entry.path().extension() == ".json") {
                std::ifstream file(entry.path());
                nlohmann::json config;
                file >> config;
                
                std::string model_id = config["model_id"];
                auto instance = std::make_shared<LLMInstance>(model_id, config);
                if (instance->initialize()) {
                    instances_[model_id] = instance;
                }
            }
        }
        
        return true;
    } catch (const std::exception& e) {
        // Log error
        return false;
    }
}

bool LLMInstanceManager::saveConfigurations() {
    try {
        std::filesystem::path config_dir(config_path_);
        std::filesystem::path instances_dir = config_dir / "instances";
        
        if (!std::filesystem::exists(instances_dir)) {
            std::filesystem::create_directories(instances_dir);
        }
        
        for (const auto& [model_id, instance] : instances_) {
            std::filesystem::path config_path = instances_dir / (model_id + ".json");
            std::ofstream file(config_path);
            file << instance->getConfig().dump(4);
        }
        
        return true;
    } catch (const std::exception& e) {
        // Log error
        return false;
    }
}

void LLMInstanceManager::monitorResources() {
    while (running_) {
        {
            std::lock_guard<std::mutex> lock(mutex_);
            
            for (auto& [model_id, instance] : instances_) {
                instance->updateResourceUsage();
            }
        }
        
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }
}

} // namespace cogniware
