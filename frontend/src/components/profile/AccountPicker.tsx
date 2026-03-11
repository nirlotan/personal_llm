// AccountPicker – per-category account selection with glass cards.
"use client";

import GlassCard from "@/components/ui/GlassCard";
import type { Account } from "@/lib/types";

interface AccountPickerProps {
  category: string;
  accounts: Account[];
  selected: string[];
  onToggle: (name: string) => void;
}

export default function AccountPicker({
  category,
  accounts,
  selected,
  onToggle,
}: AccountPickerProps) {
  return (
    <section className="w-full max-w-5xl mb-12">
      <h2 className="text-xl font-semibold text-brand-dark mb-4">
        Select accounts to follow in{" "}
        <span className="text-purple-600">{category}</span>
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {accounts.map((acc) => (
          <GlassCard
            key={`${acc.category}:${acc.twitter_screen_name}`}
            label={acc.display_name}
            description={acc.description}
            selected={selected.includes(acc.twitter_name)}
            onClick={() => onToggle(acc.twitter_name)}
          />
        ))}
      </div>
      <p className="text-sm text-gray-500 mt-3">
        {selected.length < 3
          ? "Select 3 to 5 accounts"
          : selected.length > 5
          ? "Select no more than 5 accounts"
          : `${selected.length} selected`}
      </p>
    </section>
  );
}
