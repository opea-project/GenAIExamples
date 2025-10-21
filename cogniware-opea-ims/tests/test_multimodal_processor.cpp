#include <gtest/gtest.h>
#include "multimodal/multimodal_processor.h"
#include <thread>
#include <chrono>

using namespace cogniware::multimodal;

class MultimodalProcessorTest : public ::testing::Test {
protected:
    void SetUp() override {
        config.max_text_length = 512;
        config.image_width = 224;
        config.image_height = 224;
        config.audio_sample_rate = 16000;
        config.video_fps = 30;
        config.enable_fusion = true;
        config.enable_caching = true;
    }

    void TearDown() override {
        // Cleanup
    }

    MultimodalConfig config;

    TextInput createTextInput(const std::string& text) {
        TextInput input;
        input.text = text;
        input.language = "en";
        return input;
    }

    ImageInput createImageInput(int width, int height) {
        ImageInput input;
        input.width = width;
        input.height = height;
        input.channels = 3;
        input.format = ImageFormat::RGB;
        input.data.resize(width * height * 3, 128);
        return input;
    }

    AudioInput createAudioInput(int duration_ms) {
        AudioInput input;
        input.sample_rate = 16000;
        input.channels = 1;
        input.format = AudioFormat::PCM_F32LE;
        input.duration = std::chrono::milliseconds(duration_ms);
        int num_samples = (duration_ms * input.sample_rate) / 1000;
        input.samples.resize(num_samples, 0.5f);
        return input;
    }

    VideoInput createVideoInput(int num_frames) {
        VideoInput input;
        input.width = 224;
        input.height = 224;
        input.fps = 30;
        input.format = VideoFormat::H264;
        input.duration = std::chrono::milliseconds(num_frames * 33);
        input.frames.resize(num_frames);
        for (auto& frame : input.frames) {
            frame.resize(input.width * input.height * 3, 128);
        }
        return input;
    }
};

// Test 1: Basic text processing
TEST_F(MultimodalProcessorTest, BasicTextProcessing) {
    AdvancedMultimodalProcessor processor(config);
    
    TextInput input = createTextInput("Hello, world!");
    auto result = processor.processText(input);
    
    EXPECT_TRUE(result.success);
    EXPECT_EQ(result.modality, ModalityType::TEXT);
    EXPECT_FALSE(result.embeddings.empty());
    EXPECT_GT(result.scores["confidence"], 0.0f);
}

// Test 2: Basic image processing
TEST_F(MultimodalProcessorTest, BasicImageProcessing) {
    AdvancedMultimodalProcessor processor(config);
    
    ImageInput input = createImageInput(224, 224);
    auto result = processor.processImage(input);
    
    EXPECT_TRUE(result.success);
    EXPECT_EQ(result.modality, ModalityType::IMAGE);
    EXPECT_FALSE(result.embeddings.empty());
}

// Test 3: Basic audio processing
TEST_F(MultimodalProcessorTest, BasicAudioProcessing) {
    AdvancedMultimodalProcessor processor(config);
    
    AudioInput input = createAudioInput(1000);  // 1 second
    auto result = processor.processAudio(input);
    
    EXPECT_TRUE(result.success);
    EXPECT_EQ(result.modality, ModalityType::AUDIO);
    EXPECT_FALSE(result.embeddings.empty());
}

// Test 4: Basic video processing
TEST_F(MultimodalProcessorTest, BasicVideoProcessing) {
    AdvancedMultimodalProcessor processor(config);
    
    VideoInput input = createVideoInput(30);  // 30 frames
    auto result = processor.processVideo(input);
    
    EXPECT_TRUE(result.success);
    EXPECT_EQ(result.modality, ModalityType::VIDEO);
    EXPECT_FALSE(result.embeddings.empty());
}

// Test 5: Text preprocessing
TEST_F(MultimodalProcessorTest, TextPreprocessing) {
    AdvancedMultimodalProcessor processor(config);
    
    std::string long_text(1000, 'a');
    TextInput input = createTextInput(long_text);
    
    auto preprocessed = processor.preprocessText(input);
    EXPECT_LE(preprocessed.text.length(), config.max_text_length);
}

