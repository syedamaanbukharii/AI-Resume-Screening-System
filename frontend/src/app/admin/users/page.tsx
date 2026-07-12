"use client";

import { useEffect, useState } from "react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { apiFetch } from "@/lib/api";
import type { User } from "@/types/auth";

export default function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<User[]>("/api/v1/users").then(setUsers).finally(() => setLoading(false));
  }, []);

  const changeRole = async (id: string, role: string) => {
    const updated = await apiFetch<User>(`/api/v1/users/${id}/role`, { method: "PUT", body: JSON.stringify({ role }) });
    setUsers((prev) => prev.map((u) => (u.id === id ? updated : u)));
  };

  if (loading) return <Skeleton className="h-64" />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Users</h1>
        <p className="text-sm text-muted-foreground">{users.length} user(s).</p>
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Email</TableHead>
            <TableHead>Active</TableHead>
            <TableHead className="w-40">Role</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {users.map((u) => (
            <TableRow key={u.id}>
              <TableCell className="font-medium">{u.full_name}</TableCell>
              <TableCell className="text-muted-foreground">{u.email}</TableCell>
              <TableCell>{u.is_active ? <StatusBadge status="active" /> : <StatusBadge status="closed" />}</TableCell>
              <TableCell>
                <Select value={u.role} onChange={(e) => void changeRole(u.id, e.target.value)} className="w-32">
                  <option value="recruiter">recruiter</option>
                  <option value="admin">admin</option>
                </Select>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
