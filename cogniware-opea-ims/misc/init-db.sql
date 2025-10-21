-- MSmartCompute Platform Database Initialization
-- This script creates the necessary tables for the platform

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create models table
CREATE TABLE IF NOT EXISTS models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id VARCHAR(255) UNIQUE NOT NULL,
    model_type VARCHAR(100) NOT NULL,
    model_path TEXT NOT NULL,
    max_batch_size INTEGER DEFAULT 32,
    max_sequence_length INTEGER DEFAULT 512,
    enable_quantization BOOLEAN DEFAULT FALSE,
    enable_tensor_cores BOOLEAN DEFAULT TRUE,
    enable_mixed_precision BOOLEAN DEFAULT TRUE,
    parameters JSONB,
    status VARCHAR(50) DEFAULT 'unloaded',
    memory_usage BIGINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    model_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES models(model_id) ON DELETE CASCADE
);

-- Create inference_requests table
CREATE TABLE IF NOT EXISTS inference_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id VARCHAR(255) UNIQUE NOT NULL,
    model_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255),
    batch_size INTEGER NOT NULL,
    sequence_length INTEGER NOT NULL,
    data_type VARCHAR(20) DEFAULT 'float32',
    options JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    inference_time FLOAT,
    memory_used BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (model_id) REFERENCES models(model_id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE SET NULL
);

-- Create training_requests table
CREATE TABLE IF NOT EXISTS training_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id VARCHAR(255) UNIQUE NOT NULL,
    model_id VARCHAR(255) NOT NULL,
    epochs INTEGER NOT NULL,
    learning_rate FLOAT NOT NULL,
    optimizer VARCHAR(50) DEFAULT 'adam',
    loss_function VARCHAR(50) DEFAULT 'cross_entropy',
    hyperparameters JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    final_loss FLOAT,
    loss_history JSONB,
    training_time FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (model_id) REFERENCES models(model_id) ON DELETE CASCADE
);

-- Create resource_allocations table
CREATE TABLE IF NOT EXISTS resource_allocations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    allocation_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    gpu_id INTEGER NOT NULL,
    memory_size BIGINT NOT NULL,
    compute_units INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create performance_metrics table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    gpu_utilization FLOAT,
    memory_utilization FLOAT,
    temperature FLOAT,
    power_usage FLOAT,
    throughput FLOAT,
    latency FLOAT,
    active_requests INTEGER,
    queued_requests INTEGER,
    total_requests BIGINT,
    successful_requests BIGINT,
    failed_requests BIGINT
);

-- Create API keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    permissions JSONB,
    rate_limit INTEGER DEFAULT 1000,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Create audit_log table
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(255),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    details JSONB,
    ip_address INET,
    user_agent TEXT
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_models_model_id ON models(model_id);
CREATE INDEX IF NOT EXISTS idx_models_status ON models(status);
CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_inference_requests_request_id ON inference_requests(request_id);
CREATE INDEX IF NOT EXISTS idx_inference_requests_model_id ON inference_requests(model_id);
CREATE INDEX IF NOT EXISTS idx_inference_requests_status ON inference_requests(status);
CREATE INDEX IF NOT EXISTS idx_training_requests_request_id ON training_requests(request_id);
CREATE INDEX IF NOT EXISTS idx_training_requests_model_id ON training_requests(model_id);
CREATE INDEX IF NOT EXISTS idx_training_requests_status ON training_requests(status);
CREATE INDEX IF NOT EXISTS idx_resource_allocations_allocation_id ON resource_allocations(allocation_id);
CREATE INDEX IF NOT EXISTS idx_resource_allocations_user_id ON resource_allocations(user_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);

-- Create functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_models_updated_at BEFORE UPDATE ON models
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_last_activity BEFORE UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default API key for testing (password: test-api-key-123)
INSERT INTO api_keys (key_hash, user_id, name, permissions, rate_limit) VALUES 
('$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KqQKqK', 'admin', 'Default Admin Key', 
'{"models": ["read", "write", "delete"], "inference": ["read", "write"], "training": ["read", "write"], "sessions": ["read", "write"], "metrics": ["read"], "resources": ["read", "write"]}', 10000)
ON CONFLICT (key_hash) DO NOTHING;

-- Insert sample model for testing
INSERT INTO models (model_id, model_type, model_path, max_batch_size, max_sequence_length, parameters) VALUES 
('test-model', 'transformer', '/opt/msmartcompute/models/test-model.bin', 32, 512, 
'{"vocab_size": 50257, "hidden_size": 768, "num_layers": 12, "num_heads": 12}')
ON CONFLICT (model_id) DO NOTHING;

-- Create views for common queries
CREATE OR REPLACE VIEW active_sessions AS
SELECT s.*, m.model_type, m.status as model_status
FROM sessions s
JOIN models m ON s.model_id = m.model_id
WHERE s.status = 'active' AND s.expires_at > CURRENT_TIMESTAMP;

CREATE OR REPLACE VIEW recent_inference_requests AS
SELECT ir.*, m.model_type, s.user_id
FROM inference_requests ir
JOIN models m ON ir.model_id = m.model_id
LEFT JOIN sessions s ON ir.session_id = s.session_id
WHERE ir.created_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
ORDER BY ir.created_at DESC;

CREATE OR REPLACE VIEW system_metrics_summary AS
SELECT 
    AVG(gpu_utilization) as avg_gpu_utilization,
    AVG(memory_utilization) as avg_memory_utilization,
    AVG(temperature) as avg_temperature,
    AVG(power_usage) as avg_power_usage,
    AVG(throughput) as avg_throughput,
    AVG(latency) as avg_latency,
    SUM(total_requests) as total_requests_24h,
    SUM(successful_requests) as successful_requests_24h,
    SUM(failed_requests) as failed_requests_24h
FROM performance_metrics
WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '24 hours';

-- Grant permissions to msmartcompute user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO msmartcompute;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO msmartcompute;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO msmartcompute; 