// Test 6: Image preprocessing
TEST_F(MultimodalProcessorTest, ImagePreprocessing) {
    AdvancedMultimodalProcessor processor(config);
    
    ImageInput input = createImageInput(512, 512);
    auto preprocessed = processor.preprocessImage(input);
    
    EXPECT_EQ(preprocessed.width, config.image_width);
    EXPECT_EQ(preprocessed.height, config.image_height);
}

// Test 7: Audio preprocessing
TEST_F(MultimodalProcessorTest, AudioPreprocessing) {
    AdvancedMultimodalProcessor processor(config);
    
    AudioInput input = createAudioInput(1000);
    input.sample_rate = 44100;  // Different sample rate
    
    auto preprocessed = processor.preprocessAudio(input);
    EXPECT_EQ(preprocessed.sample_rate, config.audio_sample_rate);
}

// Test 8: Video preprocessing
TEST_F(MultimodalProcessorTest, VideoPreprocessing) {
    config.max_video_frames = 50;
    AdvancedMultimodalProcessor processor(config);
    
    VideoInput input = createVideoInput(100);  // More than max
    auto preprocessed = processor.preprocessVideo(input);
    
    EXPECT_LE(preprocessed.frames.size(), config.max_video_frames);
}

// Test 9: Text embedding extraction
TEST_F(MultimodalProcessorTest, TextEmbeddingExtraction) {
    AdvancedMultimodalProcessor processor(config);
    
    TextInput input = createTextInput("Test text");
    auto embeddings = processor.extractTextEmbeddings(input);
    
    EXPECT_FALSE(embeddings.empty());
    EXPECT_EQ(embeddings.size(), 768);  // BERT-like dimension
}

// Test 10: Multimodal processing with text and image
TEST_F(MultimodalProcessorTest, MultimodalTextImage) {
    AdvancedMultimodalProcessor processor(config);
    
    MultimodalInput input;
    input.input_id = "test1";
    input.primary_modality = ModalityType::TEXT;
    input.text = std::make_shared<TextInput>(createTextInput("A beautiful sunset"));
    input.image = std::make_shared<ImageInput>(createImageInput(224, 224));
    
    auto result = processor.processMultimodal(input);
    
    EXPECT_TRUE(result.output.success);
    EXPECT_EQ(result.total_modalities_processed, 2);
    EXPECT_FALSE(result.output.fused_embeddings.empty());
}

// Test 11: Multimodal processing with all modalities
TEST_F(MultimodalProcessorTest, MultimodalAllModalities) {
    AdvancedMultimodalProcessor processor(config);
    
    MultimodalInput input;
    input.input_id = "test_all";
    input.primary_modality = ModalityType::MULTIMODAL;
    input.text = std::make_shared<TextInput>(createTextInput("Complete multimodal input"));
    input.image = std::make_shared<ImageInput>(createImageInput(224, 224));
    input.audio = std::make_shared<AudioInput>(createAudioInput(1000));
    input.video = std::make_shared<VideoInput>(createVideoInput(10));
    
    auto result = processor.processMultimodal(input);
    
    EXPECT_TRUE(result.output.success);
    EXPECT_EQ(result.total_modalities_processed, 4);
    EXPECT_GT(result.output.confidence, 0.0f);
}

// Test 12: Feature fusion with two modalities
TEST_F(MultimodalProcessorTest, FeatureFusionTwoModalities) {
    AdvancedMultimodalProcessor processor(config);
    
    std::vector<ModalityResult> results;
    
    ModalityResult text_result;
    text_result.modality = ModalityType::TEXT;
    text_result.embeddings = std::vector<float>(512, 0.5f);
    text_result.scores["confidence"] = 0.9f;
    results.push_back(text_result);
    
    ModalityResult image_result;
    image_result.modality = ModalityType::IMAGE;
    image_result.embeddings = std::vector<float>(512, 0.3f);
    image_result.scores["confidence"] = 0.8f;
    results.push_back(image_result);
    
    auto fused = processor.fuseFeatures(results);
    
    EXPECT_EQ(fused.size(), 512);
    EXPECT_GT(fused[0], 0.0f);
}

