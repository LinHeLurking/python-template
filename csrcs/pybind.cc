#include "greeter.h"
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#ifndef MODULE_NAME
#define MODULE_NAME _ext
#endif

#define __STR(x) #x
#define STR(x) __STR(x)

namespace py = pybind11;

PYBIND11_MODULE(MODULE_NAME, m) {
  m.doc() = "Sample pybind11 C++ extension";
  py::class_<Greeter>(m, "Greeter")
      .def(py::init<>())
      .def("simple_greet", &Greeter::SimpleGreet)
      .def("complex_greet", &Greeter::ComplexGreet);
}
