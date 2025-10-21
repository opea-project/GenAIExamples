#include "../../include/llm_inference/fast_router_core.h"
#include <cuda_runtime.h>
#include <cublas_v2.h>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <cmath>
#include <mutex>
#include <chrono>
#include <spdlog/spdlog.h>
#include <thread>

namespace cogniware {
namespace llm_inference {

FastRouterCore& FastRouterCore::getInstance() {
    static FastRouterCore instance;
    return instance;
}

FastRouterCore::FastRouterCore()
    : is_running_(false)
    , max_queue_size_(1000)
    , max_batch_size_(32)
    , max_wait_time_ms_(100)
    , model_embeddings_(nullptr)
    , embedding_dim_(0)
    , total_queries_(0)
    , total_confidence_(0.0f)
    , stream_(nullptr)
    , d_query_embedding_(nullptr)
    , d_model_embedding_(nullptr)
    , d_similarity_(nullptr)
{
    try {
        // Initialize thread pool
        thread_pool_ = std::make_unique<ThreadPool>(std::thread::hardware_concurrency());
        spdlog::info("Fast Router Core initialized with {} threads", std::thread::hardware_concurrency());

        cudaStreamCreate(&stream_);
    } catch (const std::exception& e) {
        spdlog::error("Failed to initialize Fast Router Core: {}", e.what());
        throw;
    }
}

FastRouterCore::~FastRouterCore() {
    try {
        stop();
        if (model_embeddings_) cudaFree(model_embeddings_);
        if (d_query_embedding_) cudaFree(d_query_embedding_);
        if (d_model_embedding_) cudaFree(d_model_embedding_);
        if (d_similarity_) cudaFree(d_similarity_);
        if (stream_) cudaStreamDestroy(stream_);
        spdlog::info("Fast Router Core cleaned up");
    } catch (const std::exception& e) {
        spdlog::error("Error during Fast Router Core cleanup: {}", e.what());
    }
}

void FastRouterCore::start() {
    try {
        std::lock_guard<std::mutex> lock(mutex_);
        if (is_running_) {
            return;
        }

        is_running_ = true;
        router_thread_ = std::thread(&FastRouterCore::routerLoop, this);
        spdlog::info("Fast Router Core started");
    } catch (const std::exception& e) {
        spdlog::error("Failed to start Fast Router Core: {}", e.what());
        throw;
    }
}

void FastRouterCore::stop() {
    try {
        {
            std::lock_guard<std::mutex> lock(mutex_);
            if (!is_running_) {
                return;
            }
            is_running_ = false;
        }

        if (router_thread_.joinable()) {
            router_thread_.join();
        }

        // Clear queues
        std::lock_guard<std::mutex> lock(mutex_);
        request_queue_.clear();
        batch_queue_.clear();
        spdlog::info("Fast Router Core stopped");
    } catch (const std::exception& e) {
        spdlog::error("Failed to stop Fast Router Core: {}", e.what());
        throw;
    }
}

bool FastRouterCore::enqueueRequest(const InferenceRequest& request) {
    try {
        std::lock_guard<std::mutex> lock(mutex_);
        if (!is_running_) {
            spdlog::error("Fast Router Core is not running");
            return false;
        }

        if (request_queue_.size() >= max_queue_size_) {
            spdlog::warn("Request queue is full");
            return false;
        }

        request_queue_.push_back(request);
        spdlog::debug("Enqueued request for model {}", request.model_id);
        return true;
    } catch (const std::exception& e) {
        spdlog::error("Failed to enqueue request: {}", e.what());
        return false;
    }
}

void FastRouterCore::setMaxQueueSize(size_t size) {
    std::lock_guard<std::mutex> lock(mutex_);
    max_queue_size_ = size;
    spdlog::info("Set maximum queue size to {}", size);
}

void FastRouterCore::setMaxBatchSize(size_t size) {
    std::lock_guard<std::mutex> lock(mutex_);
    max_batch_size_ = size;
    spdlog::info("Set maximum batch size to {}", size);
}

void FastRouterCore::setMaxWaitTime(size_t ms) {
    std::lock_guard<std::mutex> lock(mutex_);
    max_wait_time_ms_ = ms;
    spdlog::info("Set maximum wait time to {} ms", ms);
}

size_t FastRouterCore::getQueueSize() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return request_queue_.size();
}

size_t FastRouterCore::getBatchQueueSize() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return batch_queue_.size();
}

