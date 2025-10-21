#include "transformer_block.h"
#include "../cuda_runtime/cuda_utils.h"
#include "../cuda_runtime/attention_kernels.h"
#include <spdlog/spdlog.h>

namespace cogniware {
namespace llm_inference {

// Internal implementation
struct TransformerBlock::Impl {
    TransformerBlockConfig config;
    AttentionConfig attention_config;
    FeedForwardConfig ff_config;

    // Weight matrices
    float* query_weight;
    float* key_weight;
    float* value_weight;
    float* output_weight;
    float* ff1_weight;
    float* ff2_weight;
    float* layer_norm1_weight;
    float* layer_norm1_bias;
    float* layer_norm2_weight;
    float* layer_norm2_bias;

    // Half precision weights
    half* query_weight_half;
    half* key_weight_half;
    half* value_weight_half;
    half* output_weight_half;
    half* ff1_weight_half;
    half* ff2_weight_half;
    half* layer_norm1_weight_half;
    half* layer_norm1_bias_half;
    half* layer_norm2_weight_half;
    half* layer_norm2_bias_half;

    // Temporary buffers
    float* temp_buffer;
    half* temp_buffer_half;
    size_t temp_buffer_size;

    Impl(const TransformerBlockConfig& cfg) : config(cfg) {
        // Initialize attention config
        attention_config.num_heads = cfg.num_attention_heads;
        attention_config.head_dim = cfg.hidden_size / cfg.num_attention_heads;
        attention_config.hidden_size = cfg.hidden_size;
        attention_config.attention_dropout = cfg.dropout_rate;
        attention_config.use_bias = cfg.use_bias;
        attention_config.use_rotary_embeddings = true;
        attention_config.use_alibi = false;
        attention_config.rotary_embedding_base = 10000.0f;
        attention_config.rotary_embedding_dim = 32;

        // Initialize feed-forward config
        ff_config.hidden_size = cfg.hidden_size;
        ff_config.intermediate_size = cfg.intermediate_size;
        ff_config.dropout_rate = cfg.dropout_rate;
        ff_config.use_bias = cfg.use_bias;
        ff_config.activation_type = cfg.activation_type;

        // Initialize weights
        initializeWeights();
    }

    ~Impl() {
        cleanup();
    }

    void initializeWeights() {
        const size_t hidden_size = config.hidden_size;
        const size_t intermediate_size = config.intermediate_size;

        // Allocate weights
        CUDA_CHECK(cudaMalloc(&query_weight, hidden_size * hidden_size * sizeof(float)));
        CUDA_CHECK(cudaMalloc(&key_weight, hidden_size * hidden_size * sizeof(float)));
        CUDA_CHECK(cudaMalloc(&value_weight, hidden_size * hidden_size * sizeof(float)));
        CUDA_CHECK(cudaMalloc(&output_weight, hidden_size * hidden_size * sizeof(float)));
        CUDA_CHECK(cudaMalloc(&ff1_weight, hidden_size * intermediate_size * sizeof(float)));
        CUDA_CHECK(cudaMalloc(&ff2_weight, intermediate_size * hidden_size * sizeof(float)));

        if (config.use_layer_norm) {
            CUDA_CHECK(cudaMalloc(&layer_norm1_weight, hidden_size * sizeof(float)));
            CUDA_CHECK(cudaMalloc(&layer_norm1_bias, hidden_size * sizeof(float)));
            CUDA_CHECK(cudaMalloc(&layer_norm2_weight, hidden_size * sizeof(float)));
            CUDA_CHECK(cudaMalloc(&layer_norm2_bias, hidden_size * sizeof(float)));
        }

        if (config.use_fp16) {
            CUDA_CHECK(cudaMalloc(&query_weight_half, hidden_size * hidden_size * sizeof(half)));
            CUDA_CHECK(cudaMalloc(&key_weight_half, hidden_size * hidden_size * sizeof(half)));
            CUDA_CHECK(cudaMalloc(&value_weight_half, hidden_size * hidden_size * sizeof(half)));
            CUDA_CHECK(cudaMalloc(&output_weight_half, hidden_size * hidden_size * sizeof(half)));
            CUDA_CHECK(cudaMalloc(&ff1_weight_half, hidden_size * intermediate_size * sizeof(half)));
            CUDA_CHECK(cudaMalloc(&ff2_weight_half, intermediate_size * hidden_size * sizeof(half)));

            if (config.use_layer_norm) {
                CUDA_CHECK(cudaMalloc(&layer_norm1_weight_half, hidden_size * sizeof(half)));
                CUDA_CHECK(cudaMalloc(&layer_norm1_bias_half, hidden_size * sizeof(half)));
                CUDA_CHECK(cudaMalloc(&layer_norm2_weight_half, hidden_size * sizeof(half)));
                CUDA_CHECK(cudaMalloc(&layer_norm2_bias_half, hidden_size * sizeof(half)));
            }
        }

        // Initialize weights with Xavier/Glorot initialization
        initializeWeightsXavier();
    }

