# FindNumPy.cmake
# Finds the NumPy library
#
# This will define the following variables:
#
#   NumPy_FOUND        - True if the system has NumPy
#   NumPy_INCLUDE_DIR  - NumPy include directory
#   NumPy_VERSION      - NumPy version

include(FindPackageHandleStandardArgs)

# Try to find NumPy using Python
execute_process(
    COMMAND ${Python3_EXECUTABLE} -c "import numpy; print(numpy.get_include())"
    OUTPUT_VARIABLE NumPy_INCLUDE_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

# Get NumPy version
execute_process(
    COMMAND ${Python3_EXECUTABLE} -c "import numpy; print(numpy.__version__)"
    OUTPUT_VARIABLE NumPy_VERSION
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

find_package_handle_standard_args(NumPy
    REQUIRED_VARS NumPy_INCLUDE_DIR
    VERSION_VAR NumPy_VERSION
)

mark_as_advanced(NumPy_INCLUDE_DIR NumPy_VERSION) 