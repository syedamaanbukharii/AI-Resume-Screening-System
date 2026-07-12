"use client";

import { useEffect, useState } from "react";

/** Toggle and persist a light/dark theme via the `dark` class on <html>. */
export function useTheme() {
  const [theme, setTheme] = useState<"light" | "dark">("light");

  useEffect(() => {
    const stored = (window.localStorage.getItem("rs_theme") as "light" | "dark") || "light";
    setTheme(stored);
    document.documentElement.classList.toggle("dark", stored === "dark");
  }, []);

  const toggle = () => {
    const next = theme === "light" ? "dark" : "light";
    setTheme(next);
    window.localStorage.setItem("rs_theme", next);
    document.documentElement.classList.toggle("dark", next === "dark");
  };

  return { theme, toggle };
}
