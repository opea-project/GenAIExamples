#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <pybind11/chrono.h>
#include "enhanced_engine.h"

namespace py = pybind11;

PYBIND11_MODULE(enhanced_engine_py, m) {
    m.doc() = "CogniSynapse Enhanced Engine Python Bindings";

    // Bind EnhancedInferenceRequest
    py::class_<cognisynapse::EnhancedInferenceRequest>(m, "EnhancedInferenceRequest")
        .def(py::init<>())
        .def_readwrite("id", &cognisynapse::EnhancedInferenceRequest::id)
        .def_readwrite("model_id", &cognisynapse::EnhancedInferenceRequest::model_id)
        .def_readwrite("prompt", &cognisynapse::EnhancedInferenceRequest::prompt)
        .def_readwrite("max_tokens", &cognisynapse::EnhancedInferenceRequest::max_tokens)
        .def_readwrite("temperature", &cognisynapse::EnhancedInferenceRequest::temperature)
        .def_readwrite("user_id", &cognisynapse::EnhancedInferenceRequest::user_id)
        .def_readwrite("timestamp", &cognisynapse::EnhancedInferenceRequest::timestamp)
        .def_readwrite("priority", &cognisynapse::EnhancedInferenceRequest::priority)
        .def_readwrite("memory_requirement", &cognisynapse::EnhancedInferenceRequest::memory_requirement)
        .def_readwrite("use_tensor_cores", &cognisynapse::EnhancedInferenceRequest::use_tensor_cores)
        .def_readwrite("use_mixed_precision", &cognisynapse::EnhancedInferenceRequest::use_mixed_precision)
        .def_readwrite("batch_size", &cognisynapse::EnhancedInferenceRequest::batch_size);

    // Bind EnhancedInferenceResponse
    py::class_<cognisynapse::EnhancedInferenceResponse>(m, "EnhancedInferenceResponse")
        .def(py::init<>())
        .def_readwrite("id", &cognisynapse::EnhancedInferenceResponse::id)
        .def_readwrite("model_id", &cognisynapse::EnhancedInferenceResponse::model_id)
        .def_readwrite("generated_text", &cognisynapse::EnhancedInferenceResponse::generated_text)
        .def_readwrite("tokens_generated", &cognisynapse::EnhancedInferenceResponse::tokens_generated)
        .def_readwrite("processing_time_ms", &cognisynapse::EnhancedInferenceResponse::processing_time_ms)
        .def_readwrite("success", &cognisynapse::EnhancedInferenceResponse::success)
        .def_readwrite("error_message", &cognisynapse::EnhancedInferenceResponse::error_message)
        .def_readwrite("timestamp", &cognisynapse::EnhancedInferenceResponse::timestamp)
        .def_readwrite("compute_node_id", &cognisynapse::EnhancedInferenceResponse::compute_node_id)
        .def_readwrite("gpu_utilization", &cognisynapse::EnhancedInferenceResponse::gpu_utilization)
        .def_readwrite("memory_utilization", &cognisynapse::EnhancedInferenceResponse::memory_utilization)
        .def_readwrite("queue_position", &cognisynapse::EnhancedInferenceResponse::queue_position)
        .def_readwrite("wait_time_ms", &cognisynapse::EnhancedInferenceResponse::wait_time_ms);

    // Bind VirtualNodeConfig
    py::class_<cognisynapse::VirtualNodeConfig>(m, "VirtualNodeConfig")
        .def(py::init<>())
        .def_readwrite("node_id", &cognisynapse::VirtualNodeConfig::node_id)
        .def_readwrite("device_id", &cognisynapse::VirtualNodeConfig::device_id)
        .def_readwrite("memory_limit_mb", &cognisynapse::VirtualNodeConfig::memory_limit_mb)
        .def_readwrite("max_concurrent_models", &cognisynapse::VirtualNodeConfig::max_concurrent_models)
        .def_readwrite("use_tensor_cores", &cognisynapse::VirtualNodeConfig::use_tensor_cores)
        .def_readwrite("use_mixed_precision", &cognisynapse::VirtualNodeConfig::use_mixed_precision)
        .def_readwrite("memory_utilization_target", &cognisynapse::VirtualNodeConfig::memory_utilization_target)
        .def_readwrite("batch_size", &cognisynapse::VirtualNodeConfig::batch_size)
        .def_readwrite("num_streams", &cognisynapse::VirtualNodeConfig::num_streams)
        .def_readwrite("priority", &cognisynapse::VirtualNodeConfig::priority);

    // Bind VirtualNodeStatus
    py::class_<cognisynapse::VirtualNodeStatus>(m, "VirtualNodeStatus")
        .def(py::init<>())
        .def_readwrite("node_id", &cognisynapse::VirtualNodeStatus::node_id)
        .def_readwrite("active", &cognisynapse::VirtualNodeStatus::active)
        .def_readwrite("used_memory_mb", &cognisynapse::VirtualNodeStatus::used_memory_mb)
        .def_readwrite("available_memory_mb", &cognisynapse::VirtualNodeStatus::available_memory_mb)
        .def_readwrite("active_models", &cognisynapse::VirtualNodeStatus::active_models)
        .def_readwrite("queued_requests", &cognisynapse::VirtualNodeStatus::queued_requests)
        .def_readwrite("gpu_utilization", &cognisynapse::VirtualNodeStatus::gpu_utilization)
        .def_readwrite("memory_utilization", &cognisynapse::VirtualNodeStatus::memory_utilization)
        .def_readwrite("loaded_models", &cognisynapse::VirtualNodeStatus::loaded_models)
        .def_readwrite("running_requests", &cognisynapse::VirtualNodeStatus::running_requests)
        .def_readwrite("total_requests_processed", &cognisynapse::VirtualNodeStatus::total_requests_processed)
        .def_readwrite("average_processing_time_ms", &cognisynapse::VirtualNodeStatus::average_processing_time_ms);

    // Bind EnhancedModelInfo
    py::class_<cognisynapse::EnhancedModelInfo>(m, "EnhancedModelInfo")
        .def(py::init<>())
        .def_readwrite("id", &cognisynapse::EnhancedModelInfo::id)
        .def_readwrite("name", &cognisynapse::EnhancedModelInfo::name)
        .def_readwrite("type", &cognisynapse::EnhancedModelInfo::type)
        .def_readwrite("path", &cognisynapse::EnhancedModelInfo::path)
        .def_readwrite("memory_usage_mb", &cognisynapse::EnhancedModelInfo::memory_usage_mb)
        .def_readwrite("loaded", &cognisynapse::EnhancedModelInfo::loaded)
        .def_readwrite("status", &cognisynapse::EnhancedModelInfo::status)
        .def_readwrite("compute_node_id", &cognisynapse::EnhancedModelInfo::compute_node_id)
        .def_readwrite("parameter_count", &cognisynapse::EnhancedModelInfo::parameter_count)
        .def_readwrite("max_sequence_length", &cognisynapse::EnhancedModelInfo::max_sequence_length)
        .def_readwrite("supports_tensor_cores", &cognisynapse::EnhancedModelInfo::supports_tensor_cores)
        .def_readwrite("supports_mixed_precision", &cognisynapse::EnhancedModelInfo::supports_mixed_precision)
        .def_readwrite("loading_time_ms", &cognisynapse::EnhancedModelInfo::loading_time_ms)
        .def_readwrite("last_used_timestamp", &cognisynapse::EnhancedModelInfo::last_used_timestamp);

    // Bind EnhancedEngineStats
    py::class_<cognisynapse::EnhancedEngineStats>(m, "EnhancedEngineStats")
        .def(py::init<>())
        .def_readwrite("total_requests", &cognisynapse::EnhancedEngineStats::total_requests)
        .def_readwrite("successful_requests", &cognisynapse::EnhancedEngineStats::successful_requests)
        .def_readwrite("failed_requests", &cognisynapse::EnhancedEngineStats::failed_requests)
        .def_readwrite("queued_requests", &cognisynapse::EnhancedEngineStats::queued_requests)
        .def_readwrite("average_processing_time_ms", &cognisynapse::EnhancedEngineStats::average_processing_time_ms)
        .def_readwrite("average_wait_time_ms", &cognisynapse::EnhancedEngineStats::average_wait_time_ms)
        .def_readwrite("total_memory_usage_mb", &cognisynapse::EnhancedEngineStats::total_memory_usage_mb)
        .def_readwrite("active_models", &cognisynapse::EnhancedEngineStats::active_models)
        .def_readwrite("active_compute_nodes", &cognisynapse::EnhancedEngineStats::active_compute_nodes)
        .def_readwrite("overall_gpu_utilization", &cognisynapse::EnhancedEngineStats::overall_gpu_utilization)
        .def_readwrite("overall_memory_utilization", &cognisynapse::EnhancedEngineStats::overall_memory_utilization)
        .def_readwrite("requests_per_model", &cognisynapse::EnhancedEngineStats::requests_per_model)
        .def_readwrite("avg_processing_time_per_model", &cognisynapse::EnhancedEngineStats::avg_processing_time_per_model);

    // Bind VirtualComputeNode
    py::class_<cognisynapse::VirtualComputeNode>(m, "VirtualComputeNode")
        .def(py::init<const cognisynapse::VirtualNodeConfig&>())
        .def("initialize", &cognisynapse::VirtualComputeNode::initialize)
        .def("shutdown", &cognisynapse::VirtualComputeNode::shutdown)
        .def("load_model", &cognisynapse::VirtualComputeNode::loadModel)
        .def("unload_model", &cognisynapse::VirtualComputeNode::unloadModel)
        .def("process_inference_async", &cognisynapse::VirtualComputeNode::processInferenceAsync)
        .def("process_inference", &cognisynapse::VirtualComputeNode::processInference)
        .def("get_status", &cognisynapse::VirtualComputeNode::getStatus)
        .def("get_loaded_models", &cognisynapse::VirtualComputeNode::getLoadedModels)
        .def("is_healthy", &cognisynapse::VirtualComputeNode::isHealthy)
        .def("can_handle_request", &cognisynapse::VirtualComputeNode::canHandleRequest);

    // Bind EnhancedEngine
    py::class_<cognisynapse::EnhancedEngine>(m, "EnhancedEngine")
        .def(py::init<>())
        .def("initialize", &cognisynapse::EnhancedEngine::initialize,
             py::arg("config_path") = "",
             "Initialize the enhanced engine")
        .def("shutdown", &cognisynapse::EnhancedEngine::shutdown,
             "Shutdown the enhanced engine")
        .def("add_compute_node", &cognisynapse::EnhancedEngine::addComputeNode,
             "Add a virtual compute node")
        .def("remove_compute_node", &cognisynapse::EnhancedEngine::removeComputeNode,
             "Remove a virtual compute node")
        .def("get_compute_node_status", &cognisynapse::EnhancedEngine::getComputeNodeStatus,
             "Get status of all compute nodes")
        .def("load_model", &cognisynapse::EnhancedEngine::loadModel,
             py::arg("model_id"), py::arg("model_path"),
             "Load a model")
        .def("unload_model", &cognisynapse::EnhancedEngine::unloadModel,
             py::arg("model_id"),
             "Unload a model")
        .def("get_loaded_models", &cognisynapse::EnhancedEngine::getLoadedModels,
             "Get list of loaded models")
        .def("process_inference_async", &cognisynapse::EnhancedEngine::processInferenceAsync,
             py::arg("request"),
             "Process an inference request asynchronously")
        .def("process_inference", &cognisynapse::EnhancedEngine::processInference,
             py::arg("request"),
             "Process an inference request")
        .def("get_stats", &cognisynapse::EnhancedEngine::getStats,
             "Get engine statistics")
        .def("is_healthy", &cognisynapse::EnhancedEngine::isHealthy,
             "Check if engine is healthy")
        .def("get_status", [](cognisynapse::EnhancedEngine& self) {
            return self.getStatus().dump();
        }, "Get engine status as JSON string")
        .def("select_best_compute_node", &cognisynapse::EnhancedEngine::selectBestComputeNode,
             py::arg("request"),
             "Select the best compute node for a request")
        .def("rebalance_models", &cognisynapse::EnhancedEngine::rebalanceModels,
             "Rebalance models across compute nodes");
}
