# Polyglot Stack Guide: JVM (Java, Kotlin & Scala)

This manual details toolchains, test scaffolding, and database isolation for JVM languages.

## 1. Detection Markers
- **Java / Kotlin**: `pom.xml`, `build.gradle`, `build.gradle.kts`, `settings.gradle`
- **Scala**: `build.sbt`

## 2. Standard Commands
- **Maven**: `mvn test -Dtest=<ClassName>`
- **Gradle**: `./gradlew test --tests <ClassName>`
- **Scala (SBT)**: `sbt "testOnly <ClassName>"`
- **Format / Lint**:
  - Java: `mvn spotless:check` or `./gradlew checkstyleMain`
  - Kotlin: `./gradlew ktlintCheck` or `./gradlew detekt`
  - Scala: `sbt scalafmtCheck`

## 3. Boilerplate Test Scaffolding

### Java (`src/test/java/com/example/SmokeTest.java`):
```java
package com.example;

import static org.junit.jupiter.api.Assertions.assertTrue;
import org.junit.jupiter.api.Test;

class SmokeTest {
    @Test
    void testSmokeHarness() {
        assertTrue(true);
    }
}
```

### Kotlin (`src/test/kotlin/com/example/SmokeTest.kt`):
```kotlin
package com.example

import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class SmokeTest {
    @Test
    fun testSmokeHarness() {
        assertTrue(true)
    }
}
```

### Scala (`src/test/scala/com/example/SmokeTest.scala`):
```scala
package com.example

import org.scalatest.funsuite.AnyFunSuite

class SmokeTest extends AnyFunSuite {
  test("smoke test harness") {
    assert(true)
  }
}
```

## 4. Test Database Isolation
1. Use an embedded H2 database (`jdbc:h2:mem:testdb;DB_CLOSE_DELAY=-1`) for fast unit tests.
2. For integration tests, use Testcontainers with ephemeral Docker instances.
3. Use Mockito or MockK to isolate business logic from database repositories.
