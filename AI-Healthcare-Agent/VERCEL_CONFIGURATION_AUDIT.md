# Vercel Configuration Audit

## Root Cause

The Vercel deployment was failing with:

```
Property 'public' is not allowed
```

**Root cause:** The `vercel.json` file contained `"public": false` (line 7), which is **not a valid property** in the Vercel `vercel.json` schema. Vercel's configuration schema does not include a `public` property at the top level.

## Files Inspected

| File | Status |
|------|--------|
| `frontend/vercel.json` | **Modified** |
| `frontend/next.config.ts` | **Modified** |
| `frontend/package.json` | No changes needed |
| `frontend/.env.local.example` | No changes needed (reference only) |
| `render.yaml` | No changes needed (reference only) |
| `.github/` | No CI/CD files found |
| Root `vercel.json` | Does not exist |

## Files Modified

### 1. `frontend/vercel.json`

**Removed — invalid property:**
- `"public": false` — **ROOT CAUSE.** This property is not part of the Vercel schema. Vercel does not support a top-level `public` property in `vercel.json`.

**Removed — unnecessary (auto-detected by Vercel for Next.js):**
- `"framework": "nextjs"` — Vercel auto-detects Next.js from `package.json`
- `"buildCommand": "npm run build"` — Vercel auto-detects the Next.js build command
- `"outputDirectory": ".next"` — Vercel auto-detects the Next.js output directory

**Removed — duplicate configuration:**
- `"rewrites"` block — Rewrites are already configured in `next.config.ts` via `async rewrites()`. Having them in both places creates a conflict where the `vercel.json` version overrides the Next.js version on Vercel, but only the Next.js version applies during local development. This inconsistency is now resolved by keeping rewrites exclusively in `next.config.ts`, where they are environment-aware (`process.env.NEXT_PUBLIC_API_URL` with localhost fallback).

**Kept — valid properties:**
- `"installCommand": "npm ci"`
- `"regions": ["iad1"]`
- `"cleanUrls": true`
- `"trailingSlash": false`
- `"headers"` — security headers (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy)

### 2. `frontend/next.config.ts`

**Removed — incompatible with Vercel:**
- `output: "standalone"` — The `standalone` output mode is designed for **Docker self-hosting** deployments. On Vercel, Next.js uses its default output mode. Setting `output: "standalone"` causes Vercel to apply a non-standard build process, potentially breaking the deployment.

**Kept — all valid configuration:**
- `reactStrictMode: true`
- `experimental.optimizePackageImports`
- `images.remotePatterns` — correctly uses the modern `remotePatterns` API (no deprecated `images.domains`)
- `async rewrites()` — environment-aware rewrite to `NEXT_PUBLIC_API_URL` with localhost fallback

## Deployment Verification Checklist

- [x] `vercel.json` is valid JSON
- [x] No invalid properties remain (`public` removed)
- [x] No deprecated properties remain
- [x] No duplicate configuration (`rewrites` consolidated in `next.config.ts`)
- [x] `next.config.ts` uses native Next.js deployment mode (no `output: "standalone"`)
- [x] `images.remotePatterns` is correct (no deprecated `images.domains`)
- [x] API rewrites use `NEXT_PUBLIC_API_URL` env var with localhost fallback
- [x] No duplicate `vercel.json` files exist (only one at `frontend/vercel.json`)
- [x] All `NEXT_PUBLIC_*` env vars are documented in `.env.local.example`

## Environment Variables Required on Vercel

These should be set in the Vercel project dashboard:

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend API URL (e.g., `https://healthcare-backend.onrender.com/api/v1`) |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL (e.g., `wss://healthcare-backend.onrender.com/ws`) |
| `NEXT_PUBLIC_APP_URL` | Frontend URL (e.g., `https://your-app.vercel.app`) |
| `NEXT_PUBLIC_APP_NAME` | App name (e.g., `AI Healthcare Assistant`) |

## Final Configuration

### `frontend/vercel.json`
```json
{
  "installCommand": "npm ci",
  "regions": ["iad1"],
  "cleanUrls": true,
  "trailingSlash": false,
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "X-XSS-Protection", "value": "1; mode=block" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" }
      ]
    }
  ]
}
```

### `frontend/next.config.ts`
```ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  experimental: {
    optimizePackageImports: ["lucide-react", "recharts"],
  },
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "healthcare-backend.onrender.com" },
      { protocol: "http", hostname: "localhost" },
    ],
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/:path*`,
      },
    ];
  },
};

export default nextConfig;
```

## Conclusion

The next Vercel deployment should succeed. The deployment error was caused entirely by the invalid `"public": false` property in `vercel.json`, which has been removed. Additionally, `output: "standalone"` was removed from `next.config.ts` as it is incompatible with Vercel's native Next.js deployment pipeline.
