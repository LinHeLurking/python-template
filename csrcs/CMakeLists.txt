cmake_minimum_required(VERSION 3.20)
project(PythonExt LANGUAGES C CXX)

set(PYBIND11_FINDPYTHON ON)
find_package(pybind11 CONFIG REQUIRED)

set(SRC_SET pybind.cc greeter.h greeter.cc)
pybind11_add_module(_ext MODULE ${SRC_SET})
target_compile_definitions(_ext PRIVATE MODEUL_NAME=_ext)