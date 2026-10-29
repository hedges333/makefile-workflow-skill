# Polyglot Stack Guide: Perl

This manual details toolchains, test scaffolding, and isolation conventions for Perl.

## 1. Detection Markers
- `Makefile.PL`, `Build.PL`, `cpanfile`, `dist.ini`, `META.json`, `*.pl`, `*.pm`

## 2. Standard Commands
- **Targeted Test**: `prove -lv t/<test_file>.t` (or `make test`)
- **Format**: `perltidy -b <file>`
- **Lint**: `perlcritic --severity 3 lib/`

## 3. Boilerplate Test Scaffolding
If no test exists, create `t/00-smoke.t`:
```perl
use strict;
use warnings;
use Test::More tests => 1;

ok(1, 'smoke test harness executes cleanly');
```

## 4. Test Database Isolation
1. Use `DBD::SQLite` with `:memory:` for fast, hermetic database tests.
2. Use `Test::MockDBI` to simulate database statements without connecting to real database servers.
3. Use `File::Temp` to create isolated scratch folders for file-based tests.
