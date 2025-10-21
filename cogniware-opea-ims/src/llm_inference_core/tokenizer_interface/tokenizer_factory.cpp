#include "tokenizer_factory.h"
#include "bpe_tokenizer.h"
#include <spdlog/spdlog.h>

namespace cogniware {
namespace llm_inference {

TokenizerFactory::TokenizerFactory(std::shared_ptr<TokenizerConfig> defaultConfig)
    : defaultConfig_(defaultConfig) {
}

std::shared_ptr<BaseTokenizer> TokenizerFactory::createTokenizer(const std::string& type, 
                                                               std::shared_ptr<TokenizerConfig> config) {
    if (!config) {
        config = defaultConfig_;
    }
    
    if (type == "bpe") {
        return std::make_shared<BPETokenizer>(config);
    } else {
        spdlog::error("Unsupported tokenizer type: {}", type);
        return nullptr;
    }
}

} // namespace llm_inference
} // namespace cogniware
