/**
 * @file test_bpe_tokenizer.cpp
 * @brief Tests for the BPE tokenizer
 */

#include <gtest/gtest.h>
#include "llm_inference_core/tokenizer_interface/bpe_tokenizer.hpp"
#include <fstream>
#include <filesystem>

namespace cogniware {
namespace test {

class BPETokenizerTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Create temporary files for testing
        vocab_path_ = std::filesystem::temp_directory_path() / "test_vocab.txt";
        merges_path_ = std::filesystem::temp_directory_path() / "test_merges.txt";

        // Create test vocabulary
        std::ofstream vocab_file(vocab_path_);
        vocab_file << "<s>\n</s>\n<pad>\n<unk>\na\nb\nc\nab\nbc\nabc\n";
        vocab_file.close();

        // Create test merges
        std::ofstream merges_file(merges_path_);
        merges_file << "a b 0\nb c 1\n";
        merges_file.close();

        // Create tokenizer
        tokenizer_ = std::make_unique<BPETokenizer>(vocab_path_.string(), merges_path_.string());
        ASSERT_TRUE(tokenizer_->initialize());
    }

    void TearDown() override {
        // Clean up temporary files
        std::filesystem::remove(vocab_path_);
        std::filesystem::remove(merges_path_);
    }

    std::filesystem::path vocab_path_;
    std::filesystem::path merges_path_;
    std::unique_ptr<BPETokenizer> tokenizer_;
};

TEST_F(BPETokenizerTest, TokenizeSimple) {
    std::string text = "abc";
    auto token_ids = tokenizer_->tokenize(text);
    ASSERT_EQ(token_ids.size(), 1);
    ASSERT_EQ(tokenizer_->getTokenString(token_ids[0]), "abc");
}

TEST_F(BPETokenizerTest, TokenizeWithMerges) {
    std::string text = "abcabc";
    auto token_ids = tokenizer_->tokenize(text);
    ASSERT_EQ(token_ids.size(), 2);
    ASSERT_EQ(tokenizer_->getTokenString(token_ids[0]), "abc");
    ASSERT_EQ(tokenizer_->getTokenString(token_ids[1]), "abc");
}

TEST_F(BPETokenizerTest, TokenizeUnknown) {
    std::string text = "xyz";
    auto token_ids = tokenizer_->tokenize(text);
    ASSERT_EQ(token_ids.size(), 3);
    for (int token_id : token_ids) {
        ASSERT_EQ(tokenizer_->getTokenString(token_id), "<unk>");
    }
}

TEST_F(BPETokenizerTest, Detokenize) {
    std::vector<int> token_ids = {4, 5, 6}; // "a", "b", "c"
    std::string text = tokenizer_->detokenize(token_ids);
    ASSERT_EQ(text, "abc");
}

TEST_F(BPETokenizerTest, SpecialTokens) {
    ASSERT_TRUE(tokenizer_->isSpecialToken("<s>"));
    ASSERT_TRUE(tokenizer_->isSpecialToken("</s>"));
    ASSERT_TRUE(tokenizer_->isSpecialToken("<pad>"));
    ASSERT_TRUE(tokenizer_->isSpecialToken("<unk>"));
    ASSERT_FALSE(tokenizer_->isSpecialToken("a"));

    tokenizer_->addSpecialToken("test");
    ASSERT_TRUE(tokenizer_->isSpecialToken("test"));

    tokenizer_->removeSpecialToken("test");
    ASSERT_FALSE(tokenizer_->isSpecialToken("test"));
}

TEST_F(BPETokenizerTest, Vocabulary) {
    auto vocab = tokenizer_->getVocabulary();
    ASSERT_EQ(vocab.size(), 10); // 4 special tokens + 6 regular tokens

    ASSERT_EQ(tokenizer_->getTokenId("<s>"), 0);
    ASSERT_EQ(tokenizer_->getTokenId("</s>"), 1);
    ASSERT_EQ(tokenizer_->getTokenId("<pad>"), 2);
    ASSERT_EQ(tokenizer_->getTokenId("<unk>"), 3);
    ASSERT_EQ(tokenizer_->getTokenId("a"), 4);
    ASSERT_EQ(tokenizer_->getTokenId("b"), 5);
    ASSERT_EQ(tokenizer_->getTokenId("c"), 6);
    ASSERT_EQ(tokenizer_->getTokenId("ab"), 7);
    ASSERT_EQ(tokenizer_->getTokenId("bc"), 8);
    ASSERT_EQ(tokenizer_->getTokenId("abc"), 9);

    ASSERT_EQ(tokenizer_->getTokenString(0), "<s>");
    ASSERT_EQ(tokenizer_->getTokenString(1), "</s>");
    ASSERT_EQ(tokenizer_->getTokenString(2), "<pad>");
    ASSERT_EQ(tokenizer_->getTokenString(3), "<unk>");
    ASSERT_EQ(tokenizer_->getTokenString(4), "a");
    ASSERT_EQ(tokenizer_->getTokenString(5), "b");
    ASSERT_EQ(tokenizer_->getTokenString(6), "c");
    ASSERT_EQ(tokenizer_->getTokenString(7), "ab");
    ASSERT_EQ(tokenizer_->getTokenString(8), "bc");
    ASSERT_EQ(tokenizer_->getTokenString(9), "abc");
}

TEST_F(BPETokenizerTest, Merges) {
    auto merges = tokenizer_->getMerges();
    ASSERT_EQ(merges.size(), 2);

    ASSERT_EQ(merges[std::make_pair("a", "b")], 0);
    ASSERT_EQ(merges[std::make_pair("b", "c")], 1);
}

} // namespace test
} // namespace cogniware 