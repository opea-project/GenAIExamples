#!/bin/bash

# MSSmartCompute Platform API Test Script
# This script tests all the API endpoints to ensure they're working correctly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="http://localhost:8080"
API_KEY="test-api-key-123"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to make API requests
make_request() {
    local method=$1
    local endpoint=$2
    local data=$3
    local expected_status=$4
    
    local url="${BASE_URL}${endpoint}"
    local curl_opts="-s -w '%{http_code}' -o /tmp/api_response.json"
    
    if [ -n "$data" ]; then
        curl_opts="$curl_opts -H 'Content-Type: application/json' -d '$data'"
    fi
    
    if [ -n "$API_KEY" ]; then
        curl_opts="$curl_opts -H 'X-API-Key: $API_KEY'"
    fi
    
    local response_code=$(eval "curl -X $method $curl_opts $url")
    
    if [ "$response_code" = "$expected_status" ]; then
        print_success "$method $endpoint - Status: $response_code"
        if [ -f /tmp/api_response.json ]; then
            echo "Response: $(cat /tmp/api_response.json | head -c 200)..."
        fi
        return 0
    else
        print_error "$method $endpoint - Expected: $expected_status, Got: $response_code"
        if [ -f /tmp/api_response.json ]; then
            echo "Response: $(cat /tmp/api_response.json)"
        fi
        return 1
    fi
}

# Function to test health endpoint
test_health() {
    print_status "Testing health endpoint..."
    make_request "GET" "/health" "" "200"
}

# Function to test model management endpoints
test_model_management() {
    print_status "Testing model management endpoints..."
    
    # List models
    make_request "GET" "/api/v1/models" "" "200"
    
    # Load a model
    local load_model_data='{
        "model_id": "test-model",
        "model_type": "transformer",
        "model_path": "/opt/msmartcompute/models/test-model.bin",
        "max_batch_size": 32,
        "max_sequence_length": 512,
        "enable_tensor_cores": true,
        "enable_mixed_precision": true,
        "parameters": {
            "vocab_size": 50257,
            "hidden_size": 768,
            "num_layers": 12,
            "num_heads": 12
        }
    }'
    make_request "POST" "/api/v1/models" "$load_model_data" "200"
    
    # Get model info
    make_request "GET" "/api/v1/models/test-model" "" "200"
    
    # List models again
    make_request "GET" "/api/v1/models" "" "200"
}

# Function to test session management
test_session_management() {
    print_status "Testing session management endpoints..."
    
    # Create a session
    local create_session_data='{
        "user_id": "test-user-123",
        "model_id": "test-model"
    }'
    make_request "POST" "/api/v1/sessions" "$create_session_data" "200"
    
    # List sessions
    make_request "GET" "/api/v1/sessions" "" "200"
}

# Function to test inference endpoints
test_inference() {
    print_status "Testing inference endpoints..."
    
    # Create inference request
    local inference_data='{
        "model_id": "test-model",
        "session_id": "test-session-123",
        "batch_size": 1,
        "sequence_length": 128,
        "data_type": "float32",
        "input_data": [0.1, 0.2, 0.3, 0.4, 0.5],
        "options": {
            "temperature": 0.7,
            "max_tokens": 50
        }
    }'
    make_request "POST" "/api/v1/inference" "$inference_data" "200"
    
    # Get inference result (async)
    sleep 2
    make_request "GET" "/api/v1/inference/test-request-123" "" "200"
}

# Function to test training endpoints
test_training() {
    print_status "Testing training endpoints..."
    
    # Create training request
    local training_data='{
        "model_id": "test-model",
        "epochs": 5,
        "learning_rate": 0.001,
        "optimizer": "adam",
        "loss_function": "cross_entropy",
        "hyperparameters": {
            "batch_size": 32,
            "gradient_clipping": 1.0
        }
    }'
    make_request "POST" "/api/v1/training" "$training_data" "200"
    
    # Get training status
    sleep 2
    make_request "GET" "/api/v1/training/test-training-123" "" "200"
}

# Function to test resource management
test_resource_management() {
    print_status "Testing resource management endpoints..."
    
    # Get resource allocation
    make_request "GET" "/api/v1/resources" "" "200"
    
    # Request resource allocation
    local resource_data='{
        "user_id": "test-user-123",
        "gpu_id": 0,
        "memory_size": 1073741824,
        "compute_units": 4
    }'
    make_request "POST" "/api/v1/resources" "$resource_data" "200"
}

