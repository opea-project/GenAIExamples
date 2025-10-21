#include <gtest/gtest.h>
#include "engine.h"
#include <string>
#include <thread>
#include <vector>

class EngineTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Initialize engine before each test
        ASSERT_TRUE(initialize_engine(0));
    }

    void TearDown() override {
        // Shutdown engine after each test
        shutdown_engine();
    }
};

TEST_F(EngineTest, BasicInitialization) {
    // Test that engine initializes successfully
    EXPECT_TRUE(initialize_engine(0));
}

TEST_F(EngineTest, ProcessRequest) {
    // Test basic request processing
    const char* request = "{\"model\": \"test-model\", \"prompt\": \"Hello, world!\"}";
    char response[1024];
    const char* result = process_request(request, response);
    
    EXPECT_NE(result, nullptr);
    EXPECT_TRUE(strlen(result) > 0);
}

TEST_F(EngineTest, InvalidRequest) {
    // Test handling of invalid JSON
    const char* request = "invalid json";
    char response[1024];
    const char* result = process_request(request, response);
    
    EXPECT_EQ(result, nullptr);
}

TEST_F(EngineTest, ConcurrentRequests) {
    // Test concurrent request processing
    const int num_threads = 4;
    const int requests_per_thread = 10;
    std::vector<std::thread> threads;
    
    for (int i = 0; i < num_threads; ++i) {
        threads.emplace_back([requests_per_thread]() {
            for (int j = 0; j < requests_per_thread; ++j) {
                std::string request = "{\"model\": \"test-model\", \"prompt\": \"Thread " + 
                                    std::to_string(i) + " Request " + std::to_string(j) + "\"}";
                char response[1024];
                const char* result = process_request(request.c_str(), response);
                EXPECT_NE(result, nullptr);
            }
        });
    }
    
    for (auto& thread : threads) {
        thread.join();
    }
}

TEST_F(EngineTest, MultipleDevices) {
    // Test initialization on different devices
    int num_devices;
    cudaGetDeviceCount(&num_devices);
    
    for (int i = 0; i < num_devices; ++i) {
        EXPECT_TRUE(initialize_engine(i));
        shutdown_engine();
    }
}

TEST_F(EngineTest, ModelNotFound) {
    // Test handling of non-existent model
    const char* request = "{\"model\": \"non-existent-model\", \"prompt\": \"Hello\"}";
    char response[1024];
    const char* result = process_request(request, response);
    
    EXPECT_EQ(result, nullptr);
}

TEST_F(EngineTest, LargePrompt) {
    // Test handling of large prompts
    std::string large_prompt(10000, 'a');
    std::string request = "{\"model\": \"test-model\", \"prompt\": \"" + large_prompt + "\"}";
    char response[1024];
    const char* result = process_request(request.c_str(), response);
    
    EXPECT_NE(result, nullptr);
}

TEST_F(EngineTest, ShutdownDuringProcessing) {
    // Test graceful shutdown during request processing
    std::thread processing_thread([]() {
        const char* request = "{\"model\": \"test-model\", \"prompt\": \"Long running request\"}";
        char response[1024];
        process_request(request, response);
    });
    
    // Give the thread time to start processing
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    
    // Shutdown while request is being processed
    shutdown_engine();
    processing_thread.join();
    
    // Verify engine can be reinitialized
    EXPECT_TRUE(initialize_engine(0));
} 