"use client";

import Link from "next/link";
import { Users } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

export default function AdminHome() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Admin</h1>
        <p className="text-sm text-muted-foreground">Manage users and roles.</p>
      </div>
      <Link href="/admin/users">
        <Card className="transition-colors hover:border-primary/40">
          <CardContent className="flex items-center gap-3 p-5">
            <Users className="h-5 w-5 text-muted-foreground" />
            <div>
              <p className="font-medium">Users</p>
              <p className="text-sm text-muted-foreground">View users and change roles.</p>
            </div>
          </CardContent>
        </Card>
      </Link>
    </div>
  );
}
