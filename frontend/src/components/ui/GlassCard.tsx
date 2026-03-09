// GlassCard – Glassmorphism selection card (matches new_design.html).
"use client";

interface GlassCardProps {
  label: string;
  emoji?: string;
  selected?: boolean;
  onClick?: () => void;
  description?: string;
}

export default function GlassCard({
  label,
  emoji,
  selected = false,
  onClick,
  description,
}: GlassCardProps) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={onClick}
      className={`glass-card h-20 px-6 py-4 flex items-center justify-between w-full group text-left cursor-pointer transition-all duration-300 ${
        selected ? "glass-card-selected" : ""
      }`}
    >
      <div className="flex items-center">
        {emoji && (
          <span className="text-2xl mr-3" role="img">
            {emoji}
          </span>
        )}
        <div>
          <span className="text-lg font-medium text-gray-800">{label}</span>
          {description && (
            <span className="block text-sm text-gray-500">{description}</span>
          )}
        </div>
      </div>
      {selected && (
        <svg
          className="h-6 w-6 text-purple-500 flex-shrink-0"
          fill="none"
          stroke="currentColor"
          strokeWidth={2.5}
          viewBox="0 0 24 24"
        >
          <path
            d="M5 13l4 4L19 7"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      )}
    </button>
  );
}
