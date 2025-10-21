#include <gtest/gtest.h>
#include "concurrency_controller.h"
#include "llm_instance_manager.h"
#include <vector>
#include <string>
#include <thread>
#include <chrono>
#include <atomic>

class ConcurrencyControllerTest : public ::testing::Test {
protected:
    void SetUp() override {
        controller = &ConcurrencyController::getInstance();
        instance_manager = &LLMInstanceManager::getInstance();
    }
    
    void TearDown() override {
        controller->stop();
        // Clean up any test instances
        auto instances = instance_manager->getLoadedModelIds();
        for (const auto& model_id : instances) {
            instance_manager->removeInstance(model_id);
        }
    }
    
    ConcurrencyController* controller;
    LLMInstanceManager* instance_manager;
    
    // Helper function to create a test request
    InferenceRequest createTestRequest(const std::string& model_id) {
        return InferenceRequest{
            model_id,
            "Test prompt",
            10,  // max_tokens
            [](const std::string& output) {
                // Empty callback for testing
            }
        };
    }
};

TEST_F(ConcurrencyControllerTest, SingletonInstance) {
    auto& instance1 = ConcurrencyController::getInstance();
    auto& instance2 = ConcurrencyController::getInstance();
    EXPECT_EQ(&instance1, &instance2);
}

TEST_F(ConcurrencyControllerTest, StartStop) {
    EXPECT_FALSE(controller->isRunning());
    
    controller->start();
    EXPECT_TRUE(controller->isRunning());
    
    controller->stop();
    EXPECT_FALSE(controller->isRunning());
}

TEST_F(ConcurrencyControllerTest, SubmitRequest) {
    controller->start();
    
    const std::string model_id = "test_model";
    instance_manager->createInstance(model_id, "path/to/model.gguf", ModelFormat::GGUF);
    
    auto request = createTestRequest(model_id);
    controller->submitRequest(request);
    
    // Wait for request to be processed
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    
    EXPECT_EQ(controller->getCurrentQueueSize(), 0);
    EXPECT_EQ(controller->getActiveRequestCount(), 0);
}

TEST_F(ConcurrencyControllerTest, CancelRequest) {
    controller->start();
    
    const std::string model_id = "test_model";
    instance_manager->createInstance(model_id, "path/to/model.gguf", ModelFormat::GGUF);
    
    auto request = createTestRequest(model_id);
    controller->submitRequest(request);
    
    // Cancel request immediately
    controller->cancelRequest(request.request_id);
    
    // Wait for cancellation to take effect
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    
    EXPECT_EQ(controller->getCurrentQueueSize(), 0);
    EXPECT_EQ(controller->getActiveRequestCount(), 0);
}

TEST_F(LLMInstanceManagerTest, SetMaxConcurrentRequests) {
    const size_t max_requests = 5;
    controller->setMaxConcurrentRequests(max_requests);
    
    // Submit more requests than the limit
    const std::string model_id = "test_model";
    instance_manager->createInstance(model_id, "path/to/model.gguf", ModelFormat::GGUF);
    
    std::vector<InferenceRequest> requests;
    for (size_t i = 0; i < max_requests + 2; ++i) {
        requests.push_back(createTestRequest(model_id));
        controller->submitRequest(requests.back());
    }
    
    // Wait for processing to start
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    
    EXPECT_LE(controller->getActiveRequestCount(), max_requests);
}

TEST_F(LLMInstanceManagerTest, SetMaxBatchSize) {
    const size_t max_batch_size = 3;
    controller->setMaxBatchSize(max_batch_size);
    
    // Submit multiple requests
    const std::string model_id = "test_model";
    instance_manager->createInstance(model_id, "path/to/model.gguf", ModelFormat::GGUF);
    
    std::vector<InferenceRequest> requests;
    for (size_t i = 0; i < 5; ++i) {
        requests.push_back(createTestRequest(model_id));
        controller->submitRequest(requests.back());
    }
    
    // Wait for processing to start
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    
    EXPECT_LE(controller->getCurrentQueueSize(), 5 - max_batch_size);
}

TEST_F(LLMInstanceManagerTest, ConcurrentRequestSubmission) {
    controller->start();
    
    const std::string model_id = "test_model";
    instance_manager->createInstance(model_id, "path/to/model.gguf", ModelFormat::GGUF);
    
    const size_t num_threads = 4;
    const size_t requests_per_thread = 5;
    std::vector<std::thread> threads;
    std::atomic<size_t> total_requests{0};
    
    for (size_t i = 0; i < num_threads; ++i) {
        threads.emplace_back([&]() {
            for (size_t j = 0; j < requests_per_thread; ++j) {
                auto request = createTestRequest(model_id);
                controller->submitRequest(request);
                ++total_requests;
            }
        });
    }
    
    for (auto& thread : threads) {
        thread.join();
    }
    
    // Wait for requests to be processed
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    
    EXPECT_EQ(total_requests, num_threads * requests_per_thread);
    EXPECT_EQ(controller->getCurrentQueueSize(), 0);
    EXPECT_EQ(controller->getActiveRequestCount(), 0);
}

TEST_F(LLMInstanceManagerTest, RequestQueueSize) {
    controller->start();
    
    const std::string model_id = "test_model";
    instance_manager->createInstance(model_id, "path/to/model.gguf", ModelFormat::GGUF);
    
    // Submit multiple requests
    const size_t num_requests = 10;
    std::vector<InferenceRequest> requests;
    
    for (size_t i = 0; i < num_requests; ++i) {
        requests.push_back(createTestRequest(model_id));
        controller->submitRequest(requests.back());
    }
    
    // Verify queue size
    EXPECT_EQ(controller->getCurrentQueueSize(), num_requests);
    
    // Wait for processing to start
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    
    // Queue size should decrease as requests are processed
    EXPECT_LT(controller->getCurrentQueueSize(), num_requests);
}

TEST_F(LLMInstanceManagerTest, ActiveRequestCount) {
    controller->start();
    
    const std::string model_id = "test_model";
    instance_manager->createInstance(model_id, "path/to/model.gguf", ModelFormat::GGUF);
    
    // Submit a request
    auto request = createTestRequest(model_id);
    controller->submitRequest(request);
    
    // Wait for processing to start
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    
    // Verify active request count
    EXPECT_LE(controller->getActiveRequestCount(), 1);
    
    // Wait for request to complete
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    
    EXPECT_EQ(controller->getActiveRequestCount(), 0);
}

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
} 