#include "cogniware_api.h"
#include "../model_config_manager/model_config_manager.hpp"
#include "../model_config_manager/model_registry_manager.hpp"
#include "../llm_management/llm_instance_manager.hpp"
#include <memory>
#include <string>
#include <vector>
#include <cstring>

namespace cogniware {

// Global instances
static std::unique_ptr<ModelConfigManager> g_config_manager;
static std::unique_ptr<ModelRegistryManager> g_registry_manager;
static std::unique_ptr<LLMInstanceManager> g_instance_manager;

} // namespace cogniware

extern "C" {

cogniware_error_t cogniware_initialize(const char* config_path) {
    try {
        if (!config_path) {
            return MSMARTCOMPUTE_ERROR_INVALID_PARAMETER;
        }

        // Initialize managers
        cogniware::g_config_manager = std::make_unique<cogniware::ModelConfigManager>();
        cogniware::g_registry_manager = std::make_unique<cogniware::ModelRegistryManager>();
        cogniware::g_instance_manager = std::make_unique<cogniware::LLMInstanceManager>();

        // Initialize configuration manager
        if (!cogniware::g_config_manager->initialize(config_path)) {
            return MSMARTCOMPUTE_ERROR_INITIALIZATION_FAILED;
        }

        // Initialize registry manager
        if (!cogniware::g_registry_manager->initialize(config_path)) {
            return MSMARTCOMPUTE_ERROR_INITIALIZATION_FAILED;
        }

        return MSMARTCOMPUTE_SUCCESS;
    } catch (const std::exception& e) {
        return MSMARTCOMPUTE_ERROR_INITIALIZATION_FAILED;
    }
}

cogniware_error_t cogniware_shutdown(void) {
    try {
        cogniware::g_instance_manager.reset();
        cogniware::g_registry_manager.reset();
        cogniware::g_config_manager.reset();
        return MSMARTCOMPUTE_SUCCESS;
    } catch (const std::exception& e) {
        return MSMARTCOMPUTE_ERROR_INVALID_OPERATION;
    }
}

cogniware_error_t cogniware_load_model(const cogniware_model_config_t* config) {
    try {
        if (!config || !config->model_id || !config->model_path) {
            return MSMARTCOMPUTE_ERROR_INVALID_PARAMETER;
        }

        // Convert C config to C++ config
        cogniware::ModelConfig model_config;
        model_config.model_id = config->model_id;
        model_config.model_type = config->model_type;
        model_config.model_config = {
            {"path", config->model_path},
            {"max_batch_size", config->max_batch_size},
            {"max_sequence_length", config->max_sequence_length},
            {"generation", {
                {"temperature", config->temperature},
                {"top_k", config->top_k},
                {"top_p", config->top_p},
                {"num_beams", config->num_beams},
                {"num_return_sequences", config->num_return_sequences}
            }}
        };

        // Register model configuration
        if (!cogniware::g_config_manager->registerModel(model_config)) {
            return MSMARTCOMPUTE_ERROR_MODEL_LOAD_FAILED;
        }

        return MSMARTCOMPUTE_SUCCESS;
    } catch (const std::exception& e) {
        return MSMARTCOMPUTE_ERROR_MODEL_LOAD_FAILED;
    }
}

cogniware_error_t cogniware_unload_model(const char* model_id) {
    try {
        if (!model_id) {
            return MSMARTCOMPUTE_ERROR_INVALID_PARAMETER;
        }

        // TODO: Implement model unloading
        return MSMARTCOMPUTE_SUCCESS;
    } catch (const std::exception& e) {
        return MSMARTCOMPUTE_ERROR_INVALID_OPERATION;
    }
}

cogniware_error_t cogniware_infer(
    const char* model_id,
    const cogniware_inference_request_t* request,
    cogniware_inference_response_t* response
) {
    try {
        if (!model_id || !request || !response) {
            return MSMARTCOMPUTE_ERROR_INVALID_PARAMETER;
        }

        // TODO: Implement inference
        return MSMARTCOMPUTE_SUCCESS;
    } catch (const std::exception& e) {
        return MSMARTCOMPUTE_ERROR_INFERENCE_FAILED;
    }
}

void cogniware_free_response(cogniware_inference_response_t* response) {
    if (!response) {
        return;
    }

    free(response->text);
    free(response->logprobs);
    free(response->token_ids);
    free(response->token_logprobs);
}

cogniware_error_t cogniware_get_model_metadata(
    const char* model_id,
    char** metadata
) {
    try {
        if (!model_id || !metadata) {
            return MSMARTCOMPUTE_ERROR_INVALID_PARAMETER;
        }

        auto config = cogniware::g_config_manager->getModelConfig(model_id);
        if (!config) {
            return MSMARTCOMPUTE_ERROR_INVALID_MODEL_CONFIG;
        }

        auto metadata_json = config->model_config["metadata"].dump();
        *metadata = strdup(metadata_json.c_str());
        return MSMARTCOMPUTE_SUCCESS;
    } catch (const std::exception& e) {
        return MSMARTCOMPUTE_ERROR_INVALID_OPERATION;
    }
}

cogniware_error_t cogniware_get_model_performance(
    const char* model_id,
    char** metrics
) {
    try {
        if (!model_id || !metrics) {
            return MSMARTCOMPUTE_ERROR_INVALID_PARAMETER;
        }

        auto config = cogniware::g_config_manager->getModelConfig(model_id);
        if (!config) {
            return MSMARTCOMPUTE_ERROR_INVALID_MODEL_CONFIG;
        }

        auto metrics_json = config->model_config["performance_metrics"].dump();
        *metrics = strdup(metrics_json.c_str());
        return MSMARTCOMPUTE_SUCCESS;
    } catch (const std::exception& e) {
        return MSMARTCOMPUTE_ERROR_INVALID_OPERATION;
    }
}

cogniware_error_t cogniware_register_model(
    const cogniware_model_config_t* config
) {
    try {
        if (!config || !config->model_id || !config->model_path) {
            return MSMARTCOMPUTE_ERROR_INVALID_PARAMETER;
        }

        // Convert C config to C++ config
        cogniware::ModelConfig model_config;
        model_config.model_id = config->model_id;
        model_config.model_type = config->model_type;
        model_config.model_config = {
            {"path", config->model_path},
            {"max_batch_size", config->max_batch_size},
            {"max_sequence_length", config->max_sequence_length},
            {"generation", {
                {"temperature", config->temperature},
                {"top_k", config->top_k},
                {"top_p", config->top_p},
                {"num_beams", config->num_beams},
                {"num_return_sequences", config->num_return_sequences}
            }}
        };

        // Register model configuration
        if (!cogniware::g_config_manager->registerModel(model_config)) {
            return MSMARTCOMPUTE_ERROR_INVALID_MODEL_CONFIG;
        }

        return MSMARTCOMPUTE_SUCCESS;
    } catch (const std::exception& e) {
        return MSMARTCOMPUTE_ERROR_INVALID_MODEL_CONFIG;
    }
}

cogniware_error_t cogniware_update_model_config(
    const char* model_id,
    const cogniware_model_config_t* config
) {
    try {
        if (!model_id || !config) {
            return MSMARTCOMPUTE_ERROR_INVALID_PARAMETER;
        }

        // Convert C config to JSON updates
        nlohmann::json updates = {
            {"model_type", config->model_type},
            {"model_config", {
                {"path", config->model_path},
                {"max_batch_size", config->max_batch_size},
                {"max_sequence_length", config->max_sequence_length},
                {"generation", {
                    {"temperature", config->temperature},
                    {"top_k", config->top_k},
                    {"top_p", config->top_p},
                    {"num_beams", config->num_beams},
                    {"num_return_sequences", config->num_return_sequences}
                }}
            }}
        };

        // Update model configuration
        if (!cogniware::g_config_manager->updateModelConfig(model_id, updates)) {
            return MSMARTCOMPUTE_ERROR_INVALID_MODEL_CONFIG;
        }

        return MSMARTCOMPUTE_SUCCESS;
    } catch (const std::exception& e) {
        return MSMARTCOMPUTE_ERROR_INVALID_MODEL_CONFIG;
    }
}

cogniware_error_t cogniware_list_models(
    char*** model_ids,
    size_t* num_models
) {
    try {
        if (!model_ids || !num_models) {
            return MSMARTCOMPUTE_ERROR_INVALID_PARAMETER;
        }

        auto models = cogniware::g_config_manager->listModels();
        *num_models = models.size();
        
        *model_ids = static_cast<char**>(malloc(models.size() * sizeof(char*)));
        if (!*model_ids) {
            return MSMARTCOMPUTE_ERROR_MEMORY_ALLOCATION_FAILED;
        }

        for (size_t i = 0; i < models.size(); ++i) {
            (*model_ids)[i] = strdup(models[i].c_str());
        }

        return MSMARTCOMPUTE_SUCCESS;
    } catch (const std::exception& e) {
        return MSMARTCOMPUTE_ERROR_INVALID_OPERATION;
    }
}

void cogniware_free_model_ids(
    char** model_ids,
    size_t num_models
) {
    if (!model_ids) {
        return;
    }

    for (size_t i = 0; i < num_models; ++i) {
        free(model_ids[i]);
    }
    free(model_ids);
}

} // extern "C"
