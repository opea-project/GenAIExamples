/**
 * @file gguf_loader.hpp
 * @brief GGUF model loader for the cogniware engine
 */

#ifndef MSMARTCOMPUTE_GGUF_LOADER_HPP
#define MSMARTCOMPUTE_GGUF_LOADER_HPP

#include <string>
#include <memory>
#include <vector>
#include <unordered_map>
#include <nlohmann/json.hpp>

namespace cogniware {

/**
 * @brief Class for loading and managing GGUF model files
 */
class GGUFLoader {
public:
    /**
     * @brief Constructor
     * @param model_path Path to the GGUF model file
     */
    explicit GGUFLoader(const std::string& model_path);
    
    /**
     * @brief Destructor
     */
    ~GGUFLoader();
    
    /**
     * @brief Load the model
     * @return true if loading successful, false otherwise
     */
    bool load();
    
    /**
     * @brief Unload the model
     */
    void unload();
    
    /**
     * @brief Get model metadata
     * @return JSON object containing model metadata
     */
    nlohmann::json getMetadata() const;
    
    /**
     * @brief Get model parameters
     * @return JSON object containing model parameters
     */
    nlohmann::json getParameters() const;
    
    /**
     * @brief Get model tensors
     * @return Vector of tensor data
     */
    std::vector<float> getTensors() const;
    
    /**
     * @brief Get model vocabulary
     * @return Map of token IDs to token strings
     */
    std::unordered_map<int, std::string> getVocabulary() const;
    
    /**
     * @brief Get model architecture
     * @return String describing the model architecture
     */
    std::string getArchitecture() const;
    
    /**
     * @brief Get model context size
     * @return Maximum context size in tokens
     */
    size_t getContextSize() const;
    
    /**
     * @brief Get model embedding dimension
     * @return Embedding dimension size
     */
    size_t getEmbeddingDim() const;
    
    /**
     * @brief Get model number of layers
     * @return Number of transformer layers
     */
    size_t getNumLayers() const;
    
    /**
     * @brief Get model number of attention heads
     * @return Number of attention heads
     */
    size_t getNumHeads() const;
    
    /**
     * @brief Get model number of key-value heads
     * @return Number of key-value heads
     */
    size_t getNumKVHeads() const;
    
    /**
     * @brief Get model intermediate size
     * @return Size of the intermediate layer
     */
    size_t getIntermediateSize() const;
    
    /**
     * @brief Get model rotary dimension
     * @return Dimension of rotary embeddings
     */
    size_t getRotaryDim() const;
    
    /**
     * @brief Get model quantization type
     * @return String describing the quantization type
     */
    std::string getQuantizationType() const;
    
    /**
     * @brief Get model file size
     * @return Size of the model file in bytes
     */
    size_t getFileSize() const;
    
    /**
     * @brief Get model memory usage
     * @return Memory usage in bytes
     */
    size_t getMemoryUsage() const;
    
    /**
     * @brief Check if model is loaded
     * @return true if model is loaded, false otherwise
     */
    bool isLoaded() const;

private:
    /**
     * @brief Parse GGUF header
     * @return true if parsing successful, false otherwise
     */
    bool parseHeader();
    
    /**
     * @brief Parse GGUF tensors
     * @return true if parsing successful, false otherwise
     */
    bool parseTensors();
    
    /**
     * @brief Parse GGUF metadata
     * @return true if parsing successful, false otherwise
     */
    bool parseMetadata();
    
    /**
     * @brief Parse GGUF vocabulary
     * @return true if parsing successful, false otherwise
     */
    bool parseVocabulary();
    
    /**
     * @brief Validate model file
     * @return true if validation successful, false otherwise
     */
    bool validateModelFile() const;

    std::string model_path_;
    bool is_loaded_;
    std::vector<float> tensors_;
    std::unordered_map<int, std::string> vocabulary_;
    nlohmann::json metadata_;
    nlohmann::json parameters_;
    
    // Model architecture parameters
    std::string architecture_;
    size_t context_size_;
    size_t embedding_dim_;
    size_t num_layers_;
    size_t num_heads_;
    size_t num_kv_heads_;
    size_t intermediate_size_;
    size_t rotary_dim_;
    std::string quantization_type_;
    size_t file_size_;
    size_t memory_usage_;
};

} // namespace cogniware

#endif // MSMARTCOMPUTE_GGUF_LOADER_HPP 