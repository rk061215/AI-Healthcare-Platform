import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const publicPaths = ["/", "/login", "/register"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public paths and static assets
  if (publicPaths.some((p) => pathname === p)) {
    return NextResponse.next();
  }

  // Allow auth API routes and static assets
  if (pathname.startsWith("/_next") || pathname.startsWith("/api") || pathname.startsWith("/images") || pathname === "/favicon.ico") {
    return NextResponse.next();
  }

  const authCookie = request.cookies.get("healthcare-auth")?.value;

  if (!authCookie) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  try {
    const parsed = JSON.parse(decodeURIComponent(authCookie));
    const state = parsed.state || parsed;
    const userRole = state?.user?.role;

    // Role-based redirects
    if (pathname.startsWith("/patient") && userRole !== "patient") {
      const loginUrl = new URL("/login", request.url);
      loginUrl.searchParams.set("redirect", pathname);
      return NextResponse.redirect(loginUrl);
    }

    if (pathname.startsWith("/doctor") && userRole !== "doctor") {
      const loginUrl = new URL("/login", request.url);
      loginUrl.searchParams.set("redirect", pathname);
      return NextResponse.redirect(loginUrl);
    }

    return NextResponse.next();
  } catch {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|images|icons).*)"],
};
