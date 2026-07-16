"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Activity,
  Calendar,
  ChevronLeft,
  ChevronRight,
  FileText,
  MessageSquare,
  Pill,
  AlertTriangle,
  LayoutDashboard,
  LogOut,
  Menu,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Avatar } from "@/components/ui/avatar";
import { ThemeToggle } from "@/components/shared/ThemeToggle";
import { useAuthStore } from "@/lib/store/auth-store";
import { useUIStore } from "@/lib/store/ui-store";
import { authService } from "@/services/auth";

const navItems = [
  { href: "/patient/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/patient/medicines", label: "My Medicines", icon: Pill },
  { href: "/patient/reports", label: "Reports", icon: FileText },
  { href: "/patient/chat", label: "AI Chat", icon: MessageSquare },
  { href: "/patient/appointments", label: "Appointments", icon: Calendar },
  { href: "/patient/emergency", label: "Emergency", icon: AlertTriangle },
];

export default function PatientLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuthStore();
  const { sidebarOpen, sidebarCollapsed, toggleSidebar, setSidebarOpen, setSidebarCollapsed } = useUIStore();

  useEffect(() => {
    if (!isAuthenticated || user?.role !== "patient") {
      router.push("/login");
    }
  }, [isAuthenticated, user, router]);

  if (!isAuthenticated) return null;

  const handleLogout = async () => {
    const refreshToken = useAuthStore.getState().refreshToken;
    if (refreshToken) {
      try {
        await authService.logout(refreshToken);
      } catch {
        // Proceed with local logout even if API call fails
      }
    }
    logout();
    router.push("/login");
  };

  return (
    <div className="flex min-h-screen bg-background">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex flex-col border-r bg-sidebar text-sidebar-foreground transition-all duration-300 lg:static",
          sidebarCollapsed ? "w-16" : "w-64",
          sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0",
        )}
      >
        {/* Logo */}
        <div className={cn("flex h-14 items-center border-b border-sidebar-accent px-4", sidebarCollapsed && "justify-center")}>
          <Activity className="h-6 w-6 shrink-0 text-primary" />
          {!sidebarCollapsed && (
            <span className="ml-3 font-semibold">HealthAI</span>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 p-2">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setSidebarOpen(false)}
              className={cn(
                "flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors hover:bg-sidebar-accent",
                sidebarCollapsed && "justify-center px-2",
              )}
            >
              <item.icon className="h-5 w-5 shrink-0" />
              {!sidebarCollapsed && <span className="ml-3">{item.label}</span>}
            </Link>
          ))}
        </nav>

        {/* User section */}
        <div className="border-t border-sidebar-accent p-2">
          <div className={cn("flex items-center gap-3 rounded-lg px-3 py-2", sidebarCollapsed && "justify-center")}>
            <Avatar fallback={user?.full_name?.charAt(0)} />
            {!sidebarCollapsed && (
              <div className="flex-1 overflow-hidden">
                <p className="text-sm font-medium truncate">{user?.full_name}</p>
                <p className="text-xs text-sidebar-foreground/60 truncate">{user?.email}</p>
              </div>
            )}
          </div>
          <button
            onClick={handleLogout}
            className={cn(
              "mt-1 flex w-full items-center rounded-lg px-3 py-2 text-sm text-sidebar-foreground/60 transition-colors hover:bg-sidebar-accent hover:text-sidebar-foreground",
              sidebarCollapsed && "justify-center",
            )}
          >
            <LogOut className="h-5 w-5 shrink-0" />
            {!sidebarCollapsed && <span className="ml-3">Sign Out</span>}
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex flex-1 flex-col">
        {/* Top bar */}
        <header className="flex h-14 items-center gap-4 border-b bg-background px-4 lg:px-6">
          <button
            onClick={toggleSidebar}
            className="rounded-lg p-2 text-muted-foreground hover:bg-accent lg:hidden"
          >
            {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>

          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="hidden rounded-lg p-2 text-muted-foreground hover:bg-accent lg:block"
          >
            {sidebarCollapsed ? (
              <ChevronRight className="h-5 w-5" />
            ) : (
              <ChevronLeft className="h-5 w-5" />
            )}
          </button>

          <div className="flex-1" />

          <ThemeToggle />
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto p-4 lg:p-6">{children}</main>
      </div>
    </div>
  );
}
