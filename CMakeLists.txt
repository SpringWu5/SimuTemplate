cmake_minimum_required(VERSION 3.8 FATAL_ERROR)
project(SimuTemplate)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED on)

set(CMAKE_CXX_FLAGS_DEBUG "-g -DDEBUG -Wall")
set(CMAKE_CXX_FLAGS_RELEASE "-O3")


#----------------------------------------------------------------------------
# Find Geant4 package, activating all available UI and Vis drivers by default
# You can set WITH_GEANT4_UIVIS to OFF via the command line or ccmake/cmake-gui
# to build a batch mode only executable
#
option(WITH_GEANT4_UIVIS "Enable Geant4 UI and Visualization" ON)
if(WITH_GEANT4_UIVIS)
    find_package(Geant4 REQUIRED ui_all vis_all)
else()
    find_package(Geant4 REQUIRED)
endif()
include(${Geant4_USE_FILE})

#----------------------------------------------------------------------------
# Find ROOT (required package)
#
find_package(ROOT REQUIRED COMPONENTS Geom TMVA MathMore)
if(NOT ROOT_FOUND)
    message(FATAL_ERROR "Can not find ROOT!")
endif()

# Find packages used in the project
find_package(yaml-cpp REQUIRED)
find_package(spdlog REQUIRED)

# nlohmann_json (header-only, vendored with Geant4/ROOT include paths usually)
find_package(nlohmann_json 3.2.0 QUIET)

# source directory
add_subdirectory(src)

# executable
add_executable(SimuTemplate ${PROJECT_SOURCE_DIR}/main.cc)

if(nlohmann_json_FOUND)
    target_link_libraries(SimuTemplate PRIVATE nlohmann_json::nlohmann_json)
endif()

target_link_libraries(SimuTemplate PRIVATE SimuTemplateLib)

#----------------------------------------------------------------------------
# Install the executable to 'bin' directory under CMAKE_INSTALL_PREFIX
#
install(TARGETS SimuTemplate DESTINATION ${CMAKE_INSTALL_PREFIX})
