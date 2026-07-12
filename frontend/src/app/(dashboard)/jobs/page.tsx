"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, Briefcase } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { EmptyState } from "@/components/shared/EmptyState";
import { listJobs } from "@/services/jobService";
import type { Job } from "@/types/job";

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listJobs().then(setJobs).finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Jobs</h1>
          <p className="text-sm text-muted-foreground">Roles you're screening for.</p>
        </div>
        <Button asChild>
          <Link href="/jobs/new" className="flex items-center gap-2"><Plus className="h-4 w-4" /> New job</Link>
        </Button>
      </div>

      {loading ? (
        <div className="space-y-3">{[...Array(3)].map((_, i) => <Skeleton key={i} className="h-20" />)}</div>
      ) : jobs.length === 0 ? (
        <EmptyState
          icon={<Briefcase className="h-8 w-8" />}
          title="No jobs yet"
          description="Create a job posting to start uploading and ranking resumes."
          action={<Button asChild><Link href="/jobs/new">Create a job</Link></Button>}
        />
      ) : (
        <div className="grid gap-3">
          {jobs.map((job) => (
            <Link key={job.id} href={`/jobs/${job.id}`}>
              <Card className="transition-colors hover:border-primary/40">
                <CardContent className="flex items-center justify-between p-5">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium">{job.title}</h3>
                      <StatusBadge status={job.status} />
                    </div>
                    <p className="mt-0.5 text-sm text-muted-foreground">
                      {job.department || "No department"} · {job.required_skills.length} required skills
                    </p>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
