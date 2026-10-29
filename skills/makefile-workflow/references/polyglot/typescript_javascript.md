# Polyglot Stack Guide: TypeScript & JavaScript

This manual details toolchains, test scaffolding, and database isolation for TypeScript and Node.js JavaScript.

## 1. Detection Markers
- `package.json`, `tsconfig.json`, `pnpm-lock.yaml`, `yarn.lock`, `package-lock.json`

## 2. Standard Commands
- **Targeted Test (TypeScript)**: `npm test` or `npx vitest run <path>` or `npx jest <path>`
- **Targeted Test (Native Node.js)**: `node --test`
- **Format**: `npx prettier --write .` (check: `npx prettier --check .`)
- **Lint**: `npx eslint .`

## 3. Boilerplate Test Scaffolding
If no test directory exists, create `tests/smoke.test.ts` (or `tests/smoke.test.js`):

### TypeScript (`tests/smoke.test.ts`):
```typescript
import { describe, expect, it } from 'vitest';

describe('Smoke Test Harness', () => {
  it('runs successfully', () => {
    expect(true).toBe(true);
  });
});
```

### Native Node.js JavaScript (`tests/smoke.test.js`):
```javascript
const test = require('node:test');
const assert = require('node:assert');

test('smoke test harness', () => {
  assert.strictEqual(true, true);
});
```

## 4. Test Database Isolation
1. Ensure `NODE_ENV=test` is set in all test commands.
2. Use in-memory SQLite (`better-sqlite3` `:memory:`) or local Docker test instances.
3. Stub external HTTP calls using `msw` (Mock Service Worker) or `nock`.
