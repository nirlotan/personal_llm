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
      className={`glass-card h-12 px-3 py-2 flex items-center justify-between w-full group text-left cursor-pointer transition-all duration-200 ${
        selected ? "glass-card-selected" : ""
      }`}
    >
      <div className="flex items-center min-w-0">
        {emoji && (
          <span className="text-base mr-2 flex-shrink-0" role="img">
            {emoji}
          </span>
        )}
        <div className="min-w-0">
          <span className="text-sm font-medium text-gray-800 leading-tight line-clamp-1">{label}</span>
          {description && (
            <span className="block text-xs text-gray-400 leading-tight line-clamp-1">{description}</span>
          )}
        </div>
      </div>
      {selected && (
        <svg
          className="h-4 w-4 text-blue-500 flex-shrink-0 ml-1"
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
