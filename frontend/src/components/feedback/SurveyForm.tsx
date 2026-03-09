// SurveyForm – dynamic feedback form from API questions.
"use client";

import { useState, useEffect } from "react";
import StarRating from "@/components/ui/StarRating";
import GradientButton from "@/components/ui/GradientButton";
import { getSurveyQuestions, submitFeedback } from "@/lib/api";
import type { SurveyQuestion, FeedbackResponse } from "@/lib/types";

interface SurveyFormProps {
  sessionId: string;
  onSubmit: (result: FeedbackResponse) => void;
}

export default function SurveyForm({ sessionId, onSubmit }: SurveyFormProps) {
  const [questions, setQuestions] = useState<SurveyQuestion[]>([]);
  const [ratings, setRatings] = useState<Record<string, number>>({});
  const [freeText, setFreeText] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    getSurveyQuestions().then((res) => {
      setQuestions(res.questions);
      // Init all ratings to 0
      const init: Record<string, number> = {};
      res.questions.forEach((q) => (init[q.short_label] = 0));
      setRatings(init);
      setLoading(false);
    });
  }, []);

  const allRated = Object.values(ratings).every((v) => v > 0);

  const handleSubmit = async () => {
    if (!allRated || submitting) return;
    setSubmitting(true);
    try {
      const result = await submitFeedback(sessionId, {
        ratings,
        free_text: freeText,
      });
      onSubmit(result);
      // Leave submitting=true — navigation takes over; no need to re-enable the button
    } catch {
      setSubmitting(false); // Only re-enable on error so user can retry
    }
  };

  if (loading) {
    return <p className="text-gray-500">Loading questions...</p>;
  }

  return (
    <div className="glass-panel p-8 max-w-2xl mx-auto">
      {questions.map((q) => (
        <StarRating
          key={q.short_label}
          label={q.label}
          description={q.description}
          value={ratings[q.short_label] ?? 0}
          onChange={(v) =>
            setRatings((prev) => ({ ...prev, [q.short_label]: v }))
          }
        />
      ))}

      <div className="mb-6">
        <label className="block text-base font-medium text-gray-800 mb-2">
          Additional Feedback
        </label>
        <textarea
          value={freeText}
          onChange={(e) => setFreeText(e.target.value)}
          rows={3}
          className="w-full rounded-xl px-4 py-3 bg-white/40 backdrop-blur-sm border border-white/50 text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-400"
          placeholder="Share any additional thoughts..."
        />
      </div>

      {!allRated && (
        <p className="text-sm text-gray-500 mb-4">
          Please rate all questions to proceed.
        </p>
      )}

      <GradientButton onClick={handleSubmit} disabled={!allRated || submitting}>
        {submitting ? "Submitting..." : "Submit Survey"}
      </GradientButton>
    </div>
  );
}
