# FindCUDNN.cmake
# Locates the cuDNN library
#
# This module defines the following variables:
#   CUDNN_FOUND - True if cuDNN is found
#   CUDNN_INCLUDE_DIRS - cuDNN include directories
#   CUDNN_LIBRARIES - cuDNN libraries

# Try to find cuDNN in standard locations
find_path(CUDNN_INCLUDE_DIR
    NAMES cudnn.h
    PATHS
        /usr/local/cuda/include
        /usr/include
        $ENV{CUDA_PATH}/include
        $ENV{CUDNN_PATH}/include
    DOC "cuDNN include directory"
)

# Find cuDNN library
find_library(CUDNN_LIBRARY
    NAMES cudnn
    PATHS
        /usr/local/cuda/lib64
        /usr/local/cuda/lib
        /usr/lib/x86_64-linux-gnu
        $ENV{CUDA_PATH}/lib/x64
        $ENV{CUDNN_PATH}/lib
    DOC "cuDNN library"
)

# Handle the REQUIRED argument and set CUDNN_FOUND
include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(CUDNN
    REQUIRED_VARS CUDNN_LIBRARY CUDNN_INCLUDE_DIR
)

# Set CUDNN_LIBRARIES and CUDNN_INCLUDE_DIRS
if(CUDNN_FOUND)
    set(CUDNN_LIBRARIES ${CUDNN_LIBRARY})
    set(CUDNN_INCLUDE_DIRS ${CUDNN_INCLUDE_DIR})
endif()

# Mark as advanced
mark_as_advanced(CUDNN_INCLUDE_DIR CUDNN_LIBRARY) 