"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { DropZone } from "@/components/upload/DropZone";
import { UploadRow } from "@/components/upload/UploadRow";
import { Button } from "@/components/ui/button";
import { uploadResumes } from "@/services/candidateService";
import type { UploadResult } from "@/types/candidate";

export default function UploadPage() {
  const { id } = useParams<{ id: string }>();
  const [results, setResults] = useState<UploadResult[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onFiles = async (files: File[]) => {
    setBusy(true);
    setError(null);
    try {
      const res = await uploadResumes(id, files);
      setResults((prev) => [...res, ...prev]);
    } catch {
      setError("Upload failed. Check file types and size (max 20 MB).");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Upload resumes</h1>
          <p className="text-sm text-muted-foreground">Each resume is parsed and embedded in the background.</p>
        </div>
        <Button variant="outline" asChild><Link href={`/jobs/${id}/candidates`}>View ranked candidates</Link></Button>
      </div>

      <DropZone onFiles={onFiles} />
      {busy && <p className="text-sm text-muted-foreground">Uploading…</p>}
      {error && <p className="text-sm text-destructive">{error}</p>}

      {results.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-medium">Processing {results.length} file(s)</p>
          {results.map((r) => <UploadRow key={r.resume_id} result={r} />)}
        </div>
      )}
    </div>
  );
}
