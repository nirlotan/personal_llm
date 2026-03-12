// GradientButton – primary action button (matches new_design.html).
"use client";

import { ButtonHTMLAttributes } from "react";

interface GradientButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary";
}

export default function GradientButton({
  children,
  variant = "primary",
  className = "",
  disabled,
  ...props
}: GradientButtonProps) {
  if (variant === "secondary") {
    return (
      <button
        className={`text-slate-500 hover:text-blue-600 font-medium text-lg transition-colors duration-200 ${className}`}
        disabled={disabled}
        {...props}
      >
        {children}
      </button>
    );
  }

  return (
    <button
      className={`btn-gradient text-white px-12 py-3.5 rounded-[0.625rem] font-semibold text-lg hover:scale-105 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 ${className}`}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
}
