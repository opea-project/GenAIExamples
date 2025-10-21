#include <gtest/gtest.h>
#include "inference/inference_sharing.h"
#include <thread>
#include <chrono>

using namespace cogniware::inference;

class InferenceSharingSystemTest : public ::testing::Test {
protected:
    void SetUp() override {
        config.max_knowledge_cache_size = 1024 * 1024;
        config.max_inference_history = 100;
        config.enable_cross_validation = true;
        config.enable_knowledge_transfer = true;
        config.enable_collaborative_inference = true;
        config.confidence_threshold = 0.75f;
        config.min_validation_models = 2;
        config.max_validation_models = 4;
    }

    void TearDown() override {
        // Cleanup
    }

    InferenceSharingConfig config;
};

// Test 1: Basic knowledge caching
TEST_F(InferenceSharingSystemTest, BasicKnowledgeCaching) {
    AdvancedInferenceSharing sharing(config);

    auto knowledge = std::make_shared<Knowledge>();
    knowledge->id = "k1";
    knowledge->source_model = "model1";
    knowledge->domain = "nlp";
    knowledge->confidence = 0.9f;
    knowledge->usage_count = 0;

    ASSERT_TRUE(sharing.cacheKnowledge(knowledge));
    EXPECT_EQ(sharing.getKnowledgeCacheSize(), 1);

    auto retrieved = sharing.retrieveKnowledge("nlp", 10);
    EXPECT_EQ(retrieved.size(), 1);
    EXPECT_EQ(retrieved[0]->id, "k1");
}

// Test 2: Knowledge retrieval and usage tracking
TEST_F(InferenceSharingSystemTest, KnowledgeRetrievalAndUsage) {
    AdvancedInferenceSharing sharing(config);

    for (int i = 0; i < 5; ++i) {
        auto knowledge = std::make_shared<Knowledge>();
        knowledge->id = "k" + std::to_string(i);
        knowledge->source_model = "model1";
        knowledge->domain = "nlp";
        knowledge->confidence = 0.7f + i * 0.05f;
        knowledge->usage_count = 0;
        sharing.cacheKnowledge(knowledge);
    }

    EXPECT_EQ(sharing.getKnowledgeCacheSize(), 5);

    auto retrieved = sharing.retrieveKnowledge("nlp", 3);
    EXPECT_EQ(retrieved.size(), 3);
    
    // Should retrieve highest confidence first
    EXPECT_GE(retrieved[0]->confidence, retrieved[1]->confidence);
}

// Test 3: Knowledge transfer between models
TEST_F(InferenceSharingSystemTest, KnowledgeTransfer) {
    AdvancedInferenceSharing sharing(config);

    // Add knowledge for source model
    for (int i = 0; i < 3; ++i) {
        auto knowledge = std::make_shared<Knowledge>();
        knowledge->id = "k" + std::to_string(i);
        knowledge->source_model = "source_model";
        knowledge->domain = "domain1";
        knowledge->confidence = 0.85f;
        knowledge->usage_count = 0;
        sharing.cacheKnowledge(knowledge);
    }

    auto result = sharing.transferKnowledge(
        "source_model", "target_model", {"domain1"});

    EXPECT_TRUE(result.success);
    EXPECT_EQ(result.source_model, "source_model");
    EXPECT_EQ(result.target_model, "target_model");
    EXPECT_GT(result.transfer_count, 0);
    EXPECT_GT(result.transfer_quality, 0.0f);
}

// Test 4: Cross-validation with multiple models
TEST_F(InferenceSharingSystemTest, CrossValidation) {
    AdvancedInferenceSharing sharing(config);

    std::vector<std::string> model_ids = {"model1", "model2", "model3"};
    auto result = sharing.validateInference("test input", model_ids);

    EXPECT_EQ(result.model_ids.size(), 3);
    EXPECT_EQ(result.individual_results.size(), 3);
    EXPECT_FALSE(result.consensus_output.empty());
    EXPECT_GT(result.agreement_scores.size(), 0);
}