void FastRouterCore::routerLoop() {
    while (true) {
        try {
            // Check if we should stop
            {
                std::lock_guard<std::mutex> lock(mutex_);
                if (!is_running_) {
                    break;
                }
            }

            // Process requests
            processRequests();

            // Process batches
            processBatches();

            // Sleep to prevent busy waiting
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        } catch (const std::exception& e) {
            spdlog::error("Error in router loop: {}", e.what());
        }
    }
}

void FastRouterCore::processRequests() {
    try {
        std::lock_guard<std::mutex> lock(mutex_);
        if (request_queue_.empty()) {
            return;
        }

        // Group requests by model
        std::unordered_map<std::string, std::vector<InferenceRequest>> model_requests;
        auto now = std::chrono::steady_clock::now();

        while (!request_queue_.empty()) {
            auto& request = request_queue_.front();
            
            // Check if request has timed out
            if (std::chrono::duration_cast<std::chrono::milliseconds>(
                now - request.timestamp).count() > max_wait_time_ms_) {
                request_queue_.pop_front();
                continue;
            }

            // Add to model group
            model_requests[request.model_id].push_back(request);
            request_queue_.pop_front();

            // Check batch size
            if (model_requests[request.model_id].size() >= max_batch_size_) {
                break;
            }
        }

        // Create batches
        for (auto& [model_id, requests] : model_requests) {
            if (requests.empty()) {
                continue;
            }

            BatchRequest batch;
            batch.model_id = model_id;
            batch.requests = std::move(requests);
            batch.timestamp = now;

            batch_queue_.push_back(std::move(batch));
            spdlog::debug("Created batch of {} requests for model {}", 
                batch.requests.size(), model_id);
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to process requests: {}", e.what());
    }
}

void FastRouterCore::processBatches() {
    try {
        std::lock_guard<std::mutex> lock(mutex_);
        if (batch_queue_.empty()) {
            return;
        }

        auto& batch = batch_queue_.front();
        auto now = std::chrono::steady_clock::now();

        // Check if batch has timed out
        if (std::chrono::duration_cast<std::chrono::milliseconds>(
            now - batch.timestamp).count() > max_wait_time_ms_) {
            // Process batch even if timed out
            processBatch(batch);
            batch_queue_.pop_front();
            return;
        }

        // Check if we have enough requests
        if (batch.requests.size() >= max_batch_size_) {
            processBatch(batch);
            batch_queue_.pop_front();
            return;
        }

        // Wait for more requests
        return;
    } catch (const std::exception& e) {
        spdlog::error("Failed to process batches: {}", e.what());
    }
}

void FastRouterCore::processBatch(const BatchRequest& batch) {
    try {
        // Prepare batch inputs
        std::vector<std::string> prompts;
        std::vector<std::unordered_map<std::string, std::string>> parameters;
        prompts.reserve(batch.requests.size());
        parameters.reserve(batch.requests.size());

        for (const auto& request : batch.requests) {
            prompts.push_back(request.prompt);
            parameters.push_back(request.parameters);
        }

        // Run batch inference
        std::vector<std::string> outputs;
        auto& instance_manager = LLMInstanceManager::getInstance();
        if (!instance_manager.batchGenerate(batch.model_id, prompts, parameters, outputs)) {
            spdlog::error("Batch inference failed for model {}", batch.model_id);
            return;
        }

        // Send results back
        for (size_t i = 0; i < batch.requests.size(); ++i) {
            if (i < outputs.size()) {
                batch.requests[i].callback(outputs[i]);
            } else {
                batch.requests[i].callback("");
            }
        }

        spdlog::debug("Processed batch of {} requests for model {}", 
            batch.requests.size(), batch.model_id);
    } catch (const std::exception& e) {
        spdlog::error("Failed to process batch: {}", e.what());
    }
}

bool FastRouterCore::initialize(const std::vector<ModelProfile>& profiles) {
    // Clear existing profiles
    model_profiles_.clear();

    // Add new profiles
    for (const auto& profile : profiles) {
        model_profiles_[profile.model_id] = profile;
    }

    return true;
}

bool FastRouterCore::loadEmbeddings(const std::string& path) {
    std::ifstream file(path, std::ios::binary);
    if (!file) {
        return false;
    }

    // Read embedding dimension
    file.read(reinterpret_cast<char*>(&embedding_dim_), sizeof(embedding_dim_));

    // Allocate GPU memory for embeddings
    size_t num_models = model_profiles_.size();
    size_t embedding_size = num_models * embedding_dim_ * sizeof(float);

    if (model_embeddings_) {
        cudaFree(model_embeddings_);
    }
    model_embeddings_ = static_cast<float*>(GPUMemoryManager::getInstance().allocate(embedding_size));

    // Read and copy embeddings to GPU
    std::vector<float> host_embeddings(num_models * embedding_dim_);
    file.read(reinterpret_cast<char*>(host_embeddings.data()), embedding_size);
    GPUMemoryManager::getInstance().copyToDevice(model_embeddings_, host_embeddings.data(), embedding_size);

    // Allocate temporary buffers
    if (d_query_embedding_) cudaFree(d_query_embedding_);
    if (d_model_embedding_) cudaFree(d_model_embedding_);
    if (d_similarity_) cudaFree(d_similarity_);

    d_query_embedding_ = static_cast<float*>(GPUMemoryManager::getInstance().allocate(embedding_dim_ * sizeof(float)));
    d_model_embedding_ = static_cast<float*>(GPUMemoryManager::getInstance().allocate(embedding_dim_ * sizeof(float)));
    d_similarity_ = static_cast<float*>(GPUMemoryManager::getInstance().allocate(sizeof(float)));

    return true;
}

RoutingDecision FastRouterCore::routeQuery(
    const std::string& query,
    const std::vector<std::string>& context
) {
    RoutingDecision decision;
    decision.needs_system2 = false;

    // Compute query embedding
    std::vector<float> query_embedding(embedding_dim_);
    if (!computeQueryEmbedding(query, query_embedding.data())) {
        decision.model_id = "";
        decision.confidence = 0.0f;
        decision.reasoning = "Failed to compute query embedding";
        return decision;
    }

    // Copy query embedding to GPU
    GPUMemoryManager::getInstance().copyToDevice(d_query_embedding_, query_embedding.data(), embedding_dim_ * sizeof(float));

    // Find best matching model
    float best_similarity = -1.0f;
    std::string best_model_id;

    for (const auto& [model_id, profile] : model_profiles_) {
        // Compute similarity
        float similarity;
        if (!computeSimilarity(d_query_embedding_, model_embeddings_ + profile.base_confidence * embedding_dim_, similarity)) {
            continue;
        }

        // Check specialties and roles
        float specialty_score = 0.0f;
        if (!matchKeywords(query, profile.specialties, specialty_score)) {
            continue;
        }

        float role_score = 0.0f;
        if (!matchKeywords(query, profile.roles, role_score)) {
            continue;
        }

        // Combine scores
        float combined_score = similarity * 0.5f + specialty_score * 0.3f + role_score * 0.2f;
        combined_score *= profile.base_confidence;

        if (combined_score > best_similarity) {
            best_similarity = combined_score;
            best_model_id = model_id;
        }
    }

    // Update statistics
    total_queries_++;
    total_confidence_ += best_similarity;

    // Set decision
    decision.model_id = best_model_id;
    decision.confidence = best_similarity;
    decision.reasoning = "Selected based on semantic similarity, specialties, and roles";
    decision.needs_system2 = best_similarity < 0.7f;  // Threshold for System 2 routing

    return decision;
}

bool FastRouterCore::addModelProfile(const ModelProfile& profile) {
    model_profiles_[profile.model_id] = profile;
    return true;
}

bool FastRouterCore::removeModelProfile(const std::string& model_id) {
    return model_profiles_.erase(model_id) > 0;
}

bool FastRouterCore::updateModelProfile(const ModelProfile& profile) {
    if (model_profiles_.find(profile.model_id) == model_profiles_.end()) {
        return false;
    }
    model_profiles_[profile.model_id] = profile;
    return true;
}

size_t FastRouterCore::getTotalQueries() const {
    return total_queries_;
}

float FastRouterCore::getAverageConfidence() const {
    return total_queries_ > 0 ? total_confidence_ / total_queries_ : 0.0f;
}

std::vector<std::string> FastRouterCore::getMostUsedModels() const {
    // TODO: Implement model usage tracking
    return {};
}

bool FastRouterCore::computeQueryEmbedding(const std::string& query, float* embedding) {
    try {
        // Initialize embedding model if not already done
        if (!embedding_model_) {
            embedding_model_ = std::make_unique<EmbeddingModel>();
            embedding_model_->load(model_config_.embedding_model_path);
        }
        
        // Tokenize query
        auto tokens = tokenizer_->encode(query);
        
        // Compute embedding
        auto embedding_vector = embedding_model_->computeEmbedding(tokens);
        
        // Normalize embedding
        float norm = 0.0f;
        for (float value : embedding_vector) {
            norm += value * value;
        }
        norm = std::sqrt(norm);
        
        if (norm > 0.0f) {
            for (float& value : embedding_vector) {
                value /= norm;
            }
        }
        
        // Copy embedding to output
        std::copy(embedding_vector.begin(), embedding_vector.end(), embedding);
        
        return true;
    } catch (const std::exception& e) {
        throw RouterError("Failed to compute query embedding: " + std::string(e.what()));
    }
}

bool FastRouterCore::computeSimilarity(const float* query_embedding, const float* model_embedding, float& similarity) {
    // Copy model embedding to GPU
    GPUMemoryManager::getInstance().copyToDevice(d_model_embedding_, model_embedding, embedding_dim_ * sizeof(float));

    // Compute dot product using cuBLAS
    cublasHandle_t handle;
    cublasCreate(&handle);
    float alpha = 1.0f;
    float beta = 0.0f;
    cublasSgemv(handle, CUBLAS_OP_T, embedding_dim_, 1,
        &alpha, d_query_embedding_, embedding_dim_,
        d_model_embedding_, 1, &beta, d_similarity_, 1);
    cublasDestroy(handle);

    // Copy result back to host
    GPUMemoryManager::getInstance().copyToHost(&similarity, d_similarity_, sizeof(float));

    return true;
}

bool FastRouterCore::matchKeywords(const std::string& query, const std::vector<std::string>& keywords, float& score) {
    score = 0.0f;
    if (keywords.empty()) {
        return true;
    }

    std::istringstream iss(query);
    std::string word;
    std::vector<std::string> query_words;
    while (iss >> word) {
        query_words.push_back(word);
    }

    size_t matches = 0;
    for (const auto& keyword : keywords) {
        if (std::find(query_words.begin(), query_words.end(), keyword) != query_words.end()) {
            matches++;
        }
    }

    score = static_cast<float>(matches) / keywords.size();
    return true;
}

void FastRouterCore::trackModelUsage(const std::string& model_id, const RequestStats& stats) {
    std::lock_guard<std::mutex> lock(usage_mutex_);
    
    // Update model usage statistics
    auto& model_stats = model_usage_[model_id];
    model_stats.total_requests++;
    model_stats.total_tokens += stats.input_tokens + stats.output_tokens;
    model_stats.total_latency += stats.latency;
    
    // Update rolling window statistics
    auto now = std::chrono::steady_clock::now();
    model_stats.request_history.push_back({now, stats});
    
    // Remove old entries (older than 1 hour)
    auto one_hour_ago = now - std::chrono::hours(1);
    model_stats.request_history.erase(
        std::remove_if(
            model_stats.request_history.begin(),
            model_stats.request_history.end(),
            [&](const auto& entry) { return entry.timestamp < one_hour_ago; }
        ),
        model_stats.request_history.end()
    );
    
    // Calculate current metrics
    model_stats.current_throughput = calculateThroughput(model_stats.request_history);
    model_stats.current_latency = calculateAverageLatency(model_stats.request_history);
    model_stats.current_token_rate = calculateTokenRate(model_stats.request_history);
}

} // namespace llm_inference
} // namespace cogniware 