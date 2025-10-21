# FindSpdlog.cmake
# Locates the spdlog library
#
# This module defines the following variables:
#   SPDLOG_FOUND - True if spdlog is found
#   SPDLOG_INCLUDE_DIRS - spdlog include directories
#   SPDLOG_LIBRARIES - spdlog libraries

# Try to find spdlog using pkg-config first
find_package(PkgConfig QUIET)
if(PKG_CONFIG_FOUND)
    pkg_check_modules(PC_SPDLOG QUIET spdlog)
endif()

# Find spdlog headers
find_path(SPDLOG_INCLUDE_DIR
    NAMES spdlog/spdlog.h
    PATHS
        ${PC_SPDLOG_INCLUDEDIR}
        ${PC_SPDLOG_INCLUDE_DIRS}
        /usr/include
        /usr/local/include
        /opt/local/include
        /sw/include
    DOC "spdlog include directory"
)

# Find spdlog library (spdlog is header-only, but some distributions provide a library)
find_library(SPDLOG_LIBRARY
    NAMES spdlog
    PATHS
        ${PC_SPDLOG_LIBDIR}
        ${PC_SPDLOG_LIBRARY_DIRS}
        /usr/lib
        /usr/local/lib
        /opt/local/lib
        /sw/lib
    DOC "spdlog library"
)

# Handle the REQUIRED argument and set SPDLOG_FOUND
include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(Spdlog
    REQUIRED_VARS SPDLOG_INCLUDE_DIR
)

# Set SPDLOG_LIBRARIES and SPDLOG_INCLUDE_DIRS
if(SPDLOG_FOUND)
    if(SPDLOG_LIBRARY)
        set(SPDLOG_LIBRARIES ${SPDLOG_LIBRARY})
    else()
        # spdlog is header-only, no library needed
        set(SPDLOG_LIBRARIES "")
    endif()
    set(SPDLOG_INCLUDE_DIRS ${SPDLOG_INCLUDE_DIR})
endif()

# Mark as advanced
mark_as_advanced(SPDLOG_INCLUDE_DIR SPDLOG_LIBRARY) 