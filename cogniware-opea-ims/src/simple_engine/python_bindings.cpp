#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include "simple_engine.h"

namespace py = pybind11;

PYBIND11_MODULE(simple_engine_py, m) {
    m.doc() = "CogniSynapse Simple Engine Python Bindings";

    // Bind InferenceRequest
    py::class_<cognisynapse::InferenceRequest>(m, "InferenceRequest")
        .def(py::init<>())
        .def_readwrite("id", &cognisynapse::InferenceRequest::id)
        .def_readwrite("model_id", &cognisynapse::InferenceRequest::model_id)
        .def_readwrite("prompt", &cognisynapse::InferenceRequest::prompt)
        .def_readwrite("max_tokens", &cognisynapse::InferenceRequest::max_tokens)
        .def_readwrite("temperature", &cognisynapse::InferenceRequest::temperature)
        .def_readwrite("user_id", &cognisynapse::InferenceRequest::user_id)
        .def_readwrite("timestamp", &cognisynapse::InferenceRequest::timestamp);

    // Bind InferenceResponse
    py::class_<cognisynapse::InferenceResponse>(m, "InferenceResponse")
        .def(py::init<>())
        .def_readwrite("id", &cognisynapse::InferenceResponse::id)
        .def_readwrite("model_id", &cognisynapse::InferenceResponse::model_id)
        .def_readwrite("generated_text", &cognisynapse::InferenceResponse::generated_text)
        .def_readwrite("tokens_generated", &cognisynapse::InferenceResponse::tokens_generated)
        .def_readwrite("processing_time_ms", &cognisynapse::InferenceResponse::processing_time_ms)
        .def_readwrite("success", &cognisynapse::InferenceResponse::success)
        .def_readwrite("error_message", &cognisynapse::InferenceResponse::error_message)
        .def_readwrite("timestamp", &cognisynapse::InferenceResponse::timestamp);

    // Bind ModelInfo
    py::class_<cognisynapse::ModelInfo>(m, "ModelInfo")
        .def(py::init<>())
        .def_readwrite("id", &cognisynapse::ModelInfo::id)
        .def_readwrite("name", &cognisynapse::ModelInfo::name)
        .def_readwrite("type", &cognisynapse::ModelInfo::type)
        .def_readwrite("memory_usage_mb", &cognisynapse::ModelInfo::memory_usage_mb)
        .def_readwrite("loaded", &cognisynapse::ModelInfo::loaded)
        .def_readwrite("status", &cognisynapse::ModelInfo::status);

    // Bind EngineStats
    py::class_<cognisynapse::EngineStats>(m, "EngineStats")
        .def(py::init<>())
        .def_readwrite("total_requests", &cognisynapse::EngineStats::total_requests)
        .def_readwrite("successful_requests", &cognisynapse::EngineStats::successful_requests)
        .def_readwrite("failed_requests", &cognisynapse::EngineStats::failed_requests)
        .def_readwrite("average_processing_time_ms", &cognisynapse::EngineStats::average_processing_time_ms)
        .def_readwrite("memory_usage_mb", &cognisynapse::EngineStats::memory_usage_mb)
        .def_readwrite("active_models", &cognisynapse::EngineStats::active_models);

    // Bind SimpleEngine
    py::class_<cognisynapse::SimpleEngine>(m, "SimpleEngine")
        .def(py::init<>())
        .def("initialize", &cognisynapse::SimpleEngine::initialize,
             py::arg("config_path") = "",
             "Initialize the engine")
        .def("shutdown", &cognisynapse::SimpleEngine::shutdown,
             "Shutdown the engine")
        .def("load_model", &cognisynapse::SimpleEngine::loadModel,
             py::arg("model_id"), py::arg("model_path"),
             "Load a model")
        .def("unload_model", &cognisynapse::SimpleEngine::unloadModel,
             py::arg("model_id"),
             "Unload a model")
        .def("process_inference", &cognisynapse::SimpleEngine::processInference,
             py::arg("request"),
             "Process an inference request")
        .def("get_loaded_models", &cognisynapse::SimpleEngine::getLoadedModels,
             "Get list of loaded models")
        .def("get_stats", &cognisynapse::SimpleEngine::getStats,
             "Get engine statistics")
        .def("is_healthy", &cognisynapse::SimpleEngine::isHealthy,
             "Check if engine is healthy")
        .def("get_status", [](cognisynapse::SimpleEngine& self) {
            return self.getStatus().dump();
        }, "Get engine status as JSON string");
}
