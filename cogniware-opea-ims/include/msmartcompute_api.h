/**
 * @file cogniware_api.h
 * @brief C API for the cogniware engine
 */

#ifndef MSMARTCOMPUTE_API_H
#define MSMARTCOMPUTE_API_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Error codes
 */
typedef enum {
    MSMARTCOMPUTE_SUCCESS = 0,
    MSMARTCOMPUTE_ERROR_INVALID_PARAMETER = -1,
    MSMARTCOMPUTE_ERROR_INITIALIZATION_FAILED = -2,
    MSMARTCOMPUTE_ERROR_MODEL_LOAD_FAILED = -3,
    MSMARTCOMPUTE_ERROR_INFERENCE_FAILED = -4,
    MSMARTCOMPUTE_ERROR_MEMORY_ALLOCATION_FAILED = -5,
    MSMARTCOMPUTE_ERROR_DEVICE_NOT_AVAILABLE = -6,
    MSMARTCOMPUTE_ERROR_INVALID_MODEL_CONFIG = -7,
    MSMARTCOMPUTE_ERROR_INVALID_OPERATION = -8
} cogniware_error_t;

/**
 * @brief Model configuration structure
 */
typedef struct {
    const char* model_id;
    const char* model_type;
    const char* model_path;
    int max_batch_size;
    int max_sequence_length;
    float temperature;
    int top_k;
    float top_p;
    int num_beams;
    int num_return_sequences;
} cogniware_model_config_t;

/**
 * @brief Inference request structure
 */
typedef struct {
    const char* prompt;
    size_t prompt_length;
    int max_tokens;
    float temperature;
    int top_k;
    float top_p;
    int num_beams;
    int num_return_sequences;
    const char* stop_sequences;
    size_t num_stop_sequences;
} cogniware_inference_request_t;

/**
 * @brief Inference response structure
 */
typedef struct {
    char* text;
    size_t text_length;
    float* logprobs;
    size_t num_logprobs;
    int* token_ids;
    size_t num_tokens;
    float* token_logprobs;
    size_t num_token_logprobs;
} cogniware_inference_response_t;

/**
 * @brief Initialize the cogniware engine
 * @param config_path Path to configuration directory
 * @return Error code
 */
cogniware_error_t cogniware_initialize(const char* config_path);

/**
 * @brief Shutdown the cogniware engine
 * @return Error code
 */
cogniware_error_t cogniware_shutdown(void);

/**
 * @brief Load a model
 * @param config Model configuration
 * @return Error code
 */
cogniware_error_t cogniware_load_model(const cogniware_model_config_t* config);

/**
 * @brief Unload a model
 * @param model_id Model identifier
 * @return Error code
 */
cogniware_error_t cogniware_unload_model(const char* model_id);

/**
 * @brief Perform inference
 * @param model_id Model identifier
 * @param request Inference request
 * @param response Inference response (must be freed by caller)
 * @return Error code
 */
cogniware_error_t cogniware_infer(
    const char* model_id,
    const cogniware_inference_request_t* request,
    cogniware_inference_response_t* response
);

/**
 * @brief Free inference response
 * @param response Response to free
 */
void cogniware_free_response(cogniware_inference_response_t* response);

/**
 * @brief Get model metadata
 * @param model_id Model identifier
 * @param metadata JSON string containing metadata (must be freed by caller)
 * @return Error code
 */
cogniware_error_t cogniware_get_model_metadata(
    const char* model_id,
    char** metadata
);

/**
 * @brief Get model performance metrics
 * @param model_id Model identifier
 * @param metrics JSON string containing metrics (must be freed by caller)
 * @return Error code
 */
cogniware_error_t cogniware_get_model_performance(
    const char* model_id,
    char** metrics
);

/**
 * @brief Register a model
 * @param config Model configuration
 * @return Error code
 */
cogniware_error_t cogniware_register_model(
    const cogniware_model_config_t* config
);

/**
 * @brief Update model configuration
 * @param model_id Model identifier
 * @param config New model configuration
 * @return Error code
 */
cogniware_error_t cogniware_update_model_config(
    const char* model_id,
    const cogniware_model_config_t* config
);

/**
 * @brief List available models
 * @param model_ids Array of model IDs (must be freed by caller)
 * @param num_models Number of models
 * @return Error code
 */
cogniware_error_t cogniware_list_models(
    char*** model_ids,
    size_t* num_models
);

/**
 * @brief Free model ID array
 * @param model_ids Array of model IDs
 * @param num_models Number of models
 */
void cogniware_free_model_ids(
    char** model_ids,
    size_t num_models
);

#ifdef __cplusplus
}
#endif

#endif // MSMARTCOMPUTE_API_H 