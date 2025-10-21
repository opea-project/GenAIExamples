#ifndef GGUF_LOADER_H
#define GGUF_LOADER_H

#include "../../include/model_loader.h"
#include <string>
#include <vector>
#include <unordered_map>
#include <cuda_runtime.h>

namespace cogniware {

class GGUFLoader : public ModelLoader {
public:
    GGUFLoader();
    ~GGUFLoader() override;

    bool loadFromFile(const std::string& path) override;

    size_t getParameterCount() const override;
    size_t getContextLength() const override;
    size_t getHiddenSize() const override;
    size_t getNumLayers() const override;
    size_t getNumHeads() const override;

    float* getWeights() override;
    const float* getWeights() const override;
    float* getLayerWeights(size_t layer_idx) override;
    const float* getLayerWeights(size_t layer_idx) const override;
    float* getEmbeddingWeights() override;
    const float* getEmbeddingWeights() const override;
    float* getOutputWeights() override;
    const float* getOutputWeights() const override;

private:
    // GGUF file parsing
    bool parseHeader();
    bool parseTensors();
    bool loadTensorData();

    // Memory management
    void allocateGPUMemory();
    void freeGPUMemory();

    // Internal state
    std::string file_path_;
    FILE* file_handle_;
    std::vector<float> weights_;
    float* gpu_weights_;
    size_t num_parameters_;
    size_t context_length_;
    size_t hidden_size_;
    size_t num_layers_;
    size_t num_heads_;
    
    // Tensor offsets
    size_t embedding_offset_;
    size_t output_offset_;
    std::vector<size_t> layer_offsets_;
};

} // namespace cogniware

#endif // GGUF_LOADER_H 