# Polyglot Stack Guide: Dart & Flutter

This manual details toolchains, test scaffolding, and specialized failure vaccines for Dart and Flutter.

## 1. Detection Markers
- `pubspec.yaml`, `pubspec.lock`, `analysis_options.yaml`

## 2. Standard Commands
- **Targeted Test**: `flutter test <path_to_test>` or `dart test <path_to_test>`
- **Format**: `dart format --output=none --set-exit-if-changed .`
- **Lint**: `dart analyze --fatal-infos --fatal-warnings`

## 3. Boilerplate Test Scaffolding
If no test exists, create `test/smoke_test.dart`:
```dart
import 'package:test/test.dart';

void main() {
  test('smoke test harness', () {
    expect(true, isTrue);
  });
}
```

## 4. Specialized Dart & Flutter Failure Vaccines

1. **Async & FakeAsync (`SCAR-TEST-23`)**:
   Always wrap asynchronous microtasks and timer tests in `fakeAsync` or pump widget frames explicitly.
2. **Completer Guarding (`SCAR-TEST-25`)**:
   Always check `if (!completer.isCompleted)` before calling `completer.complete()` inside callbacks.
3. **AST Visitor Cascades (`SCAR-DART-09`)**:
   When analyzing Dart AST nodes, check for cascade expressions before reading member offsets.
4. **Widget Disposal Teardown**:
   Always cancel streams, animations, and focus nodes in the `dispose()` lifecycle method.
