// StarRating – Likert scale for feedback survey.
"use client";

import { useState } from "react";

interface StarRatingProps {
  maxStars?: number;
  value: number;
  onChange: (value: number) => void;
  label: string;
  description?: string;
}

export default function StarRating({
  maxStars = 5,
  value,
  onChange,
  label,
  description,
}: StarRatingProps) {
  const [hovered, setHovered] = useState(0);

  return (
    <div className="mb-6">
      <div
        className="text-base font-medium text-gray-800 mb-1"
        dangerouslySetInnerHTML={{ __html: label }}
      />
      {description && (
        <p className="text-sm text-gray-500 mb-2">{description}</p>
      )}
      <div className="star-rating flex gap-1">
        {Array.from({ length: maxStars }, (_, i) => i + 1).map((star) => (
          <button
            key={star}
            type="button"
            onMouseEnter={() => setHovered(star)}
            onMouseLeave={() => setHovered(0)}
            onClick={() => onChange(star)}
            className="text-2xl focus:outline-none"
            aria-label={`Rate ${star} out of ${maxStars}`}
          >
            {star <= (hovered || value) ? "★" : "☆"}
          </button>
        ))}
      </div>
    </div>
  );
}
