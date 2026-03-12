// CategoryGrid – 3-column interest grid with glass cards (matches new_design.html).
"use client";

import GlassCard from "@/components/ui/GlassCard";

/**
 * Extract a leading emoji from a category string like "🎮 Gaming & Esports".
 * Returns [emoji, rest] or [undefined, original] when no emoji prefix is found.
 */
function splitEmoji(text: string): [string | undefined, string] {
  // Match one or more emoji codepoints (including ZWJ sequences) at the start
  const m = text.match(
    /^(\p{Emoji_Presentation}(?:\u200d\p{Emoji_Presentation}|\ufe0f)*\s*)/u
  );
  if (m) return [m[1].trim(), text.slice(m[1].length)];
  return [undefined, text];
}

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
    <section aria-label="Interest Selection Grid" className="w-full max-w-4xl mb-12">
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-1">
        {categories.map((cat) => {
          const [emoji, label] = splitEmoji(cat);
          return (
            <div key={cat} className="w-2/3 mx-auto">
              <GlassCard
                label={label}
                emoji={emoji ?? ""}
                selected={selected.includes(cat)}
                onClick={() => onToggle(cat)}
              />
            </div>
          );
        })}
      </div>
    </section>
  );
}
