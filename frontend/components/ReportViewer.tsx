"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "@/components/ui/button";

interface Props {
  report: string;
  sources: string[];
  topic: string;
  onReset: () => void;
}

function getDomain(url: string) {
  try { return new URL(url).hostname.replace("www.", ""); } catch { return url; }
}

function toSlug(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .trim()
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .slice(0, 70)
    .replace(/-$/, "");
}

function getFilename(report: string, topic: string): string {
  const h1 = report.match(/^#\s+(.+)$/m);
  const raw = h1 ? h1[1].replace(/\[([^\]]+)\]\([^)]+\)/g, "$1") : topic;
  return `${toSlug(raw)}.md`;
}

function downloadFile(content: string, filename: string, type: string) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function ReportViewer({ report, sources, topic, onReset }: Props) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(report);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadMd = () =>
    downloadFile(report, getFilename(report, topic), "text/markdown");

  const handlePrint = () => window.print();

  const unique = [...new Set(sources)];

  return (
    <div className="flex flex-col gap-6 animate-in fade-in duration-500">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-semibold tracking-tight">Research Report</h2>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" onClick={handleCopy}>
            {copied ? "✓ Copied" : "Copy text"}
          </Button>
          <Button variant="outline" size="sm" onClick={handleDownloadMd}>
            Download .md
          </Button>
          <Button variant="outline" size="sm" onClick={handlePrint}>
            Save as PDF
          </Button>
          <Button size="sm" onClick={onReset}>
            New research
          </Button>
        </div>
      </div>

      {/* Report body */}
      <div className="rounded-xl border border-border bg-card px-7 py-6 print:border-0 print:shadow-none">
        <div className="prose dark:prose-invert prose-sm max-w-none
          prose-headings:font-semibold prose-headings:tracking-tight
          prose-h1:text-2xl prose-h1:mb-4
          prose-h2:text-lg prose-h2:mt-6 prose-h2:mb-2
          prose-p:leading-7 prose-p:my-2
          prose-li:my-0.5
          prose-a:text-blue-600 dark:prose-a:text-blue-400 prose-a:no-underline hover:prose-a:underline
          prose-strong:text-foreground
          [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{report}</ReactMarkdown>
        </div>
      </div>

      {/* Sources */}
      {unique.length > 0 && (
        <div className="flex flex-col gap-3">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
            Sources ({unique.length})
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {unique.map((url, i) => (
              <a
                key={url}
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 rounded-lg border border-border bg-muted/30 px-3 py-2 text-xs hover:bg-muted transition-colors truncate"
              >
                <span className="shrink-0 font-mono text-muted-foreground">{i + 1}.</span>
                <span className="truncate font-medium">{getDomain(url)}</span>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
