#ifndef MODEL_LOADER_H
#define MODEL_LOADER_H

#include <string>
#include <memory>
#include <vector>
#include <cuda_runtime.h>

namespace cogniware {

class ModelLoader {
public:
    virtual ~ModelLoader() = default;

    // Load model weights from file
    virtual bool loadFromFile(const std::string& path) = 0;

    // Get model parameters
    virtual size_t getParameterCount() const = 0;
    virtual size_t getContextLength() const = 0;
    virtual size_t getHiddenSize() const = 0;
    virtual size_t getNumLayers() const = 0;
    virtual size_t getNumHeads() const = 0;

    // Get weight tensors
    virtual float* getWeights() = 0;
    virtual const float* getWeights() const = 0;

    // Get specific layer weights
    virtual float* getLayerWeights(size_t layer_idx) = 0;
    virtual const float* getLayerWeights(size_t layer_idx) const = 0;

    // Get embedding weights
    virtual float* getEmbeddingWeights() = 0;
    virtual const float* getEmbeddingWeights() const = 0;

    // Get output layer weights
    virtual float* getOutputWeights() = 0;
    virtual const float* getOutputWeights() const = 0;
};

// Factory function to create appropriate model loader
std::unique_ptr<ModelLoader> createModelLoader(const std::string& format);

} // namespace cogniware

#endif // MODEL_LOADER_H 