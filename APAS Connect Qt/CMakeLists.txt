cmake_minimum_required(VERSION 3.16)
project(APASConnectQt VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# For MSVC, add /Zc:__cplusplus
if(MSVC)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /Zc:__cplusplus")
endif()

# Find Qt6
find_package(Qt6 REQUIRED COMPONENTS Core Widgets Network)

# Enable Qt automoc, autorcc, autouic
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

# Source files
set(SOURCES
    main.cpp
    MainWindow.cpp
    SystemMonitor.cpp
    TrayIcon.cpp
    HttpServer.cpp
)

set(HEADERS
    MainWindow.h
    SystemMonitor.h
    TrayIcon.h
    HttpServer.h
)

# Add executable
add_executable(APASConnectQt ${SOURCES} ${HEADERS})

# Link Qt libraries
target_link_libraries(APASConnectQt Qt6::Core Qt6::Widgets Qt6::Network)

# Set properties
set_target_properties(APASConnectQt PROPERTIES
    WIN32_EXECUTABLE TRUE  # For Windows GUI app
)