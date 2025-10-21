# FindJsonCpp.cmake
# Locates the JsonCpp library
#
# This module defines the following variables:
#   JSONCPP_FOUND - True if JsonCpp is found
#   JSONCPP_INCLUDE_DIRS - JsonCpp include directories
#   JSONCPP_LIBRARIES - JsonCpp libraries

# Try to find JsonCpp using pkg-config first
find_package(PkgConfig QUIET)
if(PKG_CONFIG_FOUND)
    pkg_check_modules(PC_JSONCPP QUIET jsoncpp)
endif()

# Find JsonCpp headers
find_path(JSONCPP_INCLUDE_DIR
    NAMES json/json.h
    PATHS
        ${PC_JSONCPP_INCLUDEDIR}
        ${PC_JSONCPP_INCLUDE_DIRS}
        /usr/include
        /usr/local/include
        /opt/local/include
        /sw/include
    DOC "JsonCpp include directory"
)

# Find JsonCpp library
find_library(JSONCPP_LIBRARY
    NAMES jsoncpp json
    PATHS
        ${PC_JSONCPP_LIBDIR}
        ${PC_JSONCPP_LIBRARY_DIRS}
        /usr/lib
        /usr/local/lib
        /opt/local/lib
        /sw/lib
    DOC "JsonCpp library"
)

# Handle the REQUIRED argument and set JSONCPP_FOUND
include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(JsonCpp
    REQUIRED_VARS JSONCPP_LIBRARY JSONCPP_INCLUDE_DIR
)

# Set JSONCPP_LIBRARIES and JSONCPP_INCLUDE_DIRS
if(JSONCPP_FOUND)
    set(JSONCPP_LIBRARIES ${JSONCPP_LIBRARY})
    set(JSONCPP_INCLUDE_DIRS ${JSONCPP_INCLUDE_DIR})
endif()

# Mark as advanced
mark_as_advanced(JSONCPP_INCLUDE_DIR JSONCPP_LIBRARY) 