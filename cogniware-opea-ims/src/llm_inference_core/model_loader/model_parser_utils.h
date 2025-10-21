#pragma once

#include <cstdint>
#include <string>
#include <vector>
#include <unordered_map>

namespace cogniware {
namespace llm_inference {

// GGUF constants
constexpr uint32_t GGUF_MAGIC = 0x46554747;  // "GGUF"
constexpr uint32_t GGUF_VERSION = 1;

// GGUF data types
enum class GGUFDataType {
    F32 = 0,
    F16 = 1,
    Q4_0 = 2,
    Q4_1 = 3,
    Q5_0 = 4,
    Q5_1 = 5,
    Q8_0 = 6,
    Q8_1 = 7,
    Q2_K = 8,
    Q3_K = 9,
    Q4_K = 10,
    Q5_K = 11,
    Q6_K = 12,
    Q8_K = 13
};

// GGUF tensor types
enum class GGUFTensorType {
    MODEL = 0,
    VOCAB = 1,
    METADATA = 2
};

// GGUF tensor info
struct GGUFTensorInfo {
    std::string name;
    GGUFDataType dtype;
    GGUFTensorType type;
    std::vector<int64_t> shape;
    size_t offset;
    size_t size;
    bool is_quantized;
    std::string quantization_type;
};

// GGUF metadata types
enum class GGUFMetadataType {
    STRING = 0,
    INT = 1,
    FLOAT = 2,
    BOOL = 3,
    ARRAY = 4,
    OBJECT = 5
};

// GGUF metadata value
struct GGUFMetadataValue {
    GGUFMetadataType type;
    union {
        std::string string_value;
        int64_t int_value;
        double float_value;
        bool bool_value;
        std::vector<GGUFMetadataValue> array_value;
        std::unordered_map<std::string, GGUFMetadataValue> object_value;
    };
};

// Helper functions
std::string getDataTypeName(GGUFDataType dtype);
size_t getDataTypeSize(GGUFDataType dtype);
bool isQuantized(GGUFDataType dtype);
std::string getQuantizationType(GGUFDataType dtype);

// Tensor operations
void* allocateTensor(const GGUFTensorInfo& info);
void deallocateTensor(void* data);
void* convertTensor(const void* data, const GGUFTensorInfo& src_info, GGUFDataType dst_dtype);
void* quantizeTensor(const void* data, const GGUFTensorInfo& info, GGUFDataType dst_dtype);
void* dequantizeTensor(const void* data, const GGUFTensorInfo& info);

// Metadata operations
GGUFMetadataValue parseMetadataValue(const char* data, size_t& offset);
std::string serializeMetadataValue(const GGUFMetadataValue& value);
void freeMetadataValue(GGUFMetadataValue& value);

// File operations
bool readFileHeader(const std::string& path, uint32_t& magic, uint32_t& version);
bool validateFileHeader(uint32_t magic, uint32_t version);
size_t getFileSize(const std::string& path);
bool isFileReadable(const std::string& path);

} // namespace llm_inference
} // namespace cogniware
