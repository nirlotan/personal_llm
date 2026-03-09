// Missed attention check page – ported from pages/missed_attention.py.
"use client";

export default function MissedAttentionPage() {
  return (
    <div className="text-center space-y-4 glass-panel p-10 max-w-lg mx-auto">
      <h2 className="text-xl font-semibold text-brand-dark">
        Unfortunately, you did not answer the attention check correctly.
      </h2>
      <p className="text-gray-600">
        If you would like to retake the study, please contact the research team.
      </p>
      <p className="text-gray-600">
        Otherwise, you may choose to withdraw without payment.
      </p>
    </div>
  );
}
