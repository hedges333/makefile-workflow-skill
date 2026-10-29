# Polyglot Stack Guide: PHP

This manual details toolchains, test scaffolding, and database isolation for PHP.

## 1. Detection Markers
- `composer.json`, `composer.lock`, `phpunit.xml`, `phpunit.xml.dist`

## 2. Standard Commands
- **Targeted Test**: `vendor/bin/phpunit --filter <test>` or `vendor/bin/pest <path>`
- **Format**: `vendor/bin/php-cs-fixer fix --dry-run --diff`
- **Lint**: `vendor/bin/phpstan analyse --level=max`

## 3. Boilerplate Test Scaffolding
If no test exists, create `tests/SmokeTest.php`:
```php
<?php

namespace Tests;

use PHPUnit\Framework\TestCase;

class SmokeTest extends TestCase
{
    public function testSmokeHarness(): void
    {
        $this->assertTrue(true);
    }
}
```

## 4. Test Database Isolation
1. Ensure `.env.testing` is configured with `DB_CONNECTION=sqlite` and `DB_DATABASE=:memory:`.
2. Wrap database tests in transaction traits (e.g. `RefreshDatabase` or `DatabaseTransactions`).
3. Never execute `php artisan migrate` without checking that `APP_ENV=testing`.
