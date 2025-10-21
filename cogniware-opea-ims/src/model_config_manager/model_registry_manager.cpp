#include "model_registry_manager.hpp"
#include <fstream>
#include <filesystem>
#include <spdlog/spdlog.h>

namespace cogniware {

ModelRegistryManager& ModelRegistryManager::getInstance() {
    static ModelRegistryManager instance;
    return instance;
}

bool ModelRegistryManager::initialize(const std::string& config_path) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    try {
        config_path_ = config_path;
        
        // Load schema
        std::filesystem::path schema_path = std::filesystem::path(config_path) / "schemas" / "model_registry_schema.json";
        std::ifstream schema_file(schema_path);
        if (!schema_file.is_open()) {
            spdlog::error("Failed to open schema file: {}", schema_path.string());
            return false;
        }
        schema_ = nlohmann::json::parse(schema_file);
        
        // Load registry
        std::filesystem::path registry_path = std::filesystem::path(config_path) / "models" / "registry.json";
        if (std::filesystem::exists(registry_path)) {
            if (!loadRegistry(registry_path.string())) {
                spdlog::error("Failed to load registry from: {}", registry_path.string());
                return false;
            }
        }
        
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Error initializing model registry manager: {}", e.what());
        return false;
    }
}

bool ModelRegistryManager::registerModel(const ModelRegistryEntry& entry) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    try {
        if (!validateModelEntry(entry)) {
            spdlog::error("Invalid model entry for model: {}", entry.model_id);
            return false;
        }
        
        registry_[entry.model_id] = entry;
        
        // Save registry
        std::filesystem::path registry_path = std::filesystem::path(config_path_) / "models" / "registry.json";
        if (!saveRegistry(registry_path.string())) {
            spdlog::error("Failed to save registry to: {}", registry_path.string());
            return false;
        }
        
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Error registering model: {}", e.what());
        return false;
    }
}

const ModelRegistryEntry* ModelRegistryManager::getModelEntry(const std::string& model_id) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = registry_.find(model_id);
    if (it == registry_.end()) {
        return nullptr;
    }
    
    return &it->second;
}

bool ModelRegistryManager::updateModelEntry(const std::string& model_id, const nlohmann::json& updates) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    try {
        auto it = registry_.find(model_id);
        if (it == registry_.end()) {
            spdlog::error("Model not found: {}", model_id);
            return false;
        }
        
        // Convert current entry to JSON
        nlohmann::json current = nlohmann::json{
            {"model_id", it->second.model_id},
            {"model_name", it->second.model_name},
            {"model_family", it->second.model_family},
            {"model_type", it->second.model_type},
            {"version", it->second.version},
            {"status", it->second.status},
            {"path_to_model_files", it->second.path_to_model_files},
            {"required_vram_mb", it->second.required_vram_mb},
            {"supported_features", it->second.supported_features},
            {"model_parameters", it->second.model_parameters},
            {"quantization", it->second.quantization},
            {"performance_metrics", it->second.performance_metrics},
            {"dependencies", it->second.dependencies},
            {"metadata", it->second.metadata}
        };
        
        // Apply updates
        current.merge_patch(updates);
        
        // Validate updated entry
        if (!validateModelEntry(ModelRegistryEntry{
            current["model_id"].get<std::string>(),
            current["model_name"].get<std::string>(),
            current["model_family"].get<std::string>(),
            current["model_type"].get<std::string>(),
            current["version"].get<std::string>(),
            current["status"].get<std::string>(),
            current["path_to_model_files"].get<std::string>(),
            current["required_vram_mb"].get<int>(),
            current["supported_features"].get<std::vector<std::string>>(),
            current["model_parameters"],
            current["quantization"],
            current["performance_metrics"],
            current["dependencies"],
            current["metadata"]
        })) {
            spdlog::error("Invalid model entry after update for model: {}", model_id);
            return false;
        }
        
        // Update registry
        it->second = ModelRegistryEntry{
            current["model_id"].get<std::string>(),
            current["model_name"].get<std::string>(),
            current["model_family"].get<std::string>(),
            current["model_type"].get<std::string>(),
            current["version"].get<std::string>(),
            current["status"].get<std::string>(),
            current["path_to_model_files"].get<std::string>(),
            current["required_vram_mb"].get<int>(),
            current["supported_features"].get<std::vector<std::string>>(),
            current["model_parameters"],
            current["quantization"],
            current["performance_metrics"],
            current["dependencies"],
            current["metadata"]
        };
        
        // Save registry
        std::filesystem::path registry_path = std::filesystem::path(config_path_) / "models" / "registry.json";
        if (!saveRegistry(registry_path.string())) {
            spdlog::error("Failed to save registry to: {}", registry_path.string());
            return false;
        }
        
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Error updating model entry: {}", e.what());
        return false;
    }
}

