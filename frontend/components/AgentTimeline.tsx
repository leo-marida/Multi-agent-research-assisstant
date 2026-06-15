"use client";

import { AgentEvent } from "@/lib/stream";

const CONFIG: Record<string, { icon: string; color: string; bg: string }> = {
  agent_start:    { icon: "◉", color: "text-blue-400",   bg: "bg-blue-500/10 border-blue-500/20" },
  tool_call:      { icon: "⚙", color: "text-amber-400",  bg: "bg-amber-500/10 border-amber-500/20" },
  tool_result:    { icon: "✓", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
  agent_complete: { icon: "◆", color: "text-purple-400",  bg: "bg-purple-500/10 border-purple-500/20" },
  error:          { icon: "✕", color: "text-red-400",     bg: "bg-red-500/10 border-red-500/20" },
};

function summarise(e: AgentEvent): string {
  const d = e.data;
  switch (e.type) {
    case "agent_start":
      return d.title
        ? `${d.agent} → ${d.title}`
        : `${d.agent} → ${String(d.input ?? "").slice(0, 55)}`;
    case "tool_call":
      return `${d.tool}(${String(d.input ?? "").slice(0, 70)})`;
    case "tool_result":
      return `${d.tool} → ${String(d.summary ?? "").slice(0, 80)}`;
    case "agent_complete":
      if (d.subtasks) return `planner → ${(d.subtasks as unknown[]).length} subtasks`;
      if (d.chunks_ingested !== undefined) return `researcher → ${d.chunks_ingested} chunks stored`;
      if (d.finding) return `analyst → ${(d.finding as string).length} char finding`;
      return `${d.agent} complete`;
    case "error":
      return `${d.type}: ${d.message}`;
    default:
      return JSON.stringify(d).slice(0, 80);
  }
}

export function AgentTimeline({ events }: { events: AgentEvent[] }) {
  if (!events.length) return null;
  return (
    <div className="flex flex-col gap-2">
      <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
        Live Activity
      </p>
      <div className="flex flex-col gap-1 max-h-[420px] overflow-y-auto pr-1">
        {events.map((e) => {
          const c = CONFIG[e.type] ?? CONFIG.agent_start;
          return (
            <div
              key={e.id}
              className={`flex items-start gap-2 rounded-md border px-2.5 py-1.5 text-xs animate-in slide-in-from-left-2 duration-150 ${c.bg}`}
            >
              <span className={`mt-px shrink-0 font-mono ${c.color}`}>{c.icon}</span>
              <span className="opacity-80 break-all leading-4">{summarise(e)}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
