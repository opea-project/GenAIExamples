#pragma once

#include <string>
#include <memory>
#include <mutex>
#include <unordered_map>
#include <vector>
#include <variant>
#include <optional>
#include <nlohmann/json.hpp>
#include "error_handler_cpp.h"

namespace cogniware {
namespace utils {

// Configuration value types
using ConfigValue = std::variant<
    bool,
    int,
    double,
    std::string,
    std::vector<bool>,
    std::vector<int>,
    std::vector<double>,
    std::vector<std::string>
>;

// Configuration section
struct ConfigSection {
    std::string name;
    std::unordered_map<std::string, ConfigValue> values;
    std::unordered_map<std::string, ConfigSection> subsections;

    ConfigSection() = default;
    explicit ConfigSection(const std::string& section_name) : name(section_name) {}
};

// Configuration schema
struct ConfigSchema {
    struct Field {
        std::string name;
        std::string type;
        bool required;
        ConfigValue default_value;
        std::vector<ConfigValue> allowed_values;
        std::function<bool(const ConfigValue&)> validator;

        Field() : required(false) {}
    };

    std::string name;
    std::vector<Field> fields;
    std::unordered_map<std::string, ConfigSchema> subschemas;
};

// Configuration parser class
class ConfigParser {
public:
    static ConfigParser& getInstance();

    // Prevent copying
    ConfigParser(const ConfigParser&) = delete;
    ConfigParser& operator=(const ConfigParser&) = delete;

    // Configuration loading
    bool loadFromFile(const std::string& filename);
    bool loadFromString(const std::string& config_str);
    bool loadFromJson(const nlohmann::json& json);
    void clear();

    // Configuration access
    bool hasSection(const std::string& section) const;
    bool hasValue(const std::string& section, const std::string& key) const;
    std::optional<ConfigValue> getValue(const std::string& section, const std::string& key) const;
    std::optional<ConfigSection> getSection(const std::string& section) const;
    std::vector<std::string> getSections() const;
    std::vector<std::string> getKeys(const std::string& section) const;

    // Configuration modification
    bool setValue(const std::string& section, const std::string& key, const ConfigValue& value);
    bool removeValue(const std::string& section, const std::string& key);
    bool addSection(const std::string& section);
    bool removeSection(const std::string& section);

    // Configuration validation
    bool validate(const ConfigSchema& schema) const;
    std::vector<std::string> getValidationErrors() const;

    // Configuration serialization
    std::string toString() const;
    nlohmann::json toJson() const;
    bool saveToFile(const std::string& filename) const;

    // Type conversion helpers
    template<typename T>
    std::optional<T> getValueAs(const std::string& section, const std::string& key) const {
        auto value = getValue(section, key);
        if (!value) {
            return std::nullopt;
        }
        try {
            return std::get<T>(*value);
        } catch (const std::bad_variant_access&) {
            return std::nullopt;
        }
    }

    // Convenience methods for common types
    std::optional<bool> getBool(const std::string& section, const std::string& key) const {
        return getValueAs<bool>(section, key);
    }

    std::optional<int> getInt(const std::string& section, const std::string& key) const {
        return getValueAs<int>(section, key);
    }

    std::optional<double> getDouble(const std::string& section, const std::string& key) const {
        return getValueAs<double>(section, key);
    }

    std::optional<std::string> getString(const std::string& section, const std::string& key) const {
        return getValueAs<std::string>(section, key);
    }

    std::optional<std::vector<bool>> getBoolArray(const std::string& section, const std::string& key) const {
        return getValueAs<std::vector<bool>>(section, key);
    }

    std::optional<std::vector<int>> getIntArray(const std::string& section, const std::string& key) const {
        return getValueAs<std::vector<int>>(section, key);
    }

    std::optional<std::vector<double>> getDoubleArray(const std::string& section, const std::string& key) const {
        return getValueAs<std::vector<double>>(section, key);
    }

    std::optional<std::vector<std::string>> getStringArray(const std::string& section, const std::string& key) const {
        return getValueAs<std::vector<std::string>>(section, key);
    }

private:
    ConfigParser();
    ~ConfigParser();

    bool parseJson(const nlohmann::json& json, ConfigSection& section);
    bool validateSection(const ConfigSection& section, const ConfigSchema& schema, 
                        std::vector<std::string>& errors, const std::string& path = "") const;
    bool validateValue(const ConfigValue& value, const ConfigSchema::Field& field,
                      std::vector<std::string>& errors, const std::string& path) const;
    nlohmann::json sectionToJson(const ConfigSection& section) const;

    std::unordered_map<std::string, ConfigSection> sections_;
    std::mutex mutex_;
    std::vector<std::string> validation_errors_;
};

} // namespace utils
} // namespace cogniware
