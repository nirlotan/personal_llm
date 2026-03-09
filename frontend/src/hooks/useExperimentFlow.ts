// useExperimentFlow – step validation and navigation guards.
"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { STEPS } from "@/lib/constants";

export type StepKey = "interests" | "chat" | "feedback";

const STEP_ORDER: StepKey[] = ["interests", "chat", "feedback"];

export function useExperimentFlow() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState<StepKey>("interests");

  const stepIndex = STEP_ORDER.indexOf(currentStep);
  const totalSteps = STEPS.length;
  const progressPercent = Math.round(((stepIndex + 1) / totalSteps) * 100);

  const goToStep = useCallback(
    (step: StepKey) => {
      setCurrentStep(step);
      const found = STEPS.find((s) => s.label.toLowerCase() === step);
      if (found) router.push(found.path);
    },
    [router]
  );

  const nextStep = useCallback(() => {
    const idx = STEP_ORDER.indexOf(currentStep);
    if (idx < STEP_ORDER.length - 1) {
      goToStep(STEP_ORDER[idx + 1]);
    }
  }, [currentStep, goToStep]);

  return {
    currentStep,
    stepIndex,
    totalSteps,
    progressPercent,
    goToStep,
    nextStep,
  };
}