// Test 13: Feature fusion with attention
TEST_F(MultimodalProcessorTest, FeatureFusionWithAttention) {
    AdvancedMultimodalProcessor processor(config);
    
    std::vector<ModalityResult> results;
    std::vector<float> attention_weights = {0.7f, 0.3f};
    
    ModalityResult result1;
    result1.embeddings = std::vector<float>(256, 1.0f);
    results.push_back(result1);
    
    ModalityResult result2;
    result2.embeddings = std::vector<float>(256, 0.0f);
    results.push_back(result2);
    
    auto fused = processor.fuseWithAttention(results, attention_weights);
    
    EXPECT_EQ(fused.size(), 256);
    // Should be closer to result1 due to higher attention weight
}

// Test 14: Batch processing
TEST_F(MultimodalProcessorTest, BatchProcessing) {
    AdvancedMultimodalProcessor processor(config);
    
    std::vector<MultimodalInput> inputs;
    for (int i = 0; i < 5; ++i) {
        MultimodalInput input;
        input.input_id = "batch_" + std::to_string(i);
        input.text = std::make_shared<TextInput>(
            createTextInput("Batch input " + std::to_string(i)));
        inputs.push_back(input);
    }
    
    auto results = processor.processBatch(inputs);
    
    EXPECT_EQ(results.size(), 5);
    for (const auto& result : results) {
        EXPECT_TRUE(result.output.success);
    }
}

// Test 15: Caching functionality
TEST_F(MultimodalProcessorTest, CachingFunctionality) {
    AdvancedMultimodalProcessor processor(config);
    
    TextInput input = createTextInput("Cached text");
    
    // First call - cache miss
    auto result1 = processor.processText(input);
    
    // Second call - should hit cache
    auto result2 = processor.processText(input);
    
    EXPECT_TRUE(result1.success);
    EXPECT_TRUE(result2.success);
    
    auto metrics = processor.getPerformanceMetrics();
    EXPECT_GT(metrics.total_cache_hits, 0);
}

// Test 16: Cache clearing
TEST_F(MultimodalProcessorTest, CacheClearing) {
    AdvancedMultimodalProcessor processor(config);
    
    TextInput input = createTextInput("Test");
    processor.processText(input);
    
    EXPECT_GT(processor.getCacheSize(), 0);
    
    processor.clearCache();
    EXPECT_EQ(processor.getCacheSize(), 0);
}

// Test 17: Performance metrics tracking
TEST_F(MultimodalProcessorTest, PerformanceMetricsTracking) {
    AdvancedMultimodalProcessor processor(config);
    
    processor.processText(createTextInput("Text"));
    processor.processImage(createImageInput(224, 224));
    processor.processAudio(createAudioInput(500));
    
    auto metrics = processor.getPerformanceMetrics();
    
    EXPECT_EQ(metrics.text_inputs_processed, 1);
    EXPECT_EQ(metrics.image_inputs_processed, 1);
    EXPECT_EQ(metrics.audio_inputs_processed, 1);
    EXPECT_GT(metrics.avg_text_processing_time_ms, 0.0);
}

// Test 18: Configuration update
TEST_F(MultimodalProcessorTest, ConfigurationUpdate) {
    AdvancedMultimodalProcessor processor(config);
    
    MultimodalConfig new_config = config;
    new_config.max_text_length = 1024;
    
    processor.updateConfig(new_config);
    auto retrieved_config = processor.getConfig();
    
    EXPECT_EQ(retrieved_config.max_text_length, 1024);
}

// Test 19: MultimodalProcessorManager - Create and destroy
TEST_F(MultimodalProcessorTest, ManagerCreateDestroy) {
    auto& manager = MultimodalProcessorManager::getInstance();
    
    ASSERT_TRUE(manager.createProcessor("proc1", config));
    EXPECT_EQ(manager.getActiveProcessorCount(), 1);
    
    ASSERT_TRUE(manager.destroyProcessor("proc1"));
    EXPECT_EQ(manager.getActiveProcessorCount(), 0);
}

// Test 20: MultimodalProcessorManager - Get processor
TEST_F(MultimodalProcessorTest, ManagerGetProcessor) {
    auto& manager = MultimodalProcessorManager::getInstance();
    
    manager.createProcessor("proc1", config);
    auto processor = manager.getProcessor("proc1");
    
    ASSERT_NE(processor, nullptr);
    
    TextInput input = createTextInput("Test");
    auto result = processor->processText(input);
    EXPECT_TRUE(result.success);
    
    manager.destroyProcessor("proc1");
}

