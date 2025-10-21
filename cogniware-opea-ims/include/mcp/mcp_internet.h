#ifndef MCP_INTERNET_H
#define MCP_INTERNET_H

#include "mcp/mcp_core.h"
#include <string>
#include <vector>
#include <unordered_map>
#include <memory>
#include <chrono>
#include <functional>

namespace cogniware {
namespace mcp {
namespace internet {

// HTTP methods
enum class HttpMethod {
    GET,
    POST,
    PUT,
    DELETE,
    PATCH,
    HEAD,
    OPTIONS
};

// HTTP request
struct HttpRequest {
    std::string url;
    HttpMethod method;
    std::unordered_map<std::string, std::string> headers;
    std::string body;
    std::chrono::milliseconds timeout;
    bool follow_redirects;
    int max_redirects;
    bool verify_ssl;
    std::string proxy;
    std::string user_agent;
};

// HTTP response
struct HttpResponse {
    int status_code;
    std::string status_message;
    std::unordered_map<std::string, std::string> headers;
    std::vector<uint8_t> body;
    std::string body_text;
    std::chrono::milliseconds response_time;
    size_t content_length;
    std::string content_type;
    bool success;
    std::string error_message;
};

// Web scraping configuration
struct ScrapingConfig {
    std::string url;
    std::vector<std::string> css_selectors;
    std::vector<std::string> xpath_selectors;
    bool extract_links;
    bool extract_images;
    bool extract_text;
    bool follow_links;
    int max_depth;
    std::vector<std::string> allowed_domains;
    std::chrono::milliseconds timeout;
};

// Scraped data
struct ScrapedData {
    std::string url;
    std::string title;
    std::vector<std::string> text_content;
    std::vector<std::string> links;
    std::vector<std::string> images;
    std::unordered_map<std::string, std::vector<std::string>> selector_results;
    bool success;
    std::string error_message;
};

// WebSocket connection
struct WebSocketConfig {
    std::string url;
    std::unordered_map<std::string, std::string> headers;
    std::chrono::milliseconds ping_interval;
    std::chrono::milliseconds timeout;
    bool auto_reconnect;
    int max_reconnect_attempts;
};

// WebSocket message
struct WebSocketMessage {
    enum class Type {
        TEXT,
        BINARY,
        PING,
        PONG,
        CLOSE
    };
    
    Type type;
    std::vector<uint8_t> data;
    std::string text;
    std::chrono::system_clock::time_point timestamp;
};

// MCP Internet tools
class MCPInternetTools {
public:
    MCPInternetTools();
    ~MCPInternetTools();
    
    // Register all internet tools to an MCP server
    static void registerAllTools(AdvancedMCPServer& server);
    
    // HTTP operations
    static HttpResponse httpGet(const std::string& url,
                               const std::unordered_map<std::string, std::string>& headers = {});
    
    static HttpResponse httpPost(const std::string& url,
                                const std::string& body,
                                const std::unordered_map<std::string, std::string>& headers = {});
    
    static HttpResponse httpPut(const std::string& url,
                               const std::string& body,
                               const std::unordered_map<std::string, std::string>& headers = {});
    
    static HttpResponse httpDelete(const std::string& url,
                                  const std::unordered_map<std::string, std::string>& headers = {});
    
    static HttpResponse httpRequest(const HttpRequest& request);
    
    // API operations
    static HttpResponse callRestApi(const std::string& endpoint,
                                   HttpMethod method,
                                   const std::string& json_body = "",
                                   const std::string& api_key = "");
    
    static std::string parseJsonResponse(const HttpResponse& response);
    
    // Web scraping
    static ScrapedData scrapeWebpage(const std::string& url,
                                    const std::vector<std::string>& selectors = {});
    
    static ScrapedData scrapeWithConfig(const ScrapingConfig& config);
    
    static std::vector<std::string> extractLinks(const std::string& html,
                                                 const std::string& base_url = "");
    
    static std::vector<std::string> extractImages(const std::string& html,
                                                  const std::string& base_url = "");
    
    static std::string extractText(const std::string& html);
    
    static std::vector<std::string> selectElements(const std::string& html,
                                                   const std::string& css_selector);
    
    // Download operations
    static bool downloadFile(const std::string& url,
                           const std::string& destination);
    
    static std::vector<uint8_t> downloadToMemory(const std::string& url);
    
    // URL utilities
    static std::string urlEncode(const std::string& input);
    static std::string urlDecode(const std::string& input);
    static std::string buildQueryString(const std::unordered_map<std::string, std::string>& params);
    static std::unordered_map<std::string, std::string> parseQueryString(const std::string& query);
    static std::string joinUrl(const std::string& base, const std::string& relative);
    
