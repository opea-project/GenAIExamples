#include "model/model_manager.h"
#include <mutex>

namespace cogniware {
namespace model {

class ModelManager::Impl {
public:
    std::unordered_map<std::string, ModelMetadata> models;
    mutable std::mutex mutex;
};

ModelManager::ModelManager() : pImpl(std::make_unique<Impl>()) {}
ModelManager::~ModelManager() = default;

std::string ModelManager::registerModel(const ModelMetadata& metadata) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    pImpl->models[metadata.model_id] = metadata;
    return metadata.model_id;
}

bool ModelManager::unregisterModel(const std::string& model_id) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    return pImpl->models.erase(model_id) > 0;
}

bool ModelManager::loadModel(const std::string& model_id, const std::string& version) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    auto it = pImpl->models.find(model_id);
    if (it != pImpl->models.end()) {
        it->second.status = ModelStatus::LOADED;
        it->second.current_version = version;
        return true;
    }
    return false;
}

bool ModelManager::unloadModel(const std::string& model_id) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    auto it = pImpl->models.find(model_id);
    if (it != pImpl->models.end()) {
        it->second.status = ModelStatus::UNLOADED;
        return true;
    }
    return false;
}

bool ModelManager::deployVersion(const std::string& model_id, const std::string& version) {
    return loadModel(model_id, version);
}

bool ModelManager::rollback(const std::string& model_id) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    auto it = pImpl->models.find(model_id);
    if (it != pImpl->models.end() && it->second.versions.size() > 1) {
        it->second.current_version = it->second.versions[it->second.versions.size() - 2].version;
        return true;
    }
    return false;
}

ModelMetadata ModelManager::getModelInfo(const std::string& model_id) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    auto it = pImpl->models.find(model_id);
    return (it != pImpl->models.end()) ? it->second : ModelMetadata{};
}

std::vector<ModelMetadata> ModelManager::listModels() {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    std::vector<ModelMetadata> result;
    for (const auto& [id, metadata] : pImpl->models) {
        result.push_back(metadata);
    }
    return result;
}

std::string ModelManager::addVersion(const std::string& model_id, const ModelVersion& version) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    auto it = pImpl->models.find(model_id);
    if (it != pImpl->models.end()) {
        it->second.versions.push_back(version);
        return version.version;
    }
    return "";
}

bool ModelManager::removeVersion(const std::string& model_id, const std::string& version) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    auto it = pImpl->models.find(model_id);
    if (it != pImpl->models.end()) {
        auto& versions = it->second.versions;
        versions.erase(std::remove_if(versions.begin(), versions.end(),
            [&](const ModelVersion& v) { return v.version == version; }), versions.end());
        return true;
    }
    return false;
}

} // namespace model
} // namespace cogniware

