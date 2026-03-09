// Tutorial / consent page (Step 0) — ported from pages/tutorial.py.
"use client";

import { useRouter } from "next/navigation";
import GradientButton from "@/components/ui/GradientButton";
import { useSession } from "@/hooks/useSession";

export default function TutorialPage() {
  const router = useRouter();
  const { startSession, loading, error } = useSession();

  const handleStart = async () => {
    try {
      await startSession();
      router.push("/profile");
    } catch {
      // error state is set by the hook and displayed below
    }
  };

  return (
    <>
      <header className="text-center mb-10 w-full max-w-3xl">
        <h1 className="text-[32px] font-bold text-brand-dark mb-2 tracking-tight">
          Personal Chat Experiment
        </h1>
        <h2 className="text-xl text-gray-600 mb-6">
          The Impact of Personalization on Large Language Models (LLMs)
        </h2>
      </header>

      <div className="glass-panel p-8 max-w-2xl w-full text-center space-y-4">
        <p className="text-gray-700">
          Hey there, and thanks for participating!
        </p>
        <p className="text-gray-700">
          You&apos;re taking part in a study exploring how personalization affects
          the way people interact with large language models (LLMs).
        </p>

        <div className="text-left space-y-2 bg-white/20 rounded-xl p-4">
          <p className="font-semibold text-gray-800">The experiment has the following parts:</p>
          <ol className="list-decimal list-inside space-y-1 text-gray-700">
            <li>Pick a few topics you&apos;re interested in, and social media accounts for each topic.</li>
            <li>You&apos;ll be asked to chat with <strong>two separate language models</strong>.</li>
            <li>After chatting <strong>with each of the models</strong> you&apos;ll be asked a few questions about the experience.</li>
          </ol>
        </div>

        <p className="text-sm text-gray-500">
          Everything is completely anonymous, and your responses will only be used for research.
        </p>
        <p className="text-sm text-gray-500">
          By clicking &quot;Start&quot; below, you agree to participate in this study.
        </p>
        <p className="font-medium text-gray-700">
          We appreciate your time and contribution!
        </p>
      </div>

      {error && (
        <div className="mt-4 max-w-2xl w-full bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm text-center">
          {error}
        </div>
      )}

      <footer className="mt-8">
        <GradientButton onClick={handleStart} disabled={loading}>
          {loading ? "Starting..." : "Start"}
        </GradientButton>
      </footer>
    </>
  );
}
