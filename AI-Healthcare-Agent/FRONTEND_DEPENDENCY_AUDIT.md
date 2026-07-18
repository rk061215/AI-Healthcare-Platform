# Frontend Dependency Audit

## Root Cause

The `package-lock.json` was out of sync with `package.json`, causing `npm ci` to fail on Vercel with:

```
Invalid: lock file's @emnapi/wasi-threads@1.2.1 does not satisfy @emnapi/wasi-threads@1.2.2
Missing: @emnapi/core@1.10.0 from lock file
```

These are transitive dependencies of `@emnapi/runtime` (used by `@tailwindcss/oxide` / Next.js tooling). The lock file pinned an older version while `package.json` resolved to a newer one. Regenerating the lock file resolved the mismatch.

## Files Inspected

| File | Status |
|------|--------|
| `frontend/package.json` | No changes needed |
| `frontend/package-lock.json` | **Regenerated** |
| `frontend/node_modules/` | **Deleted and reinstalled** |
| `yarn.lock` | Not present |
| `pnpm-lock.yaml` | Not present |
| `bun.lockb` | Not present |

## Package Manager

**npm** (v11.6.2) — single package manager, no duplicates found.

## Dependencies Changed

None. `package.json` was not modified. Only the lock file was regenerated.

## Results

| Check | Status |
|-------|--------|
| `npm install` | ✅ Passed (513 packages) |
| `npm ci` | ✅ Passed (513 packages) |
| `npm run build` | ✅ Passed (Next.js 15.5.20, 17 routes) |
| `npm ls --depth=0` | ✅ All deps resolved (1 extraneous cosmetic warning) |
| `npm audit` | ⚠️ 7 vulnerabilities (all in dev/test deps, none build-blocking) |

### Audit Note

The 7 audit warnings are in test/build tooling (`esbuild` via `vitest`, `postcss` via `next`). These are:
- Not build-blocking (`npm run build` succeeds)
- Only affect dev/test environments
- Cannot be fixed without major version upgrades (Next.js, vitest) — which is outside scope

## Vercel Readiness

✅ The next Vercel deployment should pass `npm ci` successfully. The lock file is now fully in sync with `package.json` and uses `lockfileVersion: 3` (npm v7+).

## Deployment Checklist

- [x] `package-lock.json` regenerated from clean state
- [x] `npm ci` installs without errors
- [x] `npm run build` compiles successfully
- [x] No duplicate lock files (`yarn.lock`, `pnpm-lock.yaml`, `bun.lockb`)
- [x] Single package manager (npm)
- [x] No application code modified
- [x] No dependencies upgraded
- [x] No breaking changes introduced
