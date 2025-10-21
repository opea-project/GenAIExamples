#pragma once

#include "base_tokenizer.h"
#include <unordered_map>
#include <vector>
#include <string>
#include <memory>

namespace cogniware {
namespace llm_inference {

// BPE merge rule
struct BPEMergeRule {
    std::string first;
    std::string second;
    std::string merged;
    int priority;
};

// BPE tokenizer implementation
class BPETokenizer : public BaseTokenizer {
public:
    BPETokenizer();
    explicit BPETokenizer(const std::shared_ptr<TokenizerConfig>& config);
    ~BPETokenizer() override;

    // Prevent copying
    BPETokenizer(const BPETokenizer&) = delete;
    BPETokenizer& operator=(const BPETokenizer&) = delete;

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

    // BPE specific methods
    bool loadModel(const std::string& path);
    void unloadModel();
    bool addMergeRule(const std::string& first, const std::string& second, const std::string& merged, int priority);
    bool removeMergeRule(const std::string& first, const std::string& second);
    std::vector<BPEMergeRule> getMergeRules() const;

private:
    // Internal implementation
    struct Impl;
    std::unique_ptr<Impl> pimpl;

    // Helper methods
    bool initialize();
    bool loadVocabulary();
    bool loadMergeRules();
    std::vector<std::string> applyMergeRules(const std::vector<std::string>& tokens) const;
    std::vector<std::string> splitIntoSubwords(const std::string& text) const;
};

// Helper functions
inline std::shared_ptr<BPETokenizer> createBPETokenizer(const std::shared_ptr<TokenizerConfig>& config) {
    return std::make_shared<BPETokenizer>(config);
}

} // namespace llm_inference
} // namespace cogniware
