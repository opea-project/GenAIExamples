#pragma once

#include <string>
#include <vector>
#include <memory>
#include <unordered_map>
#include <chrono>

namespace cogniware {
namespace model {

enum class ModelStatus {
    UNLOADED,
    LOADING,
    LOADED,
    UNLOADING,
    ERROR
};

struct ModelVersion {
    std::string version;
    std::string path;
    std::chrono::system_clock::time_point created_at;
    size_t size_bytes;
    std::string checksum;
};

struct ModelMetadata {
    std::string model_id;
    std::string name;
    std::string type;
    std::vector<ModelVersion> versions;
    ModelStatus status;
    int device_id;
    std::string current_version;
};

class ModelManager {
public:
    ModelManager();
    ~ModelManager();

    std::string registerModel(const ModelMetadata& metadata);
    bool unregisterModel(const std::string& model_id);
    
    bool loadModel(const std::string& model_id, const std::string& version = "latest");
    bool unloadModel(const std::string& model_id);
    
    bool deployVersion(const std::string& model_id, const std::string& version);
    bool rollback(const std::string& model_id);
    
    ModelMetadata getModelInfo(const std::string& model_id);
    std::vector<ModelMetadata> listModels();
    
    std::string addVersion(const std::string& model_id, const ModelVersion& version);
    bool removeVersion(const std::string& model_id, const std::string& version);

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

} // namespace model
} // namespace cogniware

