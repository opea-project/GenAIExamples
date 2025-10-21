#include <cuda_runtime.h>
#include <device_launch_parameters.h>
#include <cstdint>
#include <cmath>

namespace cogniware {
namespace multimodal {
namespace cuda {

// Image processing kernels

__global__ void resizeImageKernel(
    const uint8_t* input,
    uint8_t* output,
    int input_width,
    int input_height,
    int output_width,
    int output_height,
    int channels) {
    
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    
    if (x >= output_width || y >= output_height) return;
    
    float x_ratio = static_cast<float>(input_width) / output_width;
    float y_ratio = static_cast<float>(input_height) / output_height;
    
    int src_x = static_cast<int>(x * x_ratio);
    int src_y = static_cast<int>(y * y_ratio);
    
    for (int c = 0; c < channels; ++c) {
        int dst_idx = (y * output_width + x) * channels + c;
        int src_idx = (src_y * input_width + src_x) * channels + c;
        output[dst_idx] = input[src_idx];
    }
}

__global__ void normalizeImageKernel(
    const uint8_t* input,
    float* output,
    int width,
    int height,
    int channels,
    float mean,
    float std) {
    
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    int total_pixels = width * height * channels;
    
    if (idx >= total_pixels) return;
    
    output[idx] = (static_cast<float>(input[idx]) / 255.0f - mean) / std;
}

__global__ void rgbToBgrKernel(
    const uint8_t* input,
    uint8_t* output,
    int width,
    int height) {
    
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    
    if (x >= width || y >= height) return;
    
    int idx = (y * width + x) * 3;
    output[idx + 0] = input[idx + 2];  // B
    output[idx + 1] = input[idx + 1];  // G
    output[idx + 2] = input[idx + 0];  // R
}

__global__ void extractImageFeaturesKernel(
    const float* normalized_image,
    float* features,
    int width,
    int height,
    int channels,
    int feature_dim) {
    
    int feature_idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (feature_idx >= feature_dim) return;
    
    // Simple feature extraction (pooling)
    int pixels_per_feature = (width * height * channels) / feature_dim;
    float sum = 0.0f;
    
    for (int i = 0; i < pixels_per_feature; ++i) {
        int pixel_idx = feature_idx * pixels_per_feature + i;
        if (pixel_idx < width * height * channels) {
            sum += normalized_image[pixel_idx];
        }
    }
    
    features[feature_idx] = sum / pixels_per_feature;
}

// Audio processing kernels

__global__ void resampleAudioKernel(
    const float* input,
    float* output,
    int input_length,
    int output_length) {
    
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (idx >= output_length) return;
    
    float ratio = static_cast<float>(input_length) / output_length;
    int src_idx = static_cast<int>(idx * ratio);
    
    if (src_idx < input_length) {
        output[idx] = input[src_idx];
    }
}

__global__ void normalizeAudioKernel(
    const float* input,
    float* output,
    int length) {
    
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (idx >= length) return;
    
    // Simple normalization to [-1, 1] range
    output[idx] = fmaxf(-1.0f, fminf(1.0f, input[idx]));
}

__global__ void extractMelSpectrogramKernel(
    const float* audio,
    float* spectrogram,
    int audio_length,
    int n_mels,
    int hop_length) {
    
    int mel_idx = blockIdx.x * blockDim.x + threadIdx.x;
    int time_idx = blockIdx.y * blockDim.y + threadIdx.y;
    
    int n_frames = (audio_length + hop_length - 1) / hop_length;
    
    if (mel_idx >= n_mels || time_idx >= n_frames) return;
    
    int start_sample = time_idx * hop_length;
    float energy = 0.0f;
    
    for (int i = 0; i < hop_length && (start_sample + i) < audio_length; ++i) {
        float sample = audio[start_sample + i];
        energy += sample * sample;
    }
    
    spectrogram[time_idx * n_mels + mel_idx] = sqrtf(energy / hop_length);
}

__global__ void extractAudioFeaturesKernel(
    const float* spectrogram,
    float* features,
    int n_mels,
    int n_frames,
    int feature_dim) {
    
    int feature_idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (feature_idx >= feature_dim) return;
    
    int elements_per_feature = (n_mels * n_frames) / feature_dim;
    float sum = 0.0f;
    
    for (int i = 0; i < elements_per_feature; ++i) {
        int spec_idx = feature_idx * elements_per_feature + i;
        if (spec_idx < n_mels * n_frames) {
            sum += spectrogram[spec_idx];
        }
    }
    
    features[feature_idx] = sum / elements_per_feature;
}

// Video processing kernels

__global__ void extractVideoFrameFeaturesKernel(
    const uint8_t* frame,
    float* features,
    int width,
    int height,
    int channels,
    int feature_dim) {
    
    int feature_idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (feature_idx >= feature_dim) return;
    
    int pixels_per_feature = (width * height * channels) / feature_dim;
    float sum = 0.0f;
    
    for (int i = 0; i < pixels_per_feature; ++i) {
        int pixel_idx = feature_idx * pixels_per_feature + i;
        if (pixel_idx < width * height * channels) {
            sum += static_cast<float>(frame[pixel_idx]) / 255.0f;
        }
    }
    
    features[feature_idx] = sum / pixels_per_feature;
}

__global__ void aggregateVideoFeaturesKernel(
    const float* frame_features,
    float* video_features,
    int n_frames,
    int feature_dim) {
    
    int feature_idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (feature_idx >= feature_dim) return;
    
    float sum = 0.0f;
    for (int frame = 0; frame < n_frames; ++frame) {
        sum += frame_features[frame * feature_dim + feature_idx];
    }
    
    video_features[feature_idx] = sum / n_frames;
}

// Feature fusion kernels

__global__ void concatenateFeaturesKernel(
    const float* features1,
    const float* features2,
    float* output,
    int dim1,
    int dim2) {
    
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (idx < dim1) {
        output[idx] = features1[idx];
    } else if (idx < dim1 + dim2) {
        output[idx] = features2[idx - dim1];
    }
}

__global__ void weightedFeatureFusionKernel(
    const float* features1,
    const float* features2,
    float* output,
    int feature_dim,
    float weight1,
    float weight2) {
    
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (idx >= feature_dim) return;
    
    output[idx] = features1[idx] * weight1 + features2[idx] * weight2;
}

__global__ void multimodalFusionKernel(
    const float** modality_features,
    const float* weights,
    float* output,
    int n_modalities,
    int feature_dim) {
    
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (idx >= feature_dim) return;
    
    float sum = 0.0f;
    float total_weight = 0.0f;
    
    for (int m = 0; m < n_modalities; ++m) {
        sum += modality_features[m][idx] * weights[m];
        total_weight += weights[m];
    }
    
    output[idx] = total_weight > 0.0f ? sum / total_weight : 0.0f;
}

__global__ void l2NormalizeKernel(
    float* features,
    int feature_dim) {
    
    // First pass: compute norm
    __shared__ float shared_sum[256];
    int tid = threadIdx.x;
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    float local_sum = 0.0f;
    if (idx < feature_dim) {
        local_sum = features[idx] * features[idx];
    }
    
    shared_sum[tid] = local_sum;
    __syncthreads();
    
    // Reduction
    for (int s = blockDim.x / 2; s > 0; s >>= 1) {
        if (tid < s) {
            shared_sum[tid] += shared_sum[tid + s];
        }
        __syncthreads();
    }
    
    __shared__ float norm;
    if (tid == 0) {
        norm = sqrtf(shared_sum[0]);
    }
    __syncthreads();
    
    // Normalize
    if (idx < feature_dim && norm > 1e-6f) {
        features[idx] /= norm;
    }
}

// Attention mechanism kernels

__global__ void computeAttentionScoresKernel(
    const float* query,
    const float* keys,
    float* scores,
    int n_keys,
    int feature_dim) {
    
    int key_idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (key_idx >= n_keys) return;
    
    float dot_product = 0.0f;
    for (int i = 0; i < feature_dim; ++i) {
        dot_product += query[i] * keys[key_idx * feature_dim + i];
    }
    
    scores[key_idx] = dot_product / sqrtf(static_cast<float>(feature_dim));
}

__global__ void softmaxKernel(
    float* scores,
    int n_scores) {
    
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (idx >= n_scores) return;
    
    __shared__ float max_score;
    __shared__ float sum_exp;
    
    if (threadIdx.x == 0) {
        max_score = scores[0];
        for (int i = 1; i < n_scores; ++i) {
            max_score = fmaxf(max_score, scores[i]);
        }
        
        sum_exp = 0.0f;
        for (int i = 0; i < n_scores; ++i) {
            sum_exp += expf(scores[i] - max_score);
        }
    }
    __syncthreads();
    
    if (idx < n_scores) {
        scores[idx] = expf(scores[idx] - max_score) / sum_exp;
    }
}

__global__ void applyAttentionKernel(
    const float* values,
    const float* attention_weights,
    float* output,
    int n_values,
    int feature_dim) {
    
    int feature_idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (feature_idx >= feature_dim) return;
    
    float sum = 0.0f;
    for (int v = 0; v < n_values; ++v) {
        sum += values[v * feature_dim + feature_idx] * attention_weights[v];
    }
    
    output[feature_idx] = sum;
}

// Cross-modal similarity kernels

__global__ void cosineSimilarityKernel(
    const float* embeddings1,
    const float* embeddings2,
    float* similarity,
    int n_embeddings1,
    int n_embeddings2,
    int embedding_dim) {
    
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    int j = blockIdx.y * blockDim.y + threadIdx.y;
    
    if (i >= n_embeddings1 || j >= n_embeddings2) return;
    
    float dot_product = 0.0f;
    float norm1 = 0.0f;
    float norm2 = 0.0f;
    
    for (int d = 0; d < embedding_dim; ++d) {
        float v1 = embeddings1[i * embedding_dim + d];
        float v2 = embeddings2[j * embedding_dim + d];
        dot_product += v1 * v2;
        norm1 += v1 * v1;
        norm2 += v2 * v2;
    }
    
    float norm_product = sqrtf(norm1) * sqrtf(norm2);
    similarity[i * n_embeddings2 + j] = norm_product > 1e-6f ? 
        dot_product / norm_product : 0.0f;
}

// Batch processing kernel

__global__ void batchProcessFeaturesKernel(
    const float* input_batch,
    float* output_batch,
    int batch_size,
    int input_dim,
    int output_dim) {
    
    int batch_idx = blockIdx.z;
    int output_idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (batch_idx >= batch_size || output_idx >= output_dim) return;
    
    int elements_per_output = input_dim / output_dim;
    float sum = 0.0f;
    
    for (int i = 0; i < elements_per_output; ++i) {
        int input_idx = batch_idx * input_dim + output_idx * elements_per_output + i;
        sum += input_batch[input_idx];
    }
    
    output_batch[batch_idx * output_dim + output_idx] = sum / elements_per_output;
}

// Utility function wrappers for host code

extern "C" {

void launchResizeImageKernel(
    const uint8_t* d_input,
    uint8_t* d_output,
    int input_width,
    int input_height,
    int output_width,
    int output_height,
    int channels,
    cudaStream_t stream) {
    
    dim3 block(16, 16);
    dim3 grid((output_width + block.x - 1) / block.x,
              (output_height + block.y - 1) / block.y);
    
    resizeImageKernel<<<grid, block, 0, stream>>>(
        d_input, d_output,
        input_width, input_height,
        output_width, output_height,
        channels);
}

void launchNormalizeImageKernel(
    const uint8_t* d_input,
    float* d_output,
    int width,
    int height,
    int channels,
    float mean,
    float std,
    cudaStream_t stream) {
    
    int total_pixels = width * height * channels;
    int block_size = 256;
    int grid_size = (total_pixels + block_size - 1) / block_size;
    
    normalizeImageKernel<<<grid_size, block_size, 0, stream>>>(
        d_input, d_output, width, height, channels, mean, std);
}

void launchMultimodalFusionKernel(
    const float** d_modality_features,
    const float* d_weights,
    float* d_output,
    int n_modalities,
    int feature_dim,
    cudaStream_t stream) {
    
    int block_size = 256;
    int grid_size = (feature_dim + block_size - 1) / block_size;
    
    multimodalFusionKernel<<<grid_size, block_size, 0, stream>>>(
        d_modality_features, d_weights, d_output, n_modalities, feature_dim);
}

void launchL2NormalizeKernel(
    float* d_features,
    int feature_dim,
    cudaStream_t stream) {
    
    int block_size = 256;
    int grid_size = (feature_dim + block_size - 1) / block_size;
    
    l2NormalizeKernel<<<grid_size, block_size, 0, stream>>>(
        d_features, feature_dim);
}

} // extern "C"

} // namespace cuda
} // namespace multimodal
} // namespace cogniware