// Test 21: MultimodalProcessorManager - Batch across processors
TEST_F(MultimodalProcessorTest, ManagerBatchAcrossProcessors) {
    auto& manager = MultimodalProcessorManager::getInstance();
    
    manager.createProcessor("proc1", config);
    manager.createProcessor("proc2", config);
    
    std::vector<MultimodalInput> inputs;
    for (int i = 0; i < 10; ++i) {
        MultimodalInput input;
        input.input_id = "cross_" + std::to_string(i);
        input.text = std::make_shared<TextInput>(createTextInput("Input " + std::to_string(i)));
        inputs.push_back(input);
    }
    
    auto results = manager.processBatchAcrossProcessors(inputs);
    EXPECT_EQ(results.size(), 10);
    
    manager.destroyProcessor("proc1");
    manager.destroyProcessor("proc2");
}

// Test 22: GlobalMultimodalSystem - Initialize and shutdown
TEST_F(MultimodalProcessorTest, GlobalSystemInitializeShutdown) {
    auto& global = GlobalMultimodalSystem::getInstance();
    
    ASSERT_TRUE(global.initialize(config));
    EXPECT_TRUE(global.isInitialized());
    
    ASSERT_TRUE(global.shutdown());
    EXPECT_FALSE(global.isInitialized());
}

// Test 23: GlobalMultimodalSystem - Model registration
TEST_F(MultimodalProcessorTest, GlobalSystemModelRegistration) {
    auto& global = GlobalMultimodalSystem::getInstance();
    global.initialize(config);
    
    ASSERT_TRUE(global.registerModel("bert_model", ModalityType::TEXT, "/path/to/bert"));
    ASSERT_TRUE(global.registerModel("resnet_model", ModalityType::IMAGE, "/path/to/resnet"));
    
    auto text_models = global.getRegisteredModels(ModalityType::TEXT);
    EXPECT_EQ(text_models.size(), 1);
    EXPECT_EQ(text_models[0], "bert_model");
    
    global.unregisterModel("bert_model");
    global.unregisterModel("resnet_model");
    global.shutdown();
}

// Test 24: GlobalMultimodalSystem - Cross-modal similarity
TEST_F(MultimodalProcessorTest, GlobalSystemCrossModalSimilarity) {
    auto& global = GlobalMultimodalSystem::getInstance();
    global.initialize(config);
    
    ModalityResult result1, result2;
    result1.embeddings = std::vector<float>(256, 0.5f);
    result2.embeddings = std::vector<float>(256, 0.5f);
    
    float similarity = global.calculateCrossModalSimilarity(result1, result2);
    EXPECT_GT(similarity, 0.9f);  // Should be very similar
    
    global.shutdown();
}

// Test 25: GlobalMultimodalSystem - Modality alignment
TEST_F(MultimodalProcessorTest, GlobalSystemModalityAlignment) {
    auto& global = GlobalMultimodalSystem::getInstance();
    global.initialize(config);
    
    std::vector<ModalityResult> results;
    
    ModalityResult result1;
    result1.embeddings = std::vector<float>(128, 1.0f);
    result1.scores["confidence"] = 0.9f;
    results.push_back(result1);
    
    ModalityResult result2;
    result2.embeddings = std::vector<float>(128, 0.5f);
    result2.scores["confidence"] = 0.8f;
    results.push_back(result2);
    
    auto aligned = global.alignModalities(results);
    EXPECT_EQ(aligned.size(), 128);
    
    global.shutdown();
}

// Test 26: GlobalMultimodalSystem - System metrics
TEST_F(MultimodalProcessorTest, GlobalSystemMetrics) {
    auto& global = GlobalMultimodalSystem::getInstance();
    global.initialize(config);
    
    auto& manager = MultimodalProcessorManager::getInstance();
    manager.createProcessor("metrics_proc", config);
    
    auto metrics = global.getSystemMetrics();
    EXPECT_GT(metrics.total_processors, 0);
    
    manager.destroyProcessor("metrics_proc");
    global.shutdown();
}

