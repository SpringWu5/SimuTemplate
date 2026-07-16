file(GLOB sources 
     ${CMAKE_CURRENT_SOURCE_DIR}/**/*.cc 
     ${CMAKE_CURRENT_SOURCE_DIR}/**/**/*.cc 
     ${CMAKE_CURRENT_SOURCE_DIR}/**/*.cpp)

add_library(SimuTemplateLib STATIC
            ${sources})

target_include_directories(SimuTemplateLib PUBLIC
                           ${PROJECT_SOURCE_DIR}/include
                           ${ROOT_INCLUDE_DIRS})

target_link_libraries(SimuTemplateLib PUBLIC
                      ${Geant4_LIBRARIES}
                      ${ROOT_LIBRARIES}
                      spdlog::spdlog
                      yaml-cpp)
