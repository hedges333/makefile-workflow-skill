# Polyglot Stack Guide: C and C++

This guide covers detection markers, test and lint commands, smoke test templates, and isolation rules for C and C++.

## 1. Detection Markers

Look for these files when scanning a C or C++ subproject:

- `CMakeLists.txt`, `meson.build`, `Makefile`, `vcpkg.json`, `conanfile.txt`, `*.c`, `*.cpp`, `*.h`, `*.hpp`

## 2. Standard Commands

Run these commands inside the C or C++ subproject directory:

- Targeted Test: `ctest -R <test_regex> --output-on-failure` or `make test`
- Format: `clang-format --dry-run -Werror $(find src -name '*.c' -o -name '*.cpp')`
- Lint: `clang-tidy -p build/ <source_file>` or `cppcheck --error-exitcode=1 src/`

## 3. Smoke Test Templates

If no unit test exists, create `tests/smoke_test.c` or `tests/smoke_test.cpp`.

### C (`tests/smoke_test.c`)

```c
#include <assert.h>

int main(void) {
    assert(1 == 1);
    return 0;
}
```

### C++ (`tests/smoke_test.cpp`)

```cpp
#include <cassert>

int main() {
    assert(true);
    return 0;
}
```

## 4. Test Isolation and Memory Safety

Follow three safety rules in C and C++ tests:

1. Use function pointer tables or abstract interfaces to stub hardware devices and network sockets.
2. Do not write to fixed paths under `/tmp`. Create unique scratch directories with `mkdtemp()` or `std::filesystem::temp_directory_path()`.
3. Compile test targets with `-fsanitize=address,undefined` when supported to catch memory errors early.