// Test 27: Concurrent text processing
TEST_F(MultimodalProcessorTest, ConcurrentTextProcessing) {
    AdvancedMultimodalProcessor processor(config);
    
    std::vector<std::thread> threads;
    std::atomic<int> successful_processes{0};
    
    for (int t = 0; t < 5; ++t) {
        threads.emplace_back([&processor, &successful_processes, t]() {
            for (int i = 0; i < 10; ++i) {
                TextInput input;
                input.text = "Thread " + std::to_string(t) + " Input " + std::to_string(i);
                auto result = processor.processText(input);
                if (result.success) {
                    ++successful_processes;
                }
            }
        });
    }
    
    for (auto& thread : threads) {
        thread.join();
    }
    
    EXPECT_EQ(successful_processes.load(), 50);
}

// Test 28: Concurrent multimodal processing
TEST_F(MultimodalProcessorTest, ConcurrentMultimodalProcessing) {
    AdvancedMultimodalProcessor processor(config);
    
    std::vector<std::thread> threads;
    std::atomic<int> successful_processes{0};
    
    for (int t = 0; t < 3; ++t) {
        threads.emplace_back([this, &processor, &successful_processes, t]() {
            for (int i = 0; i < 5; ++i) {
                MultimodalInput input;
                input.input_id = "thread" + std::to_string(t) + "_" + std::to_string(i);
                input.text = std::make_shared<TextInput>(createTextInput("Concurrent test"));
                input.image = std::make_shared<ImageInput>(createImageInput(224, 224));
                
                auto result = processor.processMultimodal(input);
                if (result.output.success) {
                    ++successful_processes;
                }
            }
        });
    }
    
    for (auto& thread : threads) {
        thread.join();
    }
    
    EXPECT_EQ(successful_processes.load(), 15);
}

// Test 29: Different image formats
TEST_F(MultimodalProcessorTest, DifferentImageFormats) {
    AdvancedMultimodalProcessor processor(config);
    
    ImageInput rgb_input = createImageInput(224, 224);
    rgb_input.format = ImageFormat::RGB;
    
    ImageInput bgr_input = createImageInput(224, 224);
    bgr_input.format = ImageFormat::BGR;
    
    auto rgb_result = processor.processImage(rgb_input);
    auto bgr_result = processor.processImage(bgr_input);
    
    EXPECT_TRUE(rgb_result.success);
    EXPECT_TRUE(bgr_result.success);
}

// Test 30: Patent Claim - Multimodal Feature Fusion
TEST_F(MultimodalProcessorTest, PatentClaimMultimodalFeatureFusion) {
    AdvancedMultimodalProcessor processor(config);
    
    // Setup: Create multimodal input with text, image, and audio
    MultimodalInput input;
    input.input_id = "patent_test";
    input.primary_modality = ModalityType::MULTIMODAL;
    input.text = std::make_shared<TextInput>(createTextInput("A dog barking loudly"));
    input.image = std::make_shared<ImageInput>(createImageInput(224, 224));
    input.audio = std::make_shared<AudioInput>(createAudioInput(2000));
    
    // Execute: Process multimodal input with fusion
    auto start_time = std::chrono::high_resolution_clock::now();
    auto result = processor.processMultimodal(input);
    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
    
    // Verify: Multimodal fusion successful with quality metrics
    ASSERT_TRUE(result.output.success);
    EXPECT_EQ(result.total_modalities_processed, 3);
    EXPECT_FALSE(result.output.fused_embeddings.empty());
    EXPECT_GT(result.output.confidence, 0.7f);
    EXPECT_LT(duration.count(), 500);  // < 500ms processing time
    
    // Patent claim: System performs multimodal feature fusion across
    // text, image, and audio with confidence-weighted combination
    EXPECT_EQ(result.output.modality_results.size(), 3);
    
    // Verify individual modality processing times
    EXPECT_GT(result.text_processing_time.count(), 0);
    EXPECT_GT(result.image_processing_time.count(), 0);
    EXPECT_GT(result.audio_processing_time.count(), 0);
    
    // Verify fusion occurred
    if (config.enable_fusion) {
        EXPECT_GT(result.fusion_time.count(), 0);
    }
}

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}

