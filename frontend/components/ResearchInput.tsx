"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

const EXAMPLES = [
  "Latest AI chip releases in 2026",
  "State of quantum computing 2026",
  "Best electric vehicles available in 2026",
];

interface Props {
  onSubmit: (topic: string) => void;
  isLoading: boolean;
}

export function ResearchInput({ onSubmit, isLoading }: Props) {
  const [topic, setTopic] = useState("");

  const submit = () => {
    const t = topic.trim();
    if (t) onSubmit(t);
  };

  return (
    <div className="flex flex-col gap-3 w-full">
      <Textarea
        placeholder="Ask anything — Nexus will research, analyse, and synthesise a report..."
        value={topic}
        onChange={(e) => setTopic(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); }
        }}
        rows={3}
        className="resize-none text-base bg-card border-border"
        disabled={isLoading}
      />
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex flex-wrap gap-2">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              onClick={() => setTopic(ex)}
              disabled={isLoading}
              className="text-xs text-muted-foreground border border-border rounded-full px-3 py-1 hover:bg-muted transition-colors disabled:opacity-40"
            >
              {ex}
            </button>
          ))}
        </div>
        <Button onClick={submit} disabled={isLoading || !topic.trim()} size="lg">
          {isLoading ? "Researching…" : "Research →"}
        </Button>
      </div>
    </div>
  );
}
