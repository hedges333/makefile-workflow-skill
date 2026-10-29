# Polyglot Stack Guide: PowerShell

This manual details toolchains, test scaffolding, and isolation conventions for PowerShell.

## 1. Detection Markers
- `*.ps1`, `*.psm1`, `*.psd1`

## 2. Standard Commands
- **Targeted Test**: `pwsh -Command "Invoke-Pester -Path <path> -Output Detailed"`
- **Lint**: `pwsh -Command "Invoke-ScriptAnalyzer -Path . -Recurse -EnableExit"`

## 3. Boilerplate Test Scaffolding
If no test exists, create `tests/Smoke.Tests.ps1`:
```powershell
Describe 'Smoke Test Harness' {
    It 'Runs successfully' {
        $true | Should -Be $true
    }
}
```

## 4. Test Isolation
1. Use Pester's `Mock` command to mock external cmdlets (such as `Invoke-RestMethod` or `Send-MailMessage`).
2. Use temporary PSDrives (`New-PSDrive -Name 'TestEnv' -PSProvider FileSystem -Root (New-TemporaryFile).Directory`) for file tests.
3. Clean up all temporary files and mocked variables in the `AfterAll` block.
