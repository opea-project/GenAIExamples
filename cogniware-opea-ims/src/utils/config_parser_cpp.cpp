#include "config_parser_cpp.h"
#include "logger_cpp.h"
#include <fstream>
#include <sstream>
#include <filesystem>

namespace cogniware {
namespace utils {

ConfigParser& ConfigParser::getInstance() {
    static ConfigParser instance;
    return instance;
}

ConfigParser::ConfigParser() {
    // Initialize empty configuration
}

ConfigParser::~ConfigParser() {
    clear();
}

bool ConfigParser::loadFromFile(const std::string& filename) {
    try {
        if (!std::filesystem::exists(filename)) {
            LOG_ERROR("Configuration file not found: {}", filename);
            return false;
        }

        std::ifstream file(filename);
        if (!file.is_open()) {
            LOG_ERROR("Failed to open configuration file: {}", filename);
            return false;
        }

        std::stringstream buffer;
        buffer << file.rdbuf();
        return loadFromString(buffer.str());
    } catch (const std::exception& e) {
        LOG_ERROR("Error loading configuration file: {}", e.what());
        return false;
    }
}

bool ConfigParser::loadFromString(const std::string& config_str) {
    try {
        auto json = nlohmann::json::parse(config_str);
        return loadFromJson(json);
    } catch (const nlohmann::json::parse_error& e) {
        LOG_ERROR("JSON parse error: {}", e.what());
        return false;
    } catch (const std::exception& e) {
        LOG_ERROR("Error parsing configuration string: {}", e.what());
        return false;
    }
}

bool ConfigParser::loadFromJson(const nlohmann::json& json) {
    std::lock_guard<std::mutex> lock(mutex_);
    sections_.clear();
    validation_errors_.clear();

    try {
        for (const auto& [key, value] : json.items()) {
            ConfigSection section(key);
            if (!parseJson(value, section)) {
                LOG_ERROR("Failed to parse section: {}", key);
                return false;
            }
            sections_[key] = std::move(section);
        }
        return true;
    } catch (const std::exception& e) {
        LOG_ERROR("Error loading JSON configuration: {}", e.what());
        return false;
    }
}

void ConfigParser::clear() {
    std::lock_guard<std::mutex> lock(mutex_);
    sections_.clear();
    validation_errors_.clear();
}

bool ConfigParser::hasSection(const std::string& section) const {
    std::lock_guard<std::mutex> lock(mutex_);
    return sections_.find(section) != sections_.end();
}

bool ConfigParser::hasValue(const std::string& section, const std::string& key) const {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = sections_.find(section);
    if (it == sections_.end()) {
        return false;
    }
    return it->second.values.find(key) != it->second.values.end();
}

std::optional<ConfigValue> ConfigParser::getValue(const std::string& section, const std::string& key) const {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = sections_.find(section);
    if (it == sections_.end()) {
        return std::nullopt;
    }
    auto value_it = it->second.values.find(key);
    if (value_it == it->second.values.end()) {
        return std::nullopt;
    }
    return value_it->second;
}

std::optional<ConfigSection> ConfigParser::getSection(const std::string& section) const {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = sections_.find(section);
    if (it == sections_.end()) {
        return std::nullopt;
    }
    return it->second;
}

std::vector<std::string> ConfigParser::getSections() const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<std::string> result;
    result.reserve(sections_.size());
    for (const auto& [key, _] : sections_) {
        result.push_back(key);
    }
    return result;
}

std::vector<std::string> ConfigParser::getKeys(const std::string& section) const {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = sections_.find(section);
    if (it == sections_.end()) {
        return {};
    }
    std::vector<std::string> result;
    result.reserve(it->second.values.size());
    for (const auto& [key, _] : it->second.values) {
        result.push_back(key);
    }
    return result;
}

bool ConfigParser::setValue(const std::string& section, const std::string& key, const ConfigValue& value) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = sections_.find(section);
    if (it == sections_.end()) {
        sections_[section] = ConfigSection(section);
        it = sections_.find(section);
    }
    it->second.values[key] = value;
    return true;
}

bool ConfigParser::removeValue(const std::string& section, const std::string& key) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = sections_.find(section);
    if (it == sections_.end()) {
        return false;
    }
    return it->second.values.erase(key) > 0;
}

bool ConfigParser::addSection(const std::string& section) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (sections_.find(section) != sections_.end()) {
        return false;
    }
    sections_[section] = ConfigSection(section);
    return true;
}

bool ConfigParser::removeSection(const std::string& section) {
    std::lock_guard<std::mutex> lock(mutex_);
    return sections_.erase(section) > 0;
}

bool ConfigParser::validate(const ConfigSchema& schema) const {
    std::lock_guard<std::mutex> lock(mutex_);
    validation_errors_.clear();
    bool valid = true;

    for (const auto& [section_name, section] : sections_) {
        auto schema_it = schema.subschemas.find(section_name);
        if (schema_it == schema.subschemas.end()) {
            validation_errors_.push_back("Unknown section: " + section_name);
            valid = false;
            continue;
        }

        if (!validateSection(section, schema_it->second, validation_errors_, section_name)) {
            valid = false;
        }
    }

    return valid;
}

std::vector<std::string> ConfigParser::getValidationErrors() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return validation_errors_;
}

std::string ConfigParser::toString() const {
    return toJson().dump(4);
}

nlohmann::json ConfigParser::toJson() const {
    std::lock_guard<std::mutex> lock(mutex_);
    nlohmann::json result;
    for (const auto& [section_name, section] : sections_) {
        result[section_name] = sectionToJson(section);
    }
    return result;
}

