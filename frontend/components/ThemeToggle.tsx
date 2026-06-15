"use client";

import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";

function applyTheme(theme: "dark" | "light") {
  if (theme === "dark") {
    document.documentElement.classList.add("dark");
  } else {
    document.documentElement.classList.remove("dark");
  }
  localStorage.setItem("nexus-theme", theme);
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  useEffect(() => {
    const stored = localStorage.getItem("nexus-theme") as "dark" | "light" | null;
    const resolved = stored ?? "dark";
    setTheme(resolved);
    applyTheme(resolved);
  }, []);

  const toggle = () => {
    const next: "dark" | "light" = theme === "dark" ? "light" : "dark";
    setTheme(next);
    applyTheme(next);
  };

  return (
    <button
      onClick={toggle}
      aria-label="Toggle theme"
      className="flex h-8 w-8 items-center justify-center rounded-md border border-border bg-muted/50 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
    >
      {theme === "dark" ? <Sun size={14} /> : <Moon size={14} />}
    </button>
  );
}
