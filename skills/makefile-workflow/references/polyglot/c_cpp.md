# Polyglot Stack Guide: C & C++

This manual details toolchains, test scaffolding, and isolation conventions for C and C++.

## 1. Detection Markers
- `CMakeLists.txt`, `meson.build`, `Makefile`, `vcpkg.json`, `conanfile.txt`, `*.c`, `*.cpp`, `*.h`, `*.hpp`

## 2. Standard Commands
- **Targeted Test**: `ctest -R <test_regex> --output-on-failure` or `make test`
- **Format**: `clang-format --dry-run -Werror $(find src -name '*.c' -o -name '*.cpp')`
- **Lint**: `clang-tidy -p build/ <source_file>` or `cppcheck --error-exitcode=1 src/`

## 3. Boilerplate Test Scaffolding

### C Boilerplate (`tests/smoke_test.c`):
```c
#include <assert.h>

int main(void) {
    assert(1 == 1);
    return 0;
}
```

### C++ Boilerplate (`tests/smoke_test.cpp`):
```cpp
#include <cassert>

int main() {
    assert(true);
    return 0;
}
```

## 4. Test Isolation
1. Use abstract base classes or function pointer tables to mock hardware devices and external network sockets.
2. In unit tests, avoid writing directly to `/tmp`; create unique paths using `mkdtemp()` or `std::filesystem::temp_directory_path()`.
3. Use AddressSanitizer (`-fsanitize=address`) and UndefinedBehaviorSanitizer during test builds to catch memory corruption early.