    // Network utilities
    static bool isUrlValid(const std::string& url);
    static std::string getDomain(const std::string& url);
    static int getPort(const std::string& url);
    static std::string getProtocol(const std::string& url);

private:
    static std::string methodToString(HttpMethod method);
    static std::string removeHtmlTags(const std::string& html);
};

// HTTP client with connection pooling
class HttpClient {
public:
    HttpClient();
    ~HttpClient();
    
    // Configuration
    void setTimeout(std::chrono::milliseconds timeout);
    void setUserAgent(const std::string& user_agent);
    void setMaxConnections(size_t max_connections);
    void setFollowRedirects(bool follow);
    void setVerifySSL(bool verify);
    void setProxy(const std::string& proxy);
    
    // Add default headers
    void addDefaultHeader(const std::string& key, const std::string& value);
    void removeDefaultHeader(const std::string& key);
    void clearDefaultHeaders();
    
    // Request methods
    HttpResponse get(const std::string& url);
    HttpResponse post(const std::string& url, const std::string& body);
    HttpResponse put(const std::string& url, const std::string& body);
    HttpResponse del(const std::string& url);
    HttpResponse request(const HttpRequest& request);
    
    // Batch operations
    std::vector<HttpResponse> batchGet(const std::vector<std::string>& urls);
    
    // Statistics
    struct ClientStats {
        size_t total_requests;
        size_t successful_requests;
        size_t failed_requests;
        double avg_response_time_ms;
        size_t bytes_sent;
        size_t bytes_received;
    };
    
    ClientStats getStats() const;
    void resetStats();

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

// Web scraper with caching and rate limiting
class WebScraper {
public:
    WebScraper();
    ~WebScraper();
    
    // Configuration
    void setRateLimit(size_t requests_per_second);
    void setUserAgent(const std::string& user_agent);
    void enableCaching(bool enable);
    void setCacheTimeout(std::chrono::seconds timeout);
    void setMaxDepth(int depth);
    void addAllowedDomain(const std::string& domain);
    void addBlockedDomain(const std::string& domain);
    
    // Scraping operations
    ScrapedData scrape(const std::string& url);
    ScrapedData scrapeWithSelectors(const std::string& url,
                                   const std::vector<std::string>& selectors);
    
    std::vector<ScrapedData> crawl(const std::string& start_url,
                                   int max_pages = 100);
    
    // Content extraction
    std::vector<std::string> extractLinks(const std::string& url);
    std::vector<std::string> extractImages(const std::string& url);
    std::string extractMainContent(const std::string& url);
    
    // Statistics
    struct ScraperStats {
        size_t pages_scraped;
        size_t links_extracted;
        size_t images_extracted;
        size_t cache_hits;
        size_t cache_misses;
        double avg_scrape_time_ms;
    };
    
    ScraperStats getStats() const;
    void resetStats();

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

// WebSocket client
class WebSocketClient {
public:
    WebSocketClient();
    ~WebSocketClient();
    
    using MessageCallback = std::function<void(const WebSocketMessage&)>;
    using ErrorCallback = std::function<void(const std::string&)>;
    using ConnectionCallback = std::function<void(bool)>;
    
    // Connection management
    bool connect(const std::string& url);
    bool disconnect();
    bool isConnected() const;
    
    // Callbacks
    void onMessage(MessageCallback callback);
    void onError(ErrorCallback callback);
    void onConnection(ConnectionCallback callback);
    
    // Send operations
    bool sendText(const std::string& text);
    bool sendBinary(const std::vector<uint8_t>& data);
    bool sendPing();
    
    // Configuration
    void setAutoReconnect(bool enable);
    void setPingInterval(std::chrono::milliseconds interval);
    
    // Statistics
    struct WebSocketStats {
        size_t messages_sent;
        size_t messages_received;
        size_t bytes_sent;
        size_t bytes_received;
        size_t reconnect_count;
        std::chrono::milliseconds uptime;
    };
    
    WebSocketStats getStats() const;

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

// Rate limiter for API calls
class RateLimiter {
public:
    RateLimiter(size_t requests_per_second);
    ~RateLimiter();
    
    bool allowRequest();
    void waitForSlot();
    size_t getAvailableSlots() const;
    void reset();
    
    void setRate(size_t requests_per_second);
    size_t getRate() const;

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

// URL parser and builder
class URLParser {
public:
    explicit URLParser(const std::string& url);
    
    std::string getProtocol() const;
    std::string getHost() const;
    int getPort() const;
    std::string getPath() const;
    std::string getQuery() const;
    std::string getFragment() const;
    std::string getUsername() const;
    std::string getPassword() const;
    
    std::unordered_map<std::string, std::string> getQueryParams() const;
    
    bool isValid() const;
    std::string toString() const;

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

} // namespace internet
} // namespace mcp
} // namespace cogniware

#endif // MCP_INTERNET_H

