"use client";

import { useState, useRef, useMemo, useEffect } from "react";
import { ResearchInput } from "@/components/ResearchInput";
import { AgentTimeline } from "@/components/AgentTimeline";
import { ReportViewer } from "@/components/ReportViewer";
import { ProgressTracker, getInitialSteps, Step, StepStatus } from "@/components/ProgressTracker";
import { ThemeToggle } from "@/components/ThemeToggle";
import { openResearchStream, AgentEvent } from "@/lib/stream";

// ---------------------------------------------------------------------------
// Step state — pure function of the event log
// ---------------------------------------------------------------------------

function applyEvent(steps: Step[], event: AgentEvent): Step[] {
  const { type, data, receivedAt } = event;

  return steps.map((step): Step => {

    if (step.id === "planning") {
      if (type === "agent_start" && data["agent"] === "planner") {
        return { ...step, status: "running", startedAt: receivedAt };
      }
      if (type === "agent_complete" && data["agent"] === "planner") {
        return { ...step, status: "done", completedAt: receivedAt };
      }
      return step;
    }

    if (step.id === "research") {
      if (type === "agent_complete" && data["agent"] === "planner") {
        const subtasks = (data["subtasks"] as { id: string; title: string }[]) ?? [];
        return {
          ...step,
          children: subtasks.map((s) => ({ id: s.id, label: s.title, status: "pending" as StepStatus })),
        };
      }
      if (type === "agent_start" && data["agent"] === "researcher") {
        const sid = data["subtask_id"] as string;
        return {
          ...step,
          status: "running" as StepStatus,
          startedAt: step.startedAt ?? receivedAt,
          children: step.children.map((c) =>
            c.id === sid ? { ...c, status: "running" as StepStatus, startedAt: receivedAt } : c
          ),
        };
      }
      if (type === "agent_complete" && data["agent"] === "researcher") {
        const sid = data["subtask_id"] as string;
        const kids = step.children.map((c) =>
          c.id === sid ? { ...c, status: "done" as StepStatus, completedAt: receivedAt } : c
        );
        const allDone = kids.length > 0 && kids.every((c) => c.status === "done");
        return {
          ...step,
          children: kids,
          status: allDone ? ("done" as StepStatus) : step.status,
          ...(allDone ? { completedAt: receivedAt } : {}),
        };
      }
      return step;
    }

    if (step.id === "analysis") {
      if (type === "agent_complete" && data["agent"] === "planner") {
        const subtasks = (data["subtasks"] as { id: string; title: string }[]) ?? [];
        return {
          ...step,
          children: subtasks.map((s) => ({ id: s.id, label: s.title, status: "pending" as StepStatus })),
        };
      }
      if (type === "agent_start" && data["agent"] === "analyst") {
        const sid = data["subtask_id"] as string;
        return {
          ...step,
          status: "running" as StepStatus,
          startedAt: step.startedAt ?? receivedAt,
          children: step.children.map((c) =>
            c.id === sid ? { ...c, status: "running" as StepStatus, startedAt: receivedAt } : c
          ),
        };
      }
      if (type === "agent_complete" && data["agent"] === "analyst") {
        const sid = data["subtask_id"] as string;
        const kids = step.children.map((c) =>
          c.id === sid ? { ...c, status: "done" as StepStatus, completedAt: receivedAt } : c
        );
        const allDone = kids.length > 0 && kids.every((c) => c.status === "done");
        return {
          ...step,
          children: kids,
          status: allDone ? ("done" as StepStatus) : step.status,
          ...(allDone ? { completedAt: receivedAt } : {}),
        };
      }
      return step;
    }

    if (step.id === "synthesis") {
      if (type === "agent_start" && data["agent"] === "synthesizer") {
        return { ...step, status: "running", startedAt: receivedAt };
      }
      if (type === "agent_complete" && data["agent"] === "synthesizer") {
        return { ...step, status: "done", completedAt: receivedAt };
      }
      return step;
    }

    return step;
  });
}

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------

