// TaskChecklist – Friendly / Recommendation / Factual progress.
"use client";

import type { TaskStatus } from "@/lib/types";

interface TaskChecklistProps {
  tasks: TaskStatus;
  messageCount: number;
  minMessages: number;
}

export default function TaskChecklist({
  tasks,
  messageCount,
  minMessages,
}: TaskChecklistProps) {
  const remaining = Math.max(0, minMessages - messageCount);

  const items = [
    { label: "Friendly Chat", done: tasks.friendly_chat },
    { label: "Recommendation", done: tasks.recommendation },
    { label: "Factual Information", done: tasks.factual_information },
  ];

  return (
    <div className="glass-panel p-4 rounded-2xl">
      {remaining > 0 && (
        <p className="text-sm text-gray-600 mb-3">
          Write <strong>{remaining}</strong> more message{remaining > 1 ? "s" : ""} to proceed.
        </p>
      )}
      <p className="text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">
        Tasks
      </p>
      <ul className="space-y-1.5">
        {items.map(({ label, done }) => (
          <li key={label} className="flex items-center gap-2 text-sm">
            <span
              className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${
                done
                  ? "bg-green-100 text-green-600"
                  : "bg-gray-100 text-gray-400"
              }`}
            >
              {done ? "✓" : "○"}
            </span>
            <span className={done ? "text-gray-700" : "text-gray-400"}>
              {label}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
