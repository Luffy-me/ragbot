"use client";

import { useTheme } from "next-themes";

import { AuthGate } from "@/components/auth-gate";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";

function SettingsPageInner() {
  const { user } = useAuth();
  const { theme, setTheme } = useTheme();

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-2xl space-y-6 px-4 py-6">
        <div>
          <h1 className="text-xl font-semibold">Settings</h1>
          <p className="text-sm text-muted-foreground">Account and appearance preferences.</p>
        </div>

        <section className="space-y-3 rounded-xl border border-border bg-card p-5">
          <h2 className="font-medium">Account</h2>
          <div className="text-sm">
            <p>
              <span className="text-muted-foreground">Email:</span> {user?.email}
            </p>
            <p className="capitalize">
              <span className="text-muted-foreground">Role:</span> {user?.role}
            </p>
          </div>
        </section>

        <section className="space-y-3 rounded-xl border border-border bg-card p-5">
          <h2 className="font-medium">Appearance</h2>
          <p className="text-sm text-muted-foreground">Choose light, dark, or system theme.</p>
          <div className="flex flex-wrap gap-2">
            {(["light", "dark", "system"] as const).map((value) => (
              <Button
                key={value}
                variant={theme === value ? "default" : "outline"}
                onClick={() => setTheme(value)}
                className="capitalize"
              >
                {value}
              </Button>
            ))}
          </div>
        </section>
      </div>
    </AppShell>
  );
}

export default function SettingsPage() {
  return (
    <AuthGate>
      <SettingsPageInner />
    </AuthGate>
  );
}
