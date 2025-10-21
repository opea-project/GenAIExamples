#include "simple_api.h"
#include <cstring>
#include <iostream>

extern "C" {

void* simple_engine_create() {
    try {
        return new cognisynapse::SimpleEngine();
    } catch (const std::exception& e) {
        std::cerr << "Failed to create SimpleEngine: " << e.what() << std::endl;
        return nullptr;
    }
}

void simple_engine_destroy(void* engine) {
    if (engine) {
        delete static_cast<cognisynapse::SimpleEngine*>(engine);
    }
}

int simple_engine_initialize(void* engine, const char* config_path) {
    if (!engine) {
        return 0;
    }
    
    try {
        cognisynapse::SimpleEngine* eng = static_cast<cognisynapse::SimpleEngine*>(engine);
        std::string config = config_path ? config_path : "";
        return eng->initialize(config) ? 1 : 0;
    } catch (const std::exception& e) {
        std::cerr << "Failed to initialize SimpleEngine: " << e.what() << std::endl;
        return 0;
    }
}

void simple_engine_shutdown(void* engine) {
    if (engine) {
        try {
            cognisynapse::SimpleEngine* eng = static_cast<cognisynapse::SimpleEngine*>(engine);
            eng->shutdown();
        } catch (const std::exception& e) {
            std::cerr << "Failed to shutdown SimpleEngine: " << e.what() << std::endl;
        }
    }
}

int simple_engine_load_model(void* engine, const char* model_id, const char* model_path) {
    if (!engine || !model_id || !model_path) {
        return 0;
    }
    
    try {
        cognisynapse::SimpleEngine* eng = static_cast<cognisynapse::SimpleEngine*>(engine);
        return eng->loadModel(model_id, model_path) ? 1 : 0;
    } catch (const std::exception& e) {
        std::cerr << "Failed to load model: " << e.what() << std::endl;
        return 0;
    }
}

int simple_engine_unload_model(void* engine, const char* model_id) {
    if (!engine || !model_id) {
        return 0;
    }
    
    try {
        cognisynapse::SimpleEngine* eng = static_cast<cognisynapse::SimpleEngine*>(engine);
        return eng->unloadModel(model_id) ? 1 : 0;
    } catch (const std::exception& e) {
        std::cerr << "Failed to unload model: " << e.what() << std::endl;
        return 0;
    }
}

int simple_engine_process_inference(void* engine, const char* request_json, char* response_json, size_t response_size) {
    if (!engine || !request_json || !response_json || response_size == 0) {
        return 0;
    }
    
    try {
        cognisynapse::SimpleEngine* eng = static_cast<cognisynapse::SimpleEngine*>(engine);
        
        // Parse request JSON
        nlohmann::json request = nlohmann::json::parse(request_json);
        
        cognisynapse::InferenceRequest req;
        req.id = request.value("id", "");
        req.model_id = request.value("model_id", "");
        req.prompt = request.value("prompt", "");
        req.max_tokens = request.value("max_tokens", 100);
        req.temperature = request.value("temperature", 0.7f);
        req.user_id = request.value("user_id", "");
        req.document_type = request.value("document_type", "");
        req.timestamp = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::system_clock::now().time_since_epoch()).count();
        
        // Process inference
        cognisynapse::InferenceResponse resp = eng->processInference(req);
        
        // Convert response to JSON
        nlohmann::json response;
        response["id"] = resp.id;
        response["model_id"] = resp.model_id;
        response["generated_text"] = resp.generated_text;
        response["tokens_generated"] = resp.tokens_generated;
        response["processing_time_ms"] = resp.processing_time_ms;
        response["success"] = resp.success;
        response["error_message"] = resp.error_message;
        response["timestamp"] = resp.timestamp;
        
        std::string response_str = response.dump();
        
        if (response_str.length() >= response_size) {
            return 0; // Buffer too small
        }
        
        std::strcpy(response_json, response_str.c_str());
        return 1;
        
    } catch (const std::exception& e) {
        std::cerr << "Failed to process inference: " << e.what() << std::endl;
        return 0;
    }
}

int simple_engine_is_healthy(void* engine) {
    if (!engine) {
        return 0;
    }
    
    try {
        cognisynapse::SimpleEngine* eng = static_cast<cognisynapse::SimpleEngine*>(engine);
        return eng->isHealthy() ? 1 : 0;
    } catch (const std::exception& e) {
        std::cerr << "Failed to check engine health: " << e.what() << std::endl;
        return 0;
    }
}

int simple_engine_get_status(void* engine, char* status_json, size_t status_size) {
    if (!engine || !status_json || status_size == 0) {
        return 0;
    }
    
    try {
        cognisynapse::SimpleEngine* eng = static_cast<cognisynapse::SimpleEngine*>(engine);
        nlohmann::json status = eng->getStatus();
        
        std::string status_str = status.dump();
        
        if (status_str.length() >= status_size) {
            return 0; // Buffer too small
        }
        
        std::strcpy(status_json, status_str.c_str());
        return 1;
        
    } catch (const std::exception& e) {
        std::cerr << "Failed to get engine status: " << e.what() << std::endl;
        return 0;
    }
}

int simple_engine_get_models(void* engine, char* models_json, size_t models_size) {
    if (!engine || !models_json || models_size == 0) {
        return 0;
    }
    
    try {
        cognisynapse::SimpleEngine* eng = static_cast<cognisynapse::SimpleEngine*>(engine);
        auto models = eng->getLoadedModels();
        
        nlohmann::json models_array = nlohmann::json::array();
        for (const auto& model : models) {
            nlohmann::json model_json;
            model_json["id"] = model.id;
            model_json["name"] = model.name;
            model_json["type"] = model.type;
            model_json["memory_usage_mb"] = model.memory_usage_mb;
            model_json["loaded"] = model.loaded;
            model_json["status"] = model.status;
            models_array.push_back(model_json);
        }
        
        std::string models_str = models_array.dump();
        
        if (models_str.length() >= models_size) {
            return 0; // Buffer too small
        }
        
        std::strcpy(models_json, models_str.c_str());
        return 1;
        
    } catch (const std::exception& e) {
        std::cerr << "Failed to get models: " << e.what() << std::endl;
        return 0;
    }
}

} // extern "C"
