#include <gtest/gtest.h>
#include "llm_inference_core/memory/gpu_memory_manager.h"
#include <vector>
#include <random>

using namespace cogniware;

class GPUMemoryManagerTest : public ::testing::Test {
protected:
    void SetUp() override {
        manager = &GPUMemoryManager::getInstance();
    }

    void TearDown() override {
        manager->reset();
    }

    GPUMemoryManager* manager;
};

TEST_F(GPUMemoryManagerTest, Initialization) {
    EXPECT_TRUE(manager->initialize());
}

TEST_F(GPUMemoryManagerTest, MemoryAllocation) {
    ASSERT_TRUE(manager->initialize());

    // Allocate memory
    void* ptr = manager->allocate(1024);
    EXPECT_NE(ptr, nullptr);

    // Free memory
    EXPECT_TRUE(manager->free(ptr));
}

TEST_F(GPUMemoryManagerTest, MemoryReallocation) {
    ASSERT_TRUE(manager->initialize());

    // Allocate memory
    void* ptr = manager->allocate(1024);
    ASSERT_NE(ptr, nullptr);

    // Reallocate memory
    void* newPtr = manager->reallocate(ptr, 2048);
    EXPECT_NE(newPtr, nullptr);
    EXPECT_NE(newPtr, ptr);

    // Free memory
    EXPECT_TRUE(manager->free(newPtr));
}

TEST_F(GPUMemoryManagerTest, MemoryPool) {
    ASSERT_TRUE(manager->initialize());

    // Create memory pool
    EXPECT_TRUE(manager->createMemoryPool("test-pool", 1024 * 1024));  // 1MB

    // Allocate from pool
    void* ptr = manager->allocateFromPool("test-pool", 512);
    EXPECT_NE(ptr, nullptr);

    // Free to pool
    EXPECT_TRUE(manager->freeToPool("test-pool", ptr));

    // Destroy pool
    EXPECT_TRUE(manager->destroyMemoryPool("test-pool"));
}

TEST_F(GPUMemoryManagerTest, MemoryStats) {
    ASSERT_TRUE(manager->initialize());

    auto stats = manager->getMemoryStats();
    EXPECT_GE(stats.totalMemory, 0);
    EXPECT_GE(stats.usedMemory, 0);
    EXPECT_GE(stats.freeMemory, 0);
    EXPECT_GE(stats.peakMemoryUsage, 0);
}

TEST_F(GPUMemoryManagerTest, ErrorHandling) {
    ASSERT_TRUE(manager->initialize());

    // Test invalid allocation size
    EXPECT_EQ(manager->allocate(0), nullptr);

    // Test invalid pool name
    EXPECT_FALSE(manager->createMemoryPool("", 1024));
    EXPECT_FALSE(manager->destroyMemoryPool(""));

    // Test non-existent pool
    EXPECT_EQ(manager->allocateFromPool("non-existent-pool", 1024), nullptr);
    EXPECT_FALSE(manager->freeToPool("non-existent-pool", nullptr));

    // Test invalid pointer
    EXPECT_FALSE(manager->free(nullptr));
    EXPECT_EQ(manager->reallocate(nullptr, 1024), nullptr);
}

TEST_F(GPUMemoryManagerTest, MemoryFragmentation) {
    ASSERT_TRUE(manager->initialize());

    // Allocate and free memory in a way that could cause fragmentation
    std::vector<void*> ptrs;
    for (int i = 0; i < 10; ++i) {
        ptrs.push_back(manager->allocate(1024));
        EXPECT_NE(ptrs.back(), nullptr);
    }

    // Free every other pointer
    for (size_t i = 0; i < ptrs.size(); i += 2) {
        EXPECT_TRUE(manager->free(ptrs[i]));
    }

    // Allocate larger chunks
    for (int i = 0; i < 5; ++i) {
        void* ptr = manager->allocate(2048);
        EXPECT_NE(ptr, nullptr);
        EXPECT_TRUE(manager->free(ptr));
    }

    // Free remaining pointers
    for (size_t i = 1; i < ptrs.size(); i += 2) {
        EXPECT_TRUE(manager->free(ptrs[i]));
    }
}

TEST_F(GPUMemoryManagerTest, MemoryAlignment) {
    ASSERT_TRUE(manager->initialize());

    // Allocate memory with different sizes
    std::vector<size_t> sizes = {1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024};
    for (size_t size : sizes) {
        void* ptr = manager->allocate(size);
        EXPECT_NE(ptr, nullptr);
        EXPECT_EQ(reinterpret_cast<uintptr_t>(ptr) % 256, 0);  // Check 256-byte alignment
        EXPECT_TRUE(manager->free(ptr));
    }
}

TEST_F(GPUMemoryManagerTest, MemoryPoolStats) {
    ASSERT_TRUE(manager->initialize());

    // Create memory pool
    EXPECT_TRUE(manager->createMemoryPool("test-pool", 1024 * 1024));  // 1MB

    // Get pool stats
    auto stats = manager->getMemoryPoolStats("test-pool");
    EXPECT_GE(stats.totalMemory, 0);
    EXPECT_GE(stats.usedMemory, 0);
    EXPECT_GE(stats.freeMemory, 0);
    EXPECT_GE(stats.peakMemoryUsage, 0);

    // Destroy pool
    EXPECT_TRUE(manager->destroyMemoryPool("test-pool"));
}

TEST_F(GPUMemoryManagerTest, MemoryReset) {
    ASSERT_TRUE(manager->initialize());

    // Allocate some memory
    void* ptr = manager->allocate(1024);
    EXPECT_NE(ptr, nullptr);

    // Reset memory manager
    manager->reset();

    // Try to free the pointer after reset
    EXPECT_FALSE(manager->free(ptr));

    // Allocate new memory after reset
    ptr = manager->allocate(1024);
    EXPECT_NE(ptr, nullptr);
    EXPECT_TRUE(manager->free(ptr));
}

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
} 