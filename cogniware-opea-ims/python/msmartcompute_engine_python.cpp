#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include <torch/script.h>
#include <string>
#include <memory>
#include <vector>
#include <unordered_map>

#include "cogniware_engine.h"
#include "model_config_manager.h"
#include "monitoring/metrics_collector.h"

namespace py = pybind11;

class MSmartComputeEnginePython {
public:
    MSmartComputeEnginePython(int cuda_device_id = 0) {
        engine_ = std::make_unique<MSmartComputeEngine>(cuda_device_id);
    }

    py::dict process_request(const py::dict& request_data) {
        // Convert Python dict to JSON string
        std::string json_request = py::str(request_data);
        
        // Process request
        std::string response = engine_->process_request(json_request);
        
        // Parse response back to Python dict
        return py::eval(response);
    }

    void shutdown() {
        engine_->shutdown();
    }

    py::dict get_model_metrics(const std::string& model_name) {
        auto metrics = MetricsCollector::get_instance().get_model_metrics(model_name);
        py::dict result;
        result["total_requests"] = metrics.total_requests;
        result["total_input_tokens"] = metrics.total_input_tokens;
        result["total_output_tokens"] = metrics.total_output_tokens;
        result["average_latency"] = metrics.average_latency.count();
        result["error_counts"] = metrics.error_counts;
        return result;
    }

    py::dict get_gpu_metrics(int device_id) {
        auto metrics = MetricsCollector::get_instance().get_gpu_metrics(device_id);
        py::dict result;
        result["used_memory"] = metrics.used_memory;
        result["total_memory"] = metrics.total_memory;
        result["utilization"] = metrics.utilization;
        return result;
    }

    void reset_metrics() {
        MetricsCollector::get_instance().reset_metrics();
    }

private:
    std::unique_ptr<MSmartComputeEngine> engine_;
};

PYBIND11_MODULE(cogniware_engine_python, m) {
    m.doc() = "Python interface for MSmartCompute Engine";

    py::class_<MSmartComputeEnginePython>(m, "MSmartComputeEngine")
        .def(py::init<int>(), py::arg("cuda_device_id") = 0)
        .def("process_request", &MSmartComputeEnginePython::process_request)
        .def("shutdown", &MSmartComputeEnginePython::shutdown)
        .def("get_model_metrics", &MSmartComputeEnginePython::get_model_metrics)
        .def("get_gpu_metrics", &MSmartComputeEnginePython::get_gpu_metrics)
        .def("reset_metrics", &MSmartComputeEnginePython::reset_metrics);
} 