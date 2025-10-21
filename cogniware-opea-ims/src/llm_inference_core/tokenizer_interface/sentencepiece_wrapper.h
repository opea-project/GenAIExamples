#pragma once

#include "base_tokenizer.h"
#include <memory>
#include <string>
#include <vector>

namespace cogniware {
namespace llm_inference {

// Forward declarations
class SentencePieceProcessor;

// SentencePiece wrapper implementation
class SentencePieceWrapper : public BaseTokenizer {
public:
    SentencePieceWrapper();
    explicit SentencePieceWrapper(const std::shared_ptr<TokenizerConfig>& config);
    ~SentencePieceWrapper() override;

    // Prevent copying
    SentencePieceWrapper(const SentencePieceWrapper&) = delete;
    SentencePieceWrapper& operator=(const SentencePieceWrapper&) = delete;

    // Tokenization methods
    std::vector<int> encode(const std::string& text) const override;
    std::string decode(const std::vector<int>& tokens) const override;
    std::vector<std::string> tokenize(const std::string& text) const override;

    // Vocabulary methods
    size_t getVocabularySize() const override;
    std::string getToken(int id) const override;
    int getTokenId(const std::string& token) const override;
    bool hasToken(const std::string& token) const override;

    // Special tokens
    int getBOSId() const override;
    int getEOSId() const override;
    int getPADId() const override;
    int getUNKId() const override;

    // Configuration
    std::shared_ptr<const TokenizerConfig> getConfig() const override;
    void setConfig(const std::shared_ptr<TokenizerConfig>& config) override;

    // State
    bool isInitialized() const override;
    void reset() override;

    // SentencePiece specific methods
    bool loadModel(const std::string& path);
    void unloadModel();
    bool setEncodeExtraOptions(const std::string& options);
    bool setDecodeExtraOptions(const std::string& options);
    std::string getEncodeExtraOptions() const;
    std::string getDecodeExtraOptions() const;

private:
    // Internal implementation
    struct Impl;
    std::unique_ptr<Impl> pimpl;

    // Helper methods
    bool initialize();
    bool loadModelFile();
};

// Helper functions
inline std::shared_ptr<SentencePieceWrapper> createSentencePieceWrapper(
    const std::shared_ptr<TokenizerConfig>& config) {
    return std::make_shared<SentencePieceWrapper>(config);
}

} // namespace llm_inference
} // namespace cogniware
