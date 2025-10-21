#include "sentencepiece_wrapper.h"
#include <spdlog/spdlog.h>
#include <sentencepiece_processor.h>
#include <sentencepiece_trainer.h>

namespace cogniware {
namespace llm_inference {

// Internal implementation
struct SentencePieceWrapper::Impl {
    std::shared_ptr<TokenizerConfig> config;
    bool is_initialized;
    std::unique_ptr<sentencepiece::SentencePieceProcessor> processor;
    std::string encode_options;
    std::string decode_options;
    int bos_id;
    int eos_id;
    int pad_id;
    int unk_id;

    Impl() : is_initialized(false), bos_id(-1), eos_id(-1), pad_id(-1), unk_id(-1) {}

    void reset() {
        processor.reset();
        is_initialized = false;
        encode_options.clear();
        decode_options.clear();
        bos_id = -1;
        eos_id = -1;
        pad_id = -1;
        unk_id = -1;
    }
};

// Constructor and destructor
SentencePieceWrapper::SentencePieceWrapper() : pimpl(std::make_unique<Impl>()) {}

SentencePieceWrapper::SentencePieceWrapper(const std::shared_ptr<TokenizerConfig>& config)
    : pimpl(std::make_unique<Impl>()) {
    pimpl->config = config;
    initialize();
}

SentencePieceWrapper::~SentencePieceWrapper() = default;

// Tokenization methods
std::vector<int> SentencePieceWrapper::encode(const std::string& text) const {
    if (!pimpl->is_initialized || !pimpl->processor) {
        spdlog::error("Tokenizer not initialized");
        return {};
    }

    std::vector<int> token_ids;
    if (pimpl->config->add_bos_token && pimpl->bos_id != -1) {
        token_ids.push_back(pimpl->bos_id);
    }

    std::vector<int> ids;
    pimpl->processor->Encode(text, &ids);
    token_ids.insert(token_ids.end(), ids.begin(), ids.end());

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

std::string SentencePieceWrapper::decode(const std::vector<int>& tokens) const {
    if (!pimpl->is_initialized || !pimpl->processor) {
        spdlog::error("Tokenizer not initialized");
        return "";
    }

    std::vector<int> filtered_tokens;
    for (int token_id : tokens) {
        if (token_id != pimpl->bos_id && token_id != pimpl->eos_id && token_id != pimpl->pad_id) {
            filtered_tokens.push_back(token_id);
        }
    }

    std::string result;
    pimpl->processor->Decode(filtered_tokens, &result);
    return result;
}

std::vector<std::string> SentencePieceWrapper::tokenize(const std::string& text) const {
    if (!pimpl->is_initialized || !pimpl->processor) {
        spdlog::error("Tokenizer not initialized");
        return {};
    }

    std::vector<std::string> pieces;
    pimpl->processor->Encode(text, &pieces);
    return pieces;
}

// Vocabulary methods
size_t SentencePieceWrapper::getVocabularySize() const {
    if (!pimpl->is_initialized || !pimpl->processor) {
        return 0;
    }
    return pimpl->processor->GetPieceSize();
}

std::string SentencePieceWrapper::getToken(int id) const {
    if (!pimpl->is_initialized || !pimpl->processor) {
        return "";
    }
    return pimpl->processor->IdToPiece(id);
}

int SentencePieceWrapper::getTokenId(const std::string& token) const {
    if (!pimpl->is_initialized || !pimpl->processor) {
        return -1;
    }
    return pimpl->processor->PieceToId(token);
}

bool SentencePieceWrapper::hasToken(const std::string& token) const {
    if (!pimpl->is_initialized || !pimpl->processor) {
        return false;
    }
    return pimpl->processor->PieceToId(token) != pimpl->unk_id;
}

// Special tokens
int SentencePieceWrapper::getBOSId() const { return pimpl->bos_id; }
int SentencePieceWrapper::getEOSId() const { return pimpl->eos_id; }
int SentencePieceWrapper::getPADId() const { return pimpl->pad_id; }
int SentencePieceWrapper::getUNKId() const { return pimpl->unk_id; }

// Configuration
std::shared_ptr<const TokenizerConfig> SentencePieceWrapper::getConfig() const {
    return pimpl->config;
}

void SentencePieceWrapper::setConfig(const std::shared_ptr<TokenizerConfig>& config) {
    pimpl->config = config;
    initialize();
}

// State
bool SentencePieceWrapper::isInitialized() const {
    return pimpl->is_initialized;
}

void SentencePieceWrapper::reset() {
    pimpl->reset();
}

// SentencePiece specific methods
bool SentencePieceWrapper::loadModel(const std::string& path) {
    if (pimpl->is_initialized) {
        reset();
    }

    pimpl->config->model_path = path;
    return initialize();
}

void SentencePieceWrapper::unloadModel() {
    reset();
}

bool SentencePieceWrapper::setEncodeExtraOptions(const std::string& options) {
    if (!pimpl->is_initialized || !pimpl->processor) {
        return false;
    }

    pimpl->encode_options = options;
    return pimpl->processor->SetEncodeExtraOptions(options);
}

bool SentencePieceWrapper::setDecodeExtraOptions(const std::string& options) {
    if (!pimpl->is_initialized || !pimpl->processor) {
        return false;
    }

    pimpl->decode_options = options;
    return pimpl->processor->SetDecodeExtraOptions(options);
}

std::string SentencePieceWrapper::getEncodeExtraOptions() const {
    return pimpl->encode_options;
}

std::string SentencePieceWrapper::getDecodeExtraOptions() const {
    return pimpl->decode_options;
}

// Helper methods
bool SentencePieceWrapper::initialize() {
    if (!pimpl->config) {
        spdlog::error("No configuration provided");
        return false;
    }

    if (pimpl->config->model_path.empty()) {
        spdlog::error("No model path provided");
        return false;
    }

    if (!loadModelFile()) {
        spdlog::error("Failed to load model file");
        return false;
    }

    // Get special token IDs
    pimpl->bos_id = pimpl->processor->bos_id();
    pimpl->eos_id = pimpl->processor->eos_id();
    pimpl->pad_id = pimpl->processor->pad_id();
    pimpl->unk_id = pimpl->processor->unk_id();

    pimpl->is_initialized = true;
    return true;
}

bool SentencePieceWrapper::loadModelFile() {
    try {
        pimpl->processor = std::make_unique<sentencepiece::SentencePieceProcessor>();
        if (!pimpl->processor->Load(pimpl->config->model_path).ok()) {
            spdlog::error("Failed to load SentencePiece model: {}", pimpl->config->model_path);
            return false;
        }
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Exception while loading SentencePiece model: {}", e.what());
        return false;
    }
}

} // namespace llm_inference
} // namespace cogniware
