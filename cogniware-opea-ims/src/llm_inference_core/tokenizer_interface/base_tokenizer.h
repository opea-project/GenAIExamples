#pragma once

#include <string>
#include <vector>
#include <memory>
#include <unordered_map>

namespace cogniware {
namespace llm_inference {

// Forward declarations
class TokenizerConfig;

// Tokenizer interface
class BaseTokenizer {
public:
    virtual ~BaseTokenizer() = default;

    // Tokenization methods
    virtual std::vector<int> encode(const std::string& text) const = 0;
    virtual std::string decode(const std::vector<int>& tokens) const = 0;
    virtual std::vector<std::string> tokenize(const std::string& text) const = 0;

    // Vocabulary methods
    virtual size_t getVocabularySize() const = 0;
    virtual std::string getToken(int id) const = 0;
    virtual int getTokenId(const std::string& token) const = 0;
    virtual bool hasToken(const std::string& token) const = 0;

    // Special tokens
    virtual int getBOSId() const = 0;
    virtual int getEOSId() const = 0;
    virtual int getPADId() const = 0;
    virtual int getUNKId() const = 0;

    // Configuration
    virtual std::shared_ptr<const TokenizerConfig> getConfig() const = 0;
    virtual void setConfig(const std::shared_ptr<TokenizerConfig>& config) = 0;

    // State
    virtual bool isInitialized() const = 0;
    virtual void reset() = 0;
};

// Tokenizer configuration
class TokenizerConfig {
public:
    // Model configuration
    std::string model_path;
    std::string model_type;
    size_t vocabulary_size;
    bool use_bos_token;
    bool use_eos_token;
    bool use_pad_token;
    bool use_unk_token;

    // Special tokens
    std::string bos_token;
    std::string eos_token;
    std::string pad_token;
    std::string unk_token;

    // Tokenization settings
    bool add_bos_token;
    bool add_eos_token;
    bool add_pad_token;
    bool add_unk_token;
    size_t max_sequence_length;
    bool truncate_long_sequences;

    // Constructor
    TokenizerConfig() :
        vocabulary_size(0),
        use_bos_token(true),
        use_eos_token(true),
        use_pad_token(true),
        use_unk_token(true),
        bos_token("<s>"),
        eos_token("</s>"),
        pad_token("<pad>"),
        unk_token("<unk>"),
        add_bos_token(true),
        add_eos_token(true),
        add_pad_token(false),
        add_unk_token(false),
        max_sequence_length(2048),
        truncate_long_sequences(true) {}
};

// Helper functions
inline std::shared_ptr<BaseTokenizer> createTokenizer(const std::shared_ptr<TokenizerConfig>& config) {
    if (config->model_type == "bpe") {
        // TODO: Implement BPE tokenizer creation
        return nullptr;
    } else if (config->model_type == "sentencepiece") {
        // TODO: Implement SentencePiece tokenizer creation
        return nullptr;
    }
    return nullptr;
}

} // namespace llm_inference
} // namespace cogniware