// Test 5: Cross-validation with insufficient models
TEST_F(InferenceSharingSystemTest, CrossValidationInsufficientModels) {
    AdvancedInferenceSharing sharing(config);

    std::vector<std::string> model_ids = {"model1"};
    auto result = sharing.validateInference("test input", model_ids);

    EXPECT_FALSE(result.validation_passed);
}

// Test 6: Agreement score calculation
TEST_F(InferenceSharingSystemTest, AgreementScoreCalculation) {
    AdvancedInferenceSharing sharing(config);

    InferenceResult result1, result2;
    result1.output = "The cat sat on the mat";
    result2.output = "The cat sat on the mat";

    float agreement = sharing.calculateAgreementScore(result1, result2);
    EXPECT_GT(agreement, 0.5f);

    result2.output = "Completely different text";
    agreement = sharing.calculateAgreementScore(result1, result2);
    EXPECT_LT(agreement, 0.5f);
}

// Test 7: Consensus determination
TEST_F(InferenceSharingSystemTest, ConsensusDetermination) {
    AdvancedInferenceSharing sharing(config);

    std::vector<InferenceResult> results;
    for (int i = 0; i < 3; ++i) {
        InferenceResult result;
        result.model_id = "model" + std::to_string(i);
        result.output = "Similar output " + std::to_string(i);
        result.confidence = 0.8f + i * 0.05f;
        results.push_back(result);
    }

    std::string consensus = sharing.determineConsensus(results);
    EXPECT_FALSE(consensus.empty());
}

// Test 8: Collaborative inference with weighted average
TEST_F(InferenceSharingSystemTest, CollaborativeInferenceWeightedAverage) {
    AdvancedInferenceSharing sharing(config);

    std::vector<std::string> model_ids = {"model1", "model2", "model3"};
    auto result = sharing.collaborativeInference(
        "test input", model_ids, "weighted_average");

    EXPECT_TRUE(result.success);
    EXPECT_EQ(result.participating_models.size(), 3);
    EXPECT_EQ(result.partial_results.size(), 3);
    EXPECT_FALSE(result.final_output.empty());
    EXPECT_GT(result.combined_confidence, 0.0f);
    EXPECT_EQ(result.contribution_weights.size(), 3);
}

// Test 9: Collaborative inference with ensemble
TEST_F(InferenceSharingSystemTest, CollaborativeInferenceEnsemble) {
    AdvancedInferenceSharing sharing(config);

    std::vector<std::string> model_ids = {"model1", "model2"};
    auto result = sharing.collaborativeInference(
        "test input", model_ids, "ensemble");

    EXPECT_TRUE(result.success);
    EXPECT_FALSE(result.final_output.empty());
}

// Test 10: Collaborative inference with highest confidence
TEST_F(InferenceSharingSystemTest, CollaborativeInferenceHighestConfidence) {
    AdvancedInferenceSharing sharing(config);

    std::vector<std::string> model_ids = {"model1", "model2", "model3"};
    auto result = sharing.collaborativeInference(
        "test input", model_ids, "highest_confidence");

    EXPECT_TRUE(result.success);
    EXPECT_GT(result.combined_confidence, 0.0f);
}

// Test 11: Contribution weight management
TEST_F(InferenceSharingSystemTest, ContributionWeightManagement) {
    AdvancedInferenceSharing sharing(config);

    sharing.updateContributionWeights("model1", 0.9f);
    sharing.updateContributionWeights("model2", 0.7f);

    float weight1 = sharing.getModelContributionWeight("model1");
    float weight2 = sharing.getModelContributionWeight("model2");

    EXPECT_GT(weight1, weight2);
    
    // Update again with exponential moving average
    sharing.updateContributionWeights("model1", 0.5f);
    float updated_weight = sharing.getModelContributionWeight("model1");
    EXPECT_LT(updated_weight, weight1);
}

// Test 12: Inference history recording
TEST_F(InferenceSharingSystemTest, InferenceHistoryRecording) {
    AdvancedInferenceSharing sharing(config);

    for (int i = 0; i < 10; ++i) {
        InferenceResult result;
        result.model_id = "model1";
        result.input = "input" + std::to_string(i);
        result.output = "output" + std::to_string(i);
        result.confidence = 0.8f;
        sharing.recordInference(result);
    }

    auto history = sharing.getInferenceHistory("model1", 5);
    EXPECT_EQ(history.size(), 5);
}

