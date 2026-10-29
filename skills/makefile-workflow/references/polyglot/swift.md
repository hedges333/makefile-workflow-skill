# Polyglot Stack Guide: Swift

This manual details toolchains, test scaffolding, and isolation conventions for Swift.

## 1. Detection Markers
- `Package.swift`, `*.xcodeproj`, `*.xcworkspace`

## 2. Standard Commands
- **Targeted Test**: `swift test --filter <TestClass>`
- **Format**: `swiftformat --lint .`
- **Lint**: `swiftlint`

## 3. Boilerplate Test Scaffolding
If no test exists, create `Tests/SmokeTests/SmokeTests.swift`:
```swift
import XCTest

final class SmokeTests: XCTestCase {
    func testSmokeHarness() {
        XCTAssertTrue(true)
    }
}
```

## 4. Test Isolation
1. For CoreData or SwiftData tests, instantiate persistent stores with `inMemory` type so no data is written to disk.
2. Abstract network requests behind protocols and use mock URL sessions (`URLProtocol` stubs).
3. Use `FileManager.default.temporaryDirectory` for temporary file operations.
