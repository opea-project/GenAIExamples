#pragma once

#include "base_tokenizer.h"
#include <memory>
#include <string>

namespace cogniware {
namespace llm_inference {

class TokenizerFactory {
public:
    explicit TokenizerFactory(std::shared_ptr<TokenizerConfig> defaultConfig);
    ~TokenizerFactory() = default;

    // Prevent copying
    TokenizerFactory(const TokenizerFactory&) = delete;
    TokenizerFactory& operator=(const TokenizerFactory&) = delete;

    // Create tokenizer
    std::shared_ptr<BaseTokenizer> createTokenizer(const std::string& type, 
                                                   std::shared_ptr<TokenizerConfig> config = nullptr);

private:
    std::shared_ptr<TokenizerConfig> defaultConfig_;
};

} // namespace llm_inference
} // namespace cogniware
