#include "vector_search_client_cpp.h"
#include <grpcpp/grpcpp.h>
#include <grpcpp/health_check_service_interface.h>
#include <grpcpp/ext/proto_server_reflection_plugin.h>
#include <thread>
#include <chrono>
#include <algorithm>

namespace cogniware {
namespace dream {

VectorSearchClient& VectorSearchClient::getInstance() {
    static VectorSearchClient instance;
    return instance;
}

VectorSearchClient::VectorSearchClient() : 
    port_(0),
    initialized_(false) {
}

VectorSearchClient::~VectorSearchClient() {
    shutdown();
}

bool VectorSearchClient::initialize(const std::string& host, int port) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (initialized_) {
        LOG_WARN("Vector search client already initialized");
        return false;
    }

    try {
        host_ = host;
        port_ = port;
        
        // TODO: Initialize gRPC channel and stub
        // channel_ = grpc::CreateChannel(host + ":" + std::to_string(port), grpc::InsecureChannelCredentials());
        // stub_ = VectorSearchService::NewStub(channel_);
        
        initialized_ = true;
        LOG_INFO("Vector search client initialized with host: {} and port: {}", host, port);
        return true;
    } catch (const std::exception& e) {
        LOG_ERROR("Failed to initialize vector search client: {}", e.what());
        return false;
    }
}

void VectorSearchClient::shutdown() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!initialized_) {
        return;
    }

    try {
        // TODO: Cleanup gRPC resources
        // channel_.reset();
        // stub_.reset();
        
        initialized_ = false;
        LOG_INFO("Vector search client shut down");
    } catch (const std::exception& e) {
        LOG_ERROR("Error during vector search client shutdown: {}", e.what());
    }
}

bool VectorSearchClient::isInitialized() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return initialized_;
}

bool VectorSearchClient::createIndex(const IndexConfig& config) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!initialized_) {
        LOG_ERROR("Vector search client not initialized");
        return false;
    }

    if (!validateIndexConfig(config)) {
        LOG_ERROR("Invalid index configuration");
        return false;
    }

    try {
        // TODO: Implement index creation using gRPC
        // CreateIndexRequest request;
        // request.set_name(config.name);
        // request.set_dimension(config.dimension);
        // request.set_metric_type(config.metric_type);
        // request.set_max_elements(config.max_elements);
        // request.set_normalize_vectors(config.normalize_vectors);
        
        // for (const auto& [key, value] : config.parameters) {
        //     (*request.mutable_parameters())[key] = value;
        // }
        
        // CreateIndexResponse response;
        // grpc::ClientContext context;
        // grpc::Status status = stub_->CreateIndex(&context, request, &response);
        
        // if (!status.ok()) {
        //     LOG_ERROR("Failed to create index: {}", status.error_message());
        //     return false;
        // }

        index_configs_[config.name] = config;
        LOG_INFO("Index created successfully: {}", config.name);
        return true;
    } catch (const std::exception& e) {
        LOG_ERROR("Error creating index: {}", e.what());
        return false;
    }
}

bool VectorSearchClient::deleteIndex(const std::string& index_name) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!initialized_) {
        LOG_ERROR("Vector search client not initialized");
        return false;
    }

    try {
        // TODO: Implement index deletion using gRPC
        // DeleteIndexRequest request;
        // request.set_name(index_name);
        
        // DeleteIndexResponse response;
        // grpc::ClientContext context;
        // grpc::Status status = stub_->DeleteIndex(&context, request, &response);
        
        // if (!status.ok()) {
        //     LOG_ERROR("Failed to delete index: {}", status.error_message());
        //     return false;
        // }

        index_configs_.erase(index_name);
        LOG_INFO("Index deleted successfully: {}", index_name);
        return true;
    } catch (const std::exception& e) {
        LOG_ERROR("Error deleting index: {}", e.what());
        return false;
    }
}

bool VectorSearchClient::indexExists(const std::string& index_name) const {
    std::lock_guard<std::mutex> lock(mutex_);
    return index_configs_.find(index_name) != index_configs_.end();
}

std::vector<std::string> VectorSearchClient::listIndexes() const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<std::string> result;
    result.reserve(index_configs_.size());
    
    for (const auto& [name, _] : index_configs_) {
        result.push_back(name);
    }
    
    return result;
}

IndexConfig VectorSearchClient::getIndexConfig(const std::string& index_name) const {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = index_configs_.find(index_name);
    if (it == index_configs_.end()) {
        return IndexConfig();
    }
    return it->second;
}

bool VectorSearchClient::validateIndexConfig(const IndexConfig& config) const {
    if (config.name.empty()) {
        LOG_ERROR("Index name cannot be empty");
        return false;
    }

    if (config.dimension == 0) {
        LOG_ERROR("Index dimension must be greater than 0");
        return false;
    }

    if (config.metric_type != "cosine" && 
        config.metric_type != "euclidean" && 
        config.metric_type != "dot") {
        LOG_ERROR("Invalid metric type: {}", config.metric_type);
        return false;
    }

    if (config.max_elements == 0) {
        LOG_ERROR("Max elements must be greater than 0");
        return false;
    }

    return true;
}

bool VectorSearchClient::validateVectors(const std::vector<std::vector<float>>& vectors, size_t dimension) const {
    if (vectors.empty()) {
        LOG_ERROR("Vector list cannot be empty");
        return false;
    }

    for (const auto& vector : vectors) {
        if (vector.size() != dimension) {
            LOG_ERROR("Vector dimension mismatch: expected {}, got {}", dimension, vector.size());
            return false;
        }
    }

    return true;
}

bool VectorSearchClient::validateMetadata(const std::vector<std::unordered_map<std::string, std::string>>& metadata,
                                        size_t expected_size) const {
    if (metadata.empty()) {
        return true;
    }

    if (metadata.size() != expected_size) {
        LOG_ERROR("Metadata size mismatch: expected {}, got {}", expected_size, metadata.size());
        return false;
    }

    return true;
}

} // namespace dream
} // namespace cogniware
