#include "mcp/mcp_filesystem.h"
#include <algorithm>
#include <regex>
#include <sstream>
#include <ctime>

namespace cogniware {
namespace mcp {
namespace filesystem {

// MCPFilesystemTools Implementation
MCPFilesystemTools::MCPFilesystemTools() = default;
MCPFilesystemTools::~MCPFilesystemTools() = default;

void MCPFilesystemTools::registerAllTools(AdvancedMCPServer& server) {
    // Read file tool
    MCPTool read_file_tool;
    read_file_tool.name = "fs_read_file";
    read_file_tool.description = "Read contents of a file";
    
    MCPParameter path_param;
    path_param.name = "path";
    path_param.type = ParameterType::STRING;
    path_param.description = "File path to read";
    path_param.required = true;
    read_file_tool.parameters.push_back(path_param);
    
    read_file_tool.handler = [](const std::unordered_map<std::string, std::string>& params) {
        auto result = readFile(params.at("path"));
        if (result.success) {
            return std::string(result.data.begin(), result.data.end());
        }
        return "Error: " + result.message;
    };
    
    server.registerTool(read_file_tool);
    
    // Write file tool
    MCPTool write_file_tool;
    write_file_tool.name = "fs_write_file";
    write_file_tool.description = "Write content to a file";
    
    path_param.name = "path";
    write_file_tool.parameters.push_back(path_param);
    
    MCPParameter content_param;
    content_param.name = "content";
    content_param.type = ParameterType::STRING;
    content_param.description = "Content to write";
    content_param.required = true;
    write_file_tool.parameters.push_back(content_param);
    
    write_file_tool.handler = [](const std::unordered_map<std::string, std::string>& params) {
        auto result = writeFile(params.at("path"), params.at("content"));
        return result.success ? "File written successfully" : "Error: " + result.message;
    };
    
    server.registerTool(write_file_tool);
    
    // List directory tool
    MCPTool list_dir_tool;
    list_dir_tool.name = "fs_list_directory";
    list_dir_tool.description = "List contents of a directory";
    
    path_param.name = "path";
    list_dir_tool.parameters.push_back(path_param);
    
    MCPParameter recursive_param;
    recursive_param.name = "recursive";
    recursive_param.type = ParameterType::BOOLEAN;
    recursive_param.description = "List recursively";
    recursive_param.required = false;
    list_dir_tool.parameters.push_back(recursive_param);
    
    list_dir_tool.handler = [](const std::unordered_map<std::string, std::string>& params) {
        bool recursive = params.count("recursive") && params.at("recursive") == "true";
        auto result = listDirectory(params.at("path"), recursive);
        
        if (result.success) {
            std::stringstream ss;
            for (const auto& file : result.file_list) {
                ss << file.name << " (" << file.size << " bytes)\n";
            }
            return ss.str();
        }
        return "Error: " + result.message;
    };
    
    server.registerTool(list_dir_tool);
    
    // Create directory tool
    MCPTool create_dir_tool;
    create_dir_tool.name = "fs_create_directory";
    create_dir_tool.description = "Create a new directory";
    
    path_param.name = "path";
    create_dir_tool.parameters.push_back(path_param);
    
    create_dir_tool.handler = [](const std::unordered_map<std::string, std::string>& params) {
        auto result = createDirectory(params.at("path"), true);
        return result.success ? "Directory created" : "Error: " + result.message;
    };
    
    server.registerTool(create_dir_tool);
    
    // Delete file tool
    MCPTool delete_file_tool;
    delete_file_tool.name = "fs_delete_file";
    delete_file_tool.description = "Delete a file";
    
    path_param.name = "path";
    delete_file_tool.parameters.push_back(path_param);
    
    delete_file_tool.handler = [](const std::unordered_map<std::string, std::string>& params) {
        auto result = deleteFile(params.at("path"));
        return result.success ? "File deleted" : "Error: " + result.message;
    };
    
    server.registerTool(delete_file_tool);
    
    // Get file info tool
    MCPTool file_info_tool;
    file_info_tool.name = "fs_get_file_info";
    file_info_tool.description = "Get information about a file";
    
    path_param.name = "path";
    file_info_tool.parameters.push_back(path_param);
    
    file_info_tool.handler = [](const std::unordered_map<std::string, std::string>& params) {
        auto result = getFileInfo(params.at("path"));
        
        if (result.success && !result.file_list.empty()) {
            const auto& info = result.file_list[0];
            std::stringstream ss;
            ss << "Name: " << info.name << "\n"
               << "Size: " << info.size << " bytes\n"
               << "Type: " << (info.is_directory ? "Directory" : "File") << "\n"
               << "MIME: " << info.mime_type << "\n";
            return ss.str();
        }
        return "Error: " + result.message;
    };
    
    server.registerTool(file_info_tool);
    
    // Find files tool
    MCPTool find_files_tool;
    find_files_tool.name = "fs_find_files";
    find_files_tool.description = "Find files matching a pattern";
    
    path_param.name = "directory";
    find_files_tool.parameters.push_back(path_param);
    
    MCPParameter pattern_param;
    pattern_param.name = "pattern";
    pattern_param.type = ParameterType::STRING;
    pattern_param.description = "File pattern (e.g., *.txt)";
    pattern_param.required = true;
    find_files_tool.parameters.push_back(pattern_param);
    
    find_files_tool.handler = [](const std::unordered_map<std::string, std::string>& params) {
        auto result = findFiles(params.at("directory"), params.at("pattern"), true);
        
        if (result.success) {
            std::stringstream ss;
            ss << "Found " << result.file_list.size() << " files:\n";
            for (const auto& file : result.file_list) {
                ss << file.path << "\n";
            }
            return ss.str();
        }
        return "Error: " + result.message;
    };
    
    server.registerTool(find_files_tool);
}

FilesystemResult MCPFilesystemTools::readFile(const std::string& path) {
    FilesystemResult result;
    result.success = false;
    
    try {
        if (!std::filesystem::exists(path)) {
            result.message = "File does not exist";
            result.error_code = "FILE_NOT_FOUND";
            return result;
        }
        
        std::ifstream file(path, std::ios::binary);
        if (!file.is_open()) {
            result.message = "Failed to open file";
            result.error_code = "OPEN_FAILED";
            return result;
        }
        
        file.seekg(0, std::ios::end);
        size_t file_size = file.tellg();
        file.seekg(0, std::ios::beg);
        
        result.data.resize(file_size);
        file.read(reinterpret_cast<char*>(result.data.data()), file_size);
        
        result.success = true;
        result.message = "File read successfully";
        
    } catch (const std::exception& e) {
        result.message = e.what();
        result.error_code = "EXCEPTION";
    }
    
    return result;
}

FilesystemResult MCPFilesystemTools::writeFile(
    const std::string& path,
    const std::vector<uint8_t>& data,
    FileMode mode) {
    
    FilesystemResult result;
    result.success = false;
    
    try {
        std::ios::openmode open_mode = std::ios::binary;
        
        switch (mode) {
            case FileMode::WRITE:
                open_mode |= std::ios::trunc;
                break;
            case FileMode::APPEND:
                open_mode |= std::ios::app;
                break;
            case FileMode::READ_WRITE:
                open_mode |= std::ios::in | std::ios::out;
                break;
            default:
                open_mode |= std::ios::trunc;
        }
        
        std::ofstream file(path, open_mode);
        if (!file.is_open()) {
            result.message = "Failed to open file for writing";
            result.error_code = "OPEN_FAILED";
            return result;
        }
        
        file.write(reinterpret_cast<const char*>(data.data()), data.size());
        
        result.success = true;
        result.message = "File written successfully";
        
    } catch (const std::exception& e) {
        result.message = e.what();
        result.error_code = "EXCEPTION";
    }
    
    return result;
}

FilesystemResult MCPFilesystemTools::writeFile(
    const std::string& path,
    const std::string& content,
    FileMode mode) {
    
    std::vector<uint8_t> data(content.begin(), content.end());
    return writeFile(path, data, mode);
}

FilesystemResult MCPFilesystemTools::deleteFile(const std::string& path) {
    FilesystemResult result;
    result.success = false;
    
    try {
        if (!std::filesystem::exists(path)) {
            result.message = "File does not exist";
            result.error_code = "FILE_NOT_FOUND";
            return result;
        }
        
        std::filesystem::remove(path);
        
        result.success = true;
        result.message = "File deleted successfully";
        
    } catch (const std::exception& e) {
        result.message = e.what();
        result.error_code = "EXCEPTION";
    }
    
    return result;
}

FilesystemResult MCPFilesystemTools::copyFile(
    const std::string& source,
    const std::string& destination) {
    
    FilesystemResult result;
    result.success = false;
    
    try {
        if (!std::filesystem::exists(source)) {
            result.message = "Source file does not exist";
            result.error_code = "FILE_NOT_FOUND";
            return result;
        }
        
        std::filesystem::copy(source, destination,
            std::filesystem::copy_options::overwrite_existing);
        
        result.success = true;
        result.message = "File copied successfully";
        
    } catch (const std::exception& e) {
        result.message = e.what();
        result.error_code = "EXCEPTION";
    }
    
    return result;
}

FilesystemResult MCPFilesystemTools::moveFile(
    const std::string& source,
    const std::string& destination) {
    
    FilesystemResult result;
    result.success = false;
    
    try {
        if (!std::filesystem::exists(source)) {
            result.message = "Source file does not exist";
            result.error_code = "FILE_NOT_FOUND";
            return result;
        }
        
        std::filesystem::rename(source, destination);
        
        result.success = true;
        result.message = "File moved successfully";
        
    } catch (const std::exception& e) {
        result.message = e.what();
        result.error_code = "EXCEPTION";
    }
    
    return result;
}

FilesystemResult MCPFilesystemTools::getFileInfo(const std::string& path) {
    FilesystemResult result;
    result.success = false;
    
    try {
        if (!std::filesystem::exists(path)) {
            result.message = "Path does not exist";
            result.error_code = "FILE_NOT_FOUND";
            return result;
        }
        
        FileInfo info;
        info.path = std::filesystem::absolute(path).string();
        info.name = std::filesystem::path(path).filename().string();
        info.is_directory = std::filesystem::is_directory(path);
        info.is_regular_file = std::filesystem::is_regular_file(path);
        info.is_symlink = std::filesystem::is_symlink(path);
        
        if (info.is_regular_file) {
            info.size = std::filesystem::file_size(path);
        } else {
            info.size = 0;
        }
        
        auto ftime = std::filesystem::last_write_time(path);
        auto sctp = std::chrono::time_point_cast<std::chrono::system_clock::duration>(
            ftime - std::filesystem::file_time_type::clock::now() + 
            std::chrono::system_clock::now());
        info.last_modified = sctp;
        
        info.mime_type = getMimeType(path);
        
        result.file_list.push_back(info);
        result.success = true;
        result.message = "File info retrieved";
        
    } catch (const std::exception& e) {
        result.message = e.what();
        result.error_code = "EXCEPTION";
    }
    
    return result;
}

FilesystemResult MCPFilesystemTools::createDirectory(
    const std::string& path,
    bool recursive) {
    
    FilesystemResult result;
    result.success = false;
    
    try {
        if (recursive) {
            std::filesystem::create_directories(path);
        } else {
            std::filesystem::create_directory(path);
        }
        
        result.success = true;
        result.message = "Directory created successfully";
        
    } catch (const std::exception& e) {
        result.message = e.what();
        result.error_code = "EXCEPTION";
    }
    
    return result;
}

FilesystemResult MCPFilesystemTools::deleteDirectory(
    const std::string& path,
    bool recursive) {
    
    FilesystemResult result;
    result.success = false;
    
    try {
        if (!std::filesystem::exists(path)) {
            result.message = "Directory does not exist";
            result.error_code = "DIR_NOT_FOUND";
            return result;
        }
        
        if (recursive) {
            std::filesystem::remove_all(path);
        } else {
            std::filesystem::remove(path);
        }
        
        result.success = true;
        result.message = "Directory deleted successfully";
        
    } catch (const std::exception& e) {
        result.message = e.what();
        result.error_code = "EXCEPTION";
    }
    
    return result;
}

FilesystemResult MCPFilesystemTools::listDirectory(
    const std::string& path,
    bool recursive) {
    
    FilesystemResult result;
    result.success = false;
    
    try {
        if (!std::filesystem::exists(path)) {
            result.message = "Directory does not exist";
            result.error_code = "DIR_NOT_FOUND";
            return result;
        }
        
        if (!std::filesystem::is_directory(path)) {
            result.message = "Path is not a directory";
            result.error_code = "NOT_A_DIRECTORY";
            return result;
        }
        
        if (recursive) {
            for (const auto& entry : std::filesystem::recursive_directory_iterator(path)) {
                FileInfo info;
                info.path = entry.path().string();
                info.name = entry.path().filename().string();
                info.is_directory = entry.is_directory();
                info.is_regular_file = entry.is_regular_file();
                
                if (info.is_regular_file) {
                    info.size = entry.file_size();
                }
                
                result.file_list.push_back(info);
            }
        } else {
            for (const auto& entry : std::filesystem::directory_iterator(path)) {
                FileInfo info;
                info.path = entry.path().string();
                info.name = entry.path().filename().string();
                info.is_directory = entry.is_directory();
                info.is_regular_file = entry.is_regular_file();
                
                if (info.is_regular_file) {
                    info.size = entry.file_size();
                }
                
                result.file_list.push_back(info);
            }
        }
        
        result.success = true;
        result.message = "Directory listed successfully";
        
    } catch (const std::exception& e) {
        result.message = e.what();
        result.error_code = "EXCEPTION";
    }
    
    return result;
}

FilesystemResult MCPFilesystemTools::changeDirectory(const std::string& path) {
    FilesystemResult result;
    result.success = false;
    
    try {
        std::filesystem::current_path(path);
        result.success = true;
        result.message = "Changed directory";
    } catch (const std::exception& e) {
        result.message = e.what();
        result.error_code = "EXCEPTION";
    }
    
    return result;
}

std::string MCPFilesystemTools::getCurrentDirectory() {
    return std::filesystem::current_path().string();
}

bool MCPFilesystemTools::exists(const std::string& path) {
    return std::filesystem::exists(path);
}

bool MCPFilesystemTools::isDirectory(const std::string& path) {
    return std::filesystem::is_directory(path);
}

bool MCPFilesystemTools::isFile(const std::string& path) {
    return std::filesystem::is_regular_file(path);
}

std::string MCPFilesystemTools::absolutePath(const std::string& path) {
    return std::filesystem::absolute(path).string();
}

std::string MCPFilesystemTools::relativePath(
    const std::string& path,
    const std::string& base) {
    
    return std::filesystem::relative(path, base).string();
}

std::string MCPFilesystemTools::joinPaths(const std::vector<std::string>& paths) {
    std::filesystem::path result;
    for (const auto& p : paths) {
        result /= p;
    }
    return result.string();
}

std::string MCPFilesystemTools::getParentPath(const std::string& path) {
    return std::filesystem::path(path).parent_path().string();
}

std::string MCPFilesystemTools::getFilename(const std::string& path) {
    return std::filesystem::path(path).filename().string();
}

std::string MCPFilesystemTools::getExtension(const std::string& path) {
    return std::filesystem::path(path).extension().string();
}

FilesystemResult MCPFilesystemTools::findFiles(
    const std::string& directory,
    const std::string& pattern,
    bool recursive) {
    
    FilesystemResult result;
    result.success = false;
    
    try {
        if (!std::filesystem::exists(directory)) {
            result.message = "Directory does not exist";
            result.error_code = "DIR_NOT_FOUND";
            return result;
        }
        
        if (recursive) {
            for (const auto& entry : std::filesystem::recursive_directory_iterator(directory)) {
                if (entry.is_regular_file()) {
                    std::string filename = entry.path().filename().string();
                    if (matchesPattern(filename, pattern)) {
                        FileInfo info;
                        info.path = entry.path().string();
                        info.name = filename;
                        info.size = entry.file_size();
                        info.is_regular_file = true;
                        result.file_list.push_back(info);
                    }
                }
            }
        } else {
            for (const auto& entry : std::filesystem::directory_iterator(directory)) {
                if (entry.is_regular_file()) {
                    std::string filename = entry.path().filename().string();
                    if (matchesPattern(filename, pattern)) {
                        FileInfo info;
                        info.path = entry.path().string();
                        info.name = filename;
                        info.size = entry.file_size();
                        info.is_regular_file = true;
                        result.file_list.push_back(info);
                    }
                }
            }
        }
        
        result.success = true;
        result.message = "Files found: " + std::to_string(result.file_list.size());
        
    } catch (const std::exception& e) {
        result.message = e.what();
        result.error_code = "EXCEPTION";
    }
    
    return result;
}

FilesystemResult MCPFilesystemTools::searchInFiles(
    const std::string& directory,
    const std::string& search_text,
    bool recursive) {
    
    FilesystemResult result;
    result.success = false;
    
    try {
        auto file_list = listDirectory(directory, recursive);
        
        for (const auto& file_info : file_list.file_list) {
            if (file_info.is_regular_file) {
                auto read_result = readFile(file_info.path);
                if (read_result.success) {
                    std::string content(read_result.data.begin(), read_result.data.end());
                    if (content.find(search_text) != std::string::npos) {
                        result.file_list.push_back(file_info);
                    }
                }
            }
        }
        
        result.success = true;
        result.message = "Search completed";
        
    } catch (const std::exception& e) {
        result.message = e.what();
        result.error_code = "EXCEPTION";
    }
    
    return result;
}

size_t MCPFilesystemTools::getFileSize(const std::string& path) {
    try {
        return std::filesystem::file_size(path);
    } catch (...) {
        return 0;
    }
}

std::string MCPFilesystemTools::getMimeType(const std::string& path) {
    std::string extension = getExtension(path);
    return mimeTypeFromExtension(extension);
}

FilesystemResult MCPFilesystemTools::createTempFile(const std::string& prefix) {
    FilesystemResult result;
    
    try {
        auto temp_path = std::filesystem::temp_directory_path() / 
                        (prefix + "_" + std::to_string(std::time(nullptr)));
        
        std::ofstream file(temp_path);
        file.close();
        
        FileInfo info;
        info.path = temp_path.string();
        info.name = temp_path.filename().string();
        result.file_list.push_back(info);
        
        result.success = true;
        result.message = "Temp file created: " + temp_path.string();
        
    } catch (const std::exception& e) {
        result.message = e.what();
        result.error_code = "EXCEPTION";
    }
    
    return result;
}

FilesystemResult MCPFilesystemTools::createTempDirectory(const std::string& prefix) {
    FilesystemResult result;
    
    try {
        auto temp_path = std::filesystem::temp_directory_path() /
                        (prefix + "_" + std::to_string(std::time(nullptr)));
        
        std::filesystem::create_directory(temp_path);
        
        FileInfo info;
        info.path = temp_path.string();
        info.name = temp_path.filename().string();
        info.is_directory = true;
        result.file_list.push_back(info);
        
        result.success = true;
        result.message = "Temp directory created: " + temp_path.string();
        
    } catch (const std::exception& e) {
        result.message = e.what();
        result.error_code = "EXCEPTION";
    }
    
    return result;
}

std::string MCPFilesystemTools::mimeTypeFromExtension(const std::string& extension) {
    static const std::unordered_map<std::string, std::string> mime_types = {
        {".txt", "text/plain"},
        {".html", "text/html"},
        {".css", "text/css"},
        {".js", "application/javascript"},
        {".json", "application/json"},
        {".xml", "application/xml"},
        {".pdf", "application/pdf"},
        {".zip", "application/zip"},
        {".jpg", "image/jpeg"},
        {".jpeg", "image/jpeg"},
        {".png", "image/png"},
        {".gif", "image/gif"},
        {".svg", "image/svg+xml"},
        {".mp3", "audio/mpeg"},
        {".wav", "audio/wav"},
        {".mp4", "video/mp4"},
        {".avi", "video/x-msvideo"}
    };
    
    auto it = mime_types.find(extension);
    return (it != mime_types.end()) ? it->second : "application/octet-stream";
}

bool MCPFilesystemTools::matchesPattern(
    const std::string& filename,
    const std::string& pattern) {
    
    // Convert wildcard pattern to regex
    std::string regex_pattern = pattern;
    regex_pattern = std::regex_replace(regex_pattern, std::regex("\\."), "\\.");
    regex_pattern = std::regex_replace(regex_pattern, std::regex("\\*"), ".*");
    regex_pattern = std::regex_replace(regex_pattern, std::regex("\\?"), ".");
    
    std::regex re(regex_pattern);
    return std::regex_match(filename, re);
}

// FilesystemWatcher stub implementation
class FilesystemWatcher::Impl {
public:
    bool running = false;
    WatchCallback callback;
    std::vector<WatchEvent> events;
};

FilesystemWatcher::FilesystemWatcher()
    : pImpl(std::make_unique<Impl>()) {}

FilesystemWatcher::~FilesystemWatcher() {
    stop();
}

bool FilesystemWatcher::addWatch(const std::string& path, bool recursive) {
    // Implementation would use inotify on Linux, FSEvents on macOS, etc.
    return true;
}

bool FilesystemWatcher::removeWatch(const std::string& path) {
    return true;
}

void FilesystemWatcher::setCallback(WatchCallback callback) {
    pImpl->callback = callback;
}

void FilesystemWatcher::start() {
    pImpl->running = true;
}

void FilesystemWatcher::stop() {
    pImpl->running = false;
}

bool FilesystemWatcher::isRunning() const {
    return pImpl->running;
}

std::vector<FilesystemWatcher::WatchEvent> FilesystemWatcher::getEvents(size_t max_events) {
    std::vector<WatchEvent> events;
    size_t count = std::min(max_events, pImpl->events.size());
    events.assign(pImpl->events.begin(), pImpl->events.begin() + count);
    return events;
}

// FilesystemSandbox implementation
class FilesystemSandbox::Impl {
public:
    std::vector<std::string> allowed_paths;
    bool read_only = false;
    size_t max_file_size = 100 * 1024 * 1024;  // 100MB
    size_t max_total_size = 1024 * 1024 * 1024;  // 1GB
    mutable std::mutex mutex;
};

FilesystemSandbox::FilesystemSandbox()
    : pImpl(std::make_unique<Impl>()) {}

FilesystemSandbox::~FilesystemSandbox() = default;

void FilesystemSandbox::addAllowedPath(const std::string& path) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    pImpl->allowed_paths.push_back(std::filesystem::absolute(path).string());
}

void FilesystemSandbox::removeAllowedPath(const std::string& path) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    auto abs_path = std::filesystem::absolute(path).string();
    pImpl->allowed_paths.erase(
        std::remove(pImpl->allowed_paths.begin(), pImpl->allowed_paths.end(), abs_path),
        pImpl->allowed_paths.end());
}

void FilesystemSandbox::setAllowedPaths(const std::vector<std::string>& paths) {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    pImpl->allowed_paths.clear();
    for (const auto& path : paths) {
        pImpl->allowed_paths.push_back(std::filesystem::absolute(path).string());
    }
}

std::vector<std::string> FilesystemSandbox::getAllowedPaths() const {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    return pImpl->allowed_paths;
}

void FilesystemSandbox::setReadOnly(bool read_only) {
    pImpl->read_only = read_only;
}

bool FilesystemSandbox::isReadOnly() const {
    return pImpl->read_only;
}

void FilesystemSandbox::setMaxFileSize(size_t max_size) {
    pImpl->max_file_size = max_size;
}

size_t FilesystemSandbox::getMaxFileSize() const {
    return pImpl->max_file_size;
}

void FilesystemSandbox::setMaxTotalSize(size_t max_size) {
    pImpl->max_total_size = max_size;
}

size_t FilesystemSandbox::getMaxTotalSize() const {
    return pImpl->max_total_size;
}

bool FilesystemSandbox::isPathAllowed(const std::string& path) const {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    auto abs_path = std::filesystem::absolute(path).string();
    
    for (const auto& allowed : pImpl->allowed_paths) {
        if (abs_path.find(allowed) == 0) {
            return true;
        }
    }
    
    return false;
}

bool FilesystemSandbox::canRead(const std::string& path) const {
    return isPathAllowed(path);
}

bool FilesystemSandbox::canWrite(const std::string& path) const {
    return !pImpl->read_only && isPathAllowed(path);
}

bool FilesystemSandbox::canExecute(const std::string& path) const {
    return false;  // Execution disabled by default in sandbox
}

size_t FilesystemSandbox::getCurrentTotalSize() const {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    size_t total = 0;
    for (const auto& allowed_path : pImpl->allowed_paths) {
        if (std::filesystem::exists(allowed_path)) {
            if (std::filesystem::is_directory(allowed_path)) {
                for (const auto& entry : std::filesystem::recursive_directory_iterator(allowed_path)) {
                    if (entry.is_regular_file()) {
                        total += entry.file_size();
                    }
                }
            } else {
                total += std::filesystem::file_size(allowed_path);
            }
        }
    }
    
    return total;
}

size_t FilesystemSandbox::getFileCount() const {
    std::lock_guard<std::mutex> lock(pImpl->mutex);
    
    size_t count = 0;
    for (const auto& allowed_path : pImpl->allowed_paths) {
        if (std::filesystem::exists(allowed_path)) {
            if (std::filesystem::is_directory(allowed_path)) {
                for (const auto& entry : std::filesystem::recursive_directory_iterator(allowed_path)) {
                    if (entry.is_regular_file()) {
                        ++count;
                    }
                }
            } else {
                ++count;
            }
        }
    }
    
    return count;
}

} // namespace filesystem
} // namespace mcp
} // namespace cogniware

