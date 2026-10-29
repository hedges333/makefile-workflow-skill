# Polyglot Stack Guide: Scientific & Scripting (R, Julia & Lua)

This manual details toolchains, test scaffolding, and isolation conventions for R, Julia, and Lua.

## 1. R

### Detection Markers
- `DESCRIPTION`, `NAMESPACE`, `renv.lock`, `*.R`

### Standard Commands
- **Test**: `Rscript -e "testthat::test_dir('tests')"` or `Rscript -e "devtools::test()"`
- **Lint**: `Rscript -e "lintr::lint_package()"`
- **Format**: `Rscript -e "styler::style_pkg()"`

### Boilerplate Test Scaffolding (`tests/testthat/test-smoke.R`):
```R
test_that("smoke test harness runs", {
  expect_true(TRUE)
})
```

---

## 2. Julia

### Detection Markers
- `Project.toml`, `Manifest.toml`, `*.jl`

### Standard Commands
- **Test**: `julia --project -e 'using Pkg; Pkg.test()'`
- **Format**: `julia --project -e 'using JuliaFormatter; format(".")'`
- **Lint**: `julia --project -e 'using JET; report_package()'`

### Boilerplate Test Scaffolding (`test/runtests.jl`):
```julia
using Test

@testset "Smoke Test Harness" begin
    @test true
end
```

---

## 3. Lua

### Detection Markers
- `*.rockspec`, `busted.json`, `*.lua`

### Standard Commands
- **Test**: `busted` or `lua test.lua`
- **Format**: `stylua --check .` (write: `stylua .`)
- **Lint**: `luacheck .`

### Boilerplate Test Scaffolding (`spec/smoke_spec.lua`):
```lua
describe("Smoke Test Harness", function()
  it("runs successfully", function()
    assert.is_true(true)
  end)
end)
```
