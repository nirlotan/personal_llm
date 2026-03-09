// ProgressBar – step progress indicator (matches new_design.html).
"use client";

interface ProgressBarProps {
  currentStep: number;
  totalSteps: number;
  label?: string;
}

export default function ProgressBar({
  currentStep,
  totalSteps,
  label,
}: ProgressBarProps) {
  const percent = Math.round((currentStep / totalSteps) * 100);

  return (
    <div className="w-full max-w-2xl mx-auto text-left">
      <span className="text-sm font-semibold text-slate-700 block mb-2">
        {label ?? `Step ${currentStep} of ${totalSteps}`}
      </span>
      <div className="w-full bg-white/40 h-2 rounded-full overflow-hidden backdrop-blur-sm">
        <div
          className="progress-fill h-full rounded-full shadow-lg transition-all duration-500"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
