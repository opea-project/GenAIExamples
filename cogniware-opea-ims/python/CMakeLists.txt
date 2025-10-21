cmake_minimum_required(VERSION 3.18)

# Find required packages
find_package(Python3 3.8 REQUIRED COMPONENTS Interpreter Development)
find_package(pybind11 REQUIRED)
find_package(NumPy REQUIRED)
find_package(Torch REQUIRED)

# Add Python module
pybind11_add_module(msmartcompute_engine_python
    ${CMAKE_CURRENT_SOURCE_DIR}/src/msmartcompute_engine_python.cpp
)

# Set include directories
target_include_directories(msmartcompute_engine_python
    PRIVATE
    ${CMAKE_SOURCE_DIR}/include
    ${NumPy_INCLUDE_DIRS}
    ${Torch_INCLUDE_DIRS}
)

# Link libraries
target_link_libraries(msmartcompute_engine_python
    PRIVATE
    msmartcompute_engine
    ${Torch_LIBRARIES}
)

# Set output name
set_target_properties(msmartcompute_engine_python PROPERTIES
    OUTPUT_NAME "msmartcompute_engine"
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
)

# Install Python module
install(TARGETS msmartcompute_engine_python
    LIBRARY DESTINATION lib/python${Python3_VERSION_MAJOR}.${Python3_VERSION_MINOR}/site-packages
    RUNTIME DESTINATION bin
)

# Install Python package
install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/
    DESTINATION ${Python3_SITE_PACKAGES_DIR}/msmartcompute_engine
    FILES_MATCHING PATTERN "*.py"
) 