#pragma once

#include <string>
#include <vector>
#include <memory>
#include <mutex>
#include <unordered_map>
#include <functional>
#include <future>
#include "utils/error_handler_cpp.h"
#include "utils/logger_cpp.h"

namespace cogniware {
namespace dream {

// Search result structure
struct SearchResult {
    std::string id;
    float score;
    std::vector<float> vector;
    std::unordered_map<std::string, std::string> metadata;

    SearchResult() : score(0.0f) {}
};

// Search options
struct SearchOptions {
    size_t top_k;
    float score_threshold;
    bool include_vectors;
    bool include_metadata;
    std::unordered_map<std::string, std::string> filter;

    SearchOptions() :
        top_k(10),
        score_threshold(0.0f),
        include_vectors(false),
        include_metadata(false) {}
};

// Index configuration
struct IndexConfig {
    std::string name;
    size_t dimension;
    std::string metric_type;  // "cosine", "euclidean", "dot"
    size_t max_elements;
    bool normalize_vectors;
    std::unordered_map<std::string, std::string> parameters;

    IndexConfig() :
        dimension(0),
        max_elements(1000000),
        normalize_vectors(true) {}
};

// Vector search client class
class VectorSearchClient {
public:
    static VectorSearchClient& getInstance();

    // Prevent copying
    VectorSearchClient(const VectorSearchClient&) = delete;
    VectorSearchClient& operator=(const VectorSearchClient&) = delete;

    // Initialization
    bool initialize(const std::string& host, int port);
    void shutdown();
    bool isInitialized() const;

    // Index management
    bool createIndex(const IndexConfig& config);
    bool deleteIndex(const std::string& index_name);
    bool indexExists(const std::string& index_name) const;
    std::vector<std::string> listIndexes() const;
    IndexConfig getIndexConfig(const std::string& index_name) const;

    // Vector operations
    bool insertVectors(const std::string& index_name,
                      const std::vector<std::string>& ids,
                      const std::vector<std::vector<float>>& vectors,
                      const std::vector<std::unordered_map<std::string, std::string>>& metadata = {});
    
    bool deleteVectors(const std::string& index_name,
                      const std::vector<std::string>& ids);
    
    bool updateVectors(const std::string& index_name,
                      const std::vector<std::string>& ids,
                      const std::vector<std::vector<float>>& vectors,
                      const std::vector<std::unordered_map<std::string, std::string>>& metadata = {});

    // Search operations
    std::vector<SearchResult> search(const std::string& index_name,
                                   const std::vector<float>& query_vector,
                                   const SearchOptions& options = SearchOptions());

    std::vector<std::vector<SearchResult>> batchSearch(const std::string& index_name,
                                                     const std::vector<std::vector<float>>& query_vectors,
                                                     const SearchOptions& options = SearchOptions());

    // Asynchronous operations
    std::future<bool> insertVectorsAsync(const std::string& index_name,
                                       const std::vector<std::string>& ids,
                                       const std::vector<std::vector<float>>& vectors,
                                       const std::vector<std::unordered_map<std::string, std::string>>& metadata = {});
    
    std::future<bool> deleteVectorsAsync(const std::string& index_name,
                                       const std::vector<std::string>& ids);
    
    std::future<bool> updateVectorsAsync(const std::string& index_name,
                                       const std::vector<std::string>& ids,
                                       const std::vector<std::vector<float>>& vectors,
                                       const std::vector<std::unordered_map<std::string, std::string>>& metadata = {});
    
    std::future<std::vector<SearchResult>> searchAsync(const std::string& index_name,
                                                     const std::vector<float>& query_vector,
                                                     const SearchOptions& options = SearchOptions());
    
    std::future<std::vector<std::vector<SearchResult>>> batchSearchAsync(const std::string& index_name,
                                                                       const std::vector<std::vector<float>>& query_vectors,
                                                                       const SearchOptions& options = SearchOptions());

    // Statistics and monitoring
    struct IndexStats {
        size_t total_vectors;
        size_t deleted_vectors;
        size_t memory_usage;
        float average_vector_size;
        std::chrono::system_clock::time_point last_update;
    };

    IndexStats getIndexStats(const std::string& index_name) const;
    std::unordered_map<std::string, IndexStats> getAllIndexStats() const;

public:
    VectorSearchClient();
    ~VectorSearchClient();
    
private:

    bool validateIndexConfig(const IndexConfig& config) const;
    bool validateVectors(const std::vector<std::vector<float>>& vectors, size_t dimension) const;
    bool validateMetadata(const std::vector<std::unordered_map<std::string, std::string>>& metadata,
                         size_t expected_size) const;

    std::string host_;
    int port_;
    bool initialized_;
    std::mutex mutex_;
    std::unordered_map<std::string, IndexConfig> index_configs_;
};

} // namespace dream
} // namespace cogniware