// Test 13: Inference history size limit
TEST_F(InferenceSharingSystemTest, InferenceHistorySizeLimit) {
    config.max_inference_history = 10;
    AdvancedInferenceSharing sharing(config);

    for (int i = 0; i < 20; ++i) {
        InferenceResult result;
        result.model_id = "model1";
        result.input = "input" + std::to_string(i);
        sharing.recordInference(result);
    }

    auto history = sharing.getInferenceHistory("model1", 100);
    EXPECT_LE(history.size(), 10);
}

// Test 14: Clear inference history
TEST_F(InferenceSharingSystemTest, ClearInferenceHistory) {
    AdvancedInferenceSharing sharing(config);

    InferenceResult result;
    result.model_id = "model1";
    sharing.recordInference(result);

    sharing.clearInferenceHistory();
    auto history = sharing.getInferenceHistory("model1", 10);
    EXPECT_EQ(history.size(), 0);
}

// Test 15: Performance metrics tracking
TEST_F(InferenceSharingSystemTest, PerformanceMetricsTracking) {
    AdvancedInferenceSharing sharing(config);

    // Perform various operations
    sharing.transferKnowledge("model1", "model2", {"domain1"});
    sharing.validateInference("input", {"model1", "model2"});
    sharing.collaborativeInference("input", {"model1", "model2"}, "ensemble");

    auto metrics = sharing.getPerformanceMetrics();
    EXPECT_GT(metrics.total_knowledge_transfers, 0);
    EXPECT_GT(metrics.total_cross_validations, 0);
    EXPECT_GT(metrics.total_collaborative_inferences, 0);
}

// Test 16: Cache hit rate tracking
TEST_F(InferenceSharingSystemTest, CacheHitRateTracking) {
    AdvancedInferenceSharing sharing(config);

    auto knowledge = std::make_shared<Knowledge>();
    knowledge->domain = "test_domain";
    sharing.cacheKnowledge(knowledge);

    // Hit
    sharing.retrieveKnowledge("test_domain", 1);
    // Miss
    sharing.retrieveKnowledge("nonexistent_domain", 1);

    auto metrics = sharing.getPerformanceMetrics();
    EXPECT_GT(metrics.knowledge_cache_hits, 0);
    EXPECT_GT(metrics.knowledge_cache_misses, 0);
    EXPECT_GT(metrics.cache_hit_rate, 0.0);
}

// Test 17: Configuration update
TEST_F(InferenceSharingSystemTest, ConfigurationUpdate) {
    AdvancedInferenceSharing sharing(config);

    InferenceSharingConfig new_config = config;
    new_config.confidence_threshold = 0.9f;
    sharing.updateConfig(new_config);

    auto retrieved_config = sharing.getConfig();
    EXPECT_FLOAT_EQ(retrieved_config.confidence_threshold, 0.9f);
}

// Test 18: InferenceSharingManager - Create and destroy
TEST_F(InferenceSharingSystemTest, ManagerCreateDestroy) {
    auto& manager = InferenceSharingManager::getInstance();

    ASSERT_TRUE(manager.createSharingSystem("system1", config));
    EXPECT_EQ(manager.getActiveSharingSystemCount(), 1);

    ASSERT_TRUE(manager.destroySharingSystem("system1"));
    EXPECT_EQ(manager.getActiveSharingSystemCount(), 0);
}

// Test 19: InferenceSharingManager - Get sharing system
TEST_F(InferenceSharingSystemTest, ManagerGetSharingSystem) {
    auto& manager = InferenceSharingManager::getInstance();

    manager.createSharingSystem("system1", config);
    auto system = manager.getSharingSystem("system1");
    ASSERT_NE(system, nullptr);

    manager.destroySharingSystem("system1");
}

