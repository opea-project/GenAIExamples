#ifndef MCP_DATABASE_H
#define MCP_DATABASE_H

#include "mcp/mcp_core.h"
#include <string>
#include <vector>
#include <unordered_map>
#include <memory>
#include <variant>
#include <chrono>

namespace cogniware {
namespace mcp {
namespace database {

// Database types
enum class DatabaseType {
    POSTGRESQL,
    MYSQL,
    SQLITE,
    MONGODB,
    REDIS,
    CASSANDRA,
    ELASTICSEARCH
};

// SQL data types
using DbValue = std::variant<
    std::nullptr_t,
    int64_t,
    double,
    std::string,
    bool,
    std::vector<uint8_t>  // BLOB
>;

// Database connection configuration
struct DbConnectionConfig {
    DatabaseType type;
    std::string host;
    int port;
    std::string database;
    std::string username;
    std::string password;
    std::unordered_map<std::string, std::string> options;
    std::chrono::milliseconds connection_timeout;
    std::chrono::milliseconds query_timeout;
    bool use_ssl;
    int max_connections;
};

// Query result row
using DbRow = std::unordered_map<std::string, DbValue>;

// Query result set
struct DbResultSet {
    std::vector<DbRow> rows;
    std::vector<std::string> column_names;
    size_t rows_affected;
    bool success;
    std::string error_message;
    std::chrono::milliseconds execution_time;
};

// Transaction isolation levels
enum class IsolationLevel {
    READ_UNCOMMITTED,
    READ_COMMITTED,
    REPEATABLE_READ,
    SERIALIZABLE
};

// Database connection interface
class DbConnection {
public:
    virtual ~DbConnection() = default;
    
    virtual bool connect() = 0;
    virtual bool disconnect() = 0;
    virtual bool isConnected() const = 0;
    
    virtual DbResultSet executeQuery(const std::string& query) = 0;
    virtual DbResultSet executePrepared(const std::string& query,
                                       const std::vector<DbValue>& params) = 0;
    
    virtual bool beginTransaction() = 0;
    virtual bool commit() = 0;
    virtual bool rollback() = 0;
    
    virtual std::string escape(const std::string& input) = 0;
    virtual DbConnectionConfig getConfig() const = 0;
};

// SQL database connection
class SQLConnection : public DbConnection {
public:
    explicit SQLConnection(const DbConnectionConfig& config);
    ~SQLConnection() override;
    
    bool connect() override;
    bool disconnect() override;
    bool isConnected() const override;
    
    DbResultSet executeQuery(const std::string& query) override;
    DbResultSet executePrepared(const std::string& query,
                               const std::vector<DbValue>& params) override;
    
    bool beginTransaction() override;
    bool commit() override;
    bool rollback() override;
    
    std::string escape(const std::string& input) override;
    DbConnectionConfig getConfig() const override;
    
    // SQL-specific operations
    DbResultSet select(const std::string& table,
                      const std::vector<std::string>& columns = {},
                      const std::string& where = "");
    
    bool insert(const std::string& table,
               const std::unordered_map<std::string, DbValue>& data);
    
    bool update(const std::string& table,
               const std::unordered_map<std::string, DbValue>& data,
               const std::string& where);
    
    bool deleteFrom(const std::string& table,
                   const std::string& where);
    
    std::vector<std::string> listTables();
    std::vector<std::string> getTableColumns(const std::string& table);

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

// NoSQL document (for MongoDB, etc.)
using DbDocument = std::unordered_map<std::string, DbValue>;

// NoSQL query result
struct NoSQLResult {
    std::vector<DbDocument> documents;
    size_t count;
    bool success;
    std::string error_message;
    std::chrono::milliseconds execution_time;
};

// NoSQL database connection
class NoSQLConnection : public DbConnection {
public:
    explicit NoSQLConnection(const DbConnectionConfig& config);
    ~NoSQLConnection() override;
    
    bool connect() override;
    bool disconnect() override;
    bool isConnected() const override;
    
    DbResultSet executeQuery(const std::string& query) override;
    DbResultSet executePrepared(const std::string& query,
                               const std::vector<DbValue>& params) override;
    
    bool beginTransaction() override;
    bool commit() override;
    bool rollback() override;
    
    std::string escape(const std::string& input) override;
    DbConnectionConfig getConfig() const override;
    
    // NoSQL-specific operations
    NoSQLResult find(const std::string& collection,
                    const DbDocument& query = {},
                    int limit = 0);
    
    bool insertOne(const std::string& collection,
                  const DbDocument& document);
    
    bool insertMany(const std::string& collection,
                   const std::vector<DbDocument>& documents);
    
    bool updateOne(const std::string& collection,
                  const DbDocument& query,
                  const DbDocument& update);
    
    bool updateMany(const std::string& collection,
                   const DbDocument& query,
                   const DbDocument& update);
    
    bool deleteOne(const std::string& collection,
                  const DbDocument& query);
    
    bool deleteMany(const std::string& collection,
                   const DbDocument& query);
    
