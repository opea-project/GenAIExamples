# Install script for directory: /home/deadbrainviv/Documents/GitHub/cogniware-core

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/usr/local")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "Release")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Install shared libraries without execute permission?
if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  set(CMAKE_INSTALL_SO_NO_EXE "1")
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "FALSE")
endif()

# Set default install directory permissions.
if(NOT DEFINED CMAKE_OBJDUMP)
  set(CMAKE_OBJDUMP "/usr/bin/objdump")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  foreach(file
      "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libsimple_engine.so.1.0.0"
      "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libsimple_engine.so.1"
      )
    if(EXISTS "${file}" AND
       NOT IS_SYMLINK "${file}")
      file(RPATH_CHECK
           FILE "${file}"
           RPATH "")
    endif()
  endforeach()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE SHARED_LIBRARY FILES
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/build/libsimple_engine.so.1.0.0"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/build/libsimple_engine.so.1"
    )
  foreach(file
      "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libsimple_engine.so.1.0.0"
      "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libsimple_engine.so.1"
      )
    if(EXISTS "${file}" AND
       NOT IS_SYMLINK "${file}")
      if(CMAKE_INSTALL_DO_STRIP)
        execute_process(COMMAND "/usr/bin/strip" "${file}")
      endif()
    endif()
  endforeach()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE SHARED_LIBRARY FILES "/home/deadbrainviv/Documents/GitHub/cogniware-core/build/libsimple_engine.so")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libenhanced_engine.so" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libenhanced_engine.so")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libenhanced_engine.so"
         RPATH "")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE SHARED_LIBRARY FILES "/home/deadbrainviv/Documents/GitHub/cogniware-core/build/libenhanced_engine.so")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libenhanced_engine.so" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libenhanced_engine.so")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libenhanced_engine.so")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libcore_inference_engine.so" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libcore_inference_engine.so")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libcore_inference_engine.so"
         RPATH "")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE SHARED_LIBRARY FILES "/home/deadbrainviv/Documents/GitHub/cogniware-core/build/libcore_inference_engine.so")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libcore_inference_engine.so" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libcore_inference_engine.so")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libcore_inference_engine.so")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/simple_engine" TYPE FILE FILES
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/src/simple_engine/simple_engine.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/src/simple_engine/simple_api.h"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/llm_inference_core" TYPE FILE FILES
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/llm_inference_core/llm_inference_core.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/llm_inference_core/inference/inference_engine.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/llm_inference_core/model/model_manager.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/llm_inference_core/model/model_selector.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/llm_inference_core/model/model_downloader.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/llm_inference_core/model/model_configurator.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/llm_inference_core/model/model_registry.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/llm_inference_core/model/model_manager_system.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/core/customized_kernel.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/core/python_cpp_bridge.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/optimization/tensor_core_optimizer.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/virtualization/virtual_compute_node.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/memory/memory_partitioning.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/parallel/parallel_llm_execution.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/nvlink/nvlink_optimization.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/cuda/cuda_stream_management.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/scheduler/compute_node_scheduler.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/bridge/python_cpp_bridge.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/orchestration/multi_llm_orchestrator.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/inference/inference_sharing.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/multimodal/multimodal_processor.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/mcp/mcp_core.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/mcp/mcp_filesystem.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/mcp/mcp_internet.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/mcp/mcp_database.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/mcp/mcp_application.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/mcp/mcp_system_services.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/mcp/mcp_security.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/mcp/mcp_resources.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/mcp/mcp_tool_registry.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/api/rest_api.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/benchmark/performance_benchmark.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/async/async_processor.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/model/model_manager.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/monitoring/monitoring_system.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/optimization/optimizer.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/ipc/inter_llm_bus.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/distributed/distributed_system.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/gpu/gpu_virtualization.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/include/training/training_interface.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/src/llm_inference_core/tokenizer_interface/base_tokenizer.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/src/llm_inference_core/tokenizer_interface/bpe_tokenizer.h"
    "/home/deadbrainviv/Documents/GitHub/cogniware-core/src/llm_inference_core/tokenizer_interface/tokenizer_factory.h"
    )
endif()

if(CMAKE_INSTALL_COMPONENT)
  set(CMAKE_INSTALL_MANIFEST "install_manifest_${CMAKE_INSTALL_COMPONENT}.txt")
else()
  set(CMAKE_INSTALL_MANIFEST "install_manifest.txt")
endif()

string(REPLACE ";" "\n" CMAKE_INSTALL_MANIFEST_CONTENT
       "${CMAKE_INSTALL_MANIFEST_FILES}")
file(WRITE "/home/deadbrainviv/Documents/GitHub/cogniware-core/build/${CMAKE_INSTALL_MANIFEST}"
     "${CMAKE_INSTALL_MANIFEST_CONTENT}")
