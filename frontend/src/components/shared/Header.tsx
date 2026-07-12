"use client";

import { Moon, Sun, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { useTheme } from "@/hooks/useTheme";

/** Top bar with theme toggle and the signed-in user's identity. */
export function Header() {
  const { user, signOut } = useAuth();
  const { theme, toggle } = useTheme();

  return (
    <header className="flex h-14 items-center justify-between border-b bg-card px-6">
      <div />
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={toggle} aria-label="Toggle theme">
          {theme === "light" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
        </Button>
        {user && (
          <div className="flex items-center gap-3">
            <div className="text-right">
              <div className="text-sm font-medium leading-none">{user.full_name}</div>
              <div className="text-xs text-muted-foreground">{user.role}</div>
            </div>
            <Button variant="ghost" size="icon" onClick={() => void signOut()} aria-label="Sign out">
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>
    </header>
  );
}
