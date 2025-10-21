#pragma once

#include "simple_engine.h"
#include <string>

extern "C" {

/**
 * @brief C API for SimpleEngine
 */

// Engine lifecycle
void* simple_engine_create();
void simple_engine_destroy(void* engine);
int simple_engine_initialize(void* engine, const char* config_path);
void simple_engine_shutdown(void* engine);

// Model management
int simple_engine_load_model(void* engine, const char* model_id, const char* model_path);
int simple_engine_unload_model(void* engine, const char* model_id);

// Inference
int simple_engine_process_inference(void* engine, const char* request_json, char* response_json, size_t response_size);

// Status and information
int simple_engine_is_healthy(void* engine);
int simple_engine_get_status(void* engine, char* status_json, size_t status_size);
int simple_engine_get_models(void* engine, char* models_json, size_t models_size);

} // extern "C"
