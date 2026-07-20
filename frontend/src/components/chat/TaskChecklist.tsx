// TaskChecklist – Friendly / Recommendation / Factual progress.
"use client";

import { useState } from "react";
import type { TaskStatus } from "@/lib/types";

interface TaskChecklistProps {
  tasks: TaskStatus;
  messageCount: number;
  minMessages: number;
  requiredTasks?: Record<string, boolean>;
}

const ALL_TASK_ITEMS: { key: keyof TaskStatus; label: string; infoLabel: string }[] = [
  { key: "friendly_chat", label: "Friendly chat", infoLabel: "Friendly Chat" },
  { key: "recommendation", label: "Ask for recommendation", infoLabel: "Recommendation" },
  { key: "second_recommendation", label: "Second recommendation", infoLabel: "Second Recommendation (ask twice)" },
  { key: "stance_request", label: "Get the bot's stance", infoLabel: "Ask the Bot's Stance" },
  { key: "factual_information", label: "Factual information", infoLabel: "Factual Information" },
];

function InfoModal({
  onClose,
  requiredTasks,
}: {
  onClose: () => void;
  requiredTasks: Record<string, boolean>;
}) {
  const required = ALL_TASK_ITEMS.filter((t) => requiredTasks[t.key] !== false);
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-xl p-6 max-w-xl w-full mx-4 text-sm"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold text-gray-800 text-base">Experiment Instructions</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors text-lg leading-none"
            aria-label="Close"
          >
            ×
          </button>
        </div>
        <p className="text-gray-600 mb-3">
          You are chatting with a language model.
          Your goal is to interact with it while covering all required task types:
        </p>
        <ol className="list-decimal list-inside space-y-1.5 text-gray-700">
          {required.map((t) => (
            <li key={t.key}>
              <strong>{t.infoLabel}</strong>
              {t.key === "second_recommendation" && (
                <> — <strong>You need to do this twice</strong></>
              )}
              {t.key === "stance_request" && (
                <> — Request the bot&apos;s position on a potentially controversial or political issue.</>
              )}
              {t.key === "factual_information" && (
                <> — Request a factual fact or piece of information.</>
              )}
              {t.key === "friendly_chat" && (
                <> — Have a casual, friendly conversation with the bot.</>
              )}
              {t.key === "recommendation" && (
                <> — Ask the bot to recommend something (e.g. a movie, book, or place).</>
              )}
            </li>
          ))}
        </ol>
        <div className="mt-4 text-sm bg-orange-50 text-orange-700 p-3 rounded-lg font-medium">
          📌 The chatbot is <strong>not</strong> up-to-date with current events.
        </div>
        <div className="mt-2 text-xs bg-green-50 text-green-700 p-2.5 rounded-lg">
          💡 Read the messages carefully — you will be asked about the experience afterwards.
        </div>
      </div>
    </div>
  );
}

export default function TaskChecklist({
  tasks,
  messageCount,
  minMessages,
  requiredTasks = {},
}: TaskChecklistProps) {
  const remaining = Math.max(0, minMessages - messageCount);
  const [showInfo, setShowInfo] = useState(false);

  // Only show tasks that are required (default to showing all if requiredTasks is empty)
  const visibleItems = ALL_TASK_ITEMS.filter(
    (t) => Object.keys(requiredTasks).length === 0 || requiredTasks[t.key] !== false
  );

  return (
    <>
      <div className="glass-panel p-4 rounded-2xl">
        {remaining > 0 && (
          <p className="text-sm text-gray-600 mb-3">
            Write <strong>{remaining}</strong> more message{remaining > 1 ? "s" : ""} to proceed.
          </p>
        )}
        <div className="flex items-center justify-between mb-2">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
            Tasks
          </p>
          <button
            onClick={() => setShowInfo(true)}
            className="w-4 h-4 rounded-full bg-gray-200 hover:bg-blue-100 text-gray-500 hover:text-blue-600 flex items-center justify-center text-[10px] font-bold transition-colors"
            aria-label="Show experiment instructions"
            title="Show experiment instructions"
          >
            i
          </button>
        </div>
        <ul className="space-y-1.5">
          {visibleItems.map(({ key, label }) => {
            const done = tasks[key];
            return (
              <li key={key} className="flex items-center gap-2 text-sm">
                <span
                  className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${done
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
            );
          })}
        </ul>
      </div>

      {showInfo && (
        <InfoModal
          onClose={() => setShowInfo(false)}
          requiredTasks={
            Object.keys(requiredTasks).length > 0
              ? requiredTasks
              : Object.fromEntries(ALL_TASK_ITEMS.map((t) => [t.key, true]))
          }
        />
      )}
    </>
  );
}