    void initializeWeightsXavier() {
        const size_t hidden_size = config.hidden_size;
        const size_t intermediate_size = config.intermediate_size;

        // Initialize attention weights
        initializeMatrixXavier(query_weight, hidden_size, hidden_size);
        initializeMatrixXavier(key_weight, hidden_size, hidden_size);
        initializeMatrixXavier(value_weight, hidden_size, hidden_size);
        initializeMatrixXavier(output_weight, hidden_size, hidden_size);

        // Initialize feed-forward weights
        initializeMatrixXavier(ff1_weight, hidden_size, intermediate_size);
        initializeMatrixXavier(ff2_weight, intermediate_size, hidden_size);

        // Initialize layer norm weights
        if (config.use_layer_norm) {
            initializeVectorOnes(layer_norm1_weight, hidden_size);
            initializeVectorZeros(layer_norm1_bias, hidden_size);
            initializeVectorOnes(layer_norm2_weight, hidden_size);
            initializeVectorZeros(layer_norm2_bias, hidden_size);
        }

        // Convert to FP16 if needed
        if (config.use_fp16) {
            convertToFP16();
        }
    }

    void convertToFP16() {
        const size_t hidden_size = config.hidden_size;
        const size_t intermediate_size = config.intermediate_size;

        // Convert attention weights
        convertToHalf(query_weight_half, query_weight, hidden_size * hidden_size);
        convertToHalf(key_weight_half, key_weight, hidden_size * hidden_size);
        convertToHalf(value_weight_half, value_weight, hidden_size * hidden_size);
        convertToHalf(output_weight_half, output_weight, hidden_size * hidden_size);

        // Convert feed-forward weights
        convertToHalf(ff1_weight_half, ff1_weight, hidden_size * intermediate_size);
        convertToHalf(ff2_weight_half, ff2_weight, intermediate_size * hidden_size);

        // Convert layer norm weights
        if (config.use_layer_norm) {
            convertToHalf(layer_norm1_weight_half, layer_norm1_weight, hidden_size);
            convertToHalf(layer_norm1_bias_half, layer_norm1_bias, hidden_size);
            convertToHalf(layer_norm2_weight_half, layer_norm2_weight, hidden_size);
            convertToHalf(layer_norm2_bias_half, layer_norm2_bias, hidden_size);
        }
    }

