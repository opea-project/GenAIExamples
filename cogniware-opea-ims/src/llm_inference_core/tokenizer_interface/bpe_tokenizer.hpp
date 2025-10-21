/**
 * @file bpe_tokenizer.hpp
 * @brief BPE tokenizer for the cogniware engine
 */

#ifndef MSMARTCOMPUTE_BPE_TOKENIZER_HPP
#define MSMARTCOMPUTE_BPE_TOKENIZER_HPP

#include <string>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <nlohmann/json.hpp>

namespace cogniware {

/**
 * @brief Class for BPE tokenization
 */
class BPETokenizer {
public:
    /**
     * @brief Constructor
     * @param vocab_path Path to the vocabulary file
     * @param merges_path Path to the merges file
     */
    BPETokenizer(const std::string& vocab_path, const std::string& merges_path);
    
    /**
     * @brief Destructor
     */
    ~BPETokenizer();
    
    /**
     * @brief Initialize the tokenizer
     * @return true if initialization successful, false otherwise
     */
    bool initialize();
    
    /**
     * @brief Tokenize text
     * @param text Input text
     * @return Vector of token IDs
     */
    std::vector<int> tokenize(const std::string& text);
    
    /**
     * @brief Detokenize tokens
     * @param token_ids Vector of token IDs
     * @return Detokenized text
     */
    std::string detokenize(const std::vector<int>& token_ids);
    
    /**
     * @brief Get vocabulary size
     * @return Number of tokens in vocabulary
     */
    size_t getVocabSize() const;
    
    /**
     * @brief Get vocabulary
     * @return Map of token IDs to token strings
     */
    std::unordered_map<int, std::string> getVocabulary() const;
    
    /**
     * @brief Get merges
     * @return Map of merge pairs to merge ranks
     */
    std::unordered_map<std::pair<std::string, std::string>, int, PairHash> getMerges() const;
    
    /**
     * @brief Get special tokens
     * @return Set of special token strings
     */
    std::unordered_set<std::string> getSpecialTokens() const;
    
    /**
     * @brief Add special token
     * @param token Special token to add
     */
    void addSpecialToken(const std::string& token);
    
    /**
     * @brief Remove special token
     * @param token Special token to remove
     */
    void removeSpecialToken(const std::string& token);
    
    /**
     * @brief Check if token is special
     * @param token Token to check
     * @return true if token is special, false otherwise
     */
    bool isSpecialToken(const std::string& token) const;
    
    /**
     * @brief Get token ID
     * @param token Token string
     * @return Token ID, or -1 if not found
     */
    int getTokenId(const std::string& token) const;
    
    /**
     * @brief Get token string
     * @param token_id Token ID
     * @return Token string, or empty string if not found
     */
    std::string getTokenString(int token_id) const;
    
    /**
     * @brief Check if tokenizer is initialized
     * @return true if tokenizer is initialized, false otherwise
     */
    bool isInitialized() const;

private:
    /**
     * @brief Load vocabulary
     * @return true if loading successful, false otherwise
     */
    bool loadVocabulary();
    
    /**
     * @brief Load merges
     * @return true if loading successful, false otherwise
     */
    bool loadMerges();
    
    /**
     * @brief Apply BPE merges
     * @param tokens Vector of tokens to merge
     * @return Vector of merged tokens
     */
    std::vector<std::string> applyMerges(const std::vector<std::string>& tokens);
    
    /**
     * @brief Find best merge
     * @param tokens Vector of tokens
     * @return Pair of indices to merge, or (-1, -1) if no merge possible
     */
    std::pair<int, int> findBestMerge(const std::vector<std::string>& tokens);

    std::string vocab_path_;
    std::string merges_path_;
    bool is_initialized_;
    std::unordered_map<int, std::string> vocabulary_;
    std::unordered_map<std::string, int> reverse_vocabulary_;
    std::unordered_map<std::pair<std::string, std::string>, int, PairHash> merges_;
    std::unordered_set<std::string> special_tokens_;
};

/**
 * @brief Hash function for string pairs
 */
struct PairHash {
    template <class T1, class T2>
    std::size_t operator()(const std::pair<T1, T2>& p) const {
        auto h1 = std::hash<T1>{}(p.first);
        auto h2 = std::hash<T2>{}(p.second);
        return h1 ^ (h2 << 1);
    }
};

} // namespace cogniware

#endif // MSMARTCOMPUTE_BPE_TOKENIZER_HPP 