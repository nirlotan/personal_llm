// CategoryGrid – 3-column interest grid with glass cards (matches new_design.html).
"use client";

import GlassCard from "@/components/ui/GlassCard";

// Emoji mapping for known categories
const CATEGORY_EMOJIS: Record<string, string> = {
  Technology: "💻",
  Science: "🚀",
  "Arts & Culture": "🎨",
  Travel: "✈️",
  "Health & Wellness": "💪",
  Gaming: "🎮",
  Music: "🎵",
  Finance: "💰",
  News: "📰",
  Sports: "⚽",
  Entertainment: "🎬",
  Food: "🍕",
  Education: "📚",
  Fashion: "👗",
  Politics: "🏛️",
  Business: "💼",
  Lifestyle: "🌿",
  Comedy: "😂",
};

interface CategoryGridProps {
  categories: string[];
  selected: string[];
  onToggle: (category: string) => void;
}

export default function CategoryGrid({
  categories,
  selected,
  onToggle,
}: CategoryGridProps) {
  return (
    <section aria-label="Interest Selection Grid" className="w-full max-w-5xl mb-12">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {categories.map((cat) => (
          <GlassCard
            key={cat}
            label={cat}
            emoji={CATEGORY_EMOJIS[cat] ?? "📌"}
            selected={selected.includes(cat)}
            onClick={() => onToggle(cat)}
          />
        ))}
      </div>
    </section>
  );
}
