# Polyglot Stack Guide: Scientific and Scripting (R, Julia, and Lua)

This guide covers detection markers, test and lint commands, and smoke test templates for R, Julia, and Lua.

## 1. R

Look for `DESCRIPTION`, `NAMESPACE`, `renv.lock`, or `*.R` files, then run these commands:

- Targeted Test: `Rscript -e "testthat::test_dir('tests')"` or `Rscript -e "devtools::test()"`
- Lint: `Rscript -e "lintr::lint_package()"`
- Format: `Rscript -e "styler::style_pkg()"`

If no test exists, create `tests/testthat/test-smoke.R`:

```R
test_that("smoke test harness runs", {
  expect_true(TRUE)
})
```

---

## 2. Julia

Look for `Project.toml`, `Manifest.toml`, or `*.jl` files, then run these commands:

- Targeted Test: `julia --project -e 'using Pkg; Pkg.test()'`
- Format: `julia --project -e 'using JuliaFormatter; format(".")'`
- Lint: `julia --project -e 'using JET; report_package()'`

If no test exists, create `test/runtests.jl`:

```julia
using Test

@testset "Smoke Test Harness" begin
    @test true
end
```

---

## 3. Lua

Look for `*.rockspec`, `busted.json`, or `*.lua` files, then run these commands:

- Targeted Test: `busted` or `lua test.lua`
- Format: `stylua --check .` (write mode: `stylua .`)
- Lint: `luacheck .`

If no test exists, create `spec/smoke_spec.lua`:

```lua
describe("Smoke Test Harness", function()
  it("runs cleanly", function()
    assert.is_true(true)
  end)
end)
```
