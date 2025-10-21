add_executable(model_client_example model_client_example.cpp)

target_link_libraries(model_client_example
    PRIVATE
    msmartcompute_engine_cpp
    spdlog::spdlog
)

install(TARGETS model_client_example
    RUNTIME DESTINATION bin
) 