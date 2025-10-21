#include "model_config_manager.hpp"
#include <fstream>
#include <filesystem>
#include <iostream>

namespace cogniware {

ModelConfigManager& ModelConfigManager::getInstance() {
    static ModelConfigManager instance;
    return instance;
}

bool ModelConfigManager::initialize(const std::string& config_path) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    config_path_ = config_path;
    schema_path_ = config_path_ + "/schemas";
    models_path_ = config_path_ + "/models";
    
    // Create directories if they don't exist
    std::filesystem::create_directories(schema_path_);
    std::filesystem::create_directories(models_path_);
    
    // Load schema
    if (!loadSchema(schema_path_ + "/model_config_schema.json")) {
        std::cerr << "Failed to load schema" << std::endl;
        return false;
    }
    
    // Load existing configurations
    if (!loadConfigurations()) {
        std::cerr << "Failed to load configurations" << std::endl;
        return false;
    }
    
    return true;
}

bool ModelConfigManager::registerModel(const ModelConfig& config) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Convert to JSON for validation
    nlohmann::json config_json = {
        {"model_id", config.model_id},
        {"model_type", config.model_type},
        {"model_config", config.model_config}
    };
    
    if (!validateConfig(config_json)) {
        return false;
    }
    
    // Add to registry
    registry_[config.model_id] = std::make_shared<ModelConfig>(config);
    
    // Save to file
    return saveConfig(config.model_id, config_json);
}

std::shared_ptr<ModelConfig> ModelConfigManager::getModelConfig(const std::string& model_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = registry_.find(model_id);
    return it != registry_.end() ? it->second : nullptr;
}

bool ModelConfigManager::updateModelConfig(const std::string& model_id, const nlohmann::json& updates) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = registry_.find(model_id);
    if (it == registry_.end()) {
        return false;
    }
    
    // Create updated config
    nlohmann::json current_config = {
        {"model_id", it->second->model_id},
        {"model_type", it->second->model_type},
        {"model_config", it->second->model_config}
    };
    
    // Apply updates
    current_config.merge_patch(updates);
    
    if (!validateConfig(current_config)) {
        return false;
    }
    
    // Update registry
    it->second->model_id = current_config["model_id"];
    it->second->model_type = current_config["model_type"];
    it->second->model_config = current_config["model_config"];
    
    // Save to file
    return saveConfig(model_id, current_config);
}

std::vector<std::string> ModelConfigManager::listModels() {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<std::string> model_ids;
    model_ids.reserve(registry_.size());
    
    for (const auto& pair : registry_) {
        model_ids.push_back(pair.first);
    }
    
    return model_ids;
}

std::string ModelConfigManager::getModelType(const std::string& model_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = registry_.find(model_id);
    return it != registry_.end() ? it->second->model_type : "";
}

nlohmann::json ModelConfigManager::getModelArchitecture(const std::string& model_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = registry_.find(model_id);
    if (it == registry_.end()) {
        return nlohmann::json();
    }
    return it->second->model_config.value("architecture", nlohmann::json());
}

nlohmann::json ModelConfigManager::getModelParameters(const std::string& model_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = registry_.find(model_id);
    if (it == registry_.end()) {
        return nlohmann::json();
    }
    return it->second->model_config.value("parameters", nlohmann::json());
}

nlohmann::json ModelConfigManager::getTokenizerConfig(const std::string& model_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = registry_.find(model_id);
    if (it == registry_.end()) {
        return nlohmann::json();
    }
    return it->second->model_config.value("tokenizer", nlohmann::json());
}

nlohmann::json ModelConfigManager::getGenerationConfig(const std::string& model_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = registry_.find(model_id);
    if (it == registry_.end()) {
        return nlohmann::json();
    }
    return it->second->model_config.value("generation", nlohmann::json());
}

nlohmann::json ModelConfigManager::getQuantizationConfig(const std::string& model_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = registry_.find(model_id);
    if (it == registry_.end()) {
        return nlohmann::json();
    }
    return it->second->model_config.value("quantization", nlohmann::json());
}

nlohmann::json ModelConfigManager::getOptimizationConfig(const std::string& model_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = registry_.find(model_id);
    if (it == registry_.end()) {
        return nlohmann::json();
    }
    return it->second->model_config.value("optimization", nlohmann::json());
}

nlohmann::json ModelConfigManager::getModelMetadata(const std::string& model_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = registry_.find(model_id);
    if (it == registry_.end()) {
        return nlohmann::json();
    }
    return it->second->model_config.value("metadata", nlohmann::json());
}

bool ModelConfigManager::loadSchema(const std::string& schema_file) {
    try {
        std::ifstream file(schema_file);
        if (!file.is_open()) {
            std::cerr << "Failed to open schema file: " << schema_file << std::endl;
            return false;
        }
        file >> schema_;
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Error loading schema: " << e.what() << std::endl;
        return false;
    }
}

