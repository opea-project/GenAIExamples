#include "model_parser_utils.h"
#include <spdlog/spdlog.h>
#include <fstream>
#include <cstring>
#include <algorithm>

namespace cogniware {
namespace llm_inference {

// Helper functions
std::string getDataTypeName(GGUFDataType dtype) {
    switch (dtype) {
        case GGUFDataType::F32: return "F32";
        case GGUFDataType::F16: return "F16";
        case GGUFDataType::Q4_0: return "Q4_0";
        case GGUFDataType::Q4_1: return "Q4_1";
        case GGUFDataType::Q5_0: return "Q5_0";
        case GGUFDataType::Q5_1: return "Q5_1";
        case GGUFDataType::Q8_0: return "Q8_0";
        case GGUFDataType::Q8_1: return "Q8_1";
        case GGUFDataType::Q2_K: return "Q2_K";
        case GGUFDataType::Q3_K: return "Q3_K";
        case GGUFDataType::Q4_K: return "Q4_K";
        case GGUFDataType::Q5_K: return "Q5_K";
        case GGUFDataType::Q6_K: return "Q6_K";
        case GGUFDataType::Q8_K: return "Q8_K";
        default: return "UNKNOWN";
    }
}

size_t getDataTypeSize(GGUFDataType dtype) {
    switch (dtype) {
        case GGUFDataType::F32: return 4;
        case GGUFDataType::F16: return 2;
        case GGUFDataType::Q4_0: return 1;
        case GGUFDataType::Q4_1: return 1;
        case GGUFDataType::Q5_0: return 1;
        case GGUFDataType::Q5_1: return 1;
        case GGUFDataType::Q8_0: return 1;
        case GGUFDataType::Q8_1: return 1;
        case GGUFDataType::Q2_K: return 1;
        case GGUFDataType::Q3_K: return 1;
        case GGUFDataType::Q4_K: return 1;
        case GGUFDataType::Q5_K: return 1;
        case GGUFDataType::Q6_K: return 1;
        case GGUFDataType::Q8_K: return 1;
        default: return 0;
    }
}

bool isQuantized(GGUFDataType dtype) {
    return dtype != GGUFDataType::F32 && dtype != GGUFDataType::F16;
}

std::string getQuantizationType(GGUFDataType dtype) {
    if (!isQuantized(dtype)) {
        return "NONE";
    }
    return getDataTypeName(dtype);
}

// Tensor operations
void* allocateTensor(const GGUFTensorInfo& info) {
    size_t size = info.size;
    if (size == 0) {
        size = 1;
        for (int64_t dim : info.shape) {
            size *= dim;
        }
        size *= getDataTypeSize(info.dtype);
    }

    void* data = malloc(size);
    if (!data) {
        spdlog::error("Failed to allocate memory for tensor: {}", info.name);
        return nullptr;
    }

    return data;
}

void deallocateTensor(void* data) {
    if (data) {
        free(data);
    }
}

void* convertTensor(const void* data, const GGUFTensorInfo& src_info, GGUFDataType dst_dtype) {
    if (!data) {
        return nullptr;
    }

    // Calculate size
    size_t size = 1;
    for (int64_t dim : src_info.shape) {
        size *= dim;
    }

    // Allocate destination tensor
    GGUFTensorInfo dst_info = src_info;
    dst_info.dtype = dst_dtype;
    void* dst_data = allocateTensor(dst_info);
    if (!dst_data) {
        return nullptr;
    }

    // Convert data
    switch (src_info.dtype) {
        case GGUFDataType::F32:
            switch (dst_dtype) {
                case GGUFDataType::F16:
                    // TODO: Implement F32 to F16 conversion
                    break;
                case GGUFDataType::Q4_0:
                case GGUFDataType::Q4_1:
                case GGUFDataType::Q5_0:
                case GGUFDataType::Q5_1:
                case GGUFDataType::Q8_0:
                case GGUFDataType::Q8_1:
                case GGUFDataType::Q2_K:
                case GGUFDataType::Q3_K:
                case GGUFDataType::Q4_K:
                case GGUFDataType::Q5_K:
                case GGUFDataType::Q6_K:
                case GGUFDataType::Q8_K:
                    // TODO: Implement quantization
                    break;
                default:
                    spdlog::error("Unsupported conversion from F32 to {}", getDataTypeName(dst_dtype));
                    deallocateTensor(dst_data);
                    return nullptr;
            }
            break;
        case GGUFDataType::F16:
            switch (dst_dtype) {
                case GGUFDataType::F32:
                    // TODO: Implement F16 to F32 conversion
                    break;
                case GGUFDataType::Q4_0:
                case GGUFDataType::Q4_1:
                case GGUFDataType::Q5_0:
                case GGUFDataType::Q5_1:
                case GGUFDataType::Q8_0:
                case GGUFDataType::Q8_1:
                case GGUFDataType::Q2_K:
                case GGUFDataType::Q3_K:
                case GGUFDataType::Q4_K:
                case GGUFDataType::Q5_K:
                case GGUFDataType::Q6_K:
                case GGUFDataType::Q8_K:
                    // TODO: Implement quantization
                    break;
                default:
                    spdlog::error("Unsupported conversion from F16 to {}", getDataTypeName(dst_dtype));
                    deallocateTensor(dst_data);
                    return nullptr;
            }
            break;
        default:
            spdlog::error("Unsupported source data type: {}", getDataTypeName(src_info.dtype));
            deallocateTensor(dst_data);
            return nullptr;
    }

    return dst_data;
}

void* quantizeTensor(const void* data, const GGUFTensorInfo& info, GGUFDataType dst_dtype) {
    if (!isQuantized(dst_dtype)) {
        spdlog::error("Destination data type is not quantized: {}", getDataTypeName(dst_dtype));
        return nullptr;
    }

    return convertTensor(data, info, dst_dtype);
}

void* dequantizeTensor(const void* data, const GGUFTensorInfo& info) {
    if (!isQuantized(info.dtype)) {
        spdlog::error("Source data type is not quantized: {}", getDataTypeName(info.dtype));
        return nullptr;
    }

    // Create new tensor info with F32 data type
    GGUFTensorInfo dst_info = info;
    dst_info.dtype = GGUFDataType::F32;

    return convertTensor(data, info, GGUFDataType::F32);
}

// Metadata operations
GGUFMetadataValue parseMetadataValue(const char* data, size_t& offset) {
    GGUFMetadataValue value;
    value.type = static_cast<GGUFMetadataType>(data[offset++]);

    switch (value.type) {
        case GGUFMetadataType::STRING: {
            uint32_t length;
            std::memcpy(&length, data + offset, sizeof(length));
            offset += sizeof(length);
            value.string_value = std::string(data + offset, length);
            offset += length;
            break;
        }
        case GGUFMetadataType::INT: {
            std::memcpy(&value.int_value, data + offset, sizeof(value.int_value));
            offset += sizeof(value.int_value);
            break;
        }
        case GGUFMetadataType::FLOAT: {
            std::memcpy(&value.float_value, data + offset, sizeof(value.float_value));
            offset += sizeof(value.float_value);
            break;
        }
        case GGUFMetadataType::BOOL: {
            value.bool_value = data[offset++] != 0;
            break;
        }
        case GGUFMetadataType::ARRAY: {
            uint32_t length;
            std::memcpy(&length, data + offset, sizeof(length));
            offset += sizeof(length);
            value.array_value.resize(length);
            for (uint32_t i = 0; i < length; ++i) {
                value.array_value[i] = parseMetadataValue(data, offset);
            }
            break;
        }
        case GGUFMetadataType::OBJECT: {
            uint32_t length;
            std::memcpy(&length, data + offset, sizeof(length));
            offset += sizeof(length);
            for (uint32_t i = 0; i < length; ++i) {
                // Parse key
                uint32_t key_length;
                std::memcpy(&key_length, data + offset, sizeof(key_length));
                offset += sizeof(key_length);
                std::string key(data + offset, key_length);
                offset += key_length;

                // Parse value
                value.object_value[key] = parseMetadataValue(data, offset);
            }
            break;
        }
        default:
            spdlog::error("Unknown metadata type: {}", static_cast<int>(value.type));
            break;
    }

    return value;
}

std::string serializeMetadataValue(const GGUFMetadataValue& value) {
    std::string result;
    result.push_back(static_cast<char>(value.type));

    switch (value.type) {
        case GGUFMetadataType::STRING: {
            uint32_t length = static_cast<uint32_t>(value.string_value.length());
            result.append(reinterpret_cast<char*>(&length), sizeof(length));
            result.append(value.string_value);
            break;
        }
        case GGUFMetadataType::INT: {
            result.append(reinterpret_cast<const char*>(&value.int_value), sizeof(value.int_value));
            break;
        }
        case GGUFMetadataType::FLOAT: {
            result.append(reinterpret_cast<const char*>(&value.float_value), sizeof(value.float_value));
            break;
        }
        case GGUFMetadataType::BOOL: {
            result.push_back(value.bool_value ? 1 : 0);
            break;
        }
        case GGUFMetadataType::ARRAY: {
            uint32_t length = static_cast<uint32_t>(value.array_value.size());
            result.append(reinterpret_cast<char*>(&length), sizeof(length));
            for (const auto& item : value.array_value) {
                result.append(serializeMetadataValue(item));
            }
            break;
        }
        case GGUFMetadataType::OBJECT: {
            uint32_t length = static_cast<uint32_t>(value.object_value.size());
            result.append(reinterpret_cast<char*>(&length), sizeof(length));
            for (const auto& [key, val] : value.object_value) {
                uint32_t key_length = static_cast<uint32_t>(key.length());
                result.append(reinterpret_cast<char*>(&key_length), sizeof(key_length));
                result.append(key);
                result.append(serializeMetadataValue(val));
            }
            break;
        }
        default:
            spdlog::error("Unknown metadata type: {}", static_cast<int>(value.type));
            break;
    }

    return result;
}

void freeMetadataValue(GGUFMetadataValue& value) {
    switch (value.type) {
        case GGUFMetadataType::STRING:
            value.string_value.clear();
            break;
        case GGUFMetadataType::ARRAY:
            for (auto& item : value.array_value) {
                freeMetadataValue(item);
            }
            value.array_value.clear();
            break;
        case GGUFMetadataType::OBJECT:
            for (auto& [key, val] : value.object_value) {
                freeMetadataValue(val);
            }
            value.object_value.clear();
            break;
        default:
            break;
    }
}

// File operations
bool readFileHeader(const std::string& path, uint32_t& magic, uint32_t& version) {
    std::ifstream file(path, std::ios::binary);
    if (!file.is_open()) {
        spdlog::error("Failed to open file: {}", path);
        return false;
    }

    file.read(reinterpret_cast<char*>(&magic), sizeof(magic));
    file.read(reinterpret_cast<char*>(&version), sizeof(version));

    return true;
}

bool validateFileHeader(uint32_t magic, uint32_t version) {
    if (magic != GGUF_MAGIC) {
        spdlog::error("Invalid magic number: {:x}", magic);
        return false;
    }

    if (version != GGUF_VERSION) {
        spdlog::error("Unsupported version: {}", version);
        return false;
    }

    return true;
}

size_t getFileSize(const std::string& path) {
    std::ifstream file(path, std::ios::binary | std::ios::ate);
    if (!file.is_open()) {
        return 0;
    }
    return file.tellg();
}

bool isFileReadable(const std::string& path) {
    std::ifstream file(path);
    return file.is_open();
}

} // namespace llm_inference
} // namespace cogniware
