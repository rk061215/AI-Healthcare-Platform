import { describe, it, expect, beforeEach } from "vitest";
import { useUIStore } from "@/lib/store/ui-store";

describe("useUIStore", () => {
  beforeEach(() => {
    useUIStore.setState({
      sidebarOpen: false,
      sidebarCollapsed: false,
    });
  });

  it("should have initial state", () => {
    const state = useUIStore.getState();
    expect(state.sidebarOpen).toBe(false);
    expect(state.sidebarCollapsed).toBe(false);
  });

  it("toggleSidebar should toggle sidebarOpen", () => {
    expect(useUIStore.getState().sidebarOpen).toBe(false);
    useUIStore.getState().toggleSidebar();
    expect(useUIStore.getState().sidebarOpen).toBe(true);
    useUIStore.getState().toggleSidebar();
    expect(useUIStore.getState().sidebarOpen).toBe(false);
  });

  it("setSidebarOpen should set sidebarOpen", () => {
    useUIStore.getState().setSidebarOpen(true);
    expect(useUIStore.getState().sidebarOpen).toBe(true);
    useUIStore.getState().setSidebarOpen(false);
    expect(useUIStore.getState().sidebarOpen).toBe(false);
  });

  it("setSidebarCollapsed should set sidebarCollapsed", () => {
    useUIStore.getState().setSidebarCollapsed(true);
    expect(useUIStore.getState().sidebarCollapsed).toBe(true);
    useUIStore.getState().setSidebarCollapsed(false);
    expect(useUIStore.getState().sidebarCollapsed).toBe(false);
  });
});