std::vector<std::string> ModelRegistryManager::listModels() const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    std::vector<std::string> model_ids;
    model_ids.reserve(registry_.size());
    
    for (const auto& [id, _] : registry_) {
        model_ids.push_back(id);
    }
    
    return model_ids;
}

nlohmann::json ModelRegistryManager::getModelMetadata(const std::string& model_id) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = registry_.find(model_id);
    if (it == registry_.end()) {
        return nlohmann::json();
    }
    
    return it->second.metadata;
}

nlohmann::json ModelRegistryManager::getModelPerformance(const std::string& model_id) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = registry_.find(model_id);
    if (it == registry_.end()) {
        return nlohmann::json();
    }
    
    return it->second.performance_metrics;
}

bool ModelRegistryManager::validateModelEntry(const ModelRegistryEntry& entry) const {
    try {
        nlohmann::json entry_json = nlohmann::json{
            {"model_id", entry.model_id},
            {"model_name", entry.model_name},
            {"model_family", entry.model_family},
            {"model_type", entry.model_type},
            {"version", entry.version},
            {"status", entry.status},
            {"path_to_model_files", entry.path_to_model_files},
            {"required_vram_mb", entry.required_vram_mb},
            {"supported_features", entry.supported_features},
            {"model_parameters", entry.model_parameters},
            {"quantization", entry.quantization},
            {"performance_metrics", entry.performance_metrics},
            {"dependencies", entry.dependencies},
            {"metadata", entry.metadata}
        };
        
        // Validate against schema
        return true; // TODO: Implement schema validation
    } catch (const std::exception& e) {
        spdlog::error("Error validating model entry: {}", e.what());
        return false;
    }
}

bool ModelRegistryManager::loadRegistry(const std::string& file_path) {
    try {
        std::ifstream file(file_path);
        if (!file.is_open()) {
            spdlog::error("Failed to open registry file: {}", file_path);
            return false;
        }
        
        nlohmann::json registry_json = nlohmann::json::parse(file);
        
        for (const auto& [id, entry] : registry_json.items()) {
            ModelRegistryEntry model_entry{
                entry["model_id"].get<std::string>(),
                entry["model_name"].get<std::string>(),
                entry["model_family"].get<std::string>(),
                entry["model_type"].get<std::string>(),
                entry["version"].get<std::string>(),
                entry["status"].get<std::string>(),
                entry["path_to_model_files"].get<std::string>(),
                entry["required_vram_mb"].get<int>(),
                entry["supported_features"].get<std::vector<std::string>>(),
                entry["model_parameters"],
                entry["quantization"],
                entry["performance_metrics"],
                entry["dependencies"],
                entry["metadata"]
            };
            
            registry_[id] = model_entry;
        }
        
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Error loading registry: {}", e.what());
        return false;
    }
}

bool ModelRegistryManager::saveRegistry(const std::string& file_path) const {
    try {
        nlohmann::json registry_json;
        
        for (const auto& [id, entry] : registry_) {
            registry_json[id] = nlohmann::json{
                {"model_id", entry.model_id},
                {"model_name", entry.model_name},
                {"model_family", entry.model_family},
                {"model_type", entry.model_type},
                {"version", entry.version},
                {"status", entry.status},
                {"path_to_model_files", entry.path_to_model_files},
                {"required_vram_mb", entry.required_vram_mb},
                {"supported_features", entry.supported_features},
                {"model_parameters", entry.model_parameters},
                {"quantization", entry.quantization},
                {"performance_metrics", entry.performance_metrics},
                {"dependencies", entry.dependencies},
                {"metadata", entry.metadata}
            };
        }
        
        std::ofstream file(file_path);
        if (!file.is_open()) {
            spdlog::error("Failed to open registry file for writing: {}", file_path);
            return false;
        }
        
        file << registry_json.dump(2);
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Error saving registry: {}", e.what());
        return false;
    }
}

} // namespace cogniware 