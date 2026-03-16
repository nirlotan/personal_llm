// AccountPicker – per-category account selection with glass cards.
"use client";

import GlassCard from "@/components/ui/GlassCard";
import type { Account } from "@/lib/types";
import { MIN_ACCOUNTS_PER_CATEGORY, MAX_ACCOUNTS_PER_CATEGORY } from "@/lib/constants";

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
        <span className="text-blue-600">{category}</span>
      </h2>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
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
        {selected.length < MIN_ACCOUNTS_PER_CATEGORY
          ? `Select ${MIN_ACCOUNTS_PER_CATEGORY} to ${MAX_ACCOUNTS_PER_CATEGORY} accounts`
          : selected.length > MAX_ACCOUNTS_PER_CATEGORY
          ? `Select no more than ${MAX_ACCOUNTS_PER_CATEGORY} accounts`
          : `${selected.length} selected`}
      </p>
    </section>
  );
}