    void cleanup() {
        // Free weights
        CUDA_CHECK(cudaFree(query_weight));
        CUDA_CHECK(cudaFree(key_weight));
        CUDA_CHECK(cudaFree(value_weight));
        CUDA_CHECK(cudaFree(output_weight));
        CUDA_CHECK(cudaFree(ff1_weight));
        CUDA_CHECK(cudaFree(ff2_weight));

        if (config.use_layer_norm) {
            CUDA_CHECK(cudaFree(layer_norm1_weight));
            CUDA_CHECK(cudaFree(layer_norm1_bias));
            CUDA_CHECK(cudaFree(layer_norm2_weight));
            CUDA_CHECK(cudaFree(layer_norm2_bias));
        }

        if (config.use_fp16) {
            CUDA_CHECK(cudaFree(query_weight_half));
            CUDA_CHECK(cudaFree(key_weight_half));
            CUDA_CHECK(cudaFree(value_weight_half));
            CUDA_CHECK(cudaFree(output_weight_half));
            CUDA_CHECK(cudaFree(ff1_weight_half));
            CUDA_CHECK(cudaFree(ff2_weight_half));

            if (config.use_layer_norm) {
                CUDA_CHECK(cudaFree(layer_norm1_weight_half));
                CUDA_CHECK(cudaFree(layer_norm1_bias_half));
                CUDA_CHECK(cudaFree(layer_norm2_weight_half));
                CUDA_CHECK(cudaFree(layer_norm2_bias_half));
            }
        }

        // Free temporary buffers
        if (temp_buffer) {
            CUDA_CHECK(cudaFree(temp_buffer));
        }
        if (temp_buffer_half) {
            CUDA_CHECK(cudaFree(temp_buffer_half));
        }
    }

