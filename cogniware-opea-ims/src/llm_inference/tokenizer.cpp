#include "llm_inference/tokenizer.h"
#include <spdlog/spdlog.h>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <regex>
#include <nlohmann/json.hpp>
#include <filesystem>

namespace cogniware {
namespace llm_inference {

Tokenizer::Tokenizer(const TokenizerConfig& config) : config_(config) {
    try {
        load_vocabulary();
        initialize_special_tokens();
        spdlog::info("Tokenizer initialized successfully");
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize tokenizer: {}", e.what());
        throw;
    }
}

std::vector<int> Tokenizer::encode(const std::string& text) {
    try {
        std::lock_guard<std::mutex> lock(mutex_);
        
        std::string processed_text = preprocess_text(text);
        std::vector<int> tokens;
        
        if (config_.use_bpe) {
            tokens = apply_bpe(processed_text);
        } else if (config_.use_wordpiece) {
            tokens = apply_wordpiece(processed_text);
        } else if (config_.use_sentencepiece) {
            tokens = apply_sentencepiece(processed_text);
        } else {
            tokens = apply_basic_tokenization(processed_text);
        }
        
        if (config_.add_special_tokens) {
            add_special_tokens(tokens);
        }
        
        return tokens;
    } catch (const std::exception& e) {
        spdlog::error("Tokenization failed: {}", e.what());
        throw;
    }
}

std::string Tokenizer::decode(const std::vector<int>& tokens) {
    try {
        std::lock_guard<std::mutex> lock(mutex_);
        
        std::string text;
        for (size_t i = 0; i < tokens.size(); ++i) {
            if (is_special_token(tokens[i])) {
                continue;
            }
            
            auto it = id_to_token_.find(tokens[i]);
            if (it != id_to_token_.end()) {
                text += it->second;
            } else {
                text += config_.unk_token;
            }
        }
        
        return postprocess_text(text);
    } catch (const std::exception& e) {
        spdlog::error("Detokenization failed: {}", e.what());
        throw;
    }
}

std::vector<std::vector<int>> Tokenizer::batch_encode(const std::vector<std::string>& texts) {
    std::vector<std::vector<int>> results;
    results.reserve(texts.size());
    
    for (const auto& text : texts) {
        results.push_back(encode(text));
    }
    
    return results;
}

std::vector<std::string> Tokenizer::batch_decode(const std::vector<std::vector<int>>& batch_tokens) {
    std::vector<std::string> results;
    results.reserve(batch_tokens.size());
    
    for (const auto& tokens : batch_tokens) {
        results.push_back(decode(tokens));
    }
    
    return results;
}

void Tokenizer::load_vocabulary() {
    try {
        std::ifstream vocab_file(config_.vocab_file);
        if (!vocab_file) {
            throw std::runtime_error("Failed to open vocabulary file: " + config_.vocab_file);
        }
        
        std::string line;
        int token_id = 0;
        while (std::getline(vocab_file, line)) {
            token_to_id_[line] = token_id;
            id_to_token_[token_id] = line;
            token_id++;
        }
        
        if (config_.use_bpe && !config_.merges_file.empty()) {
            load_merges();
        }
        
        spdlog::info("Vocabulary loaded successfully with {} tokens", token_id);
    } catch (const std::exception& e) {
        spdlog::error("Failed to load vocabulary: {}", e.what());
        throw;
    }
}

void Tokenizer::load_merges() {
    try {
        std::ifstream merges_file(config_.merges_file);
        if (!merges_file) {
            throw std::runtime_error("Failed to open merges file: " + config_.merges_file);
        }
        
        std::string line;
        while (std::getline(merges_file, line)) {
            if (line.empty() || line[0] == '#') continue;
            
            std::istringstream iss(line);
            std::string token1, token2;
            iss >> token1 >> token2;
            
            if (!token1.empty() && !token2.empty()) {
                merges_[std::make_pair(token1, token2)] = token1 + token2;
            }
        }
        
        spdlog::info("BPE merges loaded successfully");
    } catch (const std::exception& e) {
        spdlog::error("Failed to load BPE merges: {}", e.what());
        throw;
    }
}

void Tokenizer::initialize_special_tokens() {
    special_tokens_ = {
        {config_.pad_token_id, "<pad>"},
        {config_.bos_token_id, "<bos>"},
        {config_.eos_token_id, "<eos>"},
        {config_.unk_token_id, "<unk>"},
        {config_.mask_token_id, "<mask>"},
        {config_.sep_token_id, "<sep>"},
        {config_.cls_token_id, "<cls>"}
    };
    
    for (const auto& [id, token] : special_tokens_) {
        token_to_id_[token] = id;
        id_to_token_[id] = token;
    }
}

std::vector<int> Tokenizer::apply_bpe(const std::string& text) {
    std::vector<std::string> tokens = split_into_words(text);
    std::vector<int> result;
    
    for (const auto& word : tokens) {
        std::vector<std::string> subwords = apply_bpe_to_word(word);
        for (const auto& subword : subwords) {
            auto it = token_to_id_.find(subword);
            if (it != token_to_id_.end()) {
                result.push_back(it->second);
            } else {
                result.push_back(config_.unk_token_id);
            }
        }
    }
    
    return result;
}

std::vector<std::string> Tokenizer::apply_bpe_to_word(const std::string& word) {
    std::vector<std::string> subwords;
    std::string current = word;
    
    while (!current.empty()) {
        bool found_merge = false;
        for (const auto& [pair, merged] : merges_) {
            size_t pos = current.find(pair.first + pair.second);
            if (pos != std::string::npos) {
                current.replace(pos, pair.first.length() + pair.second.length(), merged);
                found_merge = true;
                break;
            }
        }
        
        if (!found_merge) {
            subwords.push_back(current);
            break;
        }
    }
    
    return subwords;
}

std::vector<int> Tokenizer::apply_wordpiece(const std::string& text) {
    std::vector<std::string> words = split_into_words(text);
    std::vector<int> result;
    
    for (const auto& word : words) {
        std::vector<std::string> subwords = apply_wordpiece_to_word(word);
        for (const auto& subword : subwords) {
            auto it = token_to_id_.find(subword);
            if (it != token_to_id_.end()) {
                result.push_back(it->second);
            } else {
                result.push_back(config_.unk_token_id);
            }
        }
    }
    
    return result;
}

std::vector<std::string> Tokenizer::apply_wordpiece_to_word(const std::string& word) {
    std::vector<std::string> subwords;
    std::string current = word;
    
    while (!current.empty()) {
        bool found_subword = false;
        for (size_t i = current.length(); i > 0; --i) {
            std::string subword = current.substr(0, i);
            if (token_to_id_.find(subword) != token_to_id_.end()) {
                subwords.push_back(subword);
                current = current.substr(i);
                found_subword = true;
                break;
            }
        }
        
        if (!found_subword) {
            subwords.push_back("##" + current);
            break;
        }
    }
    
    return subwords;
}

std::vector<int> Tokenizer::apply_sentencepiece(const std::string& text) {
    // Implement sentencepiece tokenization
    // This is a placeholder for the actual implementation
    return apply_basic_tokenization(text);
}

std::vector<int> Tokenizer::apply_basic_tokenization(const std::string& text) {
    std::vector<std::string> words = split_into_words(text);
    std::vector<int> result;
    
    for (const auto& word : words) {
        auto it = token_to_id_.find(word);
        if (it != token_to_id_.end()) {
            result.push_back(it->second);
        } else {
            result.push_back(config_.unk_token_id);
        }
    }
    
    return result;
}

std::vector<std::string> Tokenizer::split_into_words(const std::string& text) {
    std::vector<std::string> words;
    std::string current;
    
    for (char c : text) {
        if (std::isspace(c)) {
            if (!current.empty()) {
                words.push_back(current);
                current.clear();
            }
        } else {
            current += c;
        }
    }
    
    if (!current.empty()) {
        words.push_back(current);
    }
    
    return words;
}

void Tokenizer::add_special_tokens(std::vector<int>& tokens) {
    if (config_.add_bos_token) {
        tokens.insert(tokens.begin(), config_.bos_token_id);
    }
    if (config_.add_eos_token) {
        tokens.push_back(config_.eos_token_id);
    }
}

std::string Tokenizer::preprocess_text(const std::string& text) {
    std::string result = text;
    
    if (config_.do_lower_case) {
        std::transform(result.begin(), result.end(), result.begin(), ::tolower);
    }
    
    if (config_.strip_accents) {
        // Implement accent stripping
        // This is a placeholder for the actual implementation
    }
    
    return result;
}

std::string Tokenizer::postprocess_text(const std::string& text) {
    std::string result = text;
    
    if (config_.clean_up_tokenization_spaces) {
        std::regex space_regex("\\s+");
        result = std::regex_replace(result, space_regex, " ");
        result = std::regex_replace(result, std::regex("^\\s+|\\s+$"), "");
    }
    
    return result;
}

bool Tokenizer::is_special_token(int token_id) const {
    return special_tokens_.find(token_id) != special_tokens_.end();
}

int Tokenizer::get_vocab_size() const {
    return token_to_id_.size();
}

std::string Tokenizer::get_token(int token_id) const {
    auto it = id_to_token_.find(token_id);
    return it != id_to_token_.end() ? it->second : "";
}

int Tokenizer::get_token_id(const std::string& token) const {
    auto it = token_to_id_.find(token);
    return it != token_to_id_.end() ? it->second : config_.unk_token_id;
}

} // namespace llm_inference
} // namespace cogniware 