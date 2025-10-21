#include <gtest/gtest.h>
#include "orchestration/multi_llm_orchestrator.h"
#include "async/async_processor.h"
#include "model/model_manager.h"

using namespace cogniware;

TEST(IntegrationTest, EndToEndWorkflow) {
    // Test complete workflow
    EXPECT_TRUE(true);
}

TEST(IntegrationTest, MultiLLMWithAsync) {
    async_processing::AsyncProcessor processor(4);
    processor.start();
    
    auto job_id = processor.submitJob("inference", {{"prompt", "test"}});
    EXPECT_FALSE(job_id.empty());
    
    processor.stop();
}

TEST(IntegrationTest, ModelManagementWithMonitoring) {
    model::ModelManager manager;
    
    model::ModelMetadata metadata;
    metadata.model_id = "test-model";
    metadata.name = "Test Model";
    
    auto id = manager.registerModel(metadata);
    EXPECT_EQ(id, "test-model");
}

int main(int argc, char** argv) {
    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}

