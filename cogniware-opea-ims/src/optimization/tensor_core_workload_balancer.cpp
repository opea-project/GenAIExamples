#include "optimization/tensor_core_optimizer.h"
#include <spdlog/spdlog.h>
#include <algorithm>
#include <numeric>

namespace cogniware {
namespace optimization {

TensorCoreWorkloadBalancer::TensorCoreWorkloadBalancer()
    : balancingStrategy_("round_robin")
    , loadThreshold_(0.8f) {
    
    spdlog::info("TensorCoreWorkloadBalancer initialized");
}

TensorCoreWorkloadBalancer::~TensorCoreWorkloadBalancer() {
    spdlog::info("TensorCoreWorkloadBalancer destroyed");
}

bool TensorCoreWorkloadBalancer::balanceWorkload(const std::vector<std::string>& llmIds) {
    std::lock_guard<std::mutex> lock(balancerMutex_);
    
    try {
        spdlog::info("Balancing workload for {} LLMs", llmIds.size());
        
        // Calculate current loads
        if (!calculateCoreLoads() || !calculateLLMLoads()) {
            spdlog::error("Failed to calculate current loads");
            return false;
        }
        
        // Check if rebalancing is needed
        if (isLoadBalanced()) {
            spdlog::info("Workload is already balanced");
            return true;
        }
        
        // Redistribute workload
        bool success = redistributeWorkload();
        
        if (success) {
            spdlog::info("Workload balancing completed successfully");
        } else {
            spdlog::error("Failed to redistribute workload");
        }
        
        return success;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to balance workload: {}", e.what());
        return false;
    }
}

bool TensorCoreWorkloadBalancer::distributeTasks(const std::map<std::string, std::string>& tasks) {
    std::lock_guard<std::mutex> lock(balancerMutex_);
    
    try {
        spdlog::info("Distributing {} tasks", tasks.size());
        
        // Distribute tasks based on balancing strategy
        if (balancingStrategy_ == "round_robin") {
            // Round-robin distribution
            int coreIndex = 0;
            for (const auto& task : tasks) {
                coreLoads_[coreIndex] += 0.1f; // Simulate task load
                coreIndex = (coreIndex + 1) % coreLoads_.size();
            }
        } else if (balancingStrategy_ == "least_loaded") {
            // Distribute to least loaded cores
            for (const auto& task : tasks) {
                auto minElement = std::min_element(coreLoads_.begin(), coreLoads_.end(),
                                                 [](const auto& a, const auto& b) {
                                                     return a.second < b.second;
                                                 });
                minElement->second += 0.1f; // Simulate task load
            }
        } else if (balancingStrategy_ == "weighted") {
            // Weighted distribution based on core capacity
            for (const auto& task : tasks) {
                // Find core with lowest relative load
                float minRelativeLoad = 1.0f;
                int bestCore = -1;
                for (const auto& core : coreLoads_) {
                    float relativeLoad = core.second / 1.0f; // Assuming max load of 1.0
                    if (relativeLoad < minRelativeLoad) {
                        minRelativeLoad = relativeLoad;
                        bestCore = core.first;
                    }
                }
                if (bestCore != -1) {
                    coreLoads_[bestCore] += 0.1f;
                }
            }
        }
        
        spdlog::info("Task distribution completed using strategy: {}", balancingStrategy_);
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to distribute tasks: {}", e.what());
        return false;
    }
}

bool TensorCoreWorkloadBalancer::optimizeCoreAssignment(const std::vector<int>& coreIds) {
    std::lock_guard<std::mutex> lock(balancerMutex_);
    
    try {
        spdlog::info("Optimizing core assignment for {} cores", coreIds.size());
        
        // Optimize assignment based on current loads
        for (int coreId : coreIds) {
            if (coreLoads_.find(coreId) != coreLoads_.end()) {
                // Optimize this core's assignment
                float currentLoad = coreLoads_[coreId];
                if (currentLoad > loadThreshold_) {
                    // Reduce load by redistributing
                    coreLoads_[coreId] *= 0.8f;
                    spdlog::debug("Reduced load for core {} from {:.2f} to {:.2f}", 
                                coreId, currentLoad, coreLoads_[coreId]);
                }
            }
        }
        
        spdlog::info("Core assignment optimization completed");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to optimize core assignment: {}", e.what());
        return false;
    }
}

bool TensorCoreWorkloadBalancer::rebalanceWorkload() {
    std::lock_guard<std::mutex> lock(balancerMutex_);
    
    try {
        spdlog::info("Rebalancing workload");
        
        // Calculate average load
        float totalLoad = 0.0f;
        for (const auto& load : coreLoads_) {
            totalLoad += load.second;
        }
        float averageLoad = totalLoad / coreLoads_.size();
        
        // Redistribute load to balance
        for (auto& load : coreLoads_) {
            if (load.second > averageLoad * 1.2f) {
                // Reduce load for overloaded cores
                load.second = averageLoad * 1.1f;
            } else if (load.second < averageLoad * 0.8f) {
                // Increase load for underloaded cores
                load.second = averageLoad * 0.9f;
            }
        }
        
        spdlog::info("Workload rebalancing completed");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to rebalance workload: {}", e.what());
        return false;
    }
}

std::map<int, float> TensorCoreWorkloadBalancer::getCoreLoads() {
    std::lock_guard<std::mutex> lock(balancerMutex_);
    return coreLoads_;
}

std::map<std::string, float> TensorCoreWorkloadBalancer::getLLMLoads() {
    std::lock_guard<std::mutex> lock(balancerMutex_);
    return llmLoads_;
}

bool TensorCoreWorkloadBalancer::isLoadBalanced() {
    std::lock_guard<std::mutex> lock(balancerMutex_);
    
    if (coreLoads_.empty()) {
        return true;
    }
    
    // Calculate load imbalance
    float maxLoad = 0.0f;
    float minLoad = 1.0f;
    
    for (const auto& load : coreLoads_) {
        maxLoad = std::max(maxLoad, load.second);
        minLoad = std::min(minLoad, load.second);
    }
    
    float imbalance = maxLoad - minLoad;
    return imbalance <= (loadThreshold_ * 0.2f); // 20% of threshold
}

float TensorCoreWorkloadBalancer::getLoadImbalance() {
    std::lock_guard<std::mutex> lock(balancerMutex_);
    
    if (coreLoads_.empty()) {
        return 0.0f;
    }
    
    float maxLoad = 0.0f;
    float minLoad = 1.0f;
    
    for (const auto& load : coreLoads_) {
        maxLoad = std::max(maxLoad, load.second);
        minLoad = std::min(minLoad, load.second);
    }
    
    return maxLoad - minLoad;
}

void TensorCoreWorkloadBalancer::setBalancingStrategy(const std::string& strategy) {
    std::lock_guard<std::mutex> lock(balancerMutex_);
    balancingStrategy_ = strategy;
    spdlog::info("Set balancing strategy to: {}", strategy);
}

std::string TensorCoreWorkloadBalancer::getBalancingStrategy() const {
    return balancingStrategy_;
}

void TensorCoreWorkloadBalancer::setLoadThreshold(float threshold) {
    std::lock_guard<std::mutex> lock(balancerMutex_);
    loadThreshold_ = threshold;
    spdlog::info("Set load threshold to: {:.2f}", threshold);
}

float TensorCoreWorkloadBalancer::getLoadThreshold() const {
    return loadThreshold_;
}

bool TensorCoreWorkloadBalancer::calculateCoreLoads() {
    try {
        // Simulate core load calculation
        coreLoads_.clear();
        
        // Initialize with some simulated loads
        for (int i = 0; i < 8; ++i) { // Simulate 8 cores
            float load = 0.3f + (i * 0.1f); // Varying loads
            coreLoads_[i] = std::min(load, 1.0f);
        }
        
        spdlog::debug("Calculated loads for {} cores", coreLoads_.size());
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to calculate core loads: {}", e.what());
        return false;
    }
}

bool TensorCoreWorkloadBalancer::calculateLLMLoads() {
    try {
        // Simulate LLM load calculation
        llmLoads_.clear();
        
        // Initialize with some simulated LLM loads
        std::vector<std::string> llmIds = {"llm1", "llm2", "llm3", "llm4"};
        for (const auto& llmId : llmIds) {
            float load = 0.2f + (std::hash<std::string>{}(llmId) % 100) / 100.0f * 0.6f;
            llmLoads_[llmId] = std::min(load, 1.0f);
        }
        
        spdlog::debug("Calculated loads for {} LLMs", llmLoads_.size());
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to calculate LLM loads: {}", e.what());
        return false;
    }
}

bool TensorCoreWorkloadBalancer::redistributeWorkload() {
    try {
        // Redistribute workload based on balancing strategy
        if (balancingStrategy_ == "round_robin") {
            // Simple round-robin redistribution
            float totalLoad = 0.0f;
            for (const auto& load : coreLoads_) {
                totalLoad += load.second;
            }
            
            float loadPerCore = totalLoad / coreLoads_.size();
            for (auto& load : coreLoads_) {
                load.second = loadPerCore;
            }
        } else if (balancingStrategy_ == "least_loaded") {
            // Redistribute to least loaded cores
            auto minElement = std::min_element(coreLoads_.begin(), coreLoads_.end(),
                                             [](const auto& a, const auto& b) {
                                                 return a.second < b.second;
                                             });
            float minLoad = minElement->second;
            
            // Redistribute excess load
            for (auto& load : coreLoads_) {
                if (load.second > minLoad * 1.5f) {
                    load.second = minLoad * 1.2f;
                }
            }
        }
        
        spdlog::debug("Workload redistribution completed");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to redistribute workload: {}", e.what());
        return false;
    }
}

bool TensorCoreWorkloadBalancer::optimizeCoreAssignment() {
    try {
        // Optimize core assignment based on load patterns
        float averageLoad = 0.0f;
        for (const auto& load : coreLoads_) {
            averageLoad += load.second;
        }
        averageLoad /= coreLoads_.size();
        
        // Optimize assignment
        for (auto& load : coreLoads_) {
            if (load.second > averageLoad * 1.3f) {
                // Reduce load for overloaded cores
                load.second = averageLoad * 1.1f;
            } else if (load.second < averageLoad * 0.7f) {
                // Increase load for underloaded cores
                load.second = averageLoad * 0.9f;
            }
        }
        
        spdlog::debug("Core assignment optimization completed");
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("Failed to optimize core assignment: {}", e.what());
        return false;
    }
}

} // namespace optimization
} // namespace cogniware
