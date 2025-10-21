#pragma once

#include <string>
#include <vector>
#include <unordered_map>
#include <mutex>
#include <memory>
#include <utility>

namespace cogniware {
namespace llm_inference {

struct TokenizerConfig {
    std::string vocab_file;
    std::string merges_file;
    std::string special_tokens_file;
    int pad_token_id;
    int bos_token_id;
    int eos_token_id;
    int unk_token_id;
    int mask_token_id;
    int sep_token_id;
    int cls_token_id;
    bool add_special_tokens;
    bool add_bos_token;
    bool add_eos_token;
    bool add_sep_token;
    bool add_cls_token;
    bool add_mask_token;
    bool add_unk_token;
    bool add_pad_token;
    bool do_lower_case;
    bool strip_accents;
    bool clean_up_tokenization_spaces;
    bool use_fast;
    bool use_slow;
    bool use_regex;
    bool use_byte_level;
    bool use_word_level;
    bool use_char_level;
    bool use_subword_level;
    bool use_bpe;
    bool use_wordpiece;
    bool use_unigram;
    bool use_sentencepiece;
    std::string unk_token;
};

class Tokenizer {
public:
    explicit Tokenizer(const TokenizerConfig& config);
    ~Tokenizer() = default;

    // Tokenization methods
    std::vector<int> encode(const std::string& text);
    std::string decode(const std::vector<int>& tokens);
    std::vector<std::vector<int>> batch_encode(const std::vector<std::string>& texts);
    std::vector<std::string> batch_decode(const std::vector<std::vector<int>>& batch_tokens);

    // Vocabulary management
    int get_vocab_size() const;
    bool is_special_token(int token_id) const;
    std::string get_token(int token_id) const;
    int get_token_id(const std::string& token) const;

private:
    // Configuration and state
    TokenizerConfig config_;
    std::unordered_map<std::string, int> token_to_id_;
    std::unordered_map<int, std::string> id_to_token_;
    std::unordered_map<std::pair<std::string, std::string>, std::string> merges_;
    std::unordered_map<int, std::string> special_tokens_;
    mutable std::mutex mutex_;

    // Helper methods
    void load_vocabulary();
    void load_merges();
    void initialize_special_tokens();
    std::vector<int> apply_bpe(const std::string& text);
    std::vector<std::string> apply_bpe_to_word(const std::string& word);
    std::vector<int> apply_wordpiece(const std::string& text);
    std::vector<std::string> apply_wordpiece_to_word(const std::string& word);
    std::vector<int> apply_sentencepiece(const std::string& text);
    std::vector<int> apply_basic_tokenization(const std::string& text);
    std::vector<std::string> split_into_words(const std::string& text);
    void add_special_tokens(std::vector<int>& tokens);
    std::string preprocess_text(const std::string& text);
    std::string postprocess_text(const std::string& text);
};

} // namespace llm_inference
} // namespace cogniware 