bool ModelConfigManager::loadConfigurations() {
    try {
        for (const auto& entry : std::filesystem::directory_iterator(models_path_)) {
            if (entry.path().extension() == ".json") {
                std::ifstream file(entry.path());
                if (!file.is_open()) {
                    std::cerr << "Failed to open config file: " << entry.path() << std::endl;
                    continue;
                }
                
                nlohmann::json config_json;
                file >> config_json;
                
                if (!validateConfig(config_json)) {
                    std::cerr << "Invalid config in file: " << entry.path() << std::endl;
                    continue;
                }
                
                ModelConfig config;
                config.model_id = config_json["model_id"];
                config.model_type = config_json["model_type"];
                config.model_config = config_json["model_config"];
                
                registry_[config.model_id] = std::make_shared<ModelConfig>(config);
            }
        }
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Error loading configurations: " << e.what() << std::endl;
        return false;
    }
}

bool ModelConfigManager::validateConfig(const nlohmann::json& config) {
    try {
        // Load JSON Schema
        static const nlohmann::json schema = {
            {"type", "object"},
            {"required", {"name", "type", "version", "parameters"}},
            {"properties", {
                {"name", {"type", "string"}},
                {"type", {"type", "string", "enum", {"llm", "embedding", "classification"}}},
                {"version", {"type", "string"}},
                {"description", {"type", "string"}},
                {"parameters", {
                    {"type", "object"},
                    {"required", {"model_path", "vocab_path", "max_sequence_length"}},
                    {"properties", {
                        {"model_path", {"type", "string"}},
                        {"vocab_path", {"type", "string"}},
                        {"max_sequence_length", {"type", "integer", "minimum", 1}},
                        {"batch_size", {"type", "integer", "minimum", 1}},
                        {"precision", {"type", "string", "enum", {"fp32", "fp16", "int8"}}},
                        {"device", {"type", "string", "enum", {"cpu", "cuda", "rocm"}}},
                        {"quantization", {
                            "type", "object",
                            "properties", {
                                {"enabled", {"type", "boolean"}},
                                {"method", {"type", "string", "enum", {"int8", "int4"}}},
                                {"calibration_data", {"type", "string"}}
                            }
                        }}
                    }}
                }},
                {"hyperparameters", {
                    "type", "object",
                    "properties", {
                        {"learning_rate", {"type", "number", "minimum", 0}},
                        {"batch_size", {"type", "integer", "minimum", 1}},
                        {"epochs", {"type", "integer", "minimum", 1}},
                        {"optimizer", {"type", "string", "enum", {"adam", "sgd", "adamw"}}},
                        {"scheduler", {"type", "string", "enum", {"cosine", "linear", "constant"}}}
                    }
                }}
            }}
        };

        // Validate against schema
        if (!validateJsonSchema(config, schema)) {
            logger_->error("Config validation failed: Invalid schema");
            return false;
        }

        // Additional validation rules
        if (config["type"] == "llm") {
            // LLM-specific validation
            if (!config["parameters"].contains("num_layers") ||
                !config["parameters"].contains("hidden_size") ||
                !config["parameters"].contains("num_heads")) {
                logger_->error("LLM config missing required parameters");
                return false;
            }
        } else if (config["type"] == "embedding") {
            // Embedding-specific validation
            if (!config["parameters"].contains("embedding_dim")) {
                logger_->error("Embedding config missing required parameters");
                return false;
            }
        }

        return true;
    } catch (const std::exception& e) {
        logger_->error("Config validation failed: {}", e.what());
        return false;
    }
}

bool ModelConfigManager::validateJsonSchema(const nlohmann::json& data, const nlohmann::json& schema) {
    try {
        // Type validation
        if (schema.contains("type")) {
            if (schema["type"] == "object" && !data.is_object()) return false;
            if (schema["type"] == "array" && !data.is_array()) return false;
            if (schema["type"] == "string" && !data.is_string()) return false;
            if (schema["type"] == "number" && !data.is_number()) return false;
            if (schema["type"] == "integer" && !data.is_number_integer()) return false;
            if (schema["type"] == "boolean" && !data.is_boolean()) return false;
        }

        // Required fields validation
        if (schema.contains("required")) {
            for (const auto& field : schema["required"]) {
                if (!data.contains(field)) return false;
            }
        }

        // Properties validation
        if (schema.contains("properties")) {
            for (const auto& [key, value] : schema["properties"].items()) {
                if (data.contains(key)) {
                    if (!validateJsonSchema(data[key], value)) return false;
                }
            }
        }

        // Enum validation
        if (schema.contains("enum")) {
            bool found = false;
            for (const auto& value : schema["enum"]) {
                if (data == value) {
                    found = true;
                    break;
                }
            }
            if (!found) return false;
        }

        // Minimum value validation
        if (schema.contains("minimum")) {
            if (data.is_number() && data < schema["minimum"]) return false;
        }

        return true;
    } catch (const std::exception&) {
        return false;
    }
}

bool ModelConfigManager::saveConfig(const std::string& model_id, const nlohmann::json& config) {
    try {
        std::string filename = models_path_ + "/model_config_" + model_id + ".json";
        std::ofstream file(filename);
        if (!file.is_open()) {
            std::cerr << "Failed to open file for writing: " << filename << std::endl;
            return false;
        }
        file << config.dump(4);
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Error saving config: " << e.what() << std::endl;
        return false;
    }
}

} // namespace cogniware 