// Test 20: InferenceSharingManager - Global knowledge sharing
TEST_F(InferenceSharingSystemTest, ManagerGlobalKnowledgeSharing) {
    auto& manager = InferenceSharingManager::getInstance();

    auto knowledge = std::make_shared<Knowledge>();
    knowledge->id = "global_k1";
    knowledge->domain = "global_domain";
    knowledge->confidence = 0.9f;

    ASSERT_TRUE(manager.shareKnowledgeGlobally(knowledge));
    EXPECT_GT(manager.getTotalKnowledgeCount(), 0);

    auto retrieved = manager.queryGlobalKnowledge("global_domain", 10);
    EXPECT_GT(retrieved.size(), 0);
}

// Test 21: InferenceSharingManager - System-wide validation
TEST_F(InferenceSharingSystemTest, ManagerSystemWideValidation) {
    auto& manager = InferenceSharingManager::getInstance();

    manager.createSharingSystem("system1", config);
    manager.createSharingSystem("system2", config);

    auto result = manager.validateAcrossSystems(
        "test input", {"system1", "system2"});

    EXPECT_GE(result.model_ids.size(), 2);
    
    manager.destroySharingSystem("system1");
    manager.destroySharingSystem("system2");
}

// Test 22: GlobalInferenceSharingSystem - Initialize and shutdown
TEST_F(InferenceSharingSystemTest, GlobalSystemInitializeShutdown) {
    auto& global = GlobalInferenceSharingSystem::getInstance();

    ASSERT_TRUE(global.initialize(config));
    EXPECT_TRUE(global.isInitialized());

    ASSERT_TRUE(global.shutdown());
    EXPECT_FALSE(global.isInitialized());
}

// Test 23: GlobalInferenceSharingSystem - Knowledge graph
TEST_F(InferenceSharingSystemTest, GlobalSystemKnowledgeGraph) {
    auto& global = GlobalInferenceSharingSystem::getInstance();
    global.initialize(config);

    std::vector<std::shared_ptr<Knowledge>> knowledge_list;
    for (int i = 0; i < 5; ++i) {
        auto k = std::make_shared<Knowledge>();
        k->id = "gk" + std::to_string(i);
        k->domain = "test_domain";
        k->confidence = 0.8f;
        k->embedding = std::vector<float>(128, 0.5f);
        knowledge_list.push_back(k);
    }

    ASSERT_TRUE(global.buildKnowledgeGraph(knowledge_list));

    auto metrics = global.getSystemMetrics();
    EXPECT_GT(metrics.knowledge_graph_nodes, 0);

    global.shutdown();
}

// Test 24: GlobalInferenceSharingSystem - Query knowledge graph
TEST_F(InferenceSharingSystemTest, GlobalSystemQueryKnowledgeGraph) {
    auto& global = GlobalInferenceSharingSystem::getInstance();
    global.initialize(config);

    std::vector<std::shared_ptr<Knowledge>> knowledge_list;
    auto k = std::make_shared<Knowledge>();
    k->id = "query_k1";
    k->domain = "query_domain";
    k->confidence = 0.9f;
    knowledge_list.push_back(k);

    global.buildKnowledgeGraph(knowledge_list);

    auto results = global.queryKnowledgeGraph("query_domain", 10);
    EXPECT_GT(results.size(), 0);

    global.shutdown();
}

// Test 25: GlobalInferenceSharingSystem - Update knowledge relations
TEST_F(InferenceSharingSystemTest, GlobalSystemUpdateKnowledgeRelations) {
    auto& global = GlobalInferenceSharingSystem::getInstance();
    global.initialize(config);

    std::vector<std::shared_ptr<Knowledge>> knowledge_list;
    for (int i = 0; i < 3; ++i) {
        auto k = std::make_shared<Knowledge>();
        k->id = "rel_k" + std::to_string(i);
        k->domain = "relation_domain";
        knowledge_list.push_back(k);
    }

    global.buildKnowledgeGraph(knowledge_list);
    global.updateKnowledgeRelations("rel_k0", "rel_k1", 0.95f);

    global.shutdown();
}

