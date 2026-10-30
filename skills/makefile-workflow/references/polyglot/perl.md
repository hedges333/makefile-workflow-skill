# Polyglot Stack Guide: Perl

This guide covers detection markers, test and lint commands, smoke test templates, and isolation rules for Perl.

## 1. Detection Markers

Look for these files when scanning a Perl distribution:

- `Makefile.PL`, `Build.PL`, `cpanfile`, `dist.ini`, `META.json`, `*.pl`, `*.pm`

## 2. Standard Commands

Run these commands inside the Perl distribution directory:

- Targeted Test: `prove -lv t/<test_file>.t` or `make test`
- Format: `perltidy -b <file>`
- Lint: `perlcritic --severity 3 lib/`

## 3. Smoke Test Template

If no test exists, create `t/00-smoke.t`:

```perl
use strict;
use warnings;
use Test::More tests => 1;

ok(1, 'smoke test harness runs cleanly');
```

## 4. Test Database and File Isolation

Follow three isolation rules in Perl tests:

1. Use `DBD::SQLite` with `:memory:` for unit database tests.
2. Simulate SQL statements with `Test::MockDBI` when testing without a database server.
3. Create temporary test directories with `File::Temp` (`tempdir(CLEANUP => 1)`).
