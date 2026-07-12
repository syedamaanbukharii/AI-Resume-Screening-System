"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/useAuth";
import { apiFetch } from "@/lib/api";

export default function SettingsPage() {
  const { user, refresh } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [saved, setSaved] = useState(false);

  const save = async () => {
    await apiFetch("/api/v1/users/me", { method: "PUT", body: JSON.stringify({ full_name: fullName }) });
    await refresh();
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <h1 className="text-xl font-semibold">Settings</h1>
      <Card>
        <CardHeader><CardTitle>Profile</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="name">Full name</Label>
            <Input id="name" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label>Email</Label>
            <Input value={user?.email ?? ""} disabled />
          </div>
          <div className="flex items-center gap-3">
            <Button onClick={() => void save()}>Save changes</Button>
            {saved && <span className="text-sm text-success">Saved</span>}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
