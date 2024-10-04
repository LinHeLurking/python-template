cmake_minimum_required(VERSION 3.20)
project(PythonExt LANGUAGES C CXX)

set(PYBIND11_FINDPYTHON ON)
find_package(pybind11 CONFIG REQUIRED)

file(REAL_PATH ${CMAKE_CURRENT_SOURCE_DIR}/../python_template PYTHON_ROOT)
message(STATUS "python source root: ${PYTHON_ROOT}")

function(add_pyext PYEXT_NAME)
    set(_OPTIONS)
    set(_SINGLE_VALUE_ARGS DESTINATION MODULE_NAME)
    set(_MULTI_VALUE_ARGS SOURCES)
    cmake_parse_arguments(PYEXT "${_OPTIONS}" "${_SINGLE_VALUE_ARGS}" "${_MULTI_VALUE_ARGS}" ${ARGN})
    if(NOT PYEXT_MODULE_NAME)
        set(PYEXT_MODULE_NAME ${PYEXT_NAME})
    endif()
    if(NOT PYEXT_SOURCES)
        message(FATAL_ERROR "Must provide sources for ${PYEXT_NAME}")
    endif()

    message(STATUS "building python extension: ${PYEXT_NAME}. sources: ${PYEXT_SOURCES}")
    pybind11_add_module(${PYEXT_NAME} MODULE ${PYEXT_SOURCES})
    target_compile_definitions(${PYEXT_NAME} PRIVATE MODULE_NAME=${PYEXT_MODULE_NAME})
    install(TARGETS _ext DESTINATION ${PYEXT_DESTINATION})
endfunction()

add_pyext(_ext DESTINATION ${PYTHON_ROOT} SOURCES ./greeter.cc ./greeter.h ./pybind.cc)