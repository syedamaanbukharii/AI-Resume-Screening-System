"use client";

import { useCallback, useRef, useState } from "react";
import { UploadCloud } from "lucide-react";
import { cn } from "@/lib/utils";

/** Drag-and-drop file input restricted to pdf/docx/txt. */
export function DropZone({ onFiles }: { onFiles: (files: File[]) => void }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handle = useCallback(
    (list: FileList | null) => {
      if (!list) return;
      const allowed = ["pdf", "docx", "txt"];
      const files = Array.from(list).filter((f) => allowed.includes(f.name.split(".").pop()?.toLowerCase() ?? ""));
      if (files.length) onFiles(files);
    },
    [onFiles],
  );

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => { e.preventDefault(); setDragging(false); handle(e.dataTransfer.files); }}
      onClick={() => inputRef.current?.click()}
      className={cn(
        "flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed py-12 transition-colors",
        dragging ? "border-primary bg-accent" : "border-border hover:border-primary/50",
      )}
    >
      <UploadCloud className="mb-2 h-8 w-8 text-muted-foreground" />
      <p className="text-sm font-medium">Drop resumes here, or click to browse</p>
      <p className="mt-1 text-xs text-muted-foreground">PDF, DOCX, or TXT · multiple files supported</p>
      <input ref={inputRef} type="file" multiple accept=".pdf,.docx,.txt" className="hidden" onChange={(e) => handle(e.target.files)} />
    </div>
  );
}
