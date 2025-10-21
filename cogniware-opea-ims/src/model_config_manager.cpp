#include "model_config_manager.h"
#include <fstream>
#include <sstream>
#include <stdexcept>

namespace cogniware {

void ModelConfigManager::load_config(const std::string& config_path) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    try {
        // Open and read configuration file
        std::ifstream file(config_path);
        if (!file) {
            throw std::runtime_error("Failed to open configuration file: " + config_path);
        }
        
        // Parse JSON
        Json::Value root;
        Json::Reader reader;
        if (!reader.parse(file, root)) {
            throw std::runtime_error("Failed to parse configuration file: " + 
                                   reader.getFormattedErrorMessages());
        }
        
        // Store file path
        config_file_path_ = config_path;
        
        // Load configurations
        for (const auto& model_name : root.getMemberNames()) {
            configs_[model_name] = parse_config(root[model_name]);
        }
    } catch (const std::exception& e) {
        throw std::runtime_error("Error loading model configurations: " + 
                               std::string(e.what()));
    }
}

LLMConfig ModelConfigManager::get_config(const std::string& model_name) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = configs_.find(model_name);
    if (it == configs_.end()) {
        throw std::runtime_error("Model configuration not found: " + model_name);
    }
    
    return it->second;
}

bool ModelConfigManager::has_config(const std::string& model_name) const {
    std::lock_guard<std::mutex> lock(mutex_);
    return configs_.find(model_name) != configs_.end();
}

std::vector<std::string> ModelConfigManager::list_models() const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    std::vector<std::string> models;
    models.reserve(configs_.size());
    
    for (const auto& [name, _] : configs_) {
        models.push_back(name);
    }
    
    return models;
}

void ModelConfigManager::update_config(const std::string& model_name, 
                                     const LLMConfig& config) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    configs_[model_name] = config;
    save_configs();
}

void ModelConfigManager::remove_config(const std::string& model_name) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (configs_.erase(model_name) > 0) {
        save_configs();
    }
}

LLMConfig ModelConfigManager::parse_config(const Json::Value& json_config) const {
    LLMConfig config;
    
    // Parse required fields
    config.max_sequence_length = json_config["max_sequence_length"].asInt();
    config.vocab_size = json_config["vocab_size"].asInt();
    config.hidden_size = json_config["hidden_size"].asInt();
    config.num_layers = json_config["num_layers"].asInt();
    config.num_heads = json_config["num_heads"].asInt();
    config.dropout_rate = json_config["dropout_rate"].asFloat();
    config.use_fp16 = json_config["use_fp16"].asBool();
    
    return config;
}

void ModelConfigManager::save_configs() const {
    if (config_file_path_.empty()) {
        throw std::runtime_error("No configuration file path set");
    }
    
    try {
        // Create JSON root object
        Json::Value root;
        
        // Add each configuration
        for (const auto& [name, config] : configs_) {
            Json::Value json_config;
            json_config["max_sequence_length"] = config.max_sequence_length;
            json_config["vocab_size"] = config.vocab_size;
            json_config["hidden_size"] = config.hidden_size;
            json_config["num_layers"] = config.num_layers;
            json_config["num_heads"] = config.num_heads;
            json_config["dropout_rate"] = config.dropout_rate;
            json_config["use_fp16"] = config.use_fp16;
            
            root[name] = json_config;
        }
        
        // Write to file
        std::ofstream file(config_file_path_);
        if (!file) {
            throw std::runtime_error("Failed to open configuration file for writing: " + 
                                   config_file_path_);
        }
        
        Json::StyledWriter writer;
        file << writer.write(root);
    } catch (const std::exception& e) {
        throw std::runtime_error("Error saving model configurations: " + 
                               std::string(e.what()));
    }
}

} // namespace cogniware 