bool ConfigParser::saveToFile(const std::string& filename) const {
    try {
        std::ofstream file(filename);
        if (!file.is_open()) {
            LOG_ERROR("Failed to open file for writing: {}", filename);
            return false;
        }
        file << toString();
        return true;
    } catch (const std::exception& e) {
        LOG_ERROR("Error saving configuration to file: {}", e.what());
        return false;
    }
}

bool ConfigParser::parseJson(const nlohmann::json& json, ConfigSection& section) {
    try {
        for (const auto& [key, value] : json.items()) {
            if (value.is_object()) {
                ConfigSection subsection(key);
                if (!parseJson(value, subsection)) {
                    return false;
                }
                section.subsections[key] = std::move(subsection);
            } else if (value.is_array()) {
                if (value.empty()) {
                    section.values[key] = std::vector<std::string>();
                } else if (value[0].is_boolean()) {
                    std::vector<bool> array;
                    for (const auto& item : value) {
                        array.push_back(item.get<bool>());
                    }
                    section.values[key] = std::move(array);
                } else if (value[0].is_number_integer()) {
                    std::vector<int> array;
                    for (const auto& item : value) {
                        array.push_back(item.get<int>());
                    }
                    section.values[key] = std::move(array);
                } else if (value[0].is_number_float()) {
                    std::vector<double> array;
                    for (const auto& item : value) {
                        array.push_back(item.get<double>());
                    }
                    section.values[key] = std::move(array);
                } else {
                    std::vector<std::string> array;
                    for (const auto& item : value) {
                        array.push_back(item.get<std::string>());
                    }
                    section.values[key] = std::move(array);
                }
            } else if (value.is_boolean()) {
                section.values[key] = value.get<bool>();
            } else if (value.is_number_integer()) {
                section.values[key] = value.get<int>();
            } else if (value.is_number_float()) {
                section.values[key] = value.get<double>();
            } else if (value.is_string()) {
                section.values[key] = value.get<std::string>();
            }
        }
        return true;
    } catch (const std::exception& e) {
        LOG_ERROR("Error parsing JSON section: {}", e.what());
        return false;
    }
}

bool ConfigParser::validateSection(const ConfigSection& section, const ConfigSchema& schema,
                                 std::vector<std::string>& errors, const std::string& path) const {
    bool valid = true;
    std::unordered_map<std::string, bool> field_found;

    // Check required fields
    for (const auto& field : schema.fields) {
        field_found[field.name] = false;
        auto it = section.values.find(field.name);
        if (it == section.values.end()) {
            if (field.required) {
                errors.push_back(path + "." + field.name + ": Required field missing");
                valid = false;
            }
            continue;
        }
        field_found[field.name] = true;
        if (!validateValue(it->second, field, errors, path + "." + field.name)) {
            valid = false;
        }
    }

    // Check for unknown fields
    for (const auto& [key, _] : section.values) {
        if (!field_found[key]) {
            errors.push_back(path + "." + key + ": Unknown field");
            valid = false;
        }
    }

    // Validate subsections
    for (const auto& [subsection_name, subsection] : section.subsections) {
        auto schema_it = schema.subschemas.find(subsection_name);
        if (schema_it == schema.subschemas.end()) {
            errors.push_back(path + "." + subsection_name + ": Unknown subsection");
            valid = false;
            continue;
        }
        if (!validateSection(subsection, schema_it->second, errors, path + "." + subsection_name)) {
            valid = false;
        }
    }

    return valid;
}

bool ConfigParser::validateValue(const ConfigValue& value, const ConfigSchema::Field& field,
                               std::vector<std::string>& errors, const std::string& path) const {
    // Check type
    bool type_valid = false;
    std::visit([&](const auto& v) {
        using T = std::decay_t<decltype(v)>;
        if (field.type == "bool" && std::is_same_v<T, bool>) type_valid = true;
        else if (field.type == "int" && std::is_same_v<T, int>) type_valid = true;
        else if (field.type == "double" && std::is_same_v<T, double>) type_valid = true;
        else if (field.type == "string" && std::is_same_v<T, std::string>) type_valid = true;
        else if (field.type == "bool[]" && std::is_same_v<T, std::vector<bool>>) type_valid = true;
        else if (field.type == "int[]" && std::is_same_v<T, std::vector<int>>) type_valid = true;
        else if (field.type == "double[]" && std::is_same_v<T, std::vector<double>>) type_valid = true;
        else if (field.type == "string[]" && std::is_same_v<T, std::vector<std::string>>) type_valid = true;
    }, value);

    if (!type_valid) {
        errors.push_back(path + ": Invalid type, expected " + field.type);
        return false;
    }

    // Check allowed values
    if (!field.allowed_values.empty()) {
        bool value_allowed = false;
        for (const auto& allowed : field.allowed_values) {
            if (value == allowed) {
                value_allowed = true;
                break;
            }
        }
        if (!value_allowed) {
            errors.push_back(path + ": Value not in allowed values list");
            return false;
        }
    }

    // Check custom validator
    if (field.validator && !field.validator(value)) {
        errors.push_back(path + ": Failed custom validation");
        return false;
    }

    return true;
}

nlohmann::json ConfigParser::sectionToJson(const ConfigSection& section) const {
    nlohmann::json result;
    
    // Add values
    for (const auto& [key, value] : section.values) {
        std::visit([&](const auto& v) {
            result[key] = v;
        }, value);
    }

    // Add subsections
    for (const auto& [key, subsection] : section.subsections) {
        result[key] = sectionToJson(subsection);
    }

    return result;
}

} // namespace utils
} // namespace cogniware
