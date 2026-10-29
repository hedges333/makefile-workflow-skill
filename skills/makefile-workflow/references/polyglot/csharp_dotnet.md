# Polyglot Stack Guide: C# (.NET)

This manual details toolchains, test scaffolding, and database isolation for C# and .NET.

## 1. Detection Markers
- `*.csproj`, `*.sln`, `global.json`, `Directory.Build.props`

## 2. Standard Commands
- **Targeted Test**: `dotnet test --filter <FullyQualifiedName>`
- **Format**: `dotnet format --verify-no-changes`
- **Lint**: `dotnet build /warnaserror`

## 3. Boilerplate Test Scaffolding
If no test exists, create `tests/SmokeTests.cs` (xUnit):
```csharp
using Xunit;

namespace Tests;

public class SmokeTests
{
    [Fact]
    public void SmokeTestHarness()
    {
        Assert.True(true);
    }
}
```

## 4. Test Database Isolation
1. Use the Entity Framework Core In-Memory Database provider (`UseInMemoryDatabase("TestDb")`) or SQLite in-memory provider for unit tests.
2. For integration tests requiring real SQL Server or PostgreSQL engines, use Testcontainers for .NET.
3. Configure `appsettings.Testing.json` with local test connection strings. Never point to live servers.