# Function to test performance metrics
test_performance_metrics() {
    print_status "Testing performance metrics endpoints..."
    
    # Get performance metrics
    make_request "GET" "/api/v1/metrics" "" "200"
    
    # Get GPU metrics
    make_request "GET" "/api/v1/metrics/gpu" "" "200"
    
    # Get memory metrics
    make_request "GET" "/api/v1/metrics/memory" "" "200"
}

# Function to test batch operations
test_batch_operations() {
    print_status "Testing batch operations..."
    
    # Batch inference
    local batch_inference_data='{
        "requests": [
            {
                "model_id": "test-model",
                "batch_size": 1,
                "sequence_length": 64,
                "input_data": [0.1, 0.2, 0.3]
            },
            {
                "model_id": "test-model",
                "batch_size": 1,
                "sequence_length": 64,
                "input_data": [0.4, 0.5, 0.6]
            }
        ]
    }'
    make_request "POST" "/api/v1/batch/inference" "$batch_inference_data" "200"
}

# Function to test error handling
test_error_handling() {
    print_status "Testing error handling..."
    
    # Test invalid model ID
    make_request "GET" "/api/v1/models/invalid-model" "" "404"
    
    # Test invalid session
    make_request "GET" "/api/v1/sessions/invalid-session" "" "404"
    
    # Test invalid inference request
    local invalid_inference='{
        "model_id": "invalid-model",
        "batch_size": 1,
        "sequence_length": 128
    }'
    make_request "POST" "/api/v1/inference" "$invalid_inference" "400"
}

# Function to test rate limiting
test_rate_limiting() {
    print_status "Testing rate limiting..."
    
    # Make multiple rapid requests
    for i in {1..5}; do
        make_request "GET" "/api/v1/models" "" "200" &
    done
    wait
    
    print_success "Rate limiting test completed"
}

# Function to run comprehensive tests
run_comprehensive_tests() {
    print_status "Starting comprehensive API tests..."
    
    local tests=(
        "test_health"
        "test_model_management"
        "test_session_management"
        "test_inference"
        "test_training"
        "test_resource_management"
        "test_performance_metrics"
        "test_batch_operations"
        "test_error_handling"
        "test_rate_limiting"
    )
    
    local passed=0
    local failed=0
    
    for test in "${tests[@]}"; do
        print_status "Running $test..."
        if $test; then
            ((passed++))
        else
            ((failed++))
        fi
        echo ""
    done
    
    echo "=========================================="
    print_status "Test Results:"
    print_success "Passed: $passed"
    if [ $failed -gt 0 ]; then
        print_error "Failed: $failed"
    fi
    echo "=========================================="
}

# Function to wait for platform to be ready
wait_for_platform() {
    print_status "Waiting for MSmartCompute platform to be ready..."
    
    local timeout=60
    local counter=0
    
    while [ $counter -lt $timeout ]; do
        if curl -f "$BASE_URL/health" > /dev/null 2>&1; then
            print_success "Platform is ready"
            return 0
        fi
        sleep 2
        counter=$((counter + 2))
        echo -n "."
    done
    
    print_error "Platform did not become ready within $timeout seconds"
    return 1
}

# Main execution
main() {
    echo "=========================================="
    echo "MSSmartCompute Platform API Test Suite"
    echo "=========================================="
    echo ""
    
    # Wait for platform to be ready
    if ! wait_for_platform; then
        exit 1
    fi
    
    # Run comprehensive tests
    run_comprehensive_tests
}

# Handle command line arguments
case "${1:-}" in
    "health")
        test_health
        ;;
    "models")
        test_model_management
        ;;
    "sessions")
        test_session_management
        ;;
    "inference")
        test_inference
        ;;
    "training")
        test_training
        ;;
    "resources")
        test_resource_management
        ;;
    "metrics")
        test_performance_metrics
        ;;
    "batch")
        test_batch_operations
        ;;
    "errors")
        test_error_handling
        ;;
    "rate-limit")
        test_rate_limiting
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [test_category]"
        echo ""
        echo "Test Categories:"
        echo "  (no args)  Run all tests"
        echo "  health     Test health endpoint"
        echo "  models     Test model management"
        echo "  sessions   Test session management"
        echo "  inference  Test inference endpoints"
        echo "  training   Test training endpoints"
        echo "  resources  Test resource management"
        echo "  metrics    Test performance metrics"
        echo "  batch      Test batch operations"
        echo "  errors     Test error handling"
        echo "  rate-limit Test rate limiting"
        echo "  help       Show this help"
        ;;
    *)
        main
        ;;
esac 