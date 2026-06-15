"use client";

import { useEffect, useState } from "react";

export type StepStatus = "pending" | "running" | "done" | "error";

export interface SubStep {
  id: string;
  label: string;
  status: StepStatus;
  startedAt?: number;
  completedAt?: number;
}

export interface Step {
  id: "planning" | "research" | "analysis" | "synthesis";
  label: string;
  status: StepStatus;
  startedAt?: number;
  completedAt?: number;
  estimateSec: number;
  children: SubStep[];
}

export function getInitialSteps(): Step[] {
  return [
    { id: "planning",  label: "Planning strategy",   status: "pending", estimateSec: 10, children: [] },
    { id: "research",  label: "Gathering sources",   status: "pending", estimateSec: 75, children: [] },
    { id: "analysis",  label: "Analysing findings",  status: "pending", estimateSec: 25, children: [] },
    { id: "synthesis", label: "Writing report",      status: "pending", estimateSec: 35, children: [] },
  ];
}

function fmt(sec: number): string {
  if (sec < 60) return `${Math.round(sec)}s`;
  const m = Math.floor(sec / 60);
  const s = Math.round(sec % 60);
  return s === 0 ? `${m}m` : `${m}m ${s}s`;
}

function StepDot({ status }: { status: StepStatus }) {
  if (status === "done") {
    return (
      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-500/15 ring-1 ring-emerald-500/40 text-[10px] text-emerald-400">
        ✓
      </span>
    );
  }
  if (status === "running") {
    return (
      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-blue-500/15 ring-1 ring-blue-500/40">
        <span className="h-2 w-2 rounded-full bg-blue-400 animate-pulse" />
      </span>
    );
  }
  if (status === "error") {
    return (
      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-red-500/15 ring-1 ring-red-500/40 text-[10px] text-red-400">
        ✕
      </span>
    );
  }
  return (
    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full ring-1 ring-border">
      <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground/30" />
    </span>
  );
}

function SubDot({ status }: { status: StepStatus }) {
  if (status === "done") return <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400" />;
  if (status === "running") return <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-blue-400 animate-pulse" />;
  return <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-border" />;
}

export function ProgressTracker({ steps }: { steps: Step[] }) {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 500);
    return () => clearInterval(id);
  }, []);

  const allDone = steps.every((s) => s.status === "done");

  // Overall elapsed: from first step started to last step done (or now)
  const firstStart = steps.reduce<number | undefined>((min, s) => {
    if (s.startedAt === undefined) return min;
    return min === undefined ? s.startedAt : Math.min(min, s.startedAt);
  }, undefined);

  const lastEnd = allDone
    ? steps.reduce<number | undefined>((max, s) => {
        if (s.completedAt === undefined) return max;
        return max === undefined ? s.completedAt : Math.max(max, s.completedAt);
      }, undefined)
    : undefined;

  const totalElapsed = firstStart ? ((lastEnd ?? now) - firstStart) / 1000 : 0;

  // Weighted progress bar
  const weights: Record<string, number> = { planning: 10, research: 45, analysis: 25, synthesis: 20 };
  let earned = 0;
  for (const step of steps) {
    const w = weights[step.id] ?? 25;
    if (step.status === "done") {
      earned += w;
    } else if (step.status === "running") {
      const childTotal = step.children.length;
      const childDone = step.children.filter((c) => c.status === "done").length;
      earned += w * (childTotal > 0 ? childDone / childTotal : 0.15);
    }
  }
  const pct = Math.min(99, Math.round((earned / 100) * 100));
  const displayPct = allDone ? 100 : pct;

  return (
    <div className="flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
          Progress
        </span>
        {allDone && firstStart ? (
          <span className="text-[11px] font-medium text-emerald-400">
            Done in {fmt(totalElapsed)}
          </span>
        ) : firstStart ? (
          <span className="text-[11px] tabular-nums text-muted-foreground">
            {fmt(totalElapsed)} elapsed
          </span>
        ) : null}
      </div>

      {/* Progress bar */}
      <div className="h-1 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-emerald-500 transition-all duration-700"
          style={{ width: `${displayPct}%` }}
        />
      </div>

      {/* Steps */}
      <div className="flex flex-col gap-0.5 pt-1">
        {steps.map((step) => {
          const elapsed = step.startedAt
            ? ((step.completedAt ?? now) - step.startedAt) / 1000
            : null;

          return (
            <div key={step.id} className="flex flex-col">
              {/* Main step row */}
              <div className="flex items-center gap-2.5 py-1.5">
                <StepDot status={step.status} />
                <span
                  className={`text-sm leading-none ${
                    step.status === "done"
                      ? "text-emerald-400"
                      : step.status === "running"
                      ? "font-medium text-foreground"
                      : "text-muted-foreground"
                  }`}
                >
                  {step.label}
                </span>

                {/* Time badge */}
                {step.status === "pending" && (
                  <span className="ml-auto text-[11px] text-muted-foreground/50">
                    ~{fmt(step.estimateSec)}
                  </span>
                )}
                {step.status === "running" && elapsed !== null && (
                  <span className="ml-auto text-[11px] tabular-nums text-muted-foreground">
                    {fmt(elapsed)}…
                  </span>
                )}
                {step.status === "done" && elapsed !== null && (
                  <span className="ml-auto text-[11px] tabular-nums text-emerald-400/80">
                    {fmt(elapsed)}
                  </span>
                )}
              </div>

              {/* Sub-steps */}
              {step.children.length > 0 && (
                <div className="ml-[30px] mb-1 flex flex-col gap-1 border-l border-border/40 pl-3">
                  {step.children.map((child) => {
                    const childElapsed = child.startedAt
                      ? ((child.completedAt ?? now) - child.startedAt) / 1000
                      : null;
                    return (
                      <div key={child.id} className="flex items-center gap-2 py-0.5">
                        <SubDot status={child.status} />
                        <span
                          className={`text-[12px] leading-none ${
                            child.status === "done"
                              ? "text-emerald-400/80"
                              : child.status === "running"
                              ? "text-foreground/90"
                              : "text-muted-foreground/60"
                          }`}
                        >
                          {child.label}
                        </span>
                        {child.status === "running" && childElapsed !== null && (
                          <span className="ml-auto text-[10px] tabular-nums text-muted-foreground/70">
                            {fmt(childElapsed)}…
                          </span>
                        )}
                        {child.status === "done" && childElapsed !== null && (
                          <span className="ml-auto text-[10px] tabular-nums text-emerald-400/60">
                            {fmt(childElapsed)}
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
