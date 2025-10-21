#ifndef MCP_FILESYSTEM_H
#define MCP_FILESYSTEM_H

#include "mcp/mcp_core.h"
#include <filesystem>
#include <fstream>
#include <vector>
#include <optional>

namespace cogniware {
namespace mcp {
namespace filesystem {

// File operations
enum class FileMode {
    READ,
    WRITE,
    APPEND,
    READ_WRITE
};

// File permissions
struct FilePermissions {
    bool owner_read;
    bool owner_write;
    bool owner_execute;
    bool group_read;
    bool group_write;
    bool group_execute;
    bool others_read;
    bool others_write;
    bool others_execute;
};

// File information
struct FileInfo {
    std::string path;
    std::string name;
    size_t size;
    bool is_directory;
    bool is_regular_file;
    bool is_symlink;
    std::chrono::system_clock::time_point last_modified;
    std::chrono::system_clock::time_point created;
    FilePermissions permissions;
    std::string mime_type;
};

// Directory entry
struct DirectoryEntry {
    std::string name;
    std::string path;
    bool is_directory;
    size_t size;
};

// Filesystem operation result
struct FilesystemResult {
    bool success;
    std::string message;
    std::string error_code;
    std::vector<uint8_t> data;
    std::vector<FileInfo> file_list;
};

// MCP Filesystem tools class
class MCPFilesystemTools {
public:
    MCPFilesystemTools();
    ~MCPFilesystemTools();
    
    // Register all filesystem tools to an MCP server
    static void registerAllTools(AdvancedMCPServer& server);
    
    // File operations
    static FilesystemResult readFile(const std::string& path);
    static FilesystemResult writeFile(const std::string& path, 
                                     const std::vector<uint8_t>& data,
                                     FileMode mode = FileMode::WRITE);
    static FilesystemResult writeFile(const std::string& path,
                                     const std::string& content,
                                     FileMode mode = FileMode::WRITE);
    static FilesystemResult deleteFile(const std::string& path);
    static FilesystemResult copyFile(const std::string& source, 
                                    const std::string& destination);
    static FilesystemResult moveFile(const std::string& source,
                                    const std::string& destination);
    static FilesystemResult getFileInfo(const std::string& path);
    
    // Directory operations
    static FilesystemResult createDirectory(const std::string& path,
                                           bool recursive = false);
    static FilesystemResult deleteDirectory(const std::string& path,
                                           bool recursive = false);
    static FilesystemResult listDirectory(const std::string& path,
                                         bool recursive = false);
    static FilesystemResult changeDirectory(const std::string& path);
    static std::string getCurrentDirectory();
    
    // Path operations
    static bool exists(const std::string& path);
    static bool isDirectory(const std::string& path);
    static bool isFile(const std::string& path);
    static std::string absolutePath(const std::string& path);
    static std::string relativePath(const std::string& path,
                                    const std::string& base);
    static std::string joinPaths(const std::vector<std::string>& paths);
    static std::string getParentPath(const std::string& path);
    static std::string getFilename(const std::string& path);
    static std::string getExtension(const std::string& path);
    
    // Search operations
    static FilesystemResult findFiles(const std::string& directory,
                                     const std::string& pattern,
                                     bool recursive = false);
    static FilesystemResult searchInFiles(const std::string& directory,
                                         const std::string& search_text,
                                         bool recursive = false);
    
    // Permission operations
    static FilesystemResult setPermissions(const std::string& path,
                                          const FilePermissions& permissions);
    static FilePermissions getPermissions(const std::string& path);
    
    // Utility operations
    static size_t getFileSize(const std::string& path);
    static std::string getMimeType(const std::string& path);
    static FilesystemResult createTempFile(const std::string& prefix = "temp");
    static FilesystemResult createTempDirectory(const std::string& prefix = "temp");

private:
    static std::string mimeTypeFromExtension(const std::string& extension);
    static bool matchesPattern(const std::string& filename,
                              const std::string& pattern);
};

// Filesystem watcher for monitoring changes
class FilesystemWatcher {
public:
    enum class EventType {
        CREATED,
        MODIFIED,
        DELETED,
        RENAMED,
        MOVED
    };
    
    struct WatchEvent {
        EventType type;
        std::string path;
        std::string old_path;  // For renamed/moved events
        std::chrono::system_clock::time_point timestamp;
    };
    
    using WatchCallback = std::function<void(const WatchEvent&)>;
    
    FilesystemWatcher();
    ~FilesystemWatcher();
    
    bool addWatch(const std::string& path, bool recursive = false);
    bool removeWatch(const std::string& path);
    void setCallback(WatchCallback callback);
    void start();
    void stop();
    bool isRunning() const;
    
    std::vector<WatchEvent> getEvents(size_t max_events = 100);

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

// Filesystem sandbox for security
class FilesystemSandbox {
public:
    FilesystemSandbox();
    ~FilesystemSandbox();
    
    // Configure sandbox
    void addAllowedPath(const std::string& path);
    void removeAllowedPath(const std::string& path);
    void setAllowedPaths(const std::vector<std::string>& paths);
    std::vector<std::string> getAllowedPaths() const;
    
    // Permission control
    void setReadOnly(bool read_only);
    bool isReadOnly() const;
    
    void setMaxFileSize(size_t max_size);
    size_t getMaxFileSize() const;
    
    void setMaxTotalSize(size_t max_size);
    size_t getMaxTotalSize() const;
    
    // Validation
    bool isPathAllowed(const std::string& path) const;
    bool canRead(const std::string& path) const;
    bool canWrite(const std::string& path) const;
    bool canExecute(const std::string& path) const;
    
    // Statistics
    size_t getCurrentTotalSize() const;
    size_t getFileCount() const;

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

} // namespace filesystem
} // namespace mcp
} // namespace cogniware

#endif // MCP_FILESYSTEM_H