    void allocateBuffers(size_t batch_size, size_t sequence_length) {
        const size_t hidden_size = config.hidden_size;
        const size_t intermediate_size = config.intermediate_size;

        // Calculate buffer sizes
        const size_t max_buffer_size = std::max(
            batch_size * sequence_length * hidden_size,  // Attention output
            batch_size * sequence_length * intermediate_size  // FF intermediate
        );

        // Allocate buffers if needed
        if (temp_buffer_size < max_buffer_size) {
            if (temp_buffer) {
                CUDA_CHECK(cudaFree(temp_buffer));
            }
            if (temp_buffer_half) {
                CUDA_CHECK(cudaFree(temp_buffer_half));
            }

            CUDA_CHECK(cudaMalloc(&temp_buffer, max_buffer_size * sizeof(float)));
            if (config.use_fp16) {
                CUDA_CHECK(cudaMalloc(&temp_buffer_half, max_buffer_size * sizeof(half)));
            }
            temp_buffer_size = max_buffer_size;
        }
    }
};

// Constructor and destructor
TransformerBlock::TransformerBlock(const TransformerBlockConfig& config)
    : pimpl(std::make_unique<Impl>(config)) {}

TransformerBlock::~TransformerBlock() = default;

// Forward pass implementation
void TransformerBlock::forward(
    float* output,
    const float* input,
    const float* attention_mask,
    const KVCacheEntry& kv_cache,
    size_t batch_size,
    size_t sequence_length,
    cudaStream_t stream
) {
    // Allocate temporary buffers
    pimpl->allocateBuffers(batch_size, sequence_length);

    // Compute attention
    computeAttention(
        pimpl->temp_buffer,
        input,
        attention_mask,
        kv_cache,
        batch_size,
        sequence_length,
        stream
    );

    // Apply residual connection and layer norm
    if (pimpl->config.use_residual) {
        addMatrices(
            pimpl->temp_buffer,
            pimpl->temp_buffer,
            input,
            batch_size * sequence_length,
            pimpl->config.hidden_size,
            stream
        );
    }

    if (pimpl->config.use_layer_norm) {
        layerNorm(
            pimpl->temp_buffer,
            pimpl->temp_buffer,
            pimpl->layer_norm1_weight,
            pimpl->layer_norm1_bias,
            batch_size * sequence_length,
            pimpl->config.hidden_size,
            stream
        );
    }

    // Compute feed-forward
    computeFeedForward(
        output,
        pimpl->temp_buffer,
        batch_size,
        sequence_length,
        stream
    );

    // Apply residual connection and layer norm
    if (pimpl->config.use_residual) {
        addMatrices(
            output,
            output,
            pimpl->temp_buffer,
            batch_size * sequence_length,
            pimpl->config.hidden_size,
            stream
        );
    }

    if (pimpl->config.use_layer_norm) {
        layerNorm(
            output,
            output,
            pimpl->layer_norm2_weight,
            pimpl->layer_norm2_bias,
            batch_size * sequence_length,
            pimpl->config.hidden_size,
            stream
        );
    }
}

void TransformerBlock::forward(
    half* output,
    const half* input,
    const half* attention_mask,
    const KVCacheEntry& kv_cache,
    size_t batch_size,
    size_t sequence_length,
    cudaStream_t stream
) {
    // Allocate temporary buffers
    pimpl->allocateBuffers(batch_size, sequence_length);

    // Compute attention
    computeAttention(
        pimpl->temp_buffer_half,
        input,
        attention_mask,
        kv_cache,
        batch_size,
        sequence_length,
        stream
    );

    // Apply residual connection and layer norm
    if (pimpl->config.use_residual) {
        addMatrices(
            pimpl->temp_buffer_half,
            pimpl->temp_buffer_half,
            input,
            batch_size * sequence_length,
            pimpl->config.hidden_size,
            stream
        );
    }

    if (pimpl->config.use_layer_norm) {
        layerNorm(
            pimpl->temp_buffer_half,
            pimpl->temp_buffer_half,
            pimpl->layer_norm1_weight_half,
            pimpl->layer_norm1_bias_half,
            batch_size * sequence_length,
            pimpl->config.hidden_size,
            stream
        );
    }

    // Compute feed-forward
    computeFeedForward(
        output,
        pimpl->temp_buffer_half,
        batch_size,
        sequence_length,
        stream
    );

    // Apply residual connection and layer norm
    if (pimpl->config.use_residual) {
        addMatrices(
            output,
            output,
            pimpl->temp_buffer_half,
            batch_size * sequence_length,
            pimpl->config.hidden_size,
            stream
        );
    }

    if (pimpl->config.use_layer_norm) {
        layerNorm(
            output,
            output,
            pimpl->layer_norm2_weight_half,
            pimpl->layer_norm2_bias_half,
            batch_size * sequence_length,
            pimpl->config.hidden_size,
            stream
        );
    }
}

// Weight management
void TransformerBlock::loadWeights(const std::string& path) {
    // TODO: Implement weight loading from file
    spdlog::warn("Weight loading not implemented yet");
}

void TransformerBlock::saveWeights(const std::string& path) const {
    // TODO: Implement weight saving to file
    spdlog::warn("Weight saving not implemented yet");
}

void TransformerBlock::initializeWeights() {
    pimpl->initializeWeights();
}

// Configuration
const TransformerBlockConfig& TransformerBlock::getConfig() const {
    return pimpl->config;
}

void TransformerBlock::setConfig(const TransformerBlockConfig& config) {
    pimpl->config = config;
    pimpl->cleanup();
    pimpl->initializeWeights();
}

// Memory management
size_t TransformerBlock::getParameterSize() const {
    const size_t hidden_size = pimpl->config.hidden_size;
    const size_t intermediate_size = pimpl->config.intermediate_size;
    const size_t element_size = pimpl->config.use_fp16 ? sizeof(half) : sizeof(float);

    size_t total_size = 0;

    // Attention weights
    total_size += 4 * hidden_size * hidden_size * element_size;  // Q, K, V, O

    // Feed-forward weights
    total_size += (hidden_size * intermediate_size + intermediate_size * hidden_size) * element_size;

    // Layer norm weights
    if (pimpl->config.use_layer_norm) {
        total_size += 4 * hidden_size * element_size;  // 2 weights + 2 biases
    }

    return total_size;
}

size_t TransformerBlock::getActivationSize(size_t batch_size, size_t sequence_length) const {
    const size_t hidden_size = pimpl->config.hidden_size;
    const size_t intermediate_size = pimpl->config.intermediate_size;
    const size_t element_size = pimpl->config.use_fp16 ? sizeof(half) : sizeof(float);

    // Maximum activation size needed
    return std::max(
        batch_size * sequence_length * hidden_size,  // Attention output
        batch_size * sequence_length * intermediate_size  // FF intermediate
    ) * element_size;
}

} // namespace llm_inference
} // namespace cogniware
