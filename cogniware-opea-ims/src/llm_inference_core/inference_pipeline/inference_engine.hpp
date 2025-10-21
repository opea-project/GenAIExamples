/**
 * @file inference_engine.hpp
 * @brief Inference engine for the cogniware engine
 */

#ifndef MSMARTCOMPUTE_INFERENCE_ENGINE_HPP
#define MSMARTCOMPUTE_INFERENCE_ENGINE_HPP

#include <string>
#include <memory>
#include <vector>
#include <unordered_map>
#include <nlohmann/json.hpp>
#include "llm_inference_core/model_loader/gguf_loader.hpp"

namespace cogniware {

/**
 * @brief Class for performing LLM inference
 */
class InferenceEngine {
public:
    /**
     * @brief Constructor
     * @param model_loader GGUF model loader
     */
    explicit InferenceEngine(std::shared_ptr<GGUFLoader> model_loader);
    
    /**
     * @brief Destructor
     */
    ~InferenceEngine();
    
    /**
     * @brief Initialize the engine
     * @return true if initialization successful, false otherwise
     */
    bool initialize();
    
    /**
     * @brief Shutdown the engine
     */
    void shutdown();
    
    /**
     * @brief Generate text
     * @param prompt Input prompt
     * @param max_tokens Maximum number of tokens to generate
     * @param temperature Sampling temperature
     * @param top_k Top-k sampling parameter
     * @param top_p Top-p sampling parameter
     * @param num_beams Number of beams for beam search
     * @param num_return_sequences Number of sequences to return
     * @param stop_sequences Stop sequences
     * @return Generated text
     */
    std::string generate(
        const std::string& prompt,
        int max_tokens,
        float temperature,
        int top_k,
        float top_p,
        int num_beams,
        int num_return_sequences,
        const std::vector<std::string>& stop_sequences
    );
    
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
     * @brief Get model memory usage
     * @return Memory usage in bytes
     */
    size_t getMemoryUsage() const;
    
    /**
     * @brief Check if engine is initialized
     * @return true if engine is initialized, false otherwise
     */
    bool isInitialized() const;

private:
    /**
     * @brief Initialize CUDA
     * @return true if initialization successful, false otherwise
     */
    bool initializeCUDA();
    
    /**
     * @brief Initialize model tensors
     * @return true if initialization successful, false otherwise
     */
    bool initializeTensors();
    
    /**
     * @brief Initialize attention layers
     * @return true if initialization successful, false otherwise
     */
    bool initializeAttentionLayers();
    
    /**
     * @brief Initialize feed-forward layers
     * @return true if initialization successful, false otherwise
     */
    bool initializeFeedForwardLayers();
    
    /**
     * @brief Initialize output layer
     * @return true if initialization successful, false otherwise
     */
    bool initializeOutputLayer();
    
    /**
     * @brief Forward pass through the model
     * @param input_ids Input token IDs
     * @param attention_mask Attention mask
     * @return Output logits
     */
    std::vector<float> forward(
        const std::vector<int>& input_ids,
        const std::vector<int>& attention_mask
    );
    
    /**
     * @brief Sample next token
     * @param logits Output logits
     * @param temperature Sampling temperature
     * @param top_k Top-k sampling parameter
     * @param top_p Top-p sampling parameter
     * @return Sampled token ID
     */
    int sampleNextToken(
        const std::vector<float>& logits,
        float temperature,
        int top_k,
        float top_p
    );
    
    /**
     * @brief Check for stop sequences
     * @param generated_text Generated text so far
     * @param stop_sequences Stop sequences
     * @return true if any stop sequence is found, false otherwise
     */
    bool checkStopSequences(
        const std::string& generated_text,
        const std::vector<std::string>& stop_sequences
    );

    std::shared_ptr<GGUFLoader> model_loader_;
    bool is_initialized_;
    
    // CUDA resources
    void* cuda_context_;
    void* cuda_stream_;
    
    // Model tensors
    std::vector<void*> model_tensors_;
    std::vector<void*> attention_tensors_;
    std::vector<void*> feed_forward_tensors_;
    void* output_tensor_;
    
    // Model parameters
    std::string architecture_;
    size_t context_size_;
    size_t embedding_dim_;
    size_t num_layers_;
    size_t num_heads_;
    size_t num_kv_heads_;
    size_t intermediate_size_;
    size_t rotary_dim_;
    std::string quantization_type_;
    size_t memory_usage_;
};

} // namespace cogniware

#endif // MSMARTCOMPUTE_INFERENCE_ENGINE_HPP 