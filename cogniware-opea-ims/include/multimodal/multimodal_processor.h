#ifndef MULTIMODAL_PROCESSOR_H
#define MULTIMODAL_PROCESSOR_H

#include <string>
#include <vector>
#include <memory>
#include <unordered_map>
#include <functional>
#include <chrono>
#include <cstdint>

namespace cogniware {
namespace multimodal {

// Forward declarations
struct MultimodalInput;
struct MultimodalOutput;
struct ProcessingResult;

// Modality types
enum class ModalityType {
    TEXT,
    IMAGE,
    AUDIO,
    VIDEO,
    MULTIMODAL
};

// Image formats
enum class ImageFormat {
    RGB,
    BGR,
    RGBA,
    BGRA,
    GRAYSCALE
};

// Audio formats
enum class AudioFormat {
    PCM_S16LE,
    PCM_F32LE,
    MP3,
    WAV,
    FLAC
};

// Video formats
enum class VideoFormat {
    H264,
    H265,
    VP9,
    AV1,
    RAW
};

// Multimodal processing configuration
struct MultimodalConfig {
    // Text processing
    size_t max_text_length;
    bool enable_text_preprocessing;
    std::string text_tokenizer;
    
    // Image processing
    size_t image_width;
    size_t image_height;
    ImageFormat image_format;
    bool enable_image_augmentation;
    bool use_gpu_for_images;
    
    // Audio processing
    size_t audio_sample_rate;
    size_t audio_channels;
    AudioFormat audio_format;
    bool enable_audio_preprocessing;
    bool use_gpu_for_audio;
    
    // Video processing
    size_t video_fps;
    size_t video_width;
    size_t video_height;
    VideoFormat video_format;
    size_t max_video_frames;
    bool use_gpu_for_video;
    
    // General settings
    size_t batch_size;
    size_t num_gpu_streams;
    bool enable_fusion;
    bool enable_caching;
    float fusion_temperature;
    
    MultimodalConfig()
        : max_text_length(512)
        , enable_text_preprocessing(true)
        , text_tokenizer("bpe")
        , image_width(224)
        , image_height(224)
        , image_format(ImageFormat::RGB)
        , enable_image_augmentation(false)
        , use_gpu_for_images(true)
        , audio_sample_rate(16000)
        , audio_channels(1)
        , audio_format(AudioFormat::PCM_F32LE)
        , enable_audio_preprocessing(true)
        , use_gpu_for_audio(true)
        , video_fps(30)
        , video_width(224)
        , video_height(224)
        , video_format(VideoFormat::H264)
        , max_video_frames(100)
        , use_gpu_for_video(true)
        , batch_size(32)
        , num_gpu_streams(4)
        , enable_fusion(true)
        , enable_caching(true)
        , fusion_temperature(0.7f) {}
};

// Text input
struct TextInput {
    std::string text;
    std::string language;
    std::unordered_map<std::string, std::string> metadata;
};

// Image input
struct ImageInput {
    std::vector<uint8_t> data;
    size_t width;
    size_t height;
    size_t channels;
    ImageFormat format;
    std::unordered_map<std::string, std::string> metadata;
};

// Audio input
struct AudioInput {
    std::vector<float> samples;
    size_t sample_rate;
    size_t channels;
    AudioFormat format;
    std::chrono::milliseconds duration;
    std::unordered_map<std::string, std::string> metadata;
};

// Video input
struct VideoInput {
    std::vector<std::vector<uint8_t>> frames;
    size_t width;
    size_t height;
    size_t fps;
    VideoFormat format;
    std::chrono::milliseconds duration;
    std::unordered_map<std::string, std::string> metadata;
};

// Multimodal input container
struct MultimodalInput {
    std::string input_id;
    ModalityType primary_modality;
    std::shared_ptr<TextInput> text;
    std::shared_ptr<ImageInput> image;
    std::shared_ptr<AudioInput> audio;
    std::shared_ptr<VideoInput> video;
    std::chrono::system_clock::time_point timestamp;
};

// Processing result for each modality
struct ModalityResult {
    ModalityType modality;
    std::vector<float> embeddings;
    std::vector<float> features;
    std::unordered_map<std::string, float> scores;
    bool success;
    std::string error_message;
};

// Multimodal output
struct MultimodalOutput {
    std::string output_id;
    std::vector<ModalityResult> modality_results;
    std::vector<float> fused_embeddings;
    std::string text_output;
    float confidence;
    std::chrono::milliseconds processing_time;
    bool success;
};

// Processing result with detailed metrics
struct ProcessingResult {
    MultimodalOutput output;
    size_t total_modalities_processed;
    std::chrono::milliseconds text_processing_time;
    std::chrono::milliseconds image_processing_time;
    std::chrono::milliseconds audio_processing_time;
    std::chrono::milliseconds video_processing_time;
    std::chrono::milliseconds fusion_time;
    size_t gpu_memory_used;
    bool cache_hit;
};

// Advanced multimodal processor
class AdvancedMultimodalProcessor {
public:
    explicit AdvancedMultimodalProcessor(const MultimodalConfig& config);
    ~AdvancedMultimodalProcessor();