export default function Home() {
  const [phase, setPhase] = useState<"idle" | "researching" | "done">("idle");
  const [topic, setTopic] = useState("");
  const [draftTopic, setDraftTopic] = useState("");
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [report, setReport] = useState("");
  const [sources, setSources] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const cleanup = useRef<(() => void) | null>(null);

  // When research finishes, pre-fill the draft so user can edit immediately
  useEffect(() => {
    if (phase === "done") setDraftTopic(topic);
  }, [phase, topic]);

  const steps = useMemo(
    () => events.reduce((acc, ev) => applyEvent(acc, ev), getInitialSteps()),
    [events]
  );

  const handleSubmit = (t: string) => {
    const trimmed = t.trim();
    if (!trimmed) return;
    cleanup.current?.();
    setPhase("researching");
    setTopic(trimmed);
    setDraftTopic("");
    setEvents([]);
    setReport("");
    setSources([]);
    setError(null);

    cleanup.current = openResearchStream(trimmed, {
      onAgentEvent: (e) => {
        setEvents((prev) => [...prev, e]);
        if (e.type === "agent_complete" && e.data["agent"] === "analyst" && Array.isArray(e.data["sources"])) {
          setSources((prev) => [...new Set([...prev, ...(e.data["sources"] as string[])])]);
        }
      },
      onReportChunk: (chunk) => setReport((prev) => prev + chunk),
      onComplete: () => setPhase("done"),
      onError: (err) => {
        setError(err.message);
        setPhase("idle");
      },
    });
  };

  const handleReset = () => {
    cleanup.current?.();
    setPhase("idle");
    setTopic("");
    setDraftTopic("");
    setEvents([]);
    setReport("");
    setSources([]);
    setError(null);
  };

  return (
    <main className="min-h-screen bg-background text-foreground">
      {/* ── Header ── */}
      <header className="border-b border-border/50 bg-card/40 backdrop-blur-sm sticky top-0 z-10">
        <div className="mx-auto max-w-6xl px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xl font-bold tracking-tight">Nexus</span>
            <span className="hidden sm:block text-xs text-muted-foreground border border-border rounded-full px-2 py-0.5">
              Multi-Agent Research
            </span>
          </div>
          <div className="flex items-center gap-3">
            {phase !== "idle" && (
              <button
                onClick={handleReset}
                className="text-xs text-muted-foreground hover:text-foreground transition-colors"
              >
                ← New research
              </button>
            )}
            <ThemeToggle />
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-6 py-8 flex flex-col gap-6">

        {/* ── Error banner ── */}
        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
            {error}
          </div>
        )}

        {/* ── IDLE ── */}
        {phase === "idle" && (
          <div className="flex flex-col gap-6 max-w-2xl mx-auto w-full text-center pt-8">
            <div>
              <h1 className="text-4xl sm:text-5xl font-bold tracking-tight mb-3">
                Research anything.
              </h1>
              <p className="text-muted-foreground text-lg">
                Nexus plans, searches, analyses, and synthesises a cited report — powered by GPT-4.1 and pgvector.
              </p>
            </div>
            <ResearchInput onSubmit={handleSubmit} isLoading={false} />
          </div>
        )}

        {/* ── RESEARCHING / DONE ── */}
        {(phase === "researching" || phase === "done") && (
          <>
            {/* Topic strip */}
            {phase === "researching" ? (
              /* Read-only while working */
              <div className="flex items-center gap-3 rounded-xl border border-border bg-card/60 px-5 py-4">
                <div className="flex flex-col gap-0.5 flex-1 min-w-0">
                  <span className="text-[11px] uppercase tracking-widest text-muted-foreground font-medium">
                    Research query
                  </span>
                  <span className="text-sm font-medium leading-snug">{topic}</span>
                </div>
                <div className="flex items-center gap-2 shrink-0 text-xs text-muted-foreground">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-blue-500" />
                  </span>
                  Working…
                </div>
              </div>
            ) : (
              /* Editable when done — user can modify and resubmit */
              <form
                onSubmit={(e) => { e.preventDefault(); handleSubmit(draftTopic); }}
                className="flex items-center gap-3 rounded-xl border border-border bg-card/60 px-5 py-4"
              >
                <div className="flex flex-col gap-1 flex-1 min-w-0">
                  <span className="text-[11px] uppercase tracking-widest text-muted-foreground font-medium">
                    Research query — edit and resubmit
                  </span>
                  <input
                    value={draftTopic}
                    onChange={(e) => setDraftTopic(e.target.value)}
                    className="bg-transparent text-sm font-medium leading-snug outline-none w-full placeholder:text-muted-foreground/40"
                    placeholder="Type a new query…"
                  />
                </div>
                <button
                  type="submit"
                  disabled={!draftTopic.trim()}
                  className="shrink-0 rounded-lg bg-primary px-4 py-1.5 text-xs font-semibold text-primary-foreground disabled:opacity-40 hover:opacity-90 transition-opacity"
                >
                  Research ↗
                </button>
              </form>
            )}

            {/* Two-column layout */}
            <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6 items-start">

              {/* Left: report */}
              <div className="flex flex-col gap-4 min-w-0">
                {phase === "done" ? (
                  <ReportViewer report={report} sources={sources} topic={topic} onReset={handleReset} />
                ) : report ? (
                  <div className="rounded-xl border border-border bg-card px-7 py-6">
                    <p className="text-xs font-mono text-muted-foreground mb-4 flex items-center gap-2">
                      <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                      Synthesising report…
                    </p>
                    <div className="prose dark:prose-invert prose-sm max-w-none
                      prose-headings:font-semibold prose-h1:text-xl prose-h2:text-base
                      prose-p:leading-7 prose-p:my-2 prose-li:my-0.5">
                      <ReactMarkdownWrapper content={report} />
                    </div>
                  </div>
                ) : (
                  <div className="rounded-xl border border-border bg-card/50 px-7 py-12 flex flex-col items-center gap-4 text-muted-foreground">
                    <div className="flex gap-1.5">
                      {[0, 1, 2].map((i) => (
                        <span
                          key={i}
                          className="w-2 h-2 rounded-full bg-blue-400 animate-bounce"
                          style={{ animationDelay: `${i * 0.15}s` }}
                        />
                      ))}
                    </div>
                    <p className="text-sm">Agents are gathering and analysing sources…</p>
                  </div>
                )}
              </div>

              {/* Right: progress + timeline */}
              <div className="lg:sticky lg:top-20 flex flex-col gap-4">
                <div className="rounded-xl border border-border bg-card px-5 py-4">
                  <ProgressTracker steps={steps} />
                </div>
                {events.length > 0 && (
                  <div className="rounded-xl border border-border bg-card px-5 py-4">
                    <AgentTimeline events={events} />
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </main>
  );
}

function ReactMarkdownWrapper({ content }: { content: string }) {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const ReactMarkdown = require("react-markdown").default;
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const remarkGfm = require("remark-gfm").default;
  return <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>;
}
