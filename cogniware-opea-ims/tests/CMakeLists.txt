cmake_minimum_required(VERSION 3.18)

# Find GTest
find_package(GTest REQUIRED)

# Find required packages
find_package(Threads REQUIRED)

# Add test executable
add_executable(msmartcompute_engine_tests
    test_llm_inference_core.cpp
    test_dream_manager.cpp
    test_dream_agent.cpp
)

# Link libraries
target_link_libraries(msmartcompute_engine_tests
    PRIVATE
    msmartcompute_engine_cpp
    GTest::GTest
    GTest::Main
    Threads::Threads
)

# Add tests
add_test(NAME msmartcompute_engine_tests
         COMMAND msmartcompute_engine_tests)

# Set test properties
set_tests_properties(msmartcompute_engine_tests PROPERTIES
    ENVIRONMENT "LD_LIBRARY_PATH=${CMAKE_BINARY_DIR}/lib:$ENV{LD_LIBRARY_PATH}"
    TIMEOUT 300
)

# Unit tests
add_executable(unit_tests
    unit/model_manager_test.cpp
    unit/resource_manager_test.cpp
)

target_link_libraries(unit_tests
    PRIVATE
    msmartcompute_engine_cpp
    GTest::GTest
    GTest::Main
    Threads::Threads
)

# Integration tests
add_executable(integration_tests
    integration/model_client_test.cpp
)

target_link_libraries(integration_tests
    PRIVATE
    msmartcompute_engine_cpp
    GTest::GTest
    GTest::Main
    Threads::Threads
)

# Add tests to CTest
add_test(NAME unit_tests COMMAND msmartcompute_engine_tests --gtest_filter=*Test*)
add_test(NAME integration_tests COMMAND msmartcompute_engine_tests --gtest_filter=*Integration*)

# Set test properties
set_tests_properties(unit_tests PROPERTIES
    ENVIRONMENT "LD_LIBRARY_PATH=${CMAKE_BINARY_DIR}/lib:$ENV{LD_LIBRARY_PATH}"
    TIMEOUT 300
)

set_tests_properties(integration_tests PROPERTIES
    ENVIRONMENT "LD_LIBRARY_PATH=${CMAKE_BINARY_DIR}/lib:$ENV{LD_LIBRARY_PATH}"
    TIMEOUT 300
)

# Install test executables
install(TARGETS msmartcompute_engine_tests
    RUNTIME DESTINATION bin/tests
) 