    // Single modality processing
    ModalityResult processText(const TextInput& input);
    ModalityResult processImage(const ImageInput& input);
    ModalityResult processAudio(const AudioInput& input);
    ModalityResult processVideo(const VideoInput& input);

    // Multimodal processing
    ProcessingResult processMultimodal(const MultimodalInput& input);
    std::vector<ProcessingResult> processBatch(
        const std::vector<MultimodalInput>& inputs);

    // Feature fusion
    std::vector<float> fuseFeatures(
        const std::vector<ModalityResult>& modality_results);
    
    std::vector<float> fuseWithAttention(
        const std::vector<ModalityResult>& modality_results,
        const std::vector<float>& attention_weights);

    // Preprocessing operations
    TextInput preprocessText(const TextInput& input);
    ImageInput preprocessImage(const ImageInput& input);
    AudioInput preprocessAudio(const AudioInput& input);
    VideoInput preprocessVideo(const VideoInput& input);

    // Embedding extraction
    std::vector<float> extractTextEmbeddings(const TextInput& input);
    std::vector<float> extractImageEmbeddings(const ImageInput& input);
    std::vector<float> extractAudioEmbeddings(const AudioInput& input);
    std::vector<float> extractVideoEmbeddings(const VideoInput& input);

    // Configuration management
    void updateConfig(const MultimodalConfig& config);
    MultimodalConfig getConfig() const;

    // Cache management
    void clearCache();
    size_t getCacheSize() const;
    float getCacheHitRate() const;

    // Performance metrics
    struct PerformanceMetrics {
        size_t total_inputs_processed;
        size_t text_inputs_processed;
        size_t image_inputs_processed;
        size_t audio_inputs_processed;
        size_t video_inputs_processed;
        size_t multimodal_inputs_processed;
        double avg_text_processing_time_ms;
        double avg_image_processing_time_ms;
        double avg_audio_processing_time_ms;
        double avg_video_processing_time_ms;
        double avg_multimodal_processing_time_ms;
        size_t total_cache_hits;
        size_t total_cache_misses;
        double cache_hit_rate;
        size_t peak_gpu_memory_usage;
    };

    PerformanceMetrics getPerformanceMetrics() const;
    void resetMetrics();

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

// Multimodal processor manager
class MultimodalProcessorManager {
public:
    static MultimodalProcessorManager& getInstance();

    // Processor management
    bool createProcessor(
        const std::string& processor_id,
        const MultimodalConfig& config);
    
    bool destroyProcessor(const std::string& processor_id);
    
    std::shared_ptr<AdvancedMultimodalProcessor> getProcessor(
        const std::string& processor_id);

    // Batch processing across processors
    std::vector<ProcessingResult> processBatchAcrossProcessors(
        const std::vector<MultimodalInput>& inputs);

    // Statistics
    size_t getActiveProcessorCount() const;
    std::vector<std::string> getActiveProcessorIds() const;

private:
    MultimodalProcessorManager();
    ~MultimodalProcessorManager();
    MultimodalProcessorManager(const MultimodalProcessorManager&) = delete;
    MultimodalProcessorManager& operator=(const MultimodalProcessorManager&) = delete;

    class ManagerImpl;
    std::unique_ptr<ManagerImpl> pImpl;
};

// Global multimodal processing system
class GlobalMultimodalSystem {
public:
    static GlobalMultimodalSystem& getInstance();

    // System initialization
    bool initialize(const MultimodalConfig& default_config);
    bool shutdown();
    bool isInitialized() const;

    // Model registry
    bool registerModel(
        const std::string& model_id,
        ModalityType modality,
        const std::string& model_path);
    
    bool unregisterModel(const std::string& model_id);
    std::vector<std::string> getRegisteredModels(ModalityType modality) const;

    // Cross-modal alignment
    float calculateCrossModalSimilarity(
        const ModalityResult& result1,
        const ModalityResult& result2);
    
    std::vector<float> alignModalities(
        const std::vector<ModalityResult>& results);

    // System-wide metrics
    struct SystemMetrics {
        size_t total_processors;
        size_t total_models_registered;
        size_t total_inputs_processed;
        size_t total_gpu_memory_allocated;
        double avg_throughput_inputs_per_sec;
        double avg_latency_ms;
    };

    SystemMetrics getSystemMetrics() const;

private:
    GlobalMultimodalSystem();
    ~GlobalMultimodalSystem();
    GlobalMultimodalSystem(const GlobalMultimodalSystem&) = delete;
    GlobalMultimodalSystem& operator=(const GlobalMultimodalSystem&) = delete;

    class GlobalImpl;
    std::unique_ptr<GlobalImpl> pImpl;
};

} // namespace multimodal
} // namespace cogniware

#endif // MULTIMODAL_PROCESSOR_H

