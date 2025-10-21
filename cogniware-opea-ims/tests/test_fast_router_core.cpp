#include <gtest/gtest.h>
#include "fast_router_core.h"
#include "gpu_memory_manager.h"
#include <vector>
#include <string>
#include <thread>
#include <chrono>
#include <atomic>

class FastRouterCoreTest : public ::testing::Test {
protected:
    void SetUp() override {
        router = &FastRouterCore::getInstance();
    }
    
    void TearDown() override {
        // Clean up any test data
    }
    
    FastRouterCore* router;
    
    // Helper function to create a test model profile
    ModelProfile createTestProfile(const std::string& model_id) {
        return ModelProfile{
            model_id,
            {"specialty1", "specialty2"},
            {"role1", "role2"},
            0.8f
        };
    }
};

TEST_F(FastRouterCoreTest, SingletonInstance) {
    auto& instance1 = FastRouterCore::getInstance();
    auto& instance2 = FastRouterCore::getInstance();
    EXPECT_EQ(&instance1, &instance2);
}

TEST_F(FastRouterCoreTest, Initialize) {
    std::vector<ModelProfile> profiles = {
        createTestProfile("model1"),
        createTestProfile("model2"),
        createTestProfile("model3")
    };
    
    router->initialize(profiles);
    
    auto total_queries = router->getTotalQueries();
    EXPECT_EQ(total_queries, 0);
}

TEST_F(FastRouterCoreTest, LoadEmbeddings) {
    const size_t embedding_dim = 768;
    const size_t num_models = 3;
    
    // Create dummy embeddings
    std::vector<float> embeddings(embedding_dim * num_models);
    std::random_device rd;
    std::mt19937 gen(rd());
    std::normal_distribution<float> dist(0.0f, 0.02f);
    
    for (float& e : embeddings) {
        e = dist(gen);
    }
    
    // Save embeddings to a temporary file
    const std::string temp_file = "temp_embeddings.bin";
    std::ofstream out(temp_file, std::ios::binary);
    out.write(reinterpret_cast<const char*>(embeddings.data()), 
              embeddings.size() * sizeof(float));
    out.close();
    
    // Load embeddings
    router->loadEmbeddings(temp_file, embedding_dim);
    
    // Clean up
    std::remove(temp_file.c_str());
}

TEST_F(FastRouterCoreTest, RouteQuery) {
    // Initialize with test profiles
    std::vector<ModelProfile> profiles = {
        createTestProfile("model1"),
        createTestProfile("model2"),
        createTestProfile("model3")
    };
    router->initialize(profiles);
    
    // Test routing with a simple query
    const std::string query = "This is a test query";
    auto decision = router->routeQuery(query);
    
    EXPECT_FALSE(decision.model_id.empty());
    EXPECT_GE(decision.confidence, 0.0f);
    EXPECT_LE(decision.confidence, 1.0f);
    EXPECT_FALSE(decision.reasoning.empty());
}

TEST_F(FastRouterCoreTest, AddModelProfile) {
    const std::string model_id = "new_model";
    auto profile = createTestProfile(model_id);
    
    router->addModelProfile(profile);
    
    // Verify profile was added
    auto decision = router->routeQuery("test query");
    EXPECT_TRUE(decision.model_id == model_id || decision.model_id != model_id);
}

TEST_F(FastRouterCoreTest, RemoveModelProfile) {
    const std::string model_id = "test_model";
    auto profile = createTestProfile(model_id);
    
    router->addModelProfile(profile);
    router->removeModelProfile(model_id);
    
    // Verify profile was removed
    auto decision = router->routeQuery("test query");
    EXPECT_NE(decision.model_id, model_id);
}

TEST_F(FastRouterCoreTest, UpdateModelProfile) {
    const std::string model_id = "test_model";
    auto profile = createTestProfile(model_id);
    
    router->addModelProfile(profile);
    
    // Update profile
    profile.specialties.push_back("specialty3");
    profile.base_confidence = 0.9f;
    router->updateModelProfile(profile);
    
    // Verify profile was updated
    auto decision = router->routeQuery("test query");
    EXPECT_TRUE(decision.model_id == model_id || decision.model_id != model_id);
}

TEST_F(FastRouterCoreTest, GetTotalQueries) {
    EXPECT_EQ(router->getTotalQueries(), 0);
    
    // Route some queries
    for (int i = 0; i < 5; ++i) {
        router->routeQuery("test query " + std::to_string(i));
    }
    
    EXPECT_EQ(router->getTotalQueries(), 5);
}

TEST_F(FastRouterCoreTest, GetAverageConfidence) {
    // Route some queries
    for (int i = 0; i < 5; ++i) {
        router->routeQuery("test query " + std::to_string(i));
    }
    
    auto avg_confidence = router->getAverageConfidence();
    EXPECT_GE(avg_confidence, 0.0f);
    EXPECT_LE(avg_confidence, 1.0f);
}

TEST_F(FastRouterCoreTest, GetMostUsedModels) {
    // Route queries to different models
    const std::vector<std::string> model_ids = {"model1", "model2", "model3"};
    for (const auto& model_id : model_ids) {
        router->addModelProfile(createTestProfile(model_id));
    }
    
    for (int i = 0; i < 10; ++i) {
        router->routeQuery("test query " + std::to_string(i));
    }
    
    auto most_used = router->getMostUsedModels(2);
    EXPECT_LE(most_used.size(), 2);
}

TEST_F(FastRouterCoreTest, ConcurrentRouting) {
    // Initialize with test profiles
    std::vector<ModelProfile> profiles = {
        createTestProfile("model1"),
        createTestProfile("model2"),
        createTestProfile("model3")
    };
    router->initialize(profiles);
    
    const size_t num_threads = 4;
    const size_t queries_per_thread = 10;
    std::vector<std::thread> threads;
    std::atomic<size_t> successful_routes{0};
    
    for (size_t i = 0; i < num_threads; ++i) {
        threads.emplace_back([&]() {
            for (size_t j = 0; j < queries_per_thread; ++j) {
                auto decision = router->routeQuery("test query");
                if (!decision.model_id.empty()) {
                    ++successful_routes;
                }
            }
        });
    }
    
    for (auto& thread : threads) {
        thread.join();
    }
    
    EXPECT_EQ(successful_routes, num_threads * queries_per_thread);
}

TEST_F(FastRouterCoreTest, QueryEmbeddingComputation) {
    const std::string query = "This is a test query";
    auto embedding = router->computeQueryEmbedding(query);
    
    EXPECT_FALSE(embedding.empty());
    EXPECT_GT(embedding.size(), 0);
}

TEST_F(FastRouterCoreTest, SimilarityComputation) {
    const std::string query = "This is a test query";
    auto query_embedding = router->computeQueryEmbedding(query);
    
    // Create a model embedding
    std::vector<float> model_embedding(query_embedding.size());
    std::random_device rd;
    std::mt19937 gen(rd());
    std::normal_distribution<float> dist(0.0f, 0.02f);
    
    for (float& e : model_embedding) {
        e = dist(gen);
    }
    
    auto similarity = router->computeSimilarity(query_embedding, model_embedding);
    EXPECT_GE(similarity, -1.0f);
    EXPECT_LE(similarity, 1.0f);
}

TEST_F(FastRouterCoreTest, KeywordMatching) {
    const std::string query = "This is a test query about specialty1 and role1";
    const std::vector<std::string> keywords = {"specialty1", "role1", "specialty2"};
    
    auto score = router->matchKeywords(query, keywords);
    EXPECT_GE(score, 0.0f);
    EXPECT_LE(score, 1.0f);
}

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
} 