    std::vector<std::string> listCollections();

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

// Redis key-value operations
class RedisConnection : public DbConnection {
public:
    explicit RedisConnection(const DbConnectionConfig& config);
    ~RedisConnection() override;
    
    bool connect() override;
    bool disconnect() override;
    bool isConnected() const override;
    
    DbResultSet executeQuery(const std::string& query) override;
    DbResultSet executePrepared(const std::string& query,
                               const std::vector<DbValue>& params) override;
    
    bool beginTransaction() override;
    bool commit() override;
    bool rollback() override;
    
    std::string escape(const std::string& input) override;
    DbConnectionConfig getConfig() const override;
    
    // Redis-specific operations
    bool set(const std::string& key, const std::string& value,
            std::chrono::seconds expiration = std::chrono::seconds(0));
    
    std::string get(const std::string& key);
    bool del(const std::string& key);
    bool exists(const std::string& key);
    
    bool hset(const std::string& key, const std::string& field,
             const std::string& value);
    std::string hget(const std::string& key, const std::string& field);
    std::unordered_map<std::string, std::string> hgetall(const std::string& key);
    
    bool lpush(const std::string& key, const std::string& value);
    std::string lpop(const std::string& key);
    std::vector<std::string> lrange(const std::string& key, int start, int stop);

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

// MCP Database tools
class MCPDatabaseTools {
public:
    MCPDatabaseTools();
    ~MCPDatabaseTools();
    
    // Register all database tools to an MCP server
    static void registerAllTools(AdvancedMCPServer& server);
    
    // Connection management
    static std::string createConnection(const DbConnectionConfig& config);
    static bool closeConnection(const std::string& connection_id);
    static std::shared_ptr<DbConnection> getConnection(const std::string& connection_id);
    
    // SQL operations
    static DbResultSet executeSQL(const std::string& connection_id,
                                 const std::string& query);
    
    static DbResultSet selectData(const std::string& connection_id,
                                 const std::string& table,
                                 const std::vector<std::string>& columns = {},
                                 const std::string& where = "");
    
    static bool insertData(const std::string& connection_id,
                          const std::string& table,
                          const std::unordered_map<std::string, DbValue>& data);
    
    static bool updateData(const std::string& connection_id,
                          const std::string& table,
                          const std::unordered_map<std::string, DbValue>& data,
                          const std::string& where);
    
    static bool deleteData(const std::string& connection_id,
                          const std::string& table,
                          const std::string& where);
    
    // NoSQL operations
    static NoSQLResult findDocuments(const std::string& connection_id,
                                    const std::string& collection,
                                    const DbDocument& query = {});
    
    static bool insertDocument(const std::string& connection_id,
                              const std::string& collection,
                              const DbDocument& document);
    
    static bool updateDocuments(const std::string& connection_id,
                               const std::string& collection,
                               const DbDocument& query,
                               const DbDocument& update);
    
    // Redis operations
    static bool redisSet(const std::string& connection_id,
                        const std::string& key,
                        const std::string& value);
    
    static std::string redisGet(const std::string& connection_id,
                               const std::string& key);
    
    // Utility functions
    static std::string formatResultSet(const DbResultSet& result);
    static std::string valueToString(const DbValue& value);

private:
    static std::unordered_map<std::string, std::shared_ptr<DbConnection>> connections_;
    static std::mutex connections_mutex_;
};

// Database connection pool
class DbConnectionPool {
public:
    DbConnectionPool(const DbConnectionConfig& config, size_t pool_size);
    ~DbConnectionPool();
    
    std::shared_ptr<DbConnection> acquire();
    void release(std::shared_ptr<DbConnection> conn);
    
    size_t getAvailableConnections() const;
    size_t getTotalConnections() const;
    
    struct PoolStats {
        size_t total_connections;
        size_t active_connections;
        size_t idle_connections;
        size_t total_acquires;
        size_t total_releases;
        double avg_wait_time_ms;
    };
    
    PoolStats getStats() const;

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

// Query builder for SQL
class QueryBuilder {
public:
    QueryBuilder();
    
    QueryBuilder& select(const std::vector<std::string>& columns);
    QueryBuilder& from(const std::string& table);
    QueryBuilder& where(const std::string& condition);
    QueryBuilder& orderBy(const std::string& column, bool ascending = true);
    QueryBuilder& limit(int count);
    QueryBuilder& offset(int count);
    QueryBuilder& join(const std::string& table, const std::string& condition);
    QueryBuilder& leftJoin(const std::string& table, const std::string& condition);
    
    std::string build() const;
    void reset();

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

// Database migration manager
class MigrationManager {
public:
    explicit MigrationManager(std::shared_ptr<DbConnection> connection);
    ~MigrationManager();
    
    bool initialize();
    bool runMigrations(const std::string& migrations_dir);
    bool rollback(int steps = 1);
    
    std::vector<std::string> getAppliedMigrations() const;
    std::vector<std::string> getPendingMigrations(const std::string& migrations_dir) const;

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

} // namespace database
} // namespace mcp
} // namespace cogniware

#endif // MCP_DATABASE_H

