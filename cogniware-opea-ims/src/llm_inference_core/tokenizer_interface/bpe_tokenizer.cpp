#include "bpe_tokenizer.h"
#include <spdlog/spdlog.h>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <regex>

namespace cogniware {
namespace llm_inference {

// Internal implementation
struct BPETokenizer::Impl {
    std::shared_ptr<TokenizerConfig> config;
    bool is_initialized;
    std::unordered_map<std::string, int> token_to_id;
    std::unordered_map<int, std::string> id_to_token;
    std::vector<BPEMergeRule> merge_rules;
    int bos_id;
    int eos_id;
    int pad_id;
    int unk_id;

    Impl() : is_initialized(false), bos_id(-1), eos_id(-1), pad_id(-1), unk_id(-1) {}

    void reset() {
        token_to_id.clear();
        id_to_token.clear();
        merge_rules.clear();
        is_initialized = false;
        bos_id = -1;
        eos_id = -1;
        pad_id = -1;
        unk_id = -1;
    }
};

// Constructor and destructor
BPETokenizer::BPETokenizer() : pimpl(std::make_unique<Impl>()) {}

BPETokenizer::BPETokenizer(const std::shared_ptr<TokenizerConfig>& config)
    : pimpl(std::make_unique<Impl>()) {
    pimpl->config = config;
    initialize();
}

BPETokenizer::~BPETokenizer() = default;

// Tokenization methods
std::vector<int> BPETokenizer::encode(const std::string& text) const {
    if (!pimpl->is_initialized) {
        spdlog::error("Tokenizer not initialized");
        return {};
    }

    std::vector<int> token_ids;
    if (pimpl->config->add_bos_token && pimpl->bos_id != -1) {
        token_ids.push_back(pimpl->bos_id);
    }

    auto tokens = tokenize(text);
    for (const auto& token : tokens) {
        auto it = pimpl->token_to_id.find(token);
        if (it != pimpl->token_to_id.end()) {
            token_ids.push_back(it->second);
        } else if (pimpl->unk_id != -1) {
            token_ids.push_back(pimpl->unk_id);
        }
    }

    if (pimpl->config->add_eos_token && pimpl->eos_id != -1) {
        token_ids.push_back(pimpl->eos_id);
    }

    if (pimpl->config->truncate_long_sequences && token_ids.size() > pimpl->config->max_sequence_length) {
        token_ids.resize(pimpl->config->max_sequence_length);
        if (pimpl->config->add_eos_token && pimpl->eos_id != -1) {
            token_ids.back() = pimpl->eos_id;
        }
    }

    return token_ids;
}

std::string BPETokenizer::decode(const std::vector<int>& tokens) const {
    if (!pimpl->is_initialized) {
        spdlog::error("Tokenizer not initialized");
        return "";
    }

    std::string result;
    for (int token_id : tokens) {
        if (token_id == pimpl->bos_id || token_id == pimpl->eos_id || token_id == pimpl->pad_id) {
            continue;
        }
        auto it = pimpl->id_to_token.find(token_id);
        if (it != pimpl->id_to_token.end()) {
            result += it->second;
        }
    }
    return result;
}

std::vector<std::string> BPETokenizer::tokenize(const std::string& text) const {
    if (!pimpl->is_initialized) {
        spdlog::error("Tokenizer not initialized");
        return {};
    }

    auto subwords = splitIntoSubwords(text);
    return applyMergeRules(subwords);
}

// Vocabulary methods
size_t BPETokenizer::getVocabularySize() const {
    return pimpl->token_to_id.size();
}

std::string BPETokenizer::getToken(int id) const {
    auto it = pimpl->id_to_token.find(id);
    return it != pimpl->id_to_token.end() ? it->second : "";
}

int BPETokenizer::getTokenId(const std::string& token) const {
    auto it = pimpl->token_to_id.find(token);
    return it != pimpl->token_to_id.end() ? it->second : -1;
}

bool BPETokenizer::hasToken(const std::string& token) const {
    return pimpl->token_to_id.find(token) != pimpl->token_to_id.end();
}

// Special tokens
int BPETokenizer::getBOSId() const { return pimpl->bos_id; }
int BPETokenizer::getEOSId() const { return pimpl->eos_id; }
int BPETokenizer::getPADId() const { return pimpl->pad_id; }
int BPETokenizer::getUNKId() const { return pimpl->unk_id; }

// Configuration
std::shared_ptr<const TokenizerConfig> BPETokenizer::getConfig() const {
    return pimpl->config;
}

void BPETokenizer::setConfig(const std::shared_ptr<TokenizerConfig>& config) {
    pimpl->config = config;
    initialize();
}

// State
bool BPETokenizer::isInitialized() const {
    return pimpl->is_initialized;
}

void BPETokenizer::reset() {
    pimpl->reset();
}

// BPE specific methods
bool BPETokenizer::loadModel(const std::string& path) {
    if (pimpl->is_initialized) {
        reset();
    }

    pimpl->config->model_path = path;
    return initialize();
}

void BPETokenizer::unloadModel() {
    reset();
}

bool BPETokenizer::addMergeRule(const std::string& first, const std::string& second,
                              const std::string& merged, int priority) {
    if (!pimpl->is_initialized) {
        return false;
    }

    BPEMergeRule rule{first, second, merged, priority};
    pimpl->merge_rules.push_back(rule);
    std::sort(pimpl->merge_rules.begin(), pimpl->merge_rules.end(),
              [](const BPEMergeRule& a, const BPEMergeRule& b) {
                  return a.priority > b.priority;
              });
    return true;
}

bool BPETokenizer::removeMergeRule(const std::string& first, const std::string& second) {
    if (!pimpl->is_initialized) {
        return false;
    }

    auto it = std::find_if(pimpl->merge_rules.begin(), pimpl->merge_rules.end(),
                          [&](const BPEMergeRule& rule) {
                              return rule.first == first && rule.second == second;
                          });
    if (it != pimpl->merge_rules.end()) {
        pimpl->merge_rules.erase(it);
        return true;
    }
    return false;
}

std::vector<BPEMergeRule> BPETokenizer::getMergeRules() const {
    return pimpl->merge_rules;
}

// Helper methods
bool BPETokenizer::initialize() {
    if (!pimpl->config) {
        spdlog::error("No configuration provided");
        return false;
    }

    if (pimpl->config->model_path.empty()) {
        spdlog::error("No model path provided");
        return false;
    }

    if (!loadVocabulary()) {
        spdlog::error("Failed to load vocabulary");
        return false;
    }

    if (!loadMergeRules()) {
        spdlog::error("Failed to load merge rules");
        return false;
    }

    // Add special tokens
    if (pimpl->config->use_bos_token) {
        pimpl->bos_id = getTokenId(pimpl->config->bos_token);
    }
    if (pimpl->config->use_eos_token) {
        pimpl->eos_id = getTokenId(pimpl->config->eos_token);
    }
    if (pimpl->config->use_pad_token) {
        pimpl->pad_id = getTokenId(pimpl->config->pad_token);
    }
    if (pimpl->config->use_unk_token) {
        pimpl->unk_id = getTokenId(pimpl->config->unk_token);
    }

    pimpl->is_initialized = true;
    return true;
}

bool BPETokenizer::loadVocabulary() {
    std::ifstream file(pimpl->config->model_path + ".vocab");
    if (!file.is_open()) {
        spdlog::error("Failed to open vocabulary file: {}", pimpl->config->model_path + ".vocab");
        return false;
    }

    std::string line;
    int id = 0;
    while (std::getline(file, line)) {
        pimpl->token_to_id[line] = id;
        pimpl->id_to_token[id] = line;
        ++id;
    }

    return true;
}

bool BPETokenizer::loadMergeRules() {
    std::ifstream file(pimpl->config->model_path + ".merges");
    if (!file.is_open()) {
        spdlog::error("Failed to open merge rules file: {}", pimpl->config->model_path + ".merges");
        return false;
    }

    std::string line;
    int priority = 0;
    while (std::getline(file, line)) {
        std::istringstream iss(line);
        std::string first, second, merged;
        if (iss >> first >> second >> merged) {
            BPEMergeRule rule{first, second, merged, priority++};
            pimpl->merge_rules.push_back(rule);
        }
    }

    std::sort(pimpl->merge_rules.begin(), pimpl->merge_rules.end(),
              [](const BPEMergeRule& a, const BPEMergeRule& b) {
                  return a.priority > b.priority;
              });

    return true;
}

std::vector<std::string> BPETokenizer::applyMergeRules(const std::vector<std::string>& tokens) const {
    std::vector<std::string> result = tokens;
    bool changed = true;

    while (changed) {
        changed = false;
        for (const auto& rule : pimpl->merge_rules) {
            for (size_t i = 0; i < result.size() - 1; ++i) {
                if (result[i] == rule.first && result[i + 1] == rule.second) {
                    result[i] = rule.merged;
                    result.erase(result.begin() + i + 1);
                    changed = true;
                    break;
                }
            }
            if (changed) break;
        }
    }

    return result;
}

std::vector<std::string> BPETokenizer::splitIntoSubwords(const std::string& text) const {
    std::vector<std::string> result;
    std::string current;
    
    for (char c : text) {
        if (std::isspace(c)) {
            if (!current.empty()) {
                result.push_back(current);
                current.clear();
            }
        } else {
            current += c;
        }
    }
    
    if (!current.empty()) {
        result.push_back(current);
    }

    return result;
}

} // namespace llm_inference
} // namespace cogniware
