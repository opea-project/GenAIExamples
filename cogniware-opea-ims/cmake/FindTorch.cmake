# FindTorch.cmake
# Finds the Torch library
#
# This will define the following variables:
#
#   Torch_FOUND        - True if the system has Torch
#   Torch_INCLUDE_DIRS - Torch include directory
#   Torch_LIBRARIES    - Torch libraries
#   Torch_VERSION      - Torch version

include(FindPackageHandleStandardArgs)

# Try to find Torch using Python
execute_process(
    COMMAND ${Python3_EXECUTABLE} -c "import torch; print(torch.__version__)"
    OUTPUT_VARIABLE Torch_VERSION
    OUTPUT_STRIP_TRAILING_WHITESPACE
    RESULT_VARIABLE Torch_FOUND
)

if(Torch_FOUND EQUAL 0)
    # Get Torch include directory
    execute_process(
        COMMAND ${Python3_EXECUTABLE} -c "import torch; print(torch.utils.cmake_prefix_path)"
        OUTPUT_VARIABLE Torch_CMAKE_PREFIX_PATH
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )

    # Get Torch library directory
    execute_process(
        COMMAND ${Python3_EXECUTABLE} -c "import torch; print(torch.utils.cmake_prefix_path + '/lib')"
        OUTPUT_VARIABLE Torch_LIBRARY_DIR
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )

    # Set include directories
    set(Torch_INCLUDE_DIRS ${Torch_CMAKE_PREFIX_PATH}/include)

    # Find libraries
    find_library(Torch_LIBRARIES
        NAMES torch torch_cpu torch_cuda
        PATHS ${Torch_LIBRARY_DIR}
        NO_DEFAULT_PATH
    )

    # If libraries not found in the first location, try site-packages
    if(NOT Torch_LIBRARIES)
        execute_process(
            COMMAND ${Python3_EXECUTABLE} -c "import torch; import os; print(os.path.join(os.path.dirname(torch.__file__), 'lib'))"
            OUTPUT_VARIABLE Torch_SITE_PACKAGES_LIB
            OUTPUT_STRIP_TRAILING_WHITESPACE
        )
        find_library(Torch_LIBRARIES
            NAMES torch torch_cpu torch_cuda
            PATHS ${Torch_SITE_PACKAGES_LIB}
            NO_DEFAULT_PATH
        )
    endif()

    # If still not found, try the default system paths
    if(NOT Torch_LIBRARIES)
        find_library(Torch_LIBRARIES
            NAMES torch torch_cpu torch_cuda
        )
    endif()
endif()

find_package_handle_standard_args(Torch
    REQUIRED_VARS Torch_INCLUDE_DIRS Torch_LIBRARIES
    VERSION_VAR Torch_VERSION
)

mark_as_advanced(Torch_INCLUDE_DIRS Torch_LIBRARIES Torch_VERSION) 