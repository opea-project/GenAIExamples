#include "sampling_strategies.h"
#include "../cuda_runtime/cuda_utils.h"
#include <spdlog/spdlog.h>
#include <random>
#include <algorithm>
#include <numeric>

namespace cogniware {
namespace llm_inference {

// Helper functions for sampling
namespace {
    template<typename T>
    void softmax(T* output, const T* input, size_t size, cudaStream_t stream) {
        // Find maximum value for numerical stability
        T max_val;
        CUDA_CHECK(cudaMemcpy(&max_val, input, sizeof(T), cudaMemcpyDeviceToHost));
        for (size_t i = 1; i < size; ++i) {
            T val;
            CUDA_CHECK(cudaMemcpy(&val, input + i, sizeof(T), cudaMemcpyDeviceToHost));
            max_val = std::max(max_val, val);
        }

        // Compute exp(x - max_val) and sum
        T sum = 0;
        for (size_t i = 0; i < size; ++i) {
            T val;
            CUDA_CHECK(cudaMemcpy(&val, input + i, sizeof(T), cudaMemcpyDeviceToHost));
            T exp_val = std::exp(val - max_val);
            CUDA_CHECK(cudaMemcpy(output + i, &exp_val, sizeof(T), cudaMemcpyHostToDevice));
            sum += exp_val;
        }

        // Normalize
        for (size_t i = 0; i < size; ++i) {
            T val;
            CUDA_CHECK(cudaMemcpy(&val, output + i, sizeof(T), cudaMemcpyDeviceToHost));
            val /= sum;
            CUDA_CHECK(cudaMemcpy(output + i, &val, sizeof(T), cudaMemcpyHostToDevice));
        }
    }

    template<typename T>
    void applyTemperature(T* output, const T* input, size_t size, float temperature, cudaStream_t stream) {
        for (size_t i = 0; i < size; ++i) {
            T val;
            CUDA_CHECK(cudaMemcpy(&val, input + i, sizeof(T), cudaMemcpyDeviceToHost));
            val /= temperature;
            CUDA_CHECK(cudaMemcpy(output + i, &val, sizeof(T), cudaMemcpyHostToDevice));
        }
    }

    template<typename T>
    void applyTopK(T* output, const T* input, size_t size, int k, cudaStream_t stream) {
        // Copy to host for sorting
        std::vector<T> values(size);
        CUDA_CHECK(cudaMemcpy(values.data(), input, size * sizeof(T), cudaMemcpyDeviceToHost));

        // Find k-th largest value
        std::nth_element(values.begin(), values.begin() + k, values.end(), std::greater<T>());
        T threshold = values[k - 1];

        // Apply threshold
        for (size_t i = 0; i < size; ++i) {
            T val;
            CUDA_CHECK(cudaMemcpy(&val, input + i, sizeof(T), cudaMemcpyDeviceToHost));
            if (val < threshold) {
                val = -std::numeric_limits<T>::infinity();
            }
            CUDA_CHECK(cudaMemcpy(output + i, &val, sizeof(T), cudaMemcpyHostToDevice));
        }
    }

    template<typename T>
    void applyTopP(T* output, const T* input, size_t size, float p, cudaStream_t stream) {
        // Copy to host for sorting
        std::vector<T> values(size);
        CUDA_CHECK(cudaMemcpy(values.data(), input, size * sizeof(T), cudaMemcpyDeviceToHost));

        // Sort values
        std::sort(values.begin(), values.end(), std::greater<T>());

        // Compute cumulative sum
        std::vector<T> cumsum(size);
        std::partial_sum(values.begin(), values.end(), cumsum.begin());

        // Find threshold
        T threshold = 0;
        for (size_t i = 0; i < size; ++i) {
            if (cumsum[i] >= p) {
                threshold = values[i];
                break;
            }
        }

        // Apply threshold
        for (size_t i = 0; i < size; ++i) {
            T val;
            CUDA_CHECK(cudaMemcpy(&val, input + i, sizeof(T), cudaMemcpyDeviceToHost));
            if (val < threshold) {
                val = -std::numeric_limits<T>::infinity();
            }
            CUDA_CHECK(cudaMemcpy(output + i, &val, sizeof(T), cudaMemcpyHostToDevice));
        }
    }
}

// Greedy sampling implementation
template<typename T>
SamplingResult GreedySampling<T>::sample(
    const T* logits,
    size_t vocab_size,
    const SamplingConfig& config,
    cudaStream_t stream
) {
    SamplingResult result;
    result.token_ids.resize(1);
    result.logits.resize(vocab_size);
    result.score = 0.0f;
    result.is_finished = false;

    // Copy logits to host
    std::vector<T> host_logits(vocab_size);
    CUDA_CHECK(cudaMemcpy(host_logits.data(), logits, vocab_size * sizeof(T), cudaMemcpyDeviceToHost));

    // Find maximum value
    auto max_it = std::max_element(host_logits.begin(), host_logits.end());
    size_t max_idx = std::distance(host_logits.begin(), max_it);
    result.token_ids[0] = static_cast<int>(max_idx);
    result.score = static_cast<float>(*max_it);

    return result;
}

// Temperature sampling implementation
template<typename T>
SamplingResult TemperatureSampling<T>::sample(
    const T* logits,
    size_t vocab_size,
    const SamplingConfig& config,
    cudaStream_t stream
) {
    SamplingResult result;
    result.token_ids.resize(1);
    result.logits.resize(vocab_size);
    result.score = 0.0f;
    result.is_finished = false;

    // Apply temperature
    std::vector<T> temp_logits(vocab_size);
    applyTemperature(temp_logits.data(), logits, vocab_size, config.temperature, stream);

    // Apply softmax
    softmax(temp_logits.data(), temp_logits.data(), vocab_size, stream);

    // Sample from distribution
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<float> dis(0.0f, 1.0f);
    float r = dis(gen);

    // Copy to host for sampling
    std::vector<T> host_logits(vocab_size);
    CUDA_CHECK(cudaMemcpy(host_logits.data(), temp_logits.data(), vocab_size * sizeof(T), cudaMemcpyDeviceToHost));

    // Find sampled token
    float cumsum = 0.0f;
    for (size_t i = 0; i < vocab_size; ++i) {
        cumsum += static_cast<float>(host_logits[i]);
        if (r <= cumsum) {
            result.token_ids[0] = static_cast<int>(i);
            result.score = static_cast<float>(host_logits[i]);
            break;
        }
    }

    return result;
}

// Top-K sampling implementation
template<typename T>
SamplingResult TopKSampling<T>::sample(
    const T* logits,
    size_t vocab_size,
    const SamplingConfig& config,
    cudaStream_t stream
) {
    SamplingResult result;
    result.token_ids.resize(1);
    result.logits.resize(vocab_size);
    result.score = 0.0f;
    result.is_finished = false;

    // Apply top-k
    std::vector<T> topk_logits(vocab_size);
    applyTopK(topk_logits.data(), logits, vocab_size, config.top_k, stream);

    // Apply softmax
    softmax(topk_logits.data(), topk_logits.data(), vocab_size, stream);

    // Sample from distribution
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<float> dis(0.0f, 1.0f);
    float r = dis(gen);

    // Copy to host for sampling
    std::vector<T> host_logits(vocab_size);
    CUDA_CHECK(cudaMemcpy(host_logits.data(), topk_logits.data(), vocab_size * sizeof(T), cudaMemcpyDeviceToHost));

    // Find sampled token
    float cumsum = 0.0f;
    for (size_t i = 0; i < vocab_size; ++i) {
        cumsum += static_cast<float>(host_logits[i]);
        if (r <= cumsum) {
            result.token_ids[0] = static_cast<int>(i);
            result.score = static_cast<float>(host_logits[i]);
            break;
        }
    }

    return result;
}

// Top-P (nucleus) sampling implementation
template<typename T>
SamplingResult TopPSampling<T>::sample(
    const T* logits,
    size_t vocab_size,
    const SamplingConfig& config,
    cudaStream_t stream
) {
    SamplingResult result;
    result.token_ids.resize(1);
    result.logits.resize(vocab_size);
    result.score = 0.0f;
    result.is_finished = false;

    // Apply top-p
    std::vector<T> topp_logits(vocab_size);
    applyTopP(topp_logits.data(), logits, vocab_size, config.top_p, stream);

    // Apply softmax
    softmax(topp_logits.data(), topp_logits.data(), vocab_size, stream);

    // Sample from distribution
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<float> dis(0.0f, 1.0f);
    float r = dis(gen);

    // Copy to host for sampling
    std::vector<T> host_logits(vocab_size);
    CUDA_CHECK(cudaMemcpy(host_logits.data(), topp_logits.data(), vocab_size * sizeof(T), cudaMemcpyDeviceToHost));

    // Find sampled token
    float cumsum = 0.0f;
    for (size_t i = 0; i < vocab_size; ++i) {
        cumsum += static_cast<float>(host_logits[i]);
        if (r <= cumsum) {
            result.token_ids[0] = static_cast<int>(i);
            result.score = static_cast<float>(host_logits[i]);
            break;
        }
    }

    return result;
}

// Beam search sampling implementation
template<typename T>
SamplingResult BeamSearchSampling<T>::sample(
    const T* logits,
    size_t vocab_size,
    const SamplingConfig& config,
    cudaStream_t stream
) {
    SamplingResult result;
    result.token_ids.resize(1);
    result.logits.resize(vocab_size);
    result.score = 0.0f;
    result.is_finished = false;

    // Copy logits to host
    std::vector<T> host_logits(vocab_size);
    CUDA_CHECK(cudaMemcpy(host_logits.data(), logits, vocab_size * sizeof(T), cudaMemcpyDeviceToHost));

    // Find top-k tokens
    std::vector<std::pair<T, int>> token_scores;
    for (size_t i = 0; i < vocab_size; ++i) {
        token_scores.emplace_back(host_logits[i], static_cast<int>(i));
    }
    std::partial_sort(
        token_scores.begin(),
        token_scores.begin() + config.top_k,
        token_scores.end(),
        std::greater<std::pair<T, int>>()
    );

    // Select best token
    result.token_ids[0] = token_scores[0].second;
    result.score = static_cast<float>(token_scores[0].first);

    return result;
}

// Factory implementation
std::unique_ptr<SamplingStrategy> SamplingStrategyFactory::createStrategy(
    SamplingStrategyType type,
    const SamplingConfig& config
) {
    switch (type) {
        case SamplingStrategyType::GREEDY:
            return std::make_unique<GreedySampling<float>>();
        case SamplingStrategyType::TEMPERATURE:
            return std::make_unique<TemperatureSampling<float>>();
        case SamplingStrategyType::TOP_K:
            return std::make_unique<TopKSampling<float>>();
        case SamplingStrategyType::TOP_P:
            return std::make_unique<TopPSampling<float>>();
        case SamplingStrategyType::BEAM_SEARCH:
            return std::make_unique<BeamSearchSampling<float>>();
        default:
            throw std::invalid_argument("Unknown sampling strategy type");
    }
}

// Explicit template instantiations
template class GreedySampling<float>;
template class GreedySampling<half>;
template class TemperatureSampling<float>;
template class TemperatureSampling<half>;
template class TopKSampling<float>;
template class TopKSampling<half>;
template class TopPSampling<float>;
template class TopPSampling<half>;
template class BeamSearchSampling<float>;
template class BeamSearchSampling<half>;

} // namespace llm_inference
} // namespace cogniware
