"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { createJob } from "@/services/jobService";
import { ApiError } from "@/lib/api";

export default function NewJobPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    title: "", department: "", description_raw: "",
    required_skills: "", preferred_skills: "", min_experience_years: "", education_level: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));
  const parseSkills = (s: string) => s.split(",").map((x) => x.trim()).filter(Boolean);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const job = await createJob({
        title: form.title,
        description_raw: form.description_raw,
        department: form.department || null,
        required_skills: parseSkills(form.required_skills),
        preferred_skills: parseSkills(form.preferred_skills),
        min_experience_years: form.min_experience_years ? Number(form.min_experience_years) : null,
        education_level: form.education_level || null,
      });
      router.push(`/jobs/${job.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create job");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold">New job</h1>
        <p className="text-sm text-muted-foreground">The description is embedded for semantic matching.</p>
      </div>
      <Card>
        <CardHeader><CardTitle>Details</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="title">Title</Label>
              <Input id="title" value={form.title} onChange={(e) => set("title", e.target.value)} required />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="dept">Department</Label>
              <Input id="dept" value={form.department} onChange={(e) => set("department", e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="desc">Description</Label>
              <Textarea id="desc" rows={6} value={form.description_raw} onChange={(e) => set("description_raw", e.target.value)} required />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="req">Required skills</Label>
                <Input id="req" placeholder="python, pytorch" value={form.required_skills} onChange={(e) => set("required_skills", e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="pref">Preferred skills</Label>
                <Input id="pref" placeholder="kubernetes" value={form.preferred_skills} onChange={(e) => set("preferred_skills", e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="exp">Min experience (years)</Label>
                <Input id="exp" type="number" min={0} value={form.min_experience_years} onChange={(e) => set("min_experience_years", e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="edu">Education level</Label>
                <Input id="edu" placeholder="bachelor" value={form.education_level} onChange={(e) => set("education_level", e.target.value)} />
              </div>
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <div className="flex gap-2">
              <Button type="submit" disabled={busy}>{busy ? "Creating…" : "Create job"}</Button>
              <Button type="button" variant="outline" onClick={() => router.back()}>Cancel</Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
