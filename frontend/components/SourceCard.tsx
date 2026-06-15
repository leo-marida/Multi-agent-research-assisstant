"use client";

interface Props {
  url: string;
  index: number;
}

export function SourceCard({ url, index }: Props) {
  let hostname = url;
  try {
    hostname = new URL(url).hostname.replace("www.", "");
  } catch {}

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center gap-2 rounded-lg border border-border bg-muted/40 px-3 py-2 text-sm hover:bg-muted transition-colors"
    >
      <span className="text-muted-foreground font-mono text-xs">[{index}]</span>
      <span className="font-medium truncate">{hostname}</span>
    </a>
  );
}