// Test 26: GlobalInferenceSharingSystem - Multi-model coordination
TEST_F(InferenceSharingSystemTest, GlobalSystemMultiModelCoordination) {
    auto& global = GlobalInferenceSharingSystem::getInstance();
    global.initialize(config);

    auto& manager = InferenceSharingManager::getInstance();
    manager.createSharingSystem("coord_model1", config);
    manager.createSharingSystem("coord_model2", config);

    auto result = global.coordinateMultiModelInference(
        "test input",
        {"coord_model1", "coord_model2"},
        "ensemble");

    EXPECT_EQ(result.participating_models.size(), 2);

    manager.destroySharingSystem("coord_model1");
    manager.destroySharingSystem("coord_model2");
    global.shutdown();
}

// Test 27: GlobalInferenceSharingSystem - System metrics
TEST_F(InferenceSharingSystemTest, GlobalSystemMetrics) {
    auto& global = GlobalInferenceSharingSystem::getInstance();
    global.initialize(config);

    auto& manager = InferenceSharingManager::getInstance();
    manager.createSharingSystem("metrics_system1", config);

    auto metrics = global.getSystemMetrics();
    EXPECT_GT(metrics.total_sharing_systems, 0);

    manager.destroySharingSystem("metrics_system1");
    global.shutdown();
}

// Test 28: Concurrent knowledge operations
TEST_F(InferenceSharingSystemTest, ConcurrentKnowledgeOperations) {
    AdvancedInferenceSharing sharing(config);

    std::vector<std::thread> threads;
    for (int t = 0; t < 5; ++t) {
        threads.emplace_back([&sharing, t]() {
            for (int i = 0; i < 10; ++i) {
                auto knowledge = std::make_shared<Knowledge>();
                knowledge->id = "thread" + std::to_string(t) + "_k" + std::to_string(i);
                knowledge->domain = "concurrent_domain";
                knowledge->confidence = 0.8f;
                sharing.cacheKnowledge(knowledge);
            }
        });
    }

    for (auto& thread : threads) {
        thread.join();
    }

    EXPECT_EQ(sharing.getKnowledgeCacheSize(), 50);
}

// Test 29: Concurrent validation operations
TEST_F(InferenceSharingSystemTest, ConcurrentValidationOperations) {
    AdvancedInferenceSharing sharing(config);

    std::vector<std::thread> threads;
    std::atomic<int> successful_validations{0};

    for (int t = 0; t < 3; ++t) {
        threads.emplace_back([&sharing, &successful_validations, t]() {
            for (int i = 0; i < 5; ++i) {
                auto result = sharing.validateInference(
                    "input" + std::to_string(i),
                    {"model1", "model2", "model3"});
                if (result.validation_passed || !result.model_ids.empty()) {
                    ++successful_validations;
                }
            }
        });
    }

    for (auto& thread : threads) {
        thread.join();
    }

    EXPECT_GT(successful_validations.load(), 0);
}

// Test 30: Patent Claim - Knowledge Transfer System
TEST_F(InferenceSharingSystemTest, PatentClaimKnowledgeTransfer) {
    AdvancedInferenceSharing sharing(config);

    // Setup: Create knowledge base for source model
    for (int i = 0; i < 10; ++i) {
        auto knowledge = std::make_shared<Knowledge>();
        knowledge->id = "patent_k" + std::to_string(i);
        knowledge->source_model = "expert_model";
        knowledge->domain = "specialized_domain";
        knowledge->confidence = 0.85f + (i % 3) * 0.05f;
        knowledge->usage_count = i * 10;
        sharing.cacheKnowledge(knowledge);
    }

    // Execute: Transfer knowledge from expert to new model
    auto transfer_result = sharing.transferKnowledge(
        "expert_model",
        "new_model",
        {"specialized_domain"});

    // Verify: Knowledge transfer successful with quality metrics
    ASSERT_TRUE(transfer_result.success);
    EXPECT_GT(transfer_result.transfer_count, 0);
    EXPECT_GE(transfer_result.transfer_quality, config.confidence_threshold);
    EXPECT_LT(transfer_result.transfer_time.count(), 1000);  // < 1 second
    
    // Patent claim: System enables knowledge transfer between models
    // with quality tracking and minimal latency